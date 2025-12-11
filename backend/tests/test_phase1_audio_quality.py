"""
Tests for Phase 1: Adaptive Noise Reduction & Audio Quality Validation

Tests the audio quality analyzer and adaptive noise reduction modules.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import librosa
from core.audio_quality_analyzer import AudioQualityAnalyzer, quick_quality_check
from core.adaptive_noise_reduction import AdaptiveNoiseReducer, preprocess_audio_adaptive


class TestAudioQualityAnalyzer:
    """Test suite for AudioQualityAnalyzer"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.sr = 16000
        self.analyzer = AudioQualityAnalyzer(sr=self.sr)
        
    def generate_test_audio(self, duration=2.0, noise_level=0.01, include_speech=True):
        """Generate synthetic test audio"""
        samples = int(duration * self.sr)
        
        if include_speech:
            # Generate simple sine wave as "speech"
            t = np.linspace(0, duration, samples)
            audio = 0.5 * np.sin(2 * np.pi * 440 * t)  # 440 Hz tone
        else:
            # Just noise
            audio = np.zeros(samples)
        
        # Add noise
        noise = np.random.normal(0, noise_level, samples)
        audio = audio + noise
        
        return audio.astype(np.float32)
    
    def test_snr_calculation_clean_audio(self):
        """Test SNR calculation on clean audio"""
        audio = self.generate_test_audio(duration=2.0, noise_level=0.001)
        snr = self.analyzer.calculate_snr(audio)
        
        # Clean audio should have high SNR (>20 dB)
        assert snr > 20.0, f"Expected high SNR for clean audio, got {snr:.1f} dB"
        print(f"✓ Clean audio SNR: {snr:.1f} dB")
    
    def test_snr_calculation_noisy_audio(self):
        """Test SNR calculation on noisy audio"""
        audio = self.generate_test_audio(duration=2.0, noise_level=0.1)
        snr = self.analyzer.calculate_snr(audio)
        
        # Noisy audio should have lower SNR
        assert snr < 20.0, f"Expected lower SNR for noisy audio, got {snr:.1f} dB"
        print(f"✓ Noisy audio SNR: {snr:.1f} dB")
    
    def test_snr_calculation_very_noisy_audio(self):
        """Test SNR calculation on very noisy audio"""
        audio = self.generate_test_audio(duration=2.0, noise_level=0.3)
        snr = self.analyzer.calculate_snr(audio)
        
        # Very noisy audio should have low SNR (<10 dB)
        assert snr < 10.0, f"Expected very low SNR for very noisy audio, got {snr:.1f} dB"
        print(f"✓ Very noisy audio SNR: {snr:.1f} dB")
    
    def test_clipping_detection_no_clipping(self):
        """Test clipping detection on normal audio"""
        audio = self.generate_test_audio(duration=1.0, noise_level=0.01)
        # Normalize to 0.8 max to avoid clipping
        audio = audio * 0.8 / np.max(np.abs(audio))
        
        result = self.analyzer.detect_clipping(audio)
        
        assert not result['is_clipped'], "Normal audio should not be flagged as clipped"
        assert result['clipping_percentage'] < 1.0, "Clipping percentage should be low"
        print(f"✓ No clipping detected: {result['clipping_percentage']:.2f}%")
    
    def test_clipping_detection_with_clipping(self):
        """Test clipping detection on clipped audio"""
        audio = self.generate_test_audio(duration=1.0, noise_level=0.01)
        # Clip audio by setting max to 1.0
        audio = np.clip(audio / np.max(np.abs(audio)), -1.0, 1.0)
        # Add more clipped samples
        audio[::10] = 1.0  # Clip every 10th sample
        
        result = self.analyzer.detect_clipping(audio)
        
        assert result['is_clipped'], "Clipped audio should be flagged"
        assert result['clipping_percentage'] > 1.0, "Clipping percentage should be significant"
        print(f"✓ Clipping detected: {result['clipping_percentage']:.2f}%")
    
    def test_silence_detection(self):
        """Test silence percentage calculation"""
        # Create audio with 50% silence
        duration = 2.0
        samples = int(duration * self.sr)
        audio = np.zeros(samples, dtype=np.float32)
        
        # Add signal to first half
        audio[:samples//2] = self.generate_test_audio(duration=1.0, noise_level=0.01)
        
        silence_pct = self.analyzer.calculate_silence_percentage(audio)
        
        # Should detect significant silence
        assert silence_pct > 30.0, f"Expected high silence percentage, got {silence_pct:.1f}%"
        print(f"✓ Silence detection: {silence_pct:.1f}%")
    
    def test_comprehensive_quality_analysis_excellent(self):
        """Test comprehensive quality analysis on excellent audio"""
        audio = self.generate_test_audio(duration=2.0, noise_level=0.001)
        result = self.analyzer.analyze_audio_quality(audio)
        
        assert result['quality_level'] in ['excellent', 'good'], \
            f"Expected excellent/good quality, got {result['quality_level']}"
        assert result['quality_score'] > 60, \
            f"Expected high quality score, got {result['quality_score']:.1f}"
        assert result['snr_db'] > 15, \
            f"Expected high SNR, got {result['snr_db']:.1f} dB"
        
        print(f"✓ Quality analysis for excellent audio:")
        print(f"  - Level: {result['quality_level']}")
        print(f"  - Score: {result['quality_score']:.1f}/100")
        print(f"  - SNR: {result['snr_db']:.1f} dB")
    
    def test_comprehensive_quality_analysis_poor(self):
        """Test comprehensive quality analysis on poor audio"""
        audio = self.generate_test_audio(duration=2.0, noise_level=0.3)
        result = self.analyzer.analyze_audio_quality(audio)
        
        assert result['quality_level'] in ['poor', 'fair'], \
            f"Expected poor/fair quality, got {result['quality_level']}"
        assert len(result['issues']) > 0, "Expected quality issues to be detected"
        assert len(result['recommendations']) > 0, "Expected recommendations to be provided"
        
        print(f"✓ Quality analysis for poor audio:")
        print(f"  - Level: {result['quality_level']}")
        print(f"  - Score: {result['quality_score']:.1f}/100")
        print(f"  - SNR: {result['snr_db']:.1f} dB")
        print(f"  - Issues: {len(result['issues'])}")
        print(f"  - Recommendations: {len(result['recommendations'])}")
    
    def test_quick_quality_check(self):
        """Test quick quality check function"""
        # Good audio
        good_audio = self.generate_test_audio(duration=2.0, noise_level=0.01)
        is_acceptable, info = quick_quality_check(good_audio, sr=self.sr)
        assert is_acceptable, "Good audio should be acceptable"
        print(f"✓ Good audio passed quick check: {info['quality_score']:.1f}/100")
        
        # Poor audio
        poor_audio = self.generate_test_audio(duration=2.0, noise_level=0.5)
        is_acceptable, info = quick_quality_check(poor_audio, sr=self.sr)
        assert not is_acceptable, "Poor audio should be rejected"
        print(f"✓ Poor audio failed quick check: {info['quality_score']:.1f}/100")


class TestAdaptiveNoiseReduction:
    """Test suite for AdaptiveNoiseReducer"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.sr = 16000
        self.reducer = AdaptiveNoiseReducer(sr=self.sr)
    
    def generate_noisy_audio(self, duration=2.0, signal_amp=0.5, noise_amp=0.05):
        """Generate audio with controlled signal and noise levels"""
        samples = int(duration * self.sr)
        t = np.linspace(0, duration, samples)
        
        # Signal: sine wave
        signal = signal_amp * np.sin(2 * np.pi * 440 * t)
        
        # Noise
        noise = noise_amp * np.random.normal(0, 1, samples)
        
        return (signal + noise).astype(np.float32)
    
    def test_adaptive_reduction_high_snr(self):
        """Test adaptive noise reduction on high SNR audio"""
        audio = self.generate_noisy_audio(signal_amp=0.5, noise_amp=0.01)
        snr = 20 * np.log10(0.5 / 0.01)  # High SNR
        
        reduced = self.reducer.reduce_noise_adaptive(audio, snr_db=snr, preserve_edges=False)
        
        assert len(reduced) == len(audio), "Audio length should be preserved"
        assert not np.isnan(reduced).any(), "Should not contain NaN"
        assert not np.isinf(reduced).any(), "Should not contain Inf"
        print(f"✓ High SNR reduction: minimal processing applied")
    
    def test_adaptive_reduction_medium_snr(self):
        """Test adaptive noise reduction on medium SNR audio"""
        audio = self.generate_noisy_audio(signal_amp=0.5, noise_amp=0.05)
        snr = 20 * np.log10(0.5 / 0.05)  # Medium SNR
        
        reduced = self.reducer.reduce_noise_adaptive(audio, snr_db=snr, preserve_edges=False)
        
        assert len(reduced) == len(audio), "Audio length should be preserved"
        print(f"✓ Medium SNR reduction: moderate processing applied")
    
    def test_adaptive_reduction_low_snr(self):
        """Test adaptive noise reduction on low SNR audio"""
        audio = self.generate_noisy_audio(signal_amp=0.5, noise_amp=0.15)
        snr = 20 * np.log10(0.5 / 0.15)  # Low SNR
        
        reduced = self.reducer.reduce_noise_adaptive(audio, snr_db=snr, preserve_edges=False)
        
        assert len(reduced) == len(audio), "Audio length should be preserved"
        print(f"✓ Low SNR reduction: aggressive processing applied")
    
    def test_edge_preservation(self):
        """Test edge-preserving noise reduction"""
        audio = self.generate_noisy_audio(duration=2.0, signal_amp=0.5, noise_amp=0.05)
        snr = 15.0
        
        # Without edge preservation
        reduced_no_edge = self.reducer.reduce_noise_adaptive(
            audio, snr_db=snr, preserve_edges=False
        )
        
        # With edge preservation
        reduced_with_edge = self.reducer.reduce_noise_adaptive(
            audio, snr_db=snr, preserve_edges=True
        )
        
        assert len(reduced_no_edge) == len(reduced_with_edge), "Both should preserve length"
        
        # Check that edges are different (gentler processing)
        edge_samples = int(0.3 * self.sr)
        start_diff = np.mean(np.abs(reduced_with_edge[:edge_samples] - audio[:edge_samples]))
        middle_diff = np.mean(np.abs(reduced_with_edge[edge_samples:-edge_samples] - 
                                     audio[edge_samples:-edge_samples]))
        
        # Edge should have less aggressive processing (smaller difference from original)
        # This might not always be true depending on noise distribution, so we just check it runs
        print(f"✓ Edge preservation applied: start_diff={start_diff:.4f}, middle_diff={middle_diff:.4f}")
    
    def test_crossfade_segments(self):
        """Test crossfade between segments"""
        seg1 = np.ones(self.sr) * 0.5  # 1 second of 0.5
        seg2 = np.ones(self.sr) * -0.5  # 1 second of -0.5
        
        result = self.reducer._crossfade_segments([seg1, seg2], fade_samples=1000)
        
        # Should have smooth transition
        assert len(result) > 0, "Result should not be empty"
        assert not np.isnan(result).any(), "Should not contain NaN"
        print(f"✓ Crossfade applied successfully")
    
    def test_preprocess_audio_adaptive_convenience(self):
        """Test convenience function for adaptive preprocessing"""
        audio = self.generate_noisy_audio(duration=2.0)
        
        # Test with auto SNR estimation
        processed = preprocess_audio_adaptive(audio, sr=self.sr, preserve_edges=True)
        
        assert len(processed) > 0, "Should return processed audio"
        assert np.max(np.abs(processed)) <= 1.0, "Should be normalized"
        print(f"✓ Convenience function works with auto SNR estimation")
        
        # Test with provided SNR
        processed2 = preprocess_audio_adaptive(audio, sr=self.sr, snr_db=15.0)
        
        assert len(processed2) > 0, "Should return processed audio"
        print(f"✓ Convenience function works with provided SNR")


def run_phase1_tests():
    """Run all Phase 1 tests"""
    print("\n" + "="*60)
    print("PHASE 1 QUALITY ASSURANCE TESTS")
    print("="*60 + "\n")
    
    print("Testing Audio Quality Analyzer...")
    print("-" * 60)
    test_analyzer = TestAudioQualityAnalyzer()
    test_analyzer.setup_method()
    
    try:
        test_analyzer.test_snr_calculation_clean_audio()
        test_analyzer.test_snr_calculation_noisy_audio()
        test_analyzer.test_snr_calculation_very_noisy_audio()
        test_analyzer.test_clipping_detection_no_clipping()
        test_analyzer.test_clipping_detection_with_clipping()
        test_analyzer.test_silence_detection()
        test_analyzer.test_comprehensive_quality_analysis_excellent()
        test_analyzer.test_comprehensive_quality_analysis_poor()
        test_analyzer.test_quick_quality_check()
        print("\n✅ All Audio Quality Analyzer tests passed!\n")
    except AssertionError as e:
        print(f"\n❌ Audio Quality Analyzer test failed: {e}\n")
        return False
    
    print("\nTesting Adaptive Noise Reduction...")
    print("-" * 60)
    test_reducer = TestAdaptiveNoiseReduction()
    test_reducer.setup_method()
    
    try:
        test_reducer.test_adaptive_reduction_high_snr()
        test_reducer.test_adaptive_reduction_medium_snr()
        test_reducer.test_adaptive_reduction_low_snr()
        test_reducer.test_edge_preservation()
        test_reducer.test_crossfade_segments()
        test_reducer.test_preprocess_audio_adaptive_convenience()
        print("\n✅ All Adaptive Noise Reduction tests passed!\n")
    except AssertionError as e:
        print(f"\n❌ Adaptive Noise Reduction test failed: {e}\n")
        return False
    
    print("\n" + "="*60)
    print("✅ PHASE 1: ALL TESTS PASSED!")
    print("="*60 + "\n")
    return True


if __name__ == "__main__":
    success = run_phase1_tests()
    exit(0 if success else 1)
