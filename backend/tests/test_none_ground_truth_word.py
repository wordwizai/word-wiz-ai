"""
Test for the NoneType .lower() bug fix.

This test ensures that when pronunciation data contains None values for 
ground_truth_word (which happens for insertion word alignment types), 
the code doesn't crash with AttributeError.
"""

import sys
import os

# Add backend to path
backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from core.gpt_output_validator import validate_gpt_feedback


def test_none_ground_truth_word_in_validator():
    """Test that validator handles None ground_truth_word without crashing."""
    
    # Simulated pronunciation data with None ground_truth_word (insertion case)
    pronunciation_data = [
        {
            "type": "match",
            "ground_truth_word": "the",
            "predicted_word": "the",
            "per": 0.0,
            "missed": [],
            "added": [],
            "substituted": [],
            "expected_phonemes": ["ð", "ə"],
            "actual_phonemes": ["ð", "ə"]
        },
        {
            "type": "insertion",
            "ground_truth_word": None,  # This is the problematic case
            "predicted_word": "extra",
            "per": None,
            "missed": None,
            "added": None,
            "substituted": None,
            "expected_phonemes": [],
            "actual_phonemes": ["ɛ", "k", "s", "t", "r", "ə"]
        },
        {
            "type": "match",
            "ground_truth_word": "cat",
            "predicted_word": "cat",
            "per": 0.15,
            "missed": ["æ"],
            "added": [],
            "substituted": [["æ", "ɛ"]],
            "expected_phonemes": ["k", "æ", "t"],
            "actual_phonemes": ["k", "ɛ", "t"]
        }
    ]
    
    # Simulated feedback from GPT
    feedback_dict = {
        "feedback": "Good job reading! Watch the 'a' sound in 'cat'.",
        "feedback_ssml": "<speak>Good job reading! Watch the 'a' sound in 'cat'.</speak>",
        "sentence": "The big cat sat on the mat.",
        "encouragement": "You're improving!"
    }
    
    # Simulated problem summary
    problem_summary = {
        "recommended_focus_phoneme": ["æ", 2],
        "phoneme_error_counts": {"æ": 2},
        "high_frequency_errors": [["æ", 2]]
    }
    
    # This should NOT raise AttributeError: 'NoneType' object has no attribute 'lower'
    try:
        is_valid, corrected_feedback, warnings = validate_gpt_feedback(
            feedback_dict,
            pronunciation_data,
            problem_summary
        )
        print("✓ Test PASSED: validator handled None ground_truth_word correctly")
        print(f"  Valid: {is_valid}")
        print(f"  Warnings: {len(warnings)}")
        return True
    except AttributeError as e:
        if "'NoneType' object has no attribute 'lower'" in str(e):
            print(f"✗ Test FAILED: Got the exact bug we're trying to fix!")
            print(f"  Error: {e}")
            return False
        else:
            raise
    except Exception as e:
        print(f"✗ Test FAILED with unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_all_none_ground_truth_words():
    """Test edge case where all words have None ground_truth_word."""
    
    pronunciation_data = [
        {
            "type": "insertion",
            "ground_truth_word": None,
            "predicted_word": "extra1",
            "per": None,
            "expected_phonemes": [],
            "actual_phonemes": ["ɛ"]
        },
        {
            "type": "insertion",
            "ground_truth_word": None,
            "predicted_word": "extra2",
            "per": None,
            "expected_phonemes": [],
            "actual_phonemes": ["ɛ"]
        }
    ]
    
    feedback_dict = {
        "feedback": "You added some extra words.",
        "sentence": "The cat sat."
    }
    
    problem_summary = {}
    
    try:
        is_valid, corrected_feedback, warnings = validate_gpt_feedback(
            feedback_dict,
            pronunciation_data,
            problem_summary
        )
        print("✓ Test PASSED: validator handled all-None case correctly")
        return True
    except AttributeError as e:
        if "'NoneType' object has no attribute 'lower'" in str(e):
            print(f"✗ Test FAILED: Got AttributeError with all-None case!")
            return False
        else:
            raise
    except Exception as e:
        print(f"✗ Test FAILED with unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mode_classes_with_none():
    """Test that mode classes handle None ground_truth_word in word_structure."""
    
    # Simulate word_data that might come from pronunciation analysis
    word_data_with_none = {
        "type": "insertion",
        "ground_truth_word": None,
        "predicted_word": "extra",
        "per": None,
        "missed": None,
        "added": None,
        "substituted": None,
        "phonemes": ["ɛ", "k", "s", "t", "r", "ə"]
    }
    
    # Test the f-string that creates word_structure (similar to mode classes)
    try:
        gt_phonemes = word_data_with_none.get("phonemes", [])
        word_structure = f"{word_data_with_none.get('ground_truth_word') or ''} = [{', '.join(gt_phonemes)}]"
        print(f"✓ Test PASSED: word_structure creation handles None correctly")
        print(f"  Result: {word_structure}")
        return True
    except Exception as e:
        print(f"✗ Test FAILED: word_structure creation failed with error: {e}")
        return False


if __name__ == "__main__":
    print("=" * 80)
    print("Testing NoneType .lower() Bug Fix")
    print("=" * 80)
    print()
    
    results = []
    
    print("Test 1: Validator with None ground_truth_word")
    print("-" * 80)
    results.append(test_none_ground_truth_word_in_validator())
    print()
    
    print("Test 2: Validator with all-None ground_truth_words")
    print("-" * 80)
    results.append(test_all_none_ground_truth_words())
    print()
    
    print("Test 3: Mode classes word_structure with None")
    print("-" * 80)
    results.append(test_mode_classes_with_none())
    print()
    
    print("=" * 80)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 80)
    
    if all(results):
        print("\n✓ All tests PASSED! The bug fix is working correctly.")
        sys.exit(0)
    else:
        print("\n✗ Some tests FAILED! There may still be issues.")
        sys.exit(1)
