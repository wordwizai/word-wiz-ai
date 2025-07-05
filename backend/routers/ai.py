from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends, Form
from fastapi.responses import JSONResponse, StreamingResponse
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
import json

import soundfile as sf


router = APIRouter()
phoneme_assistant = PhonemeAssistant()


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


@router.post("/analyze-audio")
async def analyze_audio(
    attempted_sentence: str = Form(...),
    audio_file: UploadFile = File(...),
    db: Session = Depends(get_db),
):

    # Process the audio file
    try:
        if audio_file.content_type not in [
            "audio/wav",
            "audio/x-wav",
            "audio/mpeg",
        ]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported audio format. Please upload a WAV or MP3 file.",
            )

        # Read audio file into numpy array
        audio_bytes = await audio_file.read()
        audio_array, _ = sf.read(io.BytesIO(audio_bytes), dtype="float32")
        if len(audio_array.shape) == 2:
            audio_array = np.mean(audio_array, axis=1)
        audio_array = preprocess_audio(audio_array)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process audio file: {str(e)}",
        )

    async def event_stream():
        try:
            # STEP 1: ANALYZE AUDIO
            pronunciation_dataframe, highest_per_word, problem_summary, per_summary = (
                phoneme_assistant.process_audio(attempted_sentence, audio_array)
            )
            analysis_payload = {
                "type": "analysis",
                "data": {
                    "pronunciation_dataframe": sanitize(
                        pronunciation_dataframe.to_dict()
                    ),
                    "highest_per_word": sanitize(highest_per_word),
                    "problem_summary": sanitize(problem_summary),
                    "per_summary": sanitize(per_summary),
                },
            }
            yield f"data: {json.dumps(analysis_payload)}\n\n"
            # STEP 2: GET GPT RESPONSE
            response = phoneme_assistant.get_gpt_response(
                attempted_sentence=attempted_sentence,
                pronunciation_data=pronunciation_dataframe.to_dict(),
                highest_per_word_data=highest_per_word,
                problem_summary=problem_summary,
                per_summary=per_summary,
            )
            gpt_payload = {"type": "gpt_response", "data": {
                "sentence": response.get("sentence", ""),
                "feedback": response.get("feedback", ""),
            }}
            yield f"data: {json.dumps(gpt_payload)}\n\n"

            # STEP 3: FEEDBACK AUDIO
            response_audio_file = phoneme_assistant.feedback_to_audio(
                response.get("feedback", "")
            )
            audio_payload = {
                "type": "audio_feedback_file",
                "data": response_audio_file["data"],
                "filename": response_audio_file["filename"],
                "mimetype": response_audio_file["mimetype"],
            }
            yield f"data: {json.dumps(audio_payload)}\n\n"

        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'error': f'AI processing failed: {str(e)}'})}\n\n"
            return

    return StreamingResponse(event_stream(), media_type="text/event-stream")

    # try:
    #     response, df, highest_per_word, problem_summary, per_summary = (
    #         phoneme_assistant.process_audio(
    #             attempted_sentence=attempted_sentence, audio_array=audio_array
    #         )
    #     )
    #
    #
    #     return JSONResponse(
    #         content={
    #             "response": response,
    #             "df": sanitize(df.to_dict()),
    #             "highest_per_word": sanitize(highest_per_word.to_dict()),
    #             "problem_summary": sanitize(problem_summary),
    #             "per_summary": sanitize(per_summary),
    #         }
    #     )
    # except Exception as e:
    #     raise HTTPException(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         detail=f"AI processing failed: {str(e)}",
    #     )
