"""
Phoneme-to-word alignment algorithms.

Aligns predicted phonemes from audio extraction to ground truth words
using dynamic programming with confidence scoring, adaptive search bounds,
and fallback strategies.
"""

import numpy as np
from .per_calculator import compute_per, align_sequences


def align_phonemes_to_words(pred_phonemes: list, gt_words_phonemes: list[tuple[str, list[str]]]):
    """
    Align predicted phonemes to ground truth words using robust dynamic programming.

    Includes confidence scoring, adaptive search bounds, and fallback strategies
    for improved resilience to extraction errors.

    Args:
        pred_phonemes: List of predicted phoneme strings.
        gt_words_phonemes: List of (word, [phonemes]) tuples for ground truth.

    Returns:
        list[tuple]: List of (word, aligned_pred_phonemes, per) tuples.
    """
    if not pred_phonemes or not gt_words_phonemes:
        print("Warning: Empty input to align_phonemes_to_words")
        return []

    # Calculate length ratio as confidence indicator
    expected_phonemes = sum(len(phonemes) for _, phonemes in gt_words_phonemes)
    length_ratio = len(pred_phonemes) / max(expected_phonemes, 1)

    if length_ratio < 0.5 or length_ratio > 2.0:
        print(f"Alignment warning: Predicted phonemes ({len(pred_phonemes)}) vs expected ({expected_phonemes}), ratio={length_ratio:.2f}")

    # Use fallback alignment for extreme variance
    if length_ratio > 2.5 or length_ratio < 0.4:
        print(f"Extreme phoneme variance ({length_ratio:.2f}x) - using fallback alignment")
        return _fallback_proportional_alignment(pred_phonemes, gt_words_phonemes, length_ratio)

    n = len(pred_phonemes)
    m = len(gt_words_phonemes)

    dp = np.full((m + 1, n + 1), np.inf, dtype=np.float32)
    backtrack = np.full((m + 1, n + 1), -1, dtype=np.int32)
    confidence = np.zeros((m + 1, n + 1), dtype=np.float32)
    dp[0, 0] = 0
    confidence[0, 0] = 1.0

    word_lengths = [len(phonemes) for _, phonemes in gt_words_phonemes]

    for i in range(1, m + 1):
        gt_word, gt_phs = gt_words_phonemes[i - 1]
        expected_length = len(gt_phs)

        # Adaptive search bounds based on phoneme variance
        flexibility = max(8, int(expected_length * abs(length_ratio - 1.0) + 5))
        min_j = max(i, sum(word_lengths[:i-1]) - flexibility)
        max_j = min(n + 1, sum(word_lengths[:i]) + flexibility)

        for j in range(min_j, max_j):
            best_cost = np.inf
            best_k = -1
            best_conf = 0.0

            min_k = max(0, j - expected_length - flexibility)
            max_k = min(j, n)

            for k in range(min_k, max_k):
                if dp[i - 1, k] == np.inf:
                    continue

                pred_segment = pred_phonemes[k:j]

                len_diff = abs(len(gt_phs) - len(pred_segment))
                if len_diff > max(len(gt_phs) * 1.5, 2):
                    continue

                distance = compute_per(gt_phs, pred_segment) * max(len(gt_phs), 1)

                per = distance / max(len(gt_phs), 1)
                length_match = 1.0 - min(len_diff / max(expected_length, 1), 1.0)
                segment_confidence = (
                    0.5 * (1.0 - min(per, 1.0)) +
                    0.3 * length_match +
                    0.2 * confidence[i-1, k]
                )

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
                confidence[i, j] = best_conf

    # Backtracking to find the alignment
    alignment = []
    failed_alignments = 0
    low_confidence_alignments = 0
    i, j = m, n
    word_confidences = []

    while i > 0:
        k = backtrack[i, j]
        gt_word, gt_phs = gt_words_phonemes[i - 1]

        if k == -1:
            failed_alignments += 1

            if j > 0:
                best_fallback_per = float('inf')
                best_fallback_segment = []
                best_fallback_start = j

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
                    word_confidences.append(0.2)
                    j = best_fallback_start
                    print(f"Fallback alignment for '{gt_word}': {best_fallback_segment} (PER: {best_fallback_per:.2f})")
                else:
                    alignment.append((gt_word, [], 1.0))
                    word_confidences.append(0.0)
                    print(f"No phonemes found for '{gt_word}'")
            else:
                alignment.append((gt_word, [], 1.0))
                word_confidences.append(0.0)
                print(f"No phonemes found for '{gt_word}'")

            i -= 1
            continue

        pred_segment = pred_phonemes[k:j]
        distance = compute_per(gt_phs, pred_segment)
        word_conf = confidence[i, j]

        alignment.append((gt_word, pred_segment, distance))
        word_confidences.append(word_conf)

        if word_conf < 0.3:
            low_confidence_alignments += 1

        i -= 1
        j = k

    alignment.reverse()
    word_confidences.reverse()

    if failed_alignments > 0:
        print(f"Alignment completed with {failed_alignments}/{m} failed word alignments")
    if low_confidence_alignments > 0:
        print(f"{low_confidence_alignments}/{m} alignments have low confidence (<0.3)")

    total_per = sum(per for _, _, per in alignment) / max(len(alignment), 1)
    avg_confidence = sum(word_confidences) / max(len(word_confidences), 1)
    print(f"Alignment confidence: avg PER={total_per:.2f}, avg_conf={avg_confidence:.2f}, length_ratio={length_ratio:.2f}, failed={failed_alignments}")

    return alignment


def _fallback_proportional_alignment(
    pred_phonemes: list,
    gt_words_phonemes: list[tuple[str, list[str]]],
    length_ratio: float
) -> list:
    """
    Fallback alignment strategy when standard alignment fails due to
    extreme phoneme variance. Distributes phonemes proportionally
    across words based on expected lengths.

    Args:
        pred_phonemes: Predicted phonemes from model.
        gt_words_phonemes: Ground truth words with expected phonemes.
        length_ratio: Ratio of predicted to expected phonemes.

    Returns:
        list[tuple]: List of (word, aligned_phonemes, per) tuples.
    """
    print(f"Using proportional fallback alignment (ratio: {length_ratio:.2f})")

    alignment = []
    start_idx = 0

    for i, (word, gt_phs) in enumerate(gt_words_phonemes):
        expected_count = len(gt_phs)

        if length_ratio > 1.0:
            allocated_count = int(expected_count * length_ratio)
        else:
            allocated_count = max(1, int(expected_count * length_ratio))

        end_idx = min(start_idx + allocated_count, len(pred_phonemes))

        if i == len(gt_words_phonemes) - 1:
            end_idx = len(pred_phonemes)

        aligned_phonemes = pred_phonemes[start_idx:end_idx]

        if aligned_phonemes:
            per = compute_per(gt_phs, aligned_phonemes)
        else:
            per = 1.0

        alignment.append((word, aligned_phonemes, per))
        start_idx = end_idx

    print(f"Proportional fallback complete - check alignment quality carefully")
    return alignment


def process_word_alignment(
    ground_truth_words: list[str],
    ground_truth_phonemes: list[tuple[str, list[str]]],
    predicted_words: list[str],
    phoneme_predictions: list[list[str]]
) -> list[dict]:
    """
    Process word alignment and calculate PER for each word.

    Aligns predicted words against ground truth words, then computes
    phoneme-level error details (missed, added, substituted) per word.

    Args:
        ground_truth_words: List of expected words.
        ground_truth_phonemes: List of (word, phonemes) tuples.
        predicted_words: List of predicted words from audio.
        phoneme_predictions: List of predicted phoneme sequences (one per word).

    Returns:
        list[dict]: Word-level analysis results with PER and error details.
    """
    word_ops = align_sequences(ground_truth_words, predicted_words)
    print("Word operations:", word_ops)

    results = []
    gt_idx, pred_idx = 0, 0

    for op, gt_word_op, pred_word_op in word_ops:
        if op in ('match', 'substitution'):
            gt_word = ground_truth_words[gt_idx]
            pred_word = predicted_words[pred_idx]
            gt_phonemes = ground_truth_phonemes[gt_idx][1]
            pred_phonemes = phoneme_predictions[pred_idx]

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
