"""
Tests for Phase 4: Device-Specific Optimization

Tests the device calibration and fingerprinting module.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import tempfile
import json
from core.device_calibration import DeviceCalibrator, apply_device_specific_preprocessing


class TestDeviceCalibration:
    """Test suite for Phase 4 device calibration"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.calibrator = DeviceCalibrator()
        self.sr = 16000
        
    def generate_test_audio(self, duration=2.0, noise_level=0.01, freq=440):
        """Generate synthetic test audio with controllable characteristics"""
        samples = int(duration * self.sr)
        t = np.linspace(0, duration, samples)
        
        # Signal
        audio = 0.5 * np.sin(2 * np.pi * freq * t)
        
        # Add noise
        noise = np.random.normal(0, noise_level, samples)
        audio = audio + noise
        
        return audio.astype(np.float32)
    
    def test_fingerprint_single_sample(self):
        """Test device fingerprinting with single audio sample"""
        audio = self.generate_test_audio(duration=2.0, noise_level=0.02)
        
        profile = self.calibrator.fingerprint_device(
            audio_samples=[audio],
            device_id='test_device_1',
            sr=self.sr
        )
        
        assert profile['device_id'] == 'test_device_1', "Device ID should match"
        assert profile['sample_count'] == 1, "Should record 1 sample"
        assert 'noise_floor' in profile, "Should have noise floor measurement"
        assert 'spectral_centroid' in profile, "Should have spectral centroid"
        assert 'dynamic_range' in profile, "Should have dynamic range"
        assert 'frequency_response' in profile, "Should have frequency response"
        
        print(f"✓ Single sample fingerprinting: noise_floor={profile['noise_floor']['mean']:.6f}")
    
    def test_fingerprint_multiple_samples(self):
        """Test device fingerprinting with multiple audio samples"""
        samples = [
            self.generate_test_audio(duration=2.0, noise_level=0.02),
            self.generate_test_audio(duration=2.0, noise_level=0.03),
            self.generate_test_audio(duration=2.0, noise_level=0.025)
        ]
        
        profile = self.calibrator.fingerprint_device(
            audio_samples=samples,
            device_id='test_device_multi',
            sr=self.sr
        )
        
        assert profile['sample_count'] == 3, "Should record 3 samples"
        # With multiple samples, should have std deviation
        assert profile['noise_floor']['std'] >= 0, "Should calculate std deviation"
        
        print(f"✓ Multiple samples: noise_floor mean={profile['noise_floor']['mean']:.6f}, "
              f"std={profile['noise_floor']['std']:.6f}")
    
    def test_noisy_device_detection(self):
        """Test that noisy devices are correctly identified"""
        # Create noisy audio
        noisy_audio = self.generate_test_audio(duration=2.0, noise_level=0.1)
        
        profile = self.calibrator.fingerprint_device(
            audio_samples=[noisy_audio],
            device_id='noisy_device',
            sr=self.sr
        )
        
        # High noise level should be detected
        assert profile['noise_floor']['mean'] > 0.05, "Should detect high noise floor"
        
        print(f"✓ Noisy device detected: noise_floor={profile['noise_floor']['mean']:.6f}")
    
    def test_clean_device_detection(self):
        """Test that clean devices are correctly identified"""
        # Create clean audio
        clean_audio = self.generate_test_audio(duration=2.0, noise_level=0.001)
        
        profile = self.calibrator.fingerprint_device(
            audio_samples=[clean_audio],
            device_id='clean_device',
            sr=self.sr
        )
        
        # Low noise level should be detected
        assert profile['noise_floor']['mean'] < 0.02, "Should detect low noise floor"
        
        print(f"✓ Clean device detected: noise_floor={profile['noise_floor']['mean']:.6f}")
    
    def test_get_preprocessing_params_noisy_device(self):
        """Test that noisy devices get appropriate preprocessing parameters"""
        noisy_audio = self.generate_test_audio(duration=2.0, noise_level=0.1)
        
        self.calibrator.fingerprint_device(
            audio_samples=[noisy_audio],
            device_id='noisy_test',
            sr=self.sr
        )
        
        params = self.calibrator.get_device_preprocessing_params('noisy_test')
        
        # Noisy device should get stronger noise reduction
        assert params['noise_reduction_strength'] >= 0.6, \
            f"Noisy device should get strong noise reduction, got {params['noise_reduction_strength']}"
        
        print(f"✓ Noisy device params: noise_reduction={params['noise_reduction_strength']:.2f}, "
              f"padding={params['padding_ms']}ms")
    
    def test_get_preprocessing_params_clean_device(self):
        """Test that clean devices get appropriate preprocessing parameters"""
        clean_audio = self.generate_test_audio(duration=2.0, noise_level=0.001)
        
        self.calibrator.fingerprint_device(
            audio_samples=[clean_audio],
            device_id='clean_test',
            sr=self.sr
        )
        
        params = self.calibrator.get_device_preprocessing_params('clean_test')
        
        # Clean device should get gentler noise reduction
        assert params['noise_reduction_strength'] <= 0.6, \
            f"Clean device should get gentle noise reduction, got {params['noise_reduction_strength']}"
        
        print(f"✓ Clean device params: noise_reduction={params['noise_reduction_strength']:.2f}, "
              f"trim_top_db={params['trim_top_db']}")
    
    def test_get_default_params_for_unknown_device(self):
        """Test that unknown devices get default parameters"""
        params = self.calibrator.get_device_preprocessing_params('unknown_device_xyz')
        
        assert 'noise_reduction_strength' in params, "Should return default params"
        assert params['noise_reduction_strength'] == 0.6, "Should use default noise reduction"
        
        print("✓ Unknown device gets default parameters")
    
    def test_frequency_response_detection(self):
        """Test that frequency response is correctly analyzed"""
        # Create audio with bass emphasis
        bass_audio = self.generate_test_audio(duration=2.0, freq=200, noise_level=0.01)
        
        profile = self.calibrator.fingerprint_device(
            audio_samples=[bass_audio],
            device_id='bass_device',
            sr=self.sr
        )
        
        freq_response = profile['frequency_response']
        
        # Bass frequency should have higher energy
        assert freq_response['low'] > 0, "Should have low frequency energy"
        
        print(f"✓ Frequency response: low={freq_response['low']:.2f}, "
              f"mid={freq_response['mid']:.2f}, high={freq_response['high']:.2f}")
    
    def test_save_and_load_profile(self):
        """Test saving and loading device profiles"""
        audio = self.generate_test_audio(duration=2.0)
        
        # Create profile
        original_profile = self.calibrator.fingerprint_device(
            audio_samples=[audio],
            device_id='save_test',
            sr=self.sr
        )
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            self.calibrator.save_profile('save_test', temp_path)
            
            # Create new calibrator and load
            new_calibrator = DeviceCalibrator()
            new_calibrator.load_profile('save_test', temp_path)
            
            loaded_profile = new_calibrator.profiles['save_test']
            
            assert loaded_profile['device_id'] == original_profile['device_id'], \
                "Device ID should match after load"
            assert loaded_profile['noise_floor']['mean'] == original_profile['noise_floor']['mean'], \
                "Noise floor should match after load"
            
            print("✓ Profile save/load works correctly")
        finally:
            # Cleanup
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def test_get_all_profiles(self):
        """Test retrieving all profiles"""
        audio1 = self.generate_test_audio(duration=2.0)
        audio2 = self.generate_test_audio(duration=2.0)
        
        self.calibrator.fingerprint_device([audio1], 'device_1', self.sr)
        self.calibrator.fingerprint_device([audio2], 'device_2', self.sr)
        
        all_profiles = self.calibrator.get_all_profiles()
        
        assert len(all_profiles) == 2, "Should have 2 profiles"
        assert 'device_1' in all_profiles, "Should have device_1"
        assert 'device_2' in all_profiles, "Should have device_2"
        
        print(f"✓ Retrieved all profiles: {list(all_profiles.keys())}")
    
    def test_delete_profile(self):
        """Test deleting a device profile"""
        audio = self.generate_test_audio(duration=2.0)
        
        self.calibrator.fingerprint_device([audio], 'delete_test', self.sr)
        assert 'delete_test' in self.calibrator.profiles, "Profile should exist"
        
        self.calibrator.delete_profile('delete_test')
        assert 'delete_test' not in self.calibrator.profiles, "Profile should be deleted"
        
        print("✓ Profile deletion works")
    
    def test_apply_device_specific_preprocessing(self):
        """Test applying device-specific preprocessing"""
        audio = self.generate_test_audio(duration=2.0, noise_level=0.05)
        
        self.calibrator.fingerprint_device([audio], 'preprocess_test', self.sr)
        
        processed = apply_device_specific_preprocessing(
            audio,
            'preprocess_test',
            self.calibrator,
            sr=self.sr
        )
        
        assert len(processed) > 0, "Should return processed audio"
        assert processed.shape == audio.shape, "Shape should be preserved"
        
        print(f"✓ Device-specific preprocessing applied: {len(processed)} samples")


def run_phase4_tests():
    """Run all Phase 4 tests"""
    print("\n" + "="*60)
    print("PHASE 4 QUALITY ASSURANCE TESTS")
    print("="*60 + "\n")
    
    print("Testing Device Calibration...")
    print("-" * 60)
    test_calibration = TestDeviceCalibration()
    test_calibration.setup_method()
    
    try:
        test_calibration.test_fingerprint_single_sample()
        test_calibration.test_fingerprint_multiple_samples()
        test_calibration.test_noisy_device_detection()
        test_calibration.test_clean_device_detection()
        test_calibration.test_get_preprocessing_params_noisy_device()
        test_calibration.test_get_preprocessing_params_clean_device()
        test_calibration.test_get_default_params_for_unknown_device()
        test_calibration.test_frequency_response_detection()
        test_calibration.test_save_and_load_profile()
        test_calibration.test_get_all_profiles()
        test_calibration.test_delete_profile()
        test_calibration.test_apply_device_specific_preprocessing()
        print("\n✅ All Device Calibration tests passed!\n")
    except AssertionError as e:
        print(f"\n❌ Device Calibration test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "="*60)
    print("✅ PHASE 4: ALL TESTS PASSED!")
    print("="*60 + "\n")
    return True


if __name__ == "__main__":
    success = run_phase4_tests()
    exit(0 if success else 1)
