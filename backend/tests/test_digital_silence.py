"""Recordings containing digital silence must survive preprocessing.

Browsers often deliver the first buffers of a recording as exact zeros.
noisereduce turned those frames into NaN (0/0), normalization spread the NaN
across the whole buffer, and the request failed with "Audio buffer is not
finite everywhere". Run from backend/:

    python -m unittest tests.test_digital_silence
"""

import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.audio_preprocessing import preprocess_audio, reset_preprocessing_state  # noqa: E402

SR = 16000


def speechlike(seconds: float, seed: int = 0) -> np.ndarray:
    """Amplitude-modulated tones plus a faint noise floor, like a quiet mic."""
    rng = np.random.default_rng(seed)
    t = np.arange(int(seconds * SR)) / SR
    voiced = 0.3 * np.sin(2 * np.pi * 220 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 3 * t))
    return (voiced + rng.normal(0, 0.004, t.shape)).astype("float32")


class DigitalSilenceTest(unittest.TestCase):
    def setUp(self):
        reset_preprocessing_state()

    def test_nan_from_noise_reduction_does_not_poison_the_buffer(self):
        # Reproduces the failure seen on real recordings with zero-padded
        # edges: the reducer returns NaN for the silent frames, and
        # normalization used to spread it over every sample.
        pad = int(0.4 * SR)
        audio = np.concatenate([np.zeros(pad, "float32"), speechlike(2.5)])

        def nan_on_silence(self_, a, **kwargs):
            out = np.array(a, copy=True)
            out[:pad] = np.nan
            return out

        from unittest import mock
        from core import audio_preprocessing as ap

        with mock.patch.object(ap.AdaptiveNoiseReducer, "reduce_noise_adaptive", nan_on_silence):
            out = preprocess_audio(audio, sr=SR)
        self.assertTrue(np.all(np.isfinite(out)))
        self.assertTrue(np.all(out[:pad] == 0))
        self.assertAlmostEqual(float(np.max(np.abs(out))), 1.0, places=5)

    def test_zero_padding_stays_finite(self):
        pad = np.zeros(int(0.4 * SR), dtype="float32")
        audio = np.concatenate([pad, speechlike(2.5), pad])
        out = preprocess_audio(audio, sr=SR)
        self.assertTrue(np.all(np.isfinite(out)))
        self.assertGreater(float(np.max(np.abs(out))), 0.5)

    def test_second_pass_stays_finite(self):
        # The handler preprocesses once and process_audio runs another pass.
        pad = np.zeros(int(0.4 * SR), dtype="float32")
        once = preprocess_audio(np.concatenate([pad, speechlike(2.5), pad]), sr=SR)
        twice = preprocess_audio(np.array(once, copy=True), sr=SR)
        self.assertTrue(np.all(np.isfinite(twice)))


if __name__ == "__main__":
    unittest.main()
