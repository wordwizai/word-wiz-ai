"""Quality gates and the single preprocessing pass (core/request_audio.py).

Run from backend/:  PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.test_request_audio -v
"""

import asyncio
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

    def test_hard_gates_reject_with_the_exact_message(self):
        # Mocked reports, because the legacy analyzer measures 60 dB SNR and 0% silence on
        # all-zero audio, so real silence never reaches the hard SNR or silence gates.
        # setUp already unset WWAI_SOFT_QUALITY_GATES, so these are the default hard gates.
        cases = [
            ("low SNR", 2.0, 0.0, 0.0,
             "Audio quality too low (SNR: 2.0 dB). "
             "Please record in a quieter environment or use a better microphone."),
            ("clipping", 20.0, 12.34, 0.0,
             "Audio is severely clipped (12.3% of samples). "
             "Please reduce microphone gain or speak further from the microphone."),
            ("silence", 20.0, 0.0, 90.0,
             "Audio is mostly silence (90.0%). "
             "Please ensure you are speaking into the microphone."),
        ]
        for gate, snr_db, clipping, silence, expected in cases:
            with self.subTest(gate=gate):
                report = {"quality_level": "poor", "quality_score": 10.0, "snr_db": snr_db,
                          "clipping_percentage": clipping, "silence_percentage": silence,
                          "issues": [], "recommendations": []}
                with mock.patch.object(R.AudioQualityAnalyzer, "analyze_audio_quality", return_value=report), \
                     _quiet(), self.assertRaises(R.AudioRejected) as ctx:
                    R.gate_audio(self.speech, self.sr)
                self.assertEqual(str(ctx.exception), expected)

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


class TestHandlerMarksItsPass(unittest.TestCase):
    """The real handler must still mark its preprocessing pass on the event loop.

    asyncio.to_thread runs gate_and_preprocess on a copy of the context. If a future edit
    moved mark_preprocessed() in there, the mark would be silently discarded and later
    stages would preprocess the recording a second time, with nothing else failing.
    """

    @classmethod
    def setUpClass(cls):
        # Same import pattern as TestHandlerGates in test_soft_quality_gates.py.
        os.environ.setdefault("DATABASE_URL", "sqlite://")
        try:
            from routers.handlers.audio_processing_handler import load_and_preprocess_audio_bytes
        except ImportError as exc:
            raise unittest.SkipTest(f"audio_processing_handler not importable ({exc})") from exc
        cls.load = staticmethod(load_and_preprocess_audio_bytes)

    def test_handler_marks_its_preprocessing_pass(self):
        from core.audio_preprocessing import is_marked_preprocessed

        with open(SAMPLE_WAV, "rb") as fh:
            wav_bytes = fh.read()

        async def run():
            arr, _ = await self.load(wav_bytes, "sample.wav", "audio/wav", session_id="test-session")
            return is_marked_preprocessed(arr)  # must be checked inside the same task

        with mock.patch.dict(os.environ, {"WWAI_SINGLE_PREPROCESS": "1"}), _quiet():
            self.assertTrue(asyncio.run(run()))


if __name__ == "__main__":
    unittest.main()
