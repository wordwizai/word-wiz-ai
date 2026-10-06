import json
import os
import tempfile
import unittest
from unittest import mock

import numpy as np

from tests.benchmark import stage_cache as SC
from tests.benchmark import testutil as U


class TestAudioSha(unittest.TestCase):
    def test_deterministic_and_rate_sensitive(self):
        a = np.arange(10, dtype=np.float32)
        self.assertEqual(SC.audio_sha(a, 16000), SC.audio_sha(a.copy(), 16000))
        self.assertNotEqual(SC.audio_sha(a, 16000), SC.audio_sha(a, 8000))
        self.assertNotEqual(SC.audio_sha(a, 16000), SC.audio_sha(a * 2, 16000))


class TestEntryHasWordError(unittest.TestCase):
    def test_error_type_counts(self):
        self.assertTrue(SC.entry_has_word_error({"word_calls": [{"input_sha": "x", "error_type": "TimeoutError"}]}))

    def test_empty_or_missing_words_count(self):
        self.assertTrue(SC.entry_has_word_error({"word_calls": [{"input_sha": "x", "words": []}]}))
        self.assertTrue(SC.entry_has_word_error({"word_calls": [{"input_sha": "x", "words": None}]}))
        self.assertTrue(SC.entry_has_word_error({"word_calls": [{"input_sha": "x"}]}))

    def test_words_present_is_not_an_error(self):
        self.assertFalse(SC.entry_has_word_error({"word_calls": [{"input_sha": "x", "words": ["a", "b"]}]}))

    def test_no_word_calls_is_not_an_error(self):
        self.assertFalse(SC.entry_has_word_error({"word_calls": []}))
        self.assertFalse(SC.entry_has_word_error({}))


class _FailingWords:
    def extract_words(self, audio, sampling_rate=16000, **_kwargs):
        raise TimeoutError("deepgram slow")


class _ValueErrorWords:
    def extract_words(self, audio, sampling_rate=16000, **_kwargs):
        raise ValueError("nope")


class TestRecordClip(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.processor = U.real_processor_or_skip()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = U.make_temp_dataset(self.tmp.name)
        self.wav = os.path.join(self.root, "WAVE", "SPEAKER0002", "000020022.WAV")
        self.cache = os.path.join(self.tmp.name, "cache")

    def tearDown(self):
        self.tmp.cleanup()

    def test_writes_entry(self):
        utt, status, word_error = SC.record_clip(
            "000020022", self.wav, U.SAMPLE_TEXT, self.cache, U.FakeOnnx(self.processor), U.FakeWords()
        )
        self.assertEqual((utt, status, word_error), ("000020022", "ok", False))
        with open(os.path.join(self.cache, "000020022.json"), encoding="utf-8") as fh:
            meta = json.load(fh)
        self.assertEqual(len(meta["phoneme_calls"]), 1)
        self.assertEqual(meta["phoneme_calls"][0]["logits_key"], "logits_0")
        self.assertEqual(meta["word_calls"][0]["words"], U.SAMPLE_TEXT.split())
        with np.load(os.path.join(self.cache, "000020022.npz")) as data:
            self.assertEqual(data["logits_0"].dtype, np.float32)

    def test_word_errors_are_recorded(self):
        _utt, status, word_error = SC.record_clip(
            "000020022", self.wav, U.SAMPLE_TEXT, self.cache, U.FakeOnnx(self.processor), _FailingWords()
        )
        self.assertEqual((status, word_error), ("rejected", True))
        with open(os.path.join(self.cache, "000020022.json"), encoding="utf-8") as fh:
            meta = json.load(fh)
        self.assertEqual(meta["word_calls"][0]["error_type"], "TimeoutError")
        self.assertIs(meta["word_calls"][0]["is_value_error"], False)
        self.assertTrue(SC.entry_has_word_error(meta))

    def test_value_error_is_flagged_so_replay_can_rebuild_it(self):
        SC.record_clip(
            "000020022", self.wav, U.SAMPLE_TEXT, self.cache, U.FakeOnnx(self.processor), _ValueErrorWords()
        )
        with open(os.path.join(self.cache, "000020022.json"), encoding="utf-8") as fh:
            meta = json.load(fh)
        self.assertEqual(meta["word_calls"][0]["error_type"], "ValueError")
        self.assertIs(meta["word_calls"][0]["is_value_error"], True)

    def test_gates_are_not_applied_when_recording(self):
        from core import request_audio

        with mock.patch.object(request_audio, "gate_audio", side_effect=request_audio.AudioRejected("no")):
            _utt, status, _ = SC.record_clip(
                "000020022", self.wav, U.SAMPLE_TEXT, self.cache, U.FakeOnnx(self.processor), U.FakeWords()
            )
        self.assertEqual(status, "ok")  # a gate that would reject was never consulted


if __name__ == "__main__":
    unittest.main()
