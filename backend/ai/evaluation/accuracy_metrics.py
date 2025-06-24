import editdistance

def flatten_phoneme_list(phoneme_list):
    """
    Convert a list of lists (phonemes per word) into a single list.
    """
    return [ph for word in phoneme_list for ph in word]

def normalize_phonemes(phoneme_seq):
    """
    Optionally remove stress markers (digits) or other symbols to enable a more lenient comparison.
    For instance, 'AH0' -> 'AH'. Adjust the normalization as needed.
    """
    normalized = []
    for ph in phoneme_seq:
        # Remove any digits that might represent stress
        ph_norm = ''.join([ch for ch in ph if not ch.isdigit()])
        normalized.append(ph_norm)
    return normalized

def compute_phoneme_error_rate(ground_truth, hypothesis):
    """
    Compute the phoneme error rate (PER) as the Levenshtein edit distance 
    divided by the number of phonemes in the ground truth.
    Both ground_truth and hypothesis should be lists of phoneme tokens.
    """
    distance = editdistance.eval(ground_truth, hypothesis)
    per = distance / len(ground_truth) if ground_truth else 0
    return per

