from database import Base
from sqlalchemy import Boolean, Column, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .theme_mode import ThemeMode


class UserSettings(Base):
    __tablename__ = "user_settings"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    preferred_language = Column(String(225), default="en")
    theme = Column(Enum(ThemeMode), default=ThemeMode.LIGHT, nullable=False)
    tts_speed = Column(Float, default=1.0)
    audio_feedback_volume = Column(Float, default=True)
    notifications_enabled = Column(Boolean, default=True)
    email_notifications = Column(Boolean, default=True)
    use_client_phoneme_extraction = Column(Boolean, default=False)
    use_websocket = Column(Boolean, default=True)  

    user = relationship("User", back_populates="settings")
