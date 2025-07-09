from database import Base
from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class FeedbackEntry(Base):
    __tablename__ = "feedback_entries"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    sentence = Column(Text)  # Sentence given to user
    phoneme_analysis = Column(JSON)  # Phoneme evaluation
    feedback_text = Column(Text)  # What GPT said
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("Session", back_populates="feedback_entries")
