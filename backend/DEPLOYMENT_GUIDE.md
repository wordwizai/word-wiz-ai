# Production Deployment Guide for Optimized Phoneme Extraction

This guide provides specific instructions for deploying the optimized phoneme extraction system in a low-resource production environment.

## Quick Setup for Low-Resource Environments

### 1. Environment Configuration

Create or update your `.env` file with these optimized settings:

```bash
# Copy from .env.example
cp .env.example .env

# Edit .env with production-optimized settings
USE_OPTIMIZED_PHONEME_MODEL=true
USE_MODEL_QUANTIZATION=true
USE_FAST_MODELS=true
USE_MODEL_COMPILATION=true
MODEL_COMPILATION_MODE=reduce-overhead
ENABLE_PERFORMANCE_LOGGING=false
ENABLE_MODEL_CACHE=true
MODEL_WARMUP_RUNS=1
FALLBACK_ON_OPTIMIZATION_ERROR=true
CLEAR_CACHE_AFTER_INIT=true
```

### 2. Docker Configuration

For containerized deployments, add these environment variables to your Docker configuration:

**docker-compose.yml:**
```yaml
services:
  backend:
    environment:
      - USE_OPTIMIZED_PHONEME_MODEL=true
      - USE_MODEL_QUANTIZATION=true
      - USE_FAST_MODELS=true
      - ENABLE_MODEL_CACHE=true
      - CLEAR_CACHE_AFTER_INIT=true
    # Ensure sufficient memory for model loading
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
```

### 3. Kubernetes Configuration

**deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: word-wiz-backend
spec:
  template:
    spec:
      containers:
      - name: backend
        env:
        - name: USE_OPTIMIZED_PHONEME_MODEL
          value: "true"
        - name: USE_MODEL_QUANTIZATION
          value: "true"
        - name: USE_FAST_MODELS
          value: "true"
        - name: ENABLE_MODEL_CACHE
          value: "true"
        resources:
          limits:
            memory: "2Gi"
            cpu: "1500m"
          requests:
            memory: "1Gi"
            cpu: "500m"
```

## Performance Tuning

### Resource-Specific Settings

**For 1.3 vCPU, 1.5GB RAM (Target Environment):**
```bash
USE_OPTIMIZED_PHONEME_MODEL=true
USE_MODEL_QUANTIZATION=true
USE_FAST_MODELS=true
USE_MODEL_COMPILATION=false  # May use too much memory on init
ENABLE_MODEL_CACHE=true
MODEL_WARMUP_RUNS=0  # Skip to save startup time
CLEAR_CACHE_AFTER_INIT=true
```

**For 2+ vCPU, 2+ GB RAM:**
```bash
USE_OPTIMIZED_PHONEME_MODEL=true
USE_MODEL_QUANTIZATION=true
USE_FAST_MODELS=true
USE_MODEL_COMPILATION=true
MODEL_COMPILATION_MODE=reduce-overhead
ENABLE_MODEL_CACHE=true
MODEL_WARMUP_RUNS=1
```

**For Development/Testing:**
```bash
USE_OPTIMIZED_PHONEME_MODEL=true
USE_MODEL_QUANTIZATION=false  # For debugging
USE_FAST_MODELS=false  # Use full model for accuracy testing
ENABLE_PERFORMANCE_LOGGING=true
MODEL_WARMUP_RUNS=0
```

## Monitoring and Alerting

### Performance Metrics to Monitor

1. **Inference Time**: Should be <2 seconds per request
2. **Memory Usage**: Should stay below 1.5GB total
3. **CPU Usage**: Should not consistently exceed 80%
4. **Model Load Time**: Should be <30 seconds on cold start

### Health Check Endpoint

Add this health check to monitor optimization status:

```python
from fastapi import APIRouter
from core.phoneme_assistant import PhonemeAssistant

router = APIRouter()

@router.get("/health/model-optimization")
async def model_optimization_health():
    try:
        assistant = PhonemeAssistant()
        info = assistant.get_performance_info()
        
        return {
            "status": "healthy",
            "optimization_enabled": info["model_info"]["use_quantization"],
            "fast_model": "base" in info["model_info"]["model_name"].lower(),
            "device": info["device"],
            "model_cached": info["model_info"]["model_cached"]
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
```

### Logging Configuration

For production monitoring:

```python
import logging

# Configure performance logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add performance logger
perf_logger = logging.getLogger('phoneme_performance')
```

## Troubleshooting

### Common Issues and Solutions

1. **High Memory Usage**
   ```bash
   # Enable cache clearing
   CLEAR_CACHE_AFTER_INIT=true
   
   # Disable model compilation
   USE_MODEL_COMPILATION=false
   ```

2. **Slow Model Loading**
   ```bash
   # Ensure model caching is enabled
   ENABLE_MODEL_CACHE=true
   
   # Skip warmup runs on resource-constrained systems
   MODEL_WARMUP_RUNS=0
   ```

3. **Inference Timeouts**
   ```bash
   # Use fastest configuration
   USE_FAST_MODELS=true
   USE_MODEL_QUANTIZATION=true
   ```

4. **Model Download Failures**
   ```bash
   # Enable fallback handling
   FALLBACK_ON_OPTIMIZATION_ERROR=true
   ```

### Performance Debugging

Enable detailed performance logging temporarily:

```bash
export ENABLE_PERFORMANCE_LOGGING=true
# Run application and monitor logs
# Disable after debugging:
export ENABLE_PERFORMANCE_LOGGING=false
```

## Deployment Checklist

### Pre-Deployment

- [ ] Set environment variables for optimization
- [ ] Test model loading with target resource constraints
- [ ] Verify quantization works correctly
- [ ] Run performance benchmark
- [ ] Test fallback mechanisms

### Post-Deployment

- [ ] Monitor inference times in production
- [ ] Check memory usage patterns
- [ ] Verify model caching is working
- [ ] Test health check endpoints
- [ ] Monitor error rates and fallbacks

### Performance Validation

Run these commands to validate performance:

```bash
# Test optimization features
python core/test_optimizations.py

# Test optimized system
python core/test_optimized_system.py

# Run performance benchmark (requires model download)
python core/phoneme_performance_test.py
```

## Scaling Considerations

### Horizontal Scaling

- Model cache is per-instance, first request to each instance will be slower
- Consider pre-warming instances or using shared model storage
- Load balancer should consider instance readiness

### Vertical Scaling

- More CPU: Enable model compilation
- More RAM: Disable cache clearing, increase warmup runs
- Less RAM: Use most aggressive optimizations

### Auto-Scaling

Configure auto-scaling based on:
- Average response time >2 seconds
- Memory usage >80%
- CPU usage >75% sustained for >2 minutes

## Security Considerations

### Model Security

- Models are downloaded from HuggingFace Hub
- Verify model checksums in production
- Consider hosting models internally for air-gapped environments

### Environment Variables

- Store sensitive configuration in secrets management
- Audit environment variable access
- Use least-privilege principles

## Migration from Unoptimized Version

### Gradual Migration

1. **Phase 1**: Enable quantization only
   ```bash
   USE_MODEL_QUANTIZATION=true
   USE_FAST_MODELS=false
   ```

2. **Phase 2**: Switch to fast model
   ```bash
   USE_MODEL_QUANTIZATION=true
   USE_FAST_MODELS=true
   ```

3. **Phase 3**: Full optimization
   ```bash
   USE_OPTIMIZED_PHONEME_MODEL=true
   # All optimizations enabled
   ```

### Rollback Plan

To rollback to unoptimized version:
```bash
USE_OPTIMIZED_PHONEME_MODEL=false
USE_MODEL_QUANTIZATION=false
USE_FAST_MODELS=false
FALLBACK_ON_OPTIMIZATION_ERROR=true
```

## Support and Maintenance

### Regular Tasks

- Monitor model performance weekly
- Update models when new optimized versions are available
- Review and tune configuration based on usage patterns
- Test optimization features after PyTorch updates

### Support Information

- Check `OPTIMIZATION_README.md` for technical details
- Run test scripts to diagnose issues
- Enable performance logging for debugging
- Monitor health check endpoints for system status