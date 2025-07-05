from pydantic import BaseModel
from transformers import TFOpenAIGPTDoubleHeadsModel
from typing import Optional
from models import ThemeMode


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: str


class UserResponse(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None


class UserInDB(UserResponse):
    hashed_password: str


class AudioAnalysisRequest(BaseModel):
    attempted_sentence: str
    audio_file: bytes  # Assuming the audio file is sent as bytes


class UserSettingsUpdate(BaseModel):
    preferred_language: Optional[str] = None
    theme: Optional[ThemeMode] = None
    tts_speed: Optional[float] = None
    audio_feedback_volume: Optional[float] = None
    notifications_enabled: Optional[bool] = None
    email_notifications: Optional[bool] = None

class UserSettingsResponse(BaseModel):
    preferred_language: str
    theme: ThemeMode
    tts_speed: float
    audio_feedback_volume: float
    notifications_enabled: bool
    email_notifications: bool
