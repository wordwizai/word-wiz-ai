"""
Phoneme Error Rate (PER) calculation and sequence alignment utilities.

Provides Levenshtein distance-based metrics for comparing phoneme sequences
and aligning ground truth with predicted sequences.
"""

import numpy as np


def compute_per(gt_phonemes, pred_phonemes):
    """
    Compute the Phoneme Error Rate (PER) between two phoneme sequences.

    Uses Levenshtein distance normalized by the length of the ground truth.

    Args:
        gt_phonemes: List of ground truth phoneme strings.
        pred_phonemes: List of predicted phoneme strings.

    Returns:
        float: PER value (0.0 = perfect match, 1.0 = completely wrong).
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


def align_sequences(gt, pred):
    """
    Align ground truth and predicted phoneme sequences using edit distance
    with backtracking to produce an operation list.

    Uses dynamic programming to compute the minimum edit distance between
    the two sequences, then backtraces to determine the optimal alignment.

    Args:
        gt: List of ground truth phoneme strings.
        pred: List of predicted phoneme strings.

    Returns:
        list[tuple]: List of operations, each a tuple of:
            (op_type, gt_phoneme, pred_phoneme) where op_type is one of:
            - 'match': gt and pred phonemes are identical
            - 'substitution': gt phoneme was replaced by pred phoneme
            - 'deletion': gt phoneme has no corresponding pred (pred is None)
            - 'insertion': pred phoneme has no corresponding gt (gt is None)
    """
    m, n = len(gt), len(pred)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

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
        if i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + (0 if gt[i - 1] == pred[j - 1] else 1):
            if gt[i - 1] == pred[j - 1]:
                operations.append(('match', gt[i - 1], pred[j - 1]))
            else:
                operations.append(('substitution', gt[i - 1], pred[j - 1]))
            i -= 1
            j -= 1
        elif i > 0 and dp[i][j] == dp[i - 1][j] + 1:
            operations.append(('deletion', gt[i - 1], None))
            i -= 1
        elif j > 0 and dp[i][j] == dp[i][j - 1] + 1:
            operations.append(('insertion', None, pred[j - 1]))
            j -= 1
    operations.reverse()
    return operations
