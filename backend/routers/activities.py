from auth.auth_handler import get_current_active_user
from core.phonics_data import PHONICS_ACTIVITY_TYPE
from database import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from models import Activity, User
from schemas.activity import ActivityOut
from sqlalchemy.orm import Session as DBSession

router = APIRouter()


@router.get("/", response_model=list[ActivityOut])
def get_activities(
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    # Every pattern session hangs off one hidden activity. Children reach
    # them through the phonics path, not the activity lists.
    activities = (
        db.query(Activity)
        .filter(Activity.activity_type != PHONICS_ACTIVITY_TYPE)
        .order_by(Activity.id)
        .all()
    )
    return [ActivityOut.model_validate(a) for a in activities]


@router.get("/{activity_id}", response_model=ActivityOut)
def get_activity_by_id(
    activity_id: int,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    return ActivityOut.model_validate(activity)
