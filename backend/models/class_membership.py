from database import Base
from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class ClassMembership(Base):
    __tablename__ = "class_memberships"
    id = Column(Integer, primary_key=True)
    class_id = Column(Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    class_obj = relationship("Class", back_populates="memberships")
    student = relationship("User", back_populates="class_memberships")

    __table_args__ = (
        UniqueConstraint('class_id', 'student_id', name='unique_membership'),
    )
