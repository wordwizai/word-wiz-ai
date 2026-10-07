from core.phonics_data import get_pattern
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
    # Only phonics pattern sessions have one (models/pattern_session.py).
    # Lazy, so ordinary session loads don't pay for it; list routes selectinload it.
    pattern = relationship(
        "PatternSession",
        back_populates="session",
        uselist=False,
        cascade="all, delete-orphan",
    )

    @property
    def pattern_slug(self) -> str | None:
        return self.pattern.pattern_slug if self.pattern else None

    @property
    def pattern_name(self) -> str | None:
        found = get_pattern(self.pattern_slug) if self.pattern_slug else None
        return found["display_name"] if found else None
