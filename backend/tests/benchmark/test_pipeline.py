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


if __name__ == "__main__":
    unittest.main()
