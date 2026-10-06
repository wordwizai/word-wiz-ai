from typing import Optional

from models import ThemeMode
from pydantic import BaseModel, Field


class UserSettingsUpdate(BaseModel):
    preferred_language: Optional[str] = Field(default=None, max_length=32)
    theme: Optional[ThemeMode] = None
    # Google TTS accepts speaking rates 0.25-4.0; volume is a 0-1 gain.
    tts_speed: Optional[float] = Field(default=None, ge=0.25, le=4.0)
    audio_feedback_volume: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    notifications_enabled: Optional[bool] = None
    email_notifications: Optional[bool] = None
    use_client_phoneme_extraction: Optional[bool] = None
    use_websocket: Optional[bool] = None


class UserSettingsResponse(BaseModel):
    preferred_language: str
    theme: ThemeMode
    tts_speed: float
    audio_feedback_volume: float
    notifications_enabled: bool
    email_notifications: bool
    use_client_phoneme_extraction: bool
    use_websocket: bool
