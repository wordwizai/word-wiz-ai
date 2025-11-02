from typing import Optional

from models import ThemeMode
from pydantic import BaseModel


class UserSettingsUpdate(BaseModel):
    preferred_language: Optional[str] = None
    theme: Optional[ThemeMode] = None
    tts_speed: Optional[float] = None
    audio_feedback_volume: Optional[float] = None
    notifications_enabled: Optional[bool] = None
    email_notifications: Optional[bool] = None
    use_client_phoneme_extraction: Optional[bool] = None


class UserSettingsResponse(BaseModel):
    preferred_language: str
    theme: ThemeMode
    tts_speed: float
    audio_feedback_volume: float
    notifications_enabled: bool
    email_notifications: bool
    use_client_phoneme_extraction: bool
