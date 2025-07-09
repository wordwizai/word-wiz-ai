from core.phoneme_assistant import PhonemeAssistant
from models.session import Session
from schemas.feedback_entry import AudioAnalysis


class BaseMode:
    """
    Base class for all modes.
    """

    def get_feedback_and_next_sentence(
        self,
        attempted_sentence: str,
        analysis: AudioAnalysis,
        phoneme_assistant: PhonemeAssistant,
        session: Session,
    ):
        """
        Get the feedback based on the pronunciation.
        """
        raise NotImplementedError("Subclasses should implement this method.")
