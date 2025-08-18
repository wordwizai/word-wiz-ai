import asyncio
import json
from typing import override

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

        # Create simplified data for LLM to reduce input size
        simplified_problem_summary = {
            "phoneme_error_counts": problem_summary.get("phoneme_error_counts", {}),
            "recommended_focus_phoneme": problem_summary.get("recommended_focus_phoneme")
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
                    "pronunciation": pronunciation_data,
                    "highest_per_word": highest_per_word_data,
                    "problem_summary": simplified_problem_summary,
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

        return json_response
