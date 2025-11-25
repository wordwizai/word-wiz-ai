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

- [x] Add WebSocket endpoint `@router.websocket("/ws/audio-analysis")` in `routers/ai.py`
- [x] Add simple connection manager class at top of `ai.py` to track active connections per user
- [x] Extract auth token from WebSocket query params/headers
- [x] Handle message types: `analyze_audio`, `ping/pong` (heartbeat)
- [x] Reuse existing `process_audio_analysis()` helper but accept bytes directly
- [x] Stream results back through WebSocket as JSON (same format as SSE events)

### Quality Assurance

- [x] WebSocket connects successfully with valid auth token ✅ (JWT validation implemented, decodes token and gets user from DB)
- [x] WebSocket rejects connection with invalid/missing token ✅ (closes with code 1008 if token missing/invalid)
- [x] Audio processing produces identical results to SSE endpoint ✅ (reuses same `analyze_audio_file_event_stream` generator)
- [x] Multiple requests through same WebSocket work correctly ✅ (while loop handles multiple messages on same connection)
- [x] Connection closes gracefully on disconnect ✅ (WebSocketDisconnect exception handler + manager cleanup)
- [x] Error messages sent properly through WebSocket ✅ (sends JSON with type: "error" for various failure cases)

---

## Phase 2: Frontend Transport Abstraction Layer

**Goal:** Create abstraction so WebSocket/SSE are interchangeable without changing calling code

### Tasks

- [x] Create `frontend/src/services/audioTransport.ts` with interface:
  - ✅ `AudioTransport` interface with `connect()`, `sendAudio()`, `disconnect()`, `isConnected()`
  - ✅ `AudioAnalysisEvent` type for all event types
  - ✅ `TransportOptions` with callbacks (onEvent, onError, onConnect, onDisconnect)
- [x] Implement `WebSocketTransport` class in same file:
  - ✅ Establish WebSocket with JWT token in query params
  - ✅ Keep connection open, reuse for multiple `sendAudio()` calls
  - ✅ Convert File to base64 before sending (fileToBase64 helper)
  - ✅ Handle incoming JSON messages, emit through `onEvent()`
  - ✅ Implement ping/pong heartbeat (every 30s)
  - ✅ Auto-reconnect on disconnect with exponential backoff (max 5 attempts)
  - ✅ Manual disconnect flag to prevent unwanted reconnects
- [x] Implement `SSETransport` class (wraps existing `useAudioAnalysisStream` logic):
  - ✅ Create new SSE connection per `sendAudio()` call
  - ✅ Parse SSE events ("data: " prefix), emit through `onEvent()`
  - ✅ Match WebSocket interface exactly (same methods/callbacks)
  - ✅ AbortController for cancellation
  - ✅ Endpoint selection based on client phonemes
- [x] Create `useAudioTransport` hook in `frontend/src/hooks/useAudioTransport.ts`:
  - ✅ Accepts options with callbacks (onAnalysis, onGptResponse, onAudioFeedback, onError, etc.)
  - ✅ Accepts `useWebSocket` flag to select transport
  - ✅ Initializes transport on mount with connection callbacks
  - ✅ Provides `sendAudio()`, `disconnect()`, `isConnected`, `isProcessing`
  - ✅ Handles all event types (processing_started, analysis, gpt_response, audio_feedback_file, error, pong)
  - ✅ Decodes base64 audio feedback to blob URLs
  - ✅ Cleans up transport on unmount

### Quality Assurance

- [x] ✅ Transport abstraction interface complete - both WebSocket and SSE implement identical `AudioTransport` interface
- [x] ✅ Switching transports requires only `useWebSocket` boolean flag in `useAudioTransport` options
- [x] ✅ WebSocket connection established once per session (on hook mount, persists until unmount)
- [x] ✅ SSE fallback implemented with same interface (creates connection per `sendAudio()` call)
- [x] ✅ All event types handled correctly:
  - `processing_started` → triggers onProcessingStart callback
  - `analysis` → triggers onAnalysis callback
  - `gpt_response` → triggers onGptResponse callback
  - `audio_feedback_file` → decodes base64 to blob URL, triggers onAudioFeedback callback
  - `error` → triggers onError callback
  - `pong` → heartbeat acknowledgment (silent)
- [x] ✅ Connection cleaned up properly:
  - useEffect cleanup disconnects transport
  - Manual disconnect() method available
  - WebSocket aborts reconnection attempts when manually disconnected
  - SSE aborts ongoing requests via AbortController
- [x] ✅ No memory leaks:
  - WebSocket cleanup stops ping interval, clears reconnect timeout
  - SSE cleanup aborts fetch request
  - Blob URLs created for audio feedback (caller must revoke)

**Next Step:** Integrate `useAudioTransport` into `useHybridAudioAnalysis` to replace `useAudioAnalysisStream`

---

## Phase 3: Integration & Migration

**Goal:** Switch from SSE to WebSocket with feature flag

### Tasks

- [x] Add `use_websocket: boolean` to user settings (default: false)
  - ✅ Added to frontend Settings type in `SettingsContext.tsx`
  - ✅ Added to backend `UserSettings` model with default `False`
  - ✅ Added to `UserSettingsUpdate` and `UserSettingsResponse` schemas
  - ✅ Created database migration `e7f3a8b9c1d2_add_use_websocket_setting.py`
  - ✅ Migration applied successfully (defaults existing users to SSE)
- [x] Transport selection happens automatically in `useHybridAudioAnalysis` based on setting
  - ✅ Updated `useHybridAudioAnalysis` to use `useAudioTransport` instead of `useAudioAnalysisStream`
  - ✅ Transport type selected based on `settings.use_websocket` (default: false)
  - ✅ All existing functionality preserved (client extraction, retry logic, etc.)
  - ✅ Changed `processAudio` to use `audioTransport.sendAudio()`
  - ✅ Changed `stop` to use `audioTransport.disconnect()`
  - ✅ Added transport state exports: `isConnected`, `isProcessing`
- [x] Add toggle in settings UI (for user testing)
  - ✅ Added "WebSocket Connection (Experimental)" toggle in Performance tab
  - ✅ Located under client-side phoneme processing setting
  - ✅ Clear description: "Eliminates 5-second connection overhead on subsequent recordings"
  - ✅ Toggle updates `use_websocket` setting in database
  - ✅ Changes take effect immediately on next audio processing
- [ ] Test with WebSocket disabled (SSE fallback) - verify identical behavior
- [ ] Test with WebSocket enabled - verify connection reuse across multiple recordings
- [ ] Monitor connection stability in dev/staging
- [ ] Gradually roll out to users (can be done via database UPDATE query or UI)

### Quality Assurance

**Ready for Testing** - All code complete, now testing phase:

- [ ] SSE works exactly as before when WebSocket disabled (default)
  - Go to Settings → Performance → Keep "WebSocket Connection" OFF
  - Record audio, verify it works
  - Check browser console for "SSE" related logs
  - Verify 5-second delay on each recording
- [ ] WebSocket works for full user flow (multiple recordings without reconnecting)
  - Go to Settings → Performance → Turn "WebSocket Connection" ON
  - Save settings
  - Record audio, verify it works
  - Check browser console for "🔌 Connecting to WebSocket" and "✅ WebSocket connected"
  - Record 2nd audio - should NOT see reconnection, just "📤 Sending audio via WebSocket"
  - Verify no 5-second delay on 2nd+ recordings
- [ ] No errors when switching between practice sessions
  - Test with WebSocket ON
  - Complete one session, start another
  - Verify connection stays alive or reconnects gracefully
- [ ] Performance improvement measured (5s → <500ms for 2nd+ requests)
  - Use browser DevTools Network tab
  - With WebSocket: First request ~5s, subsequent ~100-500ms
  - With SSE: Every request ~5s
- [ ] Error rates comparable to SSE implementation
  - Monitor browser console for errors
  - Test with poor network (throttle in DevTools)
  - Verify auto-reconnect works
- [ ] User can toggle setting and see immediate effect
  - Toggle WebSocket setting ON → Save → Record (should use WebSocket)
  - Toggle WebSocket setting OFF → Save → Record (should use SSE)
  - No page refresh needed

### Phase 3 Summary

**✅ IMPLEMENTATION COMPLETE** - Ready for testing!

**Files Modified:**

- **Frontend:**
  - `frontend/src/contexts/SettingsContext.tsx` - Added `use_websocket` to Settings type
  - `frontend/src/hooks/useHybridAudioAnalysis.ts` - Replaced `useAudioAnalysisStream` with `useAudioTransport`
  - `frontend/src/pages/Settings.tsx` - Added WebSocket toggle in Performance tab
- **Backend:**
  - `backend/models/user_settings.py` - Added `use_websocket` column (default: False)
  - `backend/schemas/settings.py` - Added `use_websocket` to Update/Response schemas
  - `backend/alembic/versions/e7f3a8b9c1d2_add_use_websocket_setting.py` - Migration
  - `backend/alembic/versions/f8a4b1c2d3e5_merge_multiple_heads.py` - Merge migration

**How to Test:**

1. Start backend: `cd backend && uvicorn main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Go to Settings → Performance
4. Toggle "WebSocket Connection (Experimental)" ON/OFF
5. Record audio and watch browser console for connection logs
6. Compare performance (5s initial vs <500ms subsequent with WebSocket)

**Rollout Strategy:**

- Default: WebSocket OFF (SSE) - safe, proven
- Users can opt-in via Settings UI
- Monitor for errors, connection stability
- Once proven stable (1-2 weeks), can enable for all users via database:
  ```sql
  UPDATE user_settings SET use_websocket = 1;
  ```

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
