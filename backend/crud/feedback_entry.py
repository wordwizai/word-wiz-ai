from models import FeedbackEntry  # Adjust import if needed
from schemas.feedback_entry import FeedbackEntryCreate, FeedbackEntryOut
from sqlalchemy.orm import Session
from models.session import Session as SessionModel


def create_feedback_entry(db: Session, feedback: FeedbackEntryCreate) -> FeedbackEntry:
    db_feedback = FeedbackEntry(
        session_id=feedback.session_id,
        sentence=feedback.sentence,
        phoneme_analysis=feedback.phoneme_analysis,
        feedback_text=feedback.feedback_text,
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
