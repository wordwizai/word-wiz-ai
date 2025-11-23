import asyncio
import json
from typing import override

from core.gpt_output_validator import validate_and_log
from core.modes.base_mode import BaseMode
from core.phoneme_assistant import PhonemeAssistant
from models.session import Session as UserSession
from schemas.feedback_entry import AudioAnalysis


class ChoiceStoryPractice(BaseMode):
    """
    The Choice Story Practice Mode allows the user to get unlimited practice but they get to choose their
    own adventure along the way. It offers them two choices (actions) to follow and adapts the story that way
    Each session follows a different plot outlined in the activity config
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
        past_sentences = []

        previous_utterances = session.feedback_entries
        for entry in previous_utterances:
            past_problem_summaries.append(
                entry.phoneme_analysis.get("problem_summary", {})
            )
            past_sentences.append(entry.sentence)

        # Enhance pronunciation data with phoneme breakdowns for better GPT context
        enhanced_pronunciation = []
        for word_data in pronunciation_data:
            enhanced_word = {
                **word_data,
                # Add expected phoneme breakdown
                "expected_phonemes": word_data.get("ground_truth_phonemes", []),
                "actual_phonemes": word_data.get("phonemes", []),
                # Create a readable word structure showing phoneme composition
                "word_structure": f"{word_data.get('ground_truth_word', '')} = [{', '.join(word_data.get('ground_truth_phonemes', []))}]"
            }
            enhanced_pronunciation.append(enhanced_word)

        # Send FULL problem_summary instead of simplified version
        full_problem_summary = {
            **problem_summary,  # Include ALL fields from problem_summary
            # Explicitly highlight key fields for GPT attention
            "phoneme_error_counts": problem_summary.get("phoneme_error_counts", {}),
            "recommended_focus_phoneme": problem_summary.get("recommended_focus_phoneme"),
            "high_frequency_errors": problem_summary.get("high_frequency_errors", []),
            "articulatory_info": problem_summary.get("articulatory_info", {}),
            "difficulty_level": problem_summary.get("difficulty_level", "medium")
        }

        user_input = {
            "role": "user",
            "content": json.dumps(
                {
                    "story_context": session.activity.activity_settings.get(
                        "story_context", ""
                    ),
                    "past_sentences": past_sentences,
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
                    "core/gpt_prompts/choice_story_mode_prompt_v4.txt"
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
