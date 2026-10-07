from models import FeedbackEntry  # Adjust import if needed
from schemas.feedback_entry import FeedbackEntryCreate
from sqlalchemy.orm import Session
from models.session import Session as SessionModel
from datetime import date, datetime, timedelta, timezone, tzinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


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
    """
    The user's `limit` most recent entries (after skipping the newest `skip`),
    returned oldest-first so charts read left to right. Ordering ascending
    before the limit used to return the *first* entries ever recorded, which
    froze the Progress charts once a child passed `limit` readings.
    """
    newest_first = (
        db.query(FeedbackEntry)
        .join(SessionModel, FeedbackEntry.session_id == SessionModel.id)
        .filter(SessionModel.user_id == user_id)
        .order_by(FeedbackEntry.created_at.desc(), FeedbackEntry.id.desc())
        .offset(max(skip, 0))
        .limit(max(limit, 0))
        .all()
    )
    return list(reversed(newest_first))


def resolve_timezone(name: str | None) -> tzinfo:
    """The family's IANA timezone (e.g. "America/Los_Angeles"), or UTC if it
    is missing or not a zone we know."""
    if not name:
        return timezone.utc
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError):
        return timezone.utc


def local_date(created_at: datetime, tz: tzinfo) -> date:
    """The calendar day a stored timestamp fell on for the family.

    created_at is UTC but the database hands it back without a zone. Taking
    .date() of it directly counted UTC days, so a family in California
    reading at 4pm one day and 6pm the next looked like they had skipped a
    day in between.
    """
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    return created_at.astimezone(tz).date()


def get_user_statistics(db: Session, user_id: int, tz_name: str | None = None) -> dict:
    """
    Calculate comprehensive user statistics for dashboard.
    
    All sessions are counted (completed or in-progress) to track overall practice activity.
    
    Args:
        db: Database session
        user_id: ID of the user
        tz_name: The family's IANA timezone, so streak days are their days.
            UTC when missing or unknown.

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
    
    tz = resolve_timezone(tz_name)
    session_dates = {local_date(session.created_at, tz) for session in all_sessions}
    current_streak, longest_streak = calculate_streaks(
        session_dates, today=datetime.now(tz).date()
    )
    
    # 3. Calculate total words read — only fetch sentence column to avoid loading
    # the large phoneme_analysis JSON for every entry
    sentences = (
        db.query(FeedbackEntry.sentence)
        .join(SessionModel, FeedbackEntry.session_id == SessionModel.id)
        .filter(SessionModel.user_id == user_id)
        .all()
    )
    words_read = sum(len(row.sentence.split()) for row in sentences if row.sentence)
    
    return {
        "total_sessions": total_sessions,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "words_read": words_read,
    }


def calculate_streaks(
    session_dates, today: date | None = None
) -> tuple[int, int]:
    """
    Current and longest runs of consecutive days with reading.

    The current streak counts back from today, or from yesterday when the
    child hasn't read yet today: the day isn't over, so yesterday's streak is
    still alive. Counting only from today showed every streak as 0 each
    morning until the child read again.

    Args:
        session_dates: Days with at least one session, in any order, repeats
            allowed. Compute them with local_date() so they are the family's
            days.
        today: The family's today. Defaults to the server's.

    Returns:
        Tuple of (current_streak, longest_streak)
    """
    dates = set(session_dates)
    if not dates:
        return 0, 0
    if today is None:
        today = date.today()

    current_streak = 0
    day = today if today in dates else today - timedelta(days=1)
    while day in dates:
        current_streak += 1
        day -= timedelta(days=1)

    longest_streak = 0
    run = 0
    previous = None
    for day in sorted(dates):
        run = run + 1 if previous is not None and (day - previous).days == 1 else 1
        longest_streak = max(longest_streak, run)
        previous = day

    return current_streak, max(longest_streak, current_streak)


def get_student_insights(
    db: Session, 
    student_id: int, 
    days: int = 14, 
    max_sessions: int = 15
) -> dict:
    """
    Calculate comprehensive insights for a student based on recent activity.
    
    Uses either last N sessions or last N days, whichever provides more data.
    
    Args:
        db: Database session
        student_id: ID of the student
        days: Number of recent days to consider (default 14)
        max_sessions: Maximum number of recent sessions to consider (default 15)
        
    Returns:
        Dictionary with session history, accuracy metrics, phoneme insights, recommendations
    """
    from datetime import datetime, timedelta
    from collections import Counter, defaultdict
    
    # Get recent sessions
    cutoff_date = datetime.now() - timedelta(days=days)
    recent_sessions_query = (
        db.query(SessionModel)
        .filter(SessionModel.user_id == student_id)
        .filter(SessionModel.created_at >= cutoff_date)
        .order_by(SessionModel.created_at.desc())
        .limit(max_sessions)
        .all()
    )
    
    if not recent_sessions_query:
        # No recent activity
        return {
            "student_id": student_id,
            "recent_sessions": [],
            "recent_accuracy": 0.0,
            "recent_per": 0.0,
            "total_sentences_practiced": 0,
            "phoneme_insights": [],
            "recommendations": ["This student has no recent practice activity. Encourage them to practice regularly!"],
            "calculation_window": f"Last {days} days"
        }
    
    # Build session activity list
    session_activities = []
    all_per_values = []
    total_sentences = 0
    phoneme_error_aggregator = Counter()
    phoneme_error_types = defaultdict(lambda: {"substitution": 0, "deletion": 0, "insertion": 0})
    
    # Fetch all feedback entries for all sessions in a single query
    session_ids = [s.id for s in recent_sessions_query]
    all_feedback_entries = (
        db.query(FeedbackEntry)
        .filter(FeedbackEntry.session_id.in_(session_ids))
        .all()
    )
    feedback_by_session: dict[int, list] = {s.id: [] for s in recent_sessions_query}
    for entry in all_feedback_entries:
        feedback_by_session[entry.session_id].append(entry)

    for session in recent_sessions_query:
        feedback_entries = feedback_by_session.get(session.id, [])

        if not feedback_entries:
            continue
        
        # Calculate session-level metrics
        session_per_values = []
        sentence_count = len(feedback_entries)
        total_sentences += sentence_count
        
        for entry in feedback_entries:
            # Extract PER from phoneme_analysis
            if entry.phoneme_analysis and isinstance(entry.phoneme_analysis, dict):
                per_summary = entry.phoneme_analysis.get("per_summary", {})
                sentence_per = per_summary.get("sentence_per", 0)
                
                if sentence_per is not None:
                    try:
                        session_per_values.append(float(sentence_per))
                        all_per_values.append(float(sentence_per))
                    except (ValueError, TypeError):
                        pass
                
                # Aggregate phoneme errors
                problem_summary = entry.phoneme_analysis.get("problem_summary", {})
                phoneme_errors = problem_summary.get("phoneme_error_counts", {})
                phoneme_error_aggregator.update(phoneme_errors)
        
        # Calculate session average PER
        session_avg_per = sum(session_per_values) / len(session_per_values) if session_per_values else 0.0
        session_accuracy = (1 - session_avg_per) * 100
        
        session_activities.append({
            "session_id": session.id,
            "date": session.created_at,
            "sentence_count": sentence_count,
            "accuracy": round(session_accuracy, 1),
            "per": round(session_avg_per, 3)
        })
    
    # Calculate overall recent accuracy
    recent_per = sum(all_per_values) / len(all_per_values) if all_per_values else 0.0
    recent_accuracy = (1 - recent_per) * 100
    
    # Generate phoneme insights (top 5 problematic phonemes)
    phoneme_insights = []
    
    # Import SpeechProblemClassifier for articulatory info
    try:
        from core.speech_problem_classifier import SpeechProblemClassifier
        
        for phoneme, count in phoneme_error_aggregator.most_common(5):
            # Get articulatory info
            articulatory_info = SpeechProblemClassifier.ARTICULATORY_INFO.get(phoneme, {})
            difficulty = SpeechProblemClassifier.PHONEME_DIFFICULTY.get(phoneme, 3)
            
            phoneme_insights.append({
                "phoneme": phoneme,
                "error_count": count,
                "error_types": dict(phoneme_error_types[phoneme]),  # Simplified for 80/20
                "description": articulatory_info.get("description", f"Practice the /{phoneme}/ sound"),
                "difficulty_level": difficulty
            })
    except ImportError:
        # Fallback if SpeechProblemClassifier not available
        for phoneme, count in phoneme_error_aggregator.most_common(5):
            phoneme_insights.append({
                "phoneme": phoneme,
                "error_count": count,
                "error_types": dict(phoneme_error_types[phoneme]),
                "description": f"Practice the /{phoneme}/ sound",
                "difficulty_level": 3
            })
    
    # Generate recommendations
    recommendations = generate_recommendations(
        recent_accuracy, 
        phoneme_insights, 
        total_sentences, 
        len(session_activities)
    )
    
    return {
        "student_id": student_id,
        "recent_sessions": session_activities,
        "recent_accuracy": round(recent_accuracy, 1),
        "recent_per": round(recent_per, 3),
        "total_sentences_practiced": total_sentences,
        "phoneme_insights": phoneme_insights,
        "recommendations": recommendations,
        "calculation_window": f"Last {len(session_activities)} sessions ({days} days)"
    }


def generate_recommendations(
    accuracy: float, 
    phoneme_insights: list, 
    total_sentences: int,
    num_sessions: int
) -> list[str]:
    """
    Generate actionable recommendations based on student performance.
    
    Args:
        accuracy: Recent accuracy percentage
        phoneme_insights: List of problematic phonemes
        total_sentences: Total sentences practiced
        num_sessions: Number of sessions analyzed
        
    Returns:
        List of recommendation strings
    """
    recommendations = []
    
    # Accuracy-based recommendations
    if accuracy >= 90:
        recommendations.append("✨ Excellent work! This student is ready for more challenging material.")
    elif accuracy >= 75:
        recommendations.append("👍 Good progress! Continue with current practice level and provide encouragement.")
    elif accuracy >= 60:
        recommendations.append("📚 This student needs more practice with foundational sounds. Focus on consistency.")
    else:
        recommendations.append("⚠️ This student is struggling. Consider one-on-one support and simpler material.")
    
    # Phoneme-specific recommendations
    if phoneme_insights:
        top_phoneme = phoneme_insights[0]
        recommendations.append(
            f"🎯 Focus Area: The /{top_phoneme['phoneme']}/ sound needs attention "
            f"({top_phoneme['error_count']} errors). {top_phoneme.get('description', 'Practice this sound regularly.')}"
        )
        
        if len(phoneme_insights) >= 3:
            other_phonemes = [p['phoneme'] for p in phoneme_insights[1:3]]
            recommendations.append(
                f"Also watch for: /{', /'.join(other_phonemes)}/ sounds."
            )
    
    # Practice frequency recommendations
    if num_sessions < 5:
        recommendations.append("📅 Encourage more frequent practice sessions (aim for 3-5 per week).")
    
    # Sentence volume recommendations
    avg_sentences_per_session = total_sentences / num_sessions if num_sessions > 0 else 0
    if avg_sentences_per_session < 5:
        recommendations.append("📖 Encourage longer practice sessions (aim for 10+ sentences per session).")
    
    return recommendations
