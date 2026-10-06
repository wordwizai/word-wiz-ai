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
    """Hard gates (the default) or soft gates, whatever the environment says."""
    with mock.patch.dict(os.environ):
        os.environ.pop("WWAI_SOFT_QUALITY_GATES", None)
        if soft:
            os.environ["WWAI_SOFT_QUALITY_GATES"] = "1"
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
        self.assertEqual(set(record), set(PL.RECORD_FIELDS))


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

    def test_compact_record_fails_loudly_on_a_missing_field(self):
        full = U.record("fox", ["f", "ɑ", "k", "s"], ["f", "ɑ", "k", "s"], 0)
        self.assertEqual(set(PL.compact_record(full)), set(PL.RECORD_FIELDS))
        del full["per"]
        with self.assertRaises(KeyError):
            PL.compact_record(full)

    def test_analyze_clip_refuses_to_run_inside_an_event_loop(self):
        async def call_it():
            return PL.analyze_clip(self.audio, U.SAMPLE_TEXT, _ListPhonemes(self.perfect), U.FakeWords())

        with self.assertRaises(RuntimeError) as ctx:
            asyncio.run(call_it())
        self.assertIn("own event loop", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
