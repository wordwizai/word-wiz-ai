"""
Audio analysis orchestration service.

Common logic for processing audio analysis with or without client phonemes.
"""

from typing import Optional
from fastapi import UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from models import User
from core.phoneme_assistant import PhonemeAssistant
from core.modes.base_mode import BaseMode
from routers.handlers.audio_processing_handler import analyze_audio_file_event_stream


async def process_audio_analysis(
    attempted_sentence: str,
    session_id: int,
    audio_file: UploadFile,
    db: Session,
    current_user: User,
    phoneme_assistant: PhonemeAssistant,
    activity_object: BaseMode,
    client_phonemes: Optional[list[list[str]]] = None,
    client_words: Optional[list[str]] = None,
) -> StreamingResponse:
    """
    Common logic for processing audio analysis with or without client phonemes.

    Args:
        attempted_sentence: The sentence the user attempted to read.
        session_id: Practice session ID.
        audio_file: Uploaded audio file.
        db: Database session.
        current_user: Authenticated user.
        phoneme_assistant: PhonemeAssistant instance.
        activity_object: Activity mode object (from mode_factory).
        client_phonemes: Optional client-extracted phonemes.
        client_words: Optional client-extracted words.

    Returns:
        StreamingResponse with Server-Sent Events for analysis progress.
    """
    from crud.session import get_session

    session = get_session(db, session_id)

    # Read audio file bytes before passing to streaming response
    # (UploadFile gets closed after request parsing, so we need to read it now)
    audio_bytes = await audio_file.read()
    audio_filename = audio_file.filename
    audio_content_type = audio_file.content_type

    # Return StreamingResponse immediately - preprocessing will happen inside the stream
    return StreamingResponse(
        analyze_audio_file_event_stream(
            phoneme_assistant=phoneme_assistant,
            activity_object=activity_object,
            audio_bytes=audio_bytes,
            audio_filename=audio_filename,
            audio_content_type=audio_content_type,
            attempted_sentence=attempted_sentence,
            current_user=current_user,
            session=session,
            db=db,
            client_phonemes=client_phonemes,
            client_words=client_words,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable buffering in nginx/proxy
            "Connection": "keep-alive",
        },
    )
