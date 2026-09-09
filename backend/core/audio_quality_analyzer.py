"""
Audio quality analysis module for pre-validation of audio before processing.

This module provides utilities for:
- Signal-to-Noise Ratio (SNR) calculation
- Clipping/distortion detection
- Silence percentage analysis
- Comprehensive quality scoring

Created as part of Phase 1: Adaptive Noise Reduction & Audio Quality Validation
"""

import os

import numpy as np
import librosa
from typing import Dict, Tuple, List, Optional
import logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Feature flag
# ---------------------------------------------------------------------------
# WWAI_SOFT_QUALITY_GATES controls BOTH:
#   1. which measurement method this module uses (legacy head/tail SNR +
#      relative-to-peak clipping vs. robust percentile SNR + absolute
#      full-scale clipping), and
#   2. whether audio_processing_handler treats quality problems as hard HTTP
#      400 rejections or as soft warnings attached to the response.
#
# It defaults to OFF. With the flag unset every number this module produces and
# every rejection the handler raises is identical to the pre-change behavior.
# ---------------------------------------------------------------------------

_TRUTHY = ("1", "true", "yes", "on")


def soft_quality_gates_enabled() -> bool:
    """Return True when WWAI_SOFT_QUALITY_GATES is set to a truthy value.

    Read at call time (not import time) so tests and deployments can toggle it
    without reimporting the module.
    """
    return os.getenv("WWAI_SOFT_QUALITY_GATES", "0").strip().lower() in _TRUTHY


class AudioQualityAnalyzer:
    """Analyzes audio quality metrics before processing."""

    # SNR reported when frame energies are too flat to separate speech from
    # noise (e.g. a pure synthetic tone, or a recording with no pauses at all).
    # Deliberately neutral-positive: an unmeasurable noise floor is not
    # evidence of a bad recording, and must not cause a rejection.
    STATIONARY_SNR_DB = 20.0

    # SNR reported when frame energies are flat AND the waveform is
    # noise-like: speech and background cannot be separated at all.
    NOISE_LIKE_SNR_DB = 3.0

    # Below this peak amplitude the recording is treated as digital silence.
    DIGITAL_SILENCE_PEAK = 1e-6

    def __init__(self, sr: int = 16000, robust_metrics: Optional[bool] = None):
        """
        Initialize the audio quality analyzer.

        Args:
            sr: Sample rate (default 16000 Hz)
            robust_metrics: Force the measurement method. None (default) means
                "follow the WWAI_SOFT_QUALITY_GATES env flag". True selects the
                percentile-noise-floor SNR and absolute full-scale clipping
                detector; False selects the legacy head/tail SNR and
                relative-to-peak clipping detector.
        """
        self.sr = sr
        self._robust_metrics_override = robust_metrics

    @property
    def robust_metrics(self) -> bool:
        """Whether the robust (percentile / absolute-scale) metrics are active."""
        if self._robust_metrics_override is not None:
            return self._robust_metrics_override
        return soft_quality_gates_enabled()

    # ------------------------------------------------------------------
    # Framing helper
    # ------------------------------------------------------------------
    def _frame_rms(self, audio: np.ndarray) -> np.ndarray:
        """Frame-wise RMS energy using 25 ms frames with a 10 ms hop.

        Short frames matter: a child's inter-word gaps and stop closures are
        tens of milliseconds long, and they are what makes a noise-floor
        estimate possible at all.
        """
        frame_length = max(64, int(0.025 * self.sr))
        hop_length = max(16, int(0.010 * self.sr))

        if len(audio) < frame_length:
            # Too short to frame: treat the whole clip as one frame.
            return np.array([float(np.sqrt(np.mean(np.square(audio))))]) if len(audio) else np.array([0.0])

        return librosa.feature.rms(
            y=np.asarray(audio, dtype=np.float64),
            frame_length=frame_length,
            hop_length=hop_length,
            center=True,
        )[0]

    @staticmethod
    def _lag1_autocorrelation(audio: np.ndarray) -> float:
        """Normalized lag-1 autocorrelation. ~1 for tonal/voiced, ~0 for noise."""
        x = np.asarray(audio, dtype=np.float64)
        if len(x) < 2:
            return 0.0
        x = x - float(np.mean(x))
        energy = float(np.dot(x, x))
        if energy <= 0.0:
            return 0.0
        return float(np.dot(x[:-1], x[1:]) / energy)

    # ------------------------------------------------------------------
    # SNR
    # ------------------------------------------------------------------
    def _calculate_snr_percentile(
        self,
        audio: np.ndarray,
        noise_percentile: float = 10.0,
    ) -> float:
        """Robust SNR using a percentile noise floor over the whole recording.

        The legacy method assumed the first and last 0.5 s were noise. A child
        who starts reading the instant the recorder opens puts SPEECH in that
        window, which makes noise_rms ~= signal_rms and reports ~0 dB for a
        perfectly good recording. Estimating the noise floor from the
        lowest-energy frames anywhere in the clip removes that assumption.
        """
        if len(audio) == 0:
            return 0.0

        peak = float(np.max(np.abs(audio)))
        if peak < self.DIGITAL_SILENCE_PEAK:
            logger.warning("No signal detected in audio (digital silence)")
            return 0.0

        frame_rms = self._frame_rms(audio)
        if len(frame_rms) < 3:
            logger.debug("Too few frames for a percentile noise floor; assuming moderate quality")
            return 10.0

        noise_rms = float(np.percentile(frame_rms, noise_percentile))
        loud_rms = float(np.percentile(frame_rms, 95.0))

        if loud_rms < 1e-12:
            logger.warning("No signal detected in audio")
            return 0.0

        if noise_rms < 1e-10:
            # Digital-silence pauses: nothing measurable in the gaps.
            logger.debug("Extremely low noise floor detected - assuming high quality audio")
            return 60.0

        # If the frame energies are essentially flat there are no pauses to
        # measure a noise floor in. Two very different things look like this:
        # a sustained tonal signal (a synthetic test tone, a held vowel), and
        # broadband noise that drowns the speech. Lag-1 autocorrelation tells
        # them apart cheaply - voiced/tonal audio is strongly correlated
        # sample to sample (~0.9+), broadband noise is not (~0).
        if loud_rms / noise_rms < 1.26:  # < 2 dB spread
            correlation = self._lag1_autocorrelation(audio)
            logger.debug(
                "Frame energies are flat (spread %.2f dB, r1=%.2f); noise floor unmeasurable",
                20 * np.log10(max(loud_rms / noise_rms, 1e-12)),
                correlation,
            )
            if correlation >= 0.5:
                # Tonal and steady: no measurable noise floor is not evidence
                # of a bad recording, so do not punish it.
                return float(self.STATIONARY_SNR_DB)
            # Noise-like and steady: speech, if any, is not separable from the
            # background. Report a low (but not zero) SNR.
            return float(self.NOISE_LIKE_SNR_DB)

        # Speech frames: everything at least 6 dB above the noise floor.
        speech_mask = frame_rms > (noise_rms * 2.0)
        if np.any(speech_mask):
            signal_rms = float(np.sqrt(np.mean(np.square(frame_rms[speech_mask]))))
        else:
            signal_rms = loud_rms

        snr_db = 20.0 * np.log10(signal_rms / noise_rms)
        return float(np.clip(snr_db, 0.0, 60.0))

    def calculate_snr(self, audio: np.ndarray, noise_duration: float = 0.5) -> float:
        """
        Calculate Signal-to-Noise Ratio.

        Two methods are available; which one runs is decided by
        `self.robust_metrics` (see WWAI_SOFT_QUALITY_GATES).

        Robust method (flag ON): estimates the noise floor from the
        lowest-energy percentile of frames across the WHOLE recording, so
        speech at the very start or end of the clip does not get counted as
        noise.

        Legacy method (flag OFF, default): assumes the first and last
        noise_duration seconds contain primarily noise.

        Args:
            audio: Input audio signal as numpy array
            noise_duration: Duration in seconds to sample for noise estimation
                (legacy method only; ignored by the robust method)

        Returns:
            SNR in dB. Returns 60.0 for essentially noise-free audio,
            10.0 for very short audio where reliable SNR cannot be calculated.
        """
        if self.robust_metrics:
            return self._calculate_snr_percentile(audio)

        return self._calculate_snr_legacy(audio, noise_duration=noise_duration)

    def _calculate_snr_legacy(self, audio: np.ndarray, noise_duration: float = 0.5) -> float:
        """Original head/tail-window SNR estimate. Preserved verbatim.

        Method: Assumes first and last noise_duration seconds contain primarily
        noise. Calculates RMS of signal vs noise to estimate SNR.
        """
        noise_samples = int(noise_duration * self.sr)

        if len(audio) < 3 * noise_samples:
            # Audio too short for reliable SNR
            logger.debug(f"Audio too short ({len(audio)} samples) for reliable SNR calculation")
            return 10.0  # Assume moderate quality
        
        # Extract noise regions (beginning and end)
        noise_start = audio[:noise_samples]
        noise_end = audio[-noise_samples:]
        noise = np.concatenate([noise_start, noise_end])
        
        # Extract signal region (middle)
        signal = audio[noise_samples:-noise_samples]
        
        # Calculate RMS (Root Mean Square)
        noise_rms = np.sqrt(np.mean(noise**2))
        signal_rms = np.sqrt(np.mean(signal**2))
        
        if noise_rms < 1e-10:
            # Essentially no noise
            logger.debug("Extremely low noise detected - assuming high quality audio")
            return 60.0
        
        if signal_rms < 1e-10:
            # No signal
            logger.warning("No signal detected in audio")
            return 0.0
        
        # SNR in dB
        snr_db = 20 * np.log10(signal_rms / noise_rms)
        
        return float(snr_db)
    
    # ------------------------------------------------------------------
    # Clipping
    # ------------------------------------------------------------------
    @staticmethod
    def _full_scale(audio: np.ndarray) -> float:
        """Digital full scale for this audio buffer.

        Float audio is ±1.0 by convention (soundfile decodes to that range).
        Integer PCM uses the dtype maximum. A float buffer whose peak already
        exceeds 1.0 is not normalized to the usual convention, so fall back to
        its own peak rather than declaring every sample clipped.
        """
        dtype = getattr(audio, "dtype", None)
        if dtype is not None and np.issubdtype(dtype, np.integer):
            return float(np.iinfo(dtype).max)

        peak = float(np.max(np.abs(audio))) if len(audio) else 0.0
        return max(1.0, peak)

    def _detect_clipping_absolute(self, audio: np.ndarray, threshold: float = 0.99) -> Dict:
        """Clipping measured against ABSOLUTE digital full scale.

        The legacy detector compared samples to `threshold * max(|audio|)` --
        the clip's own peak. By construction at least one sample always sits at
        that peak, so any peaky-but-clean recording reports nonzero "clipping".
        Real clipping means samples pinned at the converter's rails, so compare
        against full scale instead, and require a run of consecutive pinned
        samples (a genuine flat top) rather than a single grazing sample.
        """
        if len(audio) == 0:
            return {'is_clipped': False, 'clipping_percentage': 0.0, 'max_amplitude': 0.0}

        max_val = float(np.max(np.abs(audio)))
        full_scale = self._full_scale(audio)

        at_rail = np.abs(audio) >= (threshold * full_scale)

        if not np.any(at_rail):
            clipped_count = 0
        else:
            # Keep only runs of >= 3 consecutive pinned samples. A sine that
            # merely grazes full scale crosses it briefly; a clipped waveform
            # sits there.
            clipped_count = int(np.sum(self._long_runs(at_rail, min_run=3)))

        clipping_percentage = clipped_count / len(audio) * 100

        return {
            'is_clipped': clipping_percentage > 1.0,  # More than 1% clipped = issue
            'clipping_percentage': float(clipping_percentage),
            'max_amplitude': max_val,
        }

    @staticmethod
    def _long_runs(mask: np.ndarray, min_run: int = 3) -> np.ndarray:
        """Boolean mask keeping only runs of at least `min_run` consecutive Trues."""
        if min_run <= 1 or not np.any(mask):
            return mask

        padded = np.concatenate(([False], mask, [False]))
        diffs = np.diff(padded.astype(np.int8))
        starts = np.flatnonzero(diffs == 1)
        ends = np.flatnonzero(diffs == -1)

        out = np.zeros_like(mask, dtype=bool)
        for start, end in zip(starts, ends):
            if end - start >= min_run:
                out[start:end] = True
        return out

    def detect_clipping(self, audio: np.ndarray, threshold: float = 0.99) -> Dict:
        """
        Detect if audio is clipped/distorted.

        Clipping occurs when audio signal exceeds the maximum representable value,
        causing distortion and loss of information.

        Which detector runs is decided by `self.robust_metrics`
        (see WWAI_SOFT_QUALITY_GATES). Robust: absolute digital full scale.
        Legacy (default): relative to the signal's own peak.

        Args:
            audio: Input audio signal
            threshold: Threshold as fraction of full scale, or of max amplitude
                under the legacy method (default 0.99)

        Returns:
            Dictionary with:
                - is_clipped: bool, True if clipping detected (>1% samples clipped)
                - clipping_percentage: float, percentage of samples that are clipped
                - max_amplitude: float, maximum absolute amplitude in the signal
        """
        if self.robust_metrics:
            return self._detect_clipping_absolute(audio, threshold=threshold)

        # Legacy behavior, preserved verbatim.
        # Find maximum amplitude
        max_val = np.max(np.abs(audio))

        # Count samples near max/min (likely clipped)
        clipped = np.abs(audio) > threshold * max_val
        clipping_percentage = np.sum(clipped) / len(audio) * 100

        return {
            'is_clipped': clipping_percentage > 1.0,  # More than 1% clipped = issue
            'clipping_percentage': float(clipping_percentage),
            'max_amplitude': float(max_val)
        }


    def calculate_silence_percentage(self, audio: np.ndarray, 
                                     threshold_db: int = -40) -> float:
        """
        Calculate percentage of audio that is silence.
        
        Args:
            audio: Input audio signal
            threshold_db: dB threshold below which audio is considered silence
            
        Returns:
            Percentage of audio that is silence (0-100)
        """
        # Calculate frame-wise RMS energy
        frame_length = 2048
        hop_length = 512
        
        rms = librosa.feature.rms(
            y=audio,
            frame_length=frame_length,
            hop_length=hop_length
        )[0]
        
        # Convert to dB
        rms_db = librosa.amplitude_to_db(rms, ref=np.max)
        
        # Count silent frames
        silent_frames = np.sum(rms_db < threshold_db)
        total_frames = len(rms_db)
        
        silence_percentage = (silent_frames / total_frames) * 100
        
        return float(silence_percentage)
    
    def analyze_frequency_spectrum(self, audio: np.ndarray) -> Dict:
        """
        Analyze frequency spectrum to detect noise characteristics.
        
        Args:
            audio: Input audio signal
            
        Returns:
            Dictionary with frequency spectrum statistics:
                - low_freq_energy: Energy in 0-500 Hz (often noise)
                - mid_freq_energy: Energy in 500-4000 Hz (speech range)
                - high_freq_energy: Energy in 4000+ Hz
                - spectral_centroid: Center of mass of spectrum
        """
        # Compute Short-Time Fourier Transform
        stft = np.abs(librosa.stft(audio))
        
        # Convert to frequency bins
        freqs = librosa.fft_frequencies(sr=self.sr)
        
        # Calculate energy in different frequency bands
        low_mask = freqs < 500
        mid_mask = (freqs >= 500) & (freqs < 4000)
        high_mask = freqs >= 4000
        
        low_energy = np.mean(stft[low_mask, :])
        mid_energy = np.mean(stft[mid_mask, :])
        high_energy = np.mean(stft[high_mask, :])
        
        # Calculate spectral centroid
        spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=audio, sr=self.sr))
        
        return {
            'low_freq_energy': float(low_energy),
            'mid_freq_energy': float(mid_energy),
            'high_freq_energy': float(high_energy),
            'spectral_centroid': float(spectral_centroid)
        }
    
    def analyze_audio_quality(self, audio: np.ndarray) -> Dict:
        """
        Comprehensive audio quality analysis.
        
        Performs all quality checks and returns a consolidated report
        with overall quality score and recommendations.
        
        Args:
            audio: Input audio signal
            
        Returns:
            Dictionary containing:
                - snr_db: float, Signal-to-Noise Ratio in dB
                - is_clipped: bool, whether clipping detected
                - clipping_percentage: float, percentage of clipped samples
                - silence_percentage: float, percentage of silent frames
                - quality_score: float, overall quality score (0-100)
                - quality_level: str, quality level ('excellent', 'good', 'fair', 'poor')
                - issues: List[str], list of detected quality issues
                - recommendations: List[str], list of recommendations
        """
        logger.info("Analyzing audio quality...")
        
        # Calculate all metrics
        snr_db = self.calculate_snr(audio)
        clipping_info = self.detect_clipping(audio)
        silence_percentage = self.calculate_silence_percentage(audio)
        
        # Initialize issues and recommendations
        issues = []
        recommendations = []
        
        # Evaluate SNR
        if snr_db < 5:
            issues.append(f"Very low SNR ({snr_db:.1f} dB) - audio is very noisy")
            recommendations.append("Record in a quieter environment or use a better microphone")
        elif snr_db < 10:
            issues.append(f"Low SNR ({snr_db:.1f} dB) - significant background noise")
            recommendations.append("Reduce background noise if possible")
        elif snr_db < 15:
            issues.append(f"Moderate SNR ({snr_db:.1f} dB) - some background noise present")
        
        # Evaluate clipping
        if clipping_info['is_clipped']:
            issues.append(f"Audio clipping detected ({clipping_info['clipping_percentage']:.2f}% of samples)")
            recommendations.append("Reduce microphone gain or speak further from microphone")
        
        # Evaluate silence
        if silence_percentage > 70:
            issues.append(f"Excessive silence ({silence_percentage:.1f}% of audio)")
            recommendations.append("Ensure audio contains actual speech and is not blank")
        elif silence_percentage < 5:
            issues.append("Very little silence - may indicate noise or continuous speech")
        
        # Calculate overall quality score (0-100)
        quality_score = 0.0
        
        # SNR contribution (40 points max)
        snr_score = min(40.0, (snr_db / 30.0) * 40.0)  # SNR of 30+ dB gets full points
        quality_score += snr_score
        
        # Clipping contribution (30 points max)
        if not clipping_info['is_clipped']:
            clipping_score = 30.0
        else:
            clipping_score = max(0.0, 30.0 - clipping_info['clipping_percentage'] * 10)
        quality_score += clipping_score
        
        # Silence contribution (30 points max)
        # Optimal silence is 20-40%
        if 20 <= silence_percentage <= 40:
            silence_score = 30.0
        elif silence_percentage < 20:
            silence_score = max(0.0, 30.0 - (20 - silence_percentage) * 2)
        else:
            silence_score = max(0.0, 30.0 - (silence_percentage - 40) * 2)
        quality_score += silence_score
        
        # Determine quality level
        if quality_score >= 80:
            quality_level = 'excellent'
        elif quality_score >= 60:
            quality_level = 'good'
        elif quality_score >= 40:
            quality_level = 'fair'
        else:
            quality_level = 'poor'
        
        result = {
            'snr_db': snr_db,
            'is_clipped': clipping_info['is_clipped'],
            'clipping_percentage': clipping_info['clipping_percentage'],
            'max_amplitude': clipping_info['max_amplitude'],
            'silence_percentage': silence_percentage,
            'quality_score': quality_score,
            'quality_level': quality_level,
            'issues': issues,
            'recommendations': recommendations,
            # Additive: tells callers/logs which measurement method produced
            # the numbers above. Existing keys are untouched.
            'metrics_mode': 'robust' if self.robust_metrics else 'legacy',
        }
        
        logger.info(f"Audio quality analysis complete: {quality_level} (score: {quality_score:.1f})")
        if issues:
            logger.warning(f"Quality issues detected: {', '.join(issues)}")
        
        return result


def assess_processability(audio: np.ndarray) -> Tuple[bool, Optional[str]]:
    """Decide whether audio is fundamentally unprocessable.

    This is the ONLY thing that should hard-reject a recording when soft
    quality gates are enabled. Everything else -- noise, clipping, long pauses,
    a quiet child -- is a warning, not a refusal.

    Args:
        audio: Input audio signal

    Returns:
        (is_processable, reason). `reason` is None when processable.
    """
    if audio is None or len(audio) == 0:
        return False, "No audio was received. Please try recording again."

    finite = np.isfinite(audio)
    if not np.all(finite):
        return False, "Audio contains invalid samples and could not be read. Please try recording again."

    peak = float(np.max(np.abs(audio)))
    if peak < AudioQualityAnalyzer.DIGITAL_SILENCE_PEAK:
        return False, (
            "No sound was recorded. Please check that the microphone is connected "
            "and allowed, then try again."
        )

    return True, None


def build_quality_warning(quality_info: Dict) -> Optional[Dict]:
    """Turn a quality report into an optional, child-friendly warning payload.

    Returns None when there is nothing worth mentioning. The shape is additive:
    callers attach it under a NEW key and never remove existing ones.
    """
    hints: List[str] = []

    snr_db = quality_info.get('snr_db')
    if snr_db is not None and snr_db < 5.0:
        hints.append("It sounds noisy where you are - somewhere quieter might help.")

    clipping = quality_info.get('clipping_percentage')
    if clipping is not None and clipping > 10.0:
        hints.append("That was very loud - try sitting back a little from the microphone.")

    silence = quality_info.get('silence_percentage')
    if silence is not None and silence > 85.0:
        hints.append("We heard mostly quiet - try speaking a bit closer to the microphone.")

    if not hints:
        return None

    return {
        'quality_level': quality_info.get('quality_level'),
        'quality_score': quality_info.get('quality_score'),
        'snr_db': snr_db,
        'clipping_percentage': clipping,
        'silence_percentage': silence,
        'hints': hints,
        # Kept for parity with the analyzer report; frontend may ignore these.
        'issues': quality_info.get('issues', []),
    }


# Convenience function for quick quality check
def quick_quality_check(audio: np.ndarray, sr: int = 16000) -> Tuple[bool, Dict]:
    """
    Quick audio quality check with pass/fail result.
    
    Args:
        audio: Input audio signal
        sr: Sample rate
        
    Returns:
        Tuple of (is_acceptable, quality_info)
        - is_acceptable: bool, True if audio quality is acceptable for processing
        - quality_info: Dict, detailed quality analysis results
    """
    analyzer = AudioQualityAnalyzer(sr=sr)
    quality_info = analyzer.analyze_audio_quality(audio)
    
    # Define acceptance criteria
    is_acceptable = (
        quality_info['snr_db'] >= 5.0 and  # Minimum SNR
        quality_info['clipping_percentage'] < 5.0 and  # Max 5% clipping
        quality_info['silence_percentage'] < 80.0  # Not too much silence
    )
    
    return is_acceptable, quality_info
