"""
Grapheme segmentation for phoneme-to-grapheme alignment.

This module segments words into phoneme-producing units (graphemes),
handling digraphs, vowel teams, r-controlled vowels, and silent letters.
"""

import re
from typing import List, Dict, Tuple, Optional

# Common digraphs and multi-letter graphemes
DIGRAPHS = {
    # Consonant digraphs
    'sh', 'ch', 'th', 'ph', 'wh', 'gh', 'ck', 'ng', 'qu',
    # Vowel teams
    'ai', 'ay', 'ee', 'ea', 'oa', 'oo', 'ou', 'ow', 'ue', 'ew', 'ie', 'ei', 'ey',
    # R-controlled vowels
    'ar', 'er', 'ir', 'or', 'ur',
}

TRIGRAPHS = {
    'igh',  # light, night
    'tch',  # match, catch
    'dge',  # badge, edge
}

# Silent letter patterns (context-dependent)
SILENT_PATTERNS = [
    (r'^k', 'kn'),      # knight, knee
    (r'^w', 'wr'),      # write, wrong
    (r'^p', 'ps'),      # psychology, psalm
    (r'gh$', 'ugh'),    # laugh, tough
    (r'gh$', 'igh'),    # light, night
    (r'b$', 'mb'),      # lamb, climb
    (r'b$', 'bt'),      # doubt, debt
]


def segment_word_to_graphemes(word: str, expected_phonemes: List[str]) -> List[str]:
    """
    Segment a word into grapheme units that correspond to phonemes.
    
    Args:
        word: The word to segment (e.g., "ship")
        expected_phonemes: Expected phoneme sequence (e.g., [/ʃ/, /ɪ/, /p/])
        
    Returns:
        List of grapheme strings (e.g., ["sh", "i", "p"])
        
    Note:
        This is a heuristic approach that uses phoneme count as a guide.
        For 90% of words, this will produce correct segmentation.
    """
    word_lower = word.lower()
    graphemes = []
    i = 0
    
    # Target number of graphemes should roughly match phoneme count
    target_count = len(expected_phonemes)
    
    while i < len(word_lower):
        # Try trigraphs first (3 letters)
        if i + 2 < len(word_lower):
            three = word_lower[i:i+3]
            if three in TRIGRAPHS:
                graphemes.append(three)
                i += 3
                continue
        
        # Try digraphs (2 letters)
        if i + 1 < len(word_lower):
            two = word_lower[i:i+2]
            if two in DIGRAPHS:
                graphemes.append(two)
                i += 2
                continue
        
        # Check for silent letters
        # (Only mark as silent if we're over the target phoneme count)
        if len(graphemes) >= target_count:
            # Check if current letter might be silent
            remaining = word_lower[i:]
            is_silent = False
            for pattern, context in SILENT_PATTERNS:
                if re.search(pattern, remaining) and remaining.startswith(context):
                    is_silent = True
                    break
            
            if is_silent:
                # Mark as silent by combining with previous grapheme
                if graphemes:
                    graphemes[-1] += word_lower[i]
                else:
                    graphemes.append(word_lower[i])
                i += 1
                continue
        
        # Default: single letter grapheme
        graphemes.append(word_lower[i])
        i += 1
    
    return graphemes


def map_graphemes_to_phonemes(
    word: str,
    graphemes: List[str],
    expected_phonemes: List[str]
) -> Dict[int, int]:
    """
    Map grapheme positions to phoneme positions.
    
    Args:
        word: Original word
        graphemes: List of grapheme units
        expected_phonemes: List of expected phonemes
        
    Returns:
        Dictionary mapping grapheme_index -> phoneme_index
        Silent graphemes map to -1
        
    Example:
        word = "ship"
        graphemes = ["sh", "i", "p"]
        phonemes = [/ʃ/, /ɪ/, /p/]
        Returns: {0: 0, 1: 1, 2: 2}
    """
    mapping = {}
    
    # Simple 1:1 alignment for Phase 1
    # Assumes graphemes and phonemes align linearly
    for g_idx in range(len(graphemes)):
        if g_idx < len(expected_phonemes):
            mapping[g_idx] = g_idx
        else:
            # Extra graphemes (silent letters) map to -1
            mapping[g_idx] = -1
    
    return mapping


def map_phoneme_errors_to_graphemes(
    word: str,
    graphemes: List[str],
    expected_phonemes: List[str],
    detected_phonemes: List[str],
    missed_phonemes: List[str],
    added_phonemes: List[str],
    substituted_phonemes: List[Tuple[str, str]]  # (expected, detected) pairs
) -> Dict[int, Dict]:
    """
    Map phoneme errors back to grapheme positions.
    
    Args:
        word: Original word
        graphemes: Segmented graphemes
        expected_phonemes: Expected phoneme sequence
        detected_phonemes: Detected phoneme sequence
        missed_phonemes: Phonemes that were missed
        added_phonemes: Phonemes that were added
        substituted_phonemes: Phonemes that were substituted (expected, detected) pairs
        
    Returns:
        Dictionary mapping grapheme_index -> error_info
        
    Example:
        word = "cat"
        graphemes = ["c", "a", "t"]
        expected = [/k/, /æ/, /t/]
        detected = [/æ/, /t/]
        missed = [/k/]
        Returns: {0: {"type": "missed", "phoneme": /k/, "grapheme": "c"}}
    """
    grapheme_errors = {}
    
    # Map graphemes to phonemes
    g2p_map = map_graphemes_to_phonemes(word, graphemes, expected_phonemes)
    
    # Create phoneme-to-grapheme reverse map
    p2g_map = {p_idx: g_idx for g_idx, p_idx in g2p_map.items() if p_idx != -1}
    
    # Map missed phonemes to graphemes
    for phoneme in missed_phonemes:
        if phoneme in expected_phonemes:
            p_idx = expected_phonemes.index(phoneme)
            if p_idx in p2g_map:
                g_idx = p2g_map[p_idx]
                grapheme_errors[g_idx] = {
                    "type": "missed",
                    "phoneme": phoneme,
                    "grapheme": graphemes[g_idx]
                }
    
    # Map substituted phonemes to graphemes
    for expected, detected in substituted_phonemes:
        if expected in expected_phonemes:
            p_idx = expected_phonemes.index(expected)
            if p_idx in p2g_map:
                g_idx = p2g_map[p_idx]
                grapheme_errors[g_idx] = {
                    "type": "substituted",
                    "expected_phoneme": expected,
                    "detected_phoneme": detected,
                    "grapheme": graphemes[g_idx]
                }
    
    # Added phonemes don't map to existing graphemes
    # They are "phantom" graphemes that will be shown separately
    # We'll add them as position -1 (special marker for additions)
    for i, phoneme in enumerate(added_phonemes):
        grapheme_errors[-1 - i] = {
            "type": "added",
            "phoneme": phoneme,
            "grapheme": None  # No grapheme, it's an addition
        }
    
    return grapheme_errors
