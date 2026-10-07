from database import Base
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class Assignment(Base):
    """A phonics pattern a teacher gave to their class or to chosen students.

    One row per class and pattern. Progress is never stored here; it comes
    from the students' sessions (crud/phonics_progress.py).
    """

    __tablename__ = "assignments"
    id = Column(Integer, primary_key=True)
    class_id = Column(Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)
    pattern_slug = Column(String(64), nullable=False)
    # On: everyone in the class when it's read. Off: only assignment_students.
    whole_class = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    class_obj = relationship("Class", back_populates="assignments")
    students = relationship(
        "AssignmentStudent", back_populates="assignment", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("class_id", "pattern_slug", name="unique_class_pattern"),
    )


class AssignmentStudent(Base):
    __tablename__ = "assignment_students"
    id = Column(Integer, primary_key=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    assignment = relationship("Assignment", back_populates="students")

    __table_args__ = (
        UniqueConstraint("assignment_id", "student_id", name="unique_assignment_student"),
    )
