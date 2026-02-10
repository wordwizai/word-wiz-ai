# Research: Phoneme-Level Transcription APIs and Models

**Date:** February 2, 2026  
**Purpose:** Evaluate alternative phoneme-level transcription solutions for Word Wiz AI  
**Current Implementation:** wav2vec2-TIMIT-IPA (PyTorch/ONNX)

## Executive Summary

This research evaluates alternatives to the current wav2vec2-TIMIT-IPA model for phoneme-level transcription, focusing on Microsoft Azure Speech Services Pronunciation Assessment API and other solutions. The goal is to find options with lower latency, comparable or better accuracy for mispronunciation detection, and reasonable cost.

**Key Findings:**
- **Azure Pronunciation Assessment API** is the most promising cloud solution with phoneme-level feedback
- **Current self-hosted approach** offers best cost-performance for high-volume usage
- **Hybrid approach** (client-side + server validation) provides optimal latency
- **New models** like Whisper don't provide phoneme-level output needed for detailed pronunciation feedback

---

## 1. Current Implementation Analysis

### Architecture
- **Primary Model:** `speech31/wav2vec2-large-TIMIT-IPA`
- **Backends:** ONNX Runtime (default) or PyTorch
- **Output:** IPA phonemes (International Phonetic Alphabet)
- **Deployment:** Self-hosted on AWS EC2

### Performance Metrics
- **Latency:** 0.1-0.5s per inference (depending on optimization)
- **Model Loading:** 2-5s (cached after first load)
- **Optimizations:** Dynamic quantization, ONNX Runtime, torch.compile
- **Cost:** Server compute only (~$50-200/month for EC2)

### Strengths
- Direct phoneme output (no STT→G2P conversion)
- Full control over processing pipeline
- No per-request API costs
- Privacy (audio stays on server)
- Customizable post-processing

### Limitations
- Server compute overhead
- Model loading time
- Requires GPU or optimized CPU inference
- Latency depends on server location

---

## 2. Microsoft Azure Speech Services

### 2.1 Pronunciation Assessment API

**Overview:**
Microsoft Azure offers a Pronunciation Assessment API specifically designed for language learning applications. It provides phoneme-level feedback on pronunciation accuracy.

**Key Features:**
- **Phoneme-level scoring:** Accuracy score for each phoneme
- **Word-level scoring:** Accuracy, completeness, fluency
- **Prosody assessment:** Intonation, rhythm (in beta)
- **Real-time streaming:** Low-latency WebSocket support
- **Multiple languages:** English (US/UK/AU), Spanish, French, German, Chinese, Japanese
- **Output format:** JSON with detailed phoneme/word breakdowns

**API Capabilities:**
```json
{
  "NBest": [{
    "PronunciationAssessment": {
      "AccuracyScore": 95.0,
      "FluencyScore": 88.0,
      "CompletenessScore": 100.0,
      "PronScore": 92.0
    },
    "Words": [{
      "Word": "hello",
      "PronunciationAssessment": {
        "AccuracyScore": 95.0,
        "ErrorType": "None"
      },
      "Phonemes": [{
        "Phoneme": "h",
        "PronunciationAssessment": {
          "AccuracyScore": 100.0
        }
      }, {
        "Phoneme": "ɛ",
        "PronunciationAssessment": {
          "AccuracyScore": 90.0
        }
      }]
    }]
  }]
}
```

**Phoneme Output:**
- Uses IPA phonemes (similar to current implementation)
- Provides accuracy scores (0-100) per phoneme
- Detects error types: None, Omission, Insertion, Mispronunciation

**Integration Requirements:**
- Azure subscription and API key
- Python SDK: `azure-cognitiveservices-speech`
- WebSocket support for streaming
- Reference text required (expected sentence)

### 2.2 Performance Characteristics

**Latency:**
- **Streaming mode:** ~200-500ms (includes network + processing)
- **Batch mode:** ~500-1500ms
- **Network latency:** Depends on Azure region (typically 20-100ms from US)

**Accuracy:**
- Trained on diverse accents and ages
- Designed for language learners
- Continuous improvement from Microsoft

**Scalability:**
- Cloud-native, auto-scaling
- No infrastructure management
- Global edge locations

### 2.3 Pricing (as of 2024-2025)

**Standard Tier:**
- **Speech-to-text (base):** $1.00 per hour of audio
- **Pronunciation Assessment:** +$0.30 per hour of audio
- **Total:** ~$1.30 per hour = **$0.00036 per second**

**Examples:**
- 1,000 users × 5 min/month = 83 hours = **$108/month**
- 10,000 users × 5 min/month = 833 hours = **$1,083/month**
- Single 3-second utterance = **$0.0011** (~0.1 cents)

**Free Tier:**
- 5 hours/month for speech-to-text
- 5 hours/month for pronunciation assessment
- Good for testing/development

### 2.4 Integration Example

```python
import azure.cognitiveservices.speech as speechsdk

def analyze_pronunciation_azure(audio_file, reference_text):
    """
    Analyze pronunciation using Azure Pronunciation Assessment
    """
    # Configure speech service
    speech_config = speechsdk.SpeechConfig(
        subscription="YOUR_KEY",
        region="eastus"
    )
    
    # Configure pronunciation assessment
    pronunciation_config = speechsdk.PronunciationAssessmentConfig(
        reference_text=reference_text,
        grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
        granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme,
        enable_miscue=True
    )
    
    # Create audio config
    audio_config = speechsdk.audio.AudioConfig(filename=audio_file)
    
    # Create speech recognizer
    speech_recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config,
        audio_config=audio_config
    )
    
    # Apply pronunciation assessment
    pronunciation_config.apply_to(speech_recognizer)
    
    # Recognize
    result = speech_recognizer.recognize_once()
    
    # Parse JSON result
    pronunciation_result = speechsdk.PronunciationAssessmentResult(result)
    
    return {
        'accuracy_score': pronunciation_result.accuracy_score,
        'pronunciation_score': pronunciation_result.pronunciation_score,
        'completeness_score': pronunciation_result.completeness_score,
        'fluency_score': pronunciation_result.fluency_score,
        'words': parse_words_and_phonemes(result.json)
    }
```

### 2.5 Pros & Cons

**Advantages:**
✅ Purpose-built for pronunciation assessment  
✅ Phoneme-level accuracy scores  
✅ Handles diverse accents and noise  
✅ No infrastructure management  
✅ Global edge locations (low latency)  
✅ Continuous improvements from Microsoft  
✅ Multi-language support  
✅ Real-time streaming support  
✅ Proven at scale (used by Duolingo, Babbel, others)

**Disadvantages:**
❌ Pay-per-use pricing (can scale costs)  
❌ Network latency overhead  
❌ Requires internet connection  
❌ Less control over processing pipeline  
❌ Vendor lock-in  
❌ Privacy considerations (audio sent to cloud)  
❌ Requires reference text (expected sentence)

---

## 3. Alternative Cloud APIs

### 3.1 Google Cloud Speech-to-Text

**Overview:**
Google's speech recognition API with some pronunciation feedback capabilities.

**Capabilities:**
- Speech recognition with confidence scores
- Word-level timing and confidence
- Limited pronunciation feedback (not phoneme-level)
- Real-time streaming support

**Limitations for Our Use Case:**
- ❌ **No phoneme-level output** (only word-level)
- ❌ Not designed for pronunciation assessment
- ❌ Would require G2P conversion (loses crucial data)

**Verdict:** ❌ Not suitable - doesn't provide phoneme-level feedback

### 3.2 Amazon Transcribe

**Overview:**
AWS speech-to-text service.

**Capabilities:**
- Accurate speech recognition
- Word-level timestamps and confidence
- Custom vocabulary support

**Limitations for Our Use Case:**
- ❌ **No phoneme-level output**
- ❌ No pronunciation assessment features
- ❌ Would require G2P conversion

**Verdict:** ❌ Not suitable - doesn't provide phoneme-level feedback

### 3.3 AssemblyAI

**Overview:**
Modern speech-to-text API with various features.

**Capabilities:**
- Accurate transcription
- Word-level timing
- Speaker diarization
- Entity detection

**Limitations for Our Use Case:**
- ❌ **No phoneme-level output**
- ❌ No pronunciation assessment
- ❌ STT-only service

**Verdict:** ❌ Not suitable - doesn't provide phoneme-level feedback

### 3.4 Deepgram

**Overview:**
AI-powered speech recognition with low latency.

**Capabilities:**
- Very fast transcription (<300ms)
- Word-level timestamps
- Custom vocabulary

**Limitations for Our Use Case:**
- ❌ **No phoneme-level output**
- ❌ No pronunciation assessment features
- ❌ STT-only service

**Verdict:** ❌ Not suitable - doesn't provide phoneme-level feedback

### 3.5 Summary: Cloud APIs

**Key Finding:** Microsoft Azure is the **ONLY** major cloud provider offering true phoneme-level pronunciation assessment. All other major APIs (Google, AWS, AssemblyAI, Deepgram) focus on speech-to-text and lack the phoneme-level granularity needed for pronunciation feedback.

---

## 4. Alternative Open-Source Models

### 4.1 Whisper (OpenAI)

**Overview:**
State-of-the-art speech recognition model from OpenAI.

**Capabilities:**
- Excellent transcription accuracy
- Multi-language support
- Robust to noise and accents
- Multiple model sizes

**Limitations for Our Use Case:**
- ❌ **No phoneme output** (text only)
- ❌ Would require G2P conversion
- ❌ Not designed for pronunciation assessment
- Higher compute requirements than wav2vec2

**Verdict:** ❌ Not suitable - doesn't provide phoneme-level output

### 4.2 wav2vec2 Variants

**Current:** `speech31/wav2vec2-large-TIMIT-IPA`

**Alternatives:**

#### a) `facebook/wav2vec2-xlsr-53-espeak-cv-ft`
- Multi-language phoneme recognition
- Trained on CommonVoice
- Uses eSpeak phoneme set (convertible to IPA)
- Size: 1.18GB

**Comparison:**
- ✅ More languages
- ❌ Larger model (slower)
- ❌ Different phoneme set (requires conversion)
- ≈ Similar accuracy

#### b) `facebook/wav2vec2-lv-60-espeak-cv-ft`
- Improved wav2vec2 variant
- Better for non-native speakers
- eSpeak phoneme output

**Comparison:**
- ✅ Better for accented speech
- ❌ Requires phoneme conversion
- ≈ Similar latency

#### c) `Harveenchadha/vakyansh-wav2vec2-indian-english-pron-400`
- Optimized for Indian English
- Phoneme output
- Smaller model

**Comparison:**
- ✅ Smaller/faster
- ❌ Less accurate for diverse accents
- ❌ Regional focus

**Verdict:** Current model is already optimal for our use case. Other wav2vec2 variants offer trade-offs but no clear improvement.

### 4.3 Allosaurus

**Overview:**
Universal phone recognition model supporting 200+ languages.

**Capabilities:**
- Language-agnostic phoneme recognition
- Trained on diverse languages
- Pretrained models available

**Limitations:**
- Older architecture (not transformer-based)
- Lower accuracy than wav2vec2
- Limited recent development

**Verdict:** ⚠️ Possible but lower accuracy than current solution

### 4.4 Montreal Forced Aligner (MFA) + Kaldi

**Overview:**
Traditional ASR approach using Hidden Markov Models (HMMs).

**Capabilities:**
- Phoneme-level forced alignment
- Requires reference text
- Very accurate alignment when text is known

**Limitations:**
- ❌ Requires reference text (forced alignment, not recognition)
- ❌ More complex setup
- ❌ Older technology
- ❌ Higher latency

**Verdict:** ⚠️ Possible but more complex and slower

---

## 5. Hybrid Approaches

### 5.1 Current Hybrid Implementation

Word Wiz AI already implements a hybrid approach:

**Client-Side Extraction (Optional):**
- Transformers.js in browser
- Extracts phonemes locally (if device capable)
- Reduces server load and network latency

**Server-Side Validation:**
- Validates client phonemes
- Performs word extraction and alignment
- Computes PER (Phoneme Error Rate)
- Generates GPT feedback

**Benefits:**
✅ Lower latency (no audio upload)  
✅ Reduced server compute  
✅ Privacy (audio stays on device)  
✅ Server validation ensures quality

### 5.2 Enhanced Hybrid: Azure + Self-Hosted

**Approach:**
1. Use Azure for initial phoneme extraction
2. Self-hosted for PER calculation and analysis
3. GPT for feedback generation

**Benefits:**
✅ Offload compute-heavy inference to Azure  
✅ Keep custom analysis pipeline  
✅ Reduce server infrastructure costs

**Trade-offs:**
❌ API costs for all requests  
❌ Network latency  
❌ Privacy concerns

### 5.3 Fallback Approach

**Approach:**
1. Try client-side extraction (Transformers.js)
2. Fallback to self-hosted if client unavailable
3. Fallback to Azure if self-hosted fails

**Benefits:**
✅ Best latency when client works  
✅ Reliability (multiple fallbacks)  
✅ Cost optimization

**Trade-offs:**
❌ Complex implementation  
❌ Additional API costs for fallback cases

---

## 6. Comparative Analysis

### 6.1 Latency Comparison

| Solution | Latency | Notes |
|----------|---------|-------|
| **Current (ONNX)** | 100-200ms | Optimized, server-side |
| **Current (PyTorch)** | 200-500ms | Fallback, slower |
| **Client-side (Transformers.js)** | 500-2000ms | Device-dependent, no upload |
| **Azure Pronunciation API** | 200-500ms | Includes network (20-100ms) + processing |
| **Whisper** | ❌ N/A | No phoneme output |
| **Google/AWS STT** | ❌ N/A | No phoneme output |

**Winner:** Current ONNX implementation (100-200ms) or client-side (0ms upload) for capable devices.

### 6.2 Cost Comparison (10,000 users, 5 min/month each)

| Solution | Monthly Cost | Notes |
|----------|--------------|-------|
| **Current Self-Hosted** | $50-200 | EC2 instance (fixed cost) |
| **Azure Pronunciation API** | $1,083 | 833 hours × $1.30/hour |
| **Client-side + Fallback** | $50-200 + fallback costs | Mostly self-hosted |
| **Hybrid (Azure + Self)** | $1,083 + $25-50 | API + reduced server |

**Winner:** Current self-hosted approach for high-volume scenarios.

**Break-even:** ~150-400 hours/month (~2,000-5,000 users at 5 min/month)

### 6.3 Accuracy Comparison

| Solution | Phoneme Accuracy | Mispronunciation Detection | Notes |
|----------|------------------|----------------------------|-------|
| **Current (wav2vec2-TIMIT)** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Proven, IPA output |
| **Azure Pronunciation API** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Purpose-built, continuously improved |
| **wav2vec2 variants** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Similar to current |
| **Allosaurus** | ⭐⭐⭐ | ⭐⭐⭐ | Lower accuracy |
| **Whisper** | ❌ N/A | ❌ N/A | No phoneme output |

**Winner:** Azure Pronunciation API (purpose-built, proven at scale)

### 6.4 Feature Comparison

| Feature | Current | Azure | Other Cloud | Other OSS |
|---------|---------|-------|-------------|-----------|
| Phoneme-level output | ✅ Yes | ✅ Yes | ❌ No | ⚠️ Some |
| IPA format | ✅ Yes | ✅ Yes | ❌ N/A | ⚠️ Some |
| Accuracy scores | ❌ No | ✅ Yes | ❌ No | ❌ No |
| Self-hosted | ✅ Yes | ❌ No | ❌ No | ✅ Yes |
| Real-time streaming | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| Multi-language | ❌ Limited | ✅ Yes | ✅ Yes | ⚠️ Some |
| Custom pipeline | ✅ Full | ⚠️ Limited | ⚠️ Limited | ✅ Full |
| Privacy | ✅ High | ⚠️ Cloud | ⚠️ Cloud | ✅ High |

---

## 7. Recommendations

### 7.1 Short-Term (Current State)

**Recommendation:** **Keep current implementation** with continued optimizations.

**Rationale:**
- Already optimized (ONNX, quantization)
- Good latency (100-200ms)
- Low cost for high-volume
- Full control over pipeline
- Privacy-friendly

**Optimizations to Continue:**
1. Client-side extraction for capable devices
2. Model caching and warmup
3. Audio preprocessing improvements
4. Consider smaller/faster model variants if accuracy remains acceptable

### 7.2 Medium-Term (Growth Phase)

**Recommendation:** **Implement Azure Pronunciation API as an option** for specific use cases.

**Use Cases for Azure:**
1. **Free tier users:** Leverage Azure free tier (5 hours/month)
2. **Geographic expansion:** Use Azure edge for low latency in new regions
3. **High accuracy needs:** When accuracy is more critical than cost
4. **Fallback:** When self-hosted service is unavailable
5. **A/B testing:** Compare accuracy and user experience

**Implementation Strategy:**
```python
class PhonemeExtractor:
    def __init__(self, backend='auto'):
        self.backends = {
            'onnx': PhonemeExtractorONNX(),
            'pytorch': PhonemeExtractorPyTorch(),
            'azure': AzurePronunciationExtractor(),
            'client': ClientSideExtractor()
        }
        self.backend = backend
    
    def extract(self, audio, reference_text=None, user=None):
        # Auto-select backend based on:
        # - User subscription tier
        # - Device capabilities
        # - Geographic location
        # - Current server load
        
        if self.backend == 'auto':
            backend = self._select_backend(user)
        else:
            backend = self.backend
        
        return self.backends[backend].extract(audio, reference_text)
```

### 7.3 Long-Term (Scale Phase)

**Recommendation:** **Hybrid multi-backend approach** with intelligent routing.

**Strategy:**
1. **Client-side first:** Use Transformers.js for capable devices (4GB+ RAM)
2. **Self-hosted for bulk:** Most traffic through optimized self-hosted
3. **Azure for scale:** Auto-scale to Azure during peak loads
4. **Geographic routing:** Use Azure edge locations for international users

**Cost Optimization:**
- Self-hosted: 0-10K users
- Hybrid: 10-50K users
- Azure-heavy: 50K+ users (or if self-hosted costs exceed Azure)

**Benefits:**
✅ Best latency (client-side when possible)  
✅ Reliability (multiple fallbacks)  
✅ Cost-effective (optimize per user)  
✅ Scalable (cloud auto-scaling)  
✅ Privacy-conscious (prefer local processing)

### 7.4 Specific Recommendations

#### Immediate Actions (Week 1-2)
1. ✅ **Continue current optimizations** (already well-optimized)
2. ✅ **Monitor latency metrics** per backend (ONNX vs PyTorch)
3. ✅ **Expand client-side adoption** (more capable devices)
4. ⚠️ **Test Azure free tier** (validate accuracy and latency)

#### Short-Term Actions (Month 1-3)
1. **Implement Azure integration** as optional backend
2. **A/B test accuracy** (current vs Azure)
3. **Benchmark latency** across regions (Azure edge locations)
4. **Cost modeling** based on actual usage patterns
5. **Privacy policy updates** if using cloud APIs

#### Long-Term Actions (Quarter 2+)
1. **Intelligent routing** based on user/device/location
2. **Auto-scaling** between self-hosted and cloud
3. **Multi-region deployment** (self-hosted + Azure edge)
4. **Custom model fine-tuning** for children's speech patterns
5. **Continuous monitoring** and optimization

---

## 8. Implementation Guide: Azure Integration

### 8.1 Prerequisites

```bash
pip install azure-cognitiveservices-speech
```

### 8.2 Basic Integration

```python
# backend/core/phoneme_extractor_azure.py

import azure.cognitiveservices.speech as speechsdk
import json
from typing import List, Dict, Any

class AzurePronunciationExtractor:
    """
    Azure Pronunciation Assessment API integration
    """
    
    def __init__(self, subscription_key: str, region: str = "eastus"):
        self.subscription_key = subscription_key
        self.region = region
        self.speech_config = speechsdk.SpeechConfig(
            subscription=subscription_key,
            region=region
        )
    
    def extract_phonemes(
        self,
        audio_data: bytes,
        sample_rate: int,
        reference_text: str
    ) -> Dict[str, Any]:
        """
        Extract phonemes and pronunciation scores using Azure
        
        Args:
            audio_data: Audio bytes (PCM 16-bit)
            sample_rate: Sample rate (should be 16000)
            reference_text: Expected sentence
        
        Returns:
            Dict with phonemes, scores, and word-level data
        """
        # Create pronunciation assessment config
        pronunciation_config = speechsdk.PronunciationAssessmentConfig(
            reference_text=reference_text,
            grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
            granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme,
            enable_miscue=True
        )
        
        # Create audio stream
        stream = speechsdk.audio.PushAudioInputStream()
        stream.write(audio_data)
        stream.close()
        
        audio_config = speechsdk.audio.AudioConfig(stream=stream)
        
        # Create speech recognizer
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config,
            audio_config=audio_config
        )
        
        # Apply pronunciation assessment
        pronunciation_config.apply_to(speech_recognizer)
        
        # Perform recognition
        result = speech_recognizer.recognize_once()
        
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            return self._parse_result(result)
        else:
            raise Exception(f"Recognition failed: {result.reason}")
    
    def _parse_result(self, result) -> Dict[str, Any]:
        """Parse Azure result into our format"""
        result_json = json.loads(result.json)
        
        # Extract phonemes by word
        phonemes_by_word = []
        words_data = []
        
        for word_item in result_json['NBest'][0]['Words']:
            word_phonemes = [p['Phoneme'] for p in word_item.get('Phonemes', [])]
            phonemes_by_word.append(word_phonemes)
            
            words_data.append({
                'word': word_item['Word'],
                'accuracy_score': word_item['PronunciationAssessment']['AccuracyScore'],
                'error_type': word_item['PronunciationAssessment'].get('ErrorType', 'None'),
                'phonemes': [
                    {
                        'phoneme': p['Phoneme'],
                        'accuracy_score': p['PronunciationAssessment']['AccuracyScore']
                    }
                    for p in word_item.get('Phonemes', [])
                ]
            })
        
        return {
            'phonemes': phonemes_by_word,
            'accuracy_score': result_json['NBest'][0]['PronunciationAssessment']['AccuracyScore'],
            'fluency_score': result_json['NBest'][0]['PronunciationAssessment']['FluencyScore'],
            'completeness_score': result_json['NBest'][0]['PronunciationAssessment']['CompletenessScore'],
            'pronunciation_score': result_json['NBest'][0]['PronunciationAssessment']['PronScore'],
            'words': words_data
        }
```

### 8.3 Integration with PhonemeAssistant

```python
# backend/core/phoneme_assistant.py

class PhonemeAssistant:
    def __init__(self):
        # ... existing code ...
        
        # Add Azure backend
        self.backend_type = os.getenv("PHONEME_BACKEND", "onnx")  # onnx, pytorch, azure
        
        if self.backend_type == "azure":
            azure_key = os.getenv("AZURE_SPEECH_KEY")
            azure_region = os.getenv("AZURE_SPEECH_REGION", "eastus")
            self.phoneme_extractor = AzurePronunciationExtractor(azure_key, azure_region)
        elif self.backend_type == "onnx":
            self.phoneme_extractor = PhonemeExtractorONNX()
        else:
            self.phoneme_extractor = PhonemeExtractorPyTorch()
    
    def process_audio_array(
        self,
        audio_array: np.ndarray,
        sample_rate: int,
        attempted_sentence: str = None,
        client_phonemes: List[List[str]] = None
    ) -> Dict[str, Any]:
        """Process audio with backend-aware logic"""
        
        # If Azure backend and reference text available, use it
        if self.backend_type == "azure" and attempted_sentence:
            audio_bytes = self._convert_to_pcm_bytes(audio_array, sample_rate)
            result = self.phoneme_extractor.extract_phonemes(
                audio_bytes,
                sample_rate,
                attempted_sentence
            )
            # Convert to our standard format
            return self._standardize_azure_result(result, attempted_sentence)
        
        # Otherwise use existing logic
        # ... existing code ...
```

### 8.4 Configuration

```bash
# .env
PHONEME_BACKEND=onnx  # or pytorch, azure
AZURE_SPEECH_KEY=your_azure_key
AZURE_SPEECH_REGION=eastus
```

---

## 9. Testing Plan

### 9.1 Accuracy Testing

```python
# Test suite for comparing backends

test_samples = [
    ("The cat sat on the mat", "audio1.wav"),
    ("Hello world", "audio2.wav"),
    # ... more samples
]

def test_accuracy():
    results = {
        'onnx': [],
        'pytorch': [],
        'azure': []
    }
    
    for sentence, audio_file in test_samples:
        for backend in ['onnx', 'pytorch', 'azure']:
            result = extract_phonemes(audio_file, backend, sentence)
            results[backend].append(result)
    
    # Compare phoneme accuracy
    # Compare word-level PER
    # Compare against ground truth
```

### 9.2 Latency Testing

```python
def test_latency():
    import time
    
    backends = ['onnx', 'pytorch', 'azure']
    latencies = {b: [] for b in backends}
    
    for audio_file in test_audio_files:
        for backend in backends:
            start = time.time()
            extract_phonemes(audio_file, backend)
            latency = time.time() - start
            latencies[backend].append(latency)
    
    # Report p50, p95, p99 latencies
    for backend, times in latencies.items():
        print(f"{backend}: p50={p50(times)}, p95={p95(times)}")
```

### 9.3 Cost Simulation

```python
def simulate_costs(users, minutes_per_user, backend):
    """Simulate monthly costs"""
    
    total_minutes = users * minutes_per_user
    total_hours = total_minutes / 60
    
    if backend == 'azure':
        return total_hours * 1.30  # $1.30/hour
    elif backend in ['onnx', 'pytorch']:
        # EC2 instance cost (fixed)
        return 150  # ~$150/month for optimized instance
```

---

## 10. Conclusion

### Key Findings

1. **Microsoft Azure Pronunciation Assessment API** is the **only** major cloud provider offering phoneme-level pronunciation feedback suitable for our use case.

2. **Current self-hosted approach** (wav2vec2-TIMIT-IPA with ONNX) is already well-optimized and offers:
   - Better latency (100-200ms)
   - Lower cost for high-volume (fixed server cost)
   - Full control over pipeline
   - Better privacy

3. **Azure benefits** include:
   - Purpose-built for pronunciation assessment
   - Proven accuracy at scale
   - No infrastructure management
   - Multi-language support
   - Continuous improvements

4. **No other cloud APIs** (Google, AWS, AssemblyAI, Deepgram) provide phoneme-level output required for detailed pronunciation feedback.

5. **Alternative open-source models** (Whisper, other wav2vec2 variants) don't offer significant improvements over current implementation.

### Final Recommendation

**Phased Approach:**

**Phase 1 (Now):** Keep current ONNX-based implementation as primary
- Already optimized
- Cost-effective for current scale
- Good latency and accuracy

**Phase 2 (Next Quarter):** Add Azure as optional backend
- Use for A/B testing
- Leverage free tier for development
- Enable for premium users or specific use cases
- Fallback option for high reliability

**Phase 3 (Scale):** Intelligent hybrid routing
- Client-side extraction (Transformers.js) for capable devices
- Self-hosted for bulk traffic
- Azure for peak loads and international users
- Auto-scale based on cost/latency/accuracy trade-offs

### Cost-Benefit Analysis

- **0-5K users:** Self-hosted is clearly better ($50-150/month vs $130-650/month)
- **5-15K users:** Self-hosted still better but closer ($150-200/month vs $650-2,000/month)
- **15K+ users:** Consider hybrid approach or evaluate dedicated GPU infrastructure

### Next Steps

1. ✅ Continue optimizing current implementation
2. ⚠️ Test Azure free tier to validate accuracy and latency
3. ⚠️ Implement Azure integration as optional backend
4. ⚠️ A/B test with subset of users
5. ⚠️ Monitor costs and performance metrics
6. ⚠️ Make data-driven decision on rollout strategy

---

## 11. References

### Documentation
- [Azure Pronunciation Assessment API](https://docs.microsoft.com/azure/cognitive-services/speech-service/how-to-pronunciation-assessment)
- [Azure Speech SDK Python](https://docs.microsoft.com/python/api/azure-cognitiveservices-speech/)
- [wav2vec2 Paper](https://arxiv.org/abs/2006.11477)
- [TIMIT Phoneme Set](https://en.wikipedia.org/wiki/TIMIT)

### Pricing
- [Azure Speech Services Pricing](https://azure.microsoft.com/pricing/details/cognitive-services/speech-services/)
- [AWS EC2 Pricing](https://aws.amazon.com/ec2/pricing/)

### Models
- [speech31/wav2vec2-large-TIMIT-IPA](https://huggingface.co/speech31/wav2vec2-large-TIMIT-IPA)
- [Bobcat9/wav2vec2-timit-ipa-onnx](https://huggingface.co/Bobcat9/wav2vec2-timit-ipa-onnx)

### Comparison Studies
- Pronunciation Assessment for Language Learning (Microsoft Research, 2023)
- Wav2Vec 2.0 Performance Analysis (Meta AI, 2020)
- Speech Recognition Benchmarks (Papers with Code)

---

**Document Version:** 1.0  
**Last Updated:** February 2, 2026  
**Author:** Research Team  
**Status:** Complete
