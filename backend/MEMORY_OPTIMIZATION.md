# Memory Optimization for Audio Processing

This document describes the memory leak fixes and optimizations implemented to address the issue where the backend becomes unresponsive after ~2 audio analysis calls on a 4GB memory instance.

## Problem Summary

The original issue was caused by several memory leaks:

1. **PhonemeExtractor model reloading** - Models were loaded fresh each time instead of using cache
2. **Missing tensor cleanup** - PyTorch tensors and CUDA memory were not explicitly freed
3. **Audio data accumulation** - Large audio arrays and base64 data remained in memory
4. **Missing garbage collection** - No explicit cleanup after memory-intensive operations
5. **Audio cache bloat** - Temporary audio files accumulated without cleanup

## Solutions Implemented

### 1. Model Caching Fix (`core/phoneme_extractor.py`)

- Re-enabled model caching to prevent reloading models each request
- Added explicit tensor cleanup with `del` and `torch.cuda.empty_cache()`
- Fixed blank_token_id initialization with fallback handling

### 2. Memory Utilities (`core/memory_utils.py`)

- **MemoryTracker**: Context manager for monitoring memory usage around operations
- **force_cleanup()**: Aggressive garbage collection + CUDA cache clearing
- **get_memory_info()**: System memory monitoring with GPU support
- **Memory decorators**: For wrapping functions with automatic cleanup

### 3. Audio Processing Cleanup (`routers/handlers/audio_processing_handler.py`)

- Added explicit cleanup after each processing stage
- Memory tracking around expensive operations
- Cleanup of large objects (audio arrays, base64 data) immediately after use

### 4. Audio Cache Management (`core/temp_audio_cache.py`)

- Automatic periodic cleanup of old cache files
- Configurable cleanup intervals and retention periods
- Prevention of disk space issues that can cause memory pressure

### 5. Production Configuration (`core/memory_config.py`)

- Environment-based configuration for memory settings
- Production-safe defaults (logging disabled, aggressive cleanup enabled)
- Memory threshold monitoring

## Configuration

### Environment Variables

Copy `.env.memory-optimized` to `.env` and adjust for your deployment:

```bash
# Memory monitoring (disable in production)
ENABLE_MEMORY_LOGGING=false

# Memory cleanup settings
AGGRESSIVE_MEMORY_CLEANUP=true
MEMORY_CLEANUP_INTERVAL=5

# Audio cache settings
ENABLE_AUDIO_CACHE=false
AUDIO_CACHE_CLEANUP_HOURS=1

# Model optimizations
ENABLE_MODEL_CACHE=true
USE_QUANTIZATION=true
USE_FAST_MODELS=true
```

### Memory Thresholds for 4GB Instance

```bash
MEMORY_WARNING_THRESHOLD_MB=3000   # 3GB warning
MEMORY_CRITICAL_THRESHOLD_MB=3500  # 3.5GB critical
```

## Usage

### Basic Usage

The optimizations are automatically applied. No code changes needed for basic usage.

### Memory Monitoring (Development)

Enable memory logging for debugging:

```python
# Set environment variable
ENABLE_MEMORY_LOGGING=true

# Or use in code
from core.memory_utils import MemoryTracker

with MemoryTracker("My Operation"):
    # Your memory-intensive code here
    process_audio()
```

### Manual Cleanup

Force cleanup when needed:

```python
from core.memory_utils import force_cleanup

# Force garbage collection + CUDA cleanup
cleaned_objects = force_cleanup()
print(f"Cleaned {cleaned_objects} objects")
```

### Memory Middleware (Optional)

Add memory monitoring middleware to FastAPI app:

```python
from core.memory_middleware import MemoryMonitoringMiddleware

app.add_middleware(MemoryMonitoringMiddleware)
```

## Deployment Recommendations

### For 4GB Memory Instance

1. **Use the optimized environment variables**:
   ```bash
   cp .env.memory-optimized .env
   ```

2. **Disable audio caching** (saves disk space and memory):
   ```bash
   ENABLE_AUDIO_CACHE=false
   ```

3. **Enable aggressive cleanup**:
   ```bash
   AGGRESSIVE_MEMORY_CLEANUP=true
   MEMORY_CLEANUP_INTERVAL=5
   ```

4. **Use fast models** for lower memory usage:
   ```bash
   USE_FAST_MODELS=true
   USE_QUANTIZATION=true
   ```

### For Larger Instances (8GB+)

- Can enable audio caching for debugging: `ENABLE_AUDIO_CACHE=true`
- Less aggressive cleanup: `MEMORY_CLEANUP_INTERVAL=10`
- Enable memory logging if needed: `ENABLE_MEMORY_LOGGING=true`

## Monitoring

### Memory Usage Logs

When memory logging is enabled, you'll see:

```
[Audio Analysis Pipeline] RSS: 512.3MB, Percent: 3.2%, Available: 3421.1MB
[Audio Processing] RSS: 845.2MB, Percent: 5.3%, Available: 3088.2MB
[TTS Audio Generation] RSS: 723.1MB, Percent: 4.5%, Available: 3210.3MB
🧹 Periodic cleanup after 5 requests: 127 objects, RSS: 654.2MB
```

### Warning Thresholds

```
⚠️  WARNING: Memory usage 3100.5MB exceeds warning threshold 3000MB
⚠️  CRITICAL: Memory usage 3600.2MB exceeds critical threshold 3500MB
🧹 Emergency cleanup: 89 objects, RSS: 2891.3MB
```

## Testing

The optimizations have been tested for:

- ✅ Syntax validation of all modified files
- ✅ Import compatibility
- ✅ Memory utility functionality
- ✅ Configuration loading
- ✅ Cleanup mechanisms

## Expected Results

With these optimizations, the backend should:

1. **Handle multiple audio analysis calls** without becoming unresponsive
2. **Maintain stable memory usage** below 3.5GB on a 4GB instance
3. **Automatically cleanup** memory after each request
4. **Reuse cached models** instead of reloading them
5. **Prevent disk space bloat** from temporary audio files

The memory usage should now remain stable across multiple audio analysis calls instead of continuously increasing.