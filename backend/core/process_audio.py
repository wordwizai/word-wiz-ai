"""
Audio processing orchestration.

Coordinates phoneme extraction, word extraction, alignment, and analysis
for both server-side and client-provided phoneme processing paths.
"""

import time
import asyncio

import numpy as np

from .phoneme_extractor import PhonemeExtractor
from .word_extractor import WordExtractor
from .grapheme_to_phoneme import grapheme_to_phoneme as g2p
from .audio_preprocessing import preprocess_audio
from .phoneme_alignment import align_phonemes_to_words, process_word_alignment
from .audio_analysis import analyze_results

# Re-export for backwards compatibility with existing imports
from .per_calculator import compute_per, align_sequences
from .phoneme_alignment import _fallback_proportional_alignment


async def process_audio_array(
    ground_truth_phonemes,
    audio_array,
    sampling_rate=16000,
    phoneme_extraction_model=None,
    word_extraction_model=None,
    use_chunking=True,
) -> list[dict]:
    """
    Process an audio array through the full phoneme analysis pipeline.

    Extracts phonemes and words from audio, aligns them to ground truth,
    and returns word-level pronunciation analysis.

    Args:
        ground_truth_phonemes: Expected phonemes as list of (word, phonemes) tuples.
        audio_array: Audio signal as numpy array.
        sampling_rate: Sample rate (default 16000).
        phoneme_extraction_model: Phoneme extraction model (optional).
        word_extraction_model: Word extraction model (optional).
        use_chunking: Whether to chunk long audio (default True).

    Returns:
        list[dict]: Word-level pronunciation analysis results.
    """
    from .audio_chunking import should_use_chunking, chunk_audio_at_silence, merge_chunk_results

    if phoneme_extraction_model is None:
        phoneme_extraction_model = PhonemeExtractor()

    if word_extraction_model is None:
        word_extraction_model = WordExtractor()

    if len(ground_truth_phonemes) <= 1:
        raise ValueError("ground_truth_phonemes must have at least 2 elements)")

    audio_duration = len(audio_array) / sampling_rate

    # Preprocess the audio
    audio_array = preprocess_audio(audio=audio_array, sr=sampling_rate, audio_length_seconds=audio_duration)

    # Check if audio should be chunked
    if use_chunking and should_use_chunking(audio_array, sampling_rate, threshold_seconds=8):
        phoneme_predictions, predicted_words = await _process_chunked_audio(
            audio_array, sampling_rate, audio_duration,
            phoneme_extraction_model, word_extraction_model
        )
    else:
        phoneme_predictions, predicted_words = await _process_single_audio(
            audio_array, sampling_rate, audio_duration,
            phoneme_extraction_model, word_extraction_model
        )

    if phoneme_predictions is None or predicted_words is None or len(phoneme_predictions) <= 1 or len(predicted_words) <= 1:
        raise ValueError("The audio provided has no speech inside")

    print("unaligned phoneme predictions: ", phoneme_predictions)

    # Validate predicted_words
    if not isinstance(predicted_words, list):
        raise ValueError(f"predicted_words is not a list: {type(predicted_words)}")

    predicted_words = [str(word) for word in predicted_words if word]
    if not predicted_words:
        raise ValueError("No valid words extracted from audio")

    # Align phonemes to words
    alignment_start = time.time()
    flattened_phoneme_predictions = [item for sublist in phoneme_predictions for item in sublist]
    predicted_words_phonemes = g2p(" ".join(predicted_words))
    alignment = align_phonemes_to_words(flattened_phoneme_predictions, predicted_words_phonemes)
    phoneme_predictions = [pred_phonemes for _, pred_phonemes, _ in alignment]
    print(f"Phoneme-to-word alignment took {time.time() - alignment_start:.3f}s")
    print("aligned phoneme predictions: ", phoneme_predictions)

    # Process word alignment
    word_alignment_start = time.time()
    ground_truth_words = [word for word, _ in ground_truth_phonemes]
    results = process_word_alignment(
        ground_truth_words=ground_truth_words,
        ground_truth_phonemes=ground_truth_phonemes,
        predicted_words=predicted_words,
        phoneme_predictions=phoneme_predictions
    )
    print(f"Word alignment processing took {time.time() - word_alignment_start:.3f}s")

    return results


async def _process_chunked_audio(audio_array, sampling_rate, audio_duration,
                                  phoneme_extraction_model, word_extraction_model):
    """Process long audio by splitting into chunks at silence boundaries."""
    from .audio_chunking import chunk_audio_at_silence, merge_chunk_results

    print(f"Audio is {audio_duration:.1f}s - using chunking strategy")
    chunks, chunk_metadata = chunk_audio_at_silence(audio_array, sampling_rate)

    # Filter out chunks that are too short (< 0.3s) and merge with previous
    filtered_chunks = []
    filtered_metadata = []

    for i, (chunk, metadata) in enumerate(zip(chunks, chunk_metadata)):
        if metadata['duration'] < 0.3:
            if filtered_chunks:
                print(f"  Chunk {i+1} too short ({metadata['duration']:.2f}s) - merging with previous chunk")
                filtered_chunks[-1] = np.concatenate([filtered_chunks[-1], chunk])
                filtered_metadata[-1]['duration'] += metadata['duration']
                filtered_metadata[-1]['end_time'] = metadata['end_time']
                filtered_metadata[-1]['num_samples'] += metadata['num_samples']
            else:
                print(f"  Chunk {i+1} too short ({metadata['duration']:.2f}s) - keeping anyway")
                filtered_chunks.append(chunk)
                filtered_metadata.append(metadata)
        else:
            filtered_chunks.append(chunk)
            filtered_metadata.append(metadata)

    chunks = filtered_chunks
    chunk_metadata = filtered_metadata

    all_chunk_phonemes = []
    all_chunk_words = []

    for i, (chunk, metadata) in enumerate(zip(chunks, chunk_metadata)):
        print(f"  Processing chunk {i+1}/{len(chunks)} ({metadata['duration']:.1f}s)...")

        try:
            phoneme_predictions = await asyncio.to_thread(
                phoneme_extraction_model.extract_phoneme,
                audio=chunk,
                sampling_rate=sampling_rate
            )
            predicted_words = await asyncio.to_thread(
                word_extraction_model.extract_words,
                audio=chunk,
                sampling_rate=sampling_rate
            )

            all_chunk_phonemes.append(phoneme_predictions)
            all_chunk_words.append(predicted_words)
        except ValueError as e:
            print(f"  Skipping chunk {i+1}: {e}")
            all_chunk_phonemes.append([])
            all_chunk_words.append([])

    print(f"All chunks processed - merging results...")
    return merge_chunk_results(all_chunk_phonemes, all_chunk_words, chunk_metadata)


async def _process_single_audio(audio_array, sampling_rate, audio_duration,
                                 phoneme_extraction_model, word_extraction_model):
    """Process short audio without chunking using concurrent extraction."""
    print(f"Audio is {audio_duration:.1f}s - processing without chunking")

    print("  Starting concurrent extraction tasks...")
    phoneme_predictions_task = asyncio.create_task(asyncio.to_thread(
        phoneme_extraction_model.extract_phoneme, audio=audio_array, sampling_rate=sampling_rate
    ))
    predicted_words_task = asyncio.create_task(asyncio.to_thread(
        word_extraction_model.extract_words, audio=audio_array, sampling_rate=sampling_rate
    ))

    print("  Waiting for phoneme extraction...")
    phoneme_predictions = await phoneme_predictions_task
    print("  Phoneme extraction completed")

    print("  Waiting for word extraction...")
    predicted_words = await predicted_words_task
    print("  Word extraction completed")

    return phoneme_predictions, predicted_words


async def process_audio_with_client_phonemes(
    client_phonemes: list[list[str]],
    ground_truth_phonemes: list[tuple[str, list[str]]],
    audio_array: np.ndarray,
    sampling_rate: int = 16000,
    word_extraction_model=None,
    client_words: list[str] | None = None,
) -> list[dict]:
    """
    Process audio using client-provided phonemes (and optionally words).

    Used when the frontend has already extracted phonemes using the client-side
    model (eSpeak). Phonemes should already be normalized to IPA format.

    Args:
        client_phonemes: List of words, each a list of IPA phoneme strings.
        ground_truth_phonemes: List of (word, phonemes) tuples for expected sentence.
        audio_array: Audio data as numpy array.
        sampling_rate: Audio sampling rate (default 16000).
        word_extraction_model: Model to extract words (optional).
        client_words: Word strings extracted on client (optional).

    Returns:
        list[dict]: Word-level pronunciation analysis results.
    """
    if len(ground_truth_phonemes) <= 1:
        raise ValueError("ground_truth_phonemes must have at least 2 elements")

    # Only preprocess audio if we need to extract words from it
    if client_words is None or len(client_words) == 0:
        audio_array = preprocess_audio(audio=audio_array, sr=sampling_rate)

    # Determine if we need to extract words
    if client_words is not None and len(client_words) > 0:
        print(f"Using client-provided words: {client_words}")
        predicted_words = client_words
    else:
        if word_extraction_model is None:
            word_extraction_model = WordExtractor()

        print("Extracting words from audio (client phonemes provided, but not words)...")
        predicted_words = await asyncio.to_thread(
            word_extraction_model.extract_words,
            audio=audio_array,
            sampling_rate=sampling_rate
        )
        print(f"Word extraction completed: {predicted_words}")

    if predicted_words is None or len(predicted_words) <= 1:
        raise ValueError("The audio provided has no speech inside")

    phoneme_predictions = client_phonemes
    print(f"Using client-provided phonemes ({len(phoneme_predictions)} words)")

    if len(phoneme_predictions) != len(predicted_words):
        print(f"Warning: Client phoneme word count ({len(phoneme_predictions)}) "
              f"doesn't match word count ({len(predicted_words)})")

    ground_truth_words = [word for word, _ in ground_truth_phonemes]
    results = process_word_alignment(
        ground_truth_words=ground_truth_words,
        ground_truth_phonemes=ground_truth_phonemes,
        predicted_words=predicted_words,
        phoneme_predictions=phoneme_predictions
    )

    return results
