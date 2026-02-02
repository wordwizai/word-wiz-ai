# Azure Pronunciation Assessment - Implementation Guide

This guide provides ready-to-use code for integrating Microsoft Azure Pronunciation Assessment API into Word Wiz AI.

---

## Prerequisites

### 1. Install Azure Speech SDK

```bash
pip install azure-cognitiveservices-speech
```

### 2. Get Azure Credentials

1. Create Azure account: https://azure.microsoft.com/free/
2. Create Speech Service resource
3. Get subscription key and region
4. Free tier: 5 hours/month

### 3. Environment Variables

```bash
# Add to backend/.env
PHONEME_BACKEND=auto  # Options: onnx, pytorch, azure, auto
AZURE_SPEECH_KEY=your_subscription_key_here
AZURE_SPEECH_REGION=eastus  # or your preferred region
ENABLE_AZURE_FALLBACK=true
```

---

## Implementation

### File 1: Azure Phoneme Extractor

Create: `backend/core/phoneme_extractor_azure.py`

```python
"""
Azure Pronunciation Assessment API Integration
Provides phoneme-level pronunciation feedback using Microsoft Azure Speech Services
"""

import azure.cognitiveservices.speech as speechsdk
import json
import numpy as np
import io
from typing import List, Dict, Any, Optional
from pydub import AudioSegment
import logging

logger = logging.getLogger(__name__)


class AzurePronunciationExtractor:
    """
    Phoneme extractor using Azure Pronunciation Assessment API
    """
    
    def __init__(self, subscription_key: str, region: str = "eastus"):
        """
        Initialize Azure pronunciation extractor
        
        Args:
            subscription_key: Azure Speech Services subscription key
            region: Azure region (e.g., 'eastus', 'westus', 'westeurope')
        """
        self.subscription_key = subscription_key
        self.region = region
        
        # Configure speech service
        self.speech_config = speechsdk.SpeechConfig(
            subscription=subscription_key,
            region=region
        )
        
        # Set language (can be made configurable)
        self.speech_config.speech_recognition_language = "en-US"
        
        logger.info(f"Initialized Azure Pronunciation Extractor (region: {region})")
    
    def extract_phonemes(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        reference_text: str
    ) -> Dict[str, Any]:
        """
        Extract phonemes and pronunciation scores using Azure
        
        Args:
            audio_data: Audio as numpy array
            sample_rate: Sample rate (should be 16000)
            reference_text: Expected sentence/text
        
        Returns:
            Dict with phonemes, accuracy scores, and detailed results
        """
        try:
            # Convert numpy array to WAV bytes
            audio_bytes = self._numpy_to_wav_bytes(audio_data, sample_rate)
            
            # Create pronunciation assessment config
            pronunciation_config = speechsdk.PronunciationAssessmentConfig(
                reference_text=reference_text,
                grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
                granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme,
                enable_miscue=True  # Detect insertions/omissions
            )
            
            # Create audio stream
            stream = speechsdk.audio.PushAudioInputStream()
            stream.write(audio_bytes)
            stream.close()
            
            audio_config = speechsdk.audio.AudioConfig(stream=stream)
            
            # Create speech recognizer
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config,
                audio_config=audio_config
            )
            
            # Apply pronunciation assessment config
            pronunciation_config.apply_to(speech_recognizer)
            
            # Perform recognition
            result = speech_recognizer.recognize_once()
            
            # Check result
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                return self._parse_azure_result(result)
            elif result.reason == speechsdk.ResultReason.NoMatch:
                logger.warning("Azure: No speech recognized")
                raise Exception("No speech could be recognized")
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation = result.cancellation_details
                logger.error(f"Azure recognition canceled: {cancellation.reason}")
                raise Exception(f"Recognition canceled: {cancellation.error_details}")
            else:
                raise Exception(f"Unexpected result reason: {result.reason}")
                
        except Exception as e:
            logger.error(f"Azure pronunciation extraction failed: {str(e)}")
            raise
    
    def _numpy_to_wav_bytes(
        self,
        audio_data: np.ndarray,
        sample_rate: int
    ) -> bytes:
        """
        Convert numpy array to WAV bytes for Azure
        
        Args:
            audio_data: Audio as numpy array (float32, -1.0 to 1.0)
            sample_rate: Sample rate
        
        Returns:
            WAV file bytes
        """
        # Ensure audio is in correct format
        if audio_data.dtype != np.int16:
            # Convert float32 [-1.0, 1.0] to int16 [-32768, 32767]
            audio_data = (audio_data * 32767).astype(np.int16)
        
        # Create audio segment
        audio_segment = AudioSegment(
            audio_data.tobytes(),
            frame_rate=sample_rate,
            sample_width=2,  # 16-bit
            channels=1  # Mono
        )
        
        # Export to WAV bytes
        buffer = io.BytesIO()
        audio_segment.export(buffer, format="wav")
        return buffer.getvalue()
    
    def _parse_azure_result(self, result) -> Dict[str, Any]:
        """
        Parse Azure pronunciation result into our standard format
        
        Args:
            result: Azure SpeechRecognitionResult
        
        Returns:
            Dict with phonemes and scores in our format
        """
        # Parse JSON result
        result_json = json.loads(result.json)
        
        if 'NBest' not in result_json or len(result_json['NBest']) == 0:
            raise Exception("No recognition results from Azure")
        
        best_result = result_json['NBest'][0]
        pronunciation = best_result.get('PronunciationAssessment', {})
        words_data = best_result.get('Words', [])
        
        # Extract phonemes by word (our standard format)
        phonemes_by_word = []
        words_details = []
        
        for word_item in words_data:
            # Extract phonemes for this word
            word_phonemes = []
            phonemes_with_scores = []
            
            for phoneme_item in word_item.get('Phonemes', []):
                phoneme = phoneme_item['Phoneme']
                accuracy = phoneme_item['PronunciationAssessment'].get('AccuracyScore', 0.0)
                
                word_phonemes.append(phoneme)
                phonemes_with_scores.append({
                    'phoneme': phoneme,
                    'accuracy_score': accuracy
                })
            
            phonemes_by_word.append(word_phonemes)
            
            # Store word-level details
            word_assessment = word_item.get('PronunciationAssessment', {})
            words_details.append({
                'word': word_item['Word'],
                'accuracy_score': word_assessment.get('AccuracyScore', 0.0),
                'error_type': word_assessment.get('ErrorType', 'None'),
                'phonemes': phonemes_with_scores
            })
        
        # Return in format compatible with our system
        return {
            # Standard phoneme output (compatible with current system)
            'phonemes': phonemes_by_word,
            
            # Azure-specific scores (additional data)
            'azure_scores': {
                'accuracy_score': pronunciation.get('AccuracyScore', 0.0),
                'fluency_score': pronunciation.get('FluencyScore', 0.0),
                'completeness_score': pronunciation.get('CompletenessScore', 0.0),
                'pronunciation_score': pronunciation.get('PronScore', 0.0)
            },
            
            # Word-level details
            'words': words_details,
            
            # Recognized text (for validation)
            'recognized_text': result.text,
            
            # Backend identifier
            'backend': 'azure'
        }
    
    def extract_phonemes_batch(
        self,
        audio_files: List[str],
        reference_texts: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Process multiple audio files (for testing/batch processing)
        
        Args:
            audio_files: List of audio file paths
            reference_texts: List of reference texts
        
        Returns:
            List of results
        """
        results = []
        for audio_file, reference_text in zip(audio_files, reference_texts):
            # Load audio file
            import librosa
            audio_data, sr = librosa.load(audio_file, sr=16000, mono=True)
            
            # Extract phonemes
            result = self.extract_phonemes(audio_data, sr, reference_text)
            results.append(result)
        
        return results


# Helper function for testing
def test_azure_extraction():
    """Test Azure pronunciation extraction"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Get credentials
    key = os.getenv("AZURE_SPEECH_KEY")
    region = os.getenv("AZURE_SPEECH_REGION", "eastus")
    
    if not key:
        print("ERROR: AZURE_SPEECH_KEY not set in environment")
        return
    
    # Initialize extractor
    extractor = AzurePronunciationExtractor(key, region)
    
    # Test with sample audio
    test_audio_file = "backend/tests/extraction/sample_audio/the_cat.wav"
    reference_text = "The cat sat on the mat"
    
    if os.path.exists(test_audio_file):
        import librosa
        audio_data, sr = librosa.load(test_audio_file, sr=16000, mono=True)
        
        result = extractor.extract_phonemes(audio_data, sr, reference_text)
        
        print("✅ Azure Extraction Success!")
        print(f"Phonemes: {result['phonemes']}")
        print(f"Accuracy: {result['azure_scores']['accuracy_score']:.1f}")
        print(f"Pronunciation Score: {result['azure_scores']['pronunciation_score']:.1f}")
    else:
        print(f"Test audio file not found: {test_audio_file}")


if __name__ == "__main__":
    test_azure_extraction()
```

---

### File 2: Update PhonemeAssistant

Modify: `backend/core/phoneme_assistant.py`

Add Azure backend support:

```python
# At the top of the file, add:
from core.phoneme_extractor_azure import AzurePronunciationExtractor

# In __init__ method, update backend selection:
def __init__(self):
    # ... existing code ...
    
    # Determine backend
    self.backend_type = os.getenv("PHONEME_BACKEND", "auto")
    
    if self.backend_type == "azure":
        # Use Azure
        azure_key = os.getenv("AZURE_SPEECH_KEY")
        azure_region = os.getenv("AZURE_SPEECH_REGION", "eastus")
        
        if not azure_key:
            logger.warning("Azure backend requested but AZURE_SPEECH_KEY not set, falling back to ONNX")
            self.phoneme_extractor = PhonemeExtractorONNX()
            self.backend_type = "onnx"
        else:
            logger.info(f"Using Azure Pronunciation Assessment (region: {azure_region})")
            self.phoneme_extractor = AzurePronunciationExtractor(azure_key, azure_region)
    
    elif self.backend_type == "auto":
        # Auto-select based on availability
        if os.getenv("USE_ONNX_BACKEND", "true").lower() == "true":
            self.phoneme_extractor = PhonemeExtractorONNX()
            self.backend_type = "onnx"
        else:
            self.phoneme_extractor = PhonemeExtractorPyTorch()
            self.backend_type = "pytorch"
    
    elif self.backend_type == "onnx":
        self.phoneme_extractor = PhonemeExtractorONNX()
    
    else:  # pytorch
        self.phoneme_extractor = PhonemeExtractorPyTorch()
    
    logger.info(f"Phoneme backend: {self.backend_type}")

# In process_audio_array method, handle Azure backend:
def process_audio_array(
    self,
    audio_array: np.ndarray,
    sample_rate: int,
    attempted_sentence: str = None,
    client_phonemes: List[List[str]] = None,
    **kwargs
) -> Dict[str, Any]:
    """Process audio with backend-aware logic"""
    
    # ... existing validation code ...
    
    # If Azure backend and reference text available, use Azure
    if self.backend_type == "azure" and attempted_sentence:
        try:
            logger.info("Using Azure Pronunciation Assessment")
            result = self.phoneme_extractor.extract_phonemes(
                audio_array,
                sample_rate,
                attempted_sentence
            )
            
            # Extract phonemes from Azure result
            phonemes = result['phonemes']
            
            # Continue with rest of pipeline (word extraction, alignment, etc.)
            # using the phonemes from Azure
            
            # Add Azure scores to response
            response = {
                'phonemes': phonemes,
                'azure_scores': result.get('azure_scores'),
                'backend': 'azure'
            }
            
            # Continue with word extraction, alignment, PER calculation
            # ... rest of existing code ...
            
            return response
            
        except Exception as e:
            logger.error(f"Azure extraction failed: {str(e)}")
            # Fallback to ONNX/PyTorch if enabled
            if os.getenv("ENABLE_AZURE_FALLBACK", "false").lower() == "true":
                logger.info("Falling back to ONNX/PyTorch")
                self.phoneme_extractor = PhonemeExtractorONNX()
                self.backend_type = "onnx"
                # Continue with fallback (existing code path)
            else:
                raise
    
    # Otherwise use existing logic (ONNX/PyTorch/client phonemes)
    # ... existing code ...
```

---

### File 3: Environment Configuration

Update: `backend/.env.example`

```bash
# Phoneme Extraction Backend
# Options: auto, onnx, pytorch, azure
PHONEME_BACKEND=auto

# Azure Speech Services (optional)
# Get credentials from: https://portal.azure.com
AZURE_SPEECH_KEY=your_subscription_key_here
AZURE_SPEECH_REGION=eastus
ENABLE_AZURE_FALLBACK=true

# Existing ONNX configuration
USE_ONNX_BACKEND=true
```

---

### File 4: Requirements

Update: `backend/requirements.txt`

```txt
# Add Azure Speech SDK
azure-cognitiveservices-speech==1.34.0

# Existing dependencies
# ... rest of file ...
```

---

## Testing

### Test 1: Basic Functionality

```bash
cd backend
python -m core.phoneme_extractor_azure
```

Expected output:
```
✅ Azure Extraction Success!
Phonemes: [['ð', 'ə'], ['k', 'æ', 't'], ...]
Accuracy: 95.0
Pronunciation Score: 92.0
```

### Test 2: Integration Test

```python
# backend/tests/test_azure_integration.py

import os
from dotenv import load_dotenv
from core.phoneme_assistant import PhonemeAssistant
import librosa

load_dotenv()

def test_azure_integration():
    """Test Azure integration with PhonemeAssistant"""
    
    # Set backend to Azure
    os.environ["PHONEME_BACKEND"] = "azure"
    
    # Initialize assistant
    assistant = PhonemeAssistant()
    
    # Load test audio
    audio_file = "tests/extraction/sample_audio/the_cat.wav"
    audio_data, sr = librosa.load(audio_file, sr=16000, mono=True)
    
    # Process
    result = assistant.process_audio_array(
        audio_data,
        sr,
        attempted_sentence="The cat sat on the mat"
    )
    
    print("✅ Integration test passed!")
    print(f"Backend: {result.get('backend')}")
    print(f"Phonemes: {result.get('phonemes')}")
    if 'azure_scores' in result:
        print(f"Azure scores: {result['azure_scores']}")

if __name__ == "__main__":
    test_azure_integration()
```

### Test 3: Compare Backends

```python
# backend/tests/compare_backends.py

import os
from core.phoneme_assistant import PhonemeAssistant
import librosa
import time

def compare_backends():
    """Compare ONNX vs Azure performance"""
    
    test_audio = "tests/extraction/sample_audio/the_cat.wav"
    reference_text = "The cat sat on the mat"
    
    audio_data, sr = librosa.load(test_audio, sr=16000, mono=True)
    
    results = {}
    
    # Test ONNX
    os.environ["PHONEME_BACKEND"] = "onnx"
    assistant_onnx = PhonemeAssistant()
    
    start = time.time()
    result_onnx = assistant_onnx.process_audio_array(audio_data, sr, reference_text)
    time_onnx = time.time() - start
    
    results['onnx'] = {
        'latency': time_onnx,
        'phonemes': result_onnx['phonemes']
    }
    
    # Test Azure
    os.environ["PHONEME_BACKEND"] = "azure"
    assistant_azure = PhonemeAssistant()
    
    start = time.time()
    result_azure = assistant_azure.process_audio_array(audio_data, sr, reference_text)
    time_azure = time.time() - start
    
    results['azure'] = {
        'latency': time_azure,
        'phonemes': result_azure['phonemes'],
        'scores': result_azure.get('azure_scores')
    }
    
    # Print comparison
    print("\n" + "="*50)
    print("BACKEND COMPARISON")
    print("="*50)
    
    print(f"\n📊 ONNX:")
    print(f"  Latency: {time_onnx*1000:.1f}ms")
    print(f"  Phonemes: {results['onnx']['phonemes']}")
    
    print(f"\n📊 Azure:")
    print(f"  Latency: {time_azure*1000:.1f}ms")
    print(f"  Phonemes: {results['azure']['phonemes']}")
    if results['azure']['scores']:
        print(f"  Accuracy: {results['azure']['scores']['accuracy_score']:.1f}")
        print(f"  Pronunciation: {results['azure']['scores']['pronunciation_score']:.1f}")
    
    print(f"\n⚡ Latency Difference: {abs(time_onnx - time_azure)*1000:.1f}ms")
    print("="*50 + "\n")

if __name__ == "__main__":
    compare_backends()
```

---

## Usage Examples

### Example 1: Use Azure for Premium Users

```python
def get_phoneme_backend(user):
    """Select backend based on user tier"""
    if user.subscription_tier == "premium":
        return "azure"  # Better accuracy for paying users
    else:
        return "onnx"  # Cost-effective for free users
```

### Example 2: Fallback Strategy

```python
def extract_with_fallback(audio, sample_rate, reference_text):
    """Try Azure, fallback to ONNX if fails"""
    try:
        # Try Azure first
        extractor = AzurePronunciationExtractor(key, region)
        return extractor.extract_phonemes(audio, sample_rate, reference_text)
    except Exception as e:
        logger.warning(f"Azure failed: {e}, falling back to ONNX")
        extractor = PhonemeExtractorONNX()
        return extractor.extract_phonemes(audio, sample_rate)
```

### Example 3: A/B Testing

```python
import random

def select_backend_ab_test(user_id):
    """A/B test: 10% users get Azure"""
    # Consistent per user
    if hash(user_id) % 100 < 10:
        return "azure"
    return "onnx"
```

---

## Monitoring

### Metrics to Track

```python
# Add to monitoring/telemetry
metrics = {
    'backend': 'azure' or 'onnx',
    'latency_ms': processing_time * 1000,
    'accuracy_score': azure_result.get('accuracy_score'),
    'pronunciation_score': azure_result.get('pronunciation_score'),
    'error': None or error_message,
    'fallback_used': True/False
}
```

### Dashboard Queries

```sql
-- Average latency by backend
SELECT 
    backend,
    AVG(latency_ms) as avg_latency,
    P50(latency_ms) as p50_latency,
    P95(latency_ms) as p95_latency
FROM phoneme_extraction_metrics
GROUP BY backend;

-- Azure accuracy distribution
SELECT 
    FLOOR(accuracy_score / 10) * 10 as accuracy_bucket,
    COUNT(*) as count
FROM phoneme_extraction_metrics
WHERE backend = 'azure'
GROUP BY accuracy_bucket;

-- Cost estimation
SELECT 
    COUNT(*) as requests,
    SUM(duration_seconds) / 3600 as hours,
    SUM(duration_seconds) / 3600 * 1.30 as estimated_cost_usd
FROM phoneme_extraction_metrics
WHERE backend = 'azure'
    AND date >= CURRENT_DATE - INTERVAL '1 month';
```

---

## Cost Optimization Tips

### 1. Use Free Tier for Development
```bash
# Development environment
PHONEME_BACKEND=azure
AZURE_SPEECH_KEY=dev_key  # Free tier key
```

### 2. Route by Volume
```python
if monthly_usage < FREE_TIER_HOURS:
    backend = "azure"  # Use free tier
else:
    backend = "onnx"  # Switch to self-hosted
```

### 3. Batch Processing
```python
# Process multiple audio files in batch to reduce overhead
results = extractor.extract_phonemes_batch(audio_files, reference_texts)
```

### 4. Cache Results
```python
# Cache phoneme results to avoid re-processing
cache_key = f"phonemes_{audio_hash}_{reference_text_hash}"
if cache_key in redis:
    return redis.get(cache_key)
```

---

## Troubleshooting

### Error: "Invalid subscription key"
```bash
# Check environment variable is set
echo $AZURE_SPEECH_KEY

# Test with Azure portal credentials
# Visit: https://portal.azure.com -> Speech Services -> Keys and Endpoint
```

### Error: "Recognition canceled"
```python
# Add detailed error logging
if result.reason == speechsdk.ResultReason.Canceled:
    cancellation = result.cancellation_details
    print(f"Error code: {cancellation.error_code}")
    print(f"Error details: {cancellation.error_details}")
```

### High Latency
```python
# Check region selection (use closest region)
AZURE_SPEECH_REGION=eastus  # US East
AZURE_SPEECH_REGION=westus2 # US West
AZURE_SPEECH_REGION=westeurope  # Europe

# Enable connection pooling
speech_config.set_property(
    speechsdk.PropertyId.SpeechServiceConnection_InitialSilenceTimeoutMs,
    "5000"
)
```

---

## Next Steps

1. ✅ Install dependencies: `pip install azure-cognitiveservices-speech`
2. ✅ Set up Azure account and get credentials
3. ✅ Copy code files from this guide
4. ✅ Test with sample audio
5. ⚠️ A/B test with real users
6. ⚠️ Monitor costs and performance
7. ⚠️ Optimize based on metrics

---

## References

- [Azure Pronunciation Assessment Docs](https://docs.microsoft.com/azure/cognitive-services/speech-service/how-to-pronunciation-assessment)
- [Azure Speech SDK Python](https://docs.microsoft.com/python/api/azure-cognitiveservices-speech/)
- [Azure Pricing Calculator](https://azure.microsoft.com/pricing/calculator/)
- [Free Tier Details](https://azure.microsoft.com/free/cognitive-services/)
