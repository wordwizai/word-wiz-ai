from auth.auth_handler import get_current_active_user
from crud import session as session_crud
from database import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from models import Activity
from models import Session as UserSession
from models import User
from schemas.session import SessionCreate, SessionOut
from sqlalchemy.orm import Session as DBSession

router = APIRouter()


@router.post("/", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
def create_session(
    activity_id: int,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    # Ensure activity exists
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    # Create session
    session_in = SessionCreate(user_id=current_user.id, activity_id=activity_id)
    db_session = session_crud.create_session(db, session_in)
    return db_session


@router.get("/active", response_model=list[SessionOut])
def get_active_sessions(
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    sessions = (
        db.query(UserSession)
        .filter(UserSession.user_id == current_user.id)
        .filter(UserSession.is_completed == 0)  # Assuming is_completed is a boolean
        .order_by(UserSession.created_at.desc())
        .all()
    )
    return [SessionOut.model_validate(s) for s in sessions]


@router.get("/{session_id}", response_model=SessionOut)
def get_session_by_id(
    session_id: int,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    db_session = session_crud.get_session(db, session_id)
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    if db_session.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to access this session"
        )
    return SessionOut.model_validate(db_session)


@router.post("/{session_id}/deactivate", response_model=SessionOut)
def deactivate_session(
    session_id: int,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    db_session = session_crud.get_session(db, session_id)
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    if db_session.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to deactivate this session"
        )
    db_session.is_completed = 1  # Mark session as completed
    db.commit()
    db.refresh(db_session)
    return SessionOut.model_validate(db_session)
