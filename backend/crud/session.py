from models.session import Session
from schemas.session import SessionCreate
from sqlalchemy.orm import Session as orm_session


def create_session(db: orm_session, session: SessionCreate):
    db_session = Session(
        user_id=session.user_id,
        activity_id=session.activity_id,
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


def get_session(db: orm_session, session_id: int):
    return db.query(Session).filter(Session.id == session_id).first()


def get_sessions_by_user(
    db: orm_session, user_id: int, skip: int = 0, limit: int = 100
):
    return (
        db.query(Session)
        .filter(Session.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
