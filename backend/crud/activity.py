from models.activity import Activity
from schemas.activity import ActivityCreate, ActivityUpdate
from sqlalchemy.orm import Session


def create_activity(db: Session, activity: ActivityCreate):

    db_activity = Activity(
        title=activity.title,
        type=activity.type,
        target_phoneme=activity.target_phoneme,
        metadata=activity.metadata,
    )
    db.add(db_activity)
    db.commit()
    db.refresh(db_activity)
    return db_activity


def get_activity(db: Session, activity_id: int):
    return db.query(Activity).filter(Activity.id == activity_id).first()


def get_activities(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Activity).offset(skip).limit(limit).all()


def update_activity(db: Session, activity_id: int, activity: ActivityUpdate):
    db_activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not db_activity:
        return None

    for key, value in activity.dict(exclude_unset=True).items():
        setattr(db_activity, key, value)

    db.commit()
    db.refresh(db_activity)
    return db_activity
