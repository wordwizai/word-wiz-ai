import asyncio
import contextlib
import os
import unittest
from unittest import mock

import numpy as np

from tests.benchmark import common
from tests.benchmark import pipeline as PL
from tests.benchmark import testutil as U


class _ListPhonemes:
    def __init__(self, lists):
        self.lists = lists

    def extract_phoneme(self, audio, sampling_rate=16000, **_kwargs):
        return [list(p) for p in self.lists]


class _Raises:
    def __init__(self, exc):
        self.exc = exc

    def extract_phoneme(self, audio, sampling_rate=16000, **_kwargs):
        raise self.exc


class _Records:
    """Stands in for a phoneme model and remembers whether it was ever asked."""

    def __init__(self, lists):
        self.lists = lists
        self.calls = 0

    def extract_phoneme(self, audio, sampling_rate=16000, **_kwargs):
        self.calls += 1
        return [list(p) for p in self.lists]


@contextlib.contextmanager
def _gates(soft):
    """Soft gates (the default) or hard gates, whatever the environment says."""
    with mock.patch.dict(os.environ, {"WWAI_SOFT_QUALITY_GATES": "1" if soft else "0"}):
        yield


def _speech_activity(value):
    # estimate_speech_activity is imported inside check_speech_activity, so patch its home module.
    return mock.patch("core.audio_chunking.estimate_speech_activity", return_value=value)


class TestAnalyzeClip(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from core.grapheme_to_phoneme import grapheme_to_phoneme

        cls.audio = PL.load_audio(U.SAMPLE_WAV)
        cls.perfect = [list(p) for _, p in grapheme_to_phoneme(U.SAMPLE_TEXT)]

    def test_perfect_reading(self):
        outcome = PL.analyze_clip(self.audio, U.SAMPLE_TEXT.upper(), _ListPhonemes(self.perfect), U.FakeWords())
        self.assertEqual(outcome.status, "ok")
        words = [w for w in outcome.words if w["type"] != "insertion"]
        self.assertEqual(len(words), 9)
        self.assertTrue(all(w["per"] == 0 for w in words))

    def test_gate_rejection_is_an_outcome(self):
        # Soft gates reject digital silence. The legacy hard gates do not (they measure
        # 60 dB SNR and 0% silence on all-zero audio), which Round 0 will quantify.
        silence = np.zeros(32000, dtype=np.float32)
        with mock.patch.dict(os.environ, {"WWAI_SOFT_QUALITY_GATES": "1"}):
            outcome = PL.analyze_clip(silence, U.SAMPLE_TEXT, _ListPhonemes(self.perfect), U.FakeWords())
        self.assertEqual((outcome.status, outcome.error_type), ("rejected", "AudioRejected"))

    def test_stale_cache_propagates(self):
        with self.assertRaises(common.StaleCacheError):
            PL.analyze_clip(self.audio, U.SAMPLE_TEXT, _Raises(common.StaleCacheError("x")), U.FakeWords())

    def test_replayed_error_keeps_original_type(self):
        outcome = PL.analyze_clip(self.audio, U.SAMPLE_TEXT, _Raises(common.ReplayedError("DeepgramTimeout", "slow")), U.FakeWords())
        self.assertEqual(outcome.error_type, "DeepgramTimeout")

    def test_to_dict_keeps_only_scoring_fields(self):
        outcome = PL.analyze_clip(self.audio, U.SAMPLE_TEXT, _ListPhonemes(self.perfect), U.FakeWords())
        record = outcome.to_dict()["words"][0]
        self.assertEqual(set(record), set(PL.RECORD_FIELDS) | {"flagged"})

    def test_flagged_is_cores_decision_on_the_full_record(self):
        import core.phoneme_feedback_formatter as formatter

        full = dict(U.record("fox", ["f", "ɑ", "k", "s"], ["f", "ɑ", "k", "s"], 0), missed=[], extra="display")
        with mock.patch.object(formatter, "is_clear_mistake", return_value=True) as decide:
            compact = PL.compact_record(full)
        decide.assert_called_once()
        self.assertIs(decide.call_args.args[0], full)  # the full record, not the compact one
        self.assertIs(compact["flagged"], True)  # a perfect reading, so only core can have said so
        self.assertNotIn("extra", compact)

    def test_flagged_follows_the_rule_in_force_when_the_outcome_is_stored(self):
        # "fox" read as [m i n t] (four wrong sounds) and "the" as [d ə] (one, PER 0.5).
        misread = [list(p) for p in self.perfect]
        misread[0] = ["d", "ə"]
        misread[3] = ["m", "i", "n", "t"]
        with mock.patch.dict(os.environ, {"WWAI_LEGACY_FEEDBACK": ""}):
            outcome = PL.analyze_clip(self.audio, U.SAMPLE_TEXT, _ListPhonemes(misread), U.FakeWords())
            stored = outcome.to_dict()["words"]
        flagged = {r["ground_truth_word"] for r in stored if r["flagged"]}
        self.assertEqual(flagged, {"fox"})
        self.assertEqual(outcome.feedback["focus_words"][:1], ["fox"])  # the word the feedback corrects
        self.assertTrue(all(type(r["flagged"]) is bool for r in stored))
        with mock.patch.dict(os.environ, {"WWAI_LEGACY_FEEDBACK": "1"}):
            legacy = {r["ground_truth_word"] for r in outcome.to_dict()["words"] if r["flagged"]}
        self.assertEqual(legacy, {"fox", "the"})  # per >= 0.4


    def test_expected_failures_keep_their_own_type(self):
        from core.errors import UpstreamTransientError

        for exc in (ValueError("The audio provided has no speech inside"),
                    UpstreamTransientError("timeout talking to the ASR provider"),
                    common.ReplayedError("DeepgramTimeout", "slow")):
            with self.subTest(exc=type(exc).__name__):
                outcome = PL.analyze_clip(self.audio, U.SAMPLE_TEXT, _Raises(exc), U.FakeWords())
                self.assertEqual(outcome.status, "rejected")
                self.assertFalse(outcome.error_type.startswith("unexpected:"))

    def test_unexpected_failure_is_flagged_but_still_counts_as_rejected(self):
        outcome = PL.analyze_clip(self.audio, U.SAMPLE_TEXT, _Raises(AttributeError("boom")), U.FakeWords())
        self.assertEqual(outcome.status, "rejected")
        self.assertEqual(outcome.error_type, "unexpected:AttributeError")
        # The last ~1000 characters, so the exception line is always there and the head may not be.
        self.assertTrue(outcome.error.rstrip().endswith("AttributeError: boom"))
        self.assertLessEqual(len(outcome.error), 1000)

    def test_unexpected_failure_keeps_the_end_of_a_long_traceback(self):
        outcome = PL.analyze_clip(self.audio, U.SAMPLE_TEXT, _Raises(AttributeError("x" * 5000)), U.FakeWords())
        self.assertEqual(len(outcome.error), 1000)
        self.assertTrue(outcome.error.rstrip().endswith("x" * 50))

    def test_speech_activity_gate_matches_production(self):
        with _speech_activity(20.0):
            with _gates(soft=False):
                outcome = PL.analyze_clip(self.audio, U.SAMPLE_TEXT, _ListPhonemes(self.perfect), U.FakeWords())
                self.assertEqual((outcome.status, outcome.error_type), ("rejected", "AudioRejected"))
                self.assertIn("barely hear you", outcome.error)

                # stage_cache records model outputs for every clip and applies the gates later.
                outcome = PL.analyze_clip(self.audio, U.SAMPLE_TEXT, _ListPhonemes(self.perfect), U.FakeWords(),
                                          apply_gates=False)
                self.assertEqual(outcome.status, "ok")

            with _gates(soft=True):
                outcome = PL.analyze_clip(self.audio, U.SAMPLE_TEXT, _ListPhonemes(self.perfect), U.FakeWords())
                self.assertEqual(outcome.status, "ok")

    def test_speech_activity_gate_runs_before_the_phoneme_model(self):
        model = _Records(self.perfect)
        with _gates(soft=False), _speech_activity(20.0):
            outcome = PL.analyze_clip(self.audio, U.SAMPLE_TEXT, model, U.FakeWords())
        self.assertEqual(outcome.status, "rejected")
        self.assertEqual(model.calls, 0)

    def test_apply_gates_false_lets_digital_silence_reach_the_model(self):
        # Soft gates reject digital silence, so this is the case that proves stage_cache
        # really skips every gate and records what the model says about every clip.
        silence = np.zeros(32000, dtype=np.float32)
        with _gates(soft=True):
            gated = _Records(self.perfect)
            outcome = PL.analyze_clip(silence, U.SAMPLE_TEXT, gated, U.FakeWords())
            self.assertEqual((outcome.status, outcome.error_type), ("rejected", "AudioRejected"))
            self.assertEqual(gated.calls, 0)

            ungated = _Records(self.perfect)
            PL.analyze_clip(silence, U.SAMPLE_TEXT, ungated, U.FakeWords(), apply_gates=False)
            self.assertGreaterEqual(ungated.calls, 1)

    def test_analyze_results_runs_on_the_words(self):
        # A record change that would break production must break the benchmark too.
        import core.process_audio as process_audio

        with mock.patch.object(process_audio, "analyze_results", wraps=process_audio.analyze_results) as spy:
            outcome = PL.analyze_clip(self.audio, U.SAMPLE_TEXT, _ListPhonemes(self.perfect), U.FakeWords())
        self.assertEqual(outcome.status, "ok")
        spy.assert_called_once()
        self.assertEqual(spy.call_args.args[0], outcome.words)

    def test_a_broken_analysis_step_is_flagged(self):
        import core.process_audio as process_audio

        with mock.patch.object(process_audio, "analyze_results", side_effect=KeyError("per")):
            outcome = PL.analyze_clip(self.audio, U.SAMPLE_TEXT, _ListPhonemes(self.perfect), U.FakeWords())
        self.assertEqual((outcome.status, outcome.error_type), ("rejected", "unexpected:KeyError"))

    def test_feedback_is_generated_the_way_the_router_does(self):
        # The router passes analyze_results' outputs to generate_feedback by keyword, with the
        # DataFrame's records as pronunciation_data. Its text is what TTS says to the child.
        import core.phoneme_feedback_formatter as formatter
        import core.process_audio as process_audio

        seen = {}
        real_analyze, real_feedback = process_audio.analyze_results, formatter.generate_feedback

        def analyze(words):
            seen["analysis"] = real_analyze(words)
            return seen["analysis"]

        def feedback(**kwargs):
            seen["kwargs"] = kwargs
            seen["result"] = real_feedback(**kwargs)
            return seen["result"]

        with mock.patch.object(process_audio, "analyze_results", side_effect=analyze), \
                mock.patch.object(formatter, "generate_feedback", side_effect=feedback) as spy:
            outcome = PL.analyze_clip(self.audio, U.SAMPLE_TEXT, _ListPhonemes(self.perfect), U.FakeWords())
        self.assertEqual(outcome.status, "ok")
        spy.assert_called_once()
        self.assertEqual(spy.call_args.args, ())
        df, _highest, problem_summary, per_summary = seen["analysis"]
        self.assertEqual(set(seen["kwargs"]), {"problem_summary", "per_summary", "pronunciation_data"})
        self.assertIs(seen["kwargs"]["problem_summary"], problem_summary)
        self.assertIs(seen["kwargs"]["per_summary"], per_summary)
        self.assertEqual(seen["kwargs"]["pronunciation_data"], df.to_dict("records"))
        self.assertEqual(outcome.feedback, PL.describe_feedback(seen["result"]))

    def test_a_perfect_reading_is_praised(self):
        outcome = PL.analyze_clip(self.audio, U.SAMPLE_TEXT, _ListPhonemes(self.perfect), U.FakeWords())
        self.assertEqual(outcome.feedback, {"kind": "praise", "focus_phoneme": None, "focus_words": []})

    def test_a_misread_word_gets_a_correction_that_names_it(self):
        misread = [list(p) for p in self.perfect]
        misread[3] = ["m", "i", "n", "t"]  # "fox"
        outcome = PL.analyze_clip(self.audio, U.SAMPLE_TEXT, _ListPhonemes(misread), U.FakeWords())
        self.assertEqual(outcome.feedback["kind"], "correction")
        self.assertEqual(outcome.feedback["focus_words"], ["fox"])
        self.assertIn(outcome.feedback["focus_phoneme"], ["f", "ɑ", "k", "s"])

    def test_a_rejected_clip_has_no_feedback(self):
        silence = np.zeros(32000, dtype=np.float32)
        with _gates(soft=True):
            outcome = PL.analyze_clip(silence, U.SAMPLE_TEXT, _ListPhonemes(self.perfect), U.FakeWords())
        self.assertEqual(outcome.status, "rejected")
        self.assertIsNone(outcome.feedback)
        self.assertIsNone(outcome.to_dict()["feedback"])
        failed = PL.analyze_clip(self.audio, U.SAMPLE_TEXT, _Raises(AttributeError("boom")), U.FakeWords())
        self.assertIsNone(failed.to_dict()["feedback"])

    def test_to_dict_stores_the_feedback_and_survives_json(self):
        import json

        misread = [list(p) for p in self.perfect]
        misread[3] = ["m", "i", "n", "t"]
        outcome = PL.analyze_clip(self.audio, U.SAMPLE_TEXT, _ListPhonemes(misread), U.FakeWords())
        stored = outcome.to_dict()
        self.assertEqual(set(stored["feedback"]), {"kind", "focus_phoneme", "focus_words"})
        self.assertEqual(stored["feedback"], outcome.feedback)
        self.assertIsNot(stored["feedback"]["focus_words"], outcome.feedback["focus_words"])
        self.assertEqual(json.loads(json.dumps(stored, ensure_ascii=False)), stored)

    def test_describe_feedback_kinds(self):
        from core.phoneme_feedback_formatter import FeedbackResult

        self.assertEqual(PL.describe_feedback(FeedbackResult("Great job!", "Great job!")),
                         {"kind": "praise", "focus_phoneme": None, "focus_words": []})
        self.assertEqual(PL.describe_feedback(FeedbackResult("Keep practicing!", "Keep practicing!")),
                         {"kind": "generic", "focus_phoneme": None, "focus_words": []})
        correction = FeedbackResult("Watch the 'k' sound in 'cat'.", "...", focus_phoneme="k", focus_words=["cat", "kite"])
        self.assertEqual(PL.describe_feedback(correction),
                         {"kind": "correction", "focus_phoneme": "k", "focus_words": ["cat", "kite"]})

    def test_compact_record_fails_loudly_on_a_missing_field(self):
        full = U.record("fox", ["f", "ɑ", "k", "s"], ["f", "ɑ", "k", "s"], 0)
        self.assertEqual(set(PL.compact_record(full)), set(PL.RECORD_FIELDS) | {"flagged"})
        del full["per"]
        with self.assertRaises(KeyError):
            PL.compact_record(full)

    def test_analyze_clip_refuses_to_run_inside_an_event_loop(self):
        async def call_it():
            return PL.analyze_clip(self.audio, U.SAMPLE_TEXT, _ListPhonemes(self.perfect), U.FakeWords())

        with self.assertRaises(RuntimeError) as ctx:
            asyncio.run(call_it())
        self.assertIn("own event loop", str(ctx.exception))


class _RecordsInputs:
    """A phoneme model and a word model in one, keeping a copy of every audio array it was given."""

    def __init__(self, lists, words):
        self.lists = lists
        self.words = list(words)
        self.phoneme_inputs = []
        self.word_inputs = []

    def extract_phoneme(self, audio, sampling_rate=16000, **_kwargs):
        self.phoneme_inputs.append((np.array(audio, copy=True), sampling_rate))
        return [list(p) for p in self.lists]

    def extract_words(self, audio, sampling_rate=16000, **_kwargs):
        self.word_inputs.append((np.array(audio, copy=True), sampling_rate))
        return list(self.words)


class _WordsOnce:
    """A word model that may be asked once, as a replayed cache entry may."""

    def __init__(self, words):
        self.words = words
        self.calls = 0

    def extract_words(self, audio, sampling_rate=16000, **_kwargs):
        self.calls += 1
        if self.calls > 1:
            raise common.StaleCacheError("the word model was asked twice")
        return None if self.words is None else list(self.words)


class TestClientPath(unittest.TestCase):
    """path="client" mirrors the handler's client branch on the server's own model outputs."""

    @classmethod
    def setUpClass(cls):
        from core.grapheme_to_phoneme import grapheme_to_phoneme

        cls.audio = PL.load_audio(U.SAMPLE_WAV)
        cls.perfect = [list(p) for _, p in grapheme_to_phoneme(U.SAMPLE_TEXT)]

    def _client(self, text, phonemes, words=None, audio=None):
        return PL.analyze_clip(self.audio if audio is None else audio, text, phonemes,
                               words if words is not None else U.FakeWords(), path="client")

    def test_client_phonemes_are_normalized_and_scored_with_the_server_words(self):
        import core.process_audio as process_audio
        from core.grapheme_to_phoneme import clean_sentence, grapheme_to_phoneme
        from routers.handlers.phoneme_processing_handler import normalize_espeak_to_ipa

        # The model's groups, with eSpeak's schwa in "the" so the normalization shows.
        groups = [list(p) for p in self.perfect]
        groups[0] = ["ð", "@"]
        text = U.SAMPLE_TEXT.upper()
        with mock.patch.object(process_audio, "process_audio_with_client_phonemes",
                               wraps=process_audio.process_audio_with_client_phonemes) as client, \
                mock.patch.object(process_audio, "process_audio_array",
                                  wraps=process_audio.process_audio_array) as server:
            outcome = self._client(text, _ListPhonemes(groups))
        self.assertEqual(outcome.status, "ok", outcome.error)
        server.assert_not_called()
        client.assert_called_once()
        kwargs = client.call_args.kwargs
        self.assertEqual(kwargs["client_phonemes"], normalize_espeak_to_ipa(groups))
        self.assertEqual(kwargs["client_phonemes"], self.perfect)
        self.assertEqual(kwargs["client_words"], U.SAMPLE_TEXT.split())
        # The handler's ground truth, built as on the server path (clean_sentence, then G2P).
        self.assertEqual(kwargs["ground_truth_phonemes"], grapheme_to_phoneme(clean_sentence(text)))
        self.assertEqual([w for w, _ in kwargs["ground_truth_phonemes"]], U.SAMPLE_TEXT.split())
        self.assertEqual(kwargs["sampling_rate"], PL.SAMPLE_RATE)
        words = [w for w in outcome.words if w["type"] != "insertion"]
        self.assertEqual(len(words), 9)
        self.assertTrue(all(w["per"] == 0 for w in words))
        self.assertFalse(outcome.client_fallback)
        self.assertIs(outcome.to_dict()["client_fallback"], False)

    def test_the_client_path_now_scores_like_the_server_path(self):
        # The same phonemes, words and ground truth, so ground-truth-anchored scoring gives the
        # same records whichever path they came by. "the" misread mildly, "quick" clearly (three
        # wrong sounds, so the feedback corrects it), and "fox" split by the client.
        groups = [list(p) for p in self.perfect]
        groups[0] = ["d", "ə"]
        groups[1] = ["g", "w", "ɛ", "p"]
        groups[3:4] = [["f", "ɑ"], ["k", "s"]]
        text = U.SAMPLE_TEXT.upper()
        server = PL.analyze_clip(self.audio, text, _ListPhonemes(groups), U.FakeWords())
        client = self._client(text, _ListPhonemes(groups))
        self.assertEqual(client.status, "ok", client.error)
        self.assertEqual(client.to_dict()["words"], server.to_dict()["words"])
        self.assertEqual(client.feedback, server.feedback)
        self.assertEqual(client.feedback["focus_words"][:1], ["quick"])

    def test_a_validation_failure_falls_back_to_the_server_path_and_is_counted(self):
        import core.process_audio as process_audio

        misread = [list(p) for p in self.perfect]
        misread[3] = ["m", "i", "n", "t"]  # "fox"
        server = PL.analyze_clip(self.audio, U.SAMPLE_TEXT, _ListPhonemes(misread), U.FakeWords())
        with mock.patch("routers.handlers.phoneme_processing_handler.validate_client_phonemes",
                        return_value=(False, "Phonemes must be an array")) as validate, \
                mock.patch.object(process_audio, "process_audio_with_client_phonemes") as client:
            outcome = self._client(U.SAMPLE_TEXT, _ListPhonemes(misread))
        validate.assert_called_once_with(misread, U.SAMPLE_TEXT)
        client.assert_not_called()
        self.assertEqual(outcome.status, "ok", outcome.error)
        self.assertTrue(outcome.client_fallback)
        stored = outcome.to_dict()
        self.assertIs(stored["client_fallback"], True)
        # The server path's outcome, from the outputs the models already returned.
        self.assertEqual(stored["words"], server.to_dict()["words"])
        self.assertEqual(stored["feedback"], server.to_dict()["feedback"])

    def test_a_fallback_that_is_then_rejected_is_still_counted(self):
        # One phoneme group: the client path would accept it, but the server path finds no speech.
        with mock.patch("routers.handlers.phoneme_processing_handler.validate_client_phonemes",
                        return_value=(False, "bad")):
            outcome = self._client(U.SAMPLE_TEXT, _ListPhonemes([["ð", "ə", "k"]]))
        self.assertEqual((outcome.status, outcome.error_type), ("rejected", "ValueError"))
        self.assertTrue(outcome.client_fallback)
        self.assertIs(outcome.to_dict()["client_fallback"], True)

    def test_the_models_get_what_they_get_on_the_server_path(self):
        # The cache was recorded on the server path, so replay only works when the client path
        # feeds the models the same arrays, chunk for chunk. Three times the sample is still
        # over the 8 second chunking threshold after preprocessing trims it.
        long_audio = np.concatenate([self.audio] * 3)
        for name, audio in (("short", self.audio), ("chunked", long_audio)):
            with self.subTest(audio=name):
                server = _RecordsInputs(self.perfect, U.SAMPLE_TEXT.split())
                client = _RecordsInputs(self.perfect, U.SAMPLE_TEXT.split())
                PL.analyze_clip(audio, U.SAMPLE_TEXT, server, server)
                PL.analyze_clip(audio, U.SAMPLE_TEXT, client, client, path="client")
                self.assertGreaterEqual(len(server.phoneme_inputs), 2 if name == "chunked" else 1)
                for kind in ("phoneme_inputs", "word_inputs"):
                    got, want = getattr(client, kind), getattr(server, kind)
                    self.assertEqual(len(got), len(want), kind)
                    for (a, sr_a), (b, sr_b) in zip(got, want):
                        self.assertEqual(sr_a, sr_b)
                        self.assertTrue(np.array_equal(a, b), kind)

    def test_a_one_word_text_is_rejected_before_the_models_run(self):
        from core.grapheme_to_phoneme import grapheme_to_phoneme
        from core.process_audio import process_audio_with_client_phonemes

        model = _Records(self.perfect)
        words = _WordsOnce(["cat"])
        outcome = self._client("CAT", model, words)
        self.assertEqual((outcome.status, outcome.error_type), ("rejected", "ValueError"))
        self.assertEqual((model.calls, words.calls), (0, 0))
        # The same message production gives for this ground truth.
        with self.assertRaises(ValueError) as ctx:
            asyncio.run(process_audio_with_client_phonemes(
                client_phonemes=[["k", "æ", "t"]], ground_truth_phonemes=grapheme_to_phoneme("CAT"),
                audio_array=self.audio, word_extraction_model=_WordsOnce(["cat"]), client_words=["cat"]))
        self.assertEqual(outcome.error, str(ctx.exception))

    def test_no_words_from_the_asr_is_scored_without_asking_the_model_again(self):
        # Anchored to the sentence, the ASR words are only hints, so a reading the phoneme
        # model heard is scored even when the ASR heard nothing.
        for words in ([], None):
            with self.subTest(words=words):
                model = _WordsOnce(words)
                outcome = self._client(U.SAMPLE_TEXT, _ListPhonemes(self.perfect), model)
                self.assertEqual(outcome.status, "ok")
                self.assertEqual(model.calls, 1)
                self.assertFalse(outcome.client_fallback)

    def test_no_words_from_the_asr_is_no_speech_on_the_legacy_path(self):
        from unittest import mock
        for words in ([], None):
            with self.subTest(words=words), mock.patch.dict(os.environ, {"WWAI_GT_ANCHORED_ALIGNMENT": "0"}):
                model = _WordsOnce(words)
                outcome = self._client(U.SAMPLE_TEXT, _ListPhonemes(self.perfect), model)
                self.assertEqual((outcome.status, outcome.error_type), ("rejected", "ValueError"))
                self.assertEqual(outcome.error, "The audio provided has no speech inside")
                self.assertEqual(model.calls, 1)
                self.assertFalse(outcome.client_fallback)

    def test_feedback_is_recorded_on_the_client_path(self):
        misread = [list(p) for p in self.perfect]
        misread[3] = ["m", "i", "n", "t"]  # "fox"
        outcome = self._client(U.SAMPLE_TEXT, _ListPhonemes(misread))
        self.assertEqual(outcome.feedback["kind"], "correction")
        self.assertEqual(outcome.feedback["focus_words"], ["fox"])
        self.assertEqual(self._client(U.SAMPLE_TEXT, _ListPhonemes(self.perfect)).feedback["kind"], "praise")

    def test_gate_rejections_happen_on_the_client_path_too(self):
        silence = np.zeros(32000, dtype=np.float32)
        with _gates(soft=True):
            outcome = self._client(U.SAMPLE_TEXT, _ListPhonemes(self.perfect), audio=silence)
        self.assertEqual((outcome.status, outcome.error_type), ("rejected", "AudioRejected"))

    def test_the_server_path_never_falls_back(self):
        outcome = PL.analyze_clip(self.audio, U.SAMPLE_TEXT, _ListPhonemes(self.perfect), U.FakeWords())
        self.assertIs(outcome.to_dict()["client_fallback"], False)

    def test_an_unknown_path_is_refused(self):
        with self.assertRaises(ValueError):
            PL.analyze_clip(self.audio, U.SAMPLE_TEXT, _ListPhonemes(self.perfect), U.FakeWords(), path="browser")


if __name__ == "__main__":
    unittest.main()
