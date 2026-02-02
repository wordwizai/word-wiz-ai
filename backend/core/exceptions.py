"""
Domain-specific exception hierarchy for Word Wiz AI.

Provides structured error types for different stages of the pronunciation analysis pipeline.
"""


class WordWizError(Exception):
    """Base exception for all Word Wiz AI errors."""

    def __init__(self, message: str, error_code: str = None):
        """
        Initialize Word Wiz error.

        Args:
            message: Human-readable error message.
            error_code: Machine-readable error code for client handling.
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__.upper()


class AudioValidationError(WordWizError):
    """
    Raised when audio input fails validation.

    Examples:
        - Audio too short (less than minimum duration)
        - Audio too quiet (below SNR threshold)
        - Unsupported audio format
        - Corrupted audio data
    """

    pass


class PhonemeExtractionError(WordWizError):
    """
    Raised when phoneme extraction fails.

    Examples:
        - Model loading failure
        - Inference error
        - Invalid audio input for model
        - Out of memory during extraction
    """

    pass


class AlignmentError(WordWizError):
    """
    Raised when phoneme-to-word alignment fails.

    Examples:
        - Unable to align extracted phonemes to expected words
        - Extreme variance between expected and extracted phonemes
        - Invalid ground truth phonemes
    """

    pass


class GPTResponseError(WordWizError):
    """
    Raised when GPT API interaction fails.

    Examples:
        - API request timeout
        - Invalid API response format
        - Malformed JSON in response
        - Missing required fields in response
        - API rate limit exceeded
    """

    pass


class AudioEncodingError(WordWizError):
    """
    Raised when audio encoding/decoding fails.

    Examples:
        - TTS audio generation failure
        - MP3 to WAV conversion failure
        - Audio resampling error
        - Base64 encoding/decoding failure
    """

    pass


class WordExtractionError(WordWizError):
    """
    Raised when word boundary extraction fails.

    Examples:
        - External API (Deepgram) failure
        - No speech detected in audio
        - Invalid API response
    """

    pass


class ValidationError(WordWizError):
    """
    Raised when input validation fails.

    Examples:
        - Invalid client phoneme format
        - Invalid client word format
        - Missing required fields
        - Type mismatch
    """

    pass
