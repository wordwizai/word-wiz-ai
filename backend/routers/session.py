from auth.auth_handler import get_current_active_user
from crud import session
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
    session_in: SessionCreate,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    # Ensure activity exists
    activity = db.query(Activity).filter(Activity.id == session_in.activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    # Create session
    db_session = session.create_session(db, session_in)
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
    return sessions


@router.get("/{session_id}", response_model=SessionOut)
def get_session_by_id(
    session_id: int,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    db_session = session.get_session(db, session_id)
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session
