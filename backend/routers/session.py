from auth.auth_handler import get_current_active_user
from core.phonics_data import PHONICS_ACTIVITY_TYPE, get_pattern
from core.phonics_scoring import line_index
from crud import session as session_crud
from crud.phonics_sessions import finish_pattern_session
from database import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from models import Activity
from models import Session as UserSession
from models import User
from schemas.session import SessionCreate, SessionCreateRequest, SessionOut
from sqlalchemy.orm import Session as DBSession, selectinload

router = APIRouter()


@router.post("/", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
def create_session(
    session_create_request: SessionCreateRequest,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    # Ensure activity exists
    activity = (
        db.query(Activity)
        .filter(Activity.id == session_create_request.activity_id)
        .first()
    )
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    if activity.activity_type == PHONICS_ACTIVITY_TYPE:
        # A pattern session needs its pattern; POST /phonics/sessions makes them.
        raise HTTPException(status_code=400, detail="Start phonics practice from the Phonics path.")
    # Create session
    session_in = SessionCreate(
        user_id=current_user.id, activity_id=session_create_request.activity_id
    )
    db_session = session_crud.create_session(db, session_in)
    return db_session


@router.get("/active", response_model=list[SessionOut])
def get_active_sessions(
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    sessions = (
        db.query(UserSession)
        .options(selectinload(UserSession.activity), selectinload(UserSession.pattern))
        .filter(UserSession.user_id == current_user.id)
        .filter(UserSession.is_completed == 0)
        .order_by(UserSession.created_at.desc())
        .all()
    )
    return [SessionOut.model_validate(s) for s in sessions]


@router.get("/all", response_model=list[SessionOut])
def get_all_sessions(
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    sessions = (
        db.query(UserSession)
        .options(selectinload(UserSession.activity), selectinload(UserSession.pattern))
        .filter(UserSession.user_id == current_user.id)
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
        print(db_session, "not found for session_id", session_id)
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
    if db_session.pattern is not None:
        # Score the readings so far, so the path doesn't show it as in progress forever.
        finish_pattern_session(db, db_session)
    else:
        db_session.is_completed = 1  # Mark session as completed
        db.commit()
    db.refresh(db_session)
    return SessionOut.model_validate(db_session)


@router.get("/{session_id}/current-data")
def get_current_data_for_session(
    session_id: int,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    # Fetch session from the database
    db_session = session_crud.get_session(db, session_id)
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Ensure the current user is authorized to access this session
    if db_session.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to access this session"
        )

    # Pattern sessions read fixed lines, and the app shows "Line 3 of 7".
    pattern = get_pattern(db_session.pattern_slug) if db_session.pattern_slug else None

    # Retrieve feedback entries if they exist
    feedback = getattr(db_session, "feedback_entries", [])

    # If no feedback exists, return activity settings (or a pattern's first line)
    if not feedback:
        if pattern is not None:
            return {
                "type": "activity-settings",
                "data": {"first_sentence": pattern["lines"][0]},
                "line_index": 0,
                "line_count": len(pattern["lines"]),
            }
        return {
            "type": "activity-settings",
            "data": db_session.activity.activity_settings,
        }

    # The newest reading. Ids follow insertion order; created_at only has whole seconds.
    latest_feedback = max(feedback, key=lambda f: f.id)

    # Return the latest feedback in a structured format
    response = {
        "type": "full-feedback-state",
        "data": latest_feedback,
    }
    if pattern is not None:
        current = (latest_feedback.gpt_response or {}).get("sentence", "")
        index = line_index(pattern, current)
        if index is None:
            # A line no longer in the pattern; the mode counts readings in that case too.
            index = min(len(feedback), len(pattern["lines"]) - 1)
        response["line_index"] = index
        response["line_count"] = len(pattern["lines"])
    return response
