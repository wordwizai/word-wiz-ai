import asyncio
import json
from typing import override
import os

from core.gpt_output_validator import validate_and_log
from core.modes.base_mode import BaseMode
from core.phoneme_assistant import PhonemeAssistant
from models.session import Session as UserSession
from schemas.feedback_entry import AudioAnalysis


class StoryPractice(BaseMode):
    """
    The story practice mode allows students to read a classic story in a decodable format.
    The story progresses sentence by sentence, with vocabulary adapted to the reader's skill level.
    Focus is on pronunciation feedback without revealing story spoilers.
    """

    def __init__(self, story_name: str = ""):
        self.story_name = story_name
        self.story_content = {}
        self.load_story_content()

    def load_story_content(self):
        """Load story content from the story files directory."""
        story_dir = os.path.join(os.path.dirname(__file__), "..", "story_files")
        for filename in os.listdir(story_dir):
            if filename == f"{self.story_name}.txt":
                filepath = os.path.join(story_dir, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()

                # Parse story file
                lines = content.strip().split("\n")
                story_name = ""
                plot_desc = ""
                story_content_lines = []
                in_story_content = False

                for line in lines:
                    if line.startswith("NAME:"):
                        story_name = line.replace("NAME:", "").strip()
                    elif line.startswith("PLOT DESC:"):
                        plot_desc = line.replace("PLOT DESC:", "").strip()
                    elif line.startswith("STORY CONTENT:"):
                        in_story_content = True
                    elif in_story_content and line.strip():
                        story_content_lines.append(line.strip())

                if story_name and story_content_lines:
                    # Each line is a sentence
                    sentences = [line for line in story_content_lines if line]
                    self.story_content = {
                        "name": story_name,
                        "plot_desc": plot_desc,
                        "sentences": sentences,
                        "total_sentences": len(sentences),
                    }
                    break

    def get_current_sentence_index(self, session):
        """Get the current sentence index based on feedback entry count."""
        return len(session.feedback_entries)

    def get_current_sentence(self, session):
        """Get the current sentence the user should read."""
        if not self.story_content:
            return "The story could not be loaded."

        current_index = self.get_current_sentence_index(session)

        if current_index >= len(self.story_content["sentences"]):
            return "You have finished the story! Great job reading!"

        return self.story_content["sentences"][current_index]

    def get_next_sentence(self, session):
        """Get the next sentence in the story."""
        if not self.story_content:
            return "The story could not be loaded."

        current_index = self.get_current_sentence_index(session)
        next_index = current_index + 1

        if next_index >= len(self.story_content["sentences"]):
            return "You have finished the story! Great job reading! **END**"

        return self.story_content["sentences"][next_index]

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
        This method processes the audio analysis and provides feedback for the current story sentence.
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

        # Get story context and current progress
        current_index = self.get_current_sentence_index(session)
        next_sentence = self.get_next_sentence(session)
        story_context = {
            "story_name": self.story_content.get("name", ""),
            "plot_desc": self.story_content.get("plot_desc", ""),
        }

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
                    "story_context": story_context,
                    "past_sentences": past_sentences,
                    "attempted_sentence": attempted_sentence,
                    "pronunciation": enhanced_pronunciation,  # Use enhanced version with phoneme breakdowns
                    "highest_per_word": highest_per_word_data,
                    "problem_summary": full_problem_summary,  # Use full version, not simplified
                    "per_summary": per_summary,
                    "next_sentence_description": next_sentence,
                }
            ),
        }
        conversation_history = [
            {
                "role": "system",
                "content": phoneme_assistant.load_prompt(
                    "core/gpt_prompts/story_mode_prompt_v2.txt"
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

        # Extract the JSON response
        json_response = phoneme_assistant.extract_json(response)

        # Validate GPT output to catch hallucinations and ensure quality
        validated_response = validate_and_log(
            json_response,
            enhanced_pronunciation,
            full_problem_summary,
            include_warnings_in_response=False  # Set to True for debugging
        )

        return validated_response
