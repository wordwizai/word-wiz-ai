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
    def get_feedback_and_next_sentence(
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
        pronunciation_data = analysis.pronunciation_dataframe.to_dict()
        highest_per_word_data = analysis.highest_per_word
        problem_summary = analysis.problem_summary

        user_input = {
            "role": "user",
            "content": (
                "<<ATTEMPTED_SENTENCE>>\n"
                f"{attempted_sentence}"
                "<</ATTEMPTED_SENTENCE>>"
                "<<PER_SUMMARY>>\n"
                f"{per_summary}"
                "<</PER_SUMMARY>>"
                "<<PROBLEM_SUMMARY>>\n"
                f"{problem_summary}\n"
                "<</PROBLEM_SUMMARY>>\n\n"
                "<<PRONUNCIATION>>\n"
                f"{pronunciation_data}\n"
                "<</PRONUNCIATION>>\n\n"
                "<<HIGHEST_PER_WORD>>\n"
                f"{highest_per_word_data}\n"
                "<</HIGHEST_PER_WORD>>\n\n"
                "<<INSTRUCTIONS>>\n"
                "1. THINKING:\n"
                "   a. Review phoneme_error_counts to find the most frequent mispronounced phoneme.\n"
                "   b. If any count > 1, target that phoneme; else use highest_per_word substitution.\n"
                f"   c. sentence_per = {per_summary}; if ≤0.2 use advanced words, else simpler words.\n"
                "   d. Plan 20-30 word fully decodable sentence with varied phoneme positions, check the system prompt for the exact amount of words needed.\n"
                "   e. Plan feedback: compliment, explain phoneme issue, compliment.\n"
                "2. ANSWER in JSON using the earlier reasoning and the system prompt:\n"
                "Make sure to explain all of your thinking by responding to each of these thinking questions before giving your response in json\n"
                "<</INSTRUCTIONS>>"
            ),
        }
        conversation_history = [
            {
                "role": "system",
                "content": phoneme_assistant.load_prompt(
                    "core/gpt_prompts/gpt_prompt_v2.txt"
                ),
            }
        ]

        previous_utterances = session.feedback_entries
        for entry in previous_utterances:
            conversation_history.append(
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "phoneme_analysis": entry.phoneme_analysis.get("phoneme_error_counts", {}),
                            "sentence": entry.sentence,
                        }
                    ),
                }
            )
            conversation_history.append(
                {
                    "role": "assistant",
                    "content": entry.feedback_text,
                }
            )
        print("Conversation history:", conversation_history)

        # Add the current user input to the conversation history
        conversation_history.append(user_input)

        # Get GPT response
        response = phoneme_assistant.query_gpt(
            conversation_history=conversation_history,
        )
        print("GPT Response:", response)
        # get the json from the response
        json_response = phoneme_assistant.extract_json(response)

        return json_response
