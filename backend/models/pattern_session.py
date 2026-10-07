from database import Base
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship


class PatternSession(Base):
    """The phonics pattern a session practises, and its score once finished.

    It sits beside `sessions` instead of adding columns to it. main.py's
    create_all makes missing tables at startup but never adds columns, so a
    new table can't break session queries if the Alembic step is missed.
    """

    __tablename__ = "pattern_sessions"
    session_id = Column(
        Integer, ForeignKey("sessions.id", ondelete="CASCADE"), primary_key=True
    )
    pattern_slug = Column(String(64), nullable=False, index=True)
    words_correct = Column(Integer, nullable=True)
    words_total = Column(Integer, nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    session = relationship("Session", back_populates="pattern")
