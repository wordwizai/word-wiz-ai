import builtins
import copy
import json
import os
import tempfile
import unittest
from unittest import mock

import numpy as np

from tests.benchmark import common
from tests.benchmark import pipeline as PL
from tests.benchmark import replay as R
from tests.benchmark import stage_cache as SC
from tests.benchmark import testutil as U


class TestReplay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.processor = U.real_processor_or_skip()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = U.make_temp_dataset(self.tmp.name)
        self.wav = os.path.join(root, "WAVE", "SPEAKER0002", "000020022.WAV")
        self.cache = os.path.join(self.tmp.name, "cache")
        SC.record_clip("u1", self.wav, U.SAMPLE_TEXT, self.cache, U.fake_onnx_extractor(self.processor), U.FakeWords())
        self.audio = PL.load_audio(self.wav)

    def tearDown(self):
        self.tmp.cleanup()

    def _replay(self, entry=None):
        entry = entry or R.CacheEntry(self.cache, "u1")
        return PL.analyze_clip(self.audio, U.SAMPLE_TEXT, R.ReplayPhonemeExtractor(entry, self.processor), R.ReplayWordExtractor(entry))

    def test_replay_matches_a_direct_run(self):
        direct = PL.analyze_clip(self.audio, U.SAMPLE_TEXT, U.fake_onnx_extractor(self.processor), U.FakeWords())
        self.assertEqual(self._replay().to_dict(), direct.to_dict())
        self.assertEqual(direct.status, "ok")

    def test_replay_is_deterministic(self):
        self.assertEqual(self._replay().to_dict(), self._replay().to_dict())

    def test_changed_input_is_stale(self):
        replay = R.ReplayPhonemeExtractor(R.CacheEntry(self.cache, "u1"), self.processor)
        noise = np.random.default_rng(0).normal(0, 0.1, 16000).astype(np.float32)
        with self.assertRaises(common.StaleCacheError):
            replay.extract_phoneme(noise, 16000)

    def test_changed_trimming_is_stale(self):
        # The extractor trims the audio and runs the feature extractor before the ONNX session.
        # The recorded hash is of the session's input, so a change in either is caught. A hash
        # of what extract_phoneme receives would replay the old logits here without a word.
        from core.audio_optimization import OptimizedAudioPreprocessor

        original = OptimizedAudioPreprocessor.preprocess_audio

        def drop_first_160(self, *args, **kwargs):
            audio, sampling_rate = original(self, *args, **kwargs)
            return audio[160:], sampling_rate

        with mock.patch.object(OptimizedAudioPreprocessor, "preprocess_audio", drop_first_160):
            with self.assertRaises(common.StaleCacheError):
                self._replay()

    def test_replay_runs_the_production_extractor(self):
        from core.phoneme_extractor_onnx import PhonemeExtractorONNX

        replay = R.ReplayPhonemeExtractor(R.CacheEntry(self.cache, "u1"), self.processor)
        self.assertIsInstance(replay, PhonemeExtractorONNX)
        self.assertIsInstance(replay.session, R.ReplaySession)
        for name in ("extract_phoneme", "extract_logits"):
            self.assertIs(getattr(type(replay), name), getattr(PhonemeExtractorONNX, name))

    def test_extra_session_call_is_stale(self):
        session = R.ReplaySession(R.CacheEntry(self.cache, "u1"), check_inputs=False)
        feeds = {"input_values": np.zeros((1, 100), dtype=np.float32)}
        session.run(None, feeds)
        with self.assertRaises(common.StaleCacheError):
            session.run(None, feeds)

    def test_extra_call_is_stale(self):
        entry = R.CacheEntry(self.cache, "u1")
        words = R.ReplayWordExtractor(entry, check_inputs=False)
        words.extract_words(self.audio)
        with self.assertRaises(common.StaleCacheError):
            words.extract_words(self.audio)

    def test_missing_entry_is_stale(self):
        with self.assertRaises(common.StaleCacheError):
            R.CacheEntry(self.cache, "nope")

    def test_malformed_entry_is_stale(self):
        path = os.path.join(self.cache, "u1.json")
        for text in ("{", json.dumps({"utt_id": "u1"}), json.dumps({"phoneme_calls": [], "word_calls": "x"}),
                     json.dumps(["not", "a", "dict"])):
            with self.subTest(text=text):
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(text)
                with self.assertRaises(common.StaleCacheError):
                    R.CacheEntry(self.cache, "u1")

    def test_entry_takes_its_id_from_the_caller(self):
        self._edit_meta(lambda meta: meta.pop("utt_id"))
        self.assertEqual(R.CacheEntry(self.cache, "u1").utt_id, "u1")

    def test_call_without_an_input_hash_is_stale(self):
        def edit(meta):
            del meta["word_calls"][0]["input_sha"]
            del meta["phoneme_calls"][0]["input_sha"]

        self._edit_meta(edit)
        entry = R.CacheEntry(self.cache, "u1")
        with self.assertRaises(common.StaleCacheError):
            R.ReplayWordExtractor(entry, check_inputs=False).extract_words(self.audio)
        with self.assertRaises(common.StaleCacheError):
            R.ReplaySession(entry, check_inputs=False).run(None, {"input_values": np.zeros((1, 9), np.float32)})

    def test_recorded_errors_replay_with_their_type(self):
        path = os.path.join(self.cache, "u1.json")
        with open(path, encoding="utf-8") as fh:
            meta = json.load(fh)
        meta["word_calls"][0] = {"input_sha": meta["word_calls"][0]["input_sha"], "error_type": "ValueError", "error": "bad"}
        meta["phoneme_calls"][0]["error_type"] = "UpstreamAuthError"
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(meta, fh)
        entry = R.CacheEntry(self.cache, "u1")
        with self.assertRaises(ValueError):
            R.ReplayWordExtractor(entry, check_inputs=False).extract_words(self.audio)
        with self.assertRaises(common.ReplayedError):
            R.ReplayPhonemeExtractor(entry, self.processor, check_inputs=False).extract_phoneme(self.audio)

    def _edit_meta(self, edit):
        path = os.path.join(self.cache, "u1.json")
        with open(path, encoding="utf-8") as fh:
            meta = json.load(fh)
        edit(meta)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(meta, fh)

    def test_recorded_value_error_subclass_replays_as_a_value_error(self):
        # The chunk loop in process_audio_array swallows ValueError, so replay has to keep
        # "was it a ValueError" faithful even for a project exception type the builtins do not know.
        def edit(meta):
            sha = meta["phoneme_calls"][0]["input_sha"]
            meta["phoneme_calls"][0] = {
                "input_sha": sha, "error_type": "EmptyAudioError", "error": "no speech", "is_value_error": True,
            }

        self._edit_meta(edit)
        replay = R.ReplayPhonemeExtractor(R.CacheEntry(self.cache, "u1"), self.processor, check_inputs=False)
        with self.assertRaises(common.ReplayedValueError) as ctx:
            replay.extract_phoneme(self.audio)
        self.assertIsInstance(ctx.exception, ValueError)
        self.assertIsInstance(ctx.exception, common.ReplayedError)
        self.assertEqual(ctx.exception.error_type, "EmptyAudioError")

    def test_recorded_non_value_error_does_not_replay_as_a_value_error(self):
        def edit(meta):
            sha = meta["phoneme_calls"][0]["input_sha"]
            meta["phoneme_calls"][0] = {
                "input_sha": sha, "error_type": "UpstreamTransientError", "error": "timeout", "is_value_error": False,
            }

        self._edit_meta(edit)
        replay = R.ReplayPhonemeExtractor(R.CacheEntry(self.cache, "u1"), self.processor, check_inputs=False)
        with self.assertRaises(common.ReplayedError) as ctx:
            replay.extract_phoneme(self.audio)
        self.assertNotIsInstance(ctx.exception, ValueError)
        self.assertEqual((ctx.exception.error_type, str(ctx.exception)), ("UpstreamTransientError", "timeout"))

    def test_unknown_recorded_error_is_unexpected_not_a_rejection(self):
        # onnxruntime raises its own exception types (Fail, InvalidArgument). A crash like that
        # must never be scored as a rejection a child would see.
        def edit(meta):
            sha = meta["phoneme_calls"][0]["input_sha"]
            meta["phoneme_calls"][0] = {
                "input_sha": sha, "error_type": "Fail", "error": "bad alloc", "is_value_error": False,
            }

        self._edit_meta(edit)
        replay = R.ReplayPhonemeExtractor(R.CacheEntry(self.cache, "u1"), self.processor, check_inputs=False)
        with self.assertRaises(Exception) as ctx:
            replay.extract_phoneme(self.audio)
        self.assertEqual(type(ctx.exception).__name__, "Fail")
        self.assertNotIsInstance(ctx.exception, (ValueError, common.ReplayedError))
        self.assertEqual(str(ctx.exception), "bad alloc")
        outcome = PL.analyze_clip(self.audio, U.SAMPLE_TEXT,
                                  R.ReplayPhonemeExtractor(R.CacheEntry(self.cache, "u1"), self.processor),
                                  R.ReplayWordExtractor(R.CacheEntry(self.cache, "u1")))
        self.assertEqual((outcome.status, outcome.error_type), ("rejected", "unexpected:Fail"))

    def test_builtin_needing_extra_constructor_arguments_replays_as_a_value_error(self):
        # UnicodeDecodeError cannot be built from one message, so it must fall back to the
        # replayed types instead of crashing the replay with a TypeError.
        def edit(meta):
            sha = meta["word_calls"][0]["input_sha"]
            meta["word_calls"][0] = {
                "input_sha": sha, "error_type": "UnicodeDecodeError", "error": "x", "is_value_error": True,
            }

        self._edit_meta(edit)
        words = R.ReplayWordExtractor(R.CacheEntry(self.cache, "u1"), check_inputs=False)
        with self.assertRaises(common.ReplayedValueError) as ctx:
            words.extract_words(self.audio)
        self.assertIsInstance(ctx.exception, ValueError)
        self.assertEqual(ctx.exception.error_type, "UnicodeDecodeError")
        self.assertEqual(ctx.exception.message, "x")

    @unittest.skipUnless(hasattr(builtins, "ExceptionGroup"), "ExceptionGroup needs Python 3.11")
    def test_builtin_needing_extra_arguments_is_unexpected_when_not_a_value_error(self):
        # A live ExceptionGroup is not an expected rejection, so its replay must not be one either.
        def edit(meta):
            sha = meta["word_calls"][0]["input_sha"]
            meta["word_calls"][0] = {
                "input_sha": sha, "error_type": "ExceptionGroup", "error": "x", "is_value_error": False,
            }

        self._edit_meta(edit)
        words = R.ReplayWordExtractor(R.CacheEntry(self.cache, "u1"), check_inputs=False)
        with self.assertRaises(Exception) as ctx:
            words.extract_words(self.audio)
        self.assertNotIsInstance(ctx.exception, (ValueError, common.ReplayedError))
        self.assertEqual(type(ctx.exception).__name__, "ExceptionGroup")

    def test_unknown_recorded_value_error_stays_a_value_error(self):
        # A live ValueError of a type replay cannot rebuild (here numpy's AxisError) was an
        # expected rejection, and the chunk loop swallowed it. Its replay must behave the same.
        def edit(meta):
            sha = meta["word_calls"][0]["input_sha"]
            meta["word_calls"][0] = {
                "input_sha": sha, "error_type": "AxisError", "error": "axis 2 is out of bounds", "is_value_error": True,
            }

        self._edit_meta(edit)
        words = R.ReplayWordExtractor(R.CacheEntry(self.cache, "u1"), check_inputs=False)
        with self.assertRaises(common.ReplayedValueError) as ctx:
            words.extract_words(self.audio)
        self.assertEqual(ctx.exception.error_type, "AxisError")

    def test_missing_logits_file_is_stale_not_a_recorded_error(self):
        os.remove(os.path.join(self.cache, "u1.npz"))
        replay = R.ReplayPhonemeExtractor(R.CacheEntry(self.cache, "u1"), self.processor, check_inputs=False)
        with self.assertRaises(common.StaleCacheError) as ctx:
            replay.extract_phoneme(self.audio)
        self.assertNotIsInstance(ctx.exception, ValueError)
        self.assertIsNotNone(ctx.exception.__cause__)

    def test_missing_logits_key_is_stale(self):
        def edit(meta):
            meta["phoneme_calls"][0]["logits_key"] = "logits_99"

        self._edit_meta(edit)
        replay = R.ReplayPhonemeExtractor(R.CacheEntry(self.cache, "u1"), self.processor, check_inputs=False)
        with self.assertRaises(common.StaleCacheError):
            replay.extract_phoneme(self.audio)

    def test_word_call_without_words_is_stale(self):
        def edit(meta):
            meta["word_calls"][0] = {"input_sha": meta["word_calls"][0]["input_sha"]}

        self._edit_meta(edit)
        words = R.ReplayWordExtractor(R.CacheEntry(self.cache, "u1"), check_inputs=False)
        with self.assertRaises(common.StaleCacheError):
            words.extract_words(self.audio)


def _real_onnx_extractor():
    """A PhonemeExtractorONNX built by its own __init__, with every load patched out."""
    from core.phoneme_extractor_onnx import PhonemeExtractorONNX

    with (
        mock.patch("core.phoneme_extractor_onnx.Wav2Vec2Processor"),
        mock.patch("huggingface_hub.hf_hub_download"),
        mock.patch("onnxruntime.InferenceSession"),
    ):
        return PhonemeExtractorONNX(optimization_config={"model_cache_enabled": False, "warmup_runs": 0})


def _replay_extractor():
    return R.ReplayPhonemeExtractor(mock.Mock(phoneme_calls=[]), mock.Mock())


class TestExtractorsMatchProduction(unittest.TestCase):
    """Replay and the fake build their extractor by hand instead of calling PhonemeExtractorONNX.__init__
    (which loads the model). If __init__ later builds its OptimizedAudioPreprocessor differently, for
    example with a new trimming option, replay would feed the old logits through a different front end
    and report nothing. These tests make that change fail here, by name."""

    #: Set by the constructor from its arguments or the loaded model, not part of the front end.
    SKIPPED_ON_THE_EXTRACTOR = {"config", "model_name"}

    def _same_state(self, real, other, where):
        """Same attribute names, and the same values. Objects are compared by type and their own state."""
        real_state, other_state = vars(real), vars(other)
        self.assertEqual(set(real_state), set(other_state), where)
        for name, value in real_state.items():
            if name == "enable_logging":
                continue  # follows enable_performance_logging, which the replay does not use
            mine = f"{where}.{name}"
            theirs = other_state[name]
            if hasattr(value, "__dict__") and not callable(value):
                self.assertIs(type(value), type(theirs), mine)
                self._same_state(value, theirs, mine)
            else:
                self.assertEqual(value, theirs, mine)

    def _check(self, other, label):
        real = _real_onnx_extractor()
        self.assertLessEqual(set(vars(real)) - self.SKIPPED_ON_THE_EXTRACTOR, set(vars(other)),
                             f"{label} lacks an attribute PhonemeExtractorONNX.__init__ sets")
        self._same_state(real.audio_preprocessor, other.audio_preprocessor, f"{label}.audio_preprocessor")
        self.assertEqual(real._performance_logging, other._performance_logging)

    def test_the_replay_extractor_builds_the_same_front_end(self):
        self._check(_replay_extractor(), "ReplayPhonemeExtractor")

    def test_the_fake_extractor_builds_the_same_front_end(self):
        self._check(U.fake_onnx_extractor(mock.Mock()), "fake_onnx_extractor")

    def test_the_guard_notices_a_new_preprocessor_option(self):
        # What a future change to PhonemeExtractorONNX.__init__ would look like.
        from core import phoneme_extractor_onnx as module

        original = module.OptimizedAudioPreprocessor

        def with_a_new_option(*args, **kwargs):
            preprocessor = original(*args, **kwargs)
            preprocessor.trim_top_db = 20
            return preprocessor

        with mock.patch.object(module, "OptimizedAudioPreprocessor", with_a_new_option):
            real = _real_onnx_extractor()
        replay = _replay_extractor()
        with self.assertRaises(AssertionError):
            self._same_state(real.audio_preprocessor, replay.audio_preprocessor, "audio_preprocessor")

    def test_the_guard_notices_a_new_extractor_attribute(self):
        real = _real_onnx_extractor()
        real.new_option = True
        constructor_sets = set(vars(real)) - self.SKIPPED_ON_THE_EXTRACTOR
        self.assertIn("new_option", constructor_sets - set(vars(_replay_extractor())))

    def test_the_guard_notices_a_changed_nested_value(self):
        real = _real_onnx_extractor()
        replay = _replay_extractor()
        replay.audio_preprocessor.phoneme_trimmer.sr = 8000
        with self.assertRaises(AssertionError):
            self._same_state(real.audio_preprocessor, replay.audio_preprocessor, "audio_preprocessor")


class TestReplayExtractorAttributes(unittest.TestCase):
    def test_a_missing_attribute_says_the_extractor_changed(self):
        replay = _replay_extractor()
        with self.assertRaises(common.StaleCacheError) as ctx:
            replay.some_new_attribute
        self.assertEqual(
            str(ctx.exception),
            "replay extractor has no attribute some_new_attribute: PhonemeExtractorONNX changed; update replay.py",
        )

    def test_attributes_replay_sets_are_unaffected(self):
        replay = _replay_extractor()
        for name in ("processor", "audio_preprocessor", "model_output_processing", "_performance_logging",
                     "session", "entry", "extract_phoneme", "extract_logits", "_model_cache"):
            with self.subTest(name=name):
                getattr(replay, name)
        self.assertIsInstance(replay.session, R.ReplaySession)

    def test_constructor_only_attributes_are_not_set_on_a_replay_extractor(self):
        replay = _replay_extractor()
        for name in ("config", "model_name"):
            with self.subTest(name=name), self.assertRaises(common.StaleCacheError):
                getattr(replay, name)

    def test_a_default_in_getattr_does_not_hide_staleness(self):
        # hasattr and getattr(.., default) only swallow AttributeError, so they cannot be used to
        # probe past the guard.
        with self.assertRaises(common.StaleCacheError):
            getattr(_replay_extractor(), "some_new_attribute", None)

    def test_special_method_probes_still_raise_attribute_error(self):
        # copy, pickle, inspect and asyncio probe instances for dunders such as __setstate__ and
        # __wrapped__. They expect AttributeError, and a RuntimeError would break them.
        replay = _replay_extractor()
        self.assertFalse(hasattr(replay, "__wrapped__"))
        clone = copy.copy(replay)
        self.assertIs(clone.session, replay.session)


def _write_wav(path, audio):
    import soundfile as sf

    sf.write(path, audio, PL.SAMPLE_RATE, subtype="FLOAT")
    return path


class TestChunkedReplay(unittest.TestCase):
    """A long clip takes the chunked path, where a ValueError from one chunk skips that chunk."""

    @classmethod
    def setUpClass(cls):
        cls.processor = U.real_processor_or_skip()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        a = PL.load_audio(U.SAMPLE_WAV)
        pause = np.zeros(12800, dtype=np.float32)
        audio = np.concatenate([a, pause, a, pause, a])  # about 19.8 s, two chunks
        self.wav = _write_wav(os.path.join(self.tmp.name, "long.wav"), audio)
        self.audio = PL.load_audio(self.wav)
        self.cache = os.path.join(self.tmp.name, "cache")

    def tearDown(self):
        self.tmp.cleanup()

    def _extractor(self):
        return U.fake_onnx_extractor(self.processor, fail_on_call=1, exc=ValueError("chunk rejected"))

    def test_a_failed_chunk_replays_like_a_direct_run(self):
        SC.record_clip("long", self.wav, U.SAMPLE_TEXT, self.cache, self._extractor(), U.FakeWords())
        entry = R.CacheEntry(self.cache, "long")
        self.assertEqual(len(entry.phoneme_calls), 2)
        self.assertNotIn("error_type", entry.phoneme_calls[0])
        self.assertEqual(entry.phoneme_calls[1]["error_type"], "ValueError")
        self.assertIs(entry.phoneme_calls[1]["is_value_error"], True)
        self.assertEqual(len(entry.word_calls), 1)  # the failed chunk never reached Deepgram

        direct_extractor = self._extractor()
        direct = PL.analyze_clip(self.audio, U.SAMPLE_TEXT, direct_extractor, U.FakeWords())
        self.assertEqual(direct_extractor.session.calls, 2)  # the gates let it through to both chunks
        replay = PL.analyze_clip(
            self.audio, U.SAMPLE_TEXT, R.ReplayPhonemeExtractor(entry, self.processor), R.ReplayWordExtractor(entry)
        )
        self.assertEqual(replay.to_dict(), direct.to_dict())


class Fail(Exception):
    """Named like onnxruntime's exception for a failed run, which is not a ValueError."""


class TestSessionErrors(unittest.TestCase):
    """A recorded session error replays to the outcome a live run gives."""

    @classmethod
    def setUpClass(cls):
        cls.processor = U.real_processor_or_skip()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cache = os.path.join(self.tmp.name, "cache")
        self.audio = PL.load_audio(U.SAMPLE_WAV)

    def tearDown(self):
        self.tmp.cleanup()

    def _live_and_replay(self, exc):
        def extractor():
            return U.fake_onnx_extractor(self.processor, fail_on_call=0, exc=exc)

        SC.record_clip("u1", U.SAMPLE_WAV, U.SAMPLE_TEXT, self.cache, extractor(), U.FakeWords())
        entry = R.CacheEntry(self.cache, "u1")
        live = PL.analyze_clip(self.audio, U.SAMPLE_TEXT, extractor(), U.FakeWords())
        replay = PL.analyze_clip(self.audio, U.SAMPLE_TEXT, R.ReplayPhonemeExtractor(entry, self.processor),
                                 R.ReplayWordExtractor(entry))
        return entry, live, replay

    def test_a_project_error_replays_with_the_live_type_and_message(self):
        from core.errors import EmptyAudioError

        entry, live, replay = self._live_and_replay(EmptyAudioError("no speech in the recording"))
        self.assertEqual(entry.phoneme_calls[0]["error_type"], "EmptyAudioError")
        self.assertEqual((live.error_type, live.error), ("EmptyAudioError", "no speech in the recording"))
        self.assertEqual(replay.to_dict(), live.to_dict())

    def test_an_unknown_runtime_error_replays_as_unexpected(self):
        entry, live, replay = self._live_and_replay(Fail("onnxruntime could not allocate"))
        self.assertIs(entry.phoneme_calls[0]["is_value_error"], False)
        self.assertEqual(live.error_type, "unexpected:Fail")
        self.assertEqual((replay.status, replay.error_type), (live.status, live.error_type))
        self.assertTrue(replay.error.rstrip().endswith("Fail: onnxruntime could not allocate"))


class TestErrorsBeforeTheSession(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.processor = U.real_processor_or_skip()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.wav = _write_wav(os.path.join(self.tmp.name, "silence.wav"), np.zeros(32000, dtype=np.float32))
        self.audio = PL.load_audio(self.wav)
        self.cache = os.path.join(self.tmp.name, "cache")

    def tearDown(self):
        self.tmp.cleanup()

    def test_an_extractor_error_before_the_model_is_not_a_call_and_recurs_at_replay(self):
        # Digital silence fails inside extract_logits before session.run, so nothing is recorded
        # for the phoneme model. Replay runs the same extractor code and fails the same way.
        SC.record_clip("silence", self.wav, U.SAMPLE_TEXT, self.cache, U.fake_onnx_extractor(self.processor), U.FakeWords())
        entry = R.CacheEntry(self.cache, "silence")
        self.assertEqual(entry.phoneme_calls, [])
        self.assertFalse(os.path.exists(os.path.join(self.cache, "silence.npz")))

        direct = PL.analyze_clip(self.audio, U.SAMPLE_TEXT, U.fake_onnx_extractor(self.processor), U.FakeWords(),
                                 apply_gates=False)
        replay = PL.analyze_clip(self.audio, U.SAMPLE_TEXT, R.ReplayPhonemeExtractor(entry, self.processor),
                                 R.ReplayWordExtractor(entry), apply_gates=False)
        self.assertEqual(direct.status, "rejected")
        self.assertEqual((replay.status, replay.error_type), (direct.status, direct.error_type))


if __name__ == "__main__":
    unittest.main()
