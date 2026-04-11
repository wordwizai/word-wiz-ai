from core.phoneme_assistant import PhonemeAssistant
from models.session import Session
from schemas.feedback_entry import AudioAnalysis


class BaseMode:
    """
    Base class for all modes.
    """

    async def get_next_sentence(
        self,
        attempted_sentence: str,
        analysis: AudioAnalysis,
        phoneme_assistant: PhonemeAssistant,
        session: Session,
    ) -> dict:
        """
        Generate the next practice sentence (or story options) via GPT.

        Feedback text is now generated locally by phoneme_feedback_formatter —
        this method only handles sentence generation.

        Returns a dict with at minimum a "sentence" key.
        """
        raise NotImplementedError("Subclasses should implement this method.")
