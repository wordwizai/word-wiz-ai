import numpy as np
from functools import lru_cache

# Optimized PER computation with caching
@lru_cache(maxsize=1024)
def _cached_compute_per(gt_tuple, pred_tuple):
    """Cached version of compute_per using tuples for hashability"""
    return _compute_per_core(list(gt_tuple), list(pred_tuple))

def _compute_per_core(gt_phonemes, pred_phonemes):
    """
    Core PER computation with optimizations
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
    
    # Initialize first row and column
    dp[0, :] = np.arange(n + 1)
    dp[:, 0] = np.arange(m + 1)
    
    # Fill DP table
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if gt_phonemes[i - 1] == pred_phonemes[j - 1]:
                dp[i, j] = dp[i - 1, j - 1]
            else:
                dp[i, j] = 1 + min(
                    dp[i - 1, j],      # Deletion
                    dp[i, j - 1],      # Insertion
                    dp[i - 1, j - 1]   # Substitution
                )
    
    return dp[m, n] / max(m, 1)

def compute_per(gt_phonemes, pred_phonemes):
    """
    Compute the Phoneme Error Rate (PER) between two phoneme sequences.
    Optimized version with caching and fast paths.
    """
    return _cached_compute_per(tuple(gt_phonemes), tuple(pred_phonemes))

def align_phonemes_to_words(pred_phonemes, gt_words_phonemes):
    """
    Align predicted phonemes to ground truth words using optimized dynamic programming.
    
    Parameters:
    - pred_phonemes: List of predicted phonemes.
    - gt_words_phonemes: List of tuples (word, [phonemes]) representing ground truth words and their phonemes.
    
    Returns:
    - alignment: List of tuples (word, aligned_pred_phonemes, per) representing the alignment.
    """
    if not pred_phonemes or not gt_words_phonemes:
        return []
    
    n = len(pred_phonemes)
    m = len(gt_words_phonemes)
    
    # Use more efficient data types and initialization
    dp = np.full((m + 1, n + 1), np.inf, dtype=np.float32)
    backtrack = np.full((m + 1, n + 1), -1, dtype=np.int32)
    dp[0, 0] = 0
    
    # Precompute word lengths for smarter bounds
    word_lengths = [len(phonemes) for _, phonemes in gt_words_phonemes]

    for i in range(1, m + 1):
        gt_word, gt_phs = gt_words_phonemes[i - 1]
        gt_phs_tuple = tuple(gt_phs)  # For caching
        
        # Optimize search bounds based on expected word lengths
        min_j = max(i, sum(word_lengths[:i-1]))
        max_j = min(n + 1, sum(word_lengths[:i]) + 5)  # Allow some flexibility
        
        for j in range(min_j, max_j):
            best_cost = np.inf
            best_k = -1
            
            # Further optimize inner loop bounds
            min_k = max(i - 1, j - len(gt_phs) - 3)
            max_k = min(j, n)
            
            for k in range(min_k, max_k):
                if dp[i - 1, k] == np.inf:
                    continue
                    
                pred_segment = pred_phonemes[k:j]
                
                # Quick length-based pruning
                len_diff = abs(len(gt_phs) - len(pred_segment))
                if len_diff > max(len(gt_phs), 1):  # Simple heuristic
                    continue
                
                # Use cached PER computation
                per = _cached_compute_per(gt_phs_tuple, tuple(pred_segment))
                
                # Early termination for perfect matches
                if per == 0.0:
                    best_cost = dp[i - 1, k]
                    best_k = k
                    break
                
                cost = dp[i - 1, k] + per
                if cost < best_cost:
                    best_cost = cost
                    best_k = k
            
            if best_k != -1:
                dp[i, j] = best_cost
                backtrack[i, j] = best_k

    # Backtracking to find the alignment
    alignment = []
    i, j = m, n
    while i > 0:
        k = backtrack[i, j]
        if k == -1:
            # Fallback for no valid alignment
            alignment.append((gt_words_phonemes[i - 1][0], [], 1.0))
            i -= 1
            continue
            
        gt_word, gt_phs = gt_words_phonemes[i - 1]
        pred_segment = pred_phonemes[k:j]
        per = _cached_compute_per(tuple(gt_phs), tuple(pred_segment))
        alignment.append((gt_word, pred_segment, per))
        i -= 1
        j = k

    alignment.reverse()
    return alignment

if __name__ == "__main__":
    predicted_phonemes = ['ð', 't','ə', 'b', 'k', 'ɑ', 't', 'ʧ', 'ə', 'f', 'd', 't', 'ɔ', 'n']
    ground_truth = [
        ('the', ['ð', 'ə']),
        ('cat', ['k', 'æ', 't']),
        ('jumped', ['ʤ', 'ə', 'm', 'p', 't']),
        ('on', ['ɔ', 'n'])
    ]

    # alignment = align_phonemes_to_words(predicted_phonemes, ground_truth)
    # for word, pred_phs, per in alignment:
    #     print(f"Word: {word}, Predicted Phonemes: {pred_phs}, PER: {per:.2f}")

    gt_flattened = []# haha get flattened
    for val in ground_truth:
        for val2 in val[1]: # skibidi naming here
            gt_flattened.append(val2)
    test_per = compute_per(pred_phonemes=predicted_phonemes, gt_phonemes=gt_flattened)


