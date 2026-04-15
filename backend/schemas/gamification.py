from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from models.gamification import AchievementRarity, AchievementTrigger, XPReason


# ---------------------------------------------------------------------------
# Achievement definitions
# ---------------------------------------------------------------------------


class AchievementDefinitionOut(BaseModel):
    id: int
    key: str
    name: str
    description: str
    icon_name: str
    xp_reward: int
    trigger_type: AchievementTrigger
    threshold_value: Optional[int]
    rarity: AchievementRarity

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# User achievements (earned badges)
# ---------------------------------------------------------------------------


class UserAchievementOut(BaseModel):
    id: int
    achievement_id: int
    earned_at: datetime
    xp_at_earn_time: int
    definition: AchievementDefinitionOut

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# XP transaction
# ---------------------------------------------------------------------------


class XPTransactionOut(BaseModel):
    id: int
    amount: int
    reason: XPReason
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# User gamification summary (the main "me" response)
# ---------------------------------------------------------------------------

# Level thresholds — keep in sync with achievement_engine.py
LEVEL_THRESHOLDS = [
    (1, 0, "Beginner Reader"),
    (2, 100, "Phoneme Explorer"),
    (3, 300, "Word Adventurer"),
    (4, 700, "Story Seeker"),
    (5, 1_500, "Reading Champion"),
    (6, 3_000, "Phonics Master"),
    (7, 5_000, "Word Wizard"),
]


def xp_to_level(total_xp: int) -> tuple[int, str, int, int]:
    """
    Return (level, level_name, xp_into_level, xp_needed_for_next).
    At max level xp_needed_for_next == 0.
    """
    current_level, current_name, current_threshold = 1, "Beginner Reader", 0
    next_threshold = 100

    for lvl, threshold, name in LEVEL_THRESHOLDS:
        if total_xp >= threshold:
            current_level = lvl
            current_name = name
            current_threshold = threshold
        else:
            next_threshold = threshold
            break
    else:
        # max level
        return current_level, current_name, 0, 0

    xp_into_level = total_xp - current_threshold
    xp_needed = next_threshold - current_threshold
    return current_level, current_name, xp_into_level, xp_needed


class BadgeWithStatus(BaseModel):
    """A badge definition enriched with whether this user has earned it."""

    id: int
    key: str
    name: str
    description: str
    icon_name: str
    xp_reward: int
    rarity: AchievementRarity
    earned: bool
    earned_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserGamificationOut(BaseModel):
    total_xp: int
    level: int
    level_name: str
    xp_into_level: int
    xp_needed_for_next: int
    streak_freezes_available: int
    lifetime_badges_count: int
    recent_badges: list[UserAchievementOut]

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Gamification update payload (returned after each analysis)
# ---------------------------------------------------------------------------


class NewlyEarnedBadge(BaseModel):
    key: str
    name: str
    description: str
    icon_name: str
    xp_reward: int
    rarity: AchievementRarity


class GamificationUpdateOut(BaseModel):
    """
    Sent to the client after each sentence analysis so the UI can show
    XP gains and newly earned badges without a separate round-trip.
    """

    xp_earned: int
    total_xp: int
    level: int
    level_name: str
    xp_into_level: int
    xp_needed_for_next: int
    leveled_up: bool
    streak_freezes_available: int
    newly_earned_badges: list[NewlyEarnedBadge]


# ---------------------------------------------------------------------------
# Streak freeze request/response
# ---------------------------------------------------------------------------


class StreakFreezeResponse(BaseModel):
    success: bool
    message: str
    streak_freezes_remaining: int
    streak_preserved: bool
