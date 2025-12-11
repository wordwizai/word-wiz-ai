"""
Adaptive noise reduction module for phoneme extraction.

This module provides intelligent noise reduction that:
- Adapts parameters based on Signal-to-Noise Ratio (SNR)
- Preserves phonetic features at audio edges
- Uses crossfading to avoid artifacts

Created as part of Phase 1: Adaptive Noise Reduction & Audio Quality Validation
"""

import numpy as np
import noisereduce as nr
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class AdaptiveNoiseReducer:
    """Adaptive noise reduction that preserves phonetic features."""
    
    def __init__(self, sr: int = 16000):
        """
        Initialize the adaptive noise reducer.
        
        Args:
            sr: Sample rate (default 16000 Hz)
        """
        self.sr = sr
        
    def reduce_noise_adaptive(self, 
                             audio: np.ndarray, 
                             snr_db: float,
                             preserve_edges: bool = True,
                             audio_length_seconds: Optional[float] = None) -> np.ndarray:
        """
        Apply adaptive noise reduction based on SNR.
        
        Adjusts noise reduction strength based on audio quality:
        - High SNR (>20 dB): Minimal processing to preserve quality
        - Medium SNR (10-20 dB): Moderate processing
        - Low SNR (<10 dB): More aggressive but careful processing
        
        Args:
            audio: Input audio signal
            snr_db: Signal-to-noise ratio in dB
            preserve_edges: If True, uses gentler reduction on first/last 0.3s
            audio_length_seconds: Duration of audio (calculated if None)
            
        Returns:
            Noise-reduced audio
        """
        if audio_length_seconds is None:
            audio_length_seconds = len(audio) / self.sr
        
        logger.info(f"Applying adaptive noise reduction (SNR: {snr_db:.1f} dB, length: {audio_length_seconds:.1f}s)")
        
        # Determine parameters based on SNR
        if snr_db > 20:
            # High quality audio - minimal processing
            prop_decrease = 0.3
            stationary = False
            logger.debug("High SNR detected - using minimal noise reduction")
        elif snr_db > 10:
            # Medium quality - moderate processing
            prop_decrease = 0.6
            stationary = True
            logger.debug("Medium SNR detected - using moderate noise reduction")
        else:
            # Low quality - more aggressive but with caution
            prop_decrease = 0.8
            stationary = True
            logger.debug("Low SNR detected - using stronger noise reduction")
        
        # Adjust for longer audio to avoid distortion
        if audio_length_seconds > 8:
            logger.info(f"Long audio detected ({audio_length_seconds:.1f}s) - reducing aggressiveness")
            prop_decrease *= 0.7  # Reduce by 30% for long audio
        
        # Apply edge preservation if requested
        if preserve_edges and len(audio) > self.sr:  # At least 1 second
            return self._reduce_noise_with_edge_preservation(
                audio, prop_decrease, stationary
            )
        else:
            # Standard noise reduction for short audio
            return nr.reduce_noise(
                y=audio, 
                sr=self.sr, 
                stationary=stationary,
                prop_decrease=prop_decrease
            )
    
    def _reduce_noise_with_edge_preservation(self,
                                             audio: np.ndarray,
                                             prop_decrease: float,
                                             stationary: bool) -> np.ndarray:
        """
        Apply noise reduction with gentler processing on edges.
        
        Edges (first/last 0.3s) use 50% of the prop_decrease value to
        preserve initial and final phonemes which are often quiet consonants.
        
        Args:
            audio: Input audio signal
            prop_decrease: Base noise reduction strength (0-1)
            stationary: Whether to use stationary noise reduction
            
        Returns:
            Noise-reduced audio with preserved edges
        """
        edge_duration = 0.3  # seconds
        edge_samples = int(edge_duration * self.sr)
        
        if len(audio) <= 2 * edge_samples:
            # Audio too short for edge preservation
            logger.debug("Audio too short for edge preservation - using gentler overall reduction")
            return nr.reduce_noise(
                y=audio,
                sr=self.sr,
                stationary=stationary,
                prop_decrease=prop_decrease * 0.7  # Gentler overall
            )
        
        logger.debug(f"Applying edge-preserving noise reduction (edge duration: {edge_duration}s)")
        
        # Split audio into three segments
        start_edge = audio[:edge_samples]
        middle = audio[edge_samples:-edge_samples]
        end_edge = audio[-edge_samples:]
        
        # Gentler reduction on edges (50% of base strength)
        edge_prop = prop_decrease * 0.5
        
        logger.debug(f"Processing start edge (prop_decrease: {edge_prop:.2f})")
        start_processed = nr.reduce_noise(
            y=start_edge, sr=self.sr, 
            stationary=stationary, prop_decrease=edge_prop
        )
        
        logger.debug(f"Processing end edge (prop_decrease: {edge_prop:.2f})")
        end_processed = nr.reduce_noise(
            y=end_edge, sr=self.sr,
            stationary=stationary, prop_decrease=edge_prop
        )
        
        # Standard reduction on middle
        logger.debug(f"Processing middle segment (prop_decrease: {prop_decrease:.2f})")
        middle_processed = nr.reduce_noise(
            y=middle, sr=self.sr,
            stationary=stationary, prop_decrease=prop_decrease
        )
        
        # Concatenate with crossfade to avoid clicks
        fade_samples = int(0.05 * self.sr)  # 50ms crossfade
        result = self._crossfade_segments(
            [start_processed, middle_processed, end_processed],
            fade_samples=fade_samples
        )
        
        logger.debug("Edge-preserving noise reduction complete")
        return result
    
    def _crossfade_segments(self, 
                           segments: list, 
                           fade_samples: int) -> np.ndarray:
        """
        Apply crossfade between segments to avoid clicks and artifacts.
        
        Args:
            segments: List of audio segments to concatenate
            fade_samples: Number of samples for crossfade
            
        Returns:
            Concatenated audio with smooth transitions
        """
        if len(segments) == 0:
            return np.array([])
        if len(segments) == 1:
            return segments[0]
        
        # Create fade curves
        fade_out = np.linspace(1, 0, fade_samples)
        fade_in = np.linspace(0, 1, fade_samples)
        
        # Start with first segment (minus the fade region at the end)
        result = segments[0][:-fade_samples] if len(segments[0]) > fade_samples else segments[0]
        
        # Process each transition
        for i in range(len(segments) - 1):
            current_segment = segments[i]
            next_segment = segments[i + 1]
            
            # Handle short segments
            if len(current_segment) < fade_samples or len(next_segment) < fade_samples:
                # Just concatenate without crossfade
                result = np.concatenate([result, next_segment])
                continue
            
            # Extract overlapping regions
            current_end = current_segment[-fade_samples:]
            next_start = next_segment[:fade_samples]
            
            # Crossfade
            crossfaded = current_end * fade_out + next_start * fade_in
            
            # Add crossfaded region and rest of next segment
            result = np.concatenate([result, crossfaded, next_segment[fade_samples:]])
        
        return result


def preprocess_audio_adaptive(audio: np.ndarray, 
                              sr: int = 16000,
                              snr_db: Optional[float] = None,
                              preserve_edges: bool = True) -> np.ndarray:
    """
    Convenience function for adaptive audio preprocessing with noise reduction.
    
    If SNR is not provided, it will be estimated from the audio.
    
    Args:
        audio: Input audio signal
        sr: Sample rate
        snr_db: Signal-to-noise ratio in dB (estimated if None)
        preserve_edges: Whether to preserve edges during noise reduction
        
    Returns:
        Preprocessed audio with adaptive noise reduction
    """
    # Estimate SNR if not provided
    if snr_db is None:
        from .audio_quality_analyzer import AudioQualityAnalyzer
        analyzer = AudioQualityAnalyzer(sr=sr)
        snr_db = analyzer.calculate_snr(audio)
        logger.info(f"Estimated SNR: {snr_db:.1f} dB")
    
    # Apply adaptive noise reduction
    reducer = AdaptiveNoiseReducer(sr=sr)
    audio_denoised = reducer.reduce_noise_adaptive(
        audio, 
        snr_db=snr_db,
        preserve_edges=preserve_edges
    )
    
    # Normalize
    max_val = np.max(np.abs(audio_denoised))
    if max_val > 0:
        audio_denoised = audio_denoised / max_val
    
    return audio_denoised
