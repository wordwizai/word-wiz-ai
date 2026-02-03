"""
Simple integration test for grapheme segmentation in process_audio.py

Tests that the new grapheme fields are correctly added to the output.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.process_audio import _process_word_alignment


def test_grapheme_integration():
    """Test that grapheme segmentation is integrated into process_audio."""
    print("Testing grapheme integration in process_audio...")
    
    # Setup test data
    ground_truth_words = ["cat", "dog"]
    ground_truth_phonemes = [
        ("cat", ["k", "æ", "t"]),
        ("dog", ["d", "ɔ", "g"])
    ]
    predicted_words = ["cat", "dog"]
    phoneme_predictions = [
        ["æ", "t"],  # missed /k/ in "cat"
        ["d", "ɔ", "g", "z"]  # added /z/ in "dog"
    ]
    
    # Run the function
    results = _process_word_alignment(
        ground_truth_words,
        ground_truth_phonemes,
        predicted_words,
        phoneme_predictions
    )
    
    # Verify results
    assert len(results) == 2, f"Expected 2 results, got {len(results)}"
    
    # Check first word (cat - missed phoneme)
    cat_result = results[0]
    print(f"\nResult for 'cat': {cat_result}")
    
    assert "graphemes" in cat_result, "Missing 'graphemes' field"
    assert "grapheme_errors" in cat_result, "Missing 'grapheme_errors' field"
    
    assert cat_result["graphemes"] == ["c", "a", "t"], \
        f"Expected graphemes ['c', 'a', 't'], got {cat_result['graphemes']}"
    
    assert 0 in cat_result["grapheme_errors"], \
        f"Expected error at position 0, got {cat_result['grapheme_errors']}"
    
    assert cat_result["grapheme_errors"][0]["type"] == "missed", \
        f"Expected 'missed' error, got {cat_result['grapheme_errors'][0]['type']}"
    
    print("✓ 'cat' result has correct graphemes and errors")
    
    # Check second word (dog - added phoneme)
    dog_result = results[1]
    print(f"\nResult for 'dog': {dog_result}")
    
    assert "graphemes" in dog_result, "Missing 'graphemes' field"
    assert "grapheme_errors" in dog_result, "Missing 'grapheme_errors' field"
    
    assert dog_result["graphemes"] == ["d", "o", "g"], \
        f"Expected graphemes ['d', 'o', 'g'], got {dog_result['graphemes']}"
    
    assert -1 in dog_result["grapheme_errors"], \
        f"Expected error at position -1 (added), got {dog_result['grapheme_errors']}"
    
    assert dog_result["grapheme_errors"][-1]["type"] == "added", \
        f"Expected 'added' error, got {dog_result['grapheme_errors'][-1]['type']}"
    
    print("✓ 'dog' result has correct graphemes and errors")
    
    print("\n✅ Integration test passed!")
    print("=" * 60)
    print("Grapheme segmentation successfully integrated!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        success = test_grapheme_integration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
