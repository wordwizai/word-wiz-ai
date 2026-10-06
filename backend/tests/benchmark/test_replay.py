import builtins
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
