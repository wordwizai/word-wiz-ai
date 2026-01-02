# Word Wiz AI - Repository Guide

**Version:** 1.0  
**Last Updated:** December 2024  
**Purpose:** Comprehensive guide for LLM agents to understand the repository structure, architecture, and data flow.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture Overview](#architecture-overview)
3. [Technology Stack](#technology-stack)
4. [Repository Structure](#repository-structure)
5. [Data Flow](#data-flow)
6. [Core Components](#core-components)
7. [Key Features](#key-features)
8. [Database Schema](#database-schema)
9. [API Endpoints](#api-endpoints)
10. [Frontend Architecture](#frontend-architecture)
11. [Deployment](#deployment)
12. [Development Guide](#development-guide)
13. [Implementation Guides](#implementation-guides)

---

## Project Overview

**Word Wiz AI** is an AI-powered educational web application designed to help young children learn to read through phoneme-level audio feedback. The application generates decodable practice sentences and provides precise pronunciation guidance using advanced speech recognition and natural language processing.

### Key Objectives

- Provide real-time phoneme-level feedback on pronunciation
- Generate engaging, age-appropriate reading practice content
- Support multiple practice modes for varied learning experiences
- Deliver an accessible, browser-based learning platform

### Current Status

- ✅ Deployed in production
- ✅ Frontend: Vercel (wordwizai.com)
- ✅ Backend: AWS EC2 instance (api.wordwizai.com)
- ✅ Three active practice modes (Unlimited, Story, Choice Story)
- ✅ WebSocket and SSE support for real-time communication
- ✅ Client-side phoneme extraction (optional optimization)

---

## Architecture Overview

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT (Browser)                         │
│  ┌────────────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │  React Frontend│  │ Transformers │  │  WebSocket/SSE     │  │
│  │  (Vercel)      │  │ .js (Optional│  │  Client            │  │
│  │                │  │  Phoneme)    │  │                    │  │
│  └────────┬───────┘  └──────┬───────┘  └─────────┬──────────┘  │
└───────────┼──────────────────┼────────────────────┼─────────────┘
            │                  │                    │
            │ HTTPS            │ Model Loading      │ WSS/HTTPS
            │                  │                    │
┌───────────▼──────────────────▼────────────────────▼─────────────┐
│                    BACKEND (AWS EC2)                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              FastAPI Application (Port 8443)              │   │
│  │  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │   │
│  │  │   Routers   │  │  Auth/OAuth  │  │  WebSocket     │  │   │
│  │  │  (ai, user, │  │  (JWT, Google│  │  Manager       │  │   │
│  │  │   session)  │  │   OAuth)     │  │                │  │   │
│  │  └──────┬──────┘  └──────┬───────┘  └────────┬───────┘  │   │
│  └─────────┼─────────────────┼───────────────────┼──────────┘   │
│            │                 │                   │              │
│  ┌─────────▼─────────────────▼───────────────────▼──────────┐   │
│  │                   Core Processing Layer                   │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐  │   │
│  │  │   Phoneme    │  │     Word     │  │   GPT-4 API    │  │   │
│  │  │  Assistant   │  │   Extractor  │  │  (Feedback)    │  │   │
│  │  │  (wav2vec2)  │  │              │  │                │  │   │
│  │  └──────┬───────┘  └──────┬───────┘  └────────┬───────┘  │   │
│  │         │                 │                   │          │   │
│  │  ┌──────▼─────────────────▼───────────────────▼───────┐  │   │
│  │  │        ONNX Runtime / PyTorch Engine              │  │   │
│  │  │        (wav2vec2-TIMIT-IPA model)                 │  │   │
│  │  └───────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    MySQL Database                         │   │
│  │  (users, sessions, activities, feedback_entries,         │   │
│  │   user_settings)                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
            │                                    │
            │ External APIs                      │
┌───────────▼──────────┐            ┌───────────▼──────────┐
│   OpenAI GPT-4 API   │            │  Google Cloud APIs   │
│  (Sentence Gen &     │            │  (TTS, OAuth)        │
│   Feedback)          │            │                      │
└──────────────────────┘            └──────────────────────┘
```

### Communication Patterns

1. **REST API**: Standard HTTP requests for CRUD operations
2. **WebSocket**: Persistent connection for real-time audio processing
3. **SSE (Server-Sent Events)**: Alternative streaming method for audio feedback
4. **Client-Side Processing**: Optional phoneme extraction in browser (Transformers.js)

---

## Technology Stack

### Frontend

- **Framework**: React 19.1.0 with TypeScript
- **Build Tool**: Vite 7.0.2
- **Styling**: Tailwind CSS 4.1.11
- **UI Components**: Radix UI primitives
- **State Management**: React Context (Auth, Settings, Theme)
- **Routing**: React Router DOM 7.6.3
- **HTTP Client**: Axios 1.10.0
- **ML (Optional)**: @huggingface/transformers 3.7.6 (client-side phoneme extraction)
- **Deployment**: Vercel

### Backend

- **Framework**: FastAPI (Python)
- **Server**: Uvicorn + Gunicorn
- **Authentication**: PyJWT, python-jose, Authlib (Google OAuth)
- **Database ORM**: SQLAlchemy with Alembic migrations
- **Database**: MySQL (production), SQLite (development)
- **ML/AI Models**:
  - PyTorch (with CPU-only optimization)
  - ONNX Runtime (default for performance)
  - Transformers 4.30.0+
  - wav2vec2-TIMIT-IPA (phoneme recognition)
- **Audio Processing**:
  - librosa (audio loading/preprocessing)
  - soundfile (audio I/O)
  - noisereduce (noise reduction)
- **Text-to-Speech**: Google Cloud TTS, ElevenLabs
- **Speech Recognition**: wav2vec2-TIMIT-IPA model
- **NLP**: OpenAI GPT-4 API, eng_to_ipa (grapheme-to-phoneme)
- **Deployment**: AWS EC2 with Docker, Nginx reverse proxy

### DevOps

- **Containerization**: Docker + Docker Compose
- **Web Server**: Nginx (reverse proxy, SSL termination)
- **SSL/TLS**: Let's Encrypt (Certbot)
- **CI/CD**: Git-based deployment
- **Monitoring**: Custom health check endpoints

---

## Repository Structure

```
word-wiz-ai/
├── backend/                      # FastAPI backend application
│   ├── ai/                       # AI/ML research and utilities
│   │   ├── audio_recording.py    # Audio capture utilities
│   │   ├── dataset_loader.py     # Training data management
│   │   ├── evaluation/           # Model evaluation scripts
│   │   ├── phoneme_assistant_app.py  # Standalone phoneme testing
│   │   └── ...                   # Other research tools
│   ├── alembic/                  # Database migration scripts
│   ├── auth/                     # Authentication logic
│   │   └── auth_handler.py       # JWT token validation, user auth
│   ├── core/                     # Core processing logic
│   │   ├── modes/                # Practice mode implementations
│   │   │   ├── base_mode.py      # Abstract base class
│   │   │   ├── unlimited.py      # Unlimited practice mode
│   │   │   ├── story.py          # Story-based practice
│   │   │   └── choice_story.py   # Interactive choice-based stories
│   │   ├── audio_preprocessing.py    # Audio cleaning/normalization
│   │   ├── audio_optimization.py     # Performance optimizations
│   │   ├── phoneme_assistant.py      # Main phoneme analysis coordinator
│   │   ├── phoneme_extractor.py      # PyTorch-based phoneme extraction
│   │   ├── phoneme_extractor_onnx.py # ONNX-optimized extraction
│   │   ├── word_extractor.py         # Word boundary detection
│   │   ├── process_audio.py          # Audio processing pipeline
│   │   ├── text_to_audio.py          # TTS integration
│   │   ├── grapheme_to_phoneme.py    # Text-to-phoneme conversion
│   │   ├── speech_problem_classifier.py  # Error categorization
│   │   └── optimization_config.py    # Performance settings
│   ├── crud/                     # Database operations
│   │   ├── activity.py           # Activity CRUD
│   │   ├── feedback_entry.py     # Feedback CRUD
│   │   └── session.py            # Session CRUD
│   ├── models/                   # SQLAlchemy ORM models
│   │   ├── user.py               # User model
│   │   ├── activity.py           # Activity model
│   │   ├── session.py            # Session model
│   │   ├── feedback_entry.py     # Feedback storage
│   │   └── user_settings.py      # User preferences
│   ├── routers/                  # API endpoint definitions
│   │   ├── ai.py                 # Audio analysis, WebSocket
│   │   ├── auth.py               # Login, registration
│   │   ├── google_auth.py        # OAuth flow
│   │   ├── user.py               # User profile endpoints
│   │   ├── session.py            # Session management
│   │   ├── activities.py         # Activity listing
│   │   ├── feedback.py           # Feedback retrieval
│   │   ├── health.py             # Health check endpoints
│   │   └── handlers/             # Request processing helpers
│   ├── schemas/                  # Pydantic models (validation)
│   │   ├── audio.py              # Audio analysis schemas
│   │   ├── activity.py           # Activity schemas
│   │   ├── session.py            # Session schemas
│   │   ├── feedback_entry.py     # Feedback schemas
│   │   ├── settings.py           # Settings schemas
│   │   └── token_user.py         # Auth token schemas
│   ├── tests/                    # Test suite
│   │   ├── extraction/           # Phoneme extraction tests
│   │   ├── analysis/             # Analysis pipeline tests
│   │   ├── gpt/                  # GPT integration tests
│   │   └── system/               # End-to-end tests
│   ├── nginx/                    # Nginx configuration
│   ├── database.py               # Database connection setup
│   ├── main.py                   # FastAPI application entry point
│   ├── requirements.txt          # Python dependencies
│   ├── Dockerfile                # Backend container definition
│   ├── docker-compose.yml        # Multi-container orchestration
│   └── alembic.ini               # Migration configuration
│
├── frontend/                     # React frontend application
│   ├── public/                   # Static assets
│   ├── src/
│   │   ├── api.ts                # Backend API client functions
│   │   ├── App.tsx               # Root component with routing
│   │   ├── main.tsx              # React entry point
│   │   ├── components/           # Reusable UI components
│   │   │   ├── ui/               # Base UI components (buttons, inputs, etc.)
│   │   │   ├── practice/         # Practice-specific components
│   │   │   │   ├── BasePractice.tsx          # Core practice logic
│   │   │   │   ├── ChoiceStoryBasePractice.tsx  # Choice story variant
│   │   │   │   ├── FeedbackDisplay.tsx       # Pronunciation feedback UI
│   │   │   │   ├── SentenceDisplay.tsx       # Sentence rendering
│   │   │   │   └── ModelLoadingIndicator.tsx # Loading states
│   │   │   ├── Layout.tsx        # App layout wrapper
│   │   │   ├── Sidebar.tsx       # Navigation sidebar
│   │   │   ├── ProtectedRoute.tsx  # Auth guard component
│   │   │   ├── OAuthRedirect.tsx   # OAuth callback handler
│   │   │   └── ...               # Other components
│   │   ├── contexts/             # React Context providers
│   │   │   ├── AuthContext.tsx   # User authentication state
│   │   │   ├── SettingsContext.tsx  # User settings
│   │   │   └── ThemeContext.tsx  # Light/dark theme
│   │   ├── hooks/                # Custom React hooks
│   │   │   └── useAudioTransport.ts  # WebSocket/SSE abstraction
│   │   ├── pages/                # Route components
│   │   │   ├── LandingPage.tsx   # Public homepage
│   │   │   ├── Login.tsx         # Login page
│   │   │   ├── SignUp.tsx        # Registration page
│   │   │   ├── Dashboard.tsx     # Main user dashboard
│   │   │   ├── PracticeDashboard.tsx  # Practice mode selector
│   │   │   ├── PracticeRouter.tsx     # Practice session router
│   │   │   ├── ProgressDashboard.tsx  # Statistics and progress
│   │   │   ├── Settings.tsx      # User settings
│   │   │   └── ...
│   │   ├── services/             # Business logic services
│   │   │   ├── audioTransport.ts     # WebSocket/SSE transport layer
│   │   │   ├── phonemeExtractor.ts   # Client-side ML inference
│   │   │   ├── wordExtractor.ts      # Client-side word detection
│   │   │   └── performanceTracker.ts # Performance monitoring
│   │   └── utils/                # Utility functions
│   ├── package.json              # NPM dependencies
│   ├── vite.config.ts            # Vite configuration
│   ├── tsconfig.json             # TypeScript configuration
│   ├── components.json           # Shadcn UI config
│   ├── vercel.json               # Vercel deployment config
│   └── STYLE_GUIDELINES.md       # Frontend coding standards
│
├── implementation_guides/        # Feature implementation docs
│   ├── WEBSOCKET_IMPLEMENTATION_PLAN.md
│   ├── client-side-phoneme-extraction.md
│   ├── client-side-word-extraction.md
│   ├── UI_MODERNIZATION_GUIDE.md
│   ├── TESTING_SUITE_IMPLEMENTATION_GUIDE.md
│   ├── USER_STATISTICS_ENDPOINT.md
│   ├── WEBGPU_GUIDE.md
│   └── BUG_FIX_IMPLEMENTATION_PLAN.md
│
├── upload_model.py               # HuggingFace model upload script
├── vercel.json                   # Root Vercel config
├── README.md                     # Project overview
├── .gitignore                    # Git ignore rules
└── REPOSITORY_GUIDE.md           # This file
```

---

## Data Flow

### 1. User Authentication Flow

```
User → Frontend Login Form
    ↓
    → POST /auth/token (username/password)
    → POST /auth/google/login (OAuth)
    ↓
Backend validates credentials
    ↓
JWT token generated
    ↓
Frontend stores token → AuthContext
    ↓
Token included in Authorization header for all requests
```

### 2. Practice Session Flow

```
User selects activity → Frontend Dashboard
    ↓
    → GET /activities/ (fetch available activities)
    ↓
    → POST /session/ (create new session with activity_id)
    ↓
Backend creates Session record in database
    ↓
    ← Returns session_id and activity details
    ↓
Frontend navigates to /practice/{session_id}
    ↓
PracticeRouter loads appropriate practice component
    (BasePractice, ChoiceStoryBasePractice, etc.)
    ↓
Component fetches initial sentence/story data
    ↓
    → GET /session/{session_id}/current-data
    ↓
    ← Returns activity settings or latest feedback
```

### 3. Audio Analysis Flow (Primary Feature)

#### Option A: WebSocket (Default, Low Latency)

```
Frontend establishes WebSocket connection
    ↓
    → WS /ai/ws/audio-analysis?token={JWT}
    ↓
Backend authenticates and maintains connection
    ↓
User reads sentence aloud → Audio recorded in browser
    ↓
Frontend (Optional):
    - Extracts phonemes using Transformers.js
    - Extracts word boundaries
    ↓
Audio + metadata sent via WebSocket
    ↓
    → {
        type: "analyze_audio",
        audio_base64: "...",
        attempted_sentence: "...",
        session_id: 123,
        client_phonemes: [[...]], (optional)
        client_words: [...] (optional)
      }
    ↓
Backend processes audio:
    1. Validates and preprocesses audio
    2. If client_phonemes provided → Use them
       Else → Extract phonemes (ONNX/PyTorch)
    3. Extract word boundaries
    4. Align phonemes to words
    5. Compute Phoneme Error Rate (PER)
    6. Classify speech problems
    7. Generate feedback via GPT-4
    8. Generate TTS audio feedback
    ↓
Backend streams results back via WebSocket:
    ← { type: "processing_started" }
    ← { type: "analysis", data: {...} }
    ← { type: "gpt_response", data: {...} }
    ← { type: "audio_feedback_file", audio_base64: "..." }
    ↓
Frontend updates UI in real-time
    ↓
Backend saves FeedbackEntry to database
```

#### Option B: SSE (Fallback)

```
Similar flow but uses Server-Sent Events
    ↓
    → POST /ai/analyze-audio (multipart/form-data)
    ← text/event-stream response
    ← data: {"type": "processing_started"}
    ← data: {"type": "analysis", "data": {...}}
    ← ...
```

### 4. Feedback Processing in Detail

```
Audio Analysis Result (PER, alignment, errors)
    ↓
Sent to practice mode object (UnlimitedPractice, StoryPractice, etc.)
    ↓
Mode.get_feedback_and_next_sentence()
    ↓
    1. Analyzes pronunciation errors
    2. Generates context for GPT-4
    3. Calls OpenAI API with:
       - Current sentence
       - User pronunciation data
       - Past errors/context
       - Mode-specific instructions
    ↓
GPT-4 returns:
    {
      "next_sentence": "...",
      "feedback": "...",
      "encouragement": "...",
      "achievements": [...]
    }
    ↓
Backend validates GPT response
    ↓
Backend generates TTS audio from feedback
    ↓
All data returned to frontend
    ↓
FeedbackEntry saved to database:
    - session_id
    - sentence (attempted)
    - phoneme_analysis (PER, alignments, errors)
    - gpt_response (feedback, next sentence)
```

### 5. Progress Tracking Flow

```
User views progress → ProgressDashboard
    ↓
    → GET /feedback/ (fetch user's feedback entries)
    ↓
Backend queries FeedbackEntry table
    ↓
    ← Returns list of feedback with:
        - Sentences practiced
        - PER scores over time
        - Common error phonemes
        - Session timestamps
    ↓
Frontend aggregates and visualizes data
    (Charts, statistics, achievements)
```

---

## Core Components

### Backend Core Components

#### 1. PhonemeAssistant (`core/phoneme_assistant.py`)

**Purpose**: Orchestrates the entire audio analysis pipeline

**Key Responsibilities**:

- Initializes ML models (PhonemeExtractor, WordExtractor)
- Coordinates audio preprocessing
- Manages TTS generation
- Routes processing based on optimization settings

**Key Methods**:

- `analyze_pronunciation()`: Main entry point for audio analysis
- `get_performance_info()`: Returns model configuration details

**Configuration**:

- `USE_ONNX_BACKEND=true` (default): Uses ONNX Runtime for 2-3x speed
- `use_optimized_model=true`: Enables quantization and fast models

#### 2. PhonemeExtractor (`core/phoneme_extractor.py` / `phoneme_extractor_onnx.py`)

**Purpose**: Extracts phonemes from audio using wav2vec2-TIMIT-IPA

**Models**:

- Default: `speech31/wav2vec2-large-TIMIT-IPA`
- Fast: `facebook/wav2vec2-base-960h`
- ONNX: Optimized version (faster inference)

**Key Features**:

- Model caching (singleton pattern)
- Dynamic quantization for CPU optimization
- Audio preprocessing pipeline
- Blank token filtering

**Performance**:

- ONNX: ~0.5-1s per audio clip
- PyTorch: ~1-2s per audio clip

#### 3. WordExtractor (`core/word_extractor.py`)

**Purpose**: Detects word boundaries in audio

**Algorithm**:

- Analyzes energy levels in audio signal
- Detects silence/pauses between words
- Aligns detected boundaries with expected words

**Variants**:

- `WordExtractor`: Original implementation
- `WordExtractorOnline`: Used in production (improved accuracy)

#### 4. Audio Processing Pipeline (`core/process_audio.py`)

**Purpose**: Aligns phonemes to words and computes accuracy metrics

**Key Functions**:

- `align_phonemes_to_words()`: Dynamic programming alignment
- `compute_per()`: Phoneme Error Rate calculation
- `analyze_results()`: Generates pronunciation summary
- `process_audio_with_client_phonemes()`: Hybrid processing with client data

**Metrics Computed**:

- Phoneme Error Rate (PER) per word
- Overall PER
- Highest PER word (most difficult)
- Per-phoneme error breakdown
- Speech problem classification

#### 5. Practice Modes (`core/modes/`)

**Purpose**: Implement different learning experiences

**Base Class** (`base_mode.py`):

- Abstract interface for all modes
- `get_feedback_and_next_sentence()`: Must be implemented

**Unlimited Mode** (`unlimited.py`):

- Continuous practice with adaptive difficulty
- Tracks past errors across session
- Generates contextually relevant sentences

**Story Mode** (`story.py`):

- Linear story progression
- Fixed story content from JSON files
- Advances when user reads correctly

**Choice Story Mode** (`choice_story.py`):

- Interactive branching narratives
- User chooses between 2 sentences at each step
- Dynamic story generation based on choices

#### 6. GPT Integration (`core/gpt_prompts/`, mode implementations)

**Purpose**: Generate educational feedback and next sentences

**Prompt Strategy**:

- Includes pronunciation data (PER, errors)
- Provides learning context (past mistakes)
- Mode-specific instructions
- Structured JSON output

**Validation** (`core/gpt_output_validator.py`):

- Ensures GPT returns expected fields
- Validates sentence structure
- Logs malformed responses

#### 7. Text-to-Speech (`core/text_to_audio.py`)

**Purpose**: Generate audio feedback for users

**Providers**:

- `GoogleTTSAPIClient`: Default (Google Cloud TTS)
- `ElevenLabsAPIClient`: Alternative (more natural voices)

**Features**:

- Voice selection (child-friendly voices)
- Speed adjustment
- Audio format optimization

### Frontend Core Components

#### 1. AuthContext (`contexts/AuthContext.tsx`)

**Purpose**: Global authentication state management

**Responsibilities**:

- Stores JWT token
- Maintains user profile
- Provides login/logout/register functions
- Auto-refreshes user data

**API**:

```typescript
{
  user: User | null,
  token: string | null,
  login: (credentials) => Promise<void>,
  logout: () => void,
  register: (userData) => Promise<void>,
  loading: boolean
}
```

#### 2. Practice Components (`components/practice/`)

**BasePractice.tsx**:

- Core practice loop logic
- Audio recording management
- Feedback display coordination
- Sentence progression
- Used by Unlimited and Story modes

**ChoiceStoryBasePractice.tsx**:

- Extends BasePractice with choice logic
- Displays two sentence options
- Handles user selection
- Manages branching story state

**FeedbackDisplay.tsx**:

- Renders pronunciation feedback
- Shows word-level PER scores
- Highlights problematic phonemes
- Displays encouragement messages

**SentenceDisplay.tsx**:

- Renders current sentence to read
- Highlights words based on accuracy
- Shows phoneme breakdowns

#### 3. Audio Transport Layer (`services/audioTransport.ts`, `hooks/useAudioTransport.ts`)

**Purpose**: Abstracts WebSocket/SSE communication

**Architecture**:

```typescript
interface AudioTransport {
  connect(): Promise<void>
  sendAudio(file: File, ...): Promise<void>
  disconnect(): void
  isConnected(): boolean
}
```

**Implementations**:

- `WebSocketTransport`: Persistent WebSocket connection
- `SSETransport`: Server-Sent Events (fallback)

**Hook** (`useAudioTransport`):

- Manages transport lifecycle
- Routes events to callbacks
- Handles reconnection logic
- Provides unified API for components

#### 4. Client-Side ML (`services/phonemeExtractor.ts`)

**Purpose**: Optional browser-based phoneme extraction

**Features**:

- Uses Transformers.js (WebAssembly)
- Offloads processing from server
- Reduces latency for capable devices
- Model caching in IndexedDB

**Flow**:

1. Check device capabilities (RAM, WebAssembly support)
2. Load model lazily (only if enabled in settings)
3. Extract phonemes from audio
4. Send phonemes to backend (hybrid processing)
5. Backend validates and uses client phonemes

#### 5. Settings Management (`contexts/SettingsContext.tsx`)

**Purpose**: User preferences and app configuration

**Settings**:

- `use_client_phoneme_extraction`: Enable client-side ML
- Theme preferences
- Audio settings
- Notification preferences

**Persistence**:

- Stored in backend database (UserSettings table)
- Cached locally in Context
- Updated via `PATCH /users/me/settings`

---

## Key Features

### 1. Real-Time Phoneme-Level Feedback

- Analyzes user pronunciation at phoneme granularity
- Highlights specific sound errors (e.g., confusing /æ/ with /ɛ/)
- Provides targeted correction advice

### 2. Adaptive Learning Modes

- **Unlimited Practice**: Free-form practice with adaptive difficulty
- **Story Mode**: Guided reading through engaging narratives
- **Choice Story**: Interactive storytelling with user choices

### 3. AI-Generated Content

- GPT-4 generates contextually appropriate sentences
- Adapts difficulty based on user performance
- Maintains conversation continuity in choice stories

### 4. Performance Optimizations

- **ONNX Runtime**: 2-3x faster phoneme extraction
- **Client-Side Processing**: Optional browser-based inference
- **WebSocket**: Persistent connections eliminate reconnection overhead
- **Model Caching**: Singleton pattern for ML models
- **Audio Optimization**: Preprocessing pipeline reduces memory usage

### 5. Dual Authentication

- Username/password authentication
- Google OAuth integration
- JWT token-based sessions

### 6. Progress Tracking

- Historical performance data
- PER trends over time
- Common error identification
- Achievement system (planned)

### 7. Accessibility

- Browser-based (no installation required)
- Mobile-responsive design
- Light/dark theme support
- Child-friendly UI

---

## Database Schema

### Users Table

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    full_name VARCHAR(225),
    username VARCHAR(225) UNIQUE NOT NULL,
    email VARCHAR(225) UNIQUE NOT NULL,
    hashed_password VARCHAR(225),
    is_active BOOLEAN DEFAULT TRUE
);
```

### UserSettings Table

```sql
CREATE TABLE user_settings (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    user_id INTEGER FOREIGN KEY REFERENCES users(id),
    use_client_phoneme_extraction BOOLEAN DEFAULT FALSE,
    theme_mode VARCHAR(50),
    -- Other settings...
);
```

### Activities Table

```sql
CREATE TABLE activities (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(225) NOT NULL,
    description TEXT NOT NULL,
    emoji_icon VARCHAR(100),
    activity_type VARCHAR(225) NOT NULL, -- 'unlimited', 'story', 'choice-story'
    activity_settings JSON DEFAULT '{}' -- Mode-specific configuration
);
```

**Sample Activity**:

```json
{
  "id": 1,
  "title": "Unlimited Practice",
  "activity_type": "unlimited",
  "activity_settings": {
    "first_sentence": "The cat sat on the mat."
  }
}
```

### Sessions Table

```sql
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    user_id INTEGER FOREIGN KEY REFERENCES users(id),
    activity_id INTEGER FOREIGN KEY REFERENCES activities(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_completed INTEGER DEFAULT 0 -- 0: active, 1: completed
);
```

### FeedbackEntries Table

```sql
CREATE TABLE feedback_entries (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    session_id INTEGER FOREIGN KEY REFERENCES sessions(id),
    sentence TEXT, -- Sentence the user attempted
    phoneme_analysis JSON, -- PER, alignments, error breakdown
    gpt_response JSON, -- Feedback text, next sentence, achievements
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Sample FeedbackEntry**:

```json
{
  "id": 42,
  "session_id": 10,
  "sentence": "The dog runs fast.",
  "phoneme_analysis": {
    "per_summary": 0.12,
    "highest_per_word": "runs",
    "highest_per": 0.35,
    "problem_summary": {
      "substitutions": ["ʌ → ə in 'runs'"],
      "deletions": [],
      "insertions": []
    },
    "pronunciation_dataframe": [
      {
        "word": "The",
        "per": 0.0,
        "ground_truth_phonemes": ["ð", "ə"],
        "phonemes": ["ð", "ə"]
      },
      {
        "word": "runs",
        "per": 0.35,
        "ground_truth_phonemes": ["ɹ", "ʌ", "n", "z"],
        "phonemes": ["ɹ", "ə", "n", "z"]
      }
    ]
  },
  "gpt_response": {
    "feedback": "Good job! Watch the 'u' sound in 'runs'.",
    "next_sentence": "The quick brown fox jumps.",
    "encouragement": "You're improving!",
    "achievements": []
  }
}
```

### Relationships

```
User (1) ─────── (1) UserSettings
  │
  └─ (1) ─────── (*) Sessions
                    │
                    └─ (1) ─────── (1) Activity
                    │
                    └─ (1) ─────── (*) FeedbackEntries
```

---

## API Endpoints

### Authentication Endpoints

#### `POST /auth/register`

Register a new user.

**Request**:

```json
{
  "full_name": "John Doe",
  "username": "johndoe",
  "email": "john@example.com",
  "password": "securepassword"
}
```

**Response**: 201 Created

---

#### `POST /auth/token`

Login with username/password.

**Request** (form-urlencoded):

```
username=johndoe
password=securepassword
```

**Response**:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

---

#### `GET /auth/google/login`

Initiate Google OAuth flow. Redirects to Google consent screen.

---

#### `GET /auth/google/callback`

OAuth callback handler. Redirects to frontend with token.

---

### User Endpoints

#### `GET /users/me/`

Get current user profile.

**Headers**: `Authorization: Bearer {token}`

**Response**:

```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "is_active": true
}
```

---

#### `PATCH /users/me/settings`

Update user settings.

**Request**:

```json
{
  "use_client_phoneme_extraction": true,
  "theme_mode": "dark"
}
```

**Response**: Updated settings object

---

### Activity Endpoints

#### `GET /activities/`

List all available activities.

**Response**:

```json
[
  {
    "id": 1,
    "title": "Unlimited Practice",
    "description": "Practice reading with unlimited sentences.",
    "emoji_icon": "🔥",
    "activity_type": "unlimited",
    "activity_settings": { "first_sentence": "..." }
  },
  {
    "id": 2,
    "title": "Story Time",
    "description": "Read through an engaging story.",
    "emoji_icon": "📖",
    "activity_type": "story",
    "activity_settings": { "story_name": "pirate_adventure" }
  }
]
```

---

#### `GET /activities/{activity_id}`

Get specific activity details.

---

### Session Endpoints

#### `POST /session/`

Create a new practice session.

**Request**:

```json
{
  "activity_id": 1
}
```

**Response**:

```json
{
  "id": 10,
  "user_id": 1,
  "activity_id": 1,
  "is_completed": 0,
  "created_at": "2024-12-11T12:00:00Z",
  "activity": { ... }
}
```

---

#### `GET /session/active`

Get user's active (incomplete) sessions.

---

#### `GET /session/all`

Get all user's sessions (active + completed).

---

#### `GET /session/{session_id}`

Get specific session details.

---

#### `POST /session/{session_id}/deactivate`

Mark session as completed.

---

#### `GET /session/{session_id}/current-data`

Get current state for session (initial settings or latest feedback).

**Response**:

```json
{
  "type": "full-feedback-state",
  "data": { ... } // Latest FeedbackEntry
}
```

---

### AI/Audio Analysis Endpoints

#### `WS /ai/ws/audio-analysis?token={JWT}`

WebSocket endpoint for real-time audio processing.

**Client Messages**:

```json
{
  "type": "analyze_audio",
  "audio_base64": "...",
  "attempted_sentence": "The cat sat.",
  "session_id": 10,
  "client_phonemes": [
    ["ð", "ə"],
    ["k", "æ", "t"],
    ["s", "æ", "t"]
  ],
  "client_words": ["The", "cat", "sat"]
}
```

**Server Messages**:

```json
{ "type": "processing_started" }
{ "type": "analysis", "data": { "per_summary": 0.1, ... } }
{ "type": "gpt_response", "data": { "feedback": "...", ... } }
{ "type": "audio_feedback_file", "audio_base64": "..." }
{ "type": "complete" }
{ "type": "error", "message": "..." }
```

---

#### `POST /ai/analyze-audio`

SSE endpoint for audio processing (fallback).

**Request** (multipart/form-data):

- `attempted_sentence`: string
- `session_id`: integer
- `audio_file`: File

**Response**: text/event-stream (same events as WebSocket)

---

#### `POST /ai/analyze-audio-with-phonemes`

Hybrid processing with client-provided phonemes.

**Request** (multipart/form-data):

- `attempted_sentence`: string
- `session_id`: integer
- `client_phonemes`: JSON string
- `client_words`: JSON string (optional)
- `audio_file`: File

---

### Feedback Endpoints

#### `GET /feedback/`

Get user's feedback history.

**Query Params**:

- `limit`: number (default: 50)
- `offset`: number (default: 0)

**Response**: Array of FeedbackEntry objects

---

### Health Check Endpoints

#### `GET /health`

Basic health check.

**Response**:

```json
{ "status": "healthy" }
```

---

## Frontend Architecture

### Routing Structure

```
/ (LandingPage)
  - Public homepage
  - Unauthenticated users

/login (Login)
  - Login form
  - Google OAuth button

/signup (SignUp)
  - Registration form

/oauth-callback (OAuthRedirect)
  - Handles Google OAuth callback
  - Extracts token from URL
  - Redirects to dashboard

/dashboard (ProtectedRoute → Dashboard)
  - Main user dashboard
  - Overview of activities
  - Quick stats

/practice (ProtectedRoute → PracticeDashboard)
  - Activity selection
  - Start new sessions

/practice/:sessionId (ProtectedRoute → PracticeRouter)
  - Routes to appropriate practice component
  - GenericPractice (unlimited, story)
  - ChoiceStoryPractice (choice-story)

/progress (ProtectedRoute → ProgressDashboard)
  - Historical performance data
  - Charts and statistics

/settings (ProtectedRoute → Settings)
  - User profile
  - Preferences (theme, client-side processing)
  - Account management

/about (About)
  - Project information

/contact (Contact)
  - Contact form
```

### State Management

**Global State (Context)**:

1. **AuthContext**: User authentication, JWT token
2. **SettingsContext**: User preferences, app configuration
3. **ThemeContext**: Light/dark mode

**Local State (Component)**:

- Recording status
- Current sentence
- Feedback data
- Loading states
- Error states

### Component Hierarchy (Practice Flow)

```
PracticeRouter
  ├─ GenericPractice (unlimited/story)
  │   └─ BasePractice
  │       ├─ SentenceDisplay
  │       ├─ RecordAndNextButtons
  │       ├─ FeedbackDisplay
  │       │   └─ WordBadgeRow
  │       │       └─ WordBadge (shows PER per word)
  │       └─ ModelLoadingIndicator
  │
  └─ ChoiceStoryPractice (choice-story)
      └─ ChoiceStoryBasePractice
          ├─ SentenceDisplay (shows 2 options)
          ├─ RecordAndNextButtons
          └─ FeedbackDisplay
```

### Key Hooks

#### `useAudioTransport`

Manages WebSocket/SSE communication for audio analysis.

**Usage**:

```typescript
const { sendAudio, isConnected, isProcessing } = useAudioTransport({
  sessionId,
  attemptedSentence,
  useWebSocket: true,
  onAnalysis: (data) => { ... },
  onGptResponse: (data) => { ... },
  onAudioFeedback: (blob) => { ... },
  onError: (err) => { ... }
});
```

#### `usePhonemeModel`

Manages client-side ML model lifecycle.

**Usage**:

```typescript
const { extractPhonemes, isLoading, isReady, error } = usePhonemeModel({
  autoLoad: true,
});

const phonemes = await extractPhonemes(audioBlob, text);
```

---

## Deployment

### Frontend Deployment (Vercel)

**Platform**: Vercel  
**Domain**: wordwizai.com  
**Build Command**: `npm run build`  
**Output Directory**: `dist`

**Environment Variables**:

- `VITE_API_URL`: Backend API URL (https://api.wordwizai.com)
- `VITE_WS_URL`: WebSocket URL (wss://api.wordwizai.com)

**Configuration** (`frontend/vercel.json`):

```json
{
  "rewrites": [{ "source": "/(.*)", "destination": "/" }]
}
```

### Backend Deployment (AWS EC2)

**Platform**: AWS EC2 instance  
**Domain**: api.wordwizai.com  
**Containerization**: Docker + Docker Compose  
**Web Server**: Nginx (reverse proxy)  
**SSL**: Let's Encrypt (auto-renewed with Certbot)

**Architecture**:

```
Internet → Nginx (80/443)
            ↓
         Backend Container (8443)
            ↓
         MySQL Database
```

**Docker Setup**:

1. **Backend Container**: FastAPI app on port 8443 with SSL
2. **Nginx Container**: Reverse proxy on ports 80/443
3. **Certbot Container**: SSL certificate management

**Key Configuration** (`backend/docker-compose.yml`):

- Resource limits: 1.5GB RAM, 1.3 CPU
- Volume mounts: SSL certs, Google Cloud credentials
- Port mappings: 80, 443, 8443

**Nginx Configuration** (`backend/nginx/nginx.conf`):

- HTTP → HTTPS redirect
- WebSocket support (no buffering)
- Proxy to backend on 8443
- SSL termination

**SSL Certificates**:

- Let's Encrypt via Certbot
- Auto-renewal configured
- Stored in Docker volume

**Deployment Process**:

1. SSH into EC2 instance
2. Pull latest code from Git
3. Rebuild Docker containers: `docker-compose up -d --build`
4. Nginx automatically reloads

### Database (MySQL)

**Location**: On EC2 instance or separate RDS instance  
**Connection**: Via `DATABASE_URL` environment variable

**Migrations**: Alembic (SQLAlchemy migrations)

```bash
# Generate migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head
```

### Environment Variables

**Backend** (`.env`):

```bash
DATABASE_URL=mysql+pymysql://user:pass@host:port/dbname
OPENAI_API_KEY=sk-...
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=https://api.wordwizai.com/auth/google/callback
SECRET_KEY=... (JWT signing key)
USE_ONNX_BACKEND=true
```

**Frontend** (`.env.production`):

```bash
VITE_API_URL=https://api.wordwizai.com
VITE_WS_URL=wss://api.wordwizai.com
```

---

## Development Guide

### Prerequisites

**Backend**:

- Python 3.12+
- pip (Python package manager)
- Virtual environment tool (venv, conda)

**Frontend**:

- Node.js 18+
- npm or yarn

### Local Development Setup

#### Backend Setup

1. **Clone repository**:

   ```bash
   git clone <repo-url>
   cd word-wiz-ai/backend
   ```

2. **Create virtual environment**:

   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**:

   - Copy `.env.example` to `.env`
   - Set `DATABASE_URL` to SQLite for local dev:
     ```
     DATABASE_URL=sqlite:///./users.db
     ```
   - Add OpenAI API key
   - (Optional) Add Google Cloud credentials for TTS

5. **Run migrations**:

   ```bash
   alembic upgrade head
   ```

6. **Start development server**:

   ```bash
   python main.py
   # Or with auto-reload:
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

7. **Test backend**:
   - Open http://localhost:8000/docs (Swagger UI)
   - Test endpoints interactively

#### Frontend Setup

1. **Navigate to frontend**:

   ```bash
   cd ../frontend
   ```

2. **Install dependencies**:

   ```bash
   npm install
   ```

3. **Configure environment**:

   - Create `.env.local`:
     ```
     VITE_API_URL=http://localhost:8000
     VITE_WS_URL=ws://localhost:8000
     ```

4. **Start development server**:

   ```bash
   npm run dev
   ```

5. **Open browser**:
   - Navigate to http://localhost:5173

### Running Tests

**Backend**:

```bash
cd backend
pytest tests/
```

**Frontend**:

```bash
cd frontend
npm run test  # (if configured)
```

### Development Workflow

1. **Feature Development**:

   - Create feature branch: `git checkout -b feature/name`
   - Make changes
   - Test locally
   - Commit: `git commit -m "description"`
   - Push: `git push origin feature/name`

2. **Database Changes**:

   - Modify models in `backend/models/`
   - Generate migration: `alembic revision --autogenerate -m "description"`
   - Review migration in `backend/alembic/versions/`
   - Apply: `alembic upgrade head`

3. **API Changes**:

   - Update router in `backend/routers/`
   - Update schema in `backend/schemas/`
   - Update frontend API client in `frontend/src/api.ts`
   - Test with Swagger UI

4. **Frontend Changes**:
   - Follow `frontend/STYLE_GUIDELINES.md`
   - Use existing components from `components/ui/`
   - Maintain TypeScript strict mode
   - Test responsiveness (mobile/desktop)

### Debugging

**Backend**:

- Use print statements (logged to console)
- Use debugger: `import pdb; pdb.set_trace()`
- Check logs: `docker logs fastapi_backend`

**Frontend**:

- Browser DevTools Console
- React DevTools extension
- Network tab for API calls
- `console.log()` debugging

### Common Issues

1. **Port already in use**:

   - Kill process: `lsof -ti:8000 | xargs kill -9` (Mac/Linux)
   - Change port in startup command

2. **Database locked (SQLite)**:

   - Close other connections
   - Delete `users.db` and re-run migrations (dev only)

3. **WebSocket connection fails**:

   - Check CORS settings in `main.py`
   - Verify `VITE_WS_URL` matches backend

4. **Model loading errors**:
   - Ensure sufficient RAM (4GB+ recommended)
   - Check HuggingFace Hub access
   - Verify `USE_ONNX_BACKEND` setting

---

## Implementation Guides

The `implementation_guides/` directory contains detailed documentation for specific features and improvements. These guides are valuable references for understanding implementation details and future development plans.

### Available Guides

1. **WEBSOCKET_IMPLEMENTATION_PLAN.md**

   - WebSocket integration for real-time audio processing
   - Connection manager implementation
   - Transport abstraction layer
   - ✅ Completed

2. **client-side-phoneme-extraction.md**

   - Browser-based ML inference using Transformers.js
   - Hybrid processing pipeline
   - Performance optimizations
   - ✅ Completed

3. **client-side-word-extraction.md**

   - Word boundary detection in browser
   - Audio analysis utilities
   - Integration with phoneme extraction

4. **UI_MODERNIZATION_GUIDE.md**

   - Design system updates
   - Component library improvements
   - Accessibility enhancements

5. **TESTING_SUITE_IMPLEMENTATION_GUIDE.md**

   - Unit testing setup
   - Integration testing
   - E2E testing strategy

6. **USER_STATISTICS_ENDPOINT.md**

   - Analytics API design
   - Performance metrics tracking
   - Progress visualization

7. **WEBGPU_GUIDE.md**

   - WebGPU acceleration for ML inference
   - Browser compatibility considerations
   - Performance benchmarks

8. **BUG_FIX_IMPLEMENTATION_PLAN.md**
   - Known issues and fixes
   - Priority levels
   - Testing procedures

### Using Implementation Guides

When working on related features:

1. Read the relevant guide first
2. Check completion status (✅ or ⬜)
3. Follow implementation steps
4. Update guide if making changes
5. Mark sections complete as you go

---

## Key Concepts for LLM Agents

### 1. Phoneme vs. Grapheme

- **Phoneme**: The actual sound (e.g., /æ/ in "cat")
- **Grapheme**: The written letter(s) (e.g., "a" in "cat")
- The system works with phonemes (IPA notation) for pronunciation analysis

### 2. Phoneme Error Rate (PER)

- Metric similar to Word Error Rate (WER)
- Measures pronunciation accuracy at phoneme level
- Lower PER = better pronunciation
- Computed using Levenshtein distance

### 3. wav2vec2-TIMIT-IPA Model

- Pre-trained speech recognition model
- Outputs phonemes in IPA (International Phonetic Alphabet)
- Model: `speech31/wav2vec2-large-TIMIT-IPA`
- Used for phoneme extraction from audio

### 4. ONNX Runtime

- Optimized inference engine
- 2-3x faster than PyTorch for CPU inference
- Used by default in production
- Set via `USE_ONNX_BACKEND=true`

### 5. Hybrid Processing

- Combines client-side and server-side processing
- Client extracts phonemes (if capable)
- Server validates and completes analysis
- Reduces latency and server load

### 6. Practice Modes

Each mode implements `BaseMode` interface:

- `get_feedback_and_next_sentence()`: Core method
- Receives pronunciation analysis
- Calls GPT-4 with mode-specific prompts
- Returns feedback and next sentence

### 7. Session vs. Activity

- **Activity**: Template (e.g., "Unlimited Practice")
- **Session**: Instance of an activity for a user
- Session tracks progress within an activity
- Multiple users can have sessions for same activity

### 8. Feedback Entry

- Record of a single pronunciation attempt
- Contains:
  - Original sentence
  - Phoneme analysis (PER, alignments)
  - GPT response (feedback, next sentence)
- Used for progress tracking and analytics

### 9. WebSocket vs. SSE

- **WebSocket**: Bidirectional, persistent connection (preferred)
- **SSE**: Unidirectional, server-to-client streaming (fallback)
- Both use same backend processing logic
- Frontend abstracts via `AudioTransport` interface

### 10. Client-Side ML

- Optional feature (enabled per user)
- Runs Transformers.js in browser (WebAssembly)
- Models cached in IndexedDB
- Device capability detection prevents poor UX

---

## Future Development Roadmap

### Planned Features

- [ ] New practice modes (e.g., dialogue practice)
- [ ] Advanced analytics dashboard
- [ ] Achievement/badge system
- [ ] Multi-language support
- [ ] Parent/teacher dashboard
- [ ] Offline mode support
- [ ] Mobile app (React Native)
- [ ] Gamification elements
- [ ] Social features (leaderboards)

### Technical Improvements

- [ ] WebGPU acceleration
- [ ] Enhanced caching strategies
- [ ] Real-time collaboration features
- [ ] Advanced error recovery
- [ ] Improved model accuracy
- [ ] Reduced model size
- [ ] Better audio preprocessing

### Known Limitations

- Requires internet connection
- CPU-intensive processing (server-side)
- Limited to English language
- Phoneme extraction accuracy varies with background noise
- Client-side ML requires modern browsers

---

## Appendix

### Glossary

- **IPA**: International Phonetic Alphabet (standard phoneme notation)
- **PER**: Phoneme Error Rate (pronunciation accuracy metric)
- **WER**: Word Error Rate (similar to PER but for words)
- **TTS**: Text-to-Speech (audio generation from text)
- **STT**: Speech-to-Text (transcription of audio)
- **JWT**: JSON Web Token (authentication mechanism)
- **CORS**: Cross-Origin Resource Sharing (security policy)
- **SSE**: Server-Sent Events (streaming protocol)
- **ONNX**: Open Neural Network Exchange (optimized model format)
- **Alembic**: Database migration tool for SQLAlchemy

### Useful Commands

**Backend**:

```bash
# Start server
python main.py

# Run with auto-reload
uvicorn main:app --reload

# Generate migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Run tests
pytest tests/

# Install dependencies
pip install -r requirements.txt
```

**Frontend**:

```bash
# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint

# Install dependencies
npm install
```

**Docker**:

```bash
# Build and start containers
docker-compose up -d --build

# View logs
docker logs fastapi_backend -f

# Stop containers
docker-compose down

# Restart containers
docker-compose restart

# Execute command in container
docker exec -it fastapi_backend bash
```

### Important Files Reference

| File                                | Purpose                                      |
| ----------------------------------- | -------------------------------------------- |
| `backend/main.py`                   | FastAPI app entry point, router registration |
| `backend/core/phoneme_assistant.py` | Main orchestrator for audio analysis         |
| `backend/routers/ai.py`             | Audio processing endpoints, WebSocket        |
| `frontend/src/App.tsx`              | React app routing and structure              |
| `frontend/src/api.ts`               | Backend API client functions                 |
| `backend/models/*.py`               | Database ORM models                          |
| `backend/schemas/*.py`              | Pydantic validation schemas                  |
| `backend/requirements.txt`          | Python dependencies                          |
| `frontend/package.json`             | Node.js dependencies                         |
| `backend/docker-compose.yml`        | Container orchestration                      |
| `.gitignore`                        | Files excluded from Git                      |

### Contact & Support

For questions or issues, refer to:

- Main README: `README.md`
- Implementation guides: `implementation_guides/`
- API documentation: http://localhost:8000/docs (when running)
- Style guidelines: `frontend/STYLE_GUIDELINES.md`

---

**End of Repository Guide**

_This guide is maintained for LLM agents and developers to quickly understand the Word Wiz AI codebase. Keep it updated as the project evolves._
