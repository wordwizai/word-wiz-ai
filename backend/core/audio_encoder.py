"""
Audio encoding utilities for TTS feedback.

Handles conversion, resampling, normalization, and base64 encoding of audio feedback.
"""

import base64
import io
import logging

import soundfile as sf

from .audio_validation import log_audio_characteristics, validate_audio_output

logger = logging.getLogger(__name__)


def feedback_to_audio_base64(
    audio_bytes: bytes,
    target_sample_rate: int = 24000,
    validate: bool = True
) -> dict:
    """
    Convert TTS audio bytes to base64-encoded WAV with resampling and normalization.

    Args:
        audio_bytes: Raw audio bytes from TTS service (typically MP3).
        target_sample_rate: Target sample rate (default 24000 for mobile compatibility).
        validate: Whether to validate audio output (default True).

    Returns:
        dict: {
            "filename": str,
            "mimetype": str,
            "data": str (base64-encoded)
        }
    """
    audio_buffer = io.BytesIO()

    try:
        import librosa
        import numpy as np

        # Decode MP3 audio using librosa
        audio_array, original_sr = librosa.load(
            io.BytesIO(audio_bytes),
            sr=None,  # Keep original sample rate initially
            mono=True
        )

        # Resample to target sample rate if needed
        if original_sr != target_sample_rate:
            audio_array = librosa.resample(
                audio_array,
                orig_sr=original_sr,
                target_sr=target_sample_rate
            )

        # Normalize audio to prevent clipping
        audio_array = librosa.util.normalize(audio_array)

        # Write as WAV with explicit format (PCM 16-bit for maximum compatibility)
        sf.write(
            audio_buffer,
            audio_array,
            target_sample_rate,
            format='WAV',
            subtype='PCM_16'
        )

    except Exception as e:
        print(f"Audio processing error: {str(e)}")
        print(f"Attempting fallback conversion...")
        # Fallback: try to write directly as WAV
        try:
            import numpy as np
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
            sf.write(audio_buffer, audio_array, target_sample_rate, format="WAV", subtype='PCM_16')
        except Exception as fallback_error:
            print(f"Fallback also failed: {str(fallback_error)}")
            # Last resort: just write the raw bytes
            audio_buffer.write(audio_bytes)

    audio_buffer.seek(0)
    audio_bytes_final = audio_buffer.read()

    if validate:
        # Validate and log audio characteristics
        is_valid, validation_info = validate_audio_output(audio_bytes_final)

        if not is_valid:
            logger.warning(f"Audio validation failed: {validation_info['errors']}")

        if validation_info.get('warnings'):
            logger.info(f"Audio validation warnings: {validation_info['warnings']}")

        log_audio_characteristics(audio_bytes_final, context="TTS feedback")

    audio_b64 = base64.b64encode(audio_bytes_final).decode("utf-8")

    return {"filename": "feedback.wav", "mimetype": "audio/wav", "data": audio_b64}
