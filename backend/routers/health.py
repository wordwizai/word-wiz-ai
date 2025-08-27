"""
Health check and monitoring endpoints for model optimization.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import time
import numpy as np
import psutil
import os

# Import with fallback for environments where core modules aren't available
try:
    from core.phoneme_assistant import PhonemeAssistant
    from core.optimization_config import config
    CORE_AVAILABLE = True
except ImportError:
    CORE_AVAILABLE = False

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/model-optimization")
async def model_optimization_health() -> Dict[str, Any]:
    """
    Health check for model optimization status.
    Returns optimization configuration and performance metrics.
    """
    if not CORE_AVAILABLE:
        return {
            "status": "unhealthy",
            "error": "Core modules not available",
            "core_available": False
        }
    
    try:
        # Get system information
        system_info = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "memory_available_gb": psutil.virtual_memory().available / (1024**3),
        }
        
        # Get optimization configuration
        optimization_config = {
            "use_optimized_model": config.get('use_optimized_model'),
            "use_quantization": config.get('use_quantization'),
            "use_fast_models": config.get('use_fast_models'),
            "use_compilation": config.get('use_compilation'),
            "model_cache_enabled": config.get('model_cache_enabled'),
        }
        
        # Try to initialize assistant for detailed info
        assistant_info = None
        try:
            assistant = PhonemeAssistant()
            assistant_info = assistant.get_performance_info()
        except Exception as e:
            assistant_info = {"error": f"Failed to initialize assistant: {str(e)}"}
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "core_available": CORE_AVAILABLE,
            "system_info": system_info,
            "optimization_config": optimization_config,
            "assistant_info": assistant_info
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time(),
            "core_available": CORE_AVAILABLE
        }


@router.get("/performance-test")
async def performance_test() -> Dict[str, Any]:
    """
    Run a quick performance test to validate optimization performance.
    """
    if not CORE_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="Core modules not available for performance testing"
        )
    
    try:
        # Generate test audio
        test_audio = np.random.randn(16000).astype(np.float32)  # 1 second
        
        # Initialize assistant
        start_init = time.time()
        assistant = PhonemeAssistant()
        init_time = time.time() - start_init
        
        # Test inference (will fail without model download, but tests pipeline)
        start_inference = time.time()
        try:
            # This will fail without actual model, but we can test the setup
            result = assistant.phoneme_extractor.extract_phoneme(test_audio)
            inference_success = True
            inference_error = None
        except Exception as e:
            inference_success = False
            inference_error = str(e)
            result = None
        
        inference_time = time.time() - start_inference
        
        # Get performance info
        perf_info = assistant.get_performance_info()
        
        # Performance assessment
        performance_grade = "unknown"
        if inference_success:
            if inference_time < 1.0:
                performance_grade = "excellent"
            elif inference_time < 2.0:
                performance_grade = "good"
            elif inference_time < 5.0:
                performance_grade = "acceptable"
            else:
                performance_grade = "poor"
        
        return {
            "status": "completed",
            "timestamp": time.time(),
            "test_results": {
                "initialization_time": init_time,
                "inference_time": inference_time,
                "inference_success": inference_success,
                "inference_error": inference_error,
                "performance_grade": performance_grade,
                "result_length": len(result) if result else 0
            },
            "performance_info": perf_info,
            "recommendations": _get_performance_recommendations(init_time, inference_time, inference_success)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Performance test failed: {str(e)}"
        )


@router.get("/system-resources")
async def system_resources() -> Dict[str, Any]:
    """
    Get current system resource usage.
    """
    try:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "cpu": {
                "percent": psutil.cpu_percent(interval=1),
                "count": psutil.cpu_count(),
                "count_logical": psutil.cpu_count(logical=True)
            },
            "memory": {
                "total_gb": memory.total / (1024**3),
                "available_gb": memory.available / (1024**3),
                "used_gb": memory.used / (1024**3),
                "percent": memory.percent
            },
            "disk": {
                "total_gb": disk.total / (1024**3),
                "free_gb": disk.free / (1024**3),
                "used_gb": disk.used / (1024**3),
                "percent": (disk.used / disk.total) * 100
            },
            "timestamp": time.time()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get system resources: {str(e)}"
        )


def _get_performance_recommendations(init_time: float, 
                                   inference_time: float, 
                                   inference_success: bool) -> list:
    """Generate performance recommendations based on test results."""
    recommendations = []
    
    if not inference_success:
        recommendations.append("Model loading failed - check internet connection for initial setup")
    
    if init_time > 10:
        recommendations.append("Slow initialization - consider enabling model caching")
    
    if inference_time > 5:
        recommendations.append("Slow inference - enable quantization and fast models")
    elif inference_time > 2:
        recommendations.append("Moderate inference time - consider enabling model compilation")
    
    if psutil.virtual_memory().percent > 80:
        recommendations.append("High memory usage - enable cache clearing after init")
    
    if psutil.cpu_percent() > 80:
        recommendations.append("High CPU usage - consider reducing model complexity")
    
    if not recommendations:
        recommendations.append("Performance looks good - no immediate optimizations needed")
    
    return recommendations