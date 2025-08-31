#!/usr/bin/env python3
"""
Performance testing utility for PhonemeExtractor optimizations.
"""

import time
import numpy as np
import sys
import os
from typing import Dict, List

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.phoneme_extractor import PhonemeExtractor


def generate_test_audio(duration_seconds: float = 1.0, sample_rate: int = 16000) -> np.ndarray:
    """Generate test audio signal."""
    num_samples = int(duration_seconds * sample_rate)
    # Generate realistic audio-like signal (band-limited noise)
    t = np.linspace(0, duration_seconds, num_samples)
    # Mix of frequencies typical for speech
    signal = (np.sin(2 * np.pi * 200 * t) * 0.3 + 
             np.sin(2 * np.pi * 500 * t) * 0.2 +
             np.sin(2 * np.pi * 1000 * t) * 0.1 +
             np.random.normal(0, 0.1, num_samples))
    return signal.astype(np.float32)


def benchmark_model(model_config: Dict, test_audio: np.ndarray, num_runs: int = 5) -> Dict:
    """Benchmark a specific model configuration."""
    print(f"\n=== Testing {model_config['name']} ===")
    
    # Initialize model
    start_time = time.time()
    extractor = PhonemeExtractor(**model_config['params'])
    init_time = time.time() - start_time
    
    # Warm-up run
    print("Performing warm-up run...")
    extractor.extract_phoneme(test_audio)
    
    # Benchmark runs
    print(f"Running {num_runs} benchmark iterations...")
    inference_times = []
    
    for i in range(num_runs):
        start_time = time.time()
        result = extractor.extract_phoneme(test_audio)
        inference_time = time.time() - start_time
        inference_times.append(inference_time)
        print(f"Run {i+1}: {inference_time:.3f}s")
    
    # Calculate statistics
    avg_time = np.mean(inference_times)
    min_time = np.min(inference_times)
    max_time = np.max(inference_times)
    std_time = np.std(inference_times)
    
    results = {
        'name': model_config['name'],
        'init_time': init_time,
        'avg_inference_time': avg_time,
        'min_inference_time': min_time,
        'max_inference_time': max_time,
        'std_inference_time': std_time,
        'result_sample': result[:3] if result else []
    }
    
    print(f"Results for {model_config['name']}:")
    print(f"  Initialization time: {init_time:.3f}s")
    print(f"  Average inference: {avg_time:.3f}s (±{std_time:.3f}s)")
    print(f"  Min/Max inference: {min_time:.3f}s / {max_time:.3f}s")
    
    return results


def run_performance_comparison():
    """Run comprehensive performance comparison."""
    print("PhonemeExtractor Performance Benchmark")
    print("=" * 50)
    
    # Generate test audio
    test_audio = generate_test_audio(duration_seconds=2.0)
    print(f"Generated test audio: {len(test_audio)/16000:.1f}s duration")
    
    # Define model configurations to test
    model_configs = [
        {
            'name': 'Baseline (Original)',
            'params': {
                'use_quantization': False,
                'use_fast_model': False
            }
        },
        {
            'name': 'Quantized (Original Model)',
            'params': {
                'use_quantization': True,
                'use_fast_model': False
            }
        },
        {
            'name': 'Fast Model (Base)',
            'params': {
                'use_quantization': False,
                'use_fast_model': True
            }
        },
        {
            'name': 'Optimized (Fast + Quantized)',
            'params': {
                'use_quantization': True,
                'use_fast_model': True
            }
        }
    ]
    
    # Run benchmarks
    all_results = []
    for config in model_configs:
        try:
            results = benchmark_model(config, test_audio, num_runs=3)
            all_results.append(results)
        except Exception as e:
            print(f"Failed to test {config['name']}: {e}")
            continue
    
    # Summary comparison
    print("\n" + "=" * 50)
    print("PERFORMANCE SUMMARY")
    print("=" * 50)
    
    if all_results:
        print(f"{'Configuration':<25} {'Init Time':<12} {'Avg Inference':<15} {'Speedup':<10}")
        print("-" * 70)
        
        baseline_time = None
        for result in all_results:
            if 'Baseline' in result['name']:
                baseline_time = result['avg_inference_time']
                break
        
        for result in all_results:
            speedup = ""
            if baseline_time and result['avg_inference_time'] > 0:
                speedup_factor = baseline_time / result['avg_inference_time']
                speedup = f"{speedup_factor:.2f}x"
            
            print(f"{result['name']:<25} {result['init_time']:<12.3f} "
                  f"{result['avg_inference_time']:<15.3f} {speedup:<10}")
    
    return all_results


if __name__ == "__main__":
    try:
        results = run_performance_comparison()
    except KeyboardInterrupt:
        print("\nBenchmark interrupted by user")
    except Exception as e:
        print(f"Benchmark failed: {e}")
        import traceback
        traceback.print_exc()