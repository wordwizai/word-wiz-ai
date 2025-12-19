import asyncio
import json
from typing import List
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
    
    Uses new modular prompt system with adaptive difficulty and grapheme-phoneme teaching.
    """

    @override
    def _get_prompt_sections(self) -> List[str]:
        """
        Get prompt sections for unlimited practice mode.
        """
        return [
            'base/system_role',
            'base/validation_rules',
            'feedback/praise_criteria',
            'feedback/phoneme_focus',
            'feedback/grapheme_instruction',
            'feedback/error_description',
            'sentence_generation/adaptive_difficulty',
            'sentence_generation/phoneme_density',
            'sentence_generation/grapheme_patterns',
            'sentence_generation/length_guidelines',
            'modes/unlimited_context',
            'base/output_format',
        ]
