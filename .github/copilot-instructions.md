# Word Wiz AI - Copilot Instructions

## Project Overview

Educational web app helping children learn to read through **phoneme-level pronunciation feedback**. FastAPI backend processes audio with wav2vec2-TIMIT-IPA models (IPA phoneme output), React frontend with optional client-side ML inference via Transformers.js.

## Architecture

```
Frontend (Vercel) ←→ FastAPI Backend (AWS EC2) ←→ External APIs (OpenAI, Google TTS)
     │                     │
     │              ┌──────┴──────────┐
     │              │  ONNX Runtime   │  ← 2-3x faster than PyTorch
     │              │  PhonemeExtractor│
     └──────────────│  wav2vec2-TIMIT │
  (optional client  │  IPA model      │
   Transformers.js) └─────────────────┘
```

### Audio Analysis Pipeline (8 Steps)

1. User reads sentence → Audio recorded in browser (MediaRecorder API)
2. Audio sent via WebSocket (primary) or SSE (fallback) to `/ai/ws/audio-analysis`
3. Backend validates & preprocesses audio (16kHz, mono, noise reduction)
4. **Phoneme extraction**: ONNX Runtime extracts IPA phonemes (or use client phonemes if provided)
5. **Word extraction**: Detect word boundaries via energy analysis
6. **Alignment**: Dynamic programming aligns phonemes to expected words
7. **PER calculation**: Compute Phoneme Error Rate per word & overall
8. **GPT feedback**: Mode-specific prompt → JSON response → TTS audio generation
9. Results streamed back: `processing_started` → `analysis` → `gpt_response` → `audio_feedback_file`

## Development Commands

```bash
# Backend (from /backend)
pip install -r requirements.txt
python main.py                     # Dev server on :8000
python -m tests.analysis.run_analysis_tests  # Run analysis tests

# Frontend (from /frontend)
npm install && npm run dev         # Dev server on :5173
npm run build                      # Production build
```

## Critical Patterns

### Backend Structure

- **Routers** (`routers/`): API endpoints - `ai.py` handles WebSocket/audio, `auth.py` for JWT
- **Core processing** (`core/`): `phoneme_assistant.py` orchestrates pipeline, delegates to extractors
- **Practice modes** (`core/modes/`): Inherit from `BaseMode`, implement `get_feedback_and_next_sentence()`
- **GPT prompts** (`core/gpt_prompts/`): Versioned `.txt` files, auto-appends `ssml_instruction.txt`

### Model Selection

```python
# Environment: USE_ONNX_BACKEND=true (default, 2-3x faster)
# Falls back to PyTorch if ONNX fails
self.phoneme_extractor = PhonemeExtractorONNX()  # core/phoneme_extractor_onnx.py
```

### Frontend Conventions

- **UI**: shadcn/ui + Radix primitives, Tailwind CSS with oklch colors (see `STYLE_GUIDELINES.md`)
- **State**: React Context (`AuthContext`, `SettingsContext`, `ThemeContext`)
- **API calls**: Centralized in `src/api.ts`, uses axios with `VITE_API_URL`
- **Audio transport**: `hooks/useAudioTransport.ts` abstracts WebSocket/SSE

### Practice Mode Pattern

````typescript
// Frontend routes to: /practice/{session_id}
// Component loads mode-specific implemprocessing layer:
- **extraction/** - Phoneme extraction only (audio → IPA phonemes)
- **analysis/** - Full pipeline (pre-extracted phonemes + sentence → PER analysis)
- **gpt/** - GPT prompt/response validation (ensures JSON output schema)
- **system/** - End-to-end with real audio files

Each test folder has a README with file format specs. Run tests:
```bash
cd backend
python -m tests.analysis.run_analysis_tests      # Analysis layer
python -m tests.extraction.run_extraction_tests  # Extraction layer
python -m tests.system.run_system_tests          # Full E2E
````

Test JSON format example (`tests/analysis/*.json`):

````json
{
  "sentence": "The cat sat.",
  "client_phonemes": [["ð", "ə"], ["k", "æ", "t"], ["s", "æ", "t"]],
  "Key Concepts

### Phonemes vs. Graphemes
- **Phoneme**: Actual sound unit, e.g., /æ/ in "cat" (IPA notation)
- **Grapheme**: Written letter(s), e.g., "a" in "cat"
- System analyzes **phonemes** for pronunciation accuracy, not spelling

### PER (Phoneme Error Rate)
- Levenshtein distance at phoneme level: `(substitutions + deletions + insertions) / total_phonemes`
- Lower PER = better pronunciation (0.0 = perfect, 1.0 = completely wrong)
- Computed per-word AND overall for granular feedback

### Hybrid Processing
- **Client extracts phonemes** (Transformers.js in browser) if device capable (4GB+ RAM, WebAssembly)
- **Server validates & completes analysis** (word extraction, alignment, GPT prompting)
- Reduces latency (no audio upload time) & server load, while maintaining quality control

### Sessions vs. Activities
- **Activity**: Template (e.g., "Unlimited Practice") with `activity_type` + `activity_settings`
- **Session**: User instance of an activity, tracks progress via `FeedbackEntry` records
- `activity_settings` JSON stores mode-specific config (e.g., `first_sentence`, `story_name`)

## Database
**MySQL (prod) / SQLite (dev)** with Alembic migrations:
```bash
alembic revision --autogenerate -m "add user_settings table"  # Generate
alembic upgrade head                                          # Apply
alembic downgrade -1                                          # Rollback
````

Schema: `users` → `sessions` (1:_) → `feedback_entries` (1:_), `activities` (1:1 with session)

## Configuration

- **Environment**: `USE_ONNX_BACKEND=true` (default), `OPENAI_API_KEY`, `DATABASE_URL`
- **Client ML**: Enabled per-user in `user_settings.use_client_phoneme_extraction`
- **GPT prompts**: Versioned `.txt` files in `core/gpt_prompts/`, auto-appends `ssml_instruction.txt`
- **TTS**: Google Cloud TTS (default), ElevenLabs (alternative), voices in `text_to_audio.py`

## Common Patterns

### Adding a New Practice Mode

1. Create `backend/core/modes/my_mode.py` inheriting `BaseMode`
2. Implement `get_feedback_and_next_sentence(attempted_sentence, analysis, phoneme_assistant, session)`
3. Create GPT prompt in `core/gpt_prompts/my_mode_prompt_v1.txt`
4. Load prompt: `self.prompt = phoneme_assistant.load_prompt("core/gpt_prompts/my_mode_prompt_v1.txt")`
5. Call GPT: `phoneme_assistant.query_gpt(conversation_history)` with mode context
6. Return JSON: `{"next_sentence": "...", "feedback": "...", "encouragement": "..."}`
7. Update `routers/ai.py` to route `activity_type` to new mode class
8. Add frontend component in `components/practice/` (or reuse `BasePractice.tsx`)

### WebSocket Message Types

**Client → Server**:

- `{"type": "analyze_audio", "audio_base64": "...", "attempted_sentence": "...", "session_id": 123, "client_phonemes": [[...]], "client_words": [...]}`

**Server → Client** (streamed sequentially):

- `{"type": "processing_started"}` → `{"type": "analysis", "data": {...}}` → `{"type": "gpt_response", "data": {...}}` → `{"type": "audio_feedback_file", "audio_base64": "..."}` → `{"type": "complete"}`
- `{"type": "error", "message": "..."}` on failure

## Troubleshooting

- **Model loading fails**: Check RAM (4GB+ required), verify HuggingFace Hub access, try `USE_ONNX_BACKEND=false`
- **WebSocket disconnects**: Check nginx config for WebSocket support (`proxy_buffering off`), verify CORS origins in `main.py`
- **High PER despite good pronunciation**: Validate ground truth phonemes with `grapheme_to_phoneme(sentence)`, check audio quality (16kHz, low noise)
- **GPT returns malformed JSON**: Check prompt includes output schema, use `extract_json()` to parse, log full response for debugging

## Glossary

- **IPA**: International Phonetic Alphabet (standard phoneme notation: /æ/, /ð/, /ʌ/)
- **PER**: Phoneme Error Rate (pronunciation accuracy metric, 0.0-1.0)
- **TTS**: Text-to-Speech (Google Cloud TTS generates audio from feedback text)
- **ONNX**: Open Neural Network Exchange (optimized model format, 2-3x faster inference)
- **SSE**: Server-Sent Events (unidirectional streaming, fallback for WebSocket)
- **Alembic**: Database migration tool for SQLAlchemy ORM

Run specific test: `python backend/tests/analysis/run_analysis_tests.py`

## Key Files

| Purpose           | Location                                                                               |
| ----------------- | -------------------------------------------------------------------------------------- |
| API client        | [frontend/src/api.ts](frontend/src/api.ts)                                             |
| Main pipeline     | [backend/core/phoneme_assistant.py](backend/core/phoneme_assistant.py)                 |
| WebSocket handler | [backend/routers/ai.py](backend/routers/ai.py)                                         |
| Audio processing  | [backend/core/process_audio.py](backend/core/process_audio.py)                         |
| Client ML         | [frontend/src/services/phonemeExtractor.ts](frontend/src/services/phonemeExtractor.ts) |
| DB models         | [backend/models/](backend/models/)                                                     |
| Pydantic schemas  | [backend/schemas/](backend/schemas/)                                                   |

## Project-Specific Notes

- **Phonemes use IPA format** - wav2vec2-TIMIT-IPA model outputs IPA symbols
- **PER = Phoneme Error Rate** - lower is better, computed per-word and overall
- **Client-side extraction optional** - check device capabilities before enabling
- **GPT outputs JSON** - must validate with `extract_json()` in PhonemeAssistant
- **TTS providers**: Google Cloud TTS (default), ElevenLabs (alternative)
- **Database**: MySQL (prod), SQLite (dev), migrations via Alembic
