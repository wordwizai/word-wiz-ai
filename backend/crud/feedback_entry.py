from models import FeedbackEntry  # Adjust import if needed
from schemas.feedback_entry import FeedbackEntryCreate, FeedbackEntryOut
from sqlalchemy.orm import Session
from models.session import Session as SessionModel
from datetime import date, timedelta
from sqlalchemy import func, distinct


def create_feedback_entry(db: Session, feedback: FeedbackEntryCreate) -> FeedbackEntry:
    db_feedback = FeedbackEntry(
        session_id=feedback.session_id,
        sentence=feedback.sentence,
        phoneme_analysis=feedback.phoneme_analysis,
        gpt_response=feedback.gpt_response,
    )
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    return db_feedback


def get_feedback_entry(db: Session, feedback_id: int) -> FeedbackEntry:
    return db.query(FeedbackEntry).filter(FeedbackEntry.id == feedback_id).first()


def get_feedback_entries_by_session(
    db: Session, session_id: int, skip: int = 0, limit: int = 100
):
    return (
        db.query(FeedbackEntry)
        .filter(FeedbackEntry.session_id == session_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def delete_feedback_entry(db: Session, feedback_id: int):
    db_feedback = (
        db.query(FeedbackEntry).filter(FeedbackEntry.id == feedback_id).first()
    )
    if db_feedback:
        db.delete(db_feedback)
        db.commit()
    return db_feedback


def get_feedback_entries_by_user(
    db: Session, user_id: int, skip: int = 0, limit: int = 100
):
    return (
        db.query(FeedbackEntry)
        .join(SessionModel, FeedbackEntry.session_id == SessionModel.id)
        .filter(SessionModel.user_id == user_id)
        .order_by(SessionModel.created_at.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_user_statistics(db: Session, user_id: int) -> dict:
    """
    Calculate comprehensive user statistics for dashboard.
    
    All sessions are counted (completed or in-progress) to track overall practice activity.
    
    Args:
        db: Database session
        user_id: ID of the user
        
    Returns:
        Dictionary with total_sessions, current_streak, longest_streak, words_read
    """
    # 1. Get total sessions (all sessions, not just completed)
    total_sessions = (
        db.query(SessionModel)
        .filter(SessionModel.user_id == user_id)
        .count()
    )
    
    # 2. Get all session dates for streak calculation
    all_sessions = (
        db.query(SessionModel.created_at)
        .filter(SessionModel.user_id == user_id)
        .order_by(SessionModel.created_at.desc())
        .all()
    )
    
    # Extract unique dates (convert datetime to date)
    session_dates = sorted(
        set(session.created_at.date() for session in all_sessions),
        reverse=True
    )
    
    # Calculate streaks
    current_streak, longest_streak = calculate_streaks(session_dates)
    
    # 3. Calculate total words read from feedback entries
    feedback_entries = get_feedback_entries_by_user(
        db, user_id=user_id, skip=0, limit=10000  # High limit to get all
    )
    
    words_read = 0
    for entry in feedback_entries:
        if entry.sentence:
            # Simple word count: split by whitespace
            words_read += len(entry.sentence.split())
    
    return {
        "total_sessions": total_sessions,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "words_read": words_read,
    }


def calculate_streaks(session_dates: list[date]) -> tuple[int, int]:
    """
    Calculate current and longest streaks from a list of session dates.
    
    Algorithm (80/20 approach):
    - Current streak: Count backwards from today while dates are consecutive
    - Longest streak: Find maximum consecutive sequence in history
    
    Args:
        session_dates: List of dates (must be sorted descending)
        
    Returns:
        Tuple of (current_streak, longest_streak)
    """
    if not session_dates:
        return 0, 0
    
    today = date.today()
    
    # Calculate current streak
    current_streak = 0
    expected_date = today
    
    for session_date in session_dates:
        if session_date == expected_date:
            current_streak += 1
            expected_date -= timedelta(days=1)
        elif session_date < expected_date:
            # Gap found, stop counting current streak
            break
    
    # Calculate longest streak (iterate through all dates)
    longest_streak = 0
    temp_streak = 1
    
    # Sort ascending for easier consecutive checking
    sorted_dates = sorted(set(session_dates))
    
    for i in range(len(sorted_dates) - 1):
        days_diff = (sorted_dates[i + 1] - sorted_dates[i]).days
        
        if days_diff == 1:
            # Consecutive day
            temp_streak += 1
            longest_streak = max(longest_streak, temp_streak)
        else:
            # Gap found, reset temporary streak
            temp_streak = 1
    
    # Don't forget to check the final streak
    longest_streak = max(longest_streak, temp_streak, current_streak)
    
    return current_streak, longest_streak
