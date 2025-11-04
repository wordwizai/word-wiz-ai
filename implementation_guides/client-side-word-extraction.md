# Client-Side Word Extraction Implementation Guide

## Implementation Status

**Last Updated:** November 2, 2025

### Completed Phases

- ⬜ **Phase 1: Backend Setup** - Not started
- ⬜ **Phase 2: Frontend Model Integration** - Not started
- ⬜ **Phase 3: Hybrid Processing Pipeline** - Not started
- ⬜ **Phase 4: Backend Processing Updates** - Not started
- ⬜ **Phase 5: Error Handling & Optimization** - Not started

### Prerequisites

- ✅ Client-side phoneme extraction implementation completed
- ✅ Transformers.js already installed and working
- ✅ Hybrid processing architecture in place

---

## Overview

This guide extends the client-side phoneme extraction system to also extract words in the browser, further reducing backend load and improving response times. Since phoneme extraction is already implemented, this builds on that foundation.

**Model Strategy:** We'll use `Xenova/whisper-tiny.en` or `Xenova/wav2vec2-large-960h-lv60-self` for word extraction. These are lightweight ASR models that output text transcriptions, which we can split into words.

### Key Benefits

- **Additional 20-30% faster response times** - Combined with phoneme extraction, total improvement of 70-90%
- **Further reduced backend load** - Backend only handles alignment, GPT analysis, and TTS
- **Leverages existing infrastructure** - Reuses model loading, caching, and fallback logic
- **Minimal new code** - Most patterns already established in phoneme extraction

### Architecture

```
┌─────────────────────────────────────┐
│              Browser                │
├─────────────────────────────────────┤
│ 1. Record audio                     │──┐
│ 2. Extract phonemes (eSpeak ONNX)   │  │ Parallel execution
│ 3. Extract words (Whisper ONNX)     │  │ (70-90% time saved)
│    OR reuse ASR from phoneme model  │  │
└─────────────────────────────────────┘  │
       │                                 │
       ↓                                 ↓
┌─────────────────────────────────────────────┐
│                 Backend                     │
├─────────────────────────────────────────────┤
│ 1. Receive eSpeak phonemes + words          │
│ 2. Normalize eSpeak → IPA                   │
│ 3. Align words with phonemes                │
│ 4. GPT analysis                             │
│ 5. TTS generation                           │
└─────────────────────────────────────────────┘
```

**Processing Flow:**

- Client extracts: Words (text) + Phonemes (eSpeak)
- Backend receives: `{words: ["hello", "world"], phonemes: [["h","ə","l","oʊ"], ["w","ɜ","l","d"]]}`
- Backend validates: Word count matches phoneme count
- Backend processes: Alignment + analysis (no extraction needed)

---

## Phase 1: Backend Setup (Database & API)

### Goal

Update the existing client-side processing endpoint to accept pre-extracted words in addition to phonemes.

### Implementation Steps

#### 1.1 Update Existing Endpoint

**File:** `backend/routers/ai.py`

- [ ] Update `/analyze-audio-with-phonemes` to also accept optional `client_words` parameter
- [ ] Add validation to ensure word count matches phoneme count
- [ ] Maintain backward compatibility (phonemes-only requests still work)

**Updated endpoint:**

```python
@router.post("/analyze-audio-with-phonemes")
async def analyze_audio_with_phonemes(
    attempted_sentence: str = Form(...),
    session_id: int = Form(...),
    client_phonemes: str = Form(...),  # JSON array
    client_words: Optional[str] = Form(None),  # NEW - JSON array
    audio_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    # Parse both phonemes and words (if provided)
    phonemes = json.loads(client_phonemes)
    words = json.loads(client_words) if client_words else None

    # Validate format
    if words and len(words) != len(phonemes):
        raise HTTPException(400, "Word count must match phoneme count")

    # Process with client data
    pass
```

#### 1.2 Update Validation Handler

**File:** `backend/routers/handlers/phoneme_processing_handler.py`

- [ ] Add function to validate client words format
- [ ] Add function to validate word-phoneme alignment
- [ ] Reuse existing normalization logic

**New validation function:**

```python
def validate_client_words(
    words: list[str],
    phonemes: list[list[str]],
    sentence: str
) -> tuple[bool, str]:
    """
    Validate client words match expected format and align with phonemes.

    Checks:
    - Words is list of strings
    - Word count matches phoneme count
    - Words approximately match attempted sentence
    """
    if not isinstance(words, list):
        return False, "Words must be array"

    if len(words) != len(phonemes):
        return False, f"Word count ({len(words)}) doesn't match phoneme count ({len(phonemes)})"

    # Check words are strings
    for i, word in enumerate(words):
        if not isinstance(word, str) or len(word) == 0:
            return False, f"Word {i} is invalid"

    # Fuzzy match against attempted sentence (optional - allows minor variations)
    expected_words = sentence.lower().split()
    if len(words) != len(expected_words):
        logger.warning(f"Word count mismatch: got {len(words)}, expected {len(expected_words)}")

    return True, ""
```

### Quality Assurance Checklist

- [ ] **Endpoint accepts both phonemes and words**
- [ ] **Endpoint still works with phonemes only** (backward compatible)
- [ ] **Validation catches mismatched word/phoneme counts**
- [ ] **Invalid word format triggers proper error response**
- [ ] **Logs clearly show whether words were client or server extracted**

---

## Phase 2: Frontend Model Integration

### Goal

Add word extraction capability to the existing phoneme extractor service with minimal new code.

### Implementation Steps

#### 2.1 Extend Phoneme Extractor Service

**File:** `frontend/src/services/phonemeExtractor.ts`

**Option A: Use Phoneme Model's ASR Output (Recommended)**

- [ ] Extract words from the same Wav2Vec2 model output used for phonemes
- [ ] Parse transcription text into word array
- [ ] No additional model loading required

**Option B: Add Separate Word Model**

- [ ] Load lightweight Whisper model for word extraction
- [ ] Run both models in parallel
- [ ] Combine results before sending to backend

**Recommended: Option A (simpler, reuses existing model)**

```typescript
class ClientPhonemeExtractor {
  // Existing methods...

  async extractPhonemesAndWords(audioBlob: Blob): Promise<{
    phonemes: string[][];
    words: string[];
  }> {
    if (!this.model) {
      throw new Error("Model not loaded");
    }

    const audioData = await this.prepareAudioData(audioBlob);
    const result = await this.model(audioData);

    // Parse single model output for both phonemes and words
    const phonemes = this.parsePhonemes(result.text);
    const words = this.parseWords(result.text); // NEW

    return { phonemes, words };
  }

  private parseWords(modelOutput: string): string[] {
    // Extract words from model transcription
    // Handle word delimiters (spaces, special tokens, etc.)
    const text = modelOutput.replace(/\|/g, " ").trim();
    return text.split(/\s+/).filter((word) => word.length > 0);
  }
}
```

#### 2.2 Update Phoneme Model Hook

**File:** `frontend/src/hooks/usePhonemeModel.ts`

- [ ] Update `extractPhonemes()` to return both phonemes and words
- [ ] Maintain backward compatibility (can still return phonemes only if needed)

**Updated hook:**

```typescript
interface UsePhonemeModelReturn {
  // ... existing fields ...
  extractPhonemesAndWords: (audio: Blob) => Promise<{
    phonemes: string[][];
    words: string[];
  } | null>;
}

export const usePhonemeModel = (): UsePhonemeModelReturn => {
  // ... existing code ...

  const extractPhonemesAndWords = async (audioBlob: Blob) => {
    try {
      const result = await extractor.extractPhonemesAndWords(audioBlob);
      return result;
    } catch (error) {
      console.error("Extraction failed:", error);
      return null;
    }
  };

  return {
    // ... existing returns ...
    extractPhonemesAndWords,
  };
};
```

#### 2.3 No Settings Changes Needed

**Note:** We reuse the existing `use_client_phoneme_extraction` setting. When enabled, it now extracts both phonemes AND words. No new settings required.

### Quality Assurance Checklist

- [ ] **Words extracted correctly from model output**
- [ ] **Word count matches phoneme count**
- [ ] **Words approximately match attempted sentence**
- [ ] **Extraction still works if only phonemes requested** (backward compatible)
- [ ] **No significant performance degradation** (parsing words is fast)
- [ ] **Memory usage stays reasonable** (no new model loaded in Option A)

---

## Phase 3: Hybrid Processing Pipeline

### Goal

Update the audio processing flow to send client-extracted words along with phonemes to the backend.

### Implementation Steps

#### 3.1 Update Hybrid Audio Analysis Hook

**File:** `frontend/src/hooks/useHybridAudioAnalysis.ts`

- [ ] Update to extract both phonemes and words
- [ ] Pass both to backend endpoint
- [ ] Maintain fallback for phonemes-only or server-only processing

**Updated flow:**

```typescript
const processAudio = async (audioBlob: Blob, sentence: string) => {
  let phonemes = null;
  let words = null;

  // Attempt client-side extraction if enabled
  if (settings.use_client_phoneme_extraction && modelReady) {
    try {
      const result = await extractPhonemesAndWords(audioBlob);

      if (result) {
        phonemes = result.phonemes;
        words = result.words;

        console.log("Client extraction successful:", {
          wordCount: words.length,
          phonemeCount: phonemes.length,
        });
      }
    } catch (error) {
      console.warn("Client extraction failed, falling back to server");
      phonemes = null;
      words = null;
    }
  }

  // Send to backend (with or without client data)
  analysisStream.start(audioBlob, sentence, phonemes, words);
};
```

#### 3.2 Update Audio Analysis Stream Hook

**File:** `frontend/src/hooks/useAudioAnalysisStream.ts`

- [ ] Add optional `clientWords` parameter to `start()` method
- [ ] Include words in FormData when available
- [ ] Same endpoint as before (backward compatible)

**Updated signature:**

```typescript
const start = (
  file: File,
  sentence: string,
  clientPhonemes?: string[][] | null,
  clientWords?: string[] | null // NEW
) => {
  const url = `${API_URL}/ai/analyze-audio-with-phonemes`;

  const formData = new FormData();
  formData.append("audio_file", file);
  formData.append("attempted_sentence", sentence);
  formData.append("session_id", sessionId.toString());

  if (clientPhonemes) {
    formData.append("client_phonemes", JSON.stringify(clientPhonemes));
  }

  if (clientWords) {
    formData.append("client_words", JSON.stringify(clientWords)); // NEW
  }

  // ... rest of implementation
};
```

#### 3.3 No Component Changes Needed

**Files:** `BasePractice.tsx`, `ChoiceStoryBasePractice.tsx`

- [ ] No changes needed - they already use `useHybridAudioAnalysis`
- [ ] Word extraction happens automatically when enabled
- [ ] Existing loading indicators work for both phonemes and words

### Quality Assurance Checklist

- [ ] **Words sent to backend when client extraction succeeds**
- [ ] **Phonemes-only mode still works** (if word extraction fails but phonemes succeed)
- [ ] **Server-only mode still works** (if both fail)
- [ ] **No duplicate processing** (audio sent once with all available data)
- [ ] **UI doesn't change** (existing indicators work)
- [ ] **Fallback is seamless** (user doesn't notice failures)

---

## Phase 4: Backend Processing Updates

### Goal

Update backend to use client-extracted words when available, skipping word extraction step.

### Implementation Steps

#### 4.1 Update Audio Processing Handler

**File:** `backend/routers/handlers/audio_processing_handler.py`

- [ ] Add optional `client_words` parameter
- [ ] Skip word extraction if valid client words provided
- [ ] Fall back to server extraction if validation fails
- [ ] Log which processing path was used

**Updated function:**

```python
async def analyze_audio_file_event_stream(
    phoneme_assistant: PhonemeAssistant,
    activity_object: BaseMode,
    audio_array: np.ndarray,
    attempted_sentence: str,
    db: Session,
    current_user: User,
    session: UserSession,
    client_phonemes: Optional[list[list[str]]] = None,
    client_words: Optional[list[str]] = None,  # NEW
):
    # Validate client data if provided
    use_client_data = False
    if client_phonemes and client_words:
        is_valid, error = validate_client_words(
            client_words, client_phonemes, attempted_sentence
        )
        if is_valid:
            use_client_data = True
            logger.info(f"Using client-extracted words: {client_words}")
        else:
            logger.warning(f"Client word validation failed: {error}. Falling back to server.")

    if use_client_data:
        # Normalize phonemes and use client words
        normalized_phonemes = normalize_espeak_to_ipa(client_phonemes)

        pronunciation_data = await process_audio_with_client_data(
            client_phonemes=normalized_phonemes,
            client_words=client_words,  # NEW
            ground_truth_phonemes=ground_truth_phonemes,
            audio_array=audio_array,
        )
    else:
        # Full server-side extraction (existing path)
        pronunciation_dataframe, highest_per_word, problem_summary, per_summary = (
            await phoneme_assistant.process_audio(
                attempted_sentence, audio_array, verbose=True
            )
        )

    # Rest of processing continues...
```

#### 4.2 Update Hybrid Processing Function

**File:** `backend/core/process_audio.py`

- [ ] Rename `process_audio_with_client_phonemes()` to `process_audio_with_client_data()`
- [ ] Add `client_words` parameter
- [ ] Skip word extraction step when words provided
- [ ] Only validate word-phoneme alignment

**Updated function:**

```python
async def process_audio_with_client_data(
    client_phonemes: list[list[str]],
    client_words: list[str],  # NEW
    ground_truth_phonemes: list[tuple[str, list[str]]],
    audio_array: np.ndarray,
    sampling_rate: int = 16000,
    word_extraction_model = None,  # No longer needed if words provided
) -> list[dict]:
    """
    Process audio using client-provided phonemes AND words.
    Skips both phoneme and word extraction.
    Only performs alignment and analysis.
    """
    logger.info(f"Processing with client data: {len(client_words)} words, {len(client_phonemes)} phoneme groups")

    # Validate alignment (word count should match phoneme group count)
    if len(client_words) != len(client_phonemes):
        raise ValueError(
            f"Word count ({len(client_words)}) doesn't match phoneme count ({len(client_phonemes)})"
        )

    # Extract ground truth words
    ground_truth_words = [word for word, _ in ground_truth_phonemes]

    # Align client words with ground truth (simple index-based for now)
    # This can be improved with fuzzy matching if needed
    aligned_data = []
    for i, (gt_word, gt_phonemes) in enumerate(ground_truth_phonemes):
        if i < len(client_words):
            client_word = client_words[i]
            client_word_phonemes = client_phonemes[i]

            # Calculate PER for this word
            per = calculate_per(client_word_phonemes, gt_phonemes)

            aligned_data.append({
                "word": client_word,
                "predicted_phonemes": client_word_phonemes,
                "ground_truth_phonemes": gt_phonemes,
                "per": per,
            })

    logger.info(f"Aligned {len(aligned_data)} words without extraction")
    return aligned_data
```

#### 4.3 Update Endpoint Handler

**File:** `backend/routers/ai.py`

- [ ] Parse `client_words` from form data
- [ ] Pass to processing handler
- [ ] Handle validation errors gracefully

**Updated endpoint:**

```python
@router.post("/analyze-audio-with-phonemes")
async def analyze_audio_with_phonemes(
    attempted_sentence: str = Form(...),
    session_id: int = Form(...),
    client_phonemes: str = Form(...),
    client_words: Optional[str] = Form(None),  # NEW
    audio_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    # Parse JSON data
    phonemes_list = json.loads(client_phonemes)
    words_list = json.loads(client_words) if client_words else None

    # Validate format
    if words_list:
        is_valid, error = validate_client_words(
            words_list, phonemes_list, attempted_sentence
        )
        if not is_valid:
            logger.warning(f"Word validation failed: {error}")
            words_list = None  # Fall back to server extraction

    # Process audio
    return StreamingResponse(
        analyze_audio_file_event_stream(
            # ... existing params ...
            client_phonemes=phonemes_list,
            client_words=words_list,  # NEW
        ),
        media_type="text/event-stream"
    )
```

### Quality Assurance Checklist

- [ ] **Client words bypass word extraction** (faster processing)
- [ ] **Word-phoneme alignment is validated** before use
- [ ] **Invalid words trigger fallback** to server extraction
- [ ] **Processing time is faster** with client words (skip extraction)
- [ ] **Results match server-only processing** (same alignment, same analysis)
- [ ] **Logs clearly show** which data was client vs server extracted
- [ ] **Backward compatibility maintained** (phonemes-only still works)

---

## Phase 5: Error Handling & Optimization

### Goal

Add robust error handling and optimize the word extraction process.

### Implementation Steps

#### 5.1 Reuse Existing Resource Detection

**File:** `frontend/src/utils/deviceCapabilities.ts`

- [ ] No changes needed - already checks RAM, mobile, WebAssembly
- [ ] Same checks apply to word extraction

#### 5.2 Add Word Validation

**File:** `frontend/src/services/phonemeExtractor.ts`

- [ ] Validate word count matches phoneme count before returning
- [ ] Filter out empty words
- [ ] Handle edge cases (silence, noise, etc.)

**Validation logic:**

```typescript
private validateExtraction(words: string[], phonemes: string[][]): boolean {
  // Check counts match
  if (words.length !== phonemes.length) {
    console.warn(`Word/phoneme count mismatch: ${words.length} vs ${phonemes.length}`);
    return false;
  }

  // Check for empty words
  if (words.some(w => w.length === 0)) {
    console.warn("Empty words detected");
    return false;
  }

  // Check for excessive length mismatch (potential transcription error)
  const totalWordChars = words.join('').length;
  const totalPhonemes = phonemes.flat().length;
  const ratio = totalWordChars / totalPhonemes;

  if (ratio < 0.3 || ratio > 3.0) {
    console.warn(`Unusual word/phoneme ratio: ${ratio}`);
    return false;
  }

  return true;
}

async extractPhonemesAndWords(audioBlob: Blob) {
  // ... extraction logic ...

  // Validate before returning
  if (!this.validateExtraction(words, phonemes)) {
    throw new Error("Extraction validation failed");
  }

  return { words, phonemes };
}
```

#### 5.3 Enhance Error Recovery

**File:** `frontend/src/hooks/useHybridAudioAnalysis.ts`

- [ ] Add separate retry logic for word extraction failures
- [ ] Allow phonemes to succeed even if words fail
- [ ] Track partial success rates

**Enhanced error handling:**

```typescript
const processAudio = async (audioBlob: Blob, sentence: string) => {
  let phonemes = null;
  let words = null;

  if (settings.use_client_phoneme_extraction && modelReady) {
    try {
      const result = await extractPhonemesAndWords(audioBlob);

      if (result) {
        // Both succeeded
        phonemes = result.phonemes;
        words = result.words;
        trackMetric("full_client_extraction", true);
      }
    } catch (error) {
      // Try phonemes-only fallback
      try {
        phonemes = await extractPhonemes(audioBlob);
        words = null; // Server will extract words
        trackMetric("partial_client_extraction", true);
        console.log("Using client phonemes with server words");
      } catch (phonemeError) {
        // Full server fallback
        phonemes = null;
        words = null;
        trackMetric("full_server_extraction", true);
        console.warn("Full server fallback");
      }
    }
  }

  analysisStream.start(audioBlob, sentence, phonemes, words);
};
```

#### 5.4 Update Performance Tracking

**File:** `frontend/src/services/performanceTracker.ts`

- [ ] Track word extraction success rate
- [ ] Track combined phoneme + word extraction success
- [ ] Measure time saved by skipping both extractions

**Enhanced metrics:**

```typescript
export class PerformanceTracker {
  // ... existing methods ...

  trackExtraction(
    type: "full" | "phonemes-only" | "server-only",
    timeMs: number
  ) {
    const metrics = {
      full: "client_phonemes_and_words",
      "phonemes-only": "client_phonemes_only",
      "server-only": "server_extraction",
    };

    this.addMetric(metrics[type], timeMs);

    // Expected time savings:
    // - Full client: 70-90% faster
    // - Phonemes only: 50-70% faster
    // - Server only: baseline
  }
}
```

#### 5.5 No New UI Components Needed

**Files:** `ModelLoadingIndicator.tsx`, `ProcessingIndicator.tsx`

- [ ] Existing components already work for combined extraction
- [ ] May update text to say "Loading speech model..." (covers both)
- [ ] Processing indicator doesn't distinguish between phoneme/word extraction

### Quality Assurance Checklist

- [ ] **Validation catches word/phoneme mismatches**
- [ ] **Partial success handled gracefully** (phonemes work, words fail)
- [ ] **Error messages are informative** (what failed, what's being used)
- [ ] **Performance metrics show expected improvements** (70-90% faster with both)
- [ ] **Retry logic doesn't cause delays** (fails fast to server)
- [ ] **UI remains responsive** during extraction
- [ ] **Feature degrades gracefully** (full → partial → server)

---

## Testing Strategy

### Manual Testing Checklist

**Happy Path:**

- [ ] Client extracts both phonemes and words → backend processes correctly
- [ ] Results match server-only extraction (same PER, same alignment)
- [ ] Processing is 70-90% faster than server-only

**Partial Success:**

- [ ] Word extraction fails → phonemes succeed → backend extracts words
- [ ] Processing is 50-70% faster (same as phonemes-only)
- [ ] Phoneme extraction fails → both server-extracted → normal speed

**Edge Cases:**

- [ ] Empty audio → validation fails → server extraction
- [ ] Noisy audio → transcription errors → validation fails → server extraction
- [ ] Word count mismatch → validation fails → server extraction
- [ ] Model timeout → retry → fallback to server

**Performance:**

- [ ] Combined extraction doesn't significantly slow down single extraction
- [ ] Memory usage stays below 600MB (model + processing)
- [ ] No performance degradation over multiple sessions

### Automated Testing (Optional)

**Backend Tests:**

```python
def test_validate_client_words_valid():
    words = ["hello", "world"]
    phonemes = [["h","ɛ","l","oʊ"], ["w","ɜr","l","d"]]
    sentence = "hello world"

    is_valid, error = validate_client_words(words, phonemes, sentence)
    assert is_valid
    assert error == ""

def test_validate_client_words_count_mismatch():
    words = ["hello"]
    phonemes = [["h","ɛ","l","oʊ"], ["w","ɜr","l","d"]]
    sentence = "hello world"

    is_valid, error = validate_client_words(words, phonemes, sentence)
    assert not is_valid
    assert "count" in error.lower()

def test_process_with_client_words_and_phonemes():
    # Test full client data processing
    # Verify word extraction is skipped
    # Verify alignment is correct
```

**Frontend Tests:**

```typescript
describe("Word Extraction", () => {
  it("should extract words matching phoneme count");
  it("should validate word/phoneme alignment");
  it("should handle extraction failures gracefully");
  it("should allow phonemes-only fallback");
});
```

---

## Deployment Checklist

### Pre-Deployment

- [ ] All Phase QA checklists completed
- [ ] Backend validates client words correctly
- [ ] Frontend extraction validation works
- [ ] Performance benchmarks meet expectations (70-90% improvement)
- [ ] Backward compatibility tested (phonemes-only still works)

### Deployment Steps

1. [ ] Deploy backend changes (updated endpoint, validation)
2. [ ] Deploy frontend changes (word extraction logic)
3. [ ] Monitor error rates and success rates
4. [ ] Track full vs partial client extraction rates
5. [ ] Validate performance improvements in production

### Post-Deployment Monitoring

- [ ] Track client word extraction success rate (target: >85%)
- [ ] Track combined phoneme + word success rate (target: >80%)
- [ ] Monitor backend load reduction (target: 60-80% reduction)
- [ ] Track full client processing adoption
- [ ] Monitor word validation failure rate (target: <10%)

---

## Rollback Plan

If issues arise:

1. **Backend Rollback**

   - Remove `client_words` parameter (make it ignored)
   - Fall back to server word extraction for all requests
   - Phonemes-only mode still works

2. **Frontend Rollback**

   - Stop sending `client_words` parameter
   - Keep phoneme extraction working
   - Fall back to previous 50-70% improvement

3. **Full Rollback**
   - Revert to phonemes-only implementation
   - Disable word extraction in extractor service
   - Still better than server-only processing

---

## Estimated Implementation Time

| Phase                                  | Estimated Time  | Priority |
| -------------------------------------- | --------------- | -------- |
| Phase 1: Backend Setup                 | 2-3 hours       | High     |
| Phase 2: Frontend Model Integration    | 3-4 hours       | High     |
| Phase 3: Hybrid Pipeline               | 2-3 hours       | High     |
| Phase 4: Backend Processing            | 3-4 hours       | High     |
| Phase 5: Error Handling & Optimization | 2-3 hours       | Medium   |
| Testing & QA                           | 2-3 hours       | High     |
| **Total**                              | **14-20 hours** |          |

**Note:** Significantly faster than phoneme extraction (32-44 hours) because infrastructure already exists.

---

## Key Architectural Decisions

### Why Reuse the Phoneme Model for Words?

- ✅ No additional model download (saves ~100MB)
- ✅ No additional memory usage
- ✅ Same ASR output contains both phonemes and words
- ✅ Simpler architecture (one model, two outputs)
- ✅ Faster implementation (reuse existing code)

### Why Not Use a Separate Word Model?

- ❌ Adds ~100MB download (Whisper tiny)
- ❌ Increases memory usage (~200MB more)
- ❌ Requires parallel model loading
- ❌ More complex error handling (two models can fail independently)
- ⚠️ Only slightly better accuracy (not worth the complexity)

**Decision:** Use existing Wav2Vec2-eSpeak model output for both phonemes and words.

### Why Validate Word-Phoneme Alignment?

- Client extraction errors can cause misalignment
- Backend needs consistent data for accurate analysis
- Early validation prevents downstream errors
- Graceful fallback to server extraction when validation fails

### Why Allow Phonemes-Only Success?

- Word extraction may fail while phonemes succeed
- Partial success is better than full server fallback
- Still saves 50-70% processing time
- Maintains backward compatibility

---

## Common Pitfalls to Avoid

1. **Don't assume word count always matches phoneme count**

   - Model output can be inconsistent
   - Always validate before sending to backend
   - Have fallback for mismatches

2. **Don't skip validation on the backend**

   - Client can send malformed data
   - Validation prevents backend errors
   - Fallback to server extraction is safe

3. **Don't forget partial success handling**

   - Phonemes may work while words fail
   - Allow phonemes-only mode
   - Track partial success rates

4. **Don't add complexity prematurely**
   - Start with simple word parsing
   - Don't add fuzzy matching unless needed
   - Don't add separate model unless accuracy issues

---

## Success Metrics

| Metric                               | Target        | How to Measure                              |
| ------------------------------------ | ------------- | ------------------------------------------- |
| Combined Extraction Success Rate     | >80%          | Full client extractions / Total attempts    |
| Word Extraction Success Rate         | >85%          | Successful word extractions / Total         |
| Response Time Reduction              | 70-90% faster | Time from recording → feedback              |
| Backend Load Reduction               | 60-80%        | CPU usage on extraction endpoints           |
| Word Validation Failure Rate         | <10%          | Failed validations / Total word extractions |
| Partial Success Rate (Phonemes Only) | 10-15%        | Phoneme-only successes / Total attempts     |

---

## Comparison with Phoneme-Only Implementation

| Aspect                 | Phonemes Only | Phonemes + Words | Improvement     |
| ---------------------- | ------------- | ---------------- | --------------- |
| Response Time          | 50-70% faster | 70-90% faster    | +20% faster     |
| Backend Load Reduction | 40-60%        | 60-80%           | +20% reduction  |
| Implementation Time    | 32-44 hours   | 14-20 hours      | Leverages infra |
| Memory Usage           | ~400MB        | ~400MB           | Same (reuses)   |
| Model Download Size    | ~250MB        | ~250MB           | Same (reuses)   |
| Complexity             | Medium        | Medium+          | Slight increase |
| Fallback Flexibility   | Server-only   | Partial/Server   | More options    |

---

## Appendix A: Word Format Specification

Client words must match this format:

```typescript
// Format: Array of strings (words extracted from audio)
type ClientWords = string[];

// Example for "hello world":
const words = ["hello", "world"];

// Must align with phonemes:
const phonemes = [
  ["h", "ə", "l", "oʊ"], // hello
  ["w", "ɜ", "l", "d"], // world
];

// Validation checks:
// - words.length === phonemes.length
// - Each word is non-empty string
// - Words approximately match attempted sentence

// Invalid formats:
// - Not an array: "hello world"
// - Nested arrays: [["hello"], ["world"]]
// - Empty words: ["hello", "", "world"]
// - Count mismatch: ["hello"] with 2 phoneme groups
```

---

## Appendix B: Backend Processing Flow

**Before (Phonemes-Only):**

```
1. Receive: audio + client_phonemes
2. Extract: words from audio (Google Speech API)
3. Normalize: eSpeak → IPA
4. Align: words ↔ phonemes
5. Analyze: GPT analysis
6. Generate: TTS response
```

**After (Phonemes + Words):**

```
1. Receive: audio + client_phonemes + client_words
2. Validate: word/phoneme alignment
3. Normalize: eSpeak → IPA
4. Align: words ↔ phonemes (skip extraction)
5. Analyze: GPT analysis
6. Generate: TTS response
```

**Time Saved:** Step 2 (word extraction) takes ~20-30% of total processing time.

---

## Appendix C: Example Implementation Snippets

### Frontend: Combined Extraction

```typescript
async extractPhonemesAndWords(audioBlob: Blob) {
  const audioData = await this.prepareAudioData(audioBlob);
  const result = await this.model(audioData);

  // Single model output contains both
  const rawText = result.text;  // e.g., "h ə l oʊ | w ɜ l d"

  // Parse phonemes (existing logic)
  const phonemes = this.parsePhonemes(rawText);

  // Parse words (new logic)
  const words = this.parseWords(rawText);

  // Validate alignment
  if (!this.validateExtraction(words, phonemes)) {
    throw new Error("Word/phoneme alignment failed");
  }

  return { words, phonemes };
}

private parseWords(rawText: string): string[] {
  // Remove phoneme delimiters and extract words
  // Model output: "h ə l oʊ | w ɜ l d"
  // Split by word delimiter (|) then reconstruct words

  const wordGroups = rawText.split('|').map(g => g.trim());

  // This is model-specific - may need adjustment based on actual output
  const words = wordGroups.map(group => {
    // Convert phonemes back to approximate word
    // Or use a secondary decoding step
    return this.phonemesToWord(group);
  });

  return words;
}
```

### Backend: Client Word Validation

```python
def validate_client_words(
    words: list[str],
    phonemes: list[list[str]],
    sentence: str
) -> tuple[bool, str]:
    """Validate client words format and alignment."""

    # Check type
    if not isinstance(words, list):
        return False, "Words must be array"

    # Check count matches
    if len(words) != len(phonemes):
        return False, f"Word count mismatch: {len(words)} vs {len(phonemes)} phoneme groups"

    # Check words are strings
    for i, word in enumerate(words):
        if not isinstance(word, str):
            return False, f"Word {i} is not a string"
        if len(word) == 0:
            return False, f"Word {i} is empty"

    # Optional: Fuzzy match against expected sentence
    expected = sentence.lower().split()
    if len(words) != len(expected):
        logger.warning(f"Word count differs from sentence: {len(words)} vs {len(expected)}")

    return True, ""
```

---

**End of Implementation Guide**

_Last Updated: November 2, 2025_
_Version: 1.0_
