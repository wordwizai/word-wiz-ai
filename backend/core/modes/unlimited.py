import asyncio
import json
from typing_extensions import override

from core.gpt_output_validator import validate_and_log
from core.modes.base_mode import BaseMode
from core.phoneme_assistant import PhonemeAssistant
from models.session import Session as UserSession
from schemas.feedback_entry import AudioAnalysis


class UnlimitedPractice(BaseMode):
    """
    Unlimited Practice Mode for continuous practice without a set limit.
    This mode allows users to practice indefinitely, focusing on improving their skills.
    """

    @override
    async def get_feedback_and_next_sentence(
        self,
        attempted_sentence,
        analysis: AudioAnalysis,
        phoneme_assistant: PhonemeAssistant,
        session: UserSession,
    ):
        """
        Get the feedback based on the pronunciation.
        This method processes the audio analysis and provides feedback without a limit on attempts.
        """
        per_summary = analysis.per_summary
        pronunciation_data = analysis.pronunciation_dataframe.to_dict("records")
        highest_per_word_data = analysis.highest_per_word
        problem_summary = analysis.problem_summary

        past_problem_summaries = []

        previous_utterances = session.feedback_entries
        for entry in previous_utterances:
            past_problem_summaries.append(
                entry.phoneme_analysis.get("problem_summary", {})
            )

        # Enhance pronunciation data with phoneme breakdowns for better GPT context
        enhanced_pronunciation = []
        for word_data in pronunciation_data:
            # Get ground truth phonemes - might be a list or tuple
            gt_phonemes = word_data.get("ground_truth_phonemes", [])
            # If it's a tuple (word, phonemes), extract just the phonemes
            if isinstance(gt_phonemes, tuple) and len(gt_phonemes) == 2:
                gt_phonemes = gt_phonemes[1]
            # Ensure it's a list
            if not isinstance(gt_phonemes, list):
                gt_phonemes = []
            
            enhanced_word = {
                **word_data,
                # Add expected phoneme breakdown
                "expected_phonemes": gt_phonemes,
                "actual_phonemes": word_data.get("phonemes", []),
                # Create a readable word structure showing phoneme composition
                # Note: ground_truth_word can be None for insertion word alignment types
                "word_structure": f"{word_data.get('ground_truth_word') or ''} = [{', '.join(gt_phonemes)}]"
            }
            enhanced_pronunciation.append(enhanced_word)

        # Create phoneme-to-word mapping showing which words actually had errors with each phoneme
        phoneme_to_error_words = {}
        for word_data in pronunciation_data:
            # Only process words that have errors (per > 0)
            if word_data.get("per", 0) > 0:
                # ground_truth_word can be None for insertion word alignment types
                word = word_data.get("ground_truth_word") or ""
                # Check missed phonemes
                for phoneme in word_data.get("missed", []):
                    if phoneme not in phoneme_to_error_words:
                        phoneme_to_error_words[phoneme] = []
                    phoneme_to_error_words[phoneme].append({"word": word, "error_type": "missed"})
                # Check added phonemes
                for phoneme in word_data.get("added", []):
                    if phoneme not in phoneme_to_error_words:
                        phoneme_to_error_words[phoneme] = []
                    phoneme_to_error_words[phoneme].append({"word": word, "error_type": "added"})
                # Check substituted phonemes (first element is the expected phoneme)
                for sub in word_data.get("substituted", []):
                    expected_phoneme = sub[0] if isinstance(sub, (list, tuple)) and len(sub) > 0 else sub
                    if expected_phoneme not in phoneme_to_error_words:
                        phoneme_to_error_words[expected_phoneme] = []
                    phoneme_to_error_words[expected_phoneme].append({"word": word, "error_type": "substituted"})

        # Send focused problem_summary with only essential fields
        full_problem_summary = {
            "most_common_phoneme": problem_summary.get("most_common_phoneme"),
            "phoneme_error_counts": problem_summary.get("phoneme_error_counts", {}),
            "recommended_focus_phoneme": problem_summary.get("recommended_focus_phoneme"),
            "high_frequency_errors": problem_summary.get("high_frequency_errors", []),
            # NEW: Explicit mapping showing which words had errors with which phonemes
            "phoneme_to_error_words": phoneme_to_error_words
        }

        user_input = {
            "role": "user",
            "content": json.dumps(
                {
                    "attempted_sentence": attempted_sentence,
                    "pronunciation": enhanced_pronunciation,  # Use enhanced version with phoneme breakdowns
                    "highest_per_word": highest_per_word_data,
                    "problem_summary": full_problem_summary,  # Use full version, not simplified
                    "per_summary": per_summary,
                }
            ),
        }
        conversation_history = [
            {
                "role": "system",
                "content": phoneme_assistant.load_prompt(
                    "core/gpt_prompts/unlimited_mode_prompt_v4.txt"
                ),
            }
        ]

        # Add the current user input to the conversation history
        conversation_history.append(user_input)
        print("Conversation history:", conversation_history)

        # Get GPT response
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, phoneme_assistant.query_gpt, conversation_history
        )
        print("GPT Response:", response)
        # get the json from the response
        json_response = phoneme_assistant.extract_json(response)

        # Validate GPT output to catch hallucinations and ensure quality
        validated_response = validate_and_log(
            json_response,
            enhanced_pronunciation,
            full_problem_summary,
            include_warnings_in_response=False  # Set to True for debugging
        )

        return validated_response
