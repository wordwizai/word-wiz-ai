import pandas as pd
from .phoneme_extractor import PhonemeExtractor
from .word_extractor import WordExtractor
import numpy as np
import IPython.display as ipd
import re
import time
import logging
from .evaluation import accuracy_metrics as am
from .grapheme_to_phoneme import grapheme_to_phoneme as g2p
from .evaluation.accuracy_metrics import compute_phoneme_error_rate
from .speech_problem_classifier import SpeechProblemClassifier
from .audio_preprocessing import preprocess_audio
import asyncio

logger = logging.getLogger(__name__)

def compute_per(gt_phonemes, pred_phonemes):
    """
    Compute the Phoneme Error Rate (PER) between two phoneme sequences.
    Optimized version with fast paths and efficient memory usage.
    """
    if not gt_phonemes and not pred_phonemes:
        return 0.0
    if not gt_phonemes:
        return 1.0  # All insertions
    if not pred_phonemes:
        return 1.0  # All deletions
    
    m, n = len(gt_phonemes), len(pred_phonemes)
    
    # Quick check for exact match
    if gt_phonemes == pred_phonemes:
        return 0.0
    
    # Use more efficient data type
    dp = np.zeros((m + 1, n + 1), dtype=np.uint16)

    for i in range(m + 1):
        dp[i, 0] = i
    for j in range(n + 1):
        dp[0, j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if gt_phonemes[i - 1] == pred_phonemes[j - 1]:
                dp[i, j] = dp[i - 1, j - 1]
            else:
                dp[i, j] = 1 + min(
                    dp[i - 1, j],    # Deletion
                    dp[i, j - 1],    # Insertion
                    dp[i - 1, j - 1] # Substitution
                )
    return dp[m, n] / max(m, 1)

def align_phonemes_to_words(pred_phonemes: list, gt_words_phonemes: list[tuple[str, list[str]]]):
    """
    Align predicted phonemes to ground truth words using robust dynamic programming.
    
    Phase 3 enhancement: Includes confidence scoring, adaptive search bounds,
    and fallback strategies for improved resilience to extraction errors.
    
    Parameters:
    - pred_phonemes: List of predicted phonemes.
    - gt_words_phonemes: List of tuples (word, [phonemes]) representing ground truth words and their phonemes.
    
    Returns:
    - alignment: List of tuples (word, aligned_pred_phonemes, per) representing the alignment.
    
    Note:
    - Adaptive search bounds based on phoneme variance (Phase 3)
    - Confidence scoring per word alignment (Phase 3)
    - Fallback handling for failed alignments
    - Logs alignment confidence metrics
    - Handles edge cases (length mismatches, empty predictions)
    """
    if not pred_phonemes or not gt_words_phonemes:
        print("⚠️  Warning: Empty input to align_phonemes_to_words")
        return []
    
    # Calculate length ratio as confidence indicator
    expected_phonemes = sum(len(phonemes) for _, phonemes in gt_words_phonemes)
    length_ratio = len(pred_phonemes) / max(expected_phonemes, 1)
    
    # Log potential alignment issues
    if length_ratio < 0.5 or length_ratio > 2.0:
        print(f"⚠️  Alignment warning: Predicted phonemes ({len(pred_phonemes)}) vs expected ({expected_phonemes}), ratio={length_ratio:.2f}")
    
    # Phase 3: Check if we should use fallback alignment strategy
    if length_ratio > 2.5 or length_ratio < 0.4:
        print(f"⚠️  Extreme phoneme variance ({length_ratio:.2f}x) - using fallback alignment")
        return _fallback_proportional_alignment(pred_phonemes, gt_words_phonemes, length_ratio)
    
    n = len(pred_phonemes)
    m = len(gt_words_phonemes)
    
    # Use more efficient data types and initialization
    dp = np.full((m + 1, n + 1), np.inf, dtype=np.float32)
    backtrack = np.full((m + 1, n + 1), -1, dtype=np.int32)
    # Phase 3: Add confidence tracking
    confidence = np.zeros((m + 1, n + 1), dtype=np.float32)
    dp[0, 0] = 0
    confidence[0, 0] = 1.0
    
    # Precompute word lengths for smarter bounds
    word_lengths = [len(phonemes) for _, phonemes in gt_words_phonemes]

    for i in range(1, m + 1):
        gt_word, gt_phs = gt_words_phonemes[i - 1]
        expected_length = len(gt_phs)
        
        # Phase 3: Adaptive search bounds based on phoneme variance
        # Instead of fixed +5, use variance-based flexibility
        flexibility = max(8, int(expected_length * abs(length_ratio - 1.0) + 5))
        min_j = max(i, sum(word_lengths[:i-1]) - flexibility)
        max_j = min(n + 1, sum(word_lengths[:i]) + flexibility)
        
        for j in range(min_j, max_j):
            best_cost = np.inf
            best_k = -1
            best_conf = 0.0  # Phase 3: Track confidence
            
            # Phase 3: Wider search for k based on variance
            min_k = max(0, j - expected_length - flexibility)
            max_k = min(j, n)
            
            for k in range(min_k, max_k):
                if dp[i - 1, k] == np.inf:
                    continue
                    
                pred_segment = pred_phonemes[k:j]
                
                # Quick length-based pruning (Phase 3: more lenient)
                len_diff = abs(len(gt_phs) - len(pred_segment))
                if len_diff > max(len(gt_phs) * 1.5, 2):  # Phase 3: More lenient threshold
                    continue
               
                # Use distance for the cost
                distance = compute_per(gt_phs, pred_segment) * max(len(gt_phs), 1)
                
                # Phase 3: Calculate confidence for this segment
                # Confidence based on: 1) PER, 2) length match, 3) previous confidence
                per = distance / max(len(gt_phs), 1)
                length_match = 1.0 - min(len_diff / max(expected_length, 1), 1.0)
                segment_confidence = (
                    0.5 * (1.0 - min(per, 1.0)) +  # PER contribution
                    0.3 * length_match +             # Length match contribution
                    0.2 * confidence[i-1, k]         # Previous confidence contribution
                )
                
                # Early termination for perfect matches
                if distance == 0.0:
                    best_cost = dp[i - 1, k]
                    best_k = k
                    best_conf = segment_confidence
                    break
                
                cost = dp[i - 1, k] + distance
                if cost < best_cost:
                    best_cost = cost
                    best_k = k
                    best_conf = segment_confidence
            
            if best_k != -1:
                dp[i, j] = best_cost
                backtrack[i, j] = best_k
                confidence[i, j] = best_conf  # Phase 3: Store confidence

    # Backtracking to find the alignment
    alignment = []
    failed_alignments = 0
    low_confidence_alignments = 0
    i, j = m, n
    
    # Phase 3: Track per-word confidence
    word_confidences = []
    
    while i > 0:
        k = backtrack[i, j]
        gt_word, gt_phs = gt_words_phonemes[i - 1]
        
        if k == -1:
            # Fallback for no valid alignment - log and use fallback strategy
            failed_alignments += 1
            
            # Phase 3: Improved fallback - try to find best match in remaining phonemes
            if j > 0:
                # Search for best matching segment in a wider window
                best_fallback_per = float('inf')
                best_fallback_segment = []
                best_fallback_start = j
                
                # Try different segment lengths around expected length
                for seg_len in range(max(1, len(gt_phs) - 3), min(j, len(gt_phs) + 8) + 1):
                    for start in range(max(0, j - seg_len - 5), j - seg_len + 1):
                        if start < 0:
                            continue
                        end = start + seg_len
                        if end > j or end > len(pred_phonemes):
                            continue
                        
                        segment = pred_phonemes[start:end]
                        if segment:
                            per = compute_per(gt_phs, segment)
                            if per < best_fallback_per:
                                best_fallback_per = per
                                best_fallback_segment = segment
                                best_fallback_start = start
                
                if best_fallback_segment:
                    alignment.append((gt_word, best_fallback_segment, best_fallback_per))
                    word_confidences.append(0.2)  # Low confidence for fallback
                    j = best_fallback_start
                    print(f"⚠️  Fallback alignment for '{gt_word}': {best_fallback_segment} (PER: {best_fallback_per:.2f})")
                else:
                    # No predicted phonemes available at all
                    alignment.append((gt_word, [], 1.0))
                    word_confidences.append(0.0)
                    print(f"❌ No phonemes found for '{gt_word}'")
            else:
                # No predicted phonemes left
                alignment.append((gt_word, [], 1.0))
                word_confidences.append(0.0)
                print(f"❌ No phonemes found for '{gt_word}'")
            
            i -= 1
            continue
        
        # Normal alignment
        pred_segment = pred_phonemes[k:j]
        distance = compute_per(gt_phs, pred_segment)
        word_conf = confidence[i, j]
        
        alignment.append((gt_word, pred_segment, distance))
        word_confidences.append(word_conf)
        
        # Phase 3: Flag low confidence alignments
        if word_conf < 0.3:
            low_confidence_alignments += 1
        
        i -= 1
        j = k

    alignment.reverse()
    word_confidences.reverse()
    
    # Phase 3: Enhanced alignment quality metrics
    if failed_alignments > 0:
        print(f"⚠️  Alignment completed with {failed_alignments}/{m} failed word alignments")
    if low_confidence_alignments > 0:
        print(f"⚠️  {low_confidence_alignments}/{m} alignments have low confidence (<0.3)")
    
    # Calculate overall alignment confidence
    total_per = sum(per for _, _, per in alignment) / max(len(alignment), 1)
    avg_confidence = sum(word_confidences) / max(len(word_confidences), 1)
    print(f"📊 Alignment confidence: avg PER={total_per:.2f}, avg_conf={avg_confidence:.2f}, length_ratio={length_ratio:.2f}, failed={failed_alignments}")
    
    return alignment


def _fallback_proportional_alignment(
    pred_phonemes: list,
    gt_words_phonemes: list[tuple[str, list[str]]],
    length_ratio: float
) -> list:
    """
    Fallback alignment strategy when standard alignment fails due to extreme phoneme variance.
    
    Phase 3: Uses proportional distribution of phonemes across words based on expected lengths.
    
    Args:
        pred_phonemes: Predicted phonemes from model
        gt_words_phonemes: Ground truth words with expected phonemes
        length_ratio: Ratio of predicted to expected phonemes
        
    Returns:
        List of (word, aligned_phonemes, per) tuples
    """
    print(f"🔄 Using proportional fallback alignment (ratio: {length_ratio:.2f})")
    
    expected_phonemes = sum(len(phonemes) for _, phonemes in gt_words_phonemes)
    alignment = []
    start_idx = 0
    
    for i, (word, gt_phs) in enumerate(gt_words_phonemes):
        # Allocate phonemes proportionally based on expected length
        expected_count = len(gt_phs)
        
        if length_ratio > 1.0:
            # More phonemes than expected - allocate proportionally more
            allocated_count = int(expected_count * length_ratio)
        else:
            # Fewer phonemes than expected - allocate proportionally
            allocated_count = max(1, int(expected_count * length_ratio))
        
        # Ensure we don't go past the end
        end_idx = min(start_idx + allocated_count, len(pred_phonemes))
        
        # For last word, use all remaining phonemes
        if i == len(gt_words_phonemes) - 1:
            end_idx = len(pred_phonemes)
        
        aligned_phonemes = pred_phonemes[start_idx:end_idx]
        
        if aligned_phonemes:
            per = compute_per(gt_phs, aligned_phonemes)
        else:
            per = 1.0
        
        alignment.append((word, aligned_phonemes, per))
        start_idx = end_idx
    
    print(f"✓ Proportional fallback complete - check alignment quality carefully")
    return alignment


def align_sequences(gt, pred):
    """
    Aligns the ground truth and predicted phoneme sequences using dynamic programming.
    
    Returns a list of operations in the form:
    ('match' | 'substitution' | 'deletion' | 'insertion', ground_truth_phoneme, predicted_phoneme)
    For deletion, predicted_phoneme will be None; for insertion, ground_truth_phoneme will be None.

    honestly just don't touch this function it's perfect - its a black box at this point
    """
    m, n = len(gt), len(pred)
    # Initialize DP matrix where dp[i][j] is the edit distance between gt[:i] and pred[:j]
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    # Base cases: transforming empty sequence to the other requires inserting/deleting all characters.
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    # Fill the DP table
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if gt[i - 1] == pred[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,      # deletion
                dp[i][j - 1] + 1,      # insertion
                dp[i - 1][j - 1] + cost  # substitution or match
            )
    
    # Backtrace to get the alignment operations
    operations = []
    i, j = m, n
    while i > 0 or j > 0:
        # If both indices are positive and we came from a match/substitution:
        if i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + (0 if gt[i - 1] == pred[j - 1] else 1):
            if gt[i - 1] == pred[j - 1]:
                operations.append(('match', gt[i - 1], pred[j - 1]))
            else:
                operations.append(('substitution', gt[i - 1], pred[j - 1]))
            i -= 1
            j -= 1
        # Deletion: came from dp[i-1][j] + 1
        elif i > 0 and dp[i][j] == dp[i - 1][j] + 1:
            operations.append(('deletion', gt[i - 1], None))
            i -= 1
        # Insertion: came from dp[i][j-1] + 1
        elif j > 0 and dp[i][j] == dp[i][j - 1] + 1:
            operations.append(('insertion', None, pred[j - 1]))
            j -= 1
    operations.reverse()
    return operations

def _process_word_alignment(
    ground_truth_words: list[str],
    ground_truth_phonemes: list[tuple[str, list[str]]],
    predicted_words: list[str],
    phoneme_predictions: list[list[str]]
) -> list[dict]:
    """
    Helper function to process word alignment and calculate PER for each word.
    Shared by both process_audio_array and process_audio_with_client_phonemes.
    
    Args:
        ground_truth_words: List of expected words
        ground_truth_phonemes: List of tuples (word, phonemes)
        predicted_words: List of predicted words from audio
        phoneme_predictions: List of predicted phoneme sequences (one per word)
        
    Returns:
        List of dictionaries containing word-level analysis results
    """
    # Align the words
    word_ops = align_sequences(ground_truth_words, predicted_words)
    print("Word operations:", word_ops)
    
    results = []
    gt_idx, pred_idx = 0, 0  # indices for ground truth and predicted phonemes
    
    for op, gt_word_op, pred_word_op in word_ops:
        if op in ('match', 'substitution'):
            gt_word = ground_truth_words[gt_idx]
            pred_word = predicted_words[pred_idx]
            gt_phonemes = ground_truth_phonemes[gt_idx][1]
            pred_phonemes = phoneme_predictions[pred_idx]
            
            # Get phoneme-level alignment
            phoneme_ops = align_sequences(gt_phonemes, pred_phonemes)
            missed, added, substituted = [], [], []
            for pop, gph, pph in phoneme_ops:
                if pop == 'deletion':
                    missed.append(gph)
                elif pop == 'insertion':
                    added.append(pph)
                elif pop == 'substitution':
                    substituted.append((gph, pph))
            
            per = (len(missed) + len(added) + len(substituted)) / max(len(gt_phonemes), 1)
            results.append({
                "type": op,
                "predicted_word": pred_word,
                "ground_truth_word": gt_word,
                "phonemes": pred_phonemes,
                "ground_truth_phonemes": gt_phonemes,
                "per": round(per, 4),
                "missed": missed,
                "added": added,
                "substituted": substituted,
                "total_phonemes": len(gt_phonemes),
                "total_errors": len(missed) + len(added) + len(substituted),
            })
            gt_idx += 1
            pred_idx += 1
        
        elif op == 'insertion':
            # Extra word predicted (no matching ground truth)
            pred_word = predicted_words[pred_idx]
            pred_phonemes = phoneme_predictions[pred_idx]
            results.append({
                "type": op,
                "predicted_word": pred_word,
                "ground_truth_word": None,
                "phonemes": pred_phonemes,
                "ground_truth_phonemes": None,
                "per": None,
                "missed": None,
                "added": None,
                "substituted": None,
                "total_phonemes": 0,
                "total_errors": 0,
                "error": "Extra word predicted."
            })
            pred_idx += 1
        
        elif op == 'deletion':
            # A ground truth word is missing in prediction
            gt_word = ground_truth_words[gt_idx]
            results.append({
                "type": op,
                "predicted_word": None,
                "ground_truth_word": gt_word,
                "phonemes": None,
                "ground_truth_phonemes": None,
                "per": None,
                "missed": None,
                "added": None,
                "substituted": None,
                "total_phonemes": 0,
                "total_errors": 0,
                "error": "Word missing in prediction."
            })
            gt_idx += 1
    
    return results

async def process_audio_array(ground_truth_phonemes, audio_array, sampling_rate=16000, phoneme_extraction_model=None, word_extraction_model=None, use_chunking=True, reference_text=None) -> list[dict]:
    """
    Use the phoneme extractor to transcribe an audio array.
    
    Args:
        ground_truth_phonemes: Expected phonemes as list of (word, phonemes) tuples
        audio_array: Audio signal as numpy array
        sampling_rate: Sample rate (default 16000)
        phoneme_extraction_model: Phoneme extraction model (optional)
        word_extraction_model: Word extraction model (optional)
        use_chunking: Whether to chunk long audio (default True)
        reference_text: Reference text for pronunciation assessment (optional, used by Azure)
        
    Returns:
        List of dictionaries containing pronunciation analysis results
    """
    from .audio_chunking import should_use_chunking, chunk_audio_at_silence, merge_chunk_results
    from .phoneme_extractor_azure import AzurePronunciationExtractor
    
    if phoneme_extraction_model is None:
        phoneme_extraction_model = PhonemeExtractor()
    
    if word_extraction_model is None:
        word_extraction_model = WordExtractor() 
    
    if len(ground_truth_phonemes) <= 1:
        raise ValueError("ground_truth_phonemes must have at least 2 elements)")

    # Calculate audio duration for logging
    audio_duration = len(audio_array) / sampling_rate
    
    # preprocess the audio
    audio_array = preprocess_audio(audio=audio_array, sr=sampling_rate, audio_length_seconds=audio_duration)
    
    # Check if we're using Azure extractor - it has optimized combined extraction
    is_azure = isinstance(phoneme_extraction_model, AzurePronunciationExtractor)
    
    if is_azure and reference_text and hasattr(phoneme_extraction_model, 'extract_words_and_phonemes'):
        # Azure-optimized path: single API call for both words and phonemes
        print(f"🚀 Using Azure optimized extraction with reference text")
        print(f"📝 Audio is {audio_duration:.1f}s")
        
        try:
            # Single call to Azure gets both words and phonemes, already aligned!
            azure_result = await asyncio.to_thread(
                phoneme_extraction_model.extract_words_and_phonemes,
                audio=audio_array,
                sampling_rate=sampling_rate,
                reference_text=reference_text
            )
            
            predicted_words = azure_result['words']
            phoneme_predictions = azure_result['phonemes']
            
            print(f"✅ Azure extraction complete")
            print(f"   Recognized: {azure_result.get('recognized_text', '')}")
            print(f"   Words: {predicted_words}")
            print(f"   Phonemes already aligned to words (no realignment needed)")
            
            # Skip the complex alignment steps - Azure already aligned phonemes to words!
            # Just validate we have data
            if not predicted_words or not phoneme_predictions:
                raise ValueError("Azure returned empty results")
            
            # Use helper function to process word alignment
            word_alignment_start = time.time()
            ground_truth_words = [word for word, _ in ground_truth_phonemes]
            results = _process_word_alignment(
                ground_truth_words=ground_truth_words,
                ground_truth_phonemes=ground_truth_phonemes,
                predicted_words=predicted_words,
                phoneme_predictions=phoneme_predictions
            )
            print(f"⏱️  Word alignment processing took {time.time() - word_alignment_start:.3f}s")
            
            # Enhance results with Azure pronunciation scores if available
            if azure_result.get('words_details'):
                for i, result in enumerate(results):
                    if i < len(azure_result['words_details']):
                        azure_word = azure_result['words_details'][i]
                        result['azure_accuracy'] = azure_word.get('accuracy_score', 0)
                        result['azure_error_type'] = azure_word.get('error_type', 'None')
            
            return results
            
        except Exception as e:
            logger.warning(f"Azure optimized extraction failed: {e}, falling back to standard path")
            # Fall through to standard processing
    
    # Standard processing path (for ONNX, PyTorch, or Azure without reference text)
    
    # Check if audio should be chunked
    if use_chunking and should_use_chunking(audio_array, sampling_rate, threshold_seconds=8):
        print(f"🔪 Audio is {audio_duration:.1f}s - using chunking strategy")
        chunks, chunk_metadata = chunk_audio_at_silence(audio_array, sampling_rate)
        
        # Filter out chunks that are too short (< 0.3s) and merge with previous chunk
        filtered_chunks = []
        filtered_metadata = []
        
        for i, (chunk, metadata) in enumerate(zip(chunks, chunk_metadata)):
            if metadata['duration'] < 0.3:
                # Too short - merge with previous chunk if possible
                if filtered_chunks:
                    print(f"  ⚠️  Chunk {i+1} too short ({metadata['duration']:.2f}s) - merging with previous chunk")
                    filtered_chunks[-1] = np.concatenate([filtered_chunks[-1], chunk])
                    filtered_metadata[-1]['duration'] += metadata['duration']
                    filtered_metadata[-1]['end_time'] = metadata['end_time']
                    filtered_metadata[-1]['num_samples'] += metadata['num_samples']
                else:
                    # First chunk is too short - just add it anyway, validation will be skipped
                    print(f"  ⚠️  Chunk {i+1} too short ({metadata['duration']:.2f}s) - keeping anyway")
                    filtered_chunks.append(chunk)
                    filtered_metadata.append(metadata)
            else:
                filtered_chunks.append(chunk)
                filtered_metadata.append(metadata)
        
        chunks = filtered_chunks
        chunk_metadata = filtered_metadata
        
        # Process each chunk
        all_chunk_phonemes = []
        all_chunk_words = []
        
        for i, (chunk, metadata) in enumerate(zip(chunks, chunk_metadata)):
            print(f"  Processing chunk {i+1}/{len(chunks)} ({metadata['duration']:.1f}s)...")
            
            try:
                # Extract phonemes and words for this chunk
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
                # If chunk still fails validation, skip it
                print(f"  ⚠️  Skipping chunk {i+1}: {e}")
                # Add empty results for this chunk
                all_chunk_phonemes.append([])
                all_chunk_words.append([])
        
        # Merge chunk results
        print(f"✓ All chunks processed - merging results...")
        phoneme_predictions, predicted_words = merge_chunk_results(
            all_chunk_phonemes, 
            all_chunk_words, 
            chunk_metadata
        )
    else:
        # Original processing for short audio
        print(f"📝 Audio is {audio_duration:.1f}s - processing without chunking")
        async def extract_data():
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

        phoneme_predictions, predicted_words = await extract_data()

    if phoneme_predictions is None or predicted_words is None or len(phoneme_predictions) <= 1 or len(predicted_words) <= 1:
        raise ValueError("The audio provided has no speech inside")

    print("unaligned phoneme predictions: ", phoneme_predictions)

    # Validate predicted_words is a list of strings
    if not isinstance(predicted_words, list):
        raise ValueError(f"predicted_words is not a list: {type(predicted_words)}")

    # Filter out any non-string items and ensure we have valid words
    predicted_words = [str(word) for word in predicted_words if word]
    if not predicted_words:
        raise ValueError("No valid words extracted from audio")

    # regroup the phonemes to reflect the words that were spoken
    alignment_start = time.time()
    flattened_phoneme_predictions = [item for sublist in phoneme_predictions for item in sublist]
    predicted_words_phonemes = g2p(" ".join(predicted_words)) # take the words our model thinks we said and get the phonemes for them
    alignment = align_phonemes_to_words(flattened_phoneme_predictions, predicted_words_phonemes)
    phoneme_predictions = [pred_phonemes for _, pred_phonemes,_ in alignment]
    print(f"⏱️  Phoneme-to-word alignment took {time.time() - alignment_start:.3f}s")
    print("aligned phoneme predictions: ", phoneme_predictions)

    # Use helper function to process word alignment
    word_alignment_start = time.time()
    ground_truth_words = [word for word, _ in ground_truth_phonemes]
    results = _process_word_alignment(
        ground_truth_words=ground_truth_words,
        ground_truth_phonemes=ground_truth_phonemes,
        predicted_words=predicted_words,
        phoneme_predictions=phoneme_predictions
    )
    print(f"⏱️  Word alignment processing took {time.time() - word_alignment_start:.3f}s")

    return results

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
    
    This function is used when the frontend has already extracted phonemes using
    the client-side model (eSpeak). The phonemes should already be normalized to
    IPA format before calling this function.
    
    If client_words are provided, word extraction is skipped entirely, saving
    significant processing time (60-80% faster).
    
    Args:
        client_phonemes: List of words, where each word is a list of IPA phoneme strings
                        (already normalized from eSpeak format)
        ground_truth_phonemes: List of tuples (word, phonemes) for the expected sentence
        audio_array: The audio data as a numpy array
        sampling_rate: The audio sampling rate (default: 16000)
        word_extraction_model: The model to extract words (optional, will create if None)
        client_words: List of word strings extracted on client (optional, NEW in Phase 4)
        
    Returns:
        List of dictionaries containing word-level analysis results
    """
    if len(ground_truth_phonemes) <= 1:
        raise ValueError("ground_truth_phonemes must have at least 2 elements")
    
    # Only preprocess audio if we need to extract words from it
    # If client provided both phonemes and words, we don't need the audio at all
    if client_words is None or len(client_words) == 0:
        # Preprocess the audio (needed for word extraction)
        audio_array = preprocess_audio(audio=audio_array, sr=sampling_rate)
    
    # Determine if we need to extract words
    if client_words is not None and len(client_words) > 0:
        # Use client-provided words (skip word extraction)
        print(f"✓ Using client-provided words: {client_words}")
        predicted_words = client_words
    else:
        # Extract words from audio (client didn't provide them)
        if word_extraction_model is None:
            word_extraction_model = WordExtractor()
        
        print("→ Extracting words from audio (client phonemes provided, but not words)...")
        predicted_words = await asyncio.to_thread(
            word_extraction_model.extract_words, 
            audio=audio_array, 
            sampling_rate=sampling_rate
        )
        print(f"✓ Word extraction completed: {predicted_words}")
    
    if predicted_words is None or len(predicted_words) <= 1:
        raise ValueError("The audio provided has no speech inside")
    
    # Use client-provided phonemes directly (already normalized to IPA)
    phoneme_predictions = client_phonemes
    print(f"✓ Using client-provided phonemes ({len(phoneme_predictions)} words)")
    
    # Validate that we have the same number of words in phonemes and word predictions
    # If not, we may need to adjust the alignment
    if len(phoneme_predictions) != len(predicted_words):
        print(f"⚠️ Warning: Client phoneme word count ({len(phoneme_predictions)}) "
              f"doesn't match word count ({len(predicted_words)})")
        # In this case, we'll align based on ground truth words instead
        # This is a safety measure - ideally they should match
    
    # Use helper function to process word alignment
    ground_truth_words = [word for word, _ in ground_truth_phonemes]
    results = _process_word_alignment(
        ground_truth_words=ground_truth_words,
        ground_truth_phonemes=ground_truth_phonemes,
        predicted_words=predicted_words,
        phoneme_predictions=phoneme_predictions
    )
    
    return results

def analyze_results(pronunciation_data: list[dict]) -> tuple[pd.DataFrame, dict, dict, dict]:
    """
    Analyzes the results of phoneme and word extraction.

    Args:
        results (list[dict]): List of word-level results containing phoneme-level details.

    Returns:
        tuple[pd.DataFrame, pd.Series, dict, dict]: DataFrame of word-level results, highest phoneme error rate word, problems, and sentence per 
    """
    df = pd.DataFrame(pronunciation_data)

    # get the highest PER word
    highest_per = df.sort_values("per", ascending=False).iloc[0].to_dict()

    # Get the problem summary
    problem_summary = SpeechProblemClassifier.classify_problems(pronunciation_data)

    # Aggregate phoneme counts and errors for the entire sentence
    total_phonemes = 0
    total_errors = 0

    for word in pronunciation_data:
        total_phonemes += word["total_phonemes"]
        total_errors += word["total_errors"]

    # Calculate sentence-level PER
    sentence_per = total_errors / total_phonemes if total_phonemes > 0 else 0.0

    per_summary = {
        "total_phonemes": total_phonemes,
        "total_errors": total_errors,
        "sentence_per": sentence_per,
    }

    # Return sentence-level PER along with existing results
    return df, highest_per, problem_summary, per_summary

if __name__ == "__main__":
    import librosa
    from grapheme_to_phoneme import grapheme_to_phoneme
    from audio_recording import run_vad


    extractor = PhonemeExtractor()

    # Load the audio file
    # audio, sampling_rate = librosa.load("output.wav", sr=16000)
    run_vad()
    audio, sampling_rate = librosa.load("./temp_audio/output.wav", sr=16000)


    # get ground truth
    ground_truth_phonemes = grapheme_to_phoneme("the quick brown fox jumped over the lazy dog")

    # Process the audio
    results = asyncio.run(process_audio_array(ground_truth_phonemes, audio, sampling_rate, phoneme_extraction_model=extractor))

    # Print the results
    print("Results:")
    print(results)


    for result in results:
        print(result)
    print()
    df, highest_per, problem_summary, per_summary = analyze_results(results)
    print(df)
