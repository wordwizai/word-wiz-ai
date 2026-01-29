"""
Input validation utilities.

Provides common validation functions for client-provided data.
"""

import json
from typing import Optional


def validate_client_phonemes(client_phonemes: str) -> Optional[list[list[str]]]:
    """
    Validate and parse client-provided phonemes JSON string.

    Args:
        client_phonemes: JSON string representing phonemes array.

    Returns:
        Parsed phonemes if valid, None if invalid.
    """
    try:
        phonemes_data = json.loads(client_phonemes)

        # Basic validation
        if not isinstance(phonemes_data, list):
            raise ValueError("Phonemes must be an array")

        for i, word_phonemes in enumerate(phonemes_data):
            if not isinstance(word_phonemes, list):
                raise ValueError(f"Word {i} phonemes must be an array")
            if len(word_phonemes) == 0:
                raise ValueError(f"Word {i} has no phonemes")
            for phoneme in word_phonemes:
                if not isinstance(phoneme, str):
                    raise ValueError(f"Phoneme must be a string, got {type(phoneme)}")

        print(f"Validated client phonemes: {len(phonemes_data)} words")
        return phonemes_data

    except (json.JSONDecodeError, ValueError) as e:
        print(f"Invalid client phonemes, falling back to server extraction: {e}")
        return None


def validate_client_words(client_words: str, phonemes_data: Optional[list] = None) -> Optional[list[str]]:
    """
    Validate and parse client-provided words JSON string.

    Args:
        client_words: JSON string representing words array.
        phonemes_data: Optional phonemes list for count validation.

    Returns:
        Parsed words if valid, None if invalid.
    """
    try:
        words_data = json.loads(client_words)

        # Basic validation
        if not isinstance(words_data, list):
            print("Invalid client words: not an array")
            return None

        if phonemes_data and len(words_data) != len(phonemes_data):
            # Log the mismatch but don't reject - backend will handle alignment
            print(f"Word count ({len(words_data)}) differs from phoneme count ({len(phonemes_data)}) - backend will align")

        # Validate each word is a non-empty string
        for i, word in enumerate(words_data):
            if not isinstance(word, str) or len(word) == 0:
                print(f"Invalid word at index {i}")
                return None

        print(f"Validated client words: {len(words_data)} words")
        return words_data

    except (json.JSONDecodeError, ValueError) as e:
        print(f"Invalid client words, falling back to server extraction: {e}")
        return None
