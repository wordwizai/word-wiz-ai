"""
Tests for the recalibrated audio quality gates (WWAI_SOFT_QUALITY_GATES).

Covers:
  * the false-rejection case: a child who starts reading at t=0
  * genuinely noisy audio still measuring as low quality
  * a clean, quiet recording measuring ~0% clipping
  * true digital silence still being rejected
  * flag OFF reproducing today's measurements and rejections exactly

Run from the `backend/` directory:

    DATABASE_URL="sqlite://" PYTHONIOENCODING=utf-8 \
      <venv>/python.exe -m unittest tests.test_soft_quality_gates -v

Stdlib unittest only. No network, no model downloads.
"""

import asyncio
import io
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import soundfile as sf

from core.audio_quality_analyzer import (
    AudioQualityAnalyzer,
    assess_processability,
    build_quality_warning,
    soft_quality_gates_enabled,
)

SR = 16000
FLAG = "WWAI_SOFT_QUALITY_GATES"


# ---------------------------------------------------------------------------
# Signal synthesis
# ---------------------------------------------------------------------------

def make_speech_like(
    n_words: int = 5,
    word_s: float = 0.35,
    gap_s: float = 0.12,
    level: float = 0.4,
    noise_level: float = 0.002,
    lead_silence_s: float = 0.0,
    trail_silence_s: float = 0.0,
    seed: int = 7,
) -> np.ndarray:
    """Synthesize a speech-shaped signal: voiced bursts separated by pauses.

    Real speech has inter-word gaps and stop closures; those pauses are what
    makes any noise-floor estimate possible. `lead_silence_s=0.0` models a
    child who starts talking the instant recording begins - the case the
    head/tail SNR estimator gets wrong.
    """
    rng = np.random.default_rng(seed)
    parts = []

    if lead_silence_s > 0:
        parts.append(np.zeros(int(lead_silence_s * SR), dtype=np.float64))

    for i in range(n_words):
        n = int(word_s * SR)
        t = np.arange(n) / SR
        f0 = 130.0 + 20.0 * i
        wave = (
            np.sin(2 * np.pi * f0 * t)
            + 0.5 * np.sin(2 * np.pi * 2 * f0 * t)
            + 0.25 * np.sin(2 * np.pi * 4 * f0 * t)
        )
        wave *= np.hanning(n)  # word envelope
        parts.append(wave)
        if i < n_words - 1:
            parts.append(np.zeros(int(gap_s * SR), dtype=np.float64))

    if trail_silence_s > 0:
        parts.append(np.zeros(int(trail_silence_s * SR), dtype=np.float64))

    audio = np.concatenate(parts)
    peak = np.max(np.abs(audio))
    if peak > 0:
        audio = audio / peak * level

    audio = audio + rng.normal(0.0, noise_level, len(audio))
    return audio.astype(np.float32)


def legacy_snr(audio: np.ndarray, sr: int = SR, noise_duration: float = 0.5) -> float:
    """Independent reimplementation of the ORIGINAL head/tail SNR estimator.

    Used to prove that with the flag off the shipped code returns the exact
    same number it returned before this change.
    """
    noise_samples = int(noise_duration * sr)
    if len(audio) < 3 * noise_samples:
        return 10.0
    noise = np.concatenate([audio[:noise_samples], audio[-noise_samples:]])
    signal = audio[noise_samples:-noise_samples]
    noise_rms = np.sqrt(np.mean(noise ** 2))
    signal_rms = np.sqrt(np.mean(signal ** 2))
    if noise_rms < 1e-10:
        return 60.0
    if signal_rms < 1e-10:
        return 0.0
    return float(20 * np.log10(signal_rms / noise_rms))


def legacy_clipping(audio: np.ndarray, threshold: float = 0.99) -> float:
    """Independent reimplementation of the ORIGINAL relative-to-peak detector."""
    max_val = np.max(np.abs(audio))
    clipped = np.abs(audio) > threshold * max_val
    return float(np.sum(clipped) / len(audio) * 100)


def wav_bytes(audio: np.ndarray, sr: int = SR) -> bytes:
    buf = io.BytesIO()
    sf.write(buf, audio, sr, format="WAV", subtype="PCM_16")
    return buf.getvalue()


class FlagMixin:
    """Helpers for running a block with the feature flag forced on/off."""

    @staticmethod
    def flag_on():
        return mock.patch.dict(os.environ, {FLAG: "1"})

    @staticmethod
    def flag_off():
        env = dict(os.environ)
        env.pop(FLAG, None)
        return mock.patch.dict(os.environ, env, clear=True)


# ---------------------------------------------------------------------------
# Measurement tests
# ---------------------------------------------------------------------------

class TestSnrMeasurement(unittest.TestCase, FlagMixin):

    def setUp(self):
        self.analyzer = AudioQualityAnalyzer(sr=SR)

    def test_speech_starting_at_t0_is_not_rejected(self):
        """THE false-rejection case: speech occupies the assumed noise window."""
        audio = make_speech_like(lead_silence_s=0.0, noise_level=0.002)

        with self.flag_off():
            legacy = self.analyzer.calculate_snr(audio)
        with self.flag_on():
            robust = self.analyzer.calculate_snr(audio)

        print(f"\n  speech@t=0  legacy SNR={legacy:6.1f} dB   robust SNR={robust:6.1f} dB")

        # Today's behavior: the recording is clean, but the estimator reports
        # near-zero SNR because it called the first/last 0.5 s "noise".
        self.assertLess(legacy, 5.0, "expected the legacy estimator to misfire here")
        # Fixed behavior: comfortably above the 5 dB gate.
        self.assertGreater(robust, 15.0)

    def test_legacy_needs_silence_at_BOTH_edges(self):
        """The legacy estimator only works when both edges happen to be silent.

        Silence at the start alone is not enough: a recording that ends on the
        last word still puts speech in the assumed trailing noise window.
        """
        lead_only = make_speech_like(lead_silence_s=0.7, noise_level=0.002)
        both_edges = make_speech_like(
            lead_silence_s=0.7, trail_silence_s=0.7, noise_level=0.002
        )

        with self.flag_off():
            legacy_lead_only = self.analyzer.calculate_snr(lead_only)
            legacy_both = self.analyzer.calculate_snr(both_edges)
        with self.flag_on():
            robust_lead_only = self.analyzer.calculate_snr(lead_only)
            robust_both = self.analyzer.calculate_snr(both_edges)

        print(
            f"\n  lead only   legacy SNR={legacy_lead_only:6.1f} dB   "
            f"robust SNR={robust_lead_only:6.1f} dB"
            f"\n  both edges  legacy SNR={legacy_both:6.1f} dB   "
            f"robust SNR={robust_both:6.1f} dB"
        )

        # Still below the 5 dB gate -> still a false rejection today.
        self.assertLess(legacy_lead_only, 5.0)
        # Legacy only recovers when both edges are silent.
        self.assertGreater(legacy_both, 5.0)
        # The robust estimator does not care where the silence sits.
        self.assertGreater(robust_lead_only, 15.0)
        self.assertGreater(robust_both, 15.0)

    def test_genuinely_noisy_audio_still_reads_as_low_quality(self):
        """Heavy broadband noise must still be detected by the robust method."""
        audio = make_speech_like(lead_silence_s=0.0, level=0.35, noise_level=0.30)

        with self.flag_on():
            robust = self.analyzer.calculate_snr(audio)
            report = self.analyzer.analyze_audio_quality(audio)

        print(f"\n  noisy       robust SNR={robust:6.1f} dB  level={report['quality_level']}")
        self.assertLess(robust, 10.0)
        self.assertIn(report['quality_level'], ('poor', 'fair'))
        self.assertTrue(report['issues'], "noisy audio should raise at least one issue")

    def test_digital_silence_reads_zero_snr(self):
        audio = np.zeros(int(2.0 * SR), dtype=np.float32)
        with self.flag_on():
            self.assertEqual(self.analyzer.calculate_snr(audio), 0.0)

    def test_pure_tone_without_pauses_is_not_punished(self):
        """A stationary signal has no measurable noise floor - do not reject it."""
        t = np.arange(int(2.0 * SR)) / SR
        audio = (0.4 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
        with self.flag_on():
            robust = self.analyzer.calculate_snr(audio)
        print(f"\n  pure tone   robust SNR={robust:6.1f} dB")
        self.assertGreaterEqual(robust, 5.0)


class TestClippingMeasurement(unittest.TestCase, FlagMixin):

    def setUp(self):
        self.analyzer = AudioQualityAnalyzer(sr=SR)

    def test_clean_quiet_recording_has_near_zero_clipping(self):
        audio = make_speech_like(level=0.25, noise_level=0.001)

        with self.flag_off():
            legacy = self.analyzer.detect_clipping(audio)
        with self.flag_on():
            robust = self.analyzer.detect_clipping(audio)

        print(
            f"\n  quiet clip  legacy={legacy['clipping_percentage']:.4f}%   "
            f"robust={robust['clipping_percentage']:.4f}%   peak={robust['max_amplitude']:.3f}"
        )

        # Today: nonzero, purely because samples near the clip's OWN peak count.
        self.assertGreater(legacy['clipping_percentage'], 0.0)
        # Fixed: nothing is anywhere near digital full scale.
        self.assertEqual(robust['clipping_percentage'], 0.0)
        self.assertFalse(robust['is_clipped'])
        # Return-dict keys are preserved.
        self.assertEqual(
            set(robust.keys()), {'is_clipped', 'clipping_percentage', 'max_amplitude'}
        )

    def test_actually_clipped_audio_is_still_detected(self):
        audio = make_speech_like(level=1.0, noise_level=0.001)
        audio = np.clip(audio * 3.0, -1.0, 1.0).astype(np.float32)

        with self.flag_on():
            robust = self.analyzer.detect_clipping(audio)

        print(f"\n  clipped     robust={robust['clipping_percentage']:.2f}%")
        self.assertTrue(robust['is_clipped'])
        self.assertGreater(robust['clipping_percentage'], 10.0)


class TestProcessability(unittest.TestCase):

    def test_empty_audio_is_unprocessable(self):
        ok, reason = assess_processability(np.array([], dtype=np.float32))
        self.assertFalse(ok)
        self.assertIsInstance(reason, str)

    def test_digital_silence_is_unprocessable(self):
        ok, reason = assess_processability(np.zeros(SR, dtype=np.float32))
        self.assertFalse(ok)
        self.assertIn("No sound", reason)

    def test_nan_audio_is_unprocessable(self):
        audio = np.zeros(SR, dtype=np.float32)
        audio[10] = np.nan
        ok, _ = assess_processability(audio)
        self.assertFalse(ok)

    def test_ordinary_recording_is_processable(self):
        ok, reason = assess_processability(make_speech_like())
        self.assertTrue(ok)
        self.assertIsNone(reason)

    def test_warning_is_none_for_good_audio(self):
        analyzer = AudioQualityAnalyzer(sr=SR, robust_metrics=True)
        report = analyzer.analyze_audio_quality(make_speech_like(noise_level=0.002))
        self.assertIsNone(build_quality_warning(report))

    def test_warning_has_hints_for_noisy_audio(self):
        analyzer = AudioQualityAnalyzer(sr=SR, robust_metrics=True)
        report = analyzer.analyze_audio_quality(
            make_speech_like(level=0.3, noise_level=0.35)
        )
        warning = build_quality_warning(report)
        self.assertIsNotNone(warning)
        self.assertTrue(warning['hints'])


# ---------------------------------------------------------------------------
# Flag semantics
# ---------------------------------------------------------------------------

class TestFlagDefaults(unittest.TestCase, FlagMixin):

    def test_flag_defaults_off(self):
        with self.flag_off():
            self.assertFalse(soft_quality_gates_enabled())

    def test_flag_reads_truthy_values(self):
        for value in ("1", "true", "TRUE", "yes", "on"):
            with mock.patch.dict(os.environ, {FLAG: value}):
                self.assertTrue(soft_quality_gates_enabled(), value)
        for value in ("0", "false", "no", "off", ""):
            with mock.patch.dict(os.environ, {FLAG: value}):
                self.assertFalse(soft_quality_gates_enabled(), value)

    def test_flag_off_reproduces_legacy_measurements_exactly(self):
        analyzer = AudioQualityAnalyzer(sr=SR)
        for label, audio in (
            ("speech@t0", make_speech_like(lead_silence_s=0.0)),
            ("speech+lead", make_speech_like(lead_silence_s=0.7)),
            ("quiet", make_speech_like(level=0.2)),
            ("noisy", make_speech_like(level=0.3, noise_level=0.3)),
            ("short", make_speech_like(n_words=1, word_s=0.4)),
        ):
            with self.flag_off():
                self.assertAlmostEqual(
                    analyzer.calculate_snr(audio), legacy_snr(audio), places=9,
                    msg=f"SNR drifted for {label}",
                )
                self.assertAlmostEqual(
                    analyzer.detect_clipping(audio)['clipping_percentage'],
                    legacy_clipping(audio), places=9,
                    msg=f"clipping drifted for {label}",
                )

    def test_report_keys_are_preserved_in_both_modes(self):
        required = {
            'snr_db', 'is_clipped', 'clipping_percentage', 'max_amplitude',
            'silence_percentage', 'quality_score', 'quality_level',
            'issues', 'recommendations',
        }
        audio = make_speech_like()
        for ctx in (self.flag_off(), self.flag_on()):
            with ctx:
                report = AudioQualityAnalyzer(sr=SR).analyze_audio_quality(audio)
                self.assertTrue(required.issubset(report.keys()))


# ---------------------------------------------------------------------------
# Handler-level gate behavior (real code path, no network)
# ---------------------------------------------------------------------------

class TestHandlerGates(unittest.TestCase, FlagMixin):
    """Drives load_and_preprocess_audio_bytes end to end with synthetic WAVs."""

    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("DATABASE_URL", "sqlite://")
        from fastapi import HTTPException  # noqa: WPS433
        from routers.handlers.audio_processing_handler import (  # noqa: WPS433
            load_and_preprocess_audio_bytes,
        )
        cls.HTTPException = HTTPException
        cls.load = staticmethod(load_and_preprocess_audio_bytes)

    def run_handler(self, audio, quality_out=None):
        return asyncio.run(
            self.load(
                wav_bytes(audio),
                "test.wav",
                "audio/wav",
                "test-session",
                quality_out=quality_out,
            )
        )

    def test_flag_off_rejects_speech_starting_at_t0(self):
        """Documents today's false rejection. Must keep failing with the flag off."""
        audio = make_speech_like(lead_silence_s=0.0, noise_level=0.002)
        with self.flag_off():
            with self.assertRaises(self.HTTPException) as ctx:
                self.run_handler(audio)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("SNR", ctx.exception.detail)
        print(f"\n  flag OFF -> 400: {ctx.exception.detail[:60]}...")

    def test_flag_on_accepts_speech_starting_at_t0(self):
        audio = make_speech_like(lead_silence_s=0.0, noise_level=0.002)
        quality_out = {}
        with self.flag_on():
            processed, session_id = self.run_handler(audio, quality_out)
        self.assertGreater(len(processed), 0)
        self.assertEqual(session_id, "test-session")
        self.assertEqual(quality_out['quality_info']['metrics_mode'], 'robust')
        self.assertIsNone(quality_out.get('quality_warning'))
        print(f"\n  flag ON  -> accepted, SNR={quality_out['quality_info']['snr_db']:.1f} dB")

    def test_flag_on_accepts_noisy_audio_with_a_warning(self):
        audio = make_speech_like(lead_silence_s=0.0, level=0.3, noise_level=0.35)
        quality_out = {}
        with self.flag_on():
            processed, _ = self.run_handler(audio, quality_out)
        self.assertGreater(len(processed), 0)
        warning = quality_out.get('quality_warning')
        self.assertIsNotNone(warning, "noisy audio should carry a warning, not a rejection")
        self.assertTrue(warning['hints'])
        print(f"\n  flag ON  -> noisy accepted with hint: {warning['hints'][0]}")

    def test_flag_on_still_rejects_digital_silence(self):
        audio = np.zeros(int(2.0 * SR), dtype=np.float32)
        with self.flag_on():
            with self.assertRaises(self.HTTPException) as ctx:
                self.run_handler(audio)
        self.assertEqual(ctx.exception.status_code, 400)
        print(f"\n  flag ON  -> silence rejected: {ctx.exception.detail[:60]}...")

    def test_flag_on_still_rejects_audio_that_is_too_short(self):
        audio = make_speech_like(n_words=1, word_s=0.2, gap_s=0.0)
        with self.flag_on():
            with self.assertRaises(self.HTTPException) as ctx:
                self.run_handler(audio)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("too short", ctx.exception.detail)

    def test_quality_out_is_optional(self):
        """Callers that do not pass quality_out keep the old two-tuple contract."""
        audio = make_speech_like(lead_silence_s=0.0, noise_level=0.002)
        with self.flag_on():
            result = self.run_handler(audio)
        self.assertEqual(len(result), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
