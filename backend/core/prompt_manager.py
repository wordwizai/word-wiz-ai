"""
Prompt management for GPT interactions.

Handles loading, caching, and assembling prompt templates from files.
"""

import os
from functools import lru_cache


class PromptManager:
    """Manages prompt loading and assembly."""

    def __init__(self):
        self.backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    @lru_cache(maxsize=32)
    def load_prompt(self, prompt_path: str) -> str:
        """
        Load a prompt from file with comment filtering and SSML appending.

        Results are cached for performance. Lines starting with "//" are treated
        as comments and filtered out. SSML instruction is automatically appended.

        Args:
            prompt_path: Path to prompt file (absolute or relative to backend root).

        Returns:
            str: Loaded and processed prompt text.
        """
        resolved_prompt_path = (
            prompt_path if os.path.isabs(prompt_path)
            else os.path.join(self.backend_root, prompt_path)
        )

        with open(resolved_prompt_path, encoding="utf-8") as file:
            lines = file.readlines()
            content = [
                line for line in lines if not line.strip().startswith("//")
            ]
            text = "".join(content)

        # Automatically append SSML instruction to all prompts
        ssml_instruction_rel = "core/gpt_prompts/ssml_instruction.txt"
        ssml_instruction_path = os.path.join(self.backend_root, ssml_instruction_rel)
        try:
            with open(ssml_instruction_path, encoding="utf-8") as ssml_file:
                ssml_lines = ssml_file.readlines()
                ssml_content = [
                    line for line in ssml_lines if not line.strip().startswith("//")
                ]
                ssml_text = "".join(ssml_content)
                text += "\n\n" + ssml_text
        except FileNotFoundError:
            # If SSML instruction file is missing, continue without it
            pass

        return text
