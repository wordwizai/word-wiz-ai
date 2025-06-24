from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import numpy as np
import io

from ai.phoneme_assistant import PhonemeAssistant
from database import get_db
from auth.auth_handler import get_current_active_user
from models import User

router = APIRouter()
phoneme_assistant = PhonemeAssistant()

@router.post("/analyze-audio")
async def analyze_audio(
    attempted_sentence: str = Form(...),
    audio_file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    try:
        # Read audio file into numpy array
        audio_bytes = await audio_file.read()
        import soundfile as sf
        audio_array, _ = sf.read(io.BytesIO(audio_bytes), dtype='float32')
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process audio file: {str(e)}"
        )

    try:
        response, df, highest_per_word, problem_summary, per_summary = phoneme_assistant.record_audio_and_get_response(
            attempted_sentence=attempted_sentence,
            audio_array=audio_array
        )
        return JSONResponse(content={
            "response": response,
            "highest_per_word": highest_per_word.to_dict(),
            "problem_summary": problem_summary,
            "per_summary": per_summary
        })
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI processing failed: {str(e)}"
        )
