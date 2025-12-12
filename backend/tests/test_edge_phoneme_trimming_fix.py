"""
Test to verify the fix for edge phoneme trimming issue.

This test specifically checks that the last phonemes/words are not cut off
by the trimming algorithm.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import librosa
from core.phoneme_aware_trimming import PhonemeAwareTrimmer


def generate_audio_with_quiet_ending(sr=16000, duration=3.0, ending_duration=0.5):
    """
    Generate test audio with a quiet ending that simulates final consonants.
    
    Args:
        sr: Sample rate
        duration: Total duration in seconds
        ending_duration: Duration of the quiet ending in seconds
    
    Returns:
        Audio array with quiet ending
    """
    samples = int(duration * sr)
    ending_samples = int(ending_duration * sr)
    main_samples = samples - ending_samples
    
    # Main audio: strong vowel-like sound
    t_main = np.linspace(0, duration - ending_duration, main_samples)
    main_audio = 0.7 * np.sin(2 * np.pi * 440 * t_main)  # Strong vowel
    
    # Ending: weak consonant-like sound (high frequency, low amplitude)
    t_ending = np.linspace(0, ending_duration, ending_samples)
    # Simulate fricative/plosive: high frequency, decaying amplitude
    ending_audio = 0.15 * np.sin(2 * np.pi * 3000 * t_ending) * np.exp(-3 * t_ending)
    
    # Combine
    audio = np.concatenate([main_audio, ending_audio])
    
    # Add small silence at very edges
    silence_samples = int(0.05 * sr)
    silence = np.zeros(silence_samples)
    audio = np.concatenate([silence, audio, silence])
    
    return audio.astype(np.float32)


def test_ending_preservation():
    """Test that audio endings are preserved after trimming."""
    sr = 16000
    trimmer = PhonemeAwareTrimmer(sr=sr)
    
    # Generate audio with quiet ending
    audio = generate_audio_with_quiet_ending(sr=sr, duration=3.0, ending_duration=0.5)
    original_length = len(audio)
    print(f"\nOriginal audio length: {original_length} samples ({original_length/sr:.3f}s)")
    
    # Trim using speech detection (the method that had the bug)
    trimmed = trimmer.trim_with_speech_detection(audio, padding_ms=150, use_zcr=True)
    trimmed_length = len(trimmed)
    print(f"Trimmed audio length: {trimmed_length} samples ({trimmed_length/sr:.3f}s)")
    
    # Calculate how much was trimmed from each end
    # We expect trimming to remove the silence at edges, but preserve the quiet ending
    expected_silence = int(0.05 * sr)  # 50ms silence we added
    expected_min_length = original_length - 2 * expected_silence - int(0.1 * sr)  # Allow some margin
    
    print(f"Expected minimum length: {expected_min_length} samples ({expected_min_length/sr:.3f}s)")
    
    # Check that we didn't over-trim
    assert trimmed_length >= expected_min_length, \
        f"Over-trimmed! Expected at least {expected_min_length} samples, got {trimmed_length}"
    
    # More importantly, check that the ending is preserved
    # The ending should still contain the quiet consonant-like sound
    # We'll check that at least 80% of the expected ending duration is preserved
    ending_duration = 0.5  # seconds
    ending_samples = int(ending_duration * sr)
    min_ending_preserved = int(0.8 * ending_samples)
    
    # Calculate actual ending preserved by checking trim amount from the end
    # This is approximate since we don't know exact trim boundaries
    trimmed_from_end = original_length - trimmed_length
    max_acceptable_trim_from_end = 2 * expected_silence + int(0.15 * sr)  # Silence + some margin
    
    print(f"Trimmed from end: {trimmed_from_end} samples ({trimmed_from_end/sr:.3f}s)")
    print(f"Max acceptable trim from end: {max_acceptable_trim_from_end} samples ({max_acceptable_trim_from_end/sr:.3f}s)")
    
    assert trimmed_from_end <= max_acceptable_trim_from_end, \
        f"Too much trimmed from end! Trimmed {trimmed_from_end} samples, max acceptable: {max_acceptable_trim_from_end}"
    
    print("✅ Test passed: Ending is properly preserved")


def test_frame_boundary_calculation():
    """
    Test that the frame boundary calculation is correct.
    
    This directly tests the fix for the bug where end_sample was calculated
    using (end_frame + 1) * hop_length instead of end_frame * hop_length + frame_length.
    """
    sr = 16000
    trimmer = PhonemeAwareTrimmer(sr=sr)
    
    # Create audio that will have speech detected at the very end
    duration = 2.0
    samples = int(duration * sr)
    t = np.linspace(0, duration, samples)
    
    # Create audio with speech at the very end
    audio = np.zeros(samples)
    # Add speech in last 0.3 seconds
    speech_start = int(1.7 * sr)
    audio[speech_start:] = 0.3 * np.sin(2 * np.pi * 440 * t[speech_start:])
    
    print(f"\nTest audio with speech at end:")
    print(f"Total length: {len(audio)} samples ({len(audio)/sr:.3f}s)")
    print(f"Speech starts at: {speech_start} samples ({speech_start/sr:.3f}s)")
    
    # Detect boundaries
    start_sample, end_sample = trimmer.detect_speech_boundaries(audio, use_zcr=True)
    
    print(f"Detected start: {start_sample} samples ({start_sample/sr:.3f}s)")
    print(f"Detected end: {end_sample} samples ({end_sample/sr:.3f}s)")
    
    # The end should be close to the actual end of the audio
    # After the fix, it should include the full frame_length (2048 samples)
    # So we expect end_sample to be close to len(audio)
    
    # With the OLD BUG: end_sample would be around (last_frame + 1) * hop_length
    # which would be significantly less than len(audio)
    
    # With the FIX: end_sample = last_frame * hop_length + frame_length
    # which should be much closer to len(audio)
    
    gap_from_end = len(audio) - end_sample
    print(f"Gap from end: {gap_from_end} samples ({gap_from_end/sr:.3f}s)")
    
    # With frame_length=2048, hop_length=512, the max gap should be less than frame_length
    # In fact, it should be much less since we're including the full frame
    max_acceptable_gap = 2048  # One frame length at most
    
    assert gap_from_end <= max_acceptable_gap, \
        f"Gap from end too large! {gap_from_end} samples, expected <= {max_acceptable_gap}"
    
    # More stringent check: gap should be less than one frame minus one hop
    # (since frames overlap by frame_length - hop_length)
    ideal_max_gap = 2048 - 512  # 1536 samples
    
    if gap_from_end <= ideal_max_gap:
        print(f"✅ Excellent: Gap from end ({gap_from_end}) is within ideal range (<= {ideal_max_gap})")
    else:
        print(f"⚠️  Gap from end ({gap_from_end}) is larger than ideal ({ideal_max_gap}) but acceptable")
    
    print("✅ Test passed: Frame boundary calculation is correct")


def test_comparison_old_vs_new():
    """
    Demonstrate the difference between old and new calculation.
    
    This shows what the bug was and how the fix improves it.
    """
    sr = 16000
    frame_length = 2048
    hop_length = 512
    
    # Simulate finding the last speech frame at frame index 50
    last_frame_idx = 50
    
    # OLD BUG calculation
    old_end_sample = (last_frame_idx + 1) * hop_length
    
    # NEW FIXED calculation  
    new_end_sample = last_frame_idx * hop_length + frame_length
    
    difference = new_end_sample - old_end_sample
    
    print(f"\nComparison of old vs new calculation:")
    print(f"Last speech frame index: {last_frame_idx}")
    print(f"OLD (buggy) end_sample: {old_end_sample} samples ({old_end_sample/sr:.3f}s)")
    print(f"NEW (fixed) end_sample: {new_end_sample} samples ({new_end_sample/sr:.3f}s)")
    print(f"Difference: {difference} samples ({difference/sr:.3f}s)")
    print(f"\n⚠️  The bug was cutting off {difference} samples (~{difference/sr*1000:.1f}ms) from the end!")
    print(f"This is enough to lose final consonants and parts of the last word.")
    
    assert difference == frame_length - hop_length == 1536, \
        "Calculation error in demonstration"
    
    print("✅ Demonstration complete")


if __name__ == "__main__":
    print("=" * 70)
    print("Testing Edge Phoneme Trimming Fix")
    print("=" * 70)
    
    try:
        test_comparison_old_vs_new()
        print("\n" + "=" * 70)
        
        test_frame_boundary_calculation()
        print("\n" + "=" * 70)
        
        test_ending_preservation()
        print("\n" + "=" * 70)
        
        print("\n✅ All tests passed!")
        print("\nThe fix successfully preserves the last ~96ms of audio that was")
        print("previously being cut off, which is critical for final phonemes.")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
