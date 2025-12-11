"""
Audio quality analysis module for pre-validation of audio before processing.

This module provides utilities for:
- Signal-to-Noise Ratio (SNR) calculation
- Clipping/distortion detection
- Silence percentage analysis
- Comprehensive quality scoring

Created as part of Phase 1: Adaptive Noise Reduction & Audio Quality Validation
"""

import numpy as np
import librosa
from typing import Dict, Tuple, List
import logging

logger = logging.getLogger(__name__)


class AudioQualityAnalyzer:
    """Analyzes audio quality metrics before processing."""
    
    def __init__(self, sr: int = 16000):
        """
        Initialize the audio quality analyzer.
        
        Args:
            sr: Sample rate (default 16000 Hz)
        """
        self.sr = sr
        
    def calculate_snr(self, audio: np.ndarray, noise_duration: float = 0.5) -> float:
        """
        Calculate Signal-to-Noise Ratio.
        
        Method: Assumes first and last noise_duration seconds contain primarily noise.
        Calculates RMS of signal vs noise to estimate SNR.
        
        Args:
            audio: Input audio signal as numpy array
            noise_duration: Duration in seconds to sample for noise estimation
            
        Returns:
            SNR in dB. Returns 60.0 for essentially noise-free audio,
            10.0 for very short audio where reliable SNR cannot be calculated.
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
    
    def detect_clipping(self, audio: np.ndarray, threshold: float = 0.99) -> Dict:
        """
        Detect if audio is clipped/distorted.
        
        Clipping occurs when audio signal exceeds the maximum representable value,
        causing distortion and loss of information.
        
        Args:
            audio: Input audio signal
            threshold: Threshold as fraction of max amplitude (default 0.99)
            
        Returns:
            Dictionary with:
                - is_clipped: bool, True if clipping detected (>1% samples clipped)
                - clipping_percentage: float, percentage of samples that are clipped
                - max_amplitude: float, maximum absolute amplitude in the signal
        """
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
            'recommendations': recommendations
        }
        
        logger.info(f"Audio quality analysis complete: {quality_level} (score: {quality_score:.1f})")
        if issues:
            logger.warning(f"Quality issues detected: {', '.join(issues)}")
        
        return result


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
