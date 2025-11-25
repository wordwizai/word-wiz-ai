# WebSocket Implementation Plan

## Problem Statement

Current SSE (Server-Sent Events) implementation has 5-second connection overhead on every audio analysis request. This causes poor UX as users wait for connection establishment before processing even begins.

## Solution

Replace SSE with persistent WebSocket connections that remain open throughout the user's session, eliminating reconnection overhead.

## Benefits

- **Eliminate 5s connection delay** - WebSocket stays open, reused for multiple requests
- **Bidirectional communication** - Can send real-time progress, cancel requests
- **Lower latency** - No HTTP overhead per request
- **Better UX** - Near-instant response to user actions

---

## Phase 1: Backend WebSocket Endpoint

**Goal:** Add WebSocket endpoint to existing `ai.py` router (no breaking changes)

### Tasks

- [ ] Add WebSocket endpoint `@router.websocket("/ws/audio-analysis")` in `routers/ai.py`
- [ ] Add simple connection manager class at top of `ai.py` to track active connections per user
- [ ] Extract auth token from WebSocket query params/headers
- [ ] Handle message types: `analyze_audio`, `ping/pong` (heartbeat)
- [ ] Reuse existing `process_audio_analysis()` helper but accept bytes directly
- [ ] Stream results back through WebSocket as JSON (same format as SSE events)

### Quality Assurance

- [ ] WebSocket connects successfully with valid auth token
- [ ] WebSocket rejects connection with invalid/missing token
- [ ] Audio processing produces identical results to SSE endpoint
- [ ] Multiple requests through same WebSocket work correctly
- [ ] Connection closes gracefully on disconnect
- [ ] Error messages sent properly through WebSocket

---

## Phase 2: Frontend Transport Abstraction Layer

**Goal:** Create abstraction so WebSocket/SSE are interchangeable without changing calling code

### Tasks

- [ ] Create `frontend/src/services/audioTransport.ts` with interface:
  - `connect(options)` - establish connection
  - `sendAudio(file, sentence, clientPhonemes, clientWords)` - send request
  - `onEvent(callback)` - register event handler
  - `disconnect()` - close connection
- [ ] Implement `WebSocketTransport` class in same file:
  - Establish WebSocket on first `connect()` call
  - Keep connection open, reuse for multiple `sendAudio()` calls
  - Convert File to base64 before sending
  - Handle incoming JSON messages, emit through `onEvent()`
  - Implement ping/pong heartbeat (every 30s)
  - Auto-reconnect on disconnect (exponential backoff)
- [ ] Implement `SSETransport` class (wraps existing `useAudioAnalysisStream` logic):
  - Create new SSE connection per `sendAudio()` call
  - Parse SSE events, emit through `onEvent()`
  - Match WebSocket interface exactly
- [ ] Update `useHybridAudioAnalysis` to use transport abstraction:
  - Select transport based on `USE_WEBSOCKET` setting
  - Replace direct `audioAnalysisStream.start()` calls with `transport.sendAudio()`
  - Keep all other logic unchanged (client extraction, validation, etc.)

### Quality Assurance

- [ ] `useHybridAudioAnalysis` works identically with both transports
- [ ] Switching transports requires only changing one setting
- [ ] WebSocket connection established once per session
- [ ] SSE fallback works if WebSocket disabled/fails
- [ ] All event types handled correctly (analysis, GPT response, audio feedback)
- [ ] Connection cleaned up properly on unmount
- [ ] No memory leaks from unclosed connections

---

## Phase 3: Integration & Migration

**Goal:** Switch from SSE to WebSocket with feature flag

### Tasks

- [ ] Add `use_websocket: boolean` to user settings (default: false)
- [ ] Add toggle in settings UI (or use environment variable for testing)
- [ ] Transport selection happens automatically in `useHybridAudioAnalysis` based on setting
- [ ] Test with WebSocket disabled (SSE fallback) - verify identical behavior
- [ ] Test with WebSocket enabled - verify connection reuse across multiple recordings
- [ ] Monitor connection stability in dev/staging
- [ ] Gradually roll out to users (10% → 50% → 100%)

### Quality Assurance

- [ ] SSE works exactly as before when WebSocket disabled
- [ ] WebSocket works for full user flow (multiple recordings without reconnecting)
- [ ] No errors when switching between practice sessions
- [ ] Performance improvement measured (5s → <500ms for 2nd+ requests)
- [ ] Error rates comparable to SSE implementation
- [ ] User can toggle setting and see immediate effect

---

## Phase 4: Cleanup (After successful rollout)

**Goal:** Remove SSE code once WebSocket proven stable (optional)

### Tasks

- [ ] Remove `SSETransport` class from `audioTransport.ts`
- [ ] Remove SSE endpoints from `ai.py` router
- [ ] Remove transport selection logic (always use WebSocket)
- [ ] Update documentation

### Quality Assurance

- [ ] All tests pass
- [ ] No references to removed SSE code
- [ ] Production monitoring shows stable performance

**Note:** Consider keeping SSE as fallback indefinitely for maximum compatibility

---

## Implementation Notes

### 80/20 Approach

**Focus on:**

- ✅ Transport abstraction layer - makes WebSocket/SSE interchangeable
- ✅ WebSocket endpoint in existing `ai.py` router (no new files)
- ✅ Single WebSocket per user (simple connection management)
- ✅ Reuse existing `analyze_audio_file_event_stream` (no rewrite)
- ✅ Basic reconnection logic (exponential backoff)
- ✅ Graceful fallback to SSE if WebSocket fails

**Skip for now:**

- ❌ Separate WebSocket router file (keep it simple, add to `ai.py`)
- ❌ Complex load balancing across WebSocket servers
- ❌ Redis pub/sub for multi-server WebSocket support
- ❌ Advanced reconnection strategies (jitter, circuit breaker)
- ❌ WebSocket compression (marginal benefit)
- ❌ Custom binary protocol (JSON is fine)

### Key Design Decisions

1. **Transport abstraction** - `useHybridAudioAnalysis` doesn't know/care about WebSocket vs SSE
2. **WebSocket in `ai.py`** - Keep related code together, no new router files
3. **One WebSocket per user session** - Simple, sufficient for our scale
4. **Reuse existing processing pipeline** - Convert SSE events to WebSocket messages
5. **Feature flag rollout** - Keep SSE as fallback during migration
6. **Base64 audio encoding** - Simple, works in JSON, good enough for our file sizes

### Risk Mitigation

- Keep SSE endpoint active as fallback
- Feature flag to disable WebSocket if issues arise
- Monitor error rates and connection stability
- Gradual rollout to catch issues early

### Success Metrics

- ✅ Connection time: 5s → <500ms
- ✅ Error rate: ≤ current SSE error rate
- ✅ User satisfaction: Faster perceived performance
- ✅ Connection stability: >95% of connections stay open entire session

---

## Timeline

- **Phase 1:** 1-2 hours (backend endpoint)
- **Phase 2:** 1-2 hours (frontend hook)
- **Phase 3:** 1 hour (integration + testing)
- **Phase 4:** 30 minutes (cleanup after 1-2 weeks stable operation)

**Total:** ~4-6 hours implementation + 1-2 weeks monitoring
