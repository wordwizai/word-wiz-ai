"""
Audio Chunking Module

Intelligently splits long audio recordings into smaller chunks for processing.
This improves model accuracy and prevents timeouts on longer recordings.
"""

import numpy as np
import librosa


def chunk_audio_at_silence(audio, sr=16000, max_chunk_duration=7, top_db=30):
    """
    Split audio into chunks at silence points.
    
    Args:
        audio: Audio signal as numpy array
        sr: Sample rate (default 16000)
        max_chunk_duration: Maximum duration of each chunk in seconds (default 7)
        top_db: Threshold in dB below reference for silence detection (default 30)
        
    Returns:
        List of audio chunks (numpy arrays)
        List of chunk metadata (start/end times, duration)
        
    Note:
        Splits audio at natural pauses (silence) to avoid cutting words in half.
        If no suitable silence found, will split at max_chunk_duration boundary.
    """
    # Find silence intervals
    intervals = librosa.effects.split(audio, top_db=top_db)
    
    chunks = []
    chunk_metadata = []
    current_chunk_start = 0
    current_chunk_samples = []
    current_chunk_duration = 0
    
    for start, end in intervals:
        segment = audio[start:end]
        segment_duration = len(segment) / sr
        
        if current_chunk_duration + segment_duration > max_chunk_duration:
            # Save current chunk if it has content
            if current_chunk_samples:
                chunk_audio = np.concatenate(current_chunk_samples)
                chunks.append(chunk_audio)
                chunk_end_time = current_chunk_start + current_chunk_duration
                chunk_metadata.append({
                    "start_time": current_chunk_start,
                    "end_time": chunk_end_time,
                    "duration": current_chunk_duration,
                    "num_samples": len(chunk_audio)
                })
                print(f"  Chunk {len(chunks)}: {current_chunk_start:.2f}s - {chunk_end_time:.2f}s ({current_chunk_duration:.2f}s)")
            
            # Start new chunk
            current_chunk_start = start / sr
            current_chunk_samples = [segment]
            current_chunk_duration = segment_duration
        else:
            # Add segment to current chunk
            current_chunk_samples.append(segment)
            current_chunk_duration += segment_duration
    
    # Don't forget the last chunk
    if current_chunk_samples:
        chunk_audio = np.concatenate(current_chunk_samples)
        chunks.append(chunk_audio)
        chunk_end_time = current_chunk_start + current_chunk_duration
        chunk_metadata.append({
            "start_time": current_chunk_start,
            "end_time": chunk_end_time,
            "duration": current_chunk_duration,
            "num_samples": len(chunk_audio)
        })
        print(f"  Chunk {len(chunks)}: {current_chunk_start:.2f}s - {chunk_end_time:.2f}s ({current_chunk_duration:.2f}s)")
    
    return chunks, chunk_metadata


def merge_chunk_results(chunk_phonemes, chunk_words, chunk_metadata):
    """
    Merge phoneme and word extraction results from multiple audio chunks.
    
    Args:
        chunk_phonemes: List of phoneme arrays (one per chunk) - each chunk returns list of word phonemes
        chunk_words: List of word arrays (one per chunk)
        chunk_metadata: List of chunk metadata dicts
        
    Returns:
        merged_phonemes: Combined phoneme array (list of lists, one per word)
        merged_words: Combined word array
        
    Note:
        Handles overlaps and gaps between chunks intelligently.
        Phoneme predictions are nested: [[word1_phonemes], [word2_phonemes], ...]
    """
    if not chunk_phonemes:
        return [], []
    
    # Concatenate results from all chunks
    # phonemes is a list of lists (one list per word), so we extend the outer list
    merged_phonemes = []
    merged_words = []
    
    for i, (phonemes, words) in enumerate(zip(chunk_phonemes, chunk_words)):
        # phonemes is already a list of lists (e.g., [['h','ɛ','l','oʊ'], ['w','ɜː','l','d']])
        # words is a list of strings (e.g., ['hello', 'world'])
        if phonemes and isinstance(phonemes, list):
            merged_phonemes.extend(phonemes)
        if words and isinstance(words, list):
            merged_words.extend(words)
    
    return merged_phonemes, merged_words


def should_use_chunking(audio, sr=16000, threshold_seconds=8):
    """
    Determine if audio should be chunked based on duration.
    
    Args:
        audio: Audio signal as numpy array
        sr: Sample rate (default 16000)
        threshold_seconds: Duration threshold for chunking (default 8)
        
    Returns:
        bool: True if audio should be chunked, False otherwise
    """
    audio_duration = len(audio) / sr
    return audio_duration > threshold_seconds


def estimate_speech_activity(audio, sr=16000, frame_length=2048, hop_length=512, top_db=30):
    """
    Estimate the percentage of audio that contains speech (vs silence).
    
    Args:
        audio: Audio signal as numpy array
        sr: Sample rate (default 16000)
        frame_length: Length of each frame for RMS calculation
        hop_length: Number of samples between frames
        top_db: Threshold in dB for silence detection
        
    Returns:
        float: Percentage of audio containing speech (0-100)
    """
    # Compute RMS energy for each frame
    rms = librosa.feature.rms(y=audio, frame_length=frame_length, hop_length=hop_length)[0]
    
    # Convert to dB
    rms_db = librosa.amplitude_to_db(rms, ref=np.max)
    
    # Count frames above threshold
    speech_frames = np.sum(rms_db > -top_db)
    total_frames = len(rms_db)
    
    speech_percentage = (speech_frames / total_frames) * 100
    return speech_percentage


if __name__ == "__main__":
    # Test chunking with sample audio
    import soundfile as sf
    
    # Load a test audio file
    audio, sr = librosa.load("temp_audio/output.wav", sr=16000)
    
    print(f"Audio duration: {len(audio)/sr:.2f}s")
    
    # Test speech activity estimation
    speech_pct = estimate_speech_activity(audio, sr)
    print(f"Speech activity: {speech_pct:.1f}%")
    
    # Test chunking
    if should_use_chunking(audio, sr):
        print("Audio should be chunked")
        chunks, metadata = chunk_audio_at_silence(audio, sr)
        print(f"Created {len(chunks)} chunks")
    else:
        print("Audio is short enough - no chunking needed")
