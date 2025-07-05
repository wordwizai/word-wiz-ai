from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth.auth_handler import get_current_active_user
from database import get_db
from schemas import UserResponse, UserSettingsUpdate
from models import User, UserSettings


router = APIRouter()


@router.get("/users/me/", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user


@router.put("/users/me/settings", response_model=UserSettingsUpdate)
async def update_user_settings(
    settings_update: UserSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    settings = db.query(UserSettings).filter_by(user_id=current_user.id).first()
    if not settings:
        settings = UserSettings(user_id=current_user.id)
        db.add(settings)
    for field, value in settings_update.dict(exclude_unset=True).items():
        setattr(settings, field, value)
    db.commit()
    db.refresh(settings)
    return settings


@router.get("/users/me/settings", response_model=UserSettingsUpdate)
async def get_user_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    settings = db.query(UserSettings).filter_by(user_id=current_user.id).first()
    if not settings:
        raise HTTPException(status_code=404, detail="User settings not found")
    return settings
