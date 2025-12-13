from auth.auth_handler import get_current_active_user
from crud import class_crud, class_membership_crud
from database import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from models import User, Session as UserSession, FeedbackEntry
from schemas.class_schema import (
    ClassCreate,
    ClassResponse,
    ClassWithStudentCount,
    ClassWithTeacher,
)
from schemas.class_membership_schema import (
    JoinClassRequest,
    ClassMembershipResponse,
    StudentWithStats,
    StudentStatistics,
    ClassStudentsResponse,
    StudentInsightsResponse,
)
from sqlalchemy.orm import Session as DBSession
from typing import List

router = APIRouter()


@router.post("/", response_model=ClassResponse, status_code=status.HTTP_201_CREATED)
def create_class(
    class_create: ClassCreate,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new class (teacher creates a class for students to join)."""
    db_class = class_crud.create_class(
        db=db,
        name=class_create.name,
        teacher_id=current_user.id
    )
    return ClassResponse.model_validate(db_class)


@router.get("/my-classes", response_model=List[ClassWithStudentCount])
def get_my_classes(
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get all classes created by the current user (teacher's classes)."""
    classes = class_crud.get_teacher_classes(db, current_user.id)
    
    # Add student count to each class
    result = []
    for cls in classes:
        class_dict = ClassResponse.model_validate(cls).model_dump()
        class_dict["student_count"] = len(cls.memberships)
        result.append(ClassWithStudentCount(**class_dict))
    
    return result


@router.get("/my-student-classes", response_model=List[ClassWithTeacher])
def get_my_student_classes(
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get all classes the current user belongs to as a student."""
    classes = class_membership_crud.get_student_classes(db, current_user.id)
    return [ClassWithTeacher.model_validate(cls) for cls in classes]


@router.post("/join", response_model=ClassMembershipResponse, status_code=status.HTTP_201_CREATED)
def join_class(
    join_request: JoinClassRequest,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Join a class using a join code."""
    # Find class by join code
    db_class = class_crud.get_class_by_join_code(db, join_request.join_code)
    if not db_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found with that join code"
        )
    
    # Check if already a member
    if class_membership_crud.is_member(db, db_class.id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already a member of this class"
        )
    
    # Create membership
    membership = class_membership_crud.create_membership(
        db=db,
        class_id=db_class.id,
        student_id=current_user.id
    )
    
    return ClassMembershipResponse.model_validate(membership)


@router.get("/{class_id}/students", response_model=ClassStudentsResponse)
def get_class_students(
    class_id: int,
    use_recent_window: bool = True,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get all students in a class with their statistics (teacher only)."""
    from datetime import datetime, timedelta
    
    # Verify class exists
    db_class = class_crud.get_class_by_id(db, class_id)
    if not db_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    # Verify current user is the teacher of this class
    if db_class.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the teacher of this class can view students"
        )
    
    # Get all memberships with student info
    memberships = class_membership_crud.get_class_memberships(db, class_id)
    
    # Calculate statistics for each student
    students_with_stats = []
    for membership in memberships:
        student = membership.student
        
        # Get sessions (all or recent based on parameter)
        if use_recent_window:
            # Use recent window (last 14 days or 15 sessions)
            cutoff_date = datetime.now() - timedelta(days=14)
            sessions = db.query(UserSession).filter(
                UserSession.user_id == student.id,
                UserSession.created_at >= cutoff_date
            ).order_by(UserSession.created_at.desc()).limit(15).all()
        else:
            # Get all sessions (backward compatibility)
            sessions = db.query(UserSession).filter(
                UserSession.user_id == student.id
            ).all()
        
        # Get feedback entries for these sessions
        session_ids = [s.id for s in sessions]
        feedback_entries = db.query(FeedbackEntry).filter(
            FeedbackEntry.session_id.in_(session_ids)
        ).all() if session_ids else []
        
        # Calculate statistics
        total_sessions = len(sessions)
        
        # Count words read and extract PER values
        words_read = 0
        per_values = []
        for entry in feedback_entries:
            if entry.sentence:
                words_read += len(entry.sentence.split())
            if entry.phoneme_analysis and isinstance(entry.phoneme_analysis, dict):
                per_summary = entry.phoneme_analysis.get('per_summary', {})
                if isinstance(per_summary, dict):
                    sentence_per = per_summary.get('sentence_per', 0)
                    if sentence_per is not None:
                        try:
                            per_values.append(float(sentence_per))
                        except (ValueError, TypeError):
                            pass
        
        average_per = sum(per_values) / len(per_values) if per_values else 0.0
        
        # Get all sessions for streak calculation (not just recent window)
        all_sessions = db.query(UserSession).filter(
            UserSession.user_id == student.id
        ).all()
        
        last_session_date = max([s.created_at for s in all_sessions]) if all_sessions else None
        
        # Calculate current streak
        current_streak = class_membership_crud.calculate_student_streak(all_sessions)
        
        # Create student with stats
        student_stats = StudentWithStats(
            id=student.id,
            full_name=student.full_name,
            email=student.email,
            joined_at=membership.joined_at,
            statistics=StudentStatistics(
                total_sessions=total_sessions,
                words_read=words_read,
                average_per=round(average_per, 3),
                last_session_date=last_session_date,
                current_streak=current_streak
            )
        )
        students_with_stats.append(student_stats)
    
    return ClassStudentsResponse(
        class_id=db_class.id,
        class_name=db_class.name,
        join_code=db_class.join_code,
        students=students_with_stats
    )


@router.delete("/{class_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
def leave_class(
    class_id: int,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Leave a class (student removes themselves from a class)."""
    # Verify class exists
    db_class = class_crud.get_class_by_id(db, class_id)
    if not db_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    # Don't allow teachers to leave their own classes
    if db_class.teacher_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teachers cannot leave their own classes. Use delete instead."
        )
    
    # Check if member
    if not class_membership_crud.is_member(db, class_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not a member of this class"
        )
    
    # Delete membership
    class_membership_crud.delete_membership(db, class_id, current_user.id)
    
    return None


@router.delete("/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_class(
    class_id: int,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a class (teacher only, also deletes all memberships)."""
    # Verify class exists
    db_class = class_crud.get_class_by_id(db, class_id)
    if not db_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    # Verify current user is the teacher
    if db_class.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the teacher can delete this class"
        )
    
    # Delete class (cascades to memberships)
    class_crud.delete_class(db, class_id)
    
    return None


@router.get("/{class_id}/students/{student_id}/insights", response_model=StudentInsightsResponse)
def get_student_insights_endpoint(
    class_id: int,
    student_id: int,
    days: int = 14,
    max_sessions: int = 15,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get detailed insights for a specific student in a class (teacher only).
    
    Returns session history, recent accuracy metrics, phoneme-level insights,
    and actionable recommendations for teachers.
    
    Args:
        class_id: ID of the class
        student_id: ID of the student
        days: Number of recent days to analyze (default 14)
        max_sessions: Maximum sessions to analyze (default 15)
    """
    from crud.feedback_entry import get_student_insights
    
    # Verify class exists
    db_class = class_crud.get_class_by_id(db, class_id)
    if not db_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    # Verify current user is the teacher
    if db_class.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the class teacher can view student insights"
        )
    
    # Verify student is in the class
    if not class_membership_crud.is_member(db, class_id, student_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student is not a member of this class"
        )
    
    # Get insights
    insights = get_student_insights(db, student_id, days, max_sessions)
    
    return StudentInsightsResponse(**insights)
