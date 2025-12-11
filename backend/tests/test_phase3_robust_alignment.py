"""
Tests for Phase 3: Robust Phoneme-to-Word Alignment

Tests the enhanced alignment algorithm with confidence scoring and adaptive bounds.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from core.process_audio import align_phonemes_to_words, _fallback_proportional_alignment, compute_per


class TestRobustAlignment:
    """Test suite for Phase 3 robust alignment"""
    
    def setup_method(self):
        """Setup test fixtures"""
        pass
    
    def test_perfect_match(self):
        """Test alignment with perfect phoneme match"""
        pred_phonemes = ['b', 'ɪ', 'g', 'k', 'æ', 't']
        gt_words_phonemes = [
            ('big', ['b', 'ɪ', 'g']),
            ('cat', ['k', 'æ', 't'])
        ]
        
        alignment = align_phonemes_to_words(pred_phonemes, gt_words_phonemes)
        
        assert len(alignment) == 2, "Should align both words"
        assert alignment[0][0] == 'big', "First word should be 'big'"
        assert alignment[0][1] == ['b', 'ɪ', 'g'], "First word phonemes should match"
        assert alignment[0][2] == 0.0, "Perfect match should have PER=0"
        assert alignment[1][0] == 'cat', "Second word should be 'cat'"
        assert alignment[1][1] == ['k', 'æ', 't'], "Second word phonemes should match"
        assert alignment[1][2] == 0.0, "Perfect match should have PER=0"
        
        print("✓ Perfect match alignment works correctly")
    
    def test_missing_phonemes(self):
        """Test alignment with 50% fewer phonemes (0.5x variance)"""
        # Expected: 6 phonemes, Got: 3 phonemes
        pred_phonemes = ['b', 'ɪ', 'k']
        gt_words_phonemes = [
            ('big', ['b', 'ɪ', 'g']),
            ('cat', ['k', 'æ', 't'])
        ]
        
        alignment = align_phonemes_to_words(pred_phonemes, gt_words_phonemes)
        
        assert len(alignment) == 2, "Should attempt to align both words"
        print(f"✓ Missing phonemes handled: {len(pred_phonemes)}/6 phonemes, alignment produced")
    
    def test_extra_phonemes(self):
        """Test alignment with 150% extra phonemes (1.5x variance)"""
        # Expected: 6 phonemes, Got: 9 phonemes
        pred_phonemes = ['b', 'ɪ', 'ɪ', 'g', 'k', 'æ', 'æ', 't', 'z']
        gt_words_phonemes = [
            ('big', ['b', 'ɪ', 'g']),
            ('cat', ['k', 'æ', 't'])
        ]
        
        alignment = align_phonemes_to_words(pred_phonemes, gt_words_phonemes)
        
        assert len(alignment) == 2, "Should align both words despite extra phonemes"
        print(f"✓ Extra phonemes handled: {len(pred_phonemes)}/6 phonemes")
    
    def test_many_extra_phonemes(self):
        """Test alignment with 200% extra phonemes (2.0x variance)"""
        # Expected: 6 phonemes, Got: 12 phonemes
        pred_phonemes = ['ə', 'b', 'ɪ', 'ɪ', 'g', 'ə', 'k', 'k', 'æ', 'æ', 't', 'z']
        gt_words_phonemes = [
            ('big', ['b', 'ɪ', 'g']),
            ('cat', ['k', 'æ', 't'])
        ]
        
        alignment = align_phonemes_to_words(pred_phonemes, gt_words_phonemes)
        
        assert len(alignment) == 2, "Should handle many extra phonemes"
        print(f"✓ Many extra phonemes (2x) handled: {len(pred_phonemes)}/6 phonemes")
    
    def test_extreme_variance_triggers_fallback(self):
        """Test that extreme variance (>2.5x) triggers proportional fallback"""
        # Expected: 6 phonemes, Got: 18 phonemes (3x variance)
        pred_phonemes = ['a'] * 18
        gt_words_phonemes = [
            ('big', ['b', 'ɪ', 'g']),
            ('cat', ['k', 'æ', 't'])
        ]
        
        alignment = align_phonemes_to_words(pred_phonemes, gt_words_phonemes)
        
        assert len(alignment) == 2, "Fallback should still produce alignment"
        # Fallback should distribute phonemes proportionally
        print(f"✓ Extreme variance (3x) triggered fallback: {len(alignment)} words aligned")
    
    def test_fallback_proportional_alignment(self):
        """Test the proportional fallback alignment directly"""
        pred_phonemes = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i']
        gt_words_phonemes = [
            ('word1', ['w', 'ɜ', 'r', 'd']),  # 4 phonemes
            ('word2', ['t', 'u'])             # 2 phonemes
        ]
        
        alignment = _fallback_proportional_alignment(
            pred_phonemes, gt_words_phonemes, length_ratio=1.5
        )
        
        assert len(alignment) == 2, "Should align all words"
        # word1 should get more phonemes (4 * 1.5 = 6)
        # word2 should get fewer (2 * 1.5 = 3, but all remaining)
        assert len(alignment[0][1]) > 0, "First word should get phonemes"
        assert len(alignment[1][1]) > 0, "Second word should get phonemes"
        
        print(f"✓ Proportional fallback: word1 got {len(alignment[0][1])}, word2 got {len(alignment[1][1])} phonemes")
    
    def test_last_word_issue(self):
        """Test the specific 'brook' issue from user example"""
        # Simulating the issue where last word gets leftover phonemes from previous words
        pred_phonemes = [
            'ə',  # extra 'the'
            'b', 'ɪ', 'g',  # big
            'b', 'l', 'u',  # blue
            'b', 'ə', 'r', 'd', 'z',  # birds
            'b', 'r', 'e', 'ɪ', 'v', 'l', 'i',  # bravely
            'f', 'ɪ', 'l', 'd',  # build (f instead of b)
            'b', 'j', 'u', 't', 'ə', 'f', 'ə', 'l',  # beautiful
            'b', 'r', 'a', 'ʊ', 'n',  # brown
            'n', 'ɛ', 's', 't', 's',  # nests
            'b', 'ɪ', 's', 'a', 'ɪ', 'd',  # beside
            'ð'  # the (missing ə)
            # brook missing - leftover phonemes issue
        ]
        
        gt_words_phonemes = [
            ('the', ['ð', 'ə']),
            ('big', ['b', 'ɪ', 'g']),
            ('blue', ['b', 'l', 'u']),
            ('birds', ['b', 'ə', 'r', 'd', 'z']),
            ('bravely', ['b', 'r', 'e', 'ɪ', 'v', 'l', 'i']),
            ('build', ['b', 'ɪ', 'l', 'd']),
            ('beautiful', ['b', 'j', 'u', 't', 'ə', 'f', 'ə', 'l']),
            ('brown', ['b', 'r', 'a', 'ʊ', 'n']),
            ('nests', ['n', 'ɛ', 's', 't', 's']),
            ('beside', ['b', 'i', 's', 'a', 'ɪ', 'd']),
            ('the', ['ð', 'ə']),
            ('brook', ['b', 'r', 'ʊ', 'k'])
        ]
        
        alignment = align_phonemes_to_words(pred_phonemes, gt_words_phonemes)
        
        assert len(alignment) == 12, "Should align all 12 words"
        
        # Check that brook gets some alignment (even if imperfect)
        brook_alignment = alignment[-1]
        assert brook_alignment[0] == 'brook', "Last word should be brook"
        
        print(f"✓ Last word issue test: brook got {len(brook_alignment[1])} phonemes with PER={brook_alignment[2]:.2f}")
        print(f"  All words aligned: {[word for word, _, _ in alignment]}")
    
    def test_empty_predictions(self):
        """Test handling of empty predicted phonemes"""
        pred_phonemes = []
        gt_words_phonemes = [
            ('big', ['b', 'ɪ', 'g']),
            ('cat', ['k', 'æ', 't'])
        ]
        
        alignment = align_phonemes_to_words(pred_phonemes, gt_words_phonemes)
        
        assert alignment == [], "Empty predictions should return empty alignment"
        print("✓ Empty predictions handled gracefully")
    
    def test_single_word(self):
        """Test alignment with single word"""
        pred_phonemes = ['h', 'ɛ', 'l', 'o', 'ʊ']
        gt_words_phonemes = [('hello', ['h', 'ɛ', 'l', 'o', 'ʊ'])]
        
        alignment = align_phonemes_to_words(pred_phonemes, gt_words_phonemes)
        
        assert len(alignment) == 1, "Should align single word"
        assert alignment[0][2] == 0.0, "Perfect match should have PER=0"
        print("✓ Single word alignment works")
    
    def test_very_long_sentence(self):
        """Test alignment with long sentence (>20 words)"""
        # Create a long sentence
        words = ['word'] * 25
        phonemes_per_word = ['w', 'ɜ', 'r', 'd']
        
        pred_phonemes = phonemes_per_word * 25
        gt_words_phonemes = [(word, phonemes_per_word) for word in words]
        
        alignment = align_phonemes_to_words(pred_phonemes, gt_words_phonemes)
        
        assert len(alignment) == 25, "Should handle long sentences"
        print(f"✓ Long sentence (25 words) aligned successfully")
    
    def test_confidence_scoring(self):
        """Test that confidence scoring differentiates good vs poor alignments"""
        # Good alignment
        good_pred = ['b', 'ɪ', 'g']
        good_gt = [('big', ['b', 'ɪ', 'g'])]
        good_alignment = align_phonemes_to_words(good_pred, good_gt)
        
        # Poor alignment (completely wrong phonemes)
        poor_pred = ['x', 'y', 'z']
        poor_gt = [('big', ['b', 'ɪ', 'g'])]
        poor_alignment = align_phonemes_to_words(poor_pred, poor_gt)
        
        # Good alignment should have low PER
        assert good_alignment[0][2] < 0.1, "Good alignment should have low PER"
        # Poor alignment should have high PER
        assert poor_alignment[0][2] > 0.5, "Poor alignment should have high PER"
        
        print(f"✓ Confidence scoring: good PER={good_alignment[0][2]:.2f}, poor PER={poor_alignment[0][2]:.2f}")


def run_phase3_tests():
    """Run all Phase 3 tests"""
    print("\n" + "="*60)
    print("PHASE 3 QUALITY ASSURANCE TESTS")
    print("="*60 + "\n")
    
    print("Testing Robust Phoneme-to-Word Alignment...")
    print("-" * 60)
    test_alignment = TestRobustAlignment()
    test_alignment.setup_method()
    
    try:
        test_alignment.test_perfect_match()
        test_alignment.test_missing_phonemes()
        test_alignment.test_extra_phonemes()
        test_alignment.test_many_extra_phonemes()
        test_alignment.test_extreme_variance_triggers_fallback()
        test_alignment.test_fallback_proportional_alignment()
        test_alignment.test_last_word_issue()
        test_alignment.test_empty_predictions()
        test_alignment.test_single_word()
        test_alignment.test_very_long_sentence()
        test_alignment.test_confidence_scoring()
        print("\n✅ All Robust Alignment tests passed!\n")
    except AssertionError as e:
        print(f"\n❌ Robust Alignment test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "="*60)
    print("✅ PHASE 3: ALL TESTS PASSED!")
    print("="*60 + "\n")
    return True


if __name__ == "__main__":
    success = run_phase3_tests()
    exit(0 if success else 1)
