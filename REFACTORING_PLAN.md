# Word Wiz AI - Refactoring & Optimization Plan

> Generated from a comprehensive audit of the full codebase (backend, frontend, infrastructure).
> Phases are ordered by priority: security-critical items first, then structural improvements, then optimizations.

---

## Phase 1: Critical Security & Configuration Hardening

**Goal**: Eliminate active security vulnerabilities and harden production configuration.

### 1.1 Production Configuration Fixes ✅ COMPLETE

- [x] **Disable debug mode** in `backend/main.py:12` — change `FastAPI(debug=True)` to read from environment variable: `debug=os.getenv("DEBUG", "false").lower() == "true"`
- [x] **Tighten CORS** in `backend/main.py:14-23` — restrict `allow_methods` from `["*"]` to `["GET", "POST", "PUT", "OPTIONS"]` and `allow_headers` from `["*"]` to `["Content-Type", "Authorization"]`
- [x] **Reduce JWT expiration** in `backend/auth/auth_handler.py` — change `JWT_EXPIRATION_MINUTES = 43200` (30 days) to a shorter window (e.g., 1440 = 1 day) and implement refresh token rotation
- [x] **Enable nginx SSL verification** — change `proxy_ssl_verify off` to `on` in `backend/nginx/nginx.conf`
- [x] **Parameterize SSL cert paths** in `backend/Dockerfile` — replace hardcoded `/etc/letsencrypt/live/api.wordwizai.com/` with environment variables
- [x] **Validate DATABASE_URL** in `backend/database.py` — raise an error if not set instead of falling back to empty string

### QA Checks

- [ ] Test that `debug=False` hides stack traces from API error responses
- [ ] Verify CORS restrictions don't break frontend requests (test from `wordwizai.com` and `localhost:5173`)
- [ ] Confirm JWT tokens expire at the new shorter window
- [ ] Run full application smoke test after all changes

---

## Phase 2: Backend Architecture — Break Up Monoliths

**Goal**: Split oversized files into focused modules with clear responsibilities. No behavior changes.

### 2.1 Split `core/process_audio.py` (777 lines → 4 modules) ✅ COMPLETE

This is the largest and most complex backend file, mixing alignment algorithms, PER calculation, and orchestration.

- [x] Extract `core/phoneme_alignment.py` — move `align_phonemes_to_words()` (lines 52-254), `_fallback_proportional_alignment()` (lines 257-310), and `_process_word_alignment()` (lines 366-466)
- [x] Extract `core/per_calculator.py` — move `compute_per()` (lines 14-50) and `align_sequences()` (lines 313-364)
- [x] Extract `core/audio_analysis.py` — move `analyze_results()` and result formatting logic
- [x] Keep `core/process_audio.py` as a thin orchestrator (~100-150 lines) that imports from the above modules
- [x] Add docstrings to the `align_sequences()` function (currently has "don't touch this, it's a black box" comment at line 321) — document inputs, outputs, and algorithm

### 2.2 Split `routers/ai.py` (430 lines → router + services) ✅ COMPLETE

Business logic is currently mixed into the route handler.

- [x] Extract `services/websocket_manager.py` — move `ConnectionManager` class (lines 29-50)
- [x] Extract `services/mode_factory.py` — move `get_activity_object()` (lines 82-106) and add a registry pattern instead of hardcoded `if/elif` chain
- [x] Extract `services/audio_analysis_service.py` — move `process_audio_analysis()` orchestration logic (lines 108-152)
- [x] Extract `core/validators.py` — consolidated validation logic
- [x] Keep `routers/ai.py` as thin endpoint definitions (~300 lines with WebSocket handler)
- [ ] Replace global singleton `phoneme_assistant = PhonemeAssistant()` (line 25) with FastAPI dependency injection (deferred)

### 2.3 Refactor `core/phoneme_assistant.py` (429 lines → focused classes) ✅ COMPLETE

This file is a "god object" handling device setup, model management, GPT interaction, and audio encoding.

- [x] Remove 50+ lines of dead code (commented-out `get_gpt_feedback()` method at lines 191-243)
- [x] Extract `core/gpt_client.py` — move `query_gpt()` and `extract_json()` methods; make GPT model name configurable instead of hardcoded `"gpt-4o-mini"`
- [x] Extract `core/prompt_manager.py` — move `load_prompt()` with prompt caching (currently re-reads files on every request)
- [x] Extract `core/audio_encoder.py` — move `feedback_to_audio()` (lines 298-393) which handles MP3-to-WAV conversion, resampling, normalization, and base64 encoding
- [x] Keep `core/phoneme_assistant.py` as pipeline orchestrator (~220 lines)

### 2.4 Clean Up `routers/handlers/audio_processing_handler.py` (400+ lines) ✅ COMPLETE

- [x] Create a `dataclass` context object for the 8+ parameter signature of `analyze_audio_file_event_stream()`
- [ ] Extract audio loading/decoding (lines 33-99) into `core/audio_loader.py` (deferred)
- [ ] Consolidate scattered audio caching (3 cache points at lines 75-89, 117-134, 193-210) into a single `services/audio_cache_service.py` (deferred)

### QA Checks

- [ ] All existing tests pass without modification (`python -m tests.analysis.run_analysis_tests`, `python -m tests.extraction.run_extraction_tests`)
- [ ] No circular imports — verify with `python -c "from routers.ai import router"` and similar
- [ ] WebSocket audio analysis still works end-to-end (test with frontend)
- [ ] SSE fallback still works end-to-end
- [ ] No regressions in phoneme alignment accuracy (run analysis tests, compare PER values)

---

## Phase 3: Backend Code Quality & Consistency

**Goal**: Eliminate duplication, standardize error handling, and improve maintainability.

### 3.1 Consolidate Duplicated Code ✅ MOSTLY COMPLETE

- [x] **JSON/phoneme validation** — three different `validate_client_phonemes()` implementations exist (`routers/ai.py:53-80`, `routers/handlers/phoneme_processing_handler.py:17-71`, `routers/handlers/audio_processing_handler.py:305-342`). Consolidated into `core/validators.py` module in Phase 2.2
- [x] **SSML tag detection** — identical `_contains_ssml_tags()` method in both TTS classes within `core/text_to_audio.py`. Extracted to `core/text_utils.py` as `contains_ssml_tags()` function (32 lines)
- [ ] **Audio quality validation** — inconsistent thresholds and error handling between `routers/handlers/audio_processing_handler.py:136-185` and `core/audio_preprocessing.py:39-46`. Create a single `services/audio_validation_service.py` with configurable strictness

### 3.2 Standardize Error Handling

- [x] Create a domain exception hierarchy in `core/exceptions.py`:
  - `AudioValidationError` (replaces HTTPException in non-HTTP contexts)
  - `PhonemeExtractionError`
  - `AlignmentError`
  - `GPTResponseError`
  - `AudioEncodingError`
  - `WordExtractionError`
  - `ValidationError`
- [x] Created `core/logging_config.py` with centralized logging setup
- [x] Replace `print()` with logging in critical production files:
  - ✅ `routers/ai.py` (18 occurrences)
  - ✅ `core/phoneme_assistant.py` (15 occurrences)
  - ✅ `services/websocket_manager.py` (2 occurrences)
  - ✅ Added logging initialization to `main.py`
- [ ] Replace remaining `print()` statements (~165 remaining in other core modules and handlers)
- [ ] Add structured error codes to WebSocket error messages (currently just string messages, making client-side handling difficult)
- [ ] Fix silent failures:
  - `core/process_audio.py:174-223`: alignment fallback silently returns garbage data — should raise or flag low-confidence results
  - `core/word_extractor.py:86-150`: API failures return empty list instead of raising — callers can't distinguish "no speech" from "API error"

### 3.3 Add Type Hints

- [ ] Add return type annotations to all public functions in `core/process_audio.py` (e.g., `align_phonemes_to_words` returns `list[tuple[str, list[str], float]]`)
- [ ] Add return type annotations to all public functions in `core/phoneme_assistant.py`
- [ ] Add type hints to `routers/handlers/audio_processing_handler.py` (e.g., `sanitize(obj)` at line 215 has no type annotations)
- [ ] Replace bare `list` annotations with typed versions (e.g., `list` → `list[str]`)

### 3.4 Reorganize Audio Processing Modules

Currently 7 audio-related files are scattered in `core/` with overlapping concerns:

- [ ] Create `core/audio/` package with `__init__.py`
- [ ] Move and rename:
  - `audio_preprocessing.py` → `core/audio/preprocessor.py`
  - `audio_quality_analyzer.py` → `core/audio/quality.py`
  - `audio_chunking.py` → `core/audio/chunker.py`
  - `adaptive_noise_reduction.py` → `core/audio/noise_reduction.py`
  - `audio_validation.py` → merge into `core/audio/quality.py`
  - `audio_optimization.py` → merge into config or remove if unused
  - `phoneme_aware_trimming.py` → merge into `core/audio/preprocessor.py` or remove if unused
- [ ] Update all imports across the codebase

### 3.5 Miscellaneous Cleanup

- [x] Remove commented-out test code in `core/text_to_audio.py:87-91`
- [ ] Add timeout to WebSocket receive in `routers/ai.py:320` (`data = await websocket.receive_json()` has no timeout — server waits indefinitely if client sends nothing)
- [ ] Add exponential backoff to Deepgram API retries in `core/word_extractor.py:86-150` (currently retries with no backoff)
- [ ] Add retry logic with backoff to GPT API calls in `core/phoneme_assistant.py` `query_gpt()` (currently no retry)

### QA Checks (Phase 3)

- [ ] All tests pass
- [ ] Run `mypy` or `pyright` on modified files to verify type annotations are correct
- [ ] Verify logging works correctly - check that INFO/DEBUG/WARNING/ERROR logs appear as expected
- [ ] ~165 print() statements remaining in backend (critical files done, handlers and core modules remaining)
- [ ] Error responses from WebSocket include error codes (test with a deliberately invalid request)
- [ ] Verify audio quality validation behaves consistently (same thresholds in all code paths)

---

## Phase 4: Frontend — Eliminate SEO Page Duplication

**Goal**: Reduce ~7,300 lines of 95% duplicated SEO page code to ~1,000 lines using a data-driven approach.

### 4.1 Convert SEO Pages to Data-Driven Architecture ⚙️ IN PROGRESS

Currently 40 separate component files (13 comparisons, 9 articles, 18 guides) each contain identical boilerplate with only data differences.

- [x] Create `src/data/comparisons/` directory with TypeScript data files
- [x] Create `src/data/articles/` directory
- [x] Create `src/data/guides/` directory
- [x] Create `src/data/seoPageTypes.ts` with TypeScript interfaces for page data
- [x] Create `src/pages/ComparisonPage.tsx` — a single component that loads data by slug from route params
- [x] Create `src/data/comparisons/index.ts` — registry for all comparison pages
- [x] Convert first comparison page (`free-vs-paid.ts`) as proof of concept
- [ ] Convert remaining 12 comparison pages to data files
- [ ] Convert 9 article pages to data files
- [ ] Create `src/pages/ArticlePage.tsx` — a single component that loads data by slug
- [ ] Create `src/pages/GuidePage.tsx` — a single component that loads data by slug
- [ ] Delete all 40 individual SEO page component files after migration
- [ ] Update routing in `App.tsx` to use new generic components
- [ ] Update prerendering script (`frontend/scripts/prerender.mjs`) to read routes from data files instead of hardcoded list

### 4.2 Simplify Route Definitions

`App.tsx` is currently 387 lines with 40+ lazy imports and route definitions for SEO pages.

- [ ] Create `src/routes/seoRoutes.tsx` — auto-generate route definitions from data file manifests (comparison slugs, article slugs, guide slugs)
- [ ] Create `src/routes/protectedRoutes.tsx` — extract protected route definitions
- [ ] Create `src/routes/publicRoutes.tsx` — extract public route definitions
- [ ] Reduce `App.tsx` to ~50-80 lines (provider setup + route module imports)

### 4.3 Merge Duplicate Practice Components

`BasePractice.tsx` and `ChoiceStoryBasePractice.tsx` are ~95% identical.

- [ ] Merge into a single `BasePractice.tsx` with a configuration prop to handle the choice-story variant (sentence options vs. next button)
- [ ] Simplify `GenericPractice.tsx` (currently an unnecessary wrapper)

### QA Checks

- [ ] `npm run build` completes without errors
- [ ] All SEO pages render correctly at their URLs (spot-check 5 comparisons, 3 articles, 3 guides)
- [ ] Pre-rendering still works for all SEO routes (`npm run build:prerender`)
- [ ] Verify page metadata (title, description, canonical URL, OG tags) is correct on migrated pages
- [ ] Verify structured data (schema.org) is present if it was before
- [ ] Practice mode works for both unlimited and choice-story modes
- [ ] Bundle size decreased (compare `npm run build` output before/after)

---

## Phase 5: Frontend — State Management & Performance

**Goal**: Fix performance issues from missing memoization, reduce prop drilling, and improve state patterns.

### 5.1 Create Custom `useFetch` Hook

The same fetch/loading/error pattern is repeated 3+ times across Dashboard, ProgressDashboard, and ClassesPage.

- [ ] Create `src/hooks/useFetch.ts` — generic hook returning `{ data, loading, error, refetch }`
- [ ] Refactor `Dashboard.tsx` to use `useFetch` for session/activity loading
- [ ] Refactor `ProgressDashboard.tsx` to use `useFetch` for statistics loading
- [ ] Refactor `ClassesPage.tsx` to use `useFetch` for class data loading

### 5.2 Create Axios Interceptor

Authorization header is repeated in 25+ API functions in `src/api.ts`.

- [ ] Create an axios instance with `baseURL` and request interceptor that auto-attaches the auth token
- [ ] Add response interceptor for:
  - 401 responses → trigger logout or token refresh
  - 5xx responses → optional retry with backoff
- [ ] Refactor all 25+ API functions to use the axios instance (eliminates ~100 lines of repeated headers)
- [ ] Remove debug `console.log("Token:", token)` calls left in `api.ts:171-174`

### 5.3 Add Memoization

- [ ] Wrap `ActivitiesList` component with `React.memo()`
- [ ] Wrap `AnimatedProgressStat` (inline in `ProgressDashboard.tsx:27-52`) with `React.memo()` and extract to its own file
- [ ] Add `useCallback` to `onActivityClick` handler in `ActivitiesList.tsx`
- [ ] Wrap chart components (`SentencePersChart`, `PhonemeErrorsPieChart`) with `React.memo()`
- [ ] Use `useMemo` for derived data in Dashboard (e.g., filtered/sorted activity lists)

### 5.4 Reduce BasePractice State Explosion

`BasePractice.tsx` has 15+ `useState` calls.

- [ ] Convert to `useReducer` with a single state object and typed actions
- [ ] Extract audio recording concerns into a `useAudioRecorder` custom hook
- [ ] Extract analysis state management into a `useAnalysisState` custom hook

### 5.5 Split `useHybridAudioAnalysis` (300+ lines)

- [ ] Extract `src/hooks/useRetryWithBackoff.ts` — generic retry utility
- [ ] Extract model initialization into `usePhonemeExtraction` hook (or keep in existing `phonemeExtractor.ts` service)
- [ ] Keep `useHybridAudioAnalysis` as a thin orchestrator (~100 lines)

### QA Checks

- [ ] `npm run lint` passes
- [ ] No regressions in practice mode (test audio recording → analysis → feedback flow)
- [ ] Verify that Dashboard renders efficiently (React DevTools Profiler — no unnecessary re-renders of activity lists)
- [ ] ProgressDashboard chart components only re-render when data changes
- [ ] API calls include auth token automatically (test by logging in and making requests)
- [ ] 401 responses trigger appropriate behavior (logout or token refresh)

---

## Phase 6: Frontend — TypeScript & Error Handling

**Goal**: Improve type safety and add missing error handling infrastructure.

### 6.1 Fix TypeScript Issues

- [ ] Replace all `any` types in `src/api.ts` with proper interfaces:
  - `getCurrentSessionState` return type (line 138): define `SessionState` interface
  - `activity_settings` (line 22): replace `[key: string]: any` with a discriminated union by activity type
- [ ] Replace `data: any` in `AudioAnalysisEvent` (`src/hooks/useAudioTransport.ts:18`) with a discriminated union:
  ```typescript
  type AudioAnalysisEvent =
    | { type: "processing_started" }
    | { type: "analysis"; data: AnalysisData }
    | { type: "gpt_response"; data: GPTResponse }
    | { type: "audio_feedback_file"; data: AudioFeedbackData }
    | { type: "complete" }
    | { type: "error"; message: string }
  ```
- [ ] Add typed error handling — replace `catch (error)` with `catch (error: unknown)` and proper type narrowing
- [ ] Remove duplicate `Session`/`SessionData` interface definitions (defined in both `api.ts` and `Dashboard.tsx`)
- [ ] Add return types to all API functions in `api.ts` (e.g., `getActivities` should return `Promise<Activity[]>`)
- [ ] Replace `Record<string, unknown>` usage for activity objects with proper `Activity` type

### 6.2 Add Error Boundary

- [ ] Create `src/components/ErrorBoundary.tsx` — React error boundary with fallback UI and error reporting
- [ ] Wrap route content in App.tsx with `<ErrorBoundary>`
- [ ] Add specific error boundaries around:
  - Practice mode components (audio/ML failures should show recovery UI, not crash the page)
  - Dashboard data loading sections

### 6.3 Fix Incomplete Features

- [ ] `ProgressDashboard.tsx`: Replace hardcoded `value={87}` (Accuracy) and `value={15}` (Improvement) with values calculated from `statistics` data
- [ ] `Settings.tsx`: Either implement account deletion or change the button text to indicate the feature is not yet available without a broken dialog

### QA Checks

- [ ] `npm run lint` passes with no TypeScript errors
- [ ] Intentionally trigger a component error (e.g., corrupt API response) and verify ErrorBoundary catches it with recovery UI
- [ ] All API functions have explicit return types (inspect `api.ts`)
- [ ] No `any` types remain in `api.ts` or `useAudioTransport.ts`
- [ ] ProgressDashboard shows real calculated values instead of hardcoded ones

---

## Phase 7: Infrastructure & DevOps

**Goal**: Add CI/CD, improve deployment reliability, and set up monitoring.

### 7.1 CI/CD Pipeline

- [ ] Create `.github/workflows/ci.yml` with:
  - Backend: lint (flake8/ruff), type check (mypy), run tests (`python -m tests.analysis.run_analysis_tests`, etc.)
  - Frontend: lint (`npm run lint`), type check (`npx tsc --noEmit`), build (`npm run build`)
  - Trigger on: push to main, pull requests
- [ ] Add pre-commit hook (via `pre-commit` framework) to prevent:
  - `.env` files from being committed
  - Files with `console.log` debug statements
  - Large binary files

### 7.2 Dependency Management

- [ ] **Backend**: Pin all dependency versions in `requirements.txt` (currently `torch` has no version pin, `numpy<2.0.0` is the only constraint)
- [ ] **Frontend**: Remove `legacy-peer-deps=true` from `.npmrc` if possible, or document why it's needed
- [ ] Lower Vite `chunkSizeWarningLimit` from 1000KB to 500KB (default) in `vite.config.ts` to catch bundle bloat early

### 7.3 Logging & Monitoring

- [ ] Replace all `print()` statements with structured `logging` calls (overlaps with Phase 3.2 — ensure it's done by this point)
- [ ] Add a health check endpoint that tests database connectivity (current `/health/model-optimization` only reports config)
- [ ] Set `ENABLE_PERFORMANCE_LOGGING=false` in production (currently `true` in `backend/core/optimization_config.py`)
- [ ] Set `ENABLE_MODEL_CACHE=true` in production (currently `false` — models reloaded on each request)

### 7.4 Docker & Deployment

- [ ] Use Docker secrets or environment variables instead of mounting `.env` file in `docker-compose.yml`
- [ ] Add health check to Docker container definition
- [ ] Consider multi-stage Docker build to reduce image size (ensure dev dependencies like PyTorch dev tools aren't in production image)

### QA Checks

- [ ] CI pipeline runs successfully on a test PR
- [ ] Pre-commit hook blocks `.env` file commits (test by attempting to stage one)
- [ ] `pip install -r requirements.txt` installs exact pinned versions
- [ ] Health check endpoint returns database connectivity status
- [ ] Docker container starts and passes health check
- [ ] Production logs are structured (JSON format) and don't include debug-level performance logging

---

## Phase 8: Performance Optimization & Polish

**Goal**: Optimize runtime performance, reduce bundle size, and improve UX.

### 8.1 Backend Performance

- [ ] Add prompt caching to `load_prompt()` — currently re-reads prompt files from disk on every request (add `@lru_cache` or a simple dict cache)
- [ ] Add retry logic with exponential backoff to `query_gpt()` (currently fails on first API error)
- [ ] Add WebSocket receive timeout in `routers/ai.py:320` to prevent indefinite waiting
- [ ] Move `import librosa` and `import numpy` out of `feedback_to_audio()` function body (currently imported inside the function on every call)
- [ ] Improve JSON extraction in `extract_json()` — current greedy regex `\{.*\}` can merge multiple JSON objects; replace with balanced-brace matching

### 8.2 Frontend Bundle Optimization

- [ ] Lazy-load `@huggingface/transformers` — currently imported eagerly in `src/services/phonemeExtractor.ts`; should only load when client-side extraction is enabled and user starts recording
- [ ] Lazy-load recharts — only used in `ProgressDashboard`; use `React.lazy()` for chart components
- [ ] Audit bundle with `npx vite-bundle-visualizer` and identify largest chunks
- [ ] Verify tree-shaking is effective for Radix UI packages (9 packages installed)

### 8.3 UX Improvements

- [ ] Replace loading spinner (`PageLoader`) with skeleton screens for Dashboard and ProgressDashboard
- [ ] Add global unhandled promise rejection handler (`window.addEventListener("unhandledrejection", ...)`)
- [ ] Differentiate audio playback errors by type (NotAllowedError → "Please allow audio", NotSupportedError → "Format not supported")

### QA Checks

- [ ] Backend response times for audio analysis have not regressed (benchmark before/after)
- [ ] Frontend bundle size report shows reduction from baseline
- [ ] Lighthouse performance score is measured and documented
- [ ] No unhandled promise rejections in browser console during normal usage
- [ ] Loading states show skeleton screens instead of spinners

---

## Summary: Effort by Phase

| Phase | Focus | Scope | Risk |
|-------|-------|-------|------|
| **1** | Security & Config | Backend + Infra | High (must do first) |
| **2** | Backend Monolith Splitting | Backend | Medium (structural, no behavior change) |
| **3** | Backend Code Quality | Backend | Low-Medium (cleanup + consistency) |
| **4** | Frontend SEO Deduplication | Frontend | Medium (large file count change) |
| **5** | Frontend State & Performance | Frontend | Low (additive improvements) |
| **6** | Frontend TypeScript & Errors | Frontend | Low (type safety + error handling) |
| **7** | Infrastructure & DevOps | Infra | Low-Medium (new CI/CD pipeline) |
| **8** | Performance & Polish | Full Stack | Low (optimization pass) |

### Key Metrics to Track

| Metric | Current (est.) | Target |
|--------|---------------|--------|
| Backend `core/process_audio.py` | 777 lines | ~150 lines (orchestrator) |
| Backend `routers/ai.py` | 430 lines | ~60 lines (thin routes) |
| Frontend SEO page files | 40 files, ~7,300 lines | 3 template files + data |
| Frontend `App.tsx` | 387 lines | ~60 lines |
| `any` types in frontend | 15+ occurrences | 0 |
| Repeated auth header in `api.ts` | 25+ occurrences | 0 (interceptor) |
| `print()` in backend | 50+ occurrences | 0 (all converted to `logging`) |
| Exposed secrets in git | 9+ keys | 0 |
