"""
Memory optimization configuration for production deployment
"""

import os
from typing import Dict, Any

# Memory optimization settings
MEMORY_CONFIG = {
    # Enable memory monitoring (should be False in production for performance)
    "enable_memory_logging": os.getenv("ENABLE_MEMORY_LOGGING", "false").lower() in ("true", "1", "yes"),
    
    # Memory cleanup settings
    "aggressive_cleanup": os.getenv("AGGRESSIVE_MEMORY_CLEANUP", "true").lower() in ("true", "1", "yes"),
    "cleanup_interval": int(os.getenv("MEMORY_CLEANUP_INTERVAL", "5")),  # Every N requests
    
    # Audio cache settings
    "audio_cache_cleanup_hours": int(os.getenv("AUDIO_CACHE_CLEANUP_HOURS", "1")),
    "audio_cache_enabled": os.getenv("ENABLE_AUDIO_CACHE", "false").lower() in ("true", "1", "yes"),
    
    # Model cache settings
    "model_cache_enabled": os.getenv("ENABLE_MODEL_CACHE", "true").lower() in ("true", "1", "yes"),
    "clear_cache_after_init": os.getenv("CLEAR_CACHE_AFTER_INIT", "false").lower() in ("true", "1", "yes"),
    
    # Memory thresholds for warnings
    "memory_warning_threshold_mb": int(os.getenv("MEMORY_WARNING_THRESHOLD_MB", "3000")),  # 3GB
    "memory_critical_threshold_mb": int(os.getenv("MEMORY_CRITICAL_THRESHOLD_MB", "3500")),  # 3.5GB
}

def get_memory_config() -> Dict[str, Any]:
    """Get the current memory configuration"""
    return MEMORY_CONFIG.copy()

def should_enable_memory_logging() -> bool:
    """Check if memory logging should be enabled"""
    return MEMORY_CONFIG["enable_memory_logging"]

def should_use_aggressive_cleanup() -> bool:
    """Check if aggressive memory cleanup should be used"""
    return MEMORY_CONFIG["aggressive_cleanup"]

def get_cleanup_interval() -> int:
    """Get the memory cleanup interval"""
    return MEMORY_CONFIG["cleanup_interval"]

def print_memory_config():
    """Print current memory configuration (useful for debugging)"""
    print("Memory Optimization Configuration:")
    for key, value in MEMORY_CONFIG.items():
        print(f"  {key}: {value}")