from collections import Counter, defaultdict

class SpeechProblemClassifier:
    """
    Analyzes speech analysis results to detect the most common phoneme or word-level problems,
    including classification of phoneme errors by group.
    """

    # Define phoneme groups in IPA
    PHONEME_GROUPS = {
        "vowels": {"i", "ɪ", "e", "ɛ", "æ", "a", "ɑ", "ɒ", "ɔ", "o", "ʊ", "u", "ə", "ɚ", "ɝ", "ɨ", "ʉ", "ɯ", "ɤ", "ø", "y"},
        "plosives": {"p", "b", "t", "d", "k", "g", "ʔ"},
        "fricatives": {"f", "v", "θ", "ð", "s", "z", "ʃ", "ʒ", "ç", "ʝ", "x", "ɣ", "χ", "ʁ", "ħ", "ʕ", "h", "ɦ"},
        "nasals": {"m", "n", "ŋ", "ɱ", "ɳ", "ɲ", "ŋ̊"},
        "liquids": {"l", "ɫ", "r", "ɾ", "ɹ", "ɻ"},
        "glides": {"w", "j", "ɥ", "ʍ"},
    }

    @staticmethod
    def classify_problems(results):
        """
        Analyzes the results to find the most common phoneme and word-level problems,
        and classifies phoneme errors by group.

        Args:
            results (list): List of dictionaries containing phoneme and word-level analysis.

        Returns:
            dict: A summary of the most common problems.
        """
        phoneme_errors = Counter()
        word_errors = Counter()
        phoneme_group_errors = defaultdict(Counter)

        for result in results:
            if result["type"] in ("match", "substitution"):
                # Count missed, added, and substituted phonemes
                phoneme_errors.update(result.get("missed", []))
                phoneme_errors.update(result.get("added", []))
                phoneme_errors.update([sub[0] for sub in result.get("substituted", [])])  # Incorrect phonemes

                # Classify errors by phoneme group
                for phoneme in result.get("missed", []):
                    SpeechProblemClassifier._update_group_errors(phoneme_group_errors, phoneme)
                for phoneme in result.get("added", []):
                    SpeechProblemClassifier._update_group_errors(phoneme_group_errors, phoneme)
                for sub in result.get("substituted", []):
                    SpeechProblemClassifier._update_group_errors(phoneme_group_errors, sub[0])  # Incorrect phoneme

            elif result["type"] == "deletion":
                # Count missing words
                word_errors[result["ground_truth_word"]] += 1

            elif result["type"] == "insertion":
                # Count extra predicted words
                word_errors[result["predicted_word"]] += 1

        # Find the most common phoneme and word errors
        most_common_phoneme = phoneme_errors.most_common(1)
        most_common_word = word_errors.most_common(1)

        # Summarize phoneme group errors
        phoneme_group_summary = {
            group: sum(counts.values()) for group, counts in phoneme_group_errors.items()
        }

        return {
            "most_common_phoneme": most_common_phoneme[0] if most_common_phoneme else None,
            "most_common_word": most_common_word[0] if most_common_word else None,
            "phoneme_error_counts": dict(phoneme_errors),
            "word_error_counts": dict(word_errors),
            "phoneme_group_errors": phoneme_group_summary,
        }

    @staticmethod
    def _update_group_errors(group_errors, phoneme):
        """
        Updates the phoneme group error counts.

        Args:
            group_errors (defaultdict): A defaultdict of Counters for phoneme groups.
            phoneme (str): The phoneme to classify and count.
        """
        for group, phonemes in SpeechProblemClassifier.PHONEME_GROUPS.items():
            if phoneme in phonemes:
                group_errors[group][phoneme] += 1
                break

if __name__ == "__main__":
    from audio_recording import record_and_process_pronunciation
    from process_audio import analyze_results
    results, ground_truth_phonemes = record_and_process_pronunciation(
        "the quick brown fox jumped over the lazy dog",
        use_previous_recording=True
    )
        
    df, highest_per_word, problem_summary = analyze_results(results)
    print(problem_summary)