from database import Base
from sqlalchemy import JSON, Column, Integer, String
from sqlalchemy.orm import relationship


class Activity(Base):
    __tablename__ = "activities"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    activity_type = Column(String, nullable=False)  # e.g., 'story_mode', 'drill', etc.
    target_phoneme = Column(String, nullable=True)  # e.g., "/ʃ/"
    config = Column(JSON, default={})  # extra config per activity

    sessions = relationship("Session", back_populates="activity")
