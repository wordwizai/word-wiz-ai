import asyncio
import io
import json
import math
import time
from urllib.parse import quote

import numpy as np
import pandas as pd
import soundfile as sf
from core.audio_preprocessing import preprocess_audio
from core.modes.base_mode import BaseMode
from core.phoneme_assistant import PhonemeAssistant
from core.temp_audio_cache import audio_cache
from core.process_audio import process_audio_with_client_phonemes, analyze_results
from core.grapheme_to_phoneme import grapheme_to_phoneme as g2p
from crud.feedback_entry import create_feedback_entry, get_feedback_entries_by_session
from crud.session import get_session
from fastapi import HTTPException, UploadFile, status
from models.session import Session as UserSession
from models.user import User
from schemas.feedback_entry import AudioAnalysis, FeedbackEntryCreate
from schemas.session import SessionBase
from sqlalchemy.orm import Session
from routers.handlers.phoneme_processing_handler import (
    validate_client_phonemes,
    normalize_espeak_to_ipa,
    format_phonemes_for_logging,
)


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
    read_start = time.time()
    audio_bytes = await audio_file.read()
    print(f"⏱️  File read took {time.time() - read_start:.3f}s")
    
    # Check if this is an empty file (sent when client did full extraction)
    if len(audio_bytes) == 0:
        print("📭 Received empty audio - client performed full extraction")
        # Return empty array - won't be used since client provided both phonemes and words
        return np.array([]), session_id
    
    # CACHE POINT 1: Save original uploaded audio
    cache_start = time.time()
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
    print(f"⏱️  Cache save (original) took {time.time() - cache_start:.3f}s")
    
    decode_start = time.time()
    audio_array, sample_rate = sf.read(io.BytesIO(audio_bytes), dtype="float32")
    if len(audio_array.shape) == 2:
        audio_array = np.mean(audio_array, axis=1)
    print(f"⏱️  Audio decode took {time.time() - decode_start:.3f}s")
    
    # Calculate audio duration
    audio_duration = len(audio_array) / sample_rate
    print(f"📊 Audio duration: {audio_duration:.2f}s ({len(audio_array)} samples @ {sample_rate}Hz)")
    
    # Validate audio length
    if audio_duration > 10:
        print(f"⚠️  Long audio detected ({audio_duration:.1f}s) - will use chunking strategy for better accuracy.")
    
    # Validate audio is not too short
    if audio_duration < 0.5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Audio too short ({audio_duration:.1f}s). Please record at least 0.5 seconds of speech."
        )
    
    # CACHE POINT 2: Save audio after format conversion but before preprocessing
    cache_start = time.time()
    audio_cache.save_audio(
        audio_array,
        "analysis",
        session_id,
        sample_rate,
        "pre_preprocessing",
        metadata={
            "stage": "after_format_conversion",
            "original_shape": str(audio_array.shape),
            "sample_rate": sample_rate,
            "duration_seconds": audio_duration
        }
    )
    print(f"⏱️  Cache save (pre-preprocessing) took {time.time() - cache_start:.3f}s")
    
    # Apply preprocessing with audio length for adaptive noise reduction
    print("🔊 Starting audio preprocessing...")
    audio_array = preprocess_audio(audio_array, sr=sample_rate, audio_length_seconds=audio_duration)
    
    # CACHE POINT 3: Save preprocessed audio
    cache_start = time.time()
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
    print(f"⏱️  Cache save (preprocessed) took {time.time() - cache_start:.3f}s")
    
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
    audio_file: UploadFile,  # Changed from audio_array to audio_file
    attempted_sentence: str,
    db: Session,
    current_user: User,
    session: UserSession,
    client_phonemes: list[list[str]] | None = None,
    client_words: list[str] | None = None,
):
    try:
        # Send immediate acknowledgment that processing has started
        print("📤 Sending processing started event...")
        processing_started_payload = {
            "type": "processing_started",
            "data": {"message": "Audio received, analyzing..."},
        }
        yield f"data: {json.dumps(processing_started_payload)}\n\n"
        await asyncio.sleep(0.01)  # Ensure the event is flushed
        
        # NOW do the preprocessing after sending the first event
        print("🔄 Starting audio preprocessing...")
        try:
            audio_array, cache_session_id = await load_and_preprocess_audio_file(
                audio_file, str(session.id)
            )
            print("✅ Audio preprocessing completed")
        except Exception as e:
            error_payload = {
                "type": "error",
                "data": {"message": f"Failed to process audio file: {str(e)}"},
            }
            yield f"data: {json.dumps(error_payload)}\n\n"
            return
        
        # STEP 1: ANALYZE AUDIO
        
        # Check if we received empty audio (client sent it to save bandwidth)
        if len(audio_array) == 0:
            # Empty audio is only valid if we have client phonemes and words
            if client_phonemes is None or client_words is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Empty audio received but client extraction data is incomplete. Please try again."
                )
            print("📭 Empty audio received - using full client extraction")
        else:
            # Validate audio has speech content using VAD
            from core.audio_chunking import estimate_speech_activity
            speech_percentage = estimate_speech_activity(audio_array, sr=16000)
            print(f"🎤 Speech activity: {speech_percentage:.1f}%")
            
            # Require at least 30% speech activity
            if speech_percentage < 30:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Audio appears to be mostly silent ({speech_percentage:.1f}% speech activity). Please record clearer audio with speech."
                )
        
        # Determine if we should use client phonemes/words or extract on server
        use_client_phonemes = False
        use_client_words = False
        
        if client_phonemes is not None:
            # Validate client phonemes format
            is_valid, error_msg = validate_client_phonemes(client_phonemes, attempted_sentence)
            
            if is_valid:
                print(f"✓ Client phonemes validated successfully")
                print(f"  Client phonemes (eSpeak format): {format_phonemes_for_logging(client_phonemes, max_words=3)}")
                
                # Normalize eSpeak → IPA for consistent processing
                normalized_phonemes = normalize_espeak_to_ipa(client_phonemes)
                print(f"  Normalized phonemes (IPA format): {format_phonemes_for_logging(normalized_phonemes, max_words=3)}")
                
                use_client_phonemes = True
                client_phonemes = normalized_phonemes  # Use normalized version
                
                # If client words also provided, validate them
                if client_words is not None:
                    from routers.handlers.phoneme_processing_handler import validate_client_words
                    is_valid_words, error_msg_words = validate_client_words(
                        client_words, client_phonemes, attempted_sentence
                    )
                    
                    if is_valid_words:
                        print(f"✓ Client words validated successfully: {client_words}")
                        use_client_words = True
                    else:
                        print(f"✗ Client word validation failed: {error_msg_words}")
                        print(f"  Falling back to server-side word extraction")
                        client_words = None
            else:
                print(f"✗ Client phoneme validation failed: {error_msg}")
                print(f"  Falling back to server-side phoneme extraction")
                client_phonemes = None
                client_words = None  # Can't use words without phonemes
        
        # Log processing path
        if use_client_phonemes and use_client_words:
            print("→ Using full client extraction (phonemes + words) - Maximum speed! 🚀")
            processing_mode = "client"
        elif use_client_phonemes:
            print("→ Using client phonemes only - Server will extract words")
            processing_mode = "hybrid"
        else:
            print("→ Using full server-side extraction (phonemes + words)")
            processing_mode = "server"
        
        # Send processing mode update
        print(f"📤 Sending processing mode update ({processing_mode})...")
        processing_mode_payload = {
            "type": "processing_mode",
            "data": {"mode": processing_mode, "message": "Analyzing pronunciation..."},
        }
        yield f"data: {json.dumps(processing_mode_payload)}\n\n"
        await asyncio.sleep(0.01)
        
        # Process audio based on what client data we have
        import time
        processing_start = time.time()
        
        if use_client_phonemes and client_phonemes is not None:
            # Get ground truth phonemes for the sentence
            ground_truth_phonemes = g2p(attempted_sentence)
            
            # Process audio with client phonemes (and optionally client words)
            pronunciation_data = await process_audio_with_client_phonemes(
                client_phonemes=client_phonemes,
                ground_truth_phonemes=ground_truth_phonemes,
                audio_array=audio_array,
                word_extraction_model=phoneme_assistant.word_extractor,
                client_words=client_words if use_client_words else None,
            )
            
            # Analyze the results to get the same format as server processing
            analysis_start = time.time()
            pronunciation_dataframe, highest_per_word, problem_summary, per_summary = analyze_results(pronunciation_data)
            print(f"⏱️  analyze_results() took {time.time() - analysis_start:.3f}s")
            
            extraction_mode = "full client" if use_client_words else "client phonemes only"
            print(f"✓ {extraction_mode} processing completed in {time.time() - processing_start:.3f}s (PER: {per_summary.get('sentence_per', 0):.2%})")
        else:
            # Original server-side processing
            pronunciation_dataframe, highest_per_word, problem_summary, per_summary = (
                await phoneme_assistant.process_audio(
                    attempted_sentence, audio_array, verbose=True
                )
            )
            
            print(f"✓ Server phoneme processing completed in {time.time() - processing_start:.3f}s (PER: {per_summary.get('sentence_per', 0):.2%})")
        
        # Create audio analysis object (same format regardless of processing path)
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
        print("📤 Sending analysis payload...")
        yield f"data: {json.dumps(analysis_payload)}\n\n"
        await asyncio.sleep(0.01)  # Yield control to the event loop with small delay to ensure flush

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
        print("📤 Sending GPT response payload...")
        yield f"data: {json.dumps(gpt_payload)}\n\n"
        await asyncio.sleep(0.01)  # Yield control to the event loop with small delay to ensure flush

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
        # Ensure feedback is never None - use empty string as fallback
        feedback_text = response.get("feedback") or ""
        feedback_ssml = response.get("feedback_ssml")
        
        response_audio_file = await loop.run_in_executor(
            None, 
            phoneme_assistant.feedback_to_audio, 
            feedback_text,
            feedback_ssml
        )
        
        # CACHE POINT 4: Save feedback audio
        # Extract audio bytes from base64 for caching
        import base64
        feedback_audio_bytes = base64.b64decode(response_audio_file["data"])
        audio_cache.save_feedback_audio(
            feedback_audio_bytes,
            str(session.id),  # Convert session ID to string
            feedback_text,
            metadata={
                "stage": "tts_feedback",
                "feedback_text": feedback_text,
                "has_ssml": feedback_ssml is not None,
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
        print("📤 Sending audio feedback payload...")
        yield f"data: {json.dumps(audio_payload)}\n\n"
        await asyncio.sleep(0.01)  # Yield control to the event loop with small delay to ensure flush

    except Exception as e:
        error_payload = {
            "type": "error",
            "data": {"error": f"AI processing failed: {str(e)}"},
        }
        yield f"data: {json.dumps(error_payload)}\n\n"
        return
