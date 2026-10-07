from sqlalchemy.orm import Session as orm_session, selectinload
from models.class_membership import ClassMembership
from models.class_model import Class
from models.user import User
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone


def create_membership(db: orm_session, class_id: int, student_id: int) -> ClassMembership:
    """Create a new class membership.
    
    Args:
        db: Database session
        class_id: ID of the class
        student_id: ID of the student
        
    Returns:
        The created ClassMembership object
    """
    db_membership = ClassMembership(
        class_id=class_id,
        student_id=student_id
    )
    db.add(db_membership)
    db.commit()
    db.refresh(db_membership)
    return db_membership


def get_student_classes(db: orm_session, student_id: int) -> List[Class]:
    """Get all classes a student belongs to.
    
    Args:
        db: Database session
        student_id: ID of the student
        
    Returns:
        List of Class objects with membership info
    """
    memberships = (
        db.query(ClassMembership)
        .options(selectinload(ClassMembership.class_obj).selectinload(Class.teacher))
        .filter(ClassMembership.student_id == student_id)
        .order_by(ClassMembership.joined_at.desc())
        .all()
    )
    return [membership.class_obj for membership in memberships]


def get_class_students(db: orm_session, class_id: int) -> List[User]:
    """Get all students in a class.
    
    Args:
        db: Database session
        class_id: ID of the class
        
    Returns:
        List of User objects
    """
    memberships = (
        db.query(ClassMembership)
        .options(selectinload(ClassMembership.student))
        .filter(ClassMembership.class_id == class_id)
        .order_by(ClassMembership.joined_at.asc())
        .all()
    )
    return [membership.student for membership in memberships]


def get_class_memberships(db: orm_session, class_id: int) -> List[ClassMembership]:
    """Get all memberships for a class.
    
    Args:
        db: Database session
        class_id: ID of the class
        
    Returns:
        List of ClassMembership objects with student info
    """
    return (
        db.query(ClassMembership)
        .options(selectinload(ClassMembership.student))
        .filter(ClassMembership.class_id == class_id)
        .order_by(ClassMembership.joined_at.asc())
        .all()
    )


def delete_membership(db: orm_session, class_id: int, student_id: int) -> bool:
    """Delete a class membership (student leaves class).
    
    Args:
        db: Database session
        class_id: ID of the class
        student_id: ID of the student
        
    Returns:
        True if deleted, False if not found
    """
    membership = (
        db.query(ClassMembership)
        .filter(
            ClassMembership.class_id == class_id,
            ClassMembership.student_id == student_id
        )
        .first()
    )
    if membership:
        db.delete(membership)
        db.commit()
        return True
    return False


def is_member(db: orm_session, class_id: int, student_id: int) -> bool:
    """Check if a student is a member of a class.
    
    Args:
        db: Database session
        class_id: ID of the class
        student_id: ID of the student
        
    Returns:
        True if member, False otherwise
    """
    membership = (
        db.query(ClassMembership)
        .filter(
            ClassMembership.class_id == class_id,
            ClassMembership.student_id == student_id
        )
        .first()
    )
    return membership is not None


def calculate_student_streak(
    sessions: List, tz_name: str | None = None, now: datetime | None = None
) -> int:
    """Current streak of consecutive days with sessions, for the teacher view.

    Uses the same days and rules as the student's own dashboard
    (crud.feedback_entry.calculate_streaks), so the two never disagree.

    Args:
        sessions: Session objects with created_at timestamps
        tz_name: IANA timezone to count days in. UTC when missing or unknown.
        now: The current time, for tests. Defaults to now.

    Returns:
        Number of consecutive days with activity
    """
    from crud.feedback_entry import calculate_streaks, local_date, resolve_timezone

    if not sessions:
        return 0
    tz = resolve_timezone(tz_name)
    today = (now or datetime.now(timezone.utc)).astimezone(tz).date()
    current_streak, _ = calculate_streaks(
        {local_date(s.created_at, tz) for s in sessions}, today=today
    )
    return current_streak
