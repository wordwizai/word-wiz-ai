import asyncio
import json
from typing import override

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

        user_input = {
            "role": "user",
            "content": json.dumps(
                {
                    "attempted_sentence": attempted_sentence,
                    "pronunciation": pronunciation_data,
                    "highest_per_word": highest_per_word_data,
                    "problem_summary": problem_summary,
                    "past_problem_summaries": past_problem_summaries,
                    "per_summary": per_summary,
                }
            ),
        }
        conversation_history = [
            {
                "role": "system",
                "content": phoneme_assistant.load_prompt(
                    "core/gpt_prompts/unlimited_mode_prompt_v2.txt"
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
