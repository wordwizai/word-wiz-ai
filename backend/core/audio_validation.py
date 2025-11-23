"""
Audio validation utilities for ensuring audio quality before sending to clients.

This module provides functions to validate audio characteristics such as:
- Sample rate consistency
- Audio duration
- Format validation
- Basic quality checks
"""

import io
import logging
from typing import Dict, Optional, Tuple

import librosa
import numpy as np
import soundfile as sf

# Configure logging
logger = logging.getLogger(__name__)


def validate_audio_output(
    audio_bytes: bytes,
    expected_sample_rate: int = 24000,
    max_duration_seconds: float = 60.0,
    min_duration_seconds: float = 0.1,
) -> Tuple[bool, Dict[str, any]]:
    """
    Validate audio output before sending to client.
    
    Args:
        audio_bytes: The audio data as bytes (WAV format)
        expected_sample_rate: Expected sample rate in Hz (default: 24000)
        max_duration_seconds: Maximum allowed audio duration
        min_duration_seconds: Minimum allowed audio duration
        
    Returns:
        Tuple of (is_valid, validation_info)
        - is_valid: Boolean indicating if audio passes all validation checks
        - validation_info: Dictionary containing validation details and audio characteristics
    """
    validation_info = {
        "valid": False,
        "sample_rate": None,
        "duration_seconds": None,
        "num_channels": None,
        "format": None,
        "size_bytes": len(audio_bytes),
        "warnings": [],
        "errors": []
    }
    
    try:
        # Load audio data
        audio_buffer = io.BytesIO(audio_bytes)
        
        # Read audio file info
        with sf.SoundFile(audio_buffer) as sound_file:
            sample_rate = sound_file.samplerate
            num_frames = len(sound_file)
            num_channels = sound_file.channels
            format_info = sound_file.format
            subtype_info = sound_file.subtype
            
            duration_seconds = num_frames / sample_rate
            
            validation_info["sample_rate"] = sample_rate
            validation_info["duration_seconds"] = duration_seconds
            validation_info["num_channels"] = num_channels
            validation_info["format"] = f"{format_info}/{subtype_info}"
            
            # Validation checks
            
            # 1. Check sample rate
            if sample_rate != expected_sample_rate:
                validation_info["warnings"].append(
                    f"Sample rate mismatch: expected {expected_sample_rate}Hz, got {sample_rate}Hz"
                )
            
            # 2. Check duration
            if duration_seconds > max_duration_seconds:
                validation_info["errors"].append(
                    f"Audio too long: {duration_seconds:.2f}s exceeds maximum {max_duration_seconds}s"
                )
            elif duration_seconds < min_duration_seconds:
                validation_info["errors"].append(
                    f"Audio too short: {duration_seconds:.2f}s is below minimum {min_duration_seconds}s"
                )
            
            # 3. Check if mono (recommended for TTS)
            if num_channels != 1:
                validation_info["warnings"].append(
                    f"Audio is not mono: has {num_channels} channels"
                )
            
            # 4. Check format is WAV/PCM_16
            if format_info.upper() != "WAV":
                validation_info["warnings"].append(
                    f"Format is not WAV: got {format_info}"
                )
            
            # 5. Load and check audio data quality
            audio_buffer.seek(0)
            audio_data, sr = librosa.load(audio_buffer, sr=None, mono=True)
            
            # Check for silence (RMS energy)
            rms_energy = np.sqrt(np.mean(audio_data ** 2))
            if rms_energy < 0.001:
                validation_info["warnings"].append(
                    f"Audio appears to be silent (RMS energy: {rms_energy:.6f})"
                )
            
            # Check for clipping
            max_amplitude = np.max(np.abs(audio_data))
            if max_amplitude > 0.99:
                validation_info["warnings"].append(
                    f"Audio may be clipping (max amplitude: {max_amplitude:.3f})"
                )
            
            # Mark as valid if no errors
            validation_info["valid"] = len(validation_info["errors"]) == 0
            
    except Exception as e:
        validation_info["errors"].append(f"Validation error: {str(e)}")
        logger.error(f"Audio validation failed: {str(e)}")
    
    return validation_info["valid"], validation_info


def log_audio_characteristics(audio_bytes: bytes, context: str = "audio") -> None:
    """
    Log audio characteristics for debugging purposes.
    
    Args:
        audio_bytes: The audio data as bytes
        context: Context string for logging (e.g., "TTS output", "feedback audio")
    """
    is_valid, info = validate_audio_output(audio_bytes)
    
    logger.info(f"[{context}] Audio characteristics:")
    logger.info(f"  - Valid: {is_valid}")
    logger.info(f"  - Sample Rate: {info['sample_rate']}Hz")
    logger.info(f"  - Duration: {info['duration_seconds']:.2f}s")
    logger.info(f"  - Channels: {info['num_channels']}")
    logger.info(f"  - Format: {info['format']}")
    logger.info(f"  - Size: {info['size_bytes']} bytes")
    
    if info['warnings']:
        logger.warning(f"[{context}] Warnings:")
        for warning in info['warnings']:
            logger.warning(f"  - {warning}")
    
    if info['errors']:
        logger.error(f"[{context}] Errors:")
        for error in info['errors']:
            logger.error(f"  - {error}")


def ensure_compatible_audio(
    audio_bytes: bytes,
    target_sample_rate: int = 24000,
    ensure_mono: bool = True,
) -> bytes:
    """
    Ensure audio is in a compatible format for mobile playback.
    
    This function will:
    - Convert to target sample rate
    - Convert to mono if requested
    - Normalize audio
    - Write as WAV PCM_16
    
    Args:
        audio_bytes: Input audio bytes
        target_sample_rate: Target sample rate (default: 24000Hz)
        ensure_mono: Whether to convert to mono (default: True)
        
    Returns:
        Processed audio bytes in WAV format
    """
    try:
        # Load audio
        audio_buffer = io.BytesIO(audio_bytes)
        audio_data, original_sr = librosa.load(
            audio_buffer, 
            sr=None, 
            mono=ensure_mono
        )
        
        # Resample if needed
        if original_sr != target_sample_rate:
            audio_data = librosa.resample(
                audio_data,
                orig_sr=original_sr,
                target_sr=target_sample_rate
            )
        
        # Normalize
        audio_data = librosa.util.normalize(audio_data)
        
        # Write to buffer
        output_buffer = io.BytesIO()
        sf.write(
            output_buffer,
            audio_data,
            target_sample_rate,
            format='WAV',
            subtype='PCM_16'
        )
        
        output_buffer.seek(0)
        return output_buffer.read()
        
    except Exception as e:
        logger.error(f"Failed to ensure compatible audio: {str(e)}")
        # Return original bytes if processing fails
        return audio_bytes
