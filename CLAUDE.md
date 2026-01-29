# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Word Wiz AI is an educational web app helping children learn to read through **phoneme-level pronunciation feedback**. It uses a FastAPI backend for audio processing with wav2vec2-TIMIT-IPA models (IPA phoneme output) and a React frontend with optional client-side ML inference via Transformers.js.

Main Website: [wordwizai.com](https://wordwizai.com)

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

**Tech Stack:**
- Frontend: React.js, Tailwind CSS v4, shadcn/ui + Radix primitives
- Backend: FastAPI (Python), ONNX Runtime for ML inference
- AI/NLP: OpenAI API (GPT), Wav2Vec2 for phoneme transcription
- Database: MySQL (prod) / SQLite (dev) with Alembic migrations
- TTS: Google Cloud TTS (default), ElevenLabs (alternative)

## Development Commands

### Backend (from `/backend`)
```bash
pip install -r requirements.txt
python main.py                                          # Dev server on :8000
python -m tests.analysis.run_analysis_tests             # Analysis tests
python -m tests.extraction.run_extraction_tests         # Extraction tests
python -m tests.system.run_system_tests                 # Full E2E tests
```

### Frontend (from `/frontend`)
```bash
npm install && npm run dev      # Dev server on :5173
npm run build                   # Production build
npm run build:prerender         # Build with prerendering
npm run lint                    # Run ESLint
npm run preview                 # Preview production build
```

### Database Migrations
```bash
cd backend
alembic revision --autogenerate -m "description"  # Generate migration
alembic upgrade head                              # Apply migrations
alembic downgrade -1                              # Rollback one migration
```

## Audio Analysis Pipeline (9 Steps)

1. User reads sentence → Audio recorded in browser (MediaRecorder API)
2. Audio sent via WebSocket (primary) or SSE (fallback) to `/ai/ws/audio-analysis`
3. Backend validates & preprocesses audio (16kHz, mono, noise reduction)
4. **Phoneme extraction**: ONNX Runtime extracts IPA phonemes (or use client phonemes if provided)
5. **Word extraction**: Detect word boundaries via energy analysis
6. **Alignment**: Dynamic programming aligns phonemes to expected words
7. **PER calculation**: Compute Phoneme Error Rate per word & overall
8. **GPT feedback**: Mode-specific prompt → JSON response → TTS audio generation
9. Results streamed back: `processing_started` → `analysis` → `gpt_response` → `audio_feedback_file` → `complete`

## Backend Architecture

### Core Structure
- **`routers/`**: API endpoints
  - `ai.py` - WebSocket/audio analysis handler
  - `auth.py` - JWT authentication
  - `activities.py` - Activity management
  - `session.py` - Session management
  - `google_auth.py` - Google OAuth integration

- **`core/`**: Main processing logic
  - `phoneme_assistant.py` - Orchestrates the entire pipeline
  - `phoneme_extractor_onnx.py` - ONNX-based phoneme extraction (2-3x faster)
  - `phoneme_extractor.py` - PyTorch fallback
  - `process_audio.py` - Audio preprocessing
  - `word_extractor.py` - Word boundary detection
  - `text_to_audio.py` - TTS generation (Google Cloud TTS, ElevenLabs)
  - `grapheme_to_phoneme.py` - Ground truth phoneme generation
  - `gpt_output_validator.py` - Validates GPT JSON responses

- **`core/modes/`**: Practice mode implementations (inherit from `BaseMode`)
  - `unlimited.py` - Unlimited practice mode
  - `story.py` - Story-based practice
  - `choice_story.py` - Interactive choice stories

- **`core/gpt_prompts/`**: Versioned `.txt` files for GPT prompts
  - Auto-appends `ssml_instruction.txt` for TTS formatting

- **`models/`**: SQLAlchemy database models
- **`schemas/`**: Pydantic request/response schemas

### Model Selection
```python
# Environment: USE_ONNX_BACKEND=true (default, 2-3x faster)
# Falls back to PyTorch if ONNX fails
self.phoneme_extractor = PhonemeExtractorONNX()
```

## Frontend Architecture

### Structure
- **`src/pages/`**: Page components (Dashboard, Practice, Settings, etc.)
- **`src/components/`**: Reusable UI components
  - `practice/` - Practice mode components
  - `ui/` - shadcn/ui components
- **`src/contexts/`**: React Context providers (AuthContext, SettingsContext, ThemeContext)
- **`src/hooks/`**: Custom React hooks
  - `useAudioTransport.ts` - Abstracts WebSocket/SSE audio transport
- **`src/services/`**: Service layers
  - `phonemeExtractor.ts` - Client-side ML inference via Transformers.js
- **`src/api.ts`**: Centralized API calls using axios

### Styling Conventions
- **UI Framework**: shadcn/ui + Radix primitives
- **CSS**: Tailwind CSS v4 with oklch color space
- **Color System**: CSS variables in `src/index.css` (see `STYLE_GUIDELINES.md`)
- **Theme Support**: Light/dark mode via ThemeContext
- **Patterns**: Gradient backgrounds, pastel colors, rounded corners (2xl/3xl), hover effects with scale/shadow

### WebSocket Message Types

**Client → Server:**
```json
{
  "type": "analyze_audio",
  "audio_base64": "...",
  "attempted_sentence": "...",
  "session_id": 123,
  "client_phonemes": [["ð", "ə"], ["k", "æ", "t"]],
  "client_words": [...]
}
```

**Server → Client (streamed):**
```json
{"type": "processing_started"}
{"type": "analysis", "data": {...}}
{"type": "gpt_response", "data": {...}}
{"type": "audio_feedback_file", "audio_base64": "..."}
{"type": "complete"}
{"type": "error", "message": "..."} // on failure
```

## Key Concepts

### Phonemes vs. Graphemes
- **Phoneme**: Actual sound unit, e.g., /æ/ in "cat" (IPA notation)
- **Grapheme**: Written letter(s), e.g., "a" in "cat"
- System analyzes **phonemes** for pronunciation accuracy, not spelling

### PER (Phoneme Error Rate)
- Levenshtein distance at phoneme level: `(substitutions + deletions + insertions) / total_phonemes`
- Lower PER = better pronunciation (0.0 = perfect, 1.0 = completely wrong)
- Computed per-word AND overall for granular feedback

### Hybrid Processing
- **Client extracts phonemes** (Transformers.js) if device capable (4GB+ RAM, WebAssembly)
- **Server validates & completes analysis** (word extraction, alignment, GPT prompting)
- Reduces latency (no audio upload time) & server load while maintaining quality

### Sessions vs. Activities
- **Activity**: Template with `activity_type` + `activity_settings` JSON
- **Session**: User instance of an activity, tracks progress via `FeedbackEntry` records
- `activity_settings` stores mode-specific config (e.g., `first_sentence`, `story_name`)

## Database Schema

**MySQL (prod) / SQLite (dev)** with Alembic migrations

Key relationships:
- `users` → `sessions` (1:many) → `feedback_entries` (1:many)
- `sessions` → `activities` (1:1)

## Common Patterns

### Adding a New Practice Mode

1. Create `backend/core/modes/my_mode.py` inheriting `BaseMode`:
```python
from .base_mode import BaseMode

class MyMode(BaseMode):
    def get_feedback_and_next_sentence(self, attempted_sentence, analysis, phoneme_assistant, session):
        # Load prompt
        prompt = phoneme_assistant.load_prompt("core/gpt_prompts/my_mode_prompt_v1.txt")

        # Call GPT with context
        response = phoneme_assistant.query_gpt(conversation_history)

        # Return JSON
        return {
            "next_sentence": "...",
            "feedback": "...",
            "encouragement": "..."
        }
```

2. Create GPT prompt in `core/gpt_prompts/my_mode_prompt_v1.txt`
3. Update `routers/ai.py` to route `activity_type` to new mode class
4. Add frontend component in `components/practice/` (or reuse `BasePractice.tsx`)

### Testing Strategy

Tests are organized by processing layer:
- **`tests/extraction/`** - Phoneme extraction only (audio → IPA phonemes)
- **`tests/analysis/`** - Full pipeline (pre-extracted phonemes + sentence → PER analysis)
- **`tests/gpt/`** - GPT prompt/response validation
- **`tests/system/`** - End-to-end with real audio files

Each test folder has a README with file format specs.

Test JSON format example:
```json
{
  "sentence": "The cat sat.",
  "client_phonemes": [["ð", "ə"], ["k", "æ", "t"], ["s", "æ", "t"]],
  "expected_output": {...}
}
```

## Configuration

### Environment Variables
- `USE_ONNX_BACKEND=true` (default) - Use ONNX for 2-3x faster inference
- `OPENAI_API_KEY` - Required for GPT feedback
- `DATABASE_URL` - MySQL connection string (prod)
- `VITE_API_URL` - Frontend API base URL

### Client-Side ML
- Enabled per-user in `user_settings.use_client_phoneme_extraction`
- Requires 4GB+ RAM and WebAssembly support

## Important Patterns & Conventions

### Backend
- Use `PhonemeAssistant.load_prompt()` to load GPT prompts (auto-appends SSML instructions)
- Always validate GPT responses with `extract_json()` in `PhonemeAssistant`
- Phonemes are always in IPA format from wav2vec2-TIMIT-IPA model
- Audio must be preprocessed to 16kHz, mono before extraction

### Frontend
- All API calls go through `src/api.ts`
- Use `useAudioTransport` hook for WebSocket/SSE abstraction
- Follow `STYLE_GUIDELINES.md` for consistent Tailwind patterns
- Use CSS variables for colors (oklch color space)
- Practice components should handle streaming responses progressively

### Database
- Always create Alembic migrations for schema changes
- Use Pydantic schemas for API validation
- Session state is stored in `activity_settings` JSON field

## Troubleshooting

- **Model loading fails**: Check RAM (4GB+ required), verify HuggingFace Hub access, try `USE_ONNX_BACKEND=false`
- **WebSocket disconnects**: Check nginx config for WebSocket support (`proxy_buffering off`), verify CORS origins
- **High PER despite good pronunciation**: Validate ground truth with `grapheme_to_phoneme()`, check audio quality (16kHz, low noise)
- **GPT malformed JSON**: Check prompt includes output schema, use `extract_json()`, log full response

## Key Files Reference

| Purpose | Location |
|---------|----------|
| API client | `frontend/src/api.ts` |
| Main pipeline | `backend/core/phoneme_assistant.py` |
| WebSocket handler | `backend/routers/ai.py` |
| Audio processing | `backend/core/process_audio.py` |
| Client ML | `frontend/src/services/phonemeExtractor.ts` |
| DB models | `backend/models/` |
| Pydantic schemas | `backend/schemas/` |
| Style guidelines | `frontend/STYLE_GUIDELINES.md` |

## Glossary

- **IPA**: International Phonetic Alphabet (standard phoneme notation)
- **PER**: Phoneme Error Rate (0.0-1.0, lower is better)
- **TTS**: Text-to-Speech audio generation
- **ONNX**: Optimized model format (2-3x faster inference)
- **SSE**: Server-Sent Events (unidirectional streaming, WebSocket fallback)
