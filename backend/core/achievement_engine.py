"""
Achievement Engine
==================
Central service that awards XP, evaluates badge conditions, and keeps the
UserGamification summary table in sync.

Call ``process_sentence_result`` after every successful sentence analysis
(i.e. after the FeedbackEntry is committed).  It is synchronous and safe to
call inside a FastAPI dependency or a WebSocket handler.

Architecture
------------
- All writes are wrapped in a single transaction.
- Badge definitions are seeded once (``seed_achievements``).
- The engine is intentionally stateless — it reads everything it needs from
  the DB on each call so it stays correct even with concurrent sessions.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from models.feedback_entry import FeedbackEntry
from models.gamification import (
    AchievementDefinition,
    AchievementRarity,
    AchievementTrigger,
    UserAchievement,
    UserGamification,
    XPReason,
    XPTransaction,
)
from models.session import Session as SessionModel
from schemas.gamification import GamificationUpdateOut, NewlyEarnedBadge, xp_to_level

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Level thresholds (must match schemas/gamification.py)
# ---------------------------------------------------------------------------

LEVEL_THRESHOLDS: list[tuple[int, int, str]] = [
    (1, 0, "Beginner Reader"),
    (2, 100, "Phoneme Explorer"),
    (3, 300, "Word Adventurer"),
    (4, 700, "Story Seeker"),
    (5, 1_500, "Reading Champion"),
    (6, 3_000, "Phonics Master"),
    (7, 5_000, "Word Wizard"),
]

MAX_STREAK_FREEZES = 3

# ---------------------------------------------------------------------------
# Badge seed data
# ---------------------------------------------------------------------------

ACHIEVEMENT_SEED: list[dict] = [
    # First steps
    dict(key="FIRST_SESSION",    name="First Steps",       description="Complete your first practice session",               icon_name="footprints",   xp_reward=50,  trigger_type=AchievementTrigger.SESSIONS_COMPLETED,  threshold_value=1,   rarity=AchievementRarity.COMMON),
    # Session milestones
    dict(key="SESSIONS_5",       name="Getting Started",   description="Complete 5 practice sessions",                        icon_name="book-open",    xp_reward=30,  trigger_type=AchievementTrigger.SESSIONS_COMPLETED,  threshold_value=5,   rarity=AchievementRarity.COMMON),
    dict(key="SESSIONS_25",      name="Regular Reader",    description="Complete 25 practice sessions",                       icon_name="books",        xp_reward=100, trigger_type=AchievementTrigger.SESSIONS_COMPLETED,  threshold_value=25,  rarity=AchievementRarity.RARE),
    dict(key="SESSIONS_100",     name="Dedicated Learner", description="Complete 100 practice sessions",                      icon_name="trophy",       xp_reward=300, trigger_type=AchievementTrigger.SESSIONS_COMPLETED,  threshold_value=100, rarity=AchievementRarity.EPIC),
    # Streak milestones
    dict(key="STREAK_3",         name="On a Roll",         description="Practice 3 days in a row",                            icon_name="flame",        xp_reward=30,  trigger_type=AchievementTrigger.STREAK_DAYS,         threshold_value=3,   rarity=AchievementRarity.COMMON),
    dict(key="STREAK_7",         name="One Week Wonder",   description="Practice 7 days in a row",                            icon_name="fire",         xp_reward=75,  trigger_type=AchievementTrigger.STREAK_DAYS,         threshold_value=7,   rarity=AchievementRarity.RARE),
    dict(key="STREAK_14",        name="Two Week Streak",   description="Practice 14 days in a row",                           icon_name="fire-high",    xp_reward=150, trigger_type=AchievementTrigger.STREAK_DAYS,         threshold_value=14,  rarity=AchievementRarity.RARE),
    dict(key="STREAK_30",        name="Reading Machine",   description="Practice 30 days in a row",                           icon_name="rocket",       xp_reward=300, trigger_type=AchievementTrigger.STREAK_DAYS,         threshold_value=30,  rarity=AchievementRarity.EPIC),
    # Words read
    dict(key="WORDS_10",         name="First 10 Words",    description="Read 10 words total",                                  icon_name="letter-a",     xp_reward=20,  trigger_type=AchievementTrigger.WORDS_READ,          threshold_value=10,  rarity=AchievementRarity.COMMON),
    dict(key="WORDS_100",        name="Century Reader",    description="Read 100 words total",                                 icon_name="scroll",       xp_reward=50,  trigger_type=AchievementTrigger.WORDS_READ,          threshold_value=100, rarity=AchievementRarity.COMMON),
    dict(key="WORDS_500",        name="Half Thousand",     description="Read 500 words total",                                 icon_name="library",      xp_reward=100, trigger_type=AchievementTrigger.WORDS_READ,          threshold_value=500, rarity=AchievementRarity.RARE),
    dict(key="WORDS_1000",       name="Word Wizard",       description="Read 1,000 words total — you're a Word Wizard!",       icon_name="wand",         xp_reward=250, trigger_type=AchievementTrigger.WORDS_READ,          threshold_value=1000,rarity=AchievementRarity.EPIC),
    # Accuracy
    dict(key="PERFECT_WORD",     name="Nailed It",         description="Pronounce a word with a perfect score",                icon_name="star",         xp_reward=25,  trigger_type=AchievementTrigger.PERFECT_WORDS,       threshold_value=1,   rarity=AchievementRarity.COMMON),
    dict(key="PERFECT_SENTENCE", name="Flawless",          description="Read an entire sentence perfectly",                    icon_name="sparkles",     xp_reward=75,  trigger_type=AchievementTrigger.PERFECT_SENTENCES,   threshold_value=1,   rarity=AchievementRarity.RARE),
    # PER improvement
    dict(key="PER_IMPROVE_20",   name="Getting Better",    description="Improve your average accuracy by 20% in a week",       icon_name="trending-up",  xp_reward=100, trigger_type=AchievementTrigger.PER_IMPROVEMENT,     threshold_value=20,  rarity=AchievementRarity.RARE),
    # Content exploration
    dict(key="STORY_COMPLETE",   name="Story Teller",      description="Complete a full story mode activity",                  icon_name="book-heart",   xp_reward=75,  trigger_type=AchievementTrigger.STORY_COMPLETED,     threshold_value=1,   rarity=AchievementRarity.RARE),
    dict(key="ALL_MODES",        name="Explorer",          description="Try all 3 practice modes",                             icon_name="compass",      xp_reward=50,  trigger_type=AchievementTrigger.ALL_MODES_TRIED,     threshold_value=3,   rarity=AchievementRarity.RARE),
    # Level milestones
    dict(key="LEVEL_5",          name="Reading Champion",  description="Reach level 5",                                        icon_name="medal",        xp_reward=200, trigger_type=AchievementTrigger.LEVEL_REACHED,       threshold_value=5,   rarity=AchievementRarity.EPIC),
    dict(key="LEVEL_7",          name="Word Wizard Elite", description="Reach the maximum level — Word Wizard!",               icon_name="crown",        xp_reward=500, trigger_type=AchievementTrigger.LEVEL_REACHED,       threshold_value=7,   rarity=AchievementRarity.LEGENDARY),
    # Manual / time-based
    dict(key="COMEBACK_KID",     name="Comeback Kid",      description="Return to practice after a 3+ day absence",           icon_name="refresh",      xp_reward=30,  trigger_type=AchievementTrigger.MANUAL,              threshold_value=None, rarity=AchievementRarity.COMMON),
    dict(key="NIGHT_OWL",        name="Night Owl",         description="Complete a practice session after 8pm",               icon_name="moon",         xp_reward=15,  trigger_type=AchievementTrigger.MANUAL,              threshold_value=None, rarity=AchievementRarity.COMMON),
    dict(key="EARLY_BIRD",       name="Early Bird",        description="Complete a practice session before 8am",              icon_name="sun",          xp_reward=15,  trigger_type=AchievementTrigger.MANUAL,              threshold_value=None, rarity=AchievementRarity.COMMON),
    dict(key="FREEZE_USED",      name="Smart Saver",       description="Use a streak freeze to protect your streak",           icon_name="snowflake",    xp_reward=20,  trigger_type=AchievementTrigger.FREEZE_USED,         threshold_value=1,   rarity=AchievementRarity.COMMON),
    dict(key="PERFECT_STREAK_7", name="Flawless Week",     description="Maintain accuracy above 85% for 7 sessions in a row", icon_name="gem",          xp_reward=250, trigger_type=AchievementTrigger.MANUAL,              threshold_value=None, rarity=AchievementRarity.EPIC),
    dict(key="SHARE_MOMENT",     name="Proud Reader",      description="Share an achievement with someone",                    icon_name="share",        xp_reward=25,  trigger_type=AchievementTrigger.MANUAL,              threshold_value=None, rarity=AchievementRarity.COMMON),
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def seed_achievements(db: Session) -> None:
    """
    Upsert badge definitions into the DB.
    Safe to call on every startup — existing rows are skipped.
    """
    for data in ACHIEVEMENT_SEED:
        existing = (
            db.query(AchievementDefinition)
            .filter(AchievementDefinition.key == data["key"])
            .first()
        )
        if existing is None:
            db.add(AchievementDefinition(**data))
    db.commit()
    log.info("Achievement definitions seeded.")


def get_or_create_gamification(db: Session, user_id: int) -> UserGamification:
    """Return the UserGamification row, creating it lazily if absent."""
    row = db.query(UserGamification).filter(UserGamification.user_id == user_id).first()
    if row is None:
        row = UserGamification(user_id=user_id)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def process_sentence_result(
    db: Session,
    user_id: int,
    session_id: int,
    phoneme_analysis: dict,
    activity_type: Optional[str] = None,
) -> GamificationUpdateOut:
    """
    Called after every sentence analysis.  Awards XP, checks badges, and
    returns a ``GamificationUpdateOut`` to stream back to the client.

    Parameters
    ----------
    db               : SQLAlchemy session (already open; this fn commits)
    user_id          : ID of the practising user
    session_id       : ID of the current practice session
    phoneme_analysis : The ``phoneme_analysis`` dict stored on FeedbackEntry
    activity_type    : "unlimited" | "story" | "choice-story" (optional)
    """
    gamification = get_or_create_gamification(db, user_id)
    level_before = gamification.level

    xp_earned = 0
    newly_earned: list[NewlyEarnedBadge] = []

    # -----------------------------------------------------------------------
    # 1. Compute per-sentence stats from phoneme_analysis
    # -----------------------------------------------------------------------
    per_summary = phoneme_analysis.get("per_summary", {}) if phoneme_analysis else {}
    sentence_per: float = per_summary.get("sentence_per", 1.0) or 1.0
    word_results: list[dict] = phoneme_analysis.get("word_results", []) if phoneme_analysis else []

    perfect_words_this_sentence = sum(
        1 for w in word_results if (w.get("per", 1.0) or 1.0) == 0.0
    )
    perfect_sentence = sentence_per == 0.0

    # -----------------------------------------------------------------------
    # 2. XP: per-sentence awards
    # -----------------------------------------------------------------------
    # Base: complete a sentence
    xp_earned += _award_xp(db, user_id, 20, XPReason.SESSION_COMPLETE)

    # Perfect words bonus
    if perfect_words_this_sentence:
        xp_earned += _award_xp(
            db, user_id, 5 * perfect_words_this_sentence, XPReason.PERFECT_WORD
        )

    # Perfect sentence bonus
    if perfect_sentence:
        xp_earned += _award_xp(db, user_id, 15, XPReason.PERFECT_SENTENCE)

    # Daily bonuses — only once per calendar day (first sentence of the day)
    first_today = _is_first_sentence_today(db, user_id, session_id)
    current_streak = _get_current_streak(db, user_id)

    if first_today:
        xp_earned += _award_xp(db, user_id, 10, XPReason.DAILY_PRACTICE)

        # Streak bonus (day N → +5*N XP, capped at 150 to avoid exploit)
        if current_streak > 1:
            streak_bonus = min(5 * current_streak, 150)
            xp_earned += _award_xp(db, user_id, streak_bonus, XPReason.STREAK_BONUS)

    # -----------------------------------------------------------------------
    # 3. Refresh aggregate stats needed for badge evaluation
    # -----------------------------------------------------------------------
    total_sessions = _count_sessions(db, user_id)
    total_words = _count_words(db, user_id)
    has_perfect_word_ever = _has_ever_perfect_word(db, user_id)
    has_perfect_sentence_ever = _has_ever_perfect_sentence(db, user_id)
    modes_tried = _count_distinct_modes(db, user_id)

    # -----------------------------------------------------------------------
    # 4. Update gamification summary table
    # -----------------------------------------------------------------------
    gamification.total_xp += xp_earned
    gamification.level = _compute_level(gamification.total_xp)
    leveled_up = gamification.level > level_before

    # Award streak freeze every 7 consecutive days
    if current_streak > 0 and current_streak % 7 == 0:
        if gamification.streak_freezes_available < MAX_STREAK_FREEZES:
            gamification.streak_freezes_available += 1
            _award_xp(db, user_id, 5, XPReason.STREAK_FREEZE_AWARDED)

    db.add(gamification)
    db.commit()
    db.refresh(gamification)

    # -----------------------------------------------------------------------
    # 5. Evaluate badges
    # -----------------------------------------------------------------------
    already_earned = _earned_keys(db, user_id)

    def _maybe_earn(key: str) -> None:
        if key not in already_earned:
            badge = _earn_badge(db, user_id, key, gamification)
            if badge:
                newly_earned.append(badge)
                already_earned.add(key)

    # Sessions
    for key, threshold in [
        ("FIRST_SESSION", 1),
        ("SESSIONS_5", 5),
        ("SESSIONS_25", 25),
        ("SESSIONS_100", 100),
    ]:
        if total_sessions >= threshold:
            _maybe_earn(key)

    # Streak
    for key, threshold in [
        ("STREAK_3", 3),
        ("STREAK_7", 7),
        ("STREAK_14", 14),
        ("STREAK_30", 30),
    ]:
        if current_streak >= threshold:
            _maybe_earn(key)

    # Words read
    for key, threshold in [
        ("WORDS_10", 10),
        ("WORDS_100", 100),
        ("WORDS_500", 500),
        ("WORDS_1000", 1000),
    ]:
        if total_words >= threshold:
            _maybe_earn(key)

    # Accuracy
    if has_perfect_word_ever:
        _maybe_earn("PERFECT_WORD")
    if has_perfect_sentence_ever:
        _maybe_earn("PERFECT_SENTENCE")

    # Content exploration
    if modes_tried >= 3:
        _maybe_earn("ALL_MODES")

    # Level achievements
    for key, threshold in [("LEVEL_5", 5), ("LEVEL_7", 7)]:
        if gamification.level >= threshold:
            _maybe_earn(key)

    # Time-of-day (check session start time)
    hour = _session_hour(db, session_id)
    if hour is not None:
        if hour >= 20:
            _maybe_earn("NIGHT_OWL")
        if hour < 8:
            _maybe_earn("EARLY_BIRD")

    # Comeback kid (gap ≥ 3 days before this session)
    if _is_comeback(db, user_id, session_id):
        _maybe_earn("COMEBACK_KID")

    # Flawless week (7 consecutive sessions with PER < 0.15)
    if _flawless_week(db, user_id):
        _maybe_earn("PERFECT_STREAK_7")

    # PER improvement of 20% week-over-week
    if _per_improved_20pct(db, user_id):
        _maybe_earn("PER_IMPROVE_20")

    # Refresh after badge XP was added
    db.refresh(gamification)

    # -----------------------------------------------------------------------
    # 6. Build response
    # -----------------------------------------------------------------------
    level, level_name, xp_into_level, xp_needed_for_next = xp_to_level(
        gamification.total_xp
    )

    return GamificationUpdateOut(
        xp_earned=xp_earned,
        total_xp=gamification.total_xp,
        level=level,
        level_name=level_name,
        xp_into_level=xp_into_level,
        xp_needed_for_next=xp_needed_for_next,
        leveled_up=leveled_up,
        streak_freezes_available=gamification.streak_freezes_available,
        newly_earned_badges=newly_earned,
    )


def use_streak_freeze(db: Session, user_id: int) -> tuple[bool, str]:
    """
    Attempt to use a streak freeze for the user.
    Returns (success, message).
    """
    gamification = get_or_create_gamification(db, user_id)

    if gamification.streak_freezes_available <= 0:
        return False, "No streak freezes available."

    gamification.streak_freezes_available -= 1
    db.add(gamification)
    db.commit()

    # Award the FREEZE_USED badge
    already_earned = _earned_keys(db, user_id)
    if "FREEZE_USED" not in already_earned:
        _earn_badge(db, user_id, "FREEZE_USED", gamification)

    return True, "Streak freeze applied! Your streak is protected."


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _award_xp(db: Session, user_id: int, amount: int, reason: XPReason) -> int:
    """Write an XP transaction row. Returns the amount awarded."""
    if amount <= 0:
        return 0
    tx = XPTransaction(user_id=user_id, amount=amount, reason=reason)
    db.add(tx)
    # Note: caller must db.commit() after collecting all XP awards
    return amount


def _earn_badge(
    db: Session,
    user_id: int,
    key: str,
    gamification: UserGamification,
) -> Optional[NewlyEarnedBadge]:
    """
    Award a badge to a user.  Returns a ``NewlyEarnedBadge`` if successful,
    None if the definition doesn't exist or already earned.
    """
    defn = (
        db.query(AchievementDefinition)
        .filter(AchievementDefinition.key == key)
        .first()
    )
    if defn is None:
        log.warning("Badge key %r not found in DB — run seed_achievements().", key)
        return None

    ua = UserAchievement(
        user_id=user_id,
        achievement_id=defn.id,
        xp_at_earn_time=gamification.total_xp,
    )
    db.add(ua)

    # XP reward for the badge itself
    _award_xp(db, user_id, defn.xp_reward, XPReason.BADGE_EARNED)
    gamification.total_xp += defn.xp_reward
    gamification.level = _compute_level(gamification.total_xp)
    gamification.lifetime_badges_count += 1
    db.add(gamification)

    try:
        db.commit()
    except Exception:
        db.rollback()
        log.warning("Could not award badge %r (likely duplicate).", key)
        return None

    log.info("User %d earned badge %r (+%d XP).", user_id, key, defn.xp_reward)

    return NewlyEarnedBadge(
        key=defn.key,
        name=defn.name,
        description=defn.description,
        icon_name=defn.icon_name,
        xp_reward=defn.xp_reward,
        rarity=defn.rarity,
    )


def _compute_level(total_xp: int) -> int:
    level = 1
    for lvl, threshold, _ in LEVEL_THRESHOLDS:
        if total_xp >= threshold:
            level = lvl
    return level


def _earned_keys(db: Session, user_id: int) -> set[str]:
    rows = (
        db.query(AchievementDefinition.key)
        .join(UserAchievement, UserAchievement.achievement_id == AchievementDefinition.id)
        .filter(UserAchievement.user_id == user_id)
        .all()
    )
    return {r.key for r in rows}


def _count_sessions(db: Session, user_id: int) -> int:
    return (
        db.query(SessionModel)
        .filter(SessionModel.user_id == user_id)
        .count()
    )


def _count_words(db: Session, user_id: int) -> int:
    rows = (
        db.query(FeedbackEntry.sentence)
        .join(SessionModel, FeedbackEntry.session_id == SessionModel.id)
        .filter(SessionModel.user_id == user_id)
        .all()
    )
    return sum(len(r.sentence.split()) for r in rows if r.sentence)


def _get_current_streak(db: Session, user_id: int) -> int:
    from crud.feedback_entry import calculate_streaks

    rows = (
        db.query(SessionModel.created_at)
        .filter(SessionModel.user_id == user_id)
        .order_by(SessionModel.created_at.desc())
        .all()
    )
    session_dates = sorted(
        set(r.created_at.date() for r in rows), reverse=True
    )
    current, _ = calculate_streaks(session_dates)
    return current


def _is_first_sentence_today(db: Session, user_id: int, session_id: int) -> bool:
    """True if this is the first feedback entry created today for this user."""
    today = date.today()
    count = (
        db.query(FeedbackEntry)
        .join(SessionModel, FeedbackEntry.session_id == SessionModel.id)
        .filter(
            SessionModel.user_id == user_id,
            FeedbackEntry.created_at >= today,
        )
        .count()
    )
    # ≤ 1 because the current entry was just committed
    return count <= 1


def _has_ever_perfect_word(db: Session, user_id: int) -> bool:
    entries = (
        db.query(FeedbackEntry.phoneme_analysis)
        .join(SessionModel, FeedbackEntry.session_id == SessionModel.id)
        .filter(SessionModel.user_id == user_id)
        .all()
    )
    for row in entries:
        analysis = row.phoneme_analysis or {}
        for w in analysis.get("word_results", []):
            if (w.get("per", 1.0) or 1.0) == 0.0:
                return True
    return False


def _has_ever_perfect_sentence(db: Session, user_id: int) -> bool:
    entries = (
        db.query(FeedbackEntry.phoneme_analysis)
        .join(SessionModel, FeedbackEntry.session_id == SessionModel.id)
        .filter(SessionModel.user_id == user_id)
        .all()
    )
    for row in entries:
        analysis = row.phoneme_analysis or {}
        per_summary = analysis.get("per_summary", {})
        if (per_summary.get("sentence_per", 1.0) or 1.0) == 0.0:
            return True
    return False


def _count_distinct_modes(db: Session, user_id: int) -> int:
    from models.activity import Activity

    rows = (
        db.query(Activity.activity_type)
        .join(SessionModel, SessionModel.activity_id == Activity.id)
        .filter(SessionModel.user_id == user_id)
        .distinct()
        .all()
    )
    return len(rows)


def _session_hour(db: Session, session_id: int) -> Optional[int]:
    row = db.query(SessionModel.created_at).filter(SessionModel.id == session_id).first()
    if row and row.created_at:
        return row.created_at.hour
    return None


def _is_comeback(db: Session, user_id: int, current_session_id: int) -> bool:
    """True if the previous session was 3+ days ago."""
    sessions = (
        db.query(SessionModel.created_at)
        .filter(SessionModel.user_id == user_id)
        .order_by(SessionModel.created_at.desc())
        .limit(2)
        .all()
    )
    if len(sessions) < 2:
        return False
    gap = sessions[0].created_at.date() - sessions[1].created_at.date()
    return gap.days >= 3


def _flawless_week(db: Session, user_id: int) -> bool:
    """True if the last 7 FeedbackEntries all have sentence_per < 0.15."""
    entries = (
        db.query(FeedbackEntry.phoneme_analysis)
        .join(SessionModel, FeedbackEntry.session_id == SessionModel.id)
        .filter(SessionModel.user_id == user_id)
        .order_by(FeedbackEntry.created_at.desc())
        .limit(7)
        .all()
    )
    if len(entries) < 7:
        return False
    for row in entries:
        analysis = row.phoneme_analysis or {}
        per = analysis.get("per_summary", {}).get("sentence_per", 1.0) or 1.0
        if per >= 0.15:
            return False
    return True


def _per_improved_20pct(db: Session, user_id: int) -> bool:
    """
    True if the rolling average PER of the last 5 sentences is ≥ 20% better
    than the 5 sentences before that (i.e. lower by 20%).
    """
    entries = (
        db.query(FeedbackEntry.phoneme_analysis)
        .join(SessionModel, FeedbackEntry.session_id == SessionModel.id)
        .filter(SessionModel.user_id == user_id)
        .order_by(FeedbackEntry.created_at.desc())
        .limit(10)
        .all()
    )
    if len(entries) < 10:
        return False

    def avg_per(batch):
        vals = []
        for row in batch:
            analysis = row.phoneme_analysis or {}
            per = analysis.get("per_summary", {}).get("sentence_per", 1.0) or 1.0
            vals.append(per)
        return sum(vals) / len(vals)

    recent_avg = avg_per(entries[:5])
    older_avg = avg_per(entries[5:])

    if older_avg == 0:
        return False
    improvement = (older_avg - recent_avg) / older_avg
    return improvement >= 0.20
