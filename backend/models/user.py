import enum

from database import Base
from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

    settings = relationship("UserSettings", back_populates="user", uselist=False)
    sessions = relationship("Session", back_populates="user")
