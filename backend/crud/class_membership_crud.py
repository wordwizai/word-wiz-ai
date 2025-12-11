from sqlalchemy.orm import Session as orm_session, selectinload
from models.class_membership import ClassMembership
from models.class_model import Class
from models.user import User
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta


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


def calculate_student_streak(sessions: List) -> int:
    """Calculate the current streak of consecutive days with sessions.
    
    Args:
        sessions: List of session objects with created_at timestamps
        
    Returns:
        Number of consecutive days with activity
    """
    if not sessions:
        return 0
    
    # Sort sessions by date (most recent first)
    sorted_sessions = sorted(sessions, key=lambda s: s.created_at, reverse=True)
    
    # Get unique dates
    session_dates = []
    for session in sorted_sessions:
        date = session.created_at.date()
        if date not in session_dates:
            session_dates.append(date)
    
    if not session_dates:
        return 0
    
    # Check if the most recent session is today or yesterday
    today = datetime.now().date()
    if session_dates[0] not in [today, today - timedelta(days=1)]:
        return 0
    
    # Count consecutive days
    streak = 1
    for i in range(1, len(session_dates)):
        expected_date = session_dates[i-1] - timedelta(days=1)
        if session_dates[i] == expected_date:
            streak += 1
        else:
            break
    
    return streak
