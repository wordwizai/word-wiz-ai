import asyncio
import io
import json
import math
from urllib.parse import quote

import numpy as np
import pandas as pd
import soundfile as sf
from core.audio_preprocessing import preprocess_audio
from core.modes.base_mode import BaseMode
from core.phoneme_assistant import PhonemeAssistant
from core.temp_audio_cache import audio_cache
from crud.feedback_entry import create_feedback_entry, get_feedback_entries_by_session
from crud.session import get_session
from fastapi import HTTPException, UploadFile, status
from models.session import Session as UserSession
from models.user import User
from schemas.feedback_entry import AudioAnalysis, FeedbackEntryCreate
from schemas.session import SessionBase
from sqlalchemy.orm import Session


async def load_and_preprocess_audio_file(audio_file: UploadFile, session_id: str | None = None) -> tuple[np.ndarray, str]:
    """
    Load and preprocess the audio file with caching at key stages.

    Args:
        audio_file (UploadFile): The uploaded audio file.
        session_id (str, optional): Session ID for caching. If None, generates one.

    Returns:
        tuple[np.ndarray, str]: The preprocessed audio array and cache session ID.
    """
    if audio_file.content_type not in [
        "audio/wav",
        "audio/x-wav",
        "audio/mpeg",
    ]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported audio format. Please upload a WAV or MP3 file.",
        )

    # Generate session ID for caching if not provided
    if session_id is None:
        session_id = audio_cache.generate_session_id()

    # Read audio file into numpy array
    audio_bytes = await audio_file.read()
    
    # CACHE POINT 1: Save original uploaded audio
    audio_cache.save_audio_bytes(
        audio_bytes, 
        "original", 
        session_id,
        f"uploaded_{audio_file.filename}",
        metadata={
            "filename": audio_file.filename,
            "content_type": audio_file.content_type,
            "size_bytes": len(audio_bytes)
        }
    )
    
    audio_array, sample_rate = sf.read(io.BytesIO(audio_bytes), dtype="float32")
    if len(audio_array.shape) == 2:
        audio_array = np.mean(audio_array, axis=1)
    
    # CACHE POINT 2: Save audio after format conversion but before preprocessing
    audio_cache.save_audio(
        audio_array,
        "analysis",
        session_id,
        sample_rate,
        "pre_preprocessing",
        metadata={
            "stage": "after_format_conversion",
            "original_shape": str(audio_array.shape),
            "sample_rate": sample_rate
        }
    )
    
    # Apply preprocessing
    audio_array = preprocess_audio(audio_array)
    
    # CACHE POINT 3: Save preprocessed audio
    audio_cache.save_audio(
        audio_array,
        "preprocessed",
        session_id,
        sample_rate,
        "final",
        metadata={
            "stage": "after_preprocessing",
            "preprocessing_applied": "noise_reduction_and_normalization",
            "final_shape": str(audio_array.shape),
            "sample_rate": sample_rate
        }
    )
    
    return audio_array, session_id


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


async def analyze_audio_file_event_stream(
    phoneme_assistant: PhonemeAssistant,
    activity_object: BaseMode,
    audio_array: np.ndarray,
    attempted_sentence: str,
    db: Session,
    current_user: User,
    session: UserSession,
):
    try:

        # STEP 1: ANALYZE AUDIO
        pronunciation_dataframe, highest_per_word, problem_summary, per_summary = (
            await phoneme_assistant.process_audio(
                attempted_sentence, audio_array, verbose=True
            )
        )
        audio_analysis_object = AudioAnalysis(
            pronunciation_dataframe=pronunciation_dataframe,
            problem_summary=problem_summary,
            per_summary=per_summary,
            highest_per_word=highest_per_word,
        )
        analysis_payload = {
            "type": "analysis",
            "data": {
                "pronunciation_dataframe": sanitize(pronunciation_dataframe.to_dict()),
                "highest_per_word": sanitize(highest_per_word),
                "problem_summary": sanitize(problem_summary),
                "per_summary": sanitize(per_summary),
            },
        }
        yield f"data: {json.dumps(analysis_payload)}\n\n"
        await asyncio.sleep(0)  # Yield control to the event loop

        # STEP 2: GET GPT RESPONSE

        # based on the mode
        response = await activity_object.get_feedback_and_next_sentence(
            attempted_sentence=attempted_sentence,
            analysis=audio_analysis_object,
            phoneme_assistant=phoneme_assistant,
            session=session,
        )
        # response = phoneme_assistant.get_gpt_response(
        #     attempted_sentence=attempted_sentence,
        #     pronunciation_data=pronunciation_dataframe.to_dict(),
        #     highest_per_word_data=highest_per_word,
        #     problem_summary=problem_summary,
        #     per_summary=per_summary,
        # )
        gpt_payload = {
            "type": "gpt_response",
            "data": {
                "sentence": response.get("sentence", ""),
                "feedback": response.get("feedback", ""),
                "metadata": response.get("metadata", {}),
            },
        }
        yield f"data: {json.dumps(gpt_payload)}\n\n"
        await asyncio.sleep(0)  # Yield control to the event loop

        # STEP 3: LOG THE ENTRY INTO THE DB
        # Store the full response including SSML for logging, but only send plain feedback to frontend
        gpt_response_for_db = {
            "sentence": response.get("sentence", ""),
            "feedback": response.get("feedback", ""),
            "feedback_ssml": response.get("feedback_ssml", ""),
            "metadata": response.get("metadata", {}),
        }
        feedback_entry = FeedbackEntryCreate(
            session_id=session.id,
            sentence=attempted_sentence,
            phoneme_analysis=analysis_payload.get("data", {}),
            gpt_response=gpt_response_for_db,
        )
        create_feedback_entry(db, feedback_entry)

        # STEP 4: FEEDBACK AUDIO
        loop = asyncio.get_event_loop()
        response_audio_file = await loop.run_in_executor(
            None, 
            phoneme_assistant.feedback_to_audio, 
            response.get("feedback", ""),
            response.get("feedback_ssml", None)
        )
        
        # CACHE POINT 4: Save feedback audio
        # Extract audio bytes from base64 for caching
        import base64
        feedback_audio_bytes = base64.b64decode(response_audio_file["data"])
        audio_cache.save_feedback_audio(
            feedback_audio_bytes,
            str(session.id),  # Convert session ID to string
            response.get("feedback", ""),
            metadata={
                "stage": "tts_feedback",
                "feedback_text": response.get("feedback", ""),
                "has_ssml": response.get("feedback_ssml") is not None,
                "mimetype": response_audio_file["mimetype"]
            }
        )
        
        audio_payload = {
            "type": "audio_feedback_file",
            "data": response_audio_file["data"],
            "filename": response_audio_file["filename"],
            "mimetype": response_audio_file["mimetype"],
        }
        # audio_payload = {
        #     "type": "audio_feedback_url",
        #     "data": {
        #         "url": f"/feedback-audio?session_id={session.id}&text={quote(response.get('feedback',''))}"
        #     },
        # }
        yield f"data: {json.dumps(audio_payload)}\n\n"
        await asyncio.sleep(0)  # Yield control to the event loop

    except Exception as e:
        error_payload = {
            "type": "error",
            "data": {"error": f"AI processing failed: {str(e)}"},
        }
        yield f"data: {json.dumps(error_payload)}\n\n"
        return
