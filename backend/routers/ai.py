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
from routers.handlers.audio_processing_handler import (
    analyze_audio_file_event_stream,
    load_and_preprocess_audio_file,
)
from sqlalchemy.orm import Session

router = APIRouter()
phoneme_assistant = PhonemeAssistant()


@router.post("/analyze-audio")
async def analyze_audio(
    attempted_sentence: str = Form(...),
    session_id: int = Form(...),
    audio_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):

    # Process the audio file
    try:
        audio_array = await load_and_preprocess_audio_file(audio_file)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process audio file: {str(e)}",
        )

    session = get_session(db, session_id)

    # Build the activity object based on the mode
    if session is None or session.activity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session or activity not found",
        )

    if session.activity.activity_type == "unlimited":
        activity_object = UnlimitedPractice()
    elif session.activity.activity_type == "choice-story":
        activity_object = ChoiceStoryPractice()
    elif session.activity.activity_type == "story":
        activity_object = StoryPractice(session.activity.activity_settings.get("story_name",""))
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported mode: {session.activity.activity_type}",
        )

    return StreamingResponse(
        analyze_audio_file_event_stream(
            phoneme_assistant=phoneme_assistant,
            activity_object=activity_object,
            audio_array=audio_array,
            attempted_sentence=attempted_sentence,
            current_user=current_user,
            session=session,
            db=db,
        ),
        media_type="text/event-stream",
    )
