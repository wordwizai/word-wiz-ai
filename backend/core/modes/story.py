import asyncio
import json
import os
from typing_extensions import override

from core.gpt_output_validator import validate_and_log
from core.modes.base_mode import BaseMode
from core.phoneme_assistant import PhonemeAssistant
from core.phoneme_feedback_formatter import build_phoneme_to_error_words
from models.session import Session as UserSession
from schemas.feedback_entry import AudioAnalysis


class StoryPractice(BaseMode):
    """
    Story Practice mode — students read a classic story sentence by sentence.
    The story progression is deterministic; GPT adapts sentences to target
    the reader's problem phonemes while staying true to the story.
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
                    sentences = [line for line in story_content_lines if line]
                    self.story_content = {
                        "name": story_name,
                        "plot_desc": plot_desc,
                        "sentences": sentences,
                        "total_sentences": len(sentences),
                    }
                    break

    def get_current_sentence_index(self, session):
        return len(session.feedback_entries)

    def get_current_sentence(self, session):
        if not self.story_content:
            return "The story could not be loaded."
        current_index = self.get_current_sentence_index(session)
        if current_index >= len(self.story_content["sentences"]):
            return "You have finished the story! Great job reading!"
        return self.story_content["sentences"][current_index]

    @override
    async def get_next_sentence(
        self,
        attempted_sentence: str,
        analysis: AudioAnalysis,
        phoneme_assistant: PhonemeAssistant,
        session: UserSession,
    ) -> dict:
        """
        Generate the next story sentence, targeting the user's problem phonemes.
        """
        per_summary = analysis.per_summary
        pronunciation_data = analysis.pronunciation_dataframe.to_dict("records")
        problem_summary = analysis.problem_summary

        past_sentences = [entry.sentence for entry in session.feedback_entries]
        next_sentence_description = self._get_next_sentence_description(session)
        story_context = {
            "story_name": self.story_content.get("name", ""),
            "plot_desc": self.story_content.get("plot_desc", ""),
        }

        phoneme_to_error_words = build_phoneme_to_error_words(pronunciation_data)

        gpt_problem_summary = {
            "recommended_focus_phoneme": problem_summary.get("recommended_focus_phoneme"),
            "phoneme_to_error_words": phoneme_to_error_words,
        }

        user_input = {
            "role": "user",
            "content": json.dumps(
                {
                    "story_context": story_context,
                    "past_sentences": past_sentences,
                    "attempted_sentence": attempted_sentence,
                    "problem_summary": gpt_problem_summary,
                    "per_summary": per_summary,
                    "next_sentence_description": next_sentence_description,
                }
            ),
        }
        conversation_history = [
            {
                "role": "system",
                "content": phoneme_assistant.load_prompt(
                    "core/gpt_prompts/story_mode_next_sentence_v1.txt",
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

        validated_response = validate_and_log(
            json_response,
            pronunciation_data,
            gpt_problem_summary,
            include_warnings_in_response=False,
        )
        return validated_response

    def _get_next_sentence_description(self, session) -> str:
        """Return the next canonical story sentence as a guide for GPT."""
        if not self.story_content:
            return "The story could not be loaded."
        current_index = len(session.feedback_entries)
        next_index = current_index + 1
        sentences = self.story_content.get("sentences", [])
        if next_index >= len(sentences):
            return "You have finished the story! Great job reading! **END**"
        return sentences[next_index]
