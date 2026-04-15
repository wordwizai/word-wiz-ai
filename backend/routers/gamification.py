"""
Gamification Router
===================
Endpoints:
  GET  /gamification/me              → UserGamificationOut
  GET  /gamification/me/badges       → list[BadgeWithStatus]
  POST /gamification/streak-freeze   → StreakFreezeResponse
"""

from auth.auth_handler import get_current_active_user
from core.achievement_engine import get_or_create_gamification, use_streak_freeze
from database import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from models import User
from models.gamification import AchievementDefinition, UserAchievement, UserGamification
from schemas.gamification import (
    BadgeWithStatus,
    StreakFreezeResponse,
    UserAchievementOut,
    UserGamificationOut,
    xp_to_level,
)
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/me", response_model=UserGamificationOut)
def get_my_gamification(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Return the current user's gamification summary (XP, level, freezes, recent badges)."""
    gamification = get_or_create_gamification(db, current_user.id)
    level, level_name, xp_into_level, xp_needed_for_next = xp_to_level(
        gamification.total_xp
    )

    # Fetch the 5 most recently earned badges
    recent_badges = (
        db.query(UserAchievement)
        .filter(UserAchievement.user_id == current_user.id)
        .order_by(UserAchievement.earned_at.desc())
        .limit(5)
        .all()
    )

    return UserGamificationOut(
        total_xp=gamification.total_xp,
        level=level,
        level_name=level_name,
        xp_into_level=xp_into_level,
        xp_needed_for_next=xp_needed_for_next,
        streak_freezes_available=gamification.streak_freezes_available,
        lifetime_badges_count=gamification.lifetime_badges_count,
        recent_badges=recent_badges,
    )


@router.get("/me/badges", response_model=list[BadgeWithStatus])
def get_my_badges(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Return all badge definitions, each enriched with whether this user has earned it."""
    all_definitions = db.query(AchievementDefinition).all()

    earned_map: dict[int, UserAchievement] = {}
    earned_rows = (
        db.query(UserAchievement)
        .filter(UserAchievement.user_id == current_user.id)
        .all()
    )
    for ua in earned_rows:
        earned_map[ua.achievement_id] = ua

    result: list[BadgeWithStatus] = []
    for defn in all_definitions:
        ua = earned_map.get(defn.id)
        result.append(
            BadgeWithStatus(
                id=defn.id,
                key=defn.key,
                name=defn.name,
                description=defn.description,
                icon_name=defn.icon_name,
                xp_reward=defn.xp_reward,
                rarity=defn.rarity,
                earned=ua is not None,
                earned_at=ua.earned_at if ua else None,
            )
        )

    # Sort: earned first (most recent), then locked
    result.sort(key=lambda b: (not b.earned, -(b.earned_at.timestamp() if b.earned_at else 0)))
    return result


@router.post("/streak-freeze", response_model=StreakFreezeResponse)
def use_streak_freeze_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Consume one streak freeze to protect the user's current streak."""
    success, message = use_streak_freeze(db, current_user.id)

    gamification = get_or_create_gamification(db, current_user.id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )

    return StreakFreezeResponse(
        success=success,
        message=message,
        streak_freezes_remaining=gamification.streak_freezes_available,
        streak_preserved=True,
    )
