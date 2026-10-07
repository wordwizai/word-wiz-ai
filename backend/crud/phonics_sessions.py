"""Starting, resuming and finishing phonics pattern sessions."""

from datetime import datetime, timezone

from core.phonics_data import PHONICS_ACTIVITY_TYPE, get_pattern
from core.phonics_scoring import is_mastered, score_readings
from models import Activity, FeedbackEntry, PatternSession, Session
from sqlalchemy.orm import Session as DBSession


def get_phonics_activity(db: DBSession) -> Activity:
    """The one activity every pattern session belongs to, made on first use.

    Making it here means no database needs seeding before the feature works.
    """
    activity = (
        db.query(Activity)
        .filter(Activity.activity_type == PHONICS_ACTIVITY_TYPE)
        .order_by(Activity.id)
        .first()
    )
    if activity is None:
        activity = Activity(
            title="Phonics path",
            description="Practice one phonics pattern at a time, from short a word families to vowel teams.",
            emoji_icon="Blocks",
            activity_type=PHONICS_ACTIVITY_TYPE,
            activity_settings={},
        )
        db.add(activity)
        db.commit()
        db.refresh(activity)
    return activity


def start_pattern_session(db: DBSession, user_id: int, slug: str) -> Session:
    """Resume the user's newest unfinished session for the pattern, or start one.

    The caller checks that the pattern exists.
    """
    existing = (
        db.query(Session)
        .join(PatternSession, PatternSession.session_id == Session.id)
        .filter(
            Session.user_id == user_id,
            Session.is_completed == 0,
            PatternSession.pattern_slug == slug,
        )
        .order_by(Session.created_at.desc(), Session.id.desc())
        .first()
    )
    if existing is not None:
        return existing

    session = Session(user_id=user_id, activity_id=get_phonics_activity(db).id)
    session.pattern = PatternSession(pattern_slug=slug)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def finish_pattern_session(db: DBSession, session: Session) -> dict:
    """Score the session, mark it complete and return the result.

    Safe to call again (if the last line is read twice): a finished session
    keeps its first score.
    """
    row = session.pattern
    if row.completed_at is None:
        pattern = get_pattern(row.pattern_slug)
        # Insertion order is reading order; created_at only has whole seconds on SQLite.
        entries = (
            db.query(FeedbackEntry)
            .filter(FeedbackEntry.session_id == session.id)
            .order_by(FeedbackEntry.id.asc())
            .all()
        )
        correct, total = score_readings(
            pattern, [(entry.sentence or "", entry.phoneme_analysis) for entry in entries]
        )
        row.words_correct = correct
        row.words_total = total
        row.completed_at = datetime.now(timezone.utc)
        session.is_completed = 1
        db.commit()
    return {
        "words_correct": row.words_correct,
        "words_total": row.words_total,
        "mastered": is_mastered(row.words_correct, row.words_total),
        "pattern_name": session.pattern_name,
    }
