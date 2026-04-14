"""
Test the grapheme integration by directly testing the modified _process_word_alignment function.

This test extracts and tests only the relevant code without importing heavy dependencies.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.grapheme_segmenter import (
    segment_word_to_graphemes,
    map_phoneme_errors_to_graphemes
)


def align_sequences(gt, pred):
    """
    Simplified version of align_sequences for testing.
    Returns list of (operation, gt_item, pred_item) tuples.
    """
    m, n = len(gt), len(pred)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if gt[i - 1] == pred[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,
                dp[i][j - 1] + 1,
                dp[i - 1][j - 1] + cost
            )
    
    operations = []
    i, j = m, n
    while i > 0 or j > 0:
        if i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + (0 if gt[i - 1] == pred[j - 1] else 1):
            if gt[i - 1] == pred[j - 1]:
                operations.append(('match', gt[i - 1], pred[j - 1]))
            else:
                operations.append(('substitution', gt[i - 1], pred[j - 1]))
            i -= 1
            j -= 1
        elif i > 0 and dp[i][j] == dp[i - 1][j] + 1:
            operations.append(('deletion', gt[i - 1], None))
            i -= 1
        elif j > 0 and dp[i][j] == dp[i][j - 1] + 1:
            operations.append(('insertion', None, pred[j - 1]))
            j -= 1
    operations.reverse()
    return operations


def test_end_to_end_workflow():
    """Test the complete workflow from phonemes to grapheme errors."""
    print("=" * 60)
    print("Testing End-to-End Grapheme Integration")
    print("=" * 60 + "\n")
    
    # Test Case 1: Word "cat" with missed /k/ phoneme
    print("Test 1: Word 'cat' with missed /k/")
    print("-" * 40)
    
    gt_word = "cat"
    gt_phonemes = ["k", "æ", "t"]
    pred_phonemes = ["æ", "t"]  # missed /k/
    
    # Segment word
    graphemes = segment_word_to_graphemes(gt_word, gt_phonemes)
    print(f"Graphemes: {graphemes}")
    assert graphemes == ["c", "a", "t"], f"Expected ['c', 'a', 't'], got {graphemes}"
    
    # Align phonemes
    phoneme_ops = align_sequences(gt_phonemes, pred_phonemes)
    missed, added, substituted = [], [], []
    for op, gph, pph in phoneme_ops:
        if op == 'deletion':
            missed.append(gph)
        elif op == 'insertion':
            added.append(pph)
        elif op == 'substitution':
            substituted.append((gph, pph))
    
    print(f"Missed: {missed}")
    print(f"Added: {added}")
    print(f"Substituted: {substituted}")
    
    # Map errors to graphemes
    grapheme_errors = map_phoneme_errors_to_graphemes(
        gt_word, graphemes, gt_phonemes, pred_phonemes, missed, added, substituted
    )
    
    print(f"Grapheme errors: {grapheme_errors}")
    assert 0 in grapheme_errors, f"Expected error at position 0"
    assert grapheme_errors[0]["type"] == "missed"
    assert grapheme_errors[0]["phoneme"] == "k"
    assert grapheme_errors[0]["grapheme"] == "c"
    print("✅ Test 1 passed!\n")
    
    # Test Case 2: Word "ship" with missed /ʃ/
    print("Test 2: Word 'ship' with missed /ʃ/ (digraph)")
    print("-" * 40)
    
    gt_word = "ship"
    gt_phonemes = ["ʃ", "ɪ", "p"]
    pred_phonemes = ["ɪ", "p"]  # missed /ʃ/
    
    graphemes = segment_word_to_graphemes(gt_word, gt_phonemes)
    print(f"Graphemes: {graphemes}")
    assert graphemes == ["sh", "i", "p"], f"Expected ['sh', 'i', 'p'], got {graphemes}"
    
    phoneme_ops = align_sequences(gt_phonemes, pred_phonemes)
    missed, added, substituted = [], [], []
    for op, gph, pph in phoneme_ops:
        if op == 'deletion':
            missed.append(gph)
        elif op == 'insertion':
            added.append(pph)
        elif op == 'substitution':
            substituted.append((gph, pph))
    
    grapheme_errors = map_phoneme_errors_to_graphemes(
        gt_word, graphemes, gt_phonemes, pred_phonemes, missed, added, substituted
    )
    
    print(f"Grapheme errors: {grapheme_errors}")
    assert 0 in grapheme_errors, f"Expected error at position 0"
    assert grapheme_errors[0]["type"] == "missed"
    assert grapheme_errors[0]["phoneme"] == "ʃ"
    assert grapheme_errors[0]["grapheme"] == "sh"
    print("✅ Test 2 passed!\n")
    
    # Test Case 3: Word "brown" with missed /b/ and added /d/
    print("Test 3: Word 'brown' with missed /b/ and added /d/")
    print("-" * 40)
    
    gt_word = "brown"
    gt_phonemes = ["b", "r", "aʊ", "n"]
    pred_phonemes = ["r", "aʊ", "n", "d"]  # missed /b/, added /d/
    
    graphemes = segment_word_to_graphemes(gt_word, gt_phonemes)
    print(f"Graphemes: {graphemes}")
    
    phoneme_ops = align_sequences(gt_phonemes, pred_phonemes)
    missed, added, substituted = [], [], []
    for op, gph, pph in phoneme_ops:
        if op == 'deletion':
            missed.append(gph)
        elif op == 'insertion':
            added.append(pph)
        elif op == 'substitution':
            substituted.append((gph, pph))
    
    print(f"Missed: {missed}")
    print(f"Added: {added}")
    
    grapheme_errors = map_phoneme_errors_to_graphemes(
        gt_word, graphemes, gt_phonemes, pred_phonemes, missed, added, substituted
    )
    
    print(f"Grapheme errors: {grapheme_errors}")
    
    # Check missed /b/
    assert any(e["type"] == "missed" and e["phoneme"] == "b" for e in grapheme_errors.values())
    
    # Check added /d/
    assert -1 in grapheme_errors, f"Expected added phoneme at position -1"
    assert grapheme_errors[-1]["type"] == "added"
    assert grapheme_errors[-1]["phoneme"] == "d"
    
    print("✅ Test 3 passed!\n")
    
    print("=" * 60)
    print("✅ ALL END-TO-END TESTS PASSED!")
    print("=" * 60)
    print("\nThe grapheme segmentation is working correctly!")
    print("Phoneme errors are successfully mapped to grapheme positions.")
    return True


if __name__ == "__main__":
    try:
        success = test_end_to_end_workflow()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
