"""Public "try it" analysis for visitors without an account.

A parent landing on a guide can have their child read a few practice
sentences out loud and get the same sound-level feedback signed-in users get,
before creating an account. Compared with /ai/analyze-audio this route:

- needs no login and writes nothing to the database,
- never stores the recording (cache_audio=False in preprocessing),
- skips the GPT next-sentence step (the page walks through fixed sentences),
- only scores sentences from the practice-word pages (data/phonics_patterns.json),
- is rate-limited per IP, capped site-wide per hour, and runs a limited
  number of analyses at once so guests can't starve signed-in users.
"""

import asyncio
import json

from core.guest_limits import SlidingWindowLimiter, client_ip, normalize_sentence
from core.phonics_data import all_patterns
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import StreamingResponse
from routers.handlers.audio_processing_handler import analyze_audio_guest_event_stream

router = APIRouter()

# 16 kHz mono 16-bit WAV is 32 KB/s, so 20 s of audio (the guest duration cap)
# is about 640 KB. 1.5 MB leaves room for other encoders without letting
# anyone upload long recordings.
MAX_AUDIO_BYTES = 1_500_000

# Per visitor: enough to read every sentence on a page a few times over.
PER_IP_BURST = SlidingWindowLimiter(limit=15, window_seconds=10 * 60)
PER_IP_DAILY = SlidingWindowLimiter(limit=60, window_seconds=24 * 60 * 60)
# Whole site: bounds the Deepgram/TTS bill if the limits above are dodged.
SITE_HOURLY = SlidingWindowLimiter(limit=400, window_seconds=60 * 60)

# The EC2 box has ~1.3 CPU for everything. Two guest analyses at a time keeps
# headroom for signed-in sessions; a guest waits up to QUEUE_WAIT_SECONDS for
# a slot before being told to try again.
GUEST_CONCURRENCY = 2
QUEUE_WAIT_SECONDS = 20
_guest_slots = asyncio.Semaphore(GUEST_CONCURRENCY)


def _load_allowed_sentences() -> set[str]:
    return {
        normalize_sentence(sentence)
        for pattern in all_patterns().values()
        for sentence in pattern["sentences"]
    }


ALLOWED_SENTENCES = _load_allowed_sentences()

_request_count = 0


def get_phoneme_assistant():
    """The one PhonemeAssistant the app already loaded.

    Imported lazily so this module (and its tests) don't load the ONNX model
    or need API keys at import time. Never construct a second one: memory is
    the binding limit on the server.
    """
    from routers.ai import phoneme_assistant

    return phoneme_assistant


async def _stream_with_slot(make_stream):
    """Run the analysis stream only while holding one of the guest slots.

    The slot is taken inside the generator, not before the response is
    returned. If the visitor disconnects before streaming starts, Starlette
    never runs the generator, so a slot taken up front would never be
    released and guest mode would stay "busy" until a restart.
    """
    try:
        await asyncio.wait_for(_guest_slots.acquire(), timeout=QUEUE_WAIT_SECONDS)
    except asyncio.TimeoutError:
        busy = {
            "type": "error",
            "data": {"message": "Try mode is very busy right now. Please try again in a moment."},
        }
        yield f"data: {json.dumps(busy)}\n\n"
        return
    try:
        async for chunk in make_stream():
            yield chunk
    finally:
        _guest_slots.release()


@router.post("/analyze-audio")
async def guest_analyze_audio(
    request: Request,
    attempted_sentence: str = Form(...),
    audio_file: UploadFile = File(...),
    phoneme_assistant=Depends(get_phoneme_assistant),
):
    """Analyze one practice sentence for a visitor without an account (SSE)."""
    global _request_count

    if normalize_sentence(attempted_sentence) not in ALLOWED_SENTENCES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="That sentence isn't available in try mode.",
        )

    audio_bytes = await audio_file.read(MAX_AUDIO_BYTES + 1)
    if len(audio_bytes) > MAX_AUDIO_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="That recording was too long. Read just the one sentence and try again.",
        )

    ip = client_ip(request.client.host if request.client else None, request.headers)
    if not PER_IP_BURST.hit(ip) or not PER_IP_DAILY.hit(ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="You've used up the free tries for now. Create a free account to keep practicing.",
        )
    if not SITE_HOURLY.hit("site"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Try mode is very busy right now. Please try again in a little while.",
        )

    _request_count += 1
    if _request_count % 200 == 0:
        PER_IP_BURST.prune()
        PER_IP_DAILY.prune()

    print("Guest analysis accepted")
    filename = audio_file.filename
    content_type = audio_file.content_type

    def make_stream():
        return analyze_audio_guest_event_stream(
            phoneme_assistant=phoneme_assistant,
            audio_bytes=audio_bytes,
            audio_filename=filename,
            audio_content_type=content_type,
            attempted_sentence=attempted_sentence,
        )

    return StreamingResponse(
        _stream_with_slot(make_stream),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
