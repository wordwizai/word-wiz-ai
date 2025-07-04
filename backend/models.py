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
    audio_url = Column(String, nullable=False)
    phoneme_errors = Column(Text)  # Store as JSON string
    error_rates = Column(Text)  # Store as JSON string
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship back to user
    user = relationship("User", back_populates="recordings")


class UserSettings(Base):
    __tablename__ = "user_settings"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    preferred_language = Column(String, default="en")
    dark_mode = Column(Boolean, default=False)
    tts_speed = Column(Float, default=1.0)
    auto_feedback_enabled = Column(Boolean, default=True)

    user = relationship("User", back_populates="settings")
