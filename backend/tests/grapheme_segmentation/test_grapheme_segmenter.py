"""
Test suite for grapheme segmentation.

Tests the segmentation of words into phoneme-producing units (graphemes).
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.grapheme_segmenter import (
    segment_word_to_graphemes,
    map_graphemes_to_phonemes,
    map_phoneme_errors_to_graphemes
)


def test_simple_words():
    """Test simple one-to-one letter-phoneme mappings."""
    print("Testing simple words...")
    
    # Test: cat
    word = "cat"
    phonemes = ["k", "æ", "t"]
    graphemes = segment_word_to_graphemes(word, phonemes)
    assert graphemes == ["c", "a", "t"], f"Expected ['c', 'a', 't'], got {graphemes}"
    print("✓ 'cat' -> ['c', 'a', 't']")
    
    # Test: dog
    word = "dog"
    phonemes = ["d", "ɔ", "g"]
    graphemes = segment_word_to_graphemes(word, phonemes)
    assert graphemes == ["d", "o", "g"], f"Expected ['d', 'o', 'g'], got {graphemes}"
    print("✓ 'dog' -> ['d', 'o', 'g']")
    
    # Test: run
    word = "run"
    phonemes = ["r", "ʌ", "n"]
    graphemes = segment_word_to_graphemes(word, phonemes)
    assert graphemes == ["r", "u", "n"], f"Expected ['r', 'u', 'n'], got {graphemes}"
    print("✓ 'run' -> ['r', 'u', 'n']")
    
    print("✅ Simple words tests passed!\n")


def test_digraphs():
    """Test words with consonant digraphs."""
    print("Testing digraphs...")
    
    # Test: ship
    word = "ship"
    phonemes = ["ʃ", "ɪ", "p"]
    graphemes = segment_word_to_graphemes(word, phonemes)
    assert graphemes == ["sh", "i", "p"], f"Expected ['sh', 'i', 'p'], got {graphemes}"
    print("✓ 'ship' -> ['sh', 'i', 'p']")
    
    # Test: chat
    word = "chat"
    phonemes = ["ʧ", "æ", "t"]
    graphemes = segment_word_to_graphemes(word, phonemes)
    assert graphemes == ["ch", "a", "t"], f"Expected ['ch', 'a', 't'], got {graphemes}"
    print("✓ 'chat' -> ['ch', 'a', 't']")
    
    # Test: phone
    word = "phone"
    phonemes = ["f", "oʊ", "n"]
    graphemes = segment_word_to_graphemes(word, phonemes)
    assert graphemes == ["ph", "o", "n", "e"], f"Expected ['ph', 'o', 'n', 'e'], got {graphemes}"
    print("✓ 'phone' -> ['ph', 'o', 'n', 'e']")
    
    print("✅ Digraph tests passed!\n")


def test_vowel_teams():
    """Test words with vowel teams."""
    print("Testing vowel teams...")
    
    # Test: rain
    word = "rain"
    phonemes = ["r", "eɪ", "n"]
    graphemes = segment_word_to_graphemes(word, phonemes)
    assert graphemes == ["r", "ai", "n"], f"Expected ['r', 'ai', 'n'], got {graphemes}"
    print("✓ 'rain' -> ['r', 'ai', 'n']")
    
    # Test: boat
    word = "boat"
    phonemes = ["b", "oʊ", "t"]
    graphemes = segment_word_to_graphemes(word, phonemes)
    assert graphemes == ["b", "oa", "t"], f"Expected ['b', 'oa', 't'], got {graphemes}"
    print("✓ 'boat' -> ['b', 'oa', 't']")
    
    # Test: light
    word = "light"
    phonemes = ["l", "aɪ", "t"]
    graphemes = segment_word_to_graphemes(word, phonemes)
    assert graphemes == ["l", "igh", "t"], f"Expected ['l', 'igh', 't'], got {graphemes}"
    print("✓ 'light' -> ['l', 'igh', 't']")
    
    print("✅ Vowel team tests passed!\n")


def test_error_mapping():
    """Test mapping of phoneme errors to grapheme positions."""
    print("Testing error mapping...")
    
    # Test: missed phoneme in "cat"
    word = "cat"
    graphemes = ["c", "a", "t"]
    expected = ["k", "æ", "t"]
    detected = ["æ", "t"]
    missed = ["k"]
    added = []
    substituted = []
    
    errors = map_phoneme_errors_to_graphemes(
        word, graphemes, expected, detected, missed, added, substituted
    )
    
    assert 0 in errors, f"Expected error at position 0, got {errors}"
    assert errors[0]["type"] == "missed", f"Expected 'missed', got {errors[0]['type']}"
    assert errors[0]["phoneme"] == "k", f"Expected phoneme 'k', got {errors[0]['phoneme']}"
    assert errors[0]["grapheme"] == "c", f"Expected grapheme 'c', got {errors[0]['grapheme']}"
    print("✓ Missed phoneme mapped correctly: /k/ -> 'c' at position 0")
    
    # Test: substituted phoneme in "rain"
    word = "rain"
    graphemes = ["r", "ai", "n"]
    expected = ["r", "eɪ", "n"]
    detected = ["r", "ɛ", "n"]
    missed = []
    added = []
    substituted = [("eɪ", "ɛ")]
    
    errors = map_phoneme_errors_to_graphemes(
        word, graphemes, expected, detected, missed, added, substituted
    )
    
    assert 1 in errors, f"Expected error at position 1, got {errors}"
    assert errors[1]["type"] == "substituted", f"Expected 'substituted', got {errors[1]['type']}"
    assert errors[1]["expected_phoneme"] == "eɪ", f"Expected 'eɪ', got {errors[1]['expected_phoneme']}"
    assert errors[1]["detected_phoneme"] == "ɛ", f"Expected 'ɛ', got {errors[1]['detected_phoneme']}"
    assert errors[1]["grapheme"] == "ai", f"Expected grapheme 'ai', got {errors[1]['grapheme']}"
    print("✓ Substituted phoneme mapped correctly: /eɪ/ -> /ɛ/ at 'ai' (position 1)")
    
    # Test: added phoneme
    word = "dog"
    graphemes = ["d", "o", "g"]
    expected = ["d", "ɔ", "g"]
    detected = ["d", "ɔ", "g", "z"]
    missed = []
    added = ["z"]
    substituted = []
    
    errors = map_phoneme_errors_to_graphemes(
        word, graphemes, expected, detected, missed, added, substituted
    )
    
    assert -1 in errors, f"Expected error at position -1 (added), got {errors}"
    assert errors[-1]["type"] == "added", f"Expected 'added', got {errors[-1]['type']}"
    assert errors[-1]["phoneme"] == "z", f"Expected phoneme 'z', got {errors[-1]['phoneme']}"
    assert errors[-1]["grapheme"] is None, f"Expected None for added phoneme, got {errors[-1]['grapheme']}"
    print("✓ Added phoneme mapped correctly: /z/ at position -1 (phantom)")
    
    print("✅ Error mapping tests passed!\n")


def run_all_tests():
    """Run all test suites."""
    print("=" * 60)
    print("Running Grapheme Segmentation Tests")
    print("=" * 60 + "\n")
    
    try:
        test_simple_words()
        test_digraphs()
        test_vowel_teams()
        test_error_mapping()
        
        print("=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        return True
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
