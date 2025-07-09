from database import Base
from sqlalchemy import Column, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class Session(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_completed = Column(Integer, default=0)  # 0: not completed, 1: completed

    user = relationship("User", back_populates="sessions")
    activity = relationship("Activity", back_populates="sessions")
    feedback_entries = relationship("FeedbackEntry", back_populates="session")
