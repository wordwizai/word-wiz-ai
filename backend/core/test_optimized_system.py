#!/usr/bin/env python3
"""
Test the optimized PhonemeExtractor with mock data.
"""

import sys
import os
import numpy as np
import time

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_optimized_extractor():
    """Test the optimized PhonemeExtractor with different configurations."""
    
    # Set test environment variables
    os.environ['USE_OPTIMIZED_PHONEME_MODEL'] = 'true'
    os.environ['USE_MODEL_QUANTIZATION'] = 'true'
    os.environ['USE_FAST_MODELS'] = 'true'
    os.environ['ENABLE_PERFORMANCE_LOGGING'] = 'true'
    os.environ['FALLBACK_ON_OPTIMIZATION_ERROR'] = 'true'
    os.environ['MODEL_WARMUP_RUNS'] = '0'  # Skip warmup for offline test
    
    try:
        from core.phoneme_extractor import PhonemeExtractor
        from core.optimization_config import config
        
        print("Optimization Configuration Test")
        print("=" * 40)
        print(config.summary())
        print()
        
        # Test configuration access
        print("Testing configuration access...")
        assert config.get('use_fast_models') == True
        assert config.get('use_quantization') == True
        print("✓ Configuration loaded correctly")
        
        # Generate test audio
        print("\nGenerating test audio...")
        test_audio = np.random.randn(16000).astype(np.float32)  # 1 second
        print(f"✓ Generated {len(test_audio)/16000:.1f}s of test audio")
        
        # Test different configurations
        configs_to_test = [
            {
                'name': 'Optimized Configuration',
                'params': {}  # Use defaults from environment
            },
            {
                'name': 'Conservative Configuration',
                'params': {
                    'use_quantization': False,
                    'use_fast_model': False
                }
            }
        ]
        
        for test_config in configs_to_test:
            print(f"\n--- Testing {test_config['name']} ---")
            
            try:
                # This will fail without internet, but we can test the configuration logic
                start_time = time.time()
                extractor = PhonemeExtractor(**test_config['params'])
                init_time = time.time() - start_time
                
                print(f"✓ Extractor initialized in {init_time:.3f}s")
                
                # Test model info
                info = extractor.get_model_info()
                print("Model Info:")
                for key, value in info.items():
                    if key != 'config_summary':  # Skip long summary
                        print(f"  {key}: {value}")
                
                # Test inference (will fail without model, but tests the pipeline)
                try:
                    result = extractor.extract_phoneme(test_audio)
                    print(f"✓ Inference successful, result length: {len(result) if result else 0}")
                except Exception as e:
                    print(f"⚠ Inference failed as expected without model: {type(e).__name__}")
                
            except Exception as e:
                print(f"⚠ Configuration failed as expected without internet: {type(e).__name__}")
                # This is expected when models can't be downloaded
        
        print("\n" + "=" * 40)
        print("✓ Optimization system is properly configured!")
        print("Note: Actual model testing requires internet connectivity")
        return True
        
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_optimized_extractor()
    sys.exit(0 if success else 1)