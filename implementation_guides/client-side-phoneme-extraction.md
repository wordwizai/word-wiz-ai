# Client-Side Phoneme Extraction Implementation Guide

## Overview

This guide implements client-side phoneme extraction using the Wav2Vec2-TIMIT-IPA model in the browser, reducing backend load and improving response times. The implementation follows the 80/20 rule, focusing on the most impactful changes while maintaining code simplicity.

### Key Benefits

- **50-70% faster response times** - Phoneme extraction happens locally while audio uploads
- **Reduced backend load** - Backend only handles GPT analysis and TTS generation
- **Graceful degradation** - Automatic fallback to backend processing when needed
- **User control** - Settings option to disable client-side processing

### Architecture

```
┌─────────────┐
│   Browser   │
├─────────────┤
│ 1. Record   │──┐
│ 2. Extract  │  │ Parallel execution
│    Phonemes │  │ (50-70% time saved)
│    (Local)  │  │
└─────────────┘  │
       │         │
       ↓         ↓
┌─────────────────────┐
│      Backend        │
├─────────────────────┤
│ 1. Receive phonemes │
│ 2. Word alignment   │
│ 3. GPT analysis     │
│ 4. TTS generation   │
└─────────────────────┘
```

---

## Phase 1: Backend Setup (Database & API)

### Goal

Add database support for client-side processing preference and create new API endpoint that accepts pre-extracted phonemes.

### Implementation Steps

#### 1.1 Update User Settings Model

**File:** `backend/models/user_settings.py`

- [ ] Add `use_client_phoneme_extraction` boolean field (default: `True`)
- [ ] Add migration script for new database column

**Code changes:**

```python
class UserSettings(Base):
    # ... existing fields ...
    use_client_phoneme_extraction = Column(Boolean, default=True)
```

#### 1.2 Create Database Migration

**File:** `backend/alembic/versions/[timestamp]_add_client_phoneme_setting.py`

- [ ] Generate new Alembic migration
- [ ] Add upgrade/downgrade functions for new column

**Command:**

```bash
cd backend
alembic revision -m "add_client_phoneme_extraction_setting"
alembic upgrade head
```

#### 1.3 Update Settings Schema

**File:** `backend/schemas/user.py` (or wherever settings schema is defined)

- [ ] Add `use_client_phoneme_extraction: Optional[bool]` to settings schema
- [ ] Ensure field is included in API responses

#### 1.4 Create New AI Endpoint

**File:** `backend/routers/ai.py`

- [ ] Add new endpoint `/analyze-audio-with-phonemes` that accepts:
  - `audio_file` (for word extraction and validation)
  - `attempted_sentence` (ground truth text)
  - `session_id` (for session tracking)
  - `client_phonemes` (JSON array of extracted phonemes)
- [ ] Reuse existing processing logic but skip phoneme extraction step
- [ ] Add validation to ensure client phonemes match expected format

**New endpoint structure:**

```python
@router.post("/analyze-audio-with-phonemes")
async def analyze_audio_with_phonemes(
    attempted_sentence: str = Form(...),
    session_id: int = Form(...),
    client_phonemes: str = Form(...),  # JSON stringified array
    audio_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    # Parse client_phonemes from JSON
    # Validate format
    # Skip phoneme extraction
    # Continue with word extraction and analysis
    pass
```

### Quality Assurance Checklist

- [ ] **Database migration runs without errors** on fresh database
- [ ] **Settings API returns** new `use_client_phoneme_extraction` field
- [ ] **New endpoint validates** phoneme format correctly (reject invalid JSON)
- [ ] **Backend logs show** whether client or server phonemes were used
- [ ] **Endpoint handles errors gracefully** (invalid phonemes, missing audio, etc.)

---

## Phase 2: Frontend Model Integration

### Goal

Integrate Transformers.js to run Wav2Vec2-TIMIT-IPA model in the browser with automatic fallback and resource checking.

### Implementation Steps

#### 2.1 Install Dependencies

**File:** `frontend/package.json`

- [ ] Add `@xenova/transformers` (~latest version)
- [ ] Run `npm install`

**Command:**

```bash
cd frontend
npm install @xenova/transformers
```

#### 2.2 Create Phoneme Extractor Service

**File:** `frontend/src/services/phonemeExtractor.ts`

- [ ] Create class to manage model lifecycle
- [ ] Implement singleton pattern (one model instance)
- [ ] Add resource detection (RAM, CPU)
- [ ] Add model loading with progress callback
- [ ] Implement phoneme extraction from audio
- [ ] Add fallback logic for unsupported browsers

**Key features:**

```typescript
class ClientPhonemeExtractor {
  - checkBrowserSupport(): boolean
  - checkDeviceResources(): Promise<boolean>
  - loadModel(onProgress?: (progress: number) => void): Promise<void>
  - extractPhonemes(audioBlob: Blob): Promise<string[][]>
  - unloadModel(): void
}
```

#### 2.3 Create Model Loader Hook

**File:** `frontend/src/hooks/usePhonemeModel.ts`

- [ ] Create React hook to manage model state
- [ ] Track loading progress (0-100%)
- [ ] Track model ready state
- [ ] Expose methods: `loadModel()`, `extractPhonemes()`, `unloadModel()`
- [ ] Add error handling with fallback flag

**Hook interface:**

```typescript
interface UsePhonemeModelReturn {
  isSupported: boolean;
  isLoading: boolean;
  isReady: boolean;
  loadProgress: number;
  error: string | null;
  shouldFallbackToServer: boolean;
  loadModel: () => Promise<void>;
  extractPhonemes: (audio: Blob) => Promise<string[][] | null>;
  unloadModel: () => void;
}
```

#### 2.4 Add Settings Context Support

**File:** `frontend/src/contexts/SettingsContext.tsx`

- [ ] Add `use_client_phoneme_extraction` to settings state
- [ ] Update settings update function to handle new field
- [ ] Expose setting in context

#### 2.5 Update Settings Page UI

**File:** `frontend/src/pages/Settings.tsx`

- [ ] Add new tab or section for "Performance Settings"
- [ ] Add toggle switch for "Client-Side Processing"
- [ ] Add explanation text (benefits, storage requirements)
- [ ] Show model download size (~50-100MB)
- [ ] Add warning for slow devices

**UI Component:**

```tsx
<div className="flex items-center justify-between">
  <div>
    <Label htmlFor="clientProcessing">Client-Side Phoneme Processing</Label>
    <p className="text-sm text-muted-foreground">
      Process phonemes in your browser for faster results. Requires ~100MB
      download. Disable on slower devices.
    </p>
  </div>
  <Switch
    id="clientProcessing"
    checked={!!tempSettings.use_client_phoneme_extraction}
    onCheckedChange={(checked) =>
      handleChange("use_client_phoneme_extraction", checked)
    }
  />
</div>
```

### Quality Assurance Checklist

- [ ] **Model loads successfully** in Chrome, Firefox, Safari, Edge
- [ ] **Loading progress updates** smoothly from 0-100%
- [ ] **Model extraction produces valid phonemes** matching backend format
- [ ] **Settings toggle works** and persists across page refreshes
- [ ] **Browser support detection** correctly identifies unsupported browsers
- [ ] **Memory usage stays reasonable** (<500MB for model)
- [ ] **Model unloads properly** and frees memory when disabled
- [ ] **Error messages are user-friendly** ("Your browser doesn't support this feature")

---

## Phase 3: Hybrid Audio Processing Pipeline

### Goal

Update the audio recording and analysis flow to use client-side phonemes when available, with seamless fallback to backend processing.

### Implementation Steps

#### 3.1 Update Audio Analysis Hook

**File:** `frontend/src/hooks/useAudioAnalysisStream.ts`

- [ ] Add optional `clientPhonemes` parameter to `start()` method
- [ ] Update FormData to include phonemes when available
- [ ] Route to new endpoint when phonemes provided
- [ ] Add fallback logic: if client extraction fails, use original endpoint

**Updated signature:**

```typescript
const start = (
  file: File,
  sentence: string,
  clientPhonemes?: string[][] | null
) => {
  // Determine which endpoint to use
  const url = clientPhonemes
    ? `${API_URL}/ai/analyze-audio-with-phonemes`
    : `${API_URL}/ai/analyze-audio`;

  // Add phonemes to FormData if available
  if (clientPhonemes) {
    formData.append("client_phonemes", JSON.stringify(clientPhonemes));
  }
  // ... rest of implementation
};
```

#### 3.2 Create Orchestration Hook

**File:** `frontend/src/hooks/useHybridAudioAnalysis.ts`

- [ ] Combine `usePhonemeModel` + `useAudioAnalysisStream`
- [ ] Implement smart processing flow:
  1. Check if client extraction is enabled
  2. Check if model is ready
  3. If yes: extract phonemes locally, send to backend
  4. If no: send audio directly to backend
- [ ] Add performance metrics tracking (optional)

**Flow logic:**

```typescript
const processAudio = async (audioBlob: Blob, sentence: string) => {
  let phonemes = null;

  // Attempt client-side extraction if enabled
  if (settings.use_client_phoneme_extraction && modelReady) {
    try {
      phonemes = await extractPhonemes(audioBlob);
    } catch (error) {
      console.warn("Client extraction failed, falling back to server");
      phonemes = null;
    }
  }

  // Send to backend (with or without phonemes)
  analysisStream.start(audioBlob, sentence, phonemes);
};
```

#### 3.3 Update Practice Components

**Files:** `frontend/src/pages/Practice.tsx` (or similar activity components)

- [ ] Replace direct `useAudioAnalysisStream` with `useHybridAudioAnalysis`
- [ ] Add model initialization on component mount (if setting enabled)
- [ ] Show loading indicator while model loads
- [ ] Add "Processing locally..." vs "Processing on server..." status messages

**Component changes:**

```tsx
const Practice = () => {
  const { settings } = useSettings();
  const {
    processAudio,
    isModelReady,
    isModelLoading,
    loadModel,
    // ...
  } = useHybridAudioAnalysis();

  useEffect(() => {
    if (settings?.use_client_phoneme_extraction) {
      loadModel();
    }
  }, [settings]);

  // Show status indicator
  if (isModelLoading) {
    return <div>Loading AI model... {loadProgress}%</div>;
  }

  // Rest of component...
};
```

#### 3.4 Add Performance Monitoring (Optional)

**File:** `frontend/src/utils/performanceMonitor.ts`

- [ ] Track client vs server processing times
- [ ] Log to console in development
- [ ] Send anonymized metrics to analytics (optional)

### Quality Assurance Checklist

- [ ] **Audio processes correctly** when client extraction enabled
- [ ] **Audio processes correctly** when client extraction disabled
- [ ] **Fallback works seamlessly** if client extraction fails mid-session
- [ ] **No duplicate processing** (audio isn't sent twice)
- [ ] **UI shows appropriate status** ("Processing locally..." vs "Processing...")
- [ ] **Results are identical** between client and server processing
- [ ] **Settings changes take effect** without requiring page refresh
- [ ] **Model loads only once** per session (not on every recording)
- [ ] **Browser tab closing** properly cleans up model resources

---

## Phase 4: Backend Processing Updates

### Goal

Update backend audio processing to handle pre-extracted phonemes efficiently and maintain compatibility with existing flow.

### Implementation Steps

#### 4.1 Create Phoneme Processing Handler

**File:** `backend/routers/handlers/phoneme_processing_handler.py`

- [ ] Create function to validate client phoneme format
- [ ] Create function to merge client phonemes with server processing
- [ ] Add error handling for malformed phoneme data

**Validation function:**

```python
def validate_client_phonemes(
    phonemes: list[list[str]],
    expected_word_count: int
) -> bool:
    """
    Validate that client phonemes match expected format:
    - List of lists (words -> phonemes)
    - Each word has at least one phoneme
    - Phonemes are valid IPA characters
    """
    if not isinstance(phonemes, list):
        return False
    if len(phonemes) != expected_word_count:
        return False
    # ... additional validation
    return True
```

#### 4.2 Update Audio Processing Handler

**File:** `backend/routers/handlers/audio_processing_handler.py`

- [ ] Add optional `client_phonemes` parameter to `analyze_audio_file_event_stream`
- [ ] Skip phoneme extraction step if valid client phonemes provided
- [ ] Log whether client or server phonemes were used
- [ ] Maintain backward compatibility with existing flow

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
    client_phonemes: Optional[list[list[str]]] = None,  # NEW
):
    # If client phonemes provided and valid, skip extraction
    if client_phonemes:
        pronunciation_data = await process_audio_with_client_phonemes(
            client_phonemes=client_phonemes,
            ground_truth_phonemes=ground_truth_phonemes,
            audio_array=audio_array,
            word_extraction_model=phoneme_assistant.word_extractor,
        )
    else:
        # Existing server-side extraction
        pronunciation_dataframe, highest_per_word, problem_summary, per_summary = (
            await phoneme_assistant.process_audio(
                attempted_sentence, audio_array, verbose=True
            )
        )

    # Rest of processing continues as normal...
```

#### 4.3 Create Hybrid Processing Function

**File:** `backend/core/process_audio.py`

- [ ] Add new function `process_audio_with_client_phonemes()`
- [ ] Reuse existing alignment and analysis logic
- [ ] Only extract words from audio (skip phoneme extraction)
- [ ] Return same format as `process_audio_array()`

**New function signature:**

```python
async def process_audio_with_client_phonemes(
    client_phonemes: list[list[str]],
    ground_truth_phonemes: list[tuple[str, list[str]]],
    audio_array: np.ndarray,
    sampling_rate: int = 16000,
    word_extraction_model = None,
) -> list[dict]:
    """
    Process audio using client-provided phonemes instead of extracting them.
    Still extracts words for alignment validation.
    """
    # Extract words only (faster than full processing)
    predicted_words = word_extraction_model.extract_words(
        audio=audio_array,
        sampling_rate=sampling_rate
    )

    # Align client phonemes with ground truth
    # Use existing alignment logic
    # Return same format as process_audio_array
```

### Quality Assurance Checklist

- [ ] **Client phonemes are properly validated** before use
- [ ] **Invalid phonemes trigger fallback** to server extraction
- [ ] **Processing time is faster** with client phonemes (skip extraction step)
- [ ] **Results match server-only processing** (same PER, same alignment)
- [ ] **Error handling is robust** (malformed JSON, missing data, etc.)
- [ ] **Logs clearly indicate** which processing path was used
- [ ] **Backward compatibility maintained** (old clients still work)
- [ ] **Word extraction still occurs** for validation (catches recording issues)

---

## Phase 5: Error Handling & Optimization

### Goal

Add comprehensive error handling, resource management, and performance optimizations.

### Implementation Steps

#### 5.1 Add Resource Detection

**File:** `frontend/src/utils/deviceCapabilities.ts`

- [ ] Create function to estimate available RAM
- [ ] Create function to check if device is mobile
- [ ] Create function to test WebAssembly support
- [ ] Auto-disable on low-resource devices (<4GB RAM)

**Resource detection:**

```typescript
export const checkDeviceCapabilities = () => {
  const isMobile = /iPhone|iPad|Android/i.test(navigator.userAgent);
  const hasWasm = typeof WebAssembly !== "undefined";

  // Estimate RAM (not always accurate)
  const memory = (navigator as any).deviceMemory || 4;
  const hasEnoughRAM = memory >= 4;

  return {
    canRunModel: hasWasm && hasEnoughRAM,
    shouldRecommendDisabling: isMobile || !hasEnoughRAM,
    estimatedRAM: memory,
  };
};
```

#### 5.2 Add Model Caching

**File:** `frontend/src/services/phonemeExtractor.ts`

- [ ] Implement IndexedDB caching for model weights
- [ ] Check cache before downloading model
- [ ] Add cache versioning (invalidate on model updates)
- [ ] Add cache size management (clear old models)

#### 5.3 Add Network Quality Detection

**File:** `frontend/src/utils/networkQuality.ts`

- [ ] Use Network Information API to detect connection speed
- [ ] Disable client processing on slow connections (<1Mbps)
- [ ] Add retry logic for failed model downloads

**Network detection:**

```typescript
export const shouldUseClientProcessing = () => {
  const connection = (navigator as any).connection;
  if (!connection) return true;

  // Disable on slow connections
  const effectiveType = connection.effectiveType;
  return effectiveType !== "slow-2g" && effectiveType !== "2g";
};
```

#### 5.4 Add Error Recovery

**File:** `frontend/src/hooks/useHybridAudioAnalysis.ts`

- [ ] Implement retry logic (max 2 retries for client extraction)
- [ ] Add exponential backoff for model loading failures
- [ ] Clear error state when switching to server processing
- [ ] Show user-friendly error messages

**Error handling:**

```typescript
const extractWithRetry = async (audio: Blob, maxRetries = 2) => {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await extractPhonemes(audio);
    } catch (error) {
      if (i === maxRetries - 1) {
        console.warn("Client extraction failed, using server");
        return null;
      }
      await new Promise((resolve) => setTimeout(resolve, 1000 * (i + 1)));
    }
  }
  return null;
};
```

#### 5.5 Add Performance Metrics

**File:** `frontend/src/services/performanceTracker.ts`

- [ ] Track time saved by client processing
- [ ] Track success/failure rates
- [ ] Track average processing times
- [ ] Display metrics in developer tools (console)

#### 5.6 Add Loading States UI

**Files:** Practice components

- [ ] Show model download progress bar
- [ ] Show "Processing locally..." indicator during extraction
- [ ] Show fallback messages when switching to server
- [ ] Add settings banner suggesting to disable on slow devices

### Quality Assurance Checklist

- [ ] **Low-resource devices** automatically use server processing
- [ ] **Model caching works** (second load is instant)
- [ ] **Network errors are handled gracefully** (no app crashes)
- [ ] **Error messages are helpful** ("Model download failed, using server processing")
- [ ] **Retry logic doesn't cause infinite loops**
- [ ] **Performance metrics show expected improvements** (50-70% faster)
- [ ] **UI remains responsive** during model loading
- [ ] **Cache doesn't grow unbounded** (old models are cleared)
- [ ] **Feature degrades gracefully** on unsupported browsers

---

## Testing Strategy

### Manual Testing Checklist

**Happy Path:**

- [ ] New user enables client processing → model downloads → phonemes extract correctly
- [ ] User disables client processing → falls back to server → works correctly
- [ ] User switches mid-session → no errors, seamless transition

**Edge Cases:**

- [ ] Slow network → model download times out → fallback to server
- [ ] Low-resource device → client processing disabled automatically
- [ ] Browser doesn't support WebAssembly → fallback to server
- [ ] Model extraction fails → retry → fallback to server
- [ ] Invalid phonemes from client → backend validation catches → uses server extraction

**Performance:**

- [ ] Client processing is 50-70% faster than server-only
- [ ] Model loads in <10 seconds on typical connection
- [ ] Memory usage stays below 500MB with model loaded
- [ ] No memory leaks after multiple sessions

### Automated Testing (Optional)

**Backend Tests:**

```python
# test_phoneme_processing.py
def test_validate_client_phonemes_valid():
    # Test valid phoneme format

def test_validate_client_phonemes_invalid():
    # Test invalid phoneme formats

def test_process_with_client_phonemes():
    # Test processing with pre-extracted phonemes
```

**Frontend Tests:**

```typescript
// phonemeExtractor.test.ts
describe("ClientPhonemeExtractor", () => {
  it("should detect browser support correctly");
  it("should load model and extract phonemes");
  it("should handle extraction errors gracefully");
});
```

---

## Deployment Checklist

### Pre-Deployment

- [ ] All Phase QA checklists completed
- [ ] Database migration tested on staging
- [ ] Model files accessible via CDN or static hosting
- [ ] Settings default value set appropriately (`true` for good devices)
- [ ] Performance benchmarks meet expectations

### Deployment Steps

1. [ ] Run database migration on production
2. [ ] Deploy backend changes (API endpoints)
3. [ ] Deploy frontend changes (new UI, model integration)
4. [ ] Test on production with real users
5. [ ] Monitor error rates and performance metrics
6. [ ] Gradually roll out to 10% → 50% → 100% of users

### Post-Deployment Monitoring

- [ ] Monitor API endpoint usage (new vs old endpoint)
- [ ] Track client extraction success rate
- [ ] Monitor backend load reduction
- [ ] Track user settings adoption rate
- [ ] Monitor browser console for errors
- [ ] Collect user feedback on performance

---

## Rollback Plan

If issues arise after deployment:

1. **Quick Rollback (Settings Level)**

   - Change default `use_client_phoneme_extraction` to `false` in database
   - Users can manually re-enable in settings

2. **Full Rollback (Code Level)**

   - Remove new endpoint from routing
   - Frontend falls back to original `analyze-audio` endpoint
   - Database migration rollback (if needed)

3. **Partial Rollback (Feature Flag)**
   - Add backend feature flag to disable client phoneme acceptance
   - Keep frontend code but force server processing

---

## Future Enhancements (Out of Scope)

These are intentionally excluded from this implementation but can be added later:

- **Web Worker implementation** - Run model in background thread
- **Service Worker caching** - Offline model availability
- **Model quantization** - Smaller model size (~30MB instead of ~100MB)
- **Progressive model loading** - Load model in chunks during idle time
- **Client-side word extraction** - Further reduce backend load
- **A/B testing framework** - Measure real-world performance improvements
- **Analytics integration** - Track usage patterns and performance

---

## Estimated Implementation Time

| Phase                                  | Estimated Time  | Priority |
| -------------------------------------- | --------------- | -------- |
| Phase 1: Backend Setup                 | 4-6 hours       | High     |
| Phase 2: Frontend Model Integration    | 8-10 hours      | High     |
| Phase 3: Hybrid Pipeline               | 6-8 hours       | High     |
| Phase 4: Backend Processing            | 4-6 hours       | High     |
| Phase 5: Error Handling & Optimization | 6-8 hours       | Medium   |
| Testing & QA                           | 4-6 hours       | High     |
| **Total**                              | **32-44 hours** |          |

**Note:** Times assume familiarity with the codebase and technologies. Add 20-30% buffer for unexpected issues.

---

## Key Architectural Decisions

### Why Transformers.js?

- ✅ Official HuggingFace library for browser inference
- ✅ Supports Wav2Vec2 models out of the box
- ✅ Handles model conversion (PyTorch → ONNX → WASM)
- ✅ Active development and community support

### Why Not Send Phonemes from Backend Initially?

- Current architecture already optimized for server processing
- Client processing is opt-in for users with capable devices
- Maintains backward compatibility with existing clients

### Why Keep Word Extraction on Backend?

- Word extraction is less resource-intensive (10-15% of total time)
- Google Speech API provides better accuracy
- Simpler to implement (only one model in browser)
- Reduces initial scope (80/20 rule)

### Why IndexedDB for Caching?

- Larger storage quota than localStorage (100s of MB vs 5-10MB)
- Async API (doesn't block main thread)
- Persistent across sessions
- Better for binary data (model weights)

---

## Common Pitfalls to Avoid

1. **Don't load model on every recording**

   - Load once per session, reuse for multiple recordings
   - Implement singleton pattern for model instance

2. **Don't assume client extraction always works**

   - Always have fallback to server processing
   - Validate client phonemes on backend before using

3. **Don't ignore browser compatibility**

   - Test on Safari (different WebAssembly limits)
   - Test on mobile browsers (memory constraints)
   - Provide clear messaging for unsupported browsers

4. **Don't skip resource detection**

   - Low-end devices will struggle with model loading
   - Slow networks will timeout on model download
   - Auto-disable on problematic devices

5. **Don't forget to cleanup**
   - Unload model when component unmounts
   - Clear cache when model version changes
   - Free memory when switching to server mode

---

## Success Metrics

Track these metrics to measure implementation success:

| Metric                         | Target        | How to Measure                                  |
| ------------------------------ | ------------- | ----------------------------------------------- |
| Response Time Reduction        | 50-70% faster | Time from recording stop → feedback received    |
| Client Extraction Success Rate | >90%          | Client extractions / Total attempts             |
| Backend Load Reduction         | 40-60%        | CPU/memory usage on phoneme extraction endpoint |
| User Adoption Rate             | >70% enabled  | Users with `use_client_phoneme_extraction=true` |
| Error Rate                     | <5% fallbacks | Failed client extractions / Total attempts      |
| Model Load Time                | <10 seconds   | Time from load initiation → model ready         |

---

## Questions & Troubleshooting

### Q: What if the model is too large?

**A:** Consider model quantization (reduce size by 50-70%) or use a smaller base model variant. Current implementation assumes ~100MB model size.

### Q: What about mobile browsers?

**A:** Mobile browsers are supported but may be slower. Resource detection should auto-disable on low-memory devices. Users can manually disable in settings.

### Q: How do we handle model updates?

**A:** Implement cache versioning. When model version changes, invalidate old cache and download new model. Show one-time "Updating AI model..." message.

### Q: What if client phonemes don't match server phonemes?

**A:** This is expected due to different runtime environments. Backend validation ensures phonemes are in valid format but doesn't require exact match with server output.

### Q: Can we run this in a Web Worker?

**A:** Yes, but out of scope for initial implementation. Transformers.js supports Web Workers. Add in future enhancement phase.

---

## Appendix A: Phoneme Format Specification

Client phonemes must match this format to be accepted by backend:

```typescript
// Format: Array of words, each word is array of IPA phonemes
type ClientPhonemes = string[][];

// Example for "hello world":
const phonemes = [
  ["h", "ɛ", "l", "oʊ"], // "hello"
  ["w", "ɜr", "l", "d"], // "world"
];

// Invalid formats (will trigger fallback):
// - Not an array: "hello"
// - Flat array: ["h", "ɛ", "l", "oʊ"]
// - Wrong nesting: [[["h"]]]
// - Non-string phonemes: [["h", 1, "l"]]
```

Backend validation checks:

1. ✅ Top-level is array
2. ✅ Each word is array of strings
3. ✅ Number of words matches attempted sentence
4. ✅ Each phoneme is valid IPA character (lenient check)

---

## Appendix B: Settings Schema Update

**Before:**

```json
{
  "preferred_language": "en",
  "theme": "light",
  "tts_speed": 1.0,
  "audio_feedback_volume": 0.5,
  "notifications_enabled": true,
  "email_notifications": true
}
```

**After:**

```json
{
  "preferred_language": "en",
  "theme": "light",
  "tts_speed": 1.0,
  "audio_feedback_volume": 0.5,
  "notifications_enabled": true,
  "email_notifications": true,
  "use_client_phoneme_extraction": true // NEW
}
```

---

## Appendix C: Example Implementation Snippets

### Frontend: Simple Phoneme Extraction

```typescript
import { pipeline } from "@xenova/transformers";

class PhonemeExtractor {
  private model: any = null;

  async load() {
    this.model = await pipeline(
      "automatic-speech-recognition",
      "speech31/wav2vec2-large-TIMIT-IPA"
    );
  }

  async extract(audioBlob: Blob): Promise<string[][]> {
    const arrayBuffer = await audioBlob.arrayBuffer();
    const audioData = new Float32Array(arrayBuffer);

    const result = await this.model(audioData);

    // Parse result into word -> phonemes format
    return this.parsePhonemes(result.text);
  }

  private parsePhonemes(ipaText: string): string[][] {
    // Split by words and extract phonemes
    // Implementation depends on model output format
  }
}
```

### Backend: Client Phoneme Validation

```python
import re

def validate_client_phonemes(
    phonemes: list[list[str]],
    sentence: str
) -> tuple[bool, str]:
    """
    Validate client phonemes format.
    Returns (is_valid, error_message).
    """
    if not isinstance(phonemes, list):
        return False, "Phonemes must be array"

    expected_words = sentence.lower().split()
    if len(phonemes) != len(expected_words):
        return False, f"Expected {len(expected_words)} words, got {len(phonemes)}"

    for i, word_phonemes in enumerate(phonemes):
        if not isinstance(word_phonemes, list):
            return False, f"Word {i} phonemes must be array"

        if len(word_phonemes) == 0:
            return False, f"Word {i} has no phonemes"

        for phoneme in word_phonemes:
            if not isinstance(phoneme, str):
                return False, f"Phoneme must be string, got {type(phoneme)}"

    return True, ""
```

---

**End of Implementation Guide**

_Last Updated: November 2, 2025_
_Version: 1.0_
