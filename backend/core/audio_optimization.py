"""
Audio preprocessing optimizations for faster phoneme extraction.

Updated to use phoneme-aware trimming for better edge preservation.
"""

import numpy as np
import librosa
from typing import Optional, Tuple
import time
from .phoneme_aware_trimming import PhonemeAwareTrimmer


class OptimizedAudioPreprocessor:
    """Optimized audio preprocessing for faster phoneme extraction."""
    
    #: Accepted policies for `sr != target_sr`.
    SAMPLE_RATE_POLICIES = ("resample", "error")

    def __init__(self, target_sr: int = 16000, enable_logging: bool = False,
                 use_phoneme_aware_trim: bool = True,
                 sample_rate_policy: str = "resample"):
        """
        Initialize the audio preprocessor.

        Args:
            target_sr: Target sample rate
            enable_logging: Whether to enable performance logging
            use_phoneme_aware_trim: Whether to use new phoneme-aware trimming
                                   (default True). Set to False for legacy behavior.
            sample_rate_policy: What to do when the incoming sample rate differs
                                from ``target_sr``:
                                  "resample" (default) - actually resample to
                                      target_sr, so the returned sample rate is
                                      truthful.
                                  "error" - raise ValueError instead.
                                Previously the mismatch was IGNORED and target_sr
                                was returned regardless, silently mislabeling the
                                audio (a 44.1 kHz clip would be read ~2.75x fast).
                                A mismatch must never fail silently.
        """
        self.target_sr = target_sr
        self.enable_logging = enable_logging
        self.use_phoneme_aware_trim = use_phoneme_aware_trim
        self.sample_rate_policy = self._validate_policy(sample_rate_policy)

        # Initialize phoneme-aware trimmer if enabled
        if self.use_phoneme_aware_trim:
            self.phoneme_trimmer = PhonemeAwareTrimmer(sr=target_sr)
    
    @classmethod
    def _validate_policy(cls, policy: str) -> str:
        if policy not in cls.SAMPLE_RATE_POLICIES:
            raise ValueError(
                f"Unknown sample_rate_policy {policy!r}; "
                f"expected one of {cls.SAMPLE_RATE_POLICIES}"
            )
        return policy

    def preprocess_audio(self,
                        audio: np.ndarray,
                        sr: Optional[int] = None,
                        normalize: bool = False,
                        trim_silence: bool = True,
                        sample_rate_policy: Optional[str] = None) -> Tuple[np.ndarray, int]:
        """
        Optimized audio preprocessing pipeline.

        This stage performs format conditioning only: mono downmix, sample-rate
        reconciliation, silence trimming and float32 cast. Spectral noise
        reduction and peak normalization live in
        ``core.audio_preprocessing.preprocess_audio`` and must not be repeated
        here - see WWAI_SINGLE_PREPROCESS.

        Args:
            audio: Input audio array
            sr: Sample rate of input audio (if None, assumes target_sr). A value
                different from ``target_sr`` is now honoured, not ignored: see
                ``sample_rate_policy``.
            normalize: Whether to peak-normalize audio amplitude. Defaults to
                False, which is what this function actually did historically -
                the parameter used to default to True and then never be read.
                It is now genuinely applied when requested.
            trim_silence: Whether to trim leading/trailing silence
            sample_rate_policy: Per-call override of the instance policy
                ("resample" or "error").

        Returns:
            Tuple of (processed_audio, sample_rate). The returned sample rate is
            now always the true rate of the returned audio.

        Raises:
            ValueError: if `sr` differs from `target_sr` and the effective policy
                is "error", or if an unknown policy is supplied.
        """
        start_time = time.time() if self.enable_logging else None

        policy = self._validate_policy(
            self.sample_rate_policy if sample_rate_policy is None else sample_rate_policy
        )

        # Handle input sample rate
        if sr is None:
            sr = self.target_sr

        # Convert to mono if stereo
        if len(audio.shape) > 1:
            audio = np.mean(audio, axis=1)

        # Reconcile the sample rate HONESTLY. Previously `sr` was accepted and
        # then dropped on the floor while target_sr was returned as though a
        # conversion had happened.
        if int(sr) != int(self.target_sr):
            if policy == "error":
                raise ValueError(
                    f"Sample rate mismatch: audio is {sr} Hz but this preprocessor "
                    f"targets {self.target_sr} Hz. Resample before calling, or use "
                    f"sample_rate_policy='resample'."
                )
            if self.enable_logging:
                print(f"Resampling audio {sr} Hz -> {self.target_sr} Hz")
            audio = librosa.resample(
                np.asarray(audio, dtype=np.float32),
                orig_sr=int(sr),
                target_sr=int(self.target_sr),
            )

        # Trim silence
        if trim_silence:
            if self.use_phoneme_aware_trim:
                # NEW: Use phoneme-aware trimming with padding
                audio = self.phoneme_trimmer.trim_with_speech_detection(
                    audio,
                    padding_ms=200,  # Extra generous padding to preserve edge phonemes (especially final consonants)
                    use_zcr=True     # Use zero-crossing rate for consonant detection
                )
            else:
                # LEGACY: Fast energy-based trimming (may cut phonemes)
                audio = self._fast_trim_silence(audio)
        
        # Ensure audio is not empty
        if len(audio) == 0:
            # Create minimal silence if audio is empty
            audio = np.zeros(int(self.target_sr * 0.1))  # 100ms of silence

        # Peak normalization - opt-in, and now actually performed when asked.
        # Off by default so this stage stays format-conditioning only and does
        # not stack a second normalization on top of audio_preprocessing's.
        if normalize:
            audio = self._fast_normalize(audio)

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
                        sr_list: Optional[list] = None,
                        normalize: bool = False,
                        trim_silence: bool = True) -> list:
        """
        Batch process multiple audio samples efficiently.

        Args:
            audio_list: List of audio arrays
            sr_list: List of sample rates (if None, assumes target_sr for all)
            normalize: Whether to peak-normalize each sample (default False, to
                match single-sample `preprocess_audio`; this call used to pass
                normalize=True to a parameter that did nothing)
            trim_silence: Whether to trim leading/trailing silence

        Returns:
            List of (processed_audio, sample_rate) tuples
        """
        if sr_list is None:
            sr_list = [self.target_sr] * len(audio_list)
        
        results = []
        start_time = time.time() if self.enable_logging else None
        
        for audio, sr in zip(audio_list, sr_list):
            processed_audio, processed_sr = self.preprocess_audio(
                audio, sr, normalize=normalize, trim_silence=trim_silence
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
        sr: Sample rate of input audio. If it differs from `target_sr` the audio
            is genuinely resampled (it used to be silently relabelled).
        target_sr: Target sample rate

    Returns:
        Processed audio array, guaranteed to be at `target_sr`
    """
    preprocessor = OptimizedAudioPreprocessor(target_sr=target_sr, enable_logging=False)
    processed_audio, _ = preprocessor.preprocess_audio(audio, sr)
    return processed_audio
