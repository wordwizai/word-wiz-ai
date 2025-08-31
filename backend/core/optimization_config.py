"""
Configuration management for model optimizations.
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv


class OptimizationConfig:
    """Configuration class for model optimization settings."""
    
    def __init__(self):
        load_dotenv()
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        return {
            # Model Selection
            'use_optimized_model': self._get_bool('USE_OPTIMIZED_PHONEME_MODEL', True),
            'use_fast_models': self._get_bool('USE_FAST_MODELS', True),
            
            # Quantization Settings
            'use_quantization': self._get_bool('USE_MODEL_QUANTIZATION', True),
            'quantization_dtype': 'qint8',  # Could be made configurable
            
            # Compilation Settings
            'use_compilation': self._get_bool('USE_MODEL_COMPILATION', True),
            'compilation_mode': os.getenv('MODEL_COMPILATION_MODE', 'reduce-overhead'),
            
            # Performance Settings
            'enable_performance_logging': self._get_bool('ENABLE_PERFORMANCE_LOGGING', False),
            'model_cache_enabled': self._get_bool('ENABLE_MODEL_CACHE', True),
            'warmup_runs': int(os.getenv('MODEL_WARMUP_RUNS', '1')),
            
            # Fallback Settings
            'fallback_on_error': self._get_bool('FALLBACK_ON_OPTIMIZATION_ERROR', True),
            
            # Memory Settings
            'clear_cache_after_init': self._get_bool('CLEAR_CACHE_AFTER_INIT', False),
        }
    
    def _get_bool(self, key: str, default: bool) -> bool:
        """Get boolean value from environment variable."""
        value = os.getenv(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on')
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self._config.get(key, default)
    
    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-style access."""
        return self._config[key]
    
    def summary(self) -> str:
        """Get a summary of current configuration."""
        lines = ["Model Optimization Configuration:"]
        for key, value in self._config.items():
            lines.append(f"  {key}: {value}")
        return "\n".join(lines)


# Global configuration instance
config = OptimizationConfig()