from collections import Counter, defaultdict

class SpeechProblemClassifier:
    """
    Analyzes speech analysis results to detect the most common phoneme or word-level problems,
    including classification of phoneme errors by group with enhanced articulatory and pedagogical information.
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
    
    # Articulatory descriptions for teaching feedback
    ARTICULATORY_INFO = {
        # Plosives
        "p": {"place": "lips", "manner": "stop", "voice": "voiceless", "description": "Press your lips together, then release with a puff of air"},
        "b": {"place": "lips", "manner": "stop", "voice": "voiced", "description": "Press your lips together, then release with vibration in your throat"},
        "t": {"place": "tongue tip", "manner": "stop", "voice": "voiceless", "description": "Touch your tongue tip to the roof of your mouth, then release"},
        "d": {"place": "tongue tip", "manner": "stop", "voice": "voiced", "description": "Touch your tongue tip to the roof of your mouth, then release with throat vibration"},
        "k": {"place": "back of tongue", "manner": "stop", "voice": "voiceless", "description": "Lift the back of your tongue to the roof of your mouth, then release"},
        "g": {"place": "back of tongue", "manner": "stop", "voice": "voiced", "description": "Lift the back of your tongue to the roof of your mouth, then release with throat vibration"},
        
        # Fricatives
        "f": {"place": "teeth and lip", "manner": "fricative", "voice": "voiceless", "description": "Gently bite your bottom lip and blow air through"},
        "v": {"place": "teeth and lip", "manner": "fricative", "voice": "voiced", "description": "Gently bite your bottom lip and hum with vibration"},
        "θ": {"place": "tongue and teeth", "manner": "fricative", "voice": "voiceless", "description": "Put your tongue between your teeth and blow air (like 'th' in think)"},
        "ð": {"place": "tongue and teeth", "manner": "fricative", "voice": "voiced", "description": "Put your tongue between your teeth and hum (like 'th' in this)"},
        "s": {"place": "tongue tip", "manner": "fricative", "voice": "voiceless", "description": "Keep your tongue near the roof of your mouth and blow air in a thin stream"},
        "z": {"place": "tongue tip", "manner": "fricative", "voice": "voiced", "description": "Keep your tongue near the roof of your mouth and hum while blowing air"},
        "ʃ": {"place": "tongue body", "manner": "fricative", "voice": "voiceless", "description": "Curl your tongue slightly and blow air (like 'sh')"},
        "ʒ": {"place": "tongue body", "manner": "fricative", "voice": "voiced", "description": "Curl your tongue slightly and hum while blowing air (like 'zh')"},
        "h": {"place": "throat", "manner": "fricative", "voice": "voiceless", "description": "Breathe out gently through an open mouth"},
        
        # Nasals
        "m": {"place": "lips", "manner": "nasal", "voice": "voiced", "description": "Close your lips and hum with air through your nose"},
        "n": {"place": "tongue tip", "manner": "nasal", "voice": "voiced", "description": "Touch your tongue to the roof of your mouth and hum through your nose"},
        "ŋ": {"place": "back of tongue", "manner": "nasal", "voice": "voiced", "description": "Lift the back of your tongue and hum through your nose (like 'ng')"},
        
        # Liquids
        "l": {"place": "tongue tip", "manner": "liquid", "voice": "voiced", "description": "Touch your tongue tip lightly to the roof of your mouth and let air flow around the sides"},
        "r": {"place": "tongue body", "manner": "liquid", "voice": "voiced", "description": "Curl your tongue back slightly without touching the roof of your mouth"},
        "ɹ": {"place": "tongue body", "manner": "liquid", "voice": "voiced", "description": "Curl your tongue back slightly without touching the roof of your mouth"},
        
        # Glides
        "w": {"place": "lips", "manner": "glide", "voice": "voiced", "description": "Round your lips and glide to the next sound"},
        "j": {"place": "tongue body", "manner": "glide", "voice": "voiced", "description": "Raise your tongue toward the roof of your mouth and glide (like 'y')"},
    }
    
    # Phoneme difficulty levels for systematic instruction (1=easiest, 5=most complex)
    PHONEME_DIFFICULTY = {
        # Early sounds (Level 1)
        "m": 1, "a": 1, "t": 1, "s": 1, "i": 1, "f": 1, "d": 1, "r": 1, "o": 1, "g": 1,
        "l": 1, "h": 1, "u": 1, "c": 1, "b": 1, "n": 1, "k": 1, "v": 1, "e": 1, "w": 1,
        "j": 1, "p": 1, "y": 1,
        
        # Intermediate sounds (Level 2-3)
        "z": 2, "qu": 2, "x": 2, "ʃ": 2, "θ": 3, "ð": 3, "ʒ": 3, "ŋ": 3,
        
        # Complex vowels (Level 3-4)
        "ɪ": 3, "ɛ": 3, "æ": 3, "ɑ": 3, "ɔ": 3, "ʊ": 3, "ə": 4,
        
        # Advanced sounds (Level 4-5)
        "ɚ": 4, "ɝ": 4, "ɨ": 5, "ʉ": 5, "ɯ": 5, "ɤ": 5, "ø": 5, "y": 5
    }
    
    # High-frequency phonemes for prioritization
    HIGH_FREQUENCY_PHONEMES = {
        "s", "t", "n", "r", "l", "d", "m", "k", "g", "p", "b", "f", "v", "h", "w", "j", "z"
    }

    @staticmethod
    def classify_problems(results) -> dict:
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

        # Get articulatory information for problematic phonemes
        phoneme_articulatory_info = {}
        phoneme_difficulty_levels = {}
        high_frequency_errors = []
        
        for phoneme, count in phoneme_errors.items():
            if phoneme in SpeechProblemClassifier.ARTICULATORY_INFO:
                phoneme_articulatory_info[phoneme] = SpeechProblemClassifier.ARTICULATORY_INFO[phoneme]
            if phoneme in SpeechProblemClassifier.PHONEME_DIFFICULTY:
                phoneme_difficulty_levels[phoneme] = SpeechProblemClassifier.PHONEME_DIFFICULTY[phoneme]
            if phoneme in SpeechProblemClassifier.HIGH_FREQUENCY_PHONEMES:
                high_frequency_errors.append((phoneme, count))
        
        # Sort high frequency errors by count (most problematic first)
        high_frequency_errors.sort(key=lambda x: x[1], reverse=True)
        
        # Determine recommended focus phoneme based on frequency, difficulty, and utility
        recommended_focus = SpeechProblemClassifier._determine_focus_phoneme(phoneme_errors)

        return {
            "most_common_phoneme": most_common_phoneme[0] if most_common_phoneme else None,
            "most_common_word": most_common_word[0] if most_common_word else None,
            "phoneme_error_counts": dict(phoneme_errors),
            "word_error_counts": dict(word_errors),
            "phoneme_group_errors": phoneme_group_summary,
            "phoneme_articulatory_info": phoneme_articulatory_info,
            "phoneme_difficulty_levels": phoneme_difficulty_levels,
            "high_frequency_errors": high_frequency_errors,
            "recommended_focus_phoneme": recommended_focus,
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
    
    @staticmethod
    def _determine_focus_phoneme(phoneme_errors):
        """
        Determines the recommended focus phoneme based on frequency, difficulty, and pedagogical utility.
        
        Args:
            phoneme_errors (Counter): Counter of phoneme errors
            
        Returns:
            tuple: (phoneme, reasoning) for the recommended focus
        """
        if not phoneme_errors:
            return None
            
        # Priority 1: High-frequency phonemes with errors (most impactful for reading)
        high_freq_with_errors = [
            (phoneme, count) for phoneme, count in phoneme_errors.items()
            if phoneme in SpeechProblemClassifier.HIGH_FREQUENCY_PHONEMES
        ]
        
        if high_freq_with_errors:
            # Sort by error count, but prioritize lower difficulty for struggling readers
            sorted_errors = sorted(high_freq_with_errors, key=lambda x: (
                -x[1],  # Higher error count first
                SpeechProblemClassifier.PHONEME_DIFFICULTY.get(x[0], 3)  # Lower difficulty preferred
            ))
            best_phoneme = sorted_errors[0][0]
            return (best_phoneme, "high_frequency_phoneme")
        
        # Priority 2: Most frequent errors regardless of phoneme type
        most_common = phoneme_errors.most_common(1)
        if most_common:
            return (most_common[0][0], "most_frequent_error")
            
        return None

if __name__ == "__main__":
    from audio_recording import record_and_process_pronunciation
    from process_audio import analyze_results
    results, ground_truth_phonemes = record_and_process_pronunciation(
        "the quick brown fox jumped over the lazy dog",
        use_previous_recording=True
    )
        
    df, highest_per_word, problem_summary = analyze_results(results)
    print(problem_summary)
