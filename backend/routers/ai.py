from auth.auth_handler import get_current_active_user
from core.modes.story import StoryPractice
from core.modes.unlimited import UnlimitedPractice
from core.modes.choice_story import ChoiceStoryPractice
from core.phoneme_assistant import PhonemeAssistant
from crud.session import get_session
from database import get_db
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from models import User
from models.session import Session as UserSession
from routers.handlers.audio_processing_handler import (
    analyze_audio_file_event_stream,
    load_and_preprocess_audio_bytes,
)
from sqlalchemy.orm import Session
from typing import Optional
import json
import numpy as np
import base64

router = APIRouter()
phoneme_assistant = PhonemeAssistant()


# WebSocket Connection Manager
class ConnectionManager:
    """Manages active WebSocket connections per user."""
    
    def __init__(self):
        self.active_connections: dict[int, WebSocket] = {}  # user_id -> websocket
    
    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        print(f"🔌 WebSocket connected for user {user_id}")
    
    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            print(f"🔌 WebSocket disconnected for user {user_id}")
    
    async def send_json(self, user_id: int, data: dict):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(data)


manager = ConnectionManager()


def validate_client_phonemes(client_phonemes: str) -> Optional[list[list[str]]]:
    """
    Validate and parse client-provided phonemes.
    Returns parsed phonemes if valid, None if invalid.
    """
    try:
        phonemes_data = json.loads(client_phonemes)
        
        # Basic validation
        if not isinstance(phonemes_data, list):
            raise ValueError("Phonemes must be an array")
        
        for i, word_phonemes in enumerate(phonemes_data):
            if not isinstance(word_phonemes, list):
                raise ValueError(f"Word {i} phonemes must be an array")
            if len(word_phonemes) == 0:
                raise ValueError(f"Word {i} has no phonemes")
            for phoneme in word_phonemes:
                if not isinstance(phoneme, str):
                    raise ValueError(f"Phoneme must be a string, got {type(phoneme)}")
        
        print(f"Validated client phonemes: {len(phonemes_data)} words")
        return phonemes_data
        
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Invalid client phonemes, falling back to server extraction: {e}")
        return None


def get_activity_object(session: UserSession):
    """
    Build the activity object based on the session's activity type.
    """
    if session is None or session.activity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session or activity not found",
        )

    activity_type = session.activity.activity_type
    
    if activity_type == "unlimited":
        return UnlimitedPractice()
    elif activity_type == "choice-story":
        return ChoiceStoryPractice()
    elif activity_type == "story":
        story_name = session.activity.activity_settings.get("story_name", "")
        return StoryPractice(story_name)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported mode: {activity_type}",
        )


async def process_audio_analysis(
    attempted_sentence: str,
    session_id: int,
    audio_file: UploadFile,
    db: Session,
    current_user: User,
    client_phonemes: Optional[list[list[str]]] = None,
    client_words: Optional[list[str]] = None,
) -> StreamingResponse:
    """
    Common logic for processing audio analysis with or without client phonemes.
    """
    session = get_session(db, session_id)
    
    # Validate session and get activity object
    activity_object = get_activity_object(session)

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
    
    return await process_audio_analysis(
        attempted_sentence=attempted_sentence,
        session_id=session_id,
        audio_file=audio_file,
        db=db,
        current_user=current_user,
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
        try:
            words_data = json.loads(client_words)
            
            # Basic validation
            if not isinstance(words_data, list):
                print("Invalid client words: not an array")
                words_data = None
            elif phonemes_data and len(words_data) != len(phonemes_data):
                # Log the mismatch but don't reject - backend will handle alignment
                print(f"Word count ({len(words_data)}) differs from phoneme count ({len(phonemes_data)}) - backend will align")
                # Don't set to None - trust the frontend data
            
            # Validate each word is a non-empty string
            if words_data:
                for i, word in enumerate(words_data):
                    if not isinstance(word, str) or len(word) == 0:
                        print(f"Invalid word at index {i}")
                        words_data = None
                        break
                
                if words_data:
                    print(f"Validated client words: {len(words_data)} words")
        
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Invalid client words, falling back to server extraction: {e}")
            words_data = None
    
    return await process_audio_analysis(
        attempted_sentence=attempted_sentence,
        session_id=session_id,
        audio_file=audio_file,
        db=db,
        current_user=current_user,
        client_phonemes=phonemes_data,
        client_words=words_data,
    )


@router.websocket("/ws/audio-analysis")
async def websocket_audio_analysis(websocket: WebSocket):
    """
    WebSocket endpoint for audio analysis with persistent connection.
    
    Message format (client -> server):
    {
        "type": "analyze_audio",
        "audio_base64": "<base64 encoded audio>",
        "attempted_sentence": "the sentence",
        "session_id": 123,
        "filename": "recording.wav",
        "content_type": "audio/wav",
        "client_phonemes": [[...]], // optional
        "client_words": [...] // optional
    }
    
    {
        "type": "ping"
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
        return  # Just return, don't try to close
    
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
            return  # Just return, don't try to close
        
        # Get user from database (try email first, then username)
        current_user = db.query(User).filter(
            (User.email == user_identifier) | (User.username == user_identifier)
        ).first()
        
        if current_user is None:
            print(f"❌ User not found: {user_identifier}")
            return  # Just return, don't try to close
            
    except JWTError as e:
        print(f"❌ JWT Error: {e}")
        return  # Just return, don't try to close
    except Exception as e:
        print(f"❌ Authentication exception: {e}")
        return  # Just return, don't try to close
    
    # Accept the WebSocket connection (only after successful authentication)
    await websocket.accept()
    print(f"✅ WebSocket accepted for user {current_user.username} (ID: {current_user.id})")
    
    # Add to connection manager
    manager.active_connections[current_user.id] = websocket
    
    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_json()
            
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
            
            # Decode audio
            try:
                audio_bytes = base64.b64decode(audio_base64)
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": f"Failed to decode audio: {str(e)}"}
                })
                continue
            
            # Get session and activity
            try:
                session = get_session(db, session_id)
                activity_object = get_activity_object(session)
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": f"Invalid session: {str(e)}"}
                })
                continue
            
            # Process audio through the event stream generator
            try:
                async for event in analyze_audio_file_event_stream(
                    phoneme_assistant=phoneme_assistant,
                    activity_object=activity_object,
                    audio_bytes=audio_bytes,
                    audio_filename=filename,
                    audio_content_type=content_type,
                    attempted_sentence=attempted_sentence,
                    current_user=current_user,
                    session=session,
                    db=db,
                    client_phonemes=client_phonemes,
                    client_words=client_words,
                ):
                    # Parse SSE format and send as JSON
                    if event.startswith("data: "):
                        event_data = json.loads(event[6:])
                        await websocket.send_json(event_data)
            
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


