"""
Memory monitoring middleware for FastAPI
"""

import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from core.memory_utils import get_memory_info, force_cleanup
from core.memory_config import MEMORY_CONFIG, should_enable_memory_logging


class MemoryMonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware to monitor memory usage and perform cleanup"""
    
    def __init__(self, app):
        super().__init__(app)
        self.request_count = 0
        self.cleanup_interval = MEMORY_CONFIG["cleanup_interval"]
        self.warning_threshold = MEMORY_CONFIG["memory_warning_threshold_mb"]
        self.critical_threshold = MEMORY_CONFIG["memory_critical_threshold_mb"]
        
    async def dispatch(self, request: Request, call_next):
        # Only monitor if enabled
        if not should_enable_memory_logging():
            return await call_next(request)
            
        self.request_count += 1
        start_time = time.time()
        start_memory = get_memory_info()
        
        # Log memory info for audio processing endpoints
        if "/ai/analyze-audio" in str(request.url):
            print(f"[Request {self.request_count}] Starting audio analysis - "
                  f"RSS: {start_memory['rss_mb']:.1f}MB, "
                  f"Available: {start_memory['available_mb']:.1f}MB")
        
        # Process the request
        response = await call_next(request)
        
        # Check memory after request
        end_memory = get_memory_info()
        memory_delta = end_memory['rss_mb'] - start_memory['rss_mb']
        request_time = time.time() - start_time
        
        # Log for audio processing endpoints
        if "/ai/analyze-audio" in str(request.url):
            print(f"[Request {self.request_count}] Completed audio analysis - "
                  f"RSS: {end_memory['rss_mb']:.1f}MB (+{memory_delta:+.1f}MB), "
                  f"Time: {request_time:.2f}s")
        
        # Check for memory warnings
        if end_memory['rss_mb'] > self.critical_threshold:
            print(f"⚠️  CRITICAL: Memory usage {end_memory['rss_mb']:.1f}MB "
                  f"exceeds critical threshold {self.critical_threshold}MB")
            # Force aggressive cleanup
            cleaned = force_cleanup()
            post_cleanup_memory = get_memory_info()
            print(f"🧹 Emergency cleanup: {cleaned} objects, "
                  f"RSS: {post_cleanup_memory['rss_mb']:.1f}MB")
                  
        elif end_memory['rss_mb'] > self.warning_threshold:
            print(f"⚠️  WARNING: Memory usage {end_memory['rss_mb']:.1f}MB "
                  f"exceeds warning threshold {self.warning_threshold}MB")
        
        # Periodic cleanup
        if self.request_count % self.cleanup_interval == 0:
            cleaned = force_cleanup()
            if cleaned > 0:
                post_cleanup_memory = get_memory_info()
                print(f"🧹 Periodic cleanup after {self.request_count} requests: "
                      f"{cleaned} objects, RSS: {post_cleanup_memory['rss_mb']:.1f}MB")
        
        return response