"""
Device calibration module for device-specific audio optimization.

This module provides:
- Device fingerprinting based on audio characteristics
- Device profile storage and retrieval
- Device-specific preprocessing parameters

Created as part of Phase 4: Device-Specific Optimization
"""

import numpy as np
import librosa
from typing import Dict, List, Optional, Tuple
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class DeviceCalibrator:
    """Calibrate and optimize for specific audio devices."""
    
    def __init__(self):
        """Initialize the device calibrator."""
        self.profiles = {}  # In-memory storage (could be replaced with database)
        
    def fingerprint_device(self, 
                          audio_samples: List[np.ndarray],
                          device_id: str,
                          sr: int = 16000) -> Dict:
        """
        Create fingerprint from multiple audio samples.
        
        Analyzes audio characteristics to create a device profile:
        - Average noise floor
        - Frequency response characteristics
        - Dynamic range
        - Typical clipping threshold
        
        Args:
            audio_samples: List of audio arrays from same device (min 3 recommended)
            device_id: Unique device identifier
            sr: Sample rate
            
        Returns:
            Device profile dictionary
        """
        if len(audio_samples) < 1:
            raise ValueError("At least 1 audio sample required for fingerprinting")
        
        logger.info(f"Creating device fingerprint for {device_id} from {len(audio_samples)} samples")
        
        # Analyze each sample
        noise_floors = []
        spectral_centroids = []
        dynamic_ranges = []
        frequency_responses = []
        
        for audio in audio_samples:
            # Noise floor estimation (RMS of quietest 10%)
            sorted_rms = np.sort(np.abs(audio))
            noise_floor = np.mean(sorted_rms[:int(len(sorted_rms) * 0.1)])
            noise_floors.append(noise_floor)
            
            # Spectral centroid (indicates frequency bias)
            centroid = np.mean(librosa.feature.spectral_centroid(y=audio, sr=sr))
            spectral_centroids.append(centroid)
            
            # Dynamic range
            max_amplitude = np.max(np.abs(audio))
            min_amplitude = np.min(np.abs(audio[audio != 0])) if np.any(audio != 0) else 1e-10
            dynamic_range = 20 * np.log10(max_amplitude / min_amplitude) if min_amplitude > 0 else 0
            dynamic_ranges.append(dynamic_range)
            
            # Frequency response (energy in different bands)
            stft = np.abs(librosa.stft(audio))
            freqs = librosa.fft_frequencies(sr=sr)
            
            # Calculate energy in frequency bands
            low_mask = freqs < 500
            mid_mask = (freqs >= 500) & (freqs < 4000)
            high_mask = freqs >= 4000
            
            low_energy = np.mean(stft[low_mask, :]) if np.any(low_mask) else 0
            mid_energy = np.mean(stft[mid_mask, :]) if np.any(mid_mask) else 0
            high_energy = np.mean(stft[high_mask, :]) if np.any(high_mask) else 0
            
            total_energy = low_energy + mid_energy + high_energy
            if total_energy > 0:
                freq_response = {
                    'low': low_energy / total_energy,
                    'mid': mid_energy / total_energy,
                    'high': high_energy / total_energy
                }
            else:
                freq_response = {'low': 0.33, 'mid': 0.33, 'high': 0.33}
            
            frequency_responses.append(freq_response)
        
        # Aggregate measurements
        profile = {
            'device_id': device_id,
            'created_at': datetime.now().isoformat(),
            'sample_count': len(audio_samples),
            'sample_rate': sr,
            'noise_floor': {
                'mean': float(np.mean(noise_floors)),
                'std': float(np.std(noise_floors)),
                'median': float(np.median(noise_floors))
            },
            'spectral_centroid': {
                'mean': float(np.mean(spectral_centroids)),
                'std': float(np.std(spectral_centroids))
            },
            'dynamic_range': {
                'mean': float(np.mean(dynamic_ranges)),
                'std': float(np.std(dynamic_ranges))
            },
            'frequency_response': {
                'low': float(np.mean([fr['low'] for fr in frequency_responses])),
                'mid': float(np.mean([fr['mid'] for fr in frequency_responses])),
                'high': float(np.mean([fr['high'] for fr in frequency_responses]))
            }
        }
        
        # Store profile
        self.profiles[device_id] = profile
        
        logger.info(f"Device profile created: noise_floor={profile['noise_floor']['mean']:.6f}, "
                   f"centroid={profile['spectral_centroid']['mean']:.0f}Hz, "
                   f"dynamic_range={profile['dynamic_range']['mean']:.1f}dB")
        
        return profile
    
    def get_device_preprocessing_params(self, device_id: str) -> Dict:
        """
        Get optimized preprocessing parameters for device.
        
        Returns device-specific preprocessing parameters based on the device profile.
        
        Args:
            device_id: Unique device identifier
            
        Returns:
            Dictionary of preprocessing parameters
        """
        if device_id not in self.profiles:
            logger.warning(f"No profile found for device {device_id}, using defaults")
            return self._get_default_params()
        
        profile = self.profiles[device_id]
        
        # Derive preprocessing parameters from profile
        noise_floor = profile['noise_floor']['mean']
        centroid = profile['spectral_centroid']['mean']
        dynamic_range = profile['dynamic_range']['mean']
        freq_response = profile['frequency_response']
        
        params = {}
        
        # Noise reduction strength based on noise floor
        if noise_floor > 0.05:
            # High noise floor - more aggressive noise reduction
            params['noise_reduction_strength'] = 0.8
        elif noise_floor > 0.02:
            # Medium noise floor
            params['noise_reduction_strength'] = 0.6
        else:
            # Low noise floor - gentle noise reduction
            params['noise_reduction_strength'] = 0.4
        
        # Trimming threshold based on dynamic range
        if dynamic_range > 60:
            # High dynamic range - can use more aggressive trimming
            params['trim_top_db'] = 35
        elif dynamic_range > 40:
            # Medium dynamic range
            params['trim_top_db'] = 30
        else:
            # Low dynamic range - conservative trimming
            params['trim_top_db'] = 25
        
        # Frequency equalization based on frequency response
        # If device has bass/treble bias, adjust accordingly
        if freq_response['low'] > 0.4:
            params['eq_low_gain'] = 0.8  # Reduce bass
        elif freq_response['low'] < 0.25:
            params['eq_low_gain'] = 1.2  # Boost bass
        else:
            params['eq_low_gain'] = 1.0
        
        if freq_response['high'] > 0.4:
            params['eq_high_gain'] = 0.8  # Reduce treble
        elif freq_response['high'] < 0.25:
            params['eq_high_gain'] = 1.2  # Boost treble
        else:
            params['eq_high_gain'] = 1.0
        
        # Padding based on device characteristics
        # Devices with high noise might need more padding
        if noise_floor > 0.05:
            params['padding_ms'] = 200
        else:
            params['padding_ms'] = 150
        
        logger.info(f"Device-specific params for {device_id}: "
                   f"noise_reduction={params['noise_reduction_strength']:.1f}, "
                   f"trim_top_db={params['trim_top_db']}")
        
        return params
    
    def _get_default_params(self) -> Dict:
        """Get default preprocessing parameters."""
        return {
            'noise_reduction_strength': 0.6,
            'trim_top_db': 30,
            'eq_low_gain': 1.0,
            'eq_high_gain': 1.0,
            'padding_ms': 150
        }
    
    def save_profile(self, device_id: str, filepath: str):
        """
        Save device profile to file.
        
        Args:
            device_id: Device identifier
            filepath: Path to save JSON file
        """
        if device_id not in self.profiles:
            raise ValueError(f"No profile found for device {device_id}")
        
        with open(filepath, 'w') as f:
            json.dump(self.profiles[device_id], f, indent=2)
        
        logger.info(f"Profile for {device_id} saved to {filepath}")
    
    def load_profile(self, device_id: str, filepath: str):
        """
        Load device profile from file.
        
        Args:
            device_id: Device identifier
            filepath: Path to JSON file
        """
        with open(filepath, 'r') as f:
            profile = json.load(f)
        
        self.profiles[device_id] = profile
        logger.info(f"Profile for {device_id} loaded from {filepath}")
    
    def get_all_profiles(self) -> Dict:
        """Get all stored device profiles."""
        return self.profiles.copy()
    
    def delete_profile(self, device_id: str):
        """Delete a device profile."""
        if device_id in self.profiles:
            del self.profiles[device_id]
            logger.info(f"Profile for {device_id} deleted")
        else:
            logger.warning(f"No profile found for {device_id}")


def apply_device_specific_preprocessing(
    audio: np.ndarray,
    device_id: str,
    calibrator: DeviceCalibrator,
    sr: int = 16000
) -> np.ndarray:
    """
    Apply device-specific preprocessing to audio.
    
    Convenience function that applies preprocessing based on device profile.
    
    Args:
        audio: Input audio signal
        device_id: Device identifier
        calibrator: DeviceCalibrator instance with loaded profiles
        sr: Sample rate
        
    Returns:
        Preprocessed audio
    """
    params = calibrator.get_device_preprocessing_params(device_id)
    
    # Apply preprocessing based on params
    # Note: This is a simplified version - full implementation would integrate
    # with the existing audio preprocessing pipeline
    
    processed_audio = audio.copy()
    
    # Basic EQ (frequency-domain processing)
    if params['eq_low_gain'] != 1.0 or params['eq_high_gain'] != 1.0:
        stft = librosa.stft(processed_audio)
        freqs = librosa.fft_frequencies(sr=sr)
        
        # Apply gains to frequency bands
        low_mask = freqs < 500
        high_mask = freqs >= 4000
        
        stft[low_mask, :] *= params['eq_low_gain']
        stft[high_mask, :] *= params['eq_high_gain']
        
        processed_audio = librosa.istft(stft)
    
    return processed_audio
