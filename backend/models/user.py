import enum

from database import Base
from sqlalchemy import Boolean, Column, Integer, String, false
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(225), index=True)
    username = Column(String(225), unique=True, index=True)
    email = Column(String(225), unique=True, index=True)
    hashed_password = Column(String(225))
    is_active = Column(Boolean, default=True)
    # Try-mode visitors get a row too, one per browser, with no email or
    # password (crud/guest_users.py). Signing up from that browser turns the
    # row into the new account, so a visitor who signs up counts once.
    is_guest = Column(Boolean, nullable=False, default=False, server_default=false())

    settings = relationship("UserSettings", back_populates="user", uselist=False)
    sessions = relationship("Session", back_populates="user")
    classes = relationship("Class", back_populates="teacher")
    class_memberships = relationship("ClassMembership", back_populates="student")
