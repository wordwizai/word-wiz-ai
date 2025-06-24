import numpy as np

def compute_per(gt_phonemes, pred_phonemes):
    """
    Compute the Phoneme Error Rate (PER) between two phoneme sequences.
    """
    # idk how this algorythm works but I now have an idea
    # comments for further understanding


    # Ex phonemes
    # gt: ['h', 'ɛ', 'l', 'o', 'ʊ']
    # pred: ['h', 'i', 'l', 'ʊ']
    m, n = len(gt_phonemes), len(pred_phonemes)

    # m: 


    dp = np.zeros((m + 1, n + 1), dtype=int)

    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if gt_phonemes[i - 1] == pred_phonemes[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(
                    dp[i - 1][j],    # Deletion
                    dp[i][j - 1],    # Insertion
                    dp[i - 1][j - 1] # Substitution
                )
    return dp[m][n] / max(m, 1)

def align_phonemes_to_words(pred_phonemes, gt_words_phonemes):
    """
    Align predicted phonemes to ground truth words using dynamic programming to minimize total PER.
    
    Parameters:
    - pred_phonemes: List of predicted phonemes.
    - gt_words_phonemes: List of tuples (word, [phonemes]) representing ground truth words and their phonemes.
    
    Returns:
    - alignment: List of tuples (word, aligned_pred_phonemes, per) representing the alignment.
    """
    n = len(pred_phonemes)
    m = len(gt_words_phonemes)
    dp = [ [float('inf')] * (n + 1) for _ in range(m + 1) ]
    backtrack = [ [None] * (n + 1) for _ in range(m + 1) ]
    dp[0][0] = 0

    for i in range(1, m + 1):
        gt_word, gt_phs = gt_words_phonemes[i - 1]
        for j in range(i, n + 1):
            for k in range(i - 1, j):
                pred_segment = pred_phonemes[k:j]
                per = compute_per(gt_phs, pred_segment)
                cost = dp[i - 1][k] + per
                if cost < dp[i][j]:
                    dp[i][j] = cost
                    backtrack[i][j] = k

    # Backtracking to find the alignment
    alignment = []
    i, j = m, n
    while i > 0:
        k = backtrack[i][j]
        gt_word, gt_phs = gt_words_phonemes[i - 1]
        pred_segment = pred_phonemes[k:j]
        per = compute_per(gt_phs, pred_segment)
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


