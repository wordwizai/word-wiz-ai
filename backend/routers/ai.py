from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import numpy as np
import io

from ai.phoneme_assistant import PhonemeAssistant
from ai.audio_preprocessing import preprocess_audio
from database import get_db
from auth.auth_handler import get_current_active_user
from models import User
import math
import pandas as pd
from pydub import AudioSegment

router = APIRouter()
phoneme_assistant = PhonemeAssistant()


@router.post("/analyze-audio")
async def analyze_audio(
    attempted_sentence: str = Form(...),
    audio_file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    try:

        if audio_file.content_type not in ["audio/wav", "audio/x-wav", "audio/mpeg"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported audio format. Please upload a WAV or MP3 file.",
            )

        # Read audio file into numpy array
        audio_bytes = await audio_file.read()
        import soundfile as sf
        print("audio_file.filename:", audio_file.filename)
        print("audio_file.content_type:", audio_file.content_type)
        print("audio_bytes length:", len(audio_bytes))
        audio_array, _ = sf.read(io.BytesIO(audio_bytes), dtype="float32")
        print("audio_array shape:", audio_array.shape)
        if len(audio_array.shape) == 2:
            audio_array = np.mean(audio_array, axis=1)
        print("audio_array shape after mean:", audio_array.shape)
        audio_array = preprocess_audio(audio_array)


    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process audio file: {str(e)}",
        )

    try:
        response, df, highest_per_word, problem_summary, per_summary = (
            phoneme_assistant.record_audio_and_get_response(
                attempted_sentence=attempted_sentence, audio_array=audio_array
            )
        )

        def sanitize(obj):
            if isinstance(obj, float):
                if math.isnan(obj) or math.isinf(obj):
                    return None
                return obj
            elif isinstance(obj, dict):
                return {k: sanitize(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [sanitize(v) for v in obj]
            elif isinstance(obj, pd.DataFrame):
                return sanitize(obj.to_dict())
            return obj

        return JSONResponse(
            content={
                "response": response,
                "df": sanitize(df.to_dict()),
                "highest_per_word": sanitize(highest_per_word.to_dict()),
                "problem_summary": sanitize(problem_summary),
                "per_summary": sanitize(per_summary),
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI processing failed: {str(e)}",
        )
