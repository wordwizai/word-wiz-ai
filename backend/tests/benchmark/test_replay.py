import builtins
import json
import os
import tempfile
import unittest

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
        SC.record_clip("u1", self.wav, U.SAMPLE_TEXT, self.cache, U.FakeOnnx(self.processor), U.FakeWords())
        self.audio = PL.load_audio(self.wav)

    def tearDown(self):
        self.tmp.cleanup()

    def _replay(self, entry=None):
        entry = entry or R.CacheEntry(self.cache, "u1")
        return PL.analyze_clip(self.audio, U.SAMPLE_TEXT, R.ReplayPhonemeExtractor(entry, self.processor), R.ReplayWordExtractor(entry))

    def test_replay_matches_a_direct_run(self):
        direct = PL.analyze_clip(self.audio, U.SAMPLE_TEXT, U.FakeOnnxExtractor(self.processor), U.FakeWords())
        self.assertEqual(self._replay().to_dict(), direct.to_dict())
        self.assertEqual(direct.status, "ok")

    def test_replay_is_deterministic(self):
        self.assertEqual(self._replay().to_dict(), self._replay().to_dict())

    def test_changed_input_is_stale(self):
        replay = R.ReplayPhonemeExtractor(R.CacheEntry(self.cache, "u1"), self.processor)
        with self.assertRaises(common.StaleCacheError):
            replay.extract_phoneme(np.ones(16000, dtype=np.float32), 16000)

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
        meta["phoneme_calls"][0]["error_type"] = "DeepgramAuthError"
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
                "input_sha": sha, "error_type": "DeepgramAuthError", "error": "401", "is_value_error": False,
            }

        self._edit_meta(edit)
        replay = R.ReplayPhonemeExtractor(R.CacheEntry(self.cache, "u1"), self.processor, check_inputs=False)
        with self.assertRaises(common.ReplayedError) as ctx:
            replay.extract_phoneme(self.audio)
        self.assertNotIsInstance(ctx.exception, ValueError)

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
    def test_builtin_needing_extra_arguments_stays_a_plain_error_when_not_a_value_error(self):
        def edit(meta):
            sha = meta["word_calls"][0]["input_sha"]
            meta["word_calls"][0] = {
                "input_sha": sha, "error_type": "ExceptionGroup", "error": "x", "is_value_error": False,
            }

        self._edit_meta(edit)
        words = R.ReplayWordExtractor(R.CacheEntry(self.cache, "u1"), check_inputs=False)
        with self.assertRaises(common.ReplayedError) as ctx:
            words.extract_words(self.audio)
        self.assertNotIsInstance(ctx.exception, ValueError)
        self.assertEqual(ctx.exception.error_type, "ExceptionGroup")

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


if __name__ == "__main__":
    unittest.main()
