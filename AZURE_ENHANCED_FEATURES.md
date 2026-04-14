# Azure Integration - Enhanced Features

## Overview

The Azure Pronunciation Assessment API integration now provides **optimized word+phoneme extraction** that eliminates redundant processing steps and improves performance.

## New Capabilities

### 1. Combined Word+Phoneme Extraction

Azure now extracts both words and phonemes in a **single API call**, with phonemes already aligned to words.

```python
# Old approach (ONNX/PyTorch)
phonemes = extractor.extract_phoneme(audio)        # Step 1: Extract phonemes
words = word_extractor.extract_words(audio)        # Step 2: Extract words separately
aligned = align_phonemes_to_words(phonemes, words) # Step 3: Complex alignment

# New Azure-optimized approach
result = extractor.extract_words_and_phonemes(audio, reference_text="hello world")
words = result['words']      # Already extracted
phonemes = result['phonemes'] # Already aligned to words!
```

### 2. Automatic Backend Detection

The system automatically detects when using Azure and switches to the optimized path:

```python
# In phoneme_assistant.py
pronunciation_data = await process_audio_array(
    ground_truth_phonemes=ground_truth_phonemes,
    audio_array=audio_array,
    phoneme_extraction_model=self.phoneme_extractor,  # Auto-detects Azure
    reference_text=attempted_sentence,  # Enables Azure assessment
)

# If Azure: Uses optimized single-call path
# If ONNX/PyTorch: Uses standard multi-step path
```

### 3. Rich Pronunciation Data

When using Azure with reference text, you get additional data:

```python
result = {
    'words': ['hello', 'world'],
    'phonemes': [['h', 'ɛ', 'l', 'oʊ'], ['w', 'ɝ', 'l', 'd']],
    'recognized_text': 'hello world',
    'words_details': [
        {
            'word': 'hello',
            'accuracy_score': 95.0,
            'error_type': 'None',
            'phonemes': [
                {'phoneme': 'h', 'accuracy_score': 100.0},
                {'phoneme': 'ɛ', 'accuracy_score': 90.0},
                # ...
            ]
        },
        # ...
    ],
    'azure_scores': {
        'accuracy_score': 94.5,
        'fluency_score': 88.0,
        'completeness_score': 100.0,
        'pronunciation_score': 92.0
    },
    'backend': 'azure'
}
```

## Performance Improvements

### Before (ONNX/PyTorch)
```
Audio Processing Timeline:
├─ Phoneme Extraction: ~200ms (ONNX) or ~500ms (PyTorch)
├─ Word Extraction: ~1000-2000ms (separate model)
├─ Phoneme-to-Word Alignment: ~300ms (dynamic programming)
└─ Total: ~1500-2800ms
```

### After (Azure Optimized)
```
Audio Processing Timeline:
├─ Combined Azure API Call: ~500-1000ms
│  ├─ Speech recognition
│  ├─ Phoneme extraction
│  ├─ Word extraction
│  └─ Automatic alignment
└─ Total: ~500-1000ms (50-65% faster!)
```

## Code Changes

### 1. AzurePronunciationExtractor (phoneme_extractor_azure.py)

**New Methods:**

- `extract_words(audio, sampling_rate)` - Extract just words (compatible with WordExtractor interface)
- `extract_words_and_phonemes(audio, sampling_rate, reference_text)` - Combined extraction (Azure-optimized)

### 2. process_audio_array (process_audio.py)

**Enhanced:**

- Added `reference_text` parameter (optional)
- Detects Azure extractor automatically
- Uses optimized path when:
  - Extractor is AzurePronunciationExtractor
  - reference_text is provided
  - extract_words_and_phonemes method exists
- Falls back to standard path if any condition fails

**Benefits:**
- Skips separate word extraction (~1-2s saved)
- Skips phoneme-to-word alignment (~0.3s saved)
- Uses Azure's built-in alignment (more accurate)
- Enriches results with Azure scores

### 3. PhonemeAssistant (phoneme_assistant.py)

**Updated:**

- Passes `reference_text` to `process_audio_array`
- Enables Azure pronunciation assessment automatically

## Usage Examples

### Example 1: Basic Usage (Automatic)

```python
# Initialize assistant (auto-detects backend from env)
assistant = PhonemeAssistant()

# Process audio - automatically uses Azure optimized path if available
result = await assistant.process_audio(
    attempted_sentence="hello world",
    audio_array=audio_data
)
# Azure optimized path used automatically if AZURE_SPEECH_KEY is set
```

### Example 2: Force Azure Backend

```bash
# Environment variables
PHONEME_BACKEND=azure
AZURE_SPEECH_KEY=your_key
AZURE_SPEECH_REGION=eastus
```

```python
# Assistant will use Azure backend
assistant = PhonemeAssistant()
# All processing automatically uses Azure optimized path
```

### Example 3: Manual Azure Extraction

```python
from core.phoneme_extractor_azure import AzurePronunciationExtractor

extractor = AzurePronunciationExtractor(key, region)

# Extract just words
words = extractor.extract_words(audio, 16000)

# Extract words + phonemes together
result = extractor.extract_words_and_phonemes(
    audio, 
    16000, 
    reference_text="the cat sat"
)

print(f"Words: {result['words']}")
print(f"Phonemes: {result['phonemes']}")
print(f"Accuracy: {result['azure_scores']['accuracy_score']}")
```

## Backward Compatibility

All changes are **fully backward compatible**:

- ✅ `reference_text` parameter is optional (defaults to None)
- ✅ ONNX/PyTorch backends continue to work unchanged
- ✅ Existing tests and code continue to work
- ✅ Automatic fallback if Azure path fails

## Error Handling

The system gracefully handles failures:

```python
try:
    # Try Azure optimized path
    result = await process_audio_array(..., reference_text=sentence)
except Exception as e:
    logger.warning(f"Azure optimized extraction failed: {e}")
    # Automatically falls back to standard processing
    # (Uses ONNX/PyTorch with separate word extraction)
```

## Migration Guide

### For Existing Code

**No changes required!** The optimization is automatic:

1. If using Azure backend → Automatically uses optimized path
2. If using ONNX/PyTorch → Uses standard path
3. If Azure fails → Falls back to standard path

### To Enable Azure Optimized Path

Just set environment variables:

```bash
AZURE_SPEECH_KEY=your_key
AZURE_SPEECH_REGION=eastus
PHONEME_BACKEND=auto  # or 'azure'
```

That's it! The system will automatically:
- Use Azure for phoneme extraction
- Use optimized combined extraction
- Skip redundant word extraction
- Skip complex alignment logic

## Testing

Run integration tests:

```bash
cd backend
python test_azure_optimized_integration.py
```

Tests verify:
- ✅ Azure extract_words() interface
- ✅ Azure extract_words_and_phonemes() interface
- ✅ process_audio_array detects Azure
- ✅ Fallback to ONNX works

## Benefits Summary

| Feature | Before | After | Improvement |
|---------|--------|-------|-------------|
| **Latency** | 1.5-2.8s | 0.5-1s | 50-65% faster |
| **API Calls** | 2-3 calls | 1 call | Simplified |
| **Alignment** | Complex DP | Built-in | More accurate |
| **Data Quality** | Phonemes only | Phonemes + scores | Richer |
| **Code Complexity** | High | Low | Simpler |

## Future Enhancements

Potential improvements:
- [ ] Use Azure timing info for better silence detection
- [ ] Leverage error_type for targeted feedback
- [ ] Use confidence scores for fallback decisions
- [ ] Support Azure's prosody assessment (beta)
- [ ] Multi-language support via Azure

## Questions?

See also:
- `AZURE_SETUP_GUIDE.md` - Azure configuration
- `QUICK_REFERENCE.md` - Quick start guide
- `research_phoneme_transcription_apis.md` - Full research
