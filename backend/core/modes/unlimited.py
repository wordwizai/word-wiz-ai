import asyncio
import json
from typing_extensions import override

from core.gpt_output_validator import validate_and_log
from core.modes.base_mode import BaseMode
from core.phoneme_assistant import PhonemeAssistant
from core.phoneme_feedback_formatter import build_phoneme_to_error_words
from models.session import Session as UserSession
from schemas.feedback_entry import AudioAnalysis


class UnlimitedPractice(BaseMode):
    """
    Unlimited Practice Mode for continuous practice without a set limit.
    """

    @override
    async def get_next_sentence(
        self,
        attempted_sentence: str,
        analysis: AudioAnalysis,
        phoneme_assistant: PhonemeAssistant,
        session: UserSession,
    ) -> dict:
        """
        Generate the next practice sentence targeting the user's problem phonemes.

        Feedback text is generated locally by phoneme_feedback_formatter before
        this method is called, so GPT only needs to produce the sentence.
        """
        per_summary = analysis.per_summary
        pronunciation_data = analysis.pronunciation_dataframe.to_dict("records")
        problem_summary = analysis.problem_summary

        phoneme_to_error_words = build_phoneme_to_error_words(pronunciation_data)

        gpt_problem_summary = {
            "recommended_focus_phoneme": problem_summary.get("recommended_focus_phoneme"),
            "phoneme_to_error_words": phoneme_to_error_words,
            "phoneme_error_counts": problem_summary.get("phoneme_error_counts", {}),
        }

        user_input = {
            "role": "user",
            "content": json.dumps(
                {
                    "attempted_sentence": attempted_sentence,
                    "problem_summary": gpt_problem_summary,
                    "per_summary": per_summary,
                }
            ),
        }
        conversation_history = [
            {
                "role": "system",
                "content": phoneme_assistant.load_prompt(
                    "core/gpt_prompts/unlimited_mode_next_sentence_v1.txt",
                    include_ssml=False,
                ),
            },
            user_input,
        ]

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, phoneme_assistant.query_gpt, conversation_history
        )
        json_response = phoneme_assistant.extract_json(response)

        # Reuse validator to check sentence phoneme density
        validated_response = validate_and_log(
            json_response,
            pronunciation_data,
            gpt_problem_summary,
            include_warnings_in_response=False,
        )
        return validated_response
