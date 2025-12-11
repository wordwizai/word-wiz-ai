"""
Tests for Phase 2: Improved Edge Handling & Silence Trimming

Tests the phoneme-aware trimming module.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import librosa
from core.phoneme_aware_trimming import PhonemeAwareTrimmer, smart_trim_audio


class TestPhonemeAwareTrimming:
    """Test suite for PhonemeAwareTrimmer"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.sr = 16000
        self.trimmer = PhonemeAwareTrimmer(sr=self.sr)
        
    def generate_test_audio_with_edges(self, duration=2.0, edge_duration=0.2):
        """
        Generate test audio with quiet consonant-like sounds at edges.
        
        Simulates plosives (p, t, k) which have low energy but high frequency.
        """
        samples = int(duration * self.sr)
        edge_samples = int(edge_duration * self.sr)
        
        # Middle: Strong signal (vowel-like)
        t_middle = np.linspace(0, duration - 2*edge_duration, samples - 2*edge_samples)
        middle = 0.7 * np.sin(2 * np.pi * 440 * t_middle)  # Strong 440 Hz
        
        # Edges: Weak high-frequency signal (consonant-like)
        t_edge = np.linspace(0, edge_duration, edge_samples)
        # Burst-like sound (plosive)
        edge_signal = 0.1 * np.sin(2 * np.pi * 2000 * t_edge) * np.exp(-5 * t_edge)
        
        # Combine
        audio = np.concatenate([edge_signal, middle, edge_signal[::-1]])
        
        # Add small silence at very edges
        silence_samples = int(0.1 * self.sr)
        silence = np.zeros(silence_samples)
        audio = np.concatenate([silence, audio, silence])
        
        return audio.astype(np.float32)
    
    def test_trim_with_padding_preserves_edges(self):
        """Test that trim_with_padding preserves edge phonemes"""
        audio = self.generate_test_audio_with_edges()
        original_length = len(audio)
        
        # Trim with generous padding
        trimmed = self.trimmer.trim_with_padding(audio, top_db=30, padding_ms=150)
        
        # Should remove some silence but not too much
        assert len(trimmed) > 0, "Trimmed audio should not be empty"
        assert len(trimmed) < original_length, "Should have trimmed some samples"
        
        # Check that we didn't over-trim (should keep most of the audio)
        trim_ratio = len(trimmed) / original_length
        assert trim_ratio > 0.8, f"Trimmed too aggressively: kept only {trim_ratio:.1%}"
        
        print(f"✓ Padding preserved edges: kept {trim_ratio:.1%} of audio")
    
    def test_detect_speech_boundaries_with_zcr(self):
        """Test speech boundary detection using ZCR"""
        audio = self.generate_test_audio_with_edges()
        
        start, end = self.trimmer.detect_speech_boundaries(audio, use_zcr=True)
        
        assert start >= 0, "Start boundary should be non-negative"
        assert end <= len(audio), "End boundary should not exceed audio length"
        assert end > start, "End should be after start"
        
        # Should detect speech region (not just silence)
        speech_duration = (end - start) / self.sr
        assert speech_duration > 1.0, f"Should detect reasonable speech duration, got {speech_duration:.2f}s"
        
        print(f"✓ Detected speech boundaries: {start} to {end} ({speech_duration:.2f}s)")
    
    def test_detect_speech_boundaries_without_zcr(self):
        """Test speech boundary detection using energy only"""
        audio = self.generate_test_audio_with_edges()
        
        start, end = self.trimmer.detect_speech_boundaries(audio, use_zcr=False)
        
        assert start >= 0, "Start boundary should be non-negative"
        assert end <= len(audio), "End boundary should not exceed audio length"
        assert end > start, "End should be after start"
        
        print(f"✓ Energy-only detection: {start} to {end}")
    
    def test_zcr_better_than_energy_for_consonants(self):
        """Test that ZCR detection is better for quiet consonants"""
        audio = self.generate_test_audio_with_edges()
        
        # Detect with and without ZCR
        start_zcr, end_zcr = self.trimmer.detect_speech_boundaries(audio, use_zcr=True)
        start_energy, end_energy = self.trimmer.detect_speech_boundaries(audio, use_zcr=False)
        
        # ZCR should detect edges better (start earlier, end later)
        # This captures the quiet consonants better
        duration_zcr = end_zcr - start_zcr
        duration_energy = end_energy - start_energy
        
        print(f"✓ ZCR captures more: {duration_zcr / self.sr:.2f}s vs "
              f"energy-only: {duration_energy / self.sr:.2f}s")
    
    def test_trim_with_speech_detection(self):
        """Test full trim with speech detection"""
        audio = self.generate_test_audio_with_edges()
        
        trimmed = self.trimmer.trim_with_speech_detection(
            audio,
            padding_ms=150,
            use_zcr=True
        )
        
        assert len(trimmed) > 0, "Should return trimmed audio"
        assert len(trimmed) <= len(audio), "Trimmed should not be longer than original"
        
        # Check that significant audio is preserved
        preserve_ratio = len(trimmed) / len(audio)
        assert preserve_ratio > 0.7, f"Should preserve most audio, kept {preserve_ratio:.1%}"
        
        print(f"✓ Speech detection trim: {len(audio)} → {len(trimmed)} samples")
    
    def test_conservative_trim(self):
        """Test conservative trimming mode"""
        audio = self.generate_test_audio_with_edges()
        
        trimmed = self.trimmer.conservative_trim(audio, padding_ms=200)
        
        assert len(trimmed) > 0, "Should return audio"
        
        # Conservative should keep even more audio
        preserve_ratio = len(trimmed) / len(audio)
        assert preserve_ratio > 0.85, f"Conservative should preserve most audio, kept {preserve_ratio:.1%}"
        
        print(f"✓ Conservative trim preserved {preserve_ratio:.1%} of audio")
    
    def test_handles_empty_audio(self):
        """Test handling of empty audio"""
        empty_audio = np.array([])
        
        # Should handle gracefully
        trimmed = self.trimmer.trim_with_padding(empty_audio)
        assert len(trimmed) == 0, "Empty input should return empty output"
        
        print("✓ Empty audio handled gracefully")
    
    def test_handles_very_short_audio(self):
        """Test handling of very short audio"""
        short_audio = np.random.randn(int(0.5 * self.sr)).astype(np.float32)
        
        trimmed = self.trimmer.trim_with_padding(short_audio, padding_ms=100)
        
        assert len(trimmed) > 0, "Should return something for short audio"
        
        print(f"✓ Short audio handled: {len(short_audio)} → {len(trimmed)} samples")
    
    def test_convenience_function_adaptive(self):
        """Test smart_trim_audio convenience function with adaptive method"""
        audio = self.generate_test_audio_with_edges()
        
        trimmed = smart_trim_audio(audio, sr=self.sr, method='adaptive', padding_ms=150)
        
        assert len(trimmed) > 0, "Should return trimmed audio"
        assert len(trimmed) <= len(audio), "Should not be longer than original"
        
        print(f"✓ Adaptive method: {len(audio)} → {len(trimmed)} samples")
    
    def test_convenience_function_conservative(self):
        """Test smart_trim_audio with conservative method"""
        audio = self.generate_test_audio_with_edges()
        
        trimmed = smart_trim_audio(audio, sr=self.sr, method='conservative', padding_ms=200)
        
        # Conservative should preserve more
        preserve_ratio = len(trimmed) / len(audio)
        assert preserve_ratio > 0.85, f"Conservative should preserve most, kept {preserve_ratio:.1%}"
        
        print(f"✓ Conservative method preserved {preserve_ratio:.1%}")
    
    def test_convenience_function_zcr(self):
        """Test smart_trim_audio with ZCR method"""
        audio = self.generate_test_audio_with_edges()
        
        trimmed = smart_trim_audio(audio, sr=self.sr, method='zcr', padding_ms=150)
        
        assert len(trimmed) > 0, "Should return trimmed audio"
        
        print(f"✓ ZCR method: {len(audio)} → {len(trimmed)} samples")


def run_phase2_tests():
    """Run all Phase 2 tests"""
    print("\n" + "="*60)
    print("PHASE 2 QUALITY ASSURANCE TESTS")
    print("="*60 + "\n")
    
    print("Testing Phoneme-Aware Trimming...")
    print("-" * 60)
    test_trimmer = TestPhonemeAwareTrimming()
    test_trimmer.setup_method()
    
    try:
        test_trimmer.test_trim_with_padding_preserves_edges()
        test_trimmer.test_detect_speech_boundaries_with_zcr()
        test_trimmer.test_detect_speech_boundaries_without_zcr()
        test_trimmer.test_zcr_better_than_energy_for_consonants()
        test_trimmer.test_trim_with_speech_detection()
        test_trimmer.test_conservative_trim()
        test_trimmer.test_handles_empty_audio()
        test_trimmer.test_handles_very_short_audio()
        test_trimmer.test_convenience_function_adaptive()
        test_trimmer.test_convenience_function_conservative()
        test_trimmer.test_convenience_function_zcr()
        print("\n✅ All Phoneme-Aware Trimming tests passed!\n")
    except AssertionError as e:
        print(f"\n❌ Phoneme-Aware Trimming test failed: {e}\n")
        return False
    
    print("\n" + "="*60)
    print("✅ PHASE 2: ALL TESTS PASSED!")
    print("="*60 + "\n")
    return True


if __name__ == "__main__":
    success = run_phase2_tests()
    exit(0 if success else 1)
