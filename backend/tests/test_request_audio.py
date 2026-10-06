"""Quality gates and the single preprocessing pass (core/request_audio.py).

Run from backend/:  PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.test_request_audio -v
"""

import contextlib
import io
import os
import sys
import unittest
from unittest import mock

import numpy as np
import soundfile as sf

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from core import request_audio as R  # noqa: E402

SAMPLE_WAV = os.path.join(BACKEND_ROOT, "tests", "system", "test_case_02", "audio.wav")


def _quiet():
    return contextlib.redirect_stdout(io.StringIO())


class TestGates(unittest.TestCase):
    def setUp(self):
        self._saved = os.environ.pop("WWAI_SOFT_QUALITY_GATES", None)
        self.speech, self.sr = sf.read(SAMPLE_WAV, dtype="float32")

    def tearDown(self):
        os.environ.pop("WWAI_SOFT_QUALITY_GATES", None)
        if self._saved is not None:
            os.environ["WWAI_SOFT_QUALITY_GATES"] = self._saved

    def test_real_speech_passes_hard_gates(self):
        out = {}
        with _quiet():
            info = R.gate_audio(self.speech, self.sr, quality_out=out)
        self.assertIn("snr_db", info)
        self.assertIs(out["quality_info"], info)

    def test_hard_gates_reject_low_snr(self):
        # Mocked report: the legacy analyzer measures 60 dB SNR and 0% silence on
        # all-zero audio, so real silence does not reach the hard SNR/silence gates.
        report = {"quality_level": "poor", "quality_score": 10.0, "snr_db": 2.0,
                  "clipping_percentage": 0.0, "silence_percentage": 0.0,
                  "issues": [], "recommendations": []}
        with mock.patch.object(R.AudioQualityAnalyzer, "analyze_audio_quality", return_value=report), \
             _quiet(), self.assertRaises(R.AudioRejected) as ctx:
            R.gate_audio(self.speech, self.sr)
        self.assertIn("SNR", str(ctx.exception))

    def test_digital_silence_rejected_by_soft_gates(self):
        os.environ["WWAI_SOFT_QUALITY_GATES"] = "1"
        with _quiet(), self.assertRaises(R.AudioRejected):
            R.gate_audio(np.zeros(32000, dtype=np.float32), 16000)

    def test_rejection_is_a_value_error(self):
        self.assertTrue(issubclass(R.AudioRejected, ValueError))

    def test_gate_and_preprocess_runs_the_production_pass(self):
        from core.audio_preprocessing import preprocess_audio

        with _quiet():
            out = R.gate_and_preprocess(self.speech, self.sr)
            direct = preprocess_audio(self.speech, sr=self.sr, audio_length_seconds=len(self.speech) / self.sr,
                                      use_adaptive=True, already_preprocessed=False)
        self.assertTrue(np.array_equal(out, direct))
        self.assertAlmostEqual(float(np.max(np.abs(out))), 1.0, places=5)
        self.assertLessEqual(len(out), len(self.speech))  # preprocessing trims edge audio

    def test_apply_gates_false_skips_the_gates(self):
        with mock.patch.object(R, "gate_audio") as gate, _quiet():
            R.gate_and_preprocess(self.speech, self.sr, apply_gates=False)
        gate.assert_not_called()


if __name__ == "__main__":
    unittest.main()
