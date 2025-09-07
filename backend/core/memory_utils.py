"""
Memory monitoring utilities for tracking and optimizing memory usage
"""

import gc
import psutil
import os
import torch
from typing import Dict, Any


def get_memory_info() -> Dict[str, Any]:
    """Get current memory usage information"""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    
    info = {
        "rss_mb": memory_info.rss / 1024 / 1024,  # Resident Set Size in MB
        "vms_mb": memory_info.vms / 1024 / 1024,  # Virtual Memory Size in MB
        "percent": process.memory_percent(),
        "available_mb": psutil.virtual_memory().available / 1024 / 1024,
        "total_mb": psutil.virtual_memory().total / 1024 / 1024,
    }
    
    # Add GPU memory info if CUDA is available
    if torch.cuda.is_available():
        try:
            info["gpu_allocated_mb"] = torch.cuda.memory_allocated() / 1024 / 1024
            info["gpu_reserved_mb"] = torch.cuda.memory_reserved() / 1024 / 1024
            info["gpu_max_allocated_mb"] = torch.cuda.max_memory_allocated() / 1024 / 1024
        except Exception as e:
            info["gpu_error"] = str(e)
    
    return info


def force_cleanup():
    """Force garbage collection and CUDA cache cleanup"""
    # Clear Python garbage
    collected = gc.collect()
    
    # Clear CUDA cache if available
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
    
    return collected


def log_memory_usage(label: str = "Memory Usage", enable_logging: bool = True):
    """Log current memory usage with a label"""
    if not enable_logging:
        return
        
    memory_info = get_memory_info()
    print(f"[{label}] RSS: {memory_info['rss_mb']:.1f}MB, "
          f"Percent: {memory_info['percent']:.1f}%, "
          f"Available: {memory_info['available_mb']:.1f}MB")
    
    if "gpu_allocated_mb" in memory_info:
        print(f"[{label}] GPU Allocated: {memory_info['gpu_allocated_mb']:.1f}MB, "
              f"GPU Reserved: {memory_info['gpu_reserved_mb']:.1f}MB")


def memory_monitor_decorator(func_name: str = None, enable_logging: bool = True):
    """Decorator to monitor memory usage around a function call"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            name = func_name or func.__name__
            
            if enable_logging:
                log_memory_usage(f"Before {name}")
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                if enable_logging:
                    log_memory_usage(f"After {name}")
                    collected = force_cleanup()
                    if collected > 0:
                        print(f"[{name}] Garbage collected {collected} objects")
        
        return wrapper
    return decorator


class MemoryTracker:
    """Context manager for tracking memory usage"""
    
    def __init__(self, label: str = "Operation", enable_logging: bool = True):
        self.label = label
        self.enable_logging = enable_logging
        self.start_memory = None
    
    def __enter__(self):
        if self.enable_logging:
            self.start_memory = get_memory_info()
            log_memory_usage(f"Start {self.label}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.enable_logging and self.start_memory:
            end_memory = get_memory_info()
            delta_rss = end_memory['rss_mb'] - self.start_memory['rss_mb']
            
            log_memory_usage(f"End {self.label}")
            print(f"[{self.label}] Memory delta: {delta_rss:+.1f}MB")
            
            # Force cleanup
            collected = force_cleanup()
            if collected > 0:
                print(f"[{self.label}] Cleaned up {collected} objects")