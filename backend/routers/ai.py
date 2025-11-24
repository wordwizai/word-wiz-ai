from auth.auth_handler import get_current_active_user
from core.modes.story import StoryPractice
from core.modes.unlimited import UnlimitedPractice
from core.modes.choice_story import ChoiceStoryPractice
from core.phoneme_assistant import PhonemeAssistant
from crud.session import get_session
from database import get_db
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from models import User
from models.session import Session as UserSession
from routers.handlers.audio_processing_handler import (
    analyze_audio_file_event_stream,
    load_and_preprocess_audio_file,
)
from sqlalchemy.orm import Session
from typing import Optional
import json
import numpy as np

router = APIRouter()
phoneme_assistant = PhonemeAssistant()


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

    # Return StreamingResponse immediately - preprocessing will happen inside the stream
    return StreamingResponse(
        analyze_audio_file_event_stream(
            phoneme_assistant=phoneme_assistant,
            activity_object=activity_object,
            audio_file=audio_file,  # Pass the file instead of processed array
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

