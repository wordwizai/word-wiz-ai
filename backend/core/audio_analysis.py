"""
Audio analysis result aggregation.

Aggregates word-level pronunciation data into summary statistics
including PER, problem classification, and highest-error word identification.
"""

import pandas as pd
from .speech_problem_classifier import SpeechProblemClassifier


def analyze_results(pronunciation_data: list[dict]) -> tuple[pd.DataFrame, dict, dict, dict]:
    """
    Analyze pronunciation results and produce summary statistics.

    Args:
        pronunciation_data: List of word-level result dicts from alignment,
            each containing 'per', 'total_phonemes', 'total_errors', etc.

    Returns:
        tuple of:
            - DataFrame of word-level results
            - dict of the highest PER word
            - dict of problem summary (from SpeechProblemClassifier)
            - dict of sentence-level PER summary
    """
    df = pd.DataFrame(pronunciation_data)

    # Get the highest PER word
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

    return df, highest_per, problem_summary, per_summary
