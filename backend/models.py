from pydantic_core.core_schema import no_info_after_validator_function
from database import Base, engine
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Float,
    ForeignKey,
    DateTime,
    Text,
)
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from sqlalchemy import Enum


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    # Relationship to recordings
    recordings = relationship("Recording", back_populates="user")
    # Relationship to user settings
    settings = relationship("UserSettings", back_populates="user", uselist=False)


class Recording(Base):
    __tablename__ = "recordings"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    sentence = Column(Text)
    phoneme_errors = Column(Text)  # Store as JSON string
    error_rates = Column(Text)  # Store as JSON string
    problem_summary = Column(Text)  # Store as JSON string
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship back to user
    user = relationship("User", back_populates="recordings")


class ThemeMode(enum.Enum):
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


class UserSettings(Base):
    __tablename__ = "user_settings"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    preferred_language = Column(String, default="en")
    theme = Column(Enum(ThemeMode), default=ThemeMode.SYSTEM, nullable=False)
    tts_speed = Column(Float, default=1.0)
    audio_feedback_volume = Column(Float, default=True)
    notifications_enabled = Column(Boolean, default=True)
    email_notifications = Column(Boolean, default=True)

    user = relationship("User", back_populates="settings")
