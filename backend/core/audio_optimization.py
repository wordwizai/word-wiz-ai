"""
Audio preprocessing optimizations for faster phoneme extraction.
"""

import numpy as np
import librosa
from typing import Optional, Tuple
import time


class OptimizedAudioPreprocessor:
    """Optimized audio preprocessing for faster phoneme extraction."""
    
    def __init__(self, target_sr: int = 16000, enable_logging: bool = False):
        self.target_sr = target_sr
        self.enable_logging = enable_logging
    
    def preprocess_audio(self, 
                        audio: np.ndarray, 
                        sr: Optional[int] = None,
                        normalize: bool = True,
                        trim_silence: bool = True) -> Tuple[np.ndarray, int]:
        """
        Optimized audio preprocessing pipeline.
        
        Args:
            audio: Input audio array
            sr: Sample rate of input audio (if None, assumes target_sr)
            normalize: Whether to normalize audio amplitude
            trim_silence: Whether to trim leading/trailing silence
            
        Returns:
            Tuple of (processed_audio, sample_rate)
        """
        start_time = time.time() if self.enable_logging else None
        
        # Handle input sample rate
        if sr is None:
            sr = self.target_sr
        
        # Convert to mono if stereo
        if len(audio.shape) > 1:
            audio = np.mean(audio, axis=1)
        
        # Trim silence (optimized)
        if trim_silence:
            audio = self._fast_trim_silence(audio)
        
        # Ensure audio is not empty
        if len(audio) == 0:
            # Create minimal silence if audio is empty
            audio = np.zeros(int(self.target_sr * 0.1))  # 100ms of silence
        
        # Convert to float32 for model compatibility
        audio = audio.astype(np.float32)
        
        if self.enable_logging and start_time:
            process_time = time.time() - start_time
            print(f"Audio preprocessing took {process_time:.3f}s")
        
        return audio, self.target_sr
    
    def _fast_normalize(self, audio: np.ndarray) -> np.ndarray:
        """Fast audio normalization."""
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            return audio / max_val
        return audio
    
    def _fast_trim_silence(self, audio: np.ndarray, 
                          threshold: float = 0.01,
                          frame_length: int = 512) -> np.ndarray:
        """
        Fast silence trimming using energy-based detection.
        More efficient than librosa.effects.trim for real-time use.
        """
        # Calculate frame-wise energy
        energy = np.array([
            np.sum(audio[i:i+frame_length]**2) 
            for i in range(0, len(audio)-frame_length, frame_length)
        ])
        
        # Find start and end of non-silent regions
        above_threshold = energy > threshold * np.max(energy)
        
        if not np.any(above_threshold):
            # If all frames are below threshold, return original audio
            return audio
        
        # Find first and last non-silent frames
        start_frame = np.argmax(above_threshold)
        end_frame = len(above_threshold) - np.argmax(above_threshold[::-1]) - 1
        
        # Convert frame indices to sample indices
        start_sample = start_frame * frame_length
        end_sample = min((end_frame + 1) * frame_length, len(audio))
        
        return audio[start_sample:end_sample]
    
    def batch_preprocess(self, 
                        audio_list: list, 
                        sr_list: Optional[list] = None) -> list:
        """
        Batch process multiple audio samples efficiently.
        
        Args:
            audio_list: List of audio arrays
            sr_list: List of sample rates (if None, assumes target_sr for all)
            
        Returns:
            List of (processed_audio, sample_rate) tuples
        """
        if sr_list is None:
            sr_list = [self.target_sr] * len(audio_list)
        
        results = []
        start_time = time.time() if self.enable_logging else None
        
        for audio, sr in zip(audio_list, sr_list):
            processed_audio, processed_sr = self.preprocess_audio(
                audio, sr, normalize=True, trim_silence=True
            )
            results.append((processed_audio, processed_sr))
        
        if self.enable_logging and start_time:
            batch_time = time.time() - start_time
            avg_time = batch_time / len(audio_list)
            print(f"Batch processed {len(audio_list)} samples in {batch_time:.3f}s "
                  f"(avg: {avg_time:.3f}s per sample)")
        
        return results


# Convenience function for quick preprocessing
def quick_preprocess_audio(audio: np.ndarray, 
                          sr: int = 16000, 
                          target_sr: int = 16000) -> np.ndarray:
    """
    Quick audio preprocessing function for simple use cases.
    
    Args:
        audio: Input audio array
        sr: Sample rate of input audio
        target_sr: Target sample rate
        
    Returns:
        Processed audio array
    """
    preprocessor = OptimizedAudioPreprocessor(target_sr=target_sr, enable_logging=False)
    processed_audio, _ = preprocessor.preprocess_audio(audio, sr)
    return processed_audio
