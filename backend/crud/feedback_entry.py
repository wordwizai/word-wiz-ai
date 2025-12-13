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
    
    for session in recent_sessions_query:
        # Get all feedback entries for this session
        feedback_entries = (
            db.query(FeedbackEntry)
            .filter(FeedbackEntry.session_id == session.id)
            .all()
        )
        
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
