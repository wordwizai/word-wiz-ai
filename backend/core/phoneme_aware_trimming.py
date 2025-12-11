"""
Phoneme-aware audio trimming module.

This module provides intelligent audio trimming that:
- Preserves phonemes at audio boundaries (especially quiet consonants)
- Uses zero-crossing rate for better edge detection
- Adds configurable padding after trimming
- Adapts to audio dynamics

Created as part of Phase 2: Improved Edge Handling & Silence Trimming
"""

import numpy as np
import librosa
from typing import Tuple
import logging

logger = logging.getLogger(__name__)


class PhonemeAwareTrimmer:
    """Smart audio trimming that preserves phonemes."""
    
    def __init__(self, sr: int = 16000):
        """
        Initialize the phoneme-aware trimmer.
        
        Args:
            sr: Sample rate (default 16000 Hz)
        """
        self.sr = sr
        
    def trim_with_padding(self,
                          audio: np.ndarray,
                          top_db: int = 30,
                          padding_ms: int = 150) -> np.ndarray:
        """
        Trim silence with generous padding to preserve phonemes.
        
        This method uses librosa's trim with a more conservative threshold
        and adds padding to ensure initial and final phonemes (especially
        quiet consonants like p, t, k) are not cut off.
        
        Args:
            audio: Input audio signal
            top_db: Threshold in dB below peak for trimming (default 30)
                   Higher values = more aggressive trimming
            padding_ms: Padding to add on each side after trimming (default 150ms)
            
        Returns:
            Trimmed audio with padding
        """
        if len(audio) == 0:
            logger.warning("Empty audio provided to trim_with_padding")
            return audio
        
        logger.debug(f"Trimming audio with top_db={top_db}, padding={padding_ms}ms")
        
        # Use librosa's trim with appropriate threshold
        # More conservative threshold (30dB) than typical (60dB) to preserve phonemes
        trimmed, intervals = librosa.effects.trim(
            audio, 
            top_db=top_db,
            frame_length=2048,
            hop_length=512
        )
        
        # Calculate padding in samples
        padding_samples = int(padding_ms * self.sr / 1000)
        
        # Find original boundaries
        if len(intervals) > 0 and len(intervals.shape) == 2:
            start_idx = max(0, intervals[0, 0] - padding_samples)
            end_idx = min(len(audio), intervals[0, 1] + padding_samples)
            
            result = audio[start_idx:end_idx]
            logger.debug(f"Trimmed from {len(audio)} to {len(result)} samples "
                        f"(start: {start_idx}, end: {end_idx})")
            return result
        
        logger.debug("No trim intervals found, returning trimmed audio")
        return trimmed
    
    def detect_speech_boundaries(self,
                                 audio: np.ndarray,
                                 use_zcr: bool = True,
                                 min_silence_duration: float = 0.3) -> Tuple[int, int]:
        """
        Detect speech boundaries using energy + zero-crossing rate.
        
        More accurate than energy-only detection for identifying quiet consonants
        (p, t, k, f, s, etc.) which have high frequency content but low energy.
        
        Args:
            audio: Input audio signal
            use_zcr: Whether to use zero-crossing rate (default True)
            min_silence_duration: Minimum silence duration in seconds (default 0.3s)
            
        Returns:
            Tuple of (start_sample, end_sample) for speech boundaries
        """
        if len(audio) == 0:
            return 0, 0
        
        frame_length = 2048
        hop_length = 512
        
        # Calculate frame-wise energy (RMS)
        energy = librosa.feature.rms(
            y=audio,
            frame_length=frame_length,
            hop_length=hop_length
        )[0]
        
        if use_zcr:
            # Zero-crossing rate (detects high-frequency sounds like consonants)
            zcr = librosa.feature.zero_crossing_rate(
                audio,
                frame_length=frame_length,
                hop_length=hop_length
            )[0]
            
            # Normalize ZCR to similar range as energy
            zcr_normalized = (zcr - np.min(zcr)) / (np.max(zcr) - np.min(zcr) + 1e-10)
            
            # Combine metrics (weight energy more heavily)
            combined = 0.7 * energy / (np.max(energy) + 1e-10) + 0.3 * zcr_normalized
            logger.debug("Using combined energy + ZCR for boundary detection")
        else:
            combined = energy
            logger.debug("Using energy only for boundary detection")
        
        # Adaptive thresholding based on distribution
        # Use median + std to be robust to outliers
        threshold = np.median(combined) + 0.5 * np.std(combined)
        
        # Find speech regions
        above_threshold = combined > threshold
        
        if not np.any(above_threshold):
            logger.warning("No speech detected above threshold, using full audio")
            return 0, len(audio)
        
        # Find first and last speech frames
        speech_frames = np.where(above_threshold)[0]
        start_frame = speech_frames[0]
        end_frame = speech_frames[-1]
        
        # Convert to samples
        start_sample = start_frame * hop_length
        end_sample = min((end_frame + 1) * hop_length, len(audio))
        
        logger.debug(f"Detected speech boundaries: {start_sample} to {end_sample} "
                    f"({(end_sample - start_sample) / self.sr:.2f}s)")
        
        return start_sample, end_sample
    
    def trim_with_speech_detection(self,
                                   audio: np.ndarray,
                                   padding_ms: int = 150,
                                   use_zcr: bool = True) -> np.ndarray:
        """
        Trim audio using intelligent speech boundary detection.
        
        Combines energy and zero-crossing rate analysis to better detect
        speech boundaries, especially for quiet consonants.
        
        Args:
            audio: Input audio signal
            padding_ms: Padding to add on each side (default 150ms)
            use_zcr: Whether to use zero-crossing rate (default True)
            
        Returns:
            Trimmed audio with padding
        """
        if len(audio) == 0:
            return audio
        
        # Detect speech boundaries
        start_sample, end_sample = self.detect_speech_boundaries(audio, use_zcr=use_zcr)
        
        # Add padding
        padding_samples = int(padding_ms * self.sr / 1000)
        start_padded = max(0, start_sample - padding_samples)
        end_padded = min(len(audio), end_sample + padding_samples)
        
        result = audio[start_padded:end_padded]
        
        logger.info(f"Trimmed audio from {len(audio)} to {len(result)} samples "
                   f"with {padding_ms}ms padding")
        
        return result
    
    def conservative_trim(self,
                         audio: np.ndarray,
                         padding_ms: int = 200) -> np.ndarray:
        """
        Very conservative trimming that prioritizes preserving phonemes.
        
        Only removes obvious silence (>40dB below peak) and adds generous padding.
        Best for ensuring no phonemes are lost, even if it means keeping more silence.
        
        Args:
            audio: Input audio signal
            padding_ms: Padding to add on each side (default 200ms)
            
        Returns:
            Conservatively trimmed audio
        """
        # Use very conservative threshold (40dB = keep almost everything)
        return self.trim_with_padding(audio, top_db=40, padding_ms=padding_ms)


def smart_trim_audio(audio: np.ndarray, 
                    sr: int = 16000,
                    method: str = 'adaptive',
                    padding_ms: int = 150) -> np.ndarray:
    """
    Convenience function for smart audio trimming.
    
    Args:
        audio: Input audio signal
        sr: Sample rate
        method: Trimming method ('adaptive', 'conservative', 'zcr')
               - 'adaptive': Standard trim with padding (good for most cases)
               - 'conservative': Very gentle trimming (for quiet speech)
               - 'zcr': Uses zero-crossing rate (best for preserving consonants)
        padding_ms: Padding in milliseconds
        
    Returns:
        Trimmed audio
    """
    trimmer = PhonemeAwareTrimmer(sr=sr)
    
    if method == 'conservative':
        return trimmer.conservative_trim(audio, padding_ms=padding_ms)
    elif method == 'zcr':
        return trimmer.trim_with_speech_detection(audio, padding_ms=padding_ms, use_zcr=True)
    else:  # 'adaptive' or default
        return trimmer.trim_with_padding(audio, top_db=30, padding_ms=padding_ms)
