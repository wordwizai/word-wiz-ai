from typing_extensions import override

from core.modes.base_mode import BaseMode
from core.phonics_data import get_pattern
from core.phonics_scoring import line_index
from fastapi import HTTPException, status


class PhonicsPatternPractice(BaseMode):
    """One phonics pattern: its word list in short lines, then its sentences.

    The lines are fixed, so there is no GPT call. The line just read is found
    by matching the sentence, not by counting readings, because the child can
    read a line again before tapping Next.
    """

    def __init__(self, pattern: dict):
        self.pattern = pattern

    @override
    async def get_next_sentence(self, attempted_sentence, analysis, phoneme_assistant, session) -> dict:
        lines = self.pattern["lines"]
        index = line_index(self.pattern, attempted_sentence)
        if index is None:
            # Not one of this pattern's lines, which the app never sends.
            # Carry on by counting readings instead of failing the reading.
            index = min(len(session.feedback_entries), len(lines) - 1)
        if index >= len(lines) - 1:
            return {"session_complete": True, "line_index": index, "line_count": len(lines)}
        return {"sentence": lines[index + 1], "line_index": index + 1, "line_count": len(lines)}


def phonics_mode_for(session) -> PhonicsPatternPractice:
    """The mode for a pattern session, or a 404 if its pattern was removed."""
    pattern = get_pattern(session.pattern_slug) if session.pattern_slug else None
    if pattern is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This practice isn't available anymore.",
        )
    return PhonicsPatternPractice(pattern)
