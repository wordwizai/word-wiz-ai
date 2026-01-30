"""
AI router for audio analysis endpoints.

Provides HTTP POST and WebSocket endpoints for analyzing user audio recordings.
"""

import asyncio
import json
import base64
import time
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from auth.auth_handler import get_current_active_user
from core.phoneme_assistant import PhonemeAssistant
from core.validators import validate_client_phonemes, validate_client_words
from database import get_db
from models import User
from services import ConnectionManager, get_activity_object, process_audio_analysis
from routers.handlers.audio_processing_handler import analyze_audio_file_event_stream, AudioAnalysisContext

router = APIRouter()
phoneme_assistant = PhonemeAssistant()
manager = ConnectionManager()


@router.post("/analyze-audio")
async def analyze_audio(
    attempted_sentence: str = Form(...),
    session_id: int = Form(...),
    audio_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Analyze audio using server-side phoneme extraction."""
    print("Received request to /analyze-audio")

    session = db.query(User).filter(User.id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="User not found")

    from crud.session import get_session
    user_session = get_session(db, session_id)
    activity_object = get_activity_object(user_session)

    return await process_audio_analysis(
        attempted_sentence=attempted_sentence,
        session_id=session_id,
        audio_file=audio_file,
        db=db,
        current_user=current_user,
        phoneme_assistant=phoneme_assistant,
        activity_object=activity_object,
        client_phonemes=None,
    )


@router.post("/analyze-audio-with-phonemes")
async def analyze_audio_with_phonemes(
    attempted_sentence: str = Form(...),
    session_id: int = Form(...),
    client_phonemes: str = Form(...),
    client_words: Optional[str] = Form(None),
    audio_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Analyze audio with client-provided phonemes and optionally words.
    Falls back to server-side extraction if client data is invalid.
    """
    print("Received request to /analyze-audio-with-phonemes")

    # Validate client phonemes (returns None if invalid)
    phonemes_data = validate_client_phonemes(client_phonemes)

    # Validate and parse client words if provided
    words_data = None
    if client_words:
        words_data = validate_client_words(client_words, phonemes_data)

    from crud.session import get_session
    user_session = get_session(db, session_id)
    activity_object = get_activity_object(user_session)

    return await process_audio_analysis(
        attempted_sentence=attempted_sentence,
        session_id=session_id,
        audio_file=audio_file,
        db=db,
        current_user=current_user,
        phoneme_assistant=phoneme_assistant,
        activity_object=activity_object,
        client_phonemes=phonemes_data,
        client_words=words_data,
    )


@router.websocket("/ws/audio-analysis")
async def websocket_audio_analysis(websocket: WebSocket):
    """
    WebSocket endpoint for audio analysis with persistent connection.

    Message format (client -> server):
    {
        "type": "analyze_audio" | "ping",
        "audio_base64": "<base64 encoded audio>",  // for analyze_audio
        "attempted_sentence": "...",
        "session_id": 123,
        "filename": "recording.wav",
        "content_type": "audio/wav",
        "client_phonemes": [[...]], // optional
        "client_words": [...] // optional
    }

    Response format (server -> client):
    {
        "type": "processing_started" | "analysis" | "gpt_response" | "audio_feedback_file" | "error",
        "data": {...}
    }
    """
    # Extract token from query parameters
    query_params = dict(websocket.query_params)
    token = query_params.get("token")

    # Validate authentication BEFORE accepting connection
    current_user = None
    db = next(get_db())

    if not token:
        print("❌ No token provided")
        return

    try:
        # Validate token and get user
        from jose import jwt, JWTError
        import os
        from dotenv import load_dotenv

        load_dotenv()
        secret_key = os.getenv("SECRET_KEY")

        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        user_identifier: str = payload.get("sub")

        if user_identifier is None:
            print("❌ No user identifier in token")
            return

        # Get user from database
        current_user = db.query(User).filter(
            (User.email == user_identifier) | (User.username == user_identifier)
        ).first()

        if current_user is None:
            print(f"❌ User not found: {user_identifier}")
            return

    except JWTError as e:
        print(f"❌ JWT Error: {e}")
        return
    except Exception as e:
        print(f"❌ Authentication exception: {e}")
        return

    # Accept the WebSocket connection (only after successful authentication)
    await websocket.accept()
    print(f"✅ WebSocket accepted for user {current_user.username} (ID: {current_user.id})")

    # Add to connection manager
    manager.active_connections[current_user.id] = websocket

    try:
        while True:
            # Wait for messages from client
            print(f"⏳ [{time.time()}] Waiting for WebSocket message...")
            receive_start = time.time()
            data = await websocket.receive_json()
            receive_time = time.time() - receive_start
            print(f"📨 [{time.time()}] Message received in {receive_time:.3f}s, size: {len(str(data))} bytes")

            if data.get("type") == "ping":
                # Heartbeat
                await websocket.send_json({"type": "pong"})
                continue

            if data.get("type") != "analyze_audio":
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": f"Unknown message type: {data.get('type')}"}
                })
                continue

            print(f"🎯 [{time.time()}] Processing analyze_audio request")
            # Extract request data
            audio_base64 = data.get("audio_base64")
            attempted_sentence = data.get("attempted_sentence")
            session_id = data.get("session_id")
            filename = data.get("filename", "recording.wav")
            content_type = data.get("content_type", "audio/wav")
            client_phonemes = data.get("client_phonemes")
            client_words = data.get("client_words")

            if not audio_base64 or not attempted_sentence or session_id is None:
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": "Missing required fields: audio_base64, attempted_sentence, or session_id"}
                })
                continue

            # Send immediate acknowledgment BEFORE decoding audio
            ack_start = time.time()
            print(f"📤 [{time.time()}] Sending immediate processing_started acknowledgment...")
            await websocket.send_json({
                "type": "processing_started",
                "data": {"message": "Audio received, processing..."}
            })
            print(f"✅ [{time.time()}] Acknowledgment sent in {time.time() - ack_start:.3f}s")
            await asyncio.sleep(0)

            # Decode audio
            try:
                decode_start = time.time()
                audio_bytes = base64.b64decode(audio_base64)
                print(f"⏱️  Base64 decode took {time.time() - decode_start:.3f}s")
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": f"Failed to decode audio: {str(e)}"}
                })
                continue

            # Get session and activity
            try:
                from crud.session import get_session
                session_start = time.time()
                session = get_session(db, session_id)
                activity_object = get_activity_object(session)
                print(f"⏱️  Session/activity lookup took {time.time() - session_start:.3f}s")
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": f"Invalid session: {str(e)}"}
                })
                continue

            # Process audio through the event stream generator
            print("🔄 Starting event stream generator...")
            generator_start = time.time()
            try:
                ctx = AudioAnalysisContext(
                    phoneme_assistant=phoneme_assistant,
                    activity_object=activity_object,
                    audio_bytes=audio_bytes,
                    audio_filename=filename,
                    audio_content_type=content_type,
                    attempted_sentence=attempted_sentence,
                    db=db,
                    current_user=current_user,
                    session=session,
                    client_phonemes=client_phonemes,
                    client_words=client_words,
                )
                async for event in analyze_audio_file_event_stream(ctx):
                    if 'first_event' not in locals():
                        first_event = True
                        print(f"⏱️  Time to first event from generator: {time.time() - generator_start:.3f}s")

                    # Parse SSE format and send as JSON
                    if event.startswith("data: "):
                        event_data = json.loads(event[6:])
                        await websocket.send_json(event_data)
                        await asyncio.sleep(0)

            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": f"Processing failed: {str(e)}"}
                })

    except WebSocketDisconnect:
        manager.disconnect(current_user.id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(current_user.id)
    finally:
        db.close()
