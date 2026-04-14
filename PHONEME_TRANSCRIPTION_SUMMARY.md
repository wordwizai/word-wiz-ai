# Phoneme Transcription Research - Executive Summary

**Date:** February 2, 2026  
**Objective:** Evaluate alternatives to wav2vec2-TIMIT-IPA for lower latency and better cost-performance

---

## TL;DR

✅ **Current implementation is already optimal for our scale**  
✅ **Microsoft Azure Pronunciation Assessment API is the only viable cloud alternative**  
❌ **No other cloud APIs (Google, AWS, etc.) provide phoneme-level output**  
⚠️ **Recommend hybrid approach: keep current + add Azure as optional backend**

---

## Current State

**Model:** wav2vec2-TIMIT-IPA (ONNX optimized)  
**Latency:** 100-200ms (excellent)  
**Cost:** $50-200/month (fixed server cost)  
**Accuracy:** High (IPA phoneme output)  
**Status:** ✅ Well-optimized, production-ready

---

## Research Findings

### Cloud APIs Evaluated

| Provider | Phoneme Output? | Verdict |
|----------|----------------|---------|
| **Microsoft Azure** | ✅ Yes (IPA + accuracy scores) | ✅ **ONLY viable option** |
| Google Cloud | ❌ No (word-level only) | ❌ Not suitable |
| AWS Transcribe | ❌ No (word-level only) | ❌ Not suitable |
| AssemblyAI | ❌ No (STT only) | ❌ Not suitable |
| Deepgram | ❌ No (STT only) | ❌ Not suitable |

### Alternative Models Evaluated

| Model | Phoneme Output? | Verdict |
|-------|----------------|---------|
| **Whisper (OpenAI)** | ❌ No (text only) | ❌ Not suitable |
| wav2vec2 variants | ✅ Yes | ≈ Similar to current |
| Allosaurus | ✅ Yes | ⚠️ Lower accuracy |
| Kaldi/MFA | ✅ Yes (requires reference text) | ⚠️ More complex |

**Key Finding:** Current wav2vec2-TIMIT-IPA is already the best open-source option.

---

## Microsoft Azure Pronunciation Assessment

### What It Offers
- ✅ Phoneme-level accuracy scores (IPA format)
- ✅ Word-level pronunciation assessment
- ✅ Real-time streaming (WebSocket)
- ✅ Multi-language support
- ✅ Purpose-built for language learning
- ✅ Proven at scale (Duolingo, Babbel)

### Performance
- **Latency:** 200-500ms (includes network ~20-100ms + processing)
- **Accuracy:** Higher than self-hosted (continuously improved by Microsoft)
- **Reliability:** Cloud-native, auto-scaling

### Pricing
- **Cost:** $1.30 per hour of audio (~$0.00036/second)
- **Free Tier:** 5 hours/month (good for testing)

**Examples:**
- 1,000 users × 5 min/month = **$108/month**
- 10,000 users × 5 min/month = **$1,083/month**
- Single 3-second utterance = **$0.0011** (~0.1 cents)

### When Azure Makes Sense
✅ Testing/development (free tier)  
✅ Premium users (when accuracy > cost)  
✅ International users (edge locations)  
✅ Peak load handling (auto-scale)  
✅ Fallback reliability  

### When Self-Hosted Is Better
✅ High-volume usage (>5K users)  
✅ Cost-sensitive operations  
✅ Privacy requirements  
✅ Custom pipeline needs  
✅ Predictable traffic  

---

## Cost Comparison

### Monthly Cost by User Count (5 min/user/month)

| Users | Self-Hosted | Azure | Winner |
|-------|-------------|-------|--------|
| 1,000 | $50-150 | $108 | ≈ Tie |
| 5,000 | $100-200 | $542 | Self-hosted |
| 10,000 | $150-250 | $1,083 | Self-hosted |
| 50,000 | $300-500 | $5,417 | Self-hosted |

**Break-even:** ~2,000-5,000 users (depending on infrastructure)

**Conclusion:** Self-hosted is more cost-effective at scale.

---

## Latency Comparison

| Solution | Latency | Winner |
|----------|---------|--------|
| **Current (ONNX)** | 100-200ms | ✅ Best |
| **Current (PyTorch)** | 200-500ms | Good |
| **Client-side (Transformers.js)** | 500-2000ms | ⚠️ Device-dependent |
| **Azure API** | 200-500ms | Good |

**Conclusion:** Current ONNX implementation has the lowest latency.

---

## Recommendations

### ✅ Phase 1: Keep Current (Immediate)
**Action:** Continue with wav2vec2-TIMIT-IPA + ONNX optimization

**Rationale:**
- Already optimized (100-200ms latency)
- Cost-effective for current scale
- Full control over pipeline
- Privacy-friendly

**Ongoing Optimizations:**
- Expand client-side extraction (Transformers.js)
- Monitor and tune ONNX performance
- Cache warming and model optimization

### ⚠️ Phase 2: Add Azure Option (Next Quarter)
**Action:** Implement Azure Pronunciation Assessment as optional backend

**Use Cases:**
1. **Free tier users:** Leverage 5 hours/month free tier
2. **A/B testing:** Compare accuracy and user experience
3. **Premium tier:** Offer enhanced accuracy
4. **Fallback:** Reliability when self-hosted unavailable
5. **International:** Lower latency via Azure edge locations

**Implementation:**
```python
# Backend selection logic
def select_backend(user, location, device):
    if device.can_run_client_ml:
        return "client_side"
    elif user.tier == "premium":
        return "azure"
    elif server_load > 80%:
        return "azure"
    else:
        return "onnx"  # self-hosted
```

### 🎯 Phase 3: Intelligent Hybrid (Scale Phase)
**Action:** Multi-backend routing based on user/device/load

**Strategy:**
1. **Client-side first:** Transformers.js for capable devices (4GB+ RAM)
2. **Self-hosted bulk:** Most traffic through optimized ONNX
3. **Azure for scale:** Auto-scale during peaks
4. **Geographic routing:** Azure edge for international users

**Benefits:**
- Best latency (client-side when possible)
- Cost optimization (self-hosted for bulk)
- Reliability (multiple fallbacks)
- Scalability (cloud auto-scale)

---

## Implementation Priority

### Must Do Now ✅
1. ✅ Continue current optimizations
2. ✅ Document current performance metrics
3. ✅ Expand client-side extraction adoption

### Should Do Next (Month 1-2) ⚠️
1. Test Azure free tier (validate accuracy/latency)
2. Implement Azure integration (optional backend)
3. A/B test with subset of users
4. Monitor cost and performance

### Can Do Later (Quarter 2+) 💡
1. Intelligent routing logic
2. Auto-scaling between backends
3. Multi-region deployment
4. Custom model fine-tuning for children's speech

---

## Technical Details

### Azure Integration (Simplified)

```python
import azure.cognitiveservices.speech as speechsdk

def analyze_pronunciation(audio_file, expected_text):
    # Configure Azure
    speech_config = speechsdk.SpeechConfig(
        subscription="YOUR_KEY",
        region="eastus"
    )
    
    # Configure pronunciation assessment
    pronunciation_config = speechsdk.PronunciationAssessmentConfig(
        reference_text=expected_text,
        grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
        granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme
    )
    
    # Analyze
    audio_config = speechsdk.audio.AudioConfig(filename=audio_file)
    recognizer = speechsdk.SpeechRecognizer(speech_config, audio_config)
    pronunciation_config.apply_to(recognizer)
    
    result = recognizer.recognize_once()
    
    # Returns phoneme-level accuracy scores in IPA format
    return parse_result(result)
```

### Environment Variables

```bash
# .env
PHONEME_BACKEND=onnx  # Options: onnx, pytorch, azure, auto
AZURE_SPEECH_KEY=your_key_here
AZURE_SPEECH_REGION=eastus
```

---

## Why Not Other Solutions?

### Whisper (OpenAI)
❌ **No phoneme output** - only text transcription  
❌ Would require G2P conversion (loses crucial data)  
❌ Not designed for pronunciation assessment

### Google Cloud Speech / AWS Transcribe
❌ **No phoneme-level output** - word-level only  
❌ Not designed for pronunciation assessment  
❌ Would require G2P conversion

### Other wav2vec2 Variants
≈ **Similar performance** to current model  
≈ Trade-offs but no clear improvement  
✅ Current model already optimal

---

## Key Metrics to Monitor

### Performance Metrics
- **P50/P95/P99 latency** by backend
- **Model loading time** (cold start)
- **Memory usage** per request
- **CPU utilization** on server

### Business Metrics
- **Cost per user** by backend
- **Cost per minute** of audio processed
- **Accuracy scores** (compared to ground truth)
- **User satisfaction** (by backend)

### Reliability Metrics
- **Error rate** by backend
- **Fallback frequency**
- **API availability** (Azure SLA)
- **Server uptime** (self-hosted)

---

## Decision Matrix

### Choose Self-Hosted (Current) When:
✅ High volume (5K+ users)  
✅ Cost is primary concern  
✅ Privacy is critical  
✅ Custom pipeline needed  
✅ Predictable traffic

### Choose Azure When:
✅ Low volume (<2K users)  
✅ Accuracy is primary concern  
✅ No infrastructure management  
✅ Need multi-language  
✅ International users (latency)

### Choose Hybrid When:
✅ Scaling rapidly  
✅ Geographic diversity  
✅ Need reliability (fallbacks)  
✅ Optimizing cost AND performance  
✅ Different user tiers

---

## Conclusion

**Bottom Line:** Current implementation is already excellent. Azure is the only viable cloud alternative worth considering.

**Recommended Action:** Implement phased approach:
1. **Now:** Keep and optimize current system
2. **Next:** Add Azure as optional backend for testing
3. **Later:** Intelligent hybrid routing at scale

**Expected Outcome:**
- Lower costs at current scale (self-hosted)
- Higher reliability (cloud fallback)
- Better international latency (Azure edge)
- Flexibility for growth (hybrid approach)

---

## Questions?

For detailed analysis, see: [`research_phoneme_transcription_apis.md`](./research_phoneme_transcription_apis.md)

For implementation guide, see: Section 8 of main research document

For cost calculations, see: Section 6.2 of main research document
