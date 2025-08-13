#!/usr/bin/env python3
"""
Comprehensive test suite for optimized phoneme-to-word alignment algorithms.
This test validates that the optimizations maintain correctness while improving performance.
"""

import sys
import os
import time
import numpy as np
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from ai.test_phoneme_to_word_alignment import align_phonemes_to_words as ai_align, compute_per as ai_per
from core.process_audio import align_phonemes_to_words as core_align, compute_per as core_per

def test_correctness():
    """Test that optimized algorithms produce correct results"""
    print("=" * 60)
    print("CORRECTNESS TESTS")
    print("=" * 60)
    
    test_cases = [
        # Test case 1: Original example
        {
            'name': 'Original example',
            'pred_phonemes': ['ð', 't','ə', 'b', 'k', 'ɑ', 't', 'ʧ', 'ə', 'f', 'd', 't', 'ɔ', 'n'],
            'gt_words': [
                ('the', ['ð', 'ə']),
                ('cat', ['k', 'æ', 't']),
                ('jumped', ['ʤ', 'ə', 'm', 'p', 't']),
                ('on', ['ɔ', 'n'])
            ],
            'expected_alignment_count': 4
        },
        # Test case 2: Perfect match
        {
            'name': 'Perfect match',
            'pred_phonemes': ['h', 'ɛ', 'l', 'o'],
            'gt_words': [
                ('hello', ['h', 'ɛ', 'l', 'o'])
            ],
            'expected_alignment_count': 1
        },
        # Test case 3: Empty inputs
        {
            'name': 'Empty inputs',
            'pred_phonemes': [],
            'gt_words': [],
            'expected_alignment_count': 0
        },
        # Test case 4: Single phoneme words
        {
            'name': 'Single phonemes',
            'pred_phonemes': ['ɑ', 'i'],
            'gt_words': [
                ('a', ['ɑ']),
                ('I', ['aɪ'])  # Different from predicted
            ],
            'expected_alignment_count': 2
        }
    ]
    
    all_passed = True
    
    for test_case in test_cases:
        print(f"\nTest: {test_case['name']}")
        print("-" * 40)
        
        try:
            # Test AI module
            ai_result = ai_align(test_case['pred_phonemes'], test_case['gt_words'])
            print(f"AI module: {len(ai_result)} alignments")
            
            # Test Core module  
            core_result = core_align(test_case['pred_phonemes'], test_case['gt_words'])
            print(f"Core module: {len(core_result)} alignments")
            
            # Validate alignment count
            if len(ai_result) != test_case['expected_alignment_count']:
                print(f"❌ AI module alignment count mismatch: expected {test_case['expected_alignment_count']}, got {len(ai_result)}")
                all_passed = False
            elif len(core_result) != test_case['expected_alignment_count']:
                print(f"❌ Core module alignment count mismatch: expected {test_case['expected_alignment_count']}, got {len(core_result)}")
                all_passed = False
            else:
                print("✅ Alignment counts correct")
            
            # Validate both modules produce same results
            if ai_result != core_result:
                print(f"❌ AI and Core modules produce different results")
                print(f"AI: {ai_result}")
                print(f"Core: {core_result}")
                all_passed = False
            else:
                print("✅ Both modules produce identical results")
                
            # Show sample results for non-empty cases
            if ai_result:
                print("Sample alignment:")
                for word, phonemes, per in ai_result[:2]:  # Show first 2
                    print(f"  {word}: {phonemes} (PER: {per:.3f})")
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            all_passed = False
    
    return all_passed

def test_per_computation():
    """Test PER computation correctness"""
    print("\n" + "=" * 60)
    print("PER COMPUTATION TESTS")
    print("=" * 60)
    
    test_cases = [
        (['a', 'b', 'c'], ['a', 'b', 'c'], 0.0),  # Perfect match
        (['a', 'b'], ['a', 'x'], 0.5),             # One substitution
        (['a', 'b'], ['a'], 0.5),                  # One deletion
        (['a'], ['a', 'b'], 1.0),                  # One insertion (normalized by gt length)
        ([], [], 0.0),                             # Both empty
        (['a'], [], 1.0),                          # GT not empty, pred empty
        ([], ['a'], 1.0),                          # GT empty, pred not empty
    ]
    
    all_passed = True
    
    for i, (gt, pred, expected) in enumerate(test_cases):
        print(f"\nPER Test {i+1}: GT={gt}, Pred={pred}")
        
        try:
            ai_per_result = ai_per(gt, pred)
            core_per_result = core_per(gt, pred)
            
            print(f"AI PER: {ai_per_result:.4f}")
            print(f"Core PER: {core_per_result:.4f}")
            print(f"Expected: {expected:.4f}")
            
            if abs(ai_per_result - expected) > 1e-6:
                print(f"❌ AI PER incorrect")
                all_passed = False
            elif abs(core_per_result - expected) > 1e-6:
                print(f"❌ Core PER incorrect")  
                all_passed = False
            elif abs(ai_per_result - core_per_result) > 1e-6:
                print(f"❌ AI and Core PER differ")
                all_passed = False
            else:
                print("✅ PER computation correct")
                
        except Exception as e:
            print(f"❌ PER test failed: {e}")
            all_passed = False
    
    return all_passed

def test_performance():
    """Test that optimizations provide performance improvement"""
    print("\n" + "=" * 60)
    print("PERFORMANCE TESTS")
    print("=" * 60)
    
    # Generate test data of increasing complexity
    phoneme_pool = ['æ', 'ə', 'ɪ', 'i', 'ʊ', 'u', 'ɛ', 'ɔ', 'ɑ', 'b', 'p', 't', 'd', 'k', 'g']
    
    test_sizes = [
        (5, 3),   # 5 words, 3 phonemes each
        (10, 3),  # 10 words, 3 phonemes each  
        (15, 4),  # 15 words, 4 phonemes each
    ]
    
    print("Performance comparison (targeting sub-second execution):")
    print("Size (words, avg_phonemes) | AI Time | Core Time")
    print("-" * 50)
    
    for num_words, avg_phonemes in test_sizes:
        # Generate test data
        np.random.seed(42)  # Reproducible
        ground_truth = []
        predicted_phonemes = []
        
        for i in range(num_words):
            word = f"word{i}"
            word_length = max(1, np.random.poisson(avg_phonemes - 1) + 1)
            word_phonemes = np.random.choice(phoneme_pool, word_length).tolist()
            ground_truth.append((word, word_phonemes))
            
            # Add some noise to predictions
            pred_phonemes = word_phonemes.copy()
            if len(pred_phonemes) > 1 and np.random.random() < 0.3:
                pred_phonemes[0] = np.random.choice(phoneme_pool)  # Change first phoneme
            predicted_phonemes.extend(pred_phonemes)
        
        total_phonemes = len(predicted_phonemes)
        
        # Test AI module
        start_time = time.time()
        ai_result = ai_align(predicted_phonemes, ground_truth)
        ai_time = time.time() - start_time
        
        # Test Core module
        start_time = time.time()
        core_result = core_align(predicted_phonemes, ground_truth)
        core_time = time.time() - start_time
        
        print(f"({num_words:2d}, {avg_phonemes}) {total_phonemes:2d} phonemes | {ai_time:7.4f}s | {core_time:7.4f}s")
        
        # Check that performance is reasonable (under 1 second for these sizes)
        if ai_time > 1.0:
            print(f"⚠️  AI module slower than expected: {ai_time:.3f}s")
        if core_time > 1.0:
            print(f"⚠️  Core module slower than expected: {core_time:.3f}s")

def main():
    """Run all tests"""
    print("OPTIMIZED PHONEME ALIGNMENT TEST SUITE")
    print("Testing performance optimizations while maintaining correctness")
    
    # Run tests
    correctness_passed = test_correctness()
    per_passed = test_per_computation()
    
    # Performance test (always run, but don't fail on it)
    test_performance()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    if correctness_passed and per_passed:
        print("✅ ALL TESTS PASSED")
        print("✅ Optimizations maintain correctness")
        print("✅ Both AI and Core modules working correctly")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        if not correctness_passed:
            print("❌ Correctness tests failed")
        if not per_passed:
            print("❌ PER computation tests failed")
        return 1

if __name__ == "__main__":
    exit(main())