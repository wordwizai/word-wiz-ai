"""
Handler for processing and normalizing client-extracted phonemes.

This module provides utilities for:
- Validating client phoneme format
- Normalizing eSpeak phonemes to IPA format
- Error handling for malformed phoneme data
"""

from typing import Optional


def validate_client_phonemes(
    phonemes: list[list[str]],
    sentence: str
) -> tuple[bool, str]:
    """
    Validate that client phonemes match expected format.
    
    Args:
        phonemes: List of words, where each word is a list of phoneme strings
        sentence: The attempted sentence (ground truth text)
        
    Returns:
        Tuple of (is_valid, error_message)
        - If valid: (True, "")
        - If invalid: (False, "descriptive error message")
        
    Validation checks:
    - Top-level is a list
    - Each word is a list of strings
    - Number of words matches sentence
    - Each word has at least one phoneme
    - Each phoneme is a string
    """
    # Check top-level type
    if not isinstance(phonemes, list):
        return False, "Phonemes must be an array"
    
    # Get expected word count from sentence
    expected_words = sentence.strip().split()
    expected_count = len(expected_words)
    
    # Check word count matches
    if len(phonemes) != expected_count:
        return False, f"Expected {expected_count} words, got {len(phonemes)}"
    
    # Validate each word's phonemes
    for i, word_phonemes in enumerate(phonemes):
        # Check word is a list
        if not isinstance(word_phonemes, list):
            return False, f"Word {i} phonemes must be an array"
        
        # Check word has phonemes
        if len(word_phonemes) == 0:
            return False, f"Word {i} has no phonemes"
        
        # Check each phoneme is a string
        for j, phoneme in enumerate(word_phonemes):
            if not isinstance(phoneme, str):
                return False, f"Word {i}, phoneme {j} must be a string, got {type(phoneme).__name__}"
            
            # Check phoneme is not empty
            if len(phoneme) == 0:
                return False, f"Word {i}, phoneme {j} is empty"
    
    return True, ""


def normalize_espeak_to_ipa(phonemes: list[list[str]]) -> list[list[str]]:
    """
    Normalize eSpeak phonemes to IPA format for consistent processing.
    
    The frontend uses the eSpeak model (Xenova/wav2vec2-lv-60-espeak-cv-ft) which
    outputs phonemes in eSpeak format. The backend expects IPA format from the
    TIMIT-IPA model. This function bridges the gap.
    
    Args:
        phonemes: List of words, where each word is a list of eSpeak phoneme strings
        
    Returns:
        List of words with phonemes normalized to IPA format
        
    Common conversions:
    - eSpeak '@' → IPA 'ə' (schwa)
    - eSpeak '@r' → IPA 'ɝ' (r-colored schwa)
    - eSpeak 'r-' → IPA 'ɝ' (r-colored vowel)
    - eSpeak '3:' → IPA 'ɜː' (NURSE vowel)
    - eSpeak 'aI' → IPA 'aɪ' (PRICE diphthong)
    - eSpeak 'eI' → IPA 'eɪ' (FACE diphthong)
    - eSpeak 'oU' → IPA 'oʊ' (GOAT diphthong)
    
    Note: Normalization is lenient - unmapped phonemes pass through unchanged.
    This ensures compatibility even if eSpeak and IPA formats overlap.
    """
    # eSpeak to IPA mapping
    # Based on common phoneme differences between eSpeak and IPA
    espeak_to_ipa = {
        '@': 'ə',      # schwa (unstressed vowel)
        '@r': 'ɝ',     # r-colored schwa (like in "teacher")
        'r-': 'ɝ',     # r-colored vowel (like in "bird")
        '3:': 'ɜː',    # NURSE vowel (British English)
        'aI': 'aɪ',    # PRICE diphthong (like in "my")
        'eI': 'eɪ',    # FACE diphthong (like in "day")
        'oU': 'oʊ',    # GOAT diphthong (like in "go")
        'aU': 'aʊ',    # MOUTH diphthong (like in "now")
        'OI': 'ɔɪ',    # CHOICE diphthong (like in "boy")
        'I@': 'ɪə',    # NEAR diphthong (like in "here")
        'E@': 'eə',    # SQUARE diphthong (like in "there")
        'U@': 'ʊə',    # CURE diphthong (like in "poor")
        'A:': 'ɑː',    # PALM vowel (like in "father")
        'O:': 'ɔː',    # THOUGHT vowel (like in "caught")
        'u:': 'uː',    # GOOSE vowel (like in "food")
        'i:': 'iː',    # FLEECE vowel (like in "see")
        # Add more mappings as needed based on testing
    }
    
    normalized = []
    for word in phonemes:
        normalized_word = [
            espeak_to_ipa.get(phoneme, phoneme)  # Pass through if not mapped
            for phoneme in word
        ]
        normalized.append(normalized_word)
    
    return normalized


def format_phonemes_for_logging(phonemes: list[list[str]], max_words: int = 5) -> str:
    """
    Format phonemes for logging in a readable way.
    
    Args:
        phonemes: List of words with their phonemes
        max_words: Maximum number of words to include in output
        
    Returns:
        Formatted string representation of phonemes
    """
    if not phonemes:
        return "[]"
    
    # Limit to max_words for readability
    display_phonemes = phonemes[:max_words]
    formatted = []
    
    for i, word in enumerate(display_phonemes):
        formatted.append(f"[{', '.join(repr(p) for p in word)}]")
    
    result = f"[{', '.join(formatted)}"
    
    # Add ellipsis if truncated
    if len(phonemes) > max_words:
        result += f", ... ({len(phonemes) - max_words} more words)"
    
    result += "]"
    return result
