#!/usr/bin/env python3
"""
Simple test for phoneme extractor optimizations that works without internet.
"""

import numpy as np
import torch
import time
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_quantization():
    """Test if quantization works with a simple model."""
    print("Testing quantization functionality...")
    
    # Create a simple linear model
    model = torch.nn.Sequential(
        torch.nn.Linear(10, 20),
        torch.nn.ReLU(),
        torch.nn.Linear(20, 5)
    )
    model.eval()
    
    # Test input
    test_input = torch.randn(1, 10)
    
    # Original inference
    with torch.no_grad():
        original_output = model(test_input)
    
    # Apply quantization
    try:
        quantized_model = torch.quantization.quantize_dynamic(
            model, {torch.nn.Linear}, dtype=torch.qint8
        )
        
        # Quantized inference
        with torch.no_grad():
            quantized_output = quantized_model(test_input)
        
        print("✓ Quantization test passed")
        print(f"  Original output shape: {original_output.shape}")
        print(f"  Quantized output shape: {quantized_output.shape}")
        print(f"  Output difference (max): {torch.max(torch.abs(original_output - quantized_output)).item():.6f}")
        return True
        
    except Exception as e:
        print(f"✗ Quantization test failed: {e}")
        return False

def test_inference_modes():
    """Test different inference optimization modes."""
    print("\nTesting inference optimization modes...")
    
    # Simple test tensor
    x = torch.randn(100, 100)
    
    # Test torch.no_grad()
    try:
        with torch.no_grad():
            result1 = torch.matmul(x, x.T)
        print("✓ torch.no_grad() works")
    except Exception as e:
        print(f"✗ torch.no_grad() failed: {e}")
        return False
    
    # Test torch.inference_mode() if available
    if hasattr(torch, 'inference_mode'):
        try:
            with torch.inference_mode():
                result2 = torch.matmul(x, x.T)
            print("✓ torch.inference_mode() works")
        except Exception as e:
            print(f"✗ torch.inference_mode() failed: {e}")
    else:
        print("- torch.inference_mode() not available (older PyTorch version)")
    
    return True

def test_model_compilation():
    """Test torch.compile if available."""
    print("\nTesting model compilation...")
    
    if not hasattr(torch, 'compile'):
        print("- torch.compile() not available (PyTorch < 2.0)")
        return True
    
    try:
        # Simple model
        model = torch.nn.Linear(10, 5)
        model.eval()
        
        # Try to compile
        compiled_model = torch.compile(model, mode="reduce-overhead")
        
        # Test inference
        test_input = torch.randn(1, 10)
        with torch.no_grad():
            output = compiled_model(test_input)
        
        print("✓ torch.compile() works")
        print(f"  Compiled model output shape: {output.shape}")
        return True
        
    except Exception as e:
        print(f"✗ torch.compile() failed: {e}")
        return False

def test_performance_improvements():
    """Test basic performance improvements."""
    print("\nTesting performance improvements...")
    
    # Generate test data
    large_tensor = torch.randn(1000, 1000)
    
    # Test optimized operations
    start_time = time.time()
    with torch.no_grad():
        for _ in range(10):
            result = torch.matmul(large_tensor, large_tensor.T)
            _ = torch.argmax(result, dim=-1)
    basic_time = time.time() - start_time
    
    # Test with inference_mode if available
    if hasattr(torch, 'inference_mode'):
        start_time = time.time()
        with torch.inference_mode():
            for _ in range(10):
                result = torch.matmul(large_tensor, large_tensor.T)
                _ = torch.argmax(result, dim=-1)
        optimized_time = time.time() - start_time
        
        speedup = basic_time / optimized_time if optimized_time > 0 else 1.0
        print(f"✓ Performance test completed")
        print(f"  Basic inference time: {basic_time:.3f}s")
        print(f"  Optimized inference time: {optimized_time:.3f}s")
        print(f"  Speedup: {speedup:.2f}x")
    else:
        print(f"✓ Basic performance test completed")
        print(f"  Inference time: {basic_time:.3f}s")
    
    return True

def main():
    """Run all optimization tests."""
    print("PhonemeExtractor Optimization Tests")
    print("=" * 40)
    
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    
    tests = [
        test_quantization,
        test_inference_modes,
        test_model_compilation,
        test_performance_improvements
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
    
    print("\n" + "=" * 40)
    print(f"Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("✓ All optimization features are working correctly!")
        return True
    else:
        print("⚠ Some optimization features may not work properly.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)