# <img src="frontend/src/assets/wordwizIcon.svg" width="32"/> Word Wiz AI

**Word Wiz AI** is an AI-powered educational web application designed to help young children learn to read through **phoneme-level pronunciation feedback**. The application combines advanced speech recognition, natural language processing, and AI-generated content to provide precise, real-time guidance on pronunciation.

🌐 **Live Application**: [wordwizai.com](https://wordwizai.com)  
📚 **Detailed Documentation**: See [REPOSITORY_GUIDE.md](implementation_guides/REPOSITORY_GUIDE.md) for comprehensive technical documentation

---

## Table of Contents

- [✨ Key Features](#-key-features)
- [🏗️ Architecture](#️-architecture)
- [🛠️ Technology Stack](#️-technology-stack)
- [🚀 Quick Start](#-quick-start)
- [📖 Development Guide](#-development-guide)
- [🧪 Testing](#-testing)
- [🔑 Key Concepts](#-key-concepts)
- [📚 Documentation](#-documentation)
- [🚢 Deployment](#-deployment)
- [🗺️ Roadmap](#️-roadmap)
- [🤝 Contributing](#-contributing)

---

## ✨ Key Features

### Core Functionality
- 🎤 **Real-Time Phoneme-Level Feedback** — Analyzes pronunciation at the phoneme level using wav2vec2-TIMIT-IPA models with IPA (International Phonetic Alphabet) output
- 📊 **Phoneme Error Rate (PER)** — Computes accuracy metrics for each word and overall pronunciation
- 🤖 **AI-Generated Content** — GPT-4 generates contextually appropriate sentences and personalized feedback
- 🎯 **Adaptive Difficulty** — Content adjusts based on user performance and common error patterns

### Practice Modes
- 🔥 **Unlimited Practice** — Continuous practice with adaptive difficulty and varied sentences
- 📖 **Story Mode** — Guided reading through engaging, sequential narratives
- 🎭 **Choice Story Mode** — Interactive branching stories where users choose their path

### Technical Features
- ⚡ **Optimized Performance** — ONNX Runtime provides 2-3x faster inference than PyTorch
- 🌐 **WebSocket Support** — Real-time bidirectional communication for low-latency audio processing
- 💻 **Client-Side ML (Optional)** — Browser-based phoneme extraction using Transformers.js for capable devices
- 🔐 **Dual Authentication** — Username/password and Google OAuth integration
- 📈 **Progress Tracking** — Historical performance data, PER trends, and error pattern analysis
- 🎨 **Modern UI** — Built with Tailwind CSS, Radix UI primitives, and responsive design
- 🌓 **Theme Support** — Light and dark mode with customizable preferences

---

## 🏗️ Architecture

### System Overview

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
│  │              FastAPI Application                          │   │
│  │  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │   │
│  │  │   Routers   │  │  Auth/OAuth  │  │  WebSocket     │  │   │
│  │  │             │  │  (JWT)       │  │  Manager       │  │   │
│  │  └──────┬──────┘  └──────┬───────┘  └────────┬───────┘  │   │
│  └─────────┼─────────────────┼───────────────────┼──────────┘   │
│            │                 │                   │              │
│  ┌─────────▼─────────────────▼───────────────────▼──────────┐   │
│  │              Core Processing Layer                        │   │
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
│  │  (users, sessions, activities, feedback_entries)         │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
            │                                    │
            │ External APIs                      │
┌───────────▼──────────┐            ┌───────────▼──────────┐
│   OpenAI GPT-4 API   │            │  Google Cloud APIs   │
│  (Content & Feedback)│            │  (TTS, OAuth)        │
└──────────────────────┘            └──────────────────────┘
```

### Audio Analysis Pipeline

1. **User reads sentence** → Audio recorded in browser (MediaRecorder API)
2. **Audio sent** → Via WebSocket (primary) or SSE (fallback) to `/ai/ws/audio-analysis`
3. **Preprocessing** → Backend validates & preprocesses audio (16kHz, mono, noise reduction)
4. **Phoneme extraction** → ONNX Runtime extracts IPA phonemes (or uses client phonemes if provided)
5. **Word extraction** → Detect word boundaries via energy analysis
6. **Alignment** → Dynamic programming aligns phonemes to expected words
7. **PER calculation** → Compute Phoneme Error Rate per word & overall
8. **GPT feedback** → Mode-specific prompt → JSON response → TTS audio generation
9. **Results streamed back** → `processing_started` → `analysis` → `gpt_response` → `audio_feedback_file`

See [REPOSITORY_GUIDE.md](implementation_guides/REPOSITORY_GUIDE.md#data-flow) for detailed data flow diagrams.

---

## 🛠️ Technology Stack

### Frontend
- **Framework**: [React](https://react.dev/) 19.1.0 with TypeScript
- **Build Tool**: [Vite](https://vitejs.dev/) 7.0.2
- **Styling**: [Tailwind CSS](https://tailwindcss.com/) 4.1.11 ([Style Guidelines](frontend/STYLE_GUIDELINES.md))
- **UI Components**: [Radix UI](https://www.radix-ui.com/) primitives with [shadcn/ui](https://ui.shadcn.com/)
- **State Management**: React Context (Auth, Settings, Theme)
- **Routing**: [React Router DOM](https://reactrouter.com/) 7.6.3
- **HTTP Client**: [Axios](https://axios-http.com/) 1.10.0
- **ML (Optional)**: [@huggingface/transformers](https://huggingface.co/docs/transformers.js) 3.7.6
- **Deployment**: [Vercel](https://vercel.com/)

### Backend
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.12+)
- **Server**: Uvicorn + Gunicorn
- **Authentication**: PyJWT, python-jose, [Authlib](https://authlib.org/) (Google OAuth)
- **Database**: MySQL (production), SQLite (development)
- **ORM**: [SQLAlchemy](https://www.sqlalchemy.org/) with [Alembic](https://alembic.sqlalchemy.org/) migrations
- **ML/AI**:
  - [PyTorch](https://pytorch.org/) (CPU-optimized)
  - [ONNX Runtime](https://onnxruntime.ai/) (default, 2-3x faster)
  - [Transformers](https://huggingface.co/docs/transformers) 4.30.0+
  - [wav2vec2-TIMIT-IPA](https://huggingface.co/speech31/wav2vec2-large-TIMIT-IPA) (phoneme recognition)
- **Audio Processing**: librosa, soundfile, noisereduce
- **Text-to-Speech**: Google Cloud TTS, ElevenLabs
- **NLP**: OpenAI GPT-4 API, eng_to_ipa (grapheme-to-phoneme)
- **Deployment**: AWS EC2 with Docker, Nginx reverse proxy

### DevOps
- **Containerization**: Docker + Docker Compose
- **Web Server**: Nginx (reverse proxy, SSL termination)
- **SSL/TLS**: Let's Encrypt (Certbot)
- **CI/CD**: Git-based deployment

---

## 🚀 Quick Start

### Prerequisites
- **Backend**: Python 3.12+, pip
- **Frontend**: Node.js 18+, npm
- **API Keys**: OpenAI API key (required), Google Cloud credentials (optional for TTS)

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY and DATABASE_URL

# Run database migrations
alembic upgrade head

# Start development server
python main.py
# Server runs on http://localhost:8000
# API docs available at http://localhost:8000/docs
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Configure environment
# Create .env.local with:
# VITE_API_URL=http://localhost:8000
# VITE_WS_URL=ws://localhost:8000

# Start development server
npm run dev
# Open http://localhost:5173
```

See [Development Guide](#-development-guide) for detailed setup instructions.

---

## 📖 Development Guide

### Project Structure

```
word-wiz-ai/
├── backend/                      # FastAPI backend
│   ├── core/                     # Core processing logic
│   │   ├── modes/                # Practice mode implementations
│   │   ├── phoneme_assistant.py  # Main orchestrator
│   │   ├── phoneme_extractor*.py # Phoneme extraction (PyTorch/ONNX)
│   │   ├── word_extractor.py     # Word boundary detection
│   │   └── process_audio.py      # Audio analysis pipeline
│   ├── routers/                  # API endpoints
│   │   ├── ai.py                 # Audio analysis, WebSocket
│   │   ├── auth.py               # Authentication
│   │   └── ...
│   ├── models/                   # Database ORM models
│   ├── schemas/                  # Pydantic validation schemas
│   ├── tests/                    # Test suite
│   └── main.py                   # Application entry point
│
├── frontend/                     # React frontend
│   ├── src/
│   │   ├── components/           # UI components
│   │   │   ├── ui/               # Base components (shadcn/ui)
│   │   │   └── practice/         # Practice-specific components
│   │   ├── contexts/             # React Context providers
│   │   ├── hooks/                # Custom React hooks
│   │   ├── pages/                # Route components
│   │   ├── services/             # Business logic
│   │   └── api.ts                # Backend API client
│   └── STYLE_GUIDELINES.md       # Frontend coding standards
│
└── implementation_guides/        # Feature documentation
    ├── REPOSITORY_GUIDE.md       # Comprehensive technical guide
    ├── TESTING_SUITE_*.md        # Testing documentation
    └── ...                       # 40+ implementation guides
```

### Development Commands

**Backend:**
```bash
python main.py                    # Start dev server
uvicorn main:app --reload         # Auto-reload mode
alembic revision --autogenerate   # Generate migration
alembic upgrade head              # Apply migrations
pytest tests/                     # Run tests
```

**Frontend:**
```bash
npm run dev                       # Start dev server
npm run build                     # Production build
npm run preview                   # Preview production build
npm run lint                      # Lint code
```

### Key Development Patterns

#### Backend Structure
- **Routers** (`routers/`): API endpoints - `ai.py` handles WebSocket/audio, `auth.py` for JWT
- **Core processing** (`core/`): `phoneme_assistant.py` orchestrates pipeline
- **Practice modes** (`core/modes/`): Inherit from `BaseMode`, implement `get_feedback_and_next_sentence()`
- **GPT prompts** (`core/gpt_prompts/`): Versioned `.txt` files, auto-appends `ssml_instruction.txt`

#### Frontend Conventions
- **UI**: shadcn/ui + Radix primitives, follow [STYLE_GUIDELINES.md](frontend/STYLE_GUIDELINES.md)
- **State**: React Context (`AuthContext`, `SettingsContext`, `ThemeContext`)
- **API calls**: Centralized in `src/api.ts`
- **Audio transport**: `hooks/useAudioTransport.ts` abstracts WebSocket/SSE

### Adding a New Practice Mode

1. Create `backend/core/modes/my_mode.py` inheriting `BaseMode`
2. Implement `get_feedback_and_next_sentence(attempted_sentence, analysis, phoneme_assistant, session)`
3. Create GPT prompt in `core/gpt_prompts/my_mode_prompt_v1.txt`
4. Update `routers/ai.py` to route `activity_type` to new mode class
5. Add frontend component in `components/practice/` (or reuse `BasePractice.tsx`)

See [REPOSITORY_GUIDE.md - Common Patterns](implementation_guides/REPOSITORY_GUIDE.md#common-patterns) for more details.

---

## 🧪 Testing

### Test Suite Structure

The backend includes comprehensive test coverage across multiple layers:

```
backend/tests/
├── extraction/       # Phoneme extraction tests (audio → IPA phonemes)
├── analysis/         # Full pipeline tests (phonemes + sentence → PER)
├── gpt/              # GPT prompt/response validation tests
└── system/           # End-to-end tests with real audio files
```

Each test folder has a [README](backend/tests/README.md) with file format specifications.

### Running Tests

```bash
cd backend

# Run specific test suites
python -m tests.analysis.run_analysis_tests      # Analysis layer
python -m tests.extraction.run_extraction_tests  # Extraction layer
python -m tests.gpt.run_gpt_tests                # GPT integration
python -m tests.system.run_system_tests          # Full E2E

# Run all tests
pytest tests/
```

### Test Data Format

Tests use JSON files with expected inputs/outputs. Example (`tests/analysis/*.json`):

```json
{
  "sentence": "The cat sat.",
  "client_phonemes": [["ð", "ə"], ["k", "æ", "t"], ["s", "æ", "t"]],
  "expected_per": 0.0
}
```

See [TESTING_SUITE_IMPLEMENTATION_GUIDE.md](implementation_guides/TESTING_SUITE_IMPLEMENTATION_GUIDE.md) for comprehensive testing documentation.

---

## 🔑 Key Concepts

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

### WebSocket vs. SSE
- **WebSocket**: Bidirectional, persistent connection (preferred for low latency)
- **SSE**: Unidirectional, server-to-client streaming (fallback)
- Both use same backend processing logic
- Frontend abstracts via `AudioTransport` interface

---

## 📚 Documentation

### Core Documentation
- **[REPOSITORY_GUIDE.md](implementation_guides/REPOSITORY_GUIDE.md)** - Comprehensive technical documentation (1,900+ lines)
  - Architecture overview and data flow diagrams
  - Database schema and API endpoints
  - Core components and their responsibilities
  - Development workflows and best practices
- **[STYLE_GUIDELINES.md](frontend/STYLE_GUIDELINES.md)** - Frontend coding standards
  - Color palette and design system
  - Component styling patterns
  - Animation and responsive design
  - Accessibility considerations

### Implementation Guides (40+ Guides)

**Feature Implementation:**
- [WEBSOCKET_IMPLEMENTATION_PLAN.md](implementation_guides/WEBSOCKET_IMPLEMENTATION_PLAN.md) - Real-time communication ✅
- [client-side-phoneme-extraction.md](implementation_guides/client-side-phoneme-extraction.md) - Browser ML inference ✅
- [client-side-word-extraction.md](implementation_guides/client-side-word-extraction.md) - Client word detection
- [UI_MODERNIZATION_GUIDE.md](implementation_guides/UI_MODERNIZATION_GUIDE.md) - Design system updates
- [USER_STATISTICS_ENDPOINT.md](implementation_guides/USER_STATISTICS_ENDPOINT.md) - Analytics API

**Optimization:**
- [GPT_AND_TTS_OPTIMIZATION_GUIDE.md](implementation_guides/GPT_AND_TTS_OPTIMIZATION_GUIDE.md) - AI service optimization
- [CORE_WEB_VITALS_OPTIMIZATION.md](implementation_guides/CORE_WEB_VITALS_OPTIMIZATION.md) - Performance improvements
- [OPTIMIZATION_QUICK_START.md](implementation_guides/OPTIMIZATION_QUICK_START.md) - Performance best practices

**Testing:**
- [TESTING_SUITE_IMPLEMENTATION_GUIDE.md](implementation_guides/TESTING_SUITE_IMPLEMENTATION_GUIDE.md) - Test infrastructure
- [backend/tests/README.md](backend/tests/README.md) - Test suite structure
- Test-specific READMEs in each test folder

**Bug Fixes & Improvements:**
- [BUG_FIX_IMPLEMENTATION_PLAN.md](implementation_guides/BUG_FIX_IMPLEMENTATION_PLAN.md) - Known issues and fixes
- [PHONEME_EXTRACTION_ACCURACY_IMPROVEMENTS.md](implementation_guides/PHONEME_EXTRACTION_ACCURACY_IMPROVEMENTS.md) - Model accuracy
- [COMPLETE_FIX_SUMMARY.md](implementation_guides/COMPLETE_FIX_SUMMARY.md) - Recent fixes

**SEO & Content:**
- [SEO_EXECUTIVE_SUMMARY.md](implementation_guides/SEO_EXECUTIVE_SUMMARY.md) - SEO strategy overview
- [SEO_CONTENT_MASTER.md](implementation_guides/SEO_CONTENT_MASTER.md) - Content guidelines

**Features:**
- [STUDENT_INSIGHTS_AND_ACTIVITY_GUIDE.md](implementation_guides/STUDENT_INSIGHTS_AND_ACTIVITY_GUIDE.md) - Analytics features
- [TEACHER_STUDENT_CLASS_FEATURE.md](implementation_guides/TEACHER_STUDENT_CLASS_FEATURE.md) - Classroom management

### API Documentation
When running the backend, interactive API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🚢 Deployment

### Frontend (Vercel)
- **Domain**: [wordwizai.com](https://wordwizai.com)
- **Build Command**: `npm run build`
- **Output Directory**: `dist`
- **Environment Variables**: `VITE_API_URL`, `VITE_WS_URL`

### Backend (AWS EC2)
- **Domain**: api.wordwizai.com
- **Stack**: Docker + Docker Compose + Nginx
- **SSL**: Let's Encrypt (auto-renewed)
- **Database**: MySQL (production), SQLite (development)

**Deployment Process:**
```bash
# SSH into EC2 instance
ssh user@api.wordwizai.com

# Pull latest code
git pull origin main

# Rebuild containers
docker-compose up -d --build

# Nginx automatically reloads
```

### Environment Variables

**Backend (`.env`):**
```bash
DATABASE_URL=mysql+pymysql://user:pass@host/db
OPENAI_API_KEY=sk-...
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
SECRET_KEY=... (JWT signing key)
USE_ONNX_BACKEND=true
```

**Frontend (`.env.production`):**
```bash
VITE_API_URL=https://api.wordwizai.com
VITE_WS_URL=wss://api.wordwizai.com
```

See [REPOSITORY_GUIDE.md - Deployment](implementation_guides/REPOSITORY_GUIDE.md#deployment) for detailed deployment documentation.

---

## 🗺️ Roadmap

### ✅ Completed
- [X] Real-time speech input with phoneme feedback
- [X] Customizable difficulty for different reading levels
- [X] Quality frontend with modern UI
- [X] Three engaging practice modes (Unlimited, Story, Choice Story)
- [X] Production deployment on Vercel + AWS
- [X] WebSocket support for low-latency audio processing
- [X] ONNX Runtime integration (2-3x performance improvement)
- [X] Optional client-side ML inference

### 🚧 In Progress
- [ ] Advanced analytics dashboard
- [ ] Achievement/badge system
- [ ] Enhanced progress tracking visualizations

### 🔮 Future Plans
- [ ] New practice modes (dialogue practice, word families)
- [ ] Multi-language support (Spanish, French)
- [ ] Parent/teacher dashboard
- [ ] Offline mode support
- [ ] Mobile app (React Native)
- [ ] Gamification elements
- [ ] Social features (leaderboards, sharing)
- [ ] WebGPU acceleration for ML inference

### Known Limitations
- Requires internet connection
- CPU-intensive processing (server-side)
- Limited to English language
- Phoneme extraction accuracy varies with background noise
- Client-side ML requires modern browsers (4GB+ RAM, WebAssembly)

---

## 🤝 Contributing

Contributions are welcome! We appreciate your interest in improving Word Wiz AI.

### How to Contribute

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes** following our coding standards:
   - Backend: Follow FastAPI best practices
   - Frontend: Follow [STYLE_GUIDELINES.md](frontend/STYLE_GUIDELINES.md)
4. **Test your changes**: Run relevant test suites
5. **Commit your changes**: `git commit -m "Add feature: your feature description"`
6. **Push to your fork**: `git push origin feature/your-feature-name`
7. **Open a Pull Request** with a clear description of your changes

### Guidelines

- **Code Quality**: Maintain high code quality and follow existing patterns
- **Documentation**: Update relevant documentation (README, guides, code comments)
- **Testing**: Add tests for new features when applicable
- **Commit Messages**: Use clear, descriptive commit messages
- **Issues**: For major changes, open an issue first to discuss your proposal

### Development Resources

Before contributing, please review:
- [REPOSITORY_GUIDE.md](implementation_guides/REPOSITORY_GUIDE.md) - Technical architecture and patterns
- [Development Guide](#-development-guide) - Setup and workflow
- [Testing Guide](#-testing) - Test suite structure
- [STYLE_GUIDELINES.md](frontend/STYLE_GUIDELINES.md) - Frontend standards

### Getting Help

- Check existing documentation in `implementation_guides/`
- Review [API documentation](http://localhost:8000/docs) when backend is running
- Open an issue for questions or bug reports

---

## 📄 License

This project is part of an educational initiative to help children learn to read.

---

## 🙏 Acknowledgments

- **OpenAI** - GPT-4 for content generation and feedback
- **HuggingFace** - wav2vec2-TIMIT-IPA model and Transformers library
- **Google Cloud** - Text-to-Speech services
- **Radix UI** & **shadcn/ui** - Component primitives
- **FastAPI** & **React** - Core frameworks

---

## 📞 Contact & Support

- **Website**: [wordwizai.com](https://wordwizai.com)
- **Issues**: [GitHub Issues](https://github.com/wordwizai/word-wiz-ai/issues)
- **Documentation**: [implementation_guides/](implementation_guides/)

For detailed technical information, see [REPOSITORY_GUIDE.md](implementation_guides/REPOSITORY_GUIDE.md).

---

**Built with ❤️ to help children learn to read**
