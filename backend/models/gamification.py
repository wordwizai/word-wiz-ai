import enum

from database import Base
from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class AchievementRarity(str, enum.Enum):
    COMMON = "common"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


class XPReason(str, enum.Enum):
    SESSION_COMPLETE = "session_complete"
    PERFECT_WORD = "perfect_word"
    PERFECT_SENTENCE = "perfect_sentence"
    DAILY_PRACTICE = "daily_practice"
    STREAK_BONUS = "streak_bonus"
    BADGE_EARNED = "badge_earned"
    STREAK_FREEZE_AWARDED = "streak_freeze_awarded"


class AchievementTrigger(str, enum.Enum):
    SESSIONS_COMPLETED = "sessions_completed"
    STREAK_DAYS = "streak_days"
    WORDS_READ = "words_read"
    PERFECT_WORDS = "perfect_words"
    PERFECT_SENTENCES = "perfect_sentences"
    PER_IMPROVEMENT = "per_improvement"
    LEVEL_REACHED = "level_reached"
    ALL_MODES_TRIED = "all_modes_tried"
    STORY_COMPLETED = "story_completed"
    FREEZE_USED = "freeze_used"
    MANUAL = "manual"  # triggered manually (e.g. comeback kid, night owl)


class AchievementDefinition(Base):
    """Seed-data table — one row per badge definition. Not user-specific."""

    __tablename__ = "achievement_definitions"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=False)
    icon_name = Column(String(64), nullable=False, default="star")
    xp_reward = Column(Integer, nullable=False, default=25)
    trigger_type = Column(Enum(AchievementTrigger), nullable=False)
    threshold_value = Column(Integer, nullable=True)  # e.g. streak of 7
    rarity = Column(
        Enum(AchievementRarity), nullable=False, default=AchievementRarity.COMMON
    )

    user_achievements = relationship("UserAchievement", back_populates="definition")


class UserAchievement(Base):
    """One row per (user, badge) pair — written when the badge is earned."""

    __tablename__ = "user_achievements"
    __table_args__ = (
        UniqueConstraint("user_id", "achievement_id", name="uq_user_achievement"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    achievement_id = Column(
        Integer, ForeignKey("achievement_definitions.id"), nullable=False
    )
    earned_at = Column(DateTime(timezone=True), server_default=func.now())
    xp_at_earn_time = Column(Integer, nullable=False, default=0)

    definition = relationship("AchievementDefinition", back_populates="user_achievements")
    user = relationship("User", back_populates="achievements")


class XPTransaction(Base):
    """Immutable audit log of every XP award."""

    __tablename__ = "xp_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Integer, nullable=False)
    reason = Column(Enum(XPReason), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="xp_transactions")


class UserGamification(Base):
    """
    Denormalised summary of a user's gamification state.
    Kept in sync by the achievement engine so reads are O(1).
    """

    __tablename__ = "user_gamification"

    user_id = Column(
        Integer, ForeignKey("users.id"), primary_key=True, nullable=False
    )
    total_xp = Column(Integer, nullable=False, default=0)
    level = Column(Integer, nullable=False, default=1)
    streak_freezes_available = Column(Integer, nullable=False, default=0)
    lifetime_badges_count = Column(Integer, nullable=False, default=0)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user = relationship("User", back_populates="gamification")
