"""The phonics path for the signed-in child (mounted at /phonics)."""

from auth.auth_handler import get_current_active_user
from core.phonics_data import get_pattern
from crud import assignment_crud
from crud.phonics_progress import curriculum, pattern_statuses, phonics_path
from crud.phonics_sessions import start_pattern_session
from database import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from models import User
from schemas.phonics import Curriculum, PatternSessionStart, PhonicsPath, StudentAssignment
from schemas.session import SessionOut
from sqlalchemy.orm import Session as DBSession

router = APIRouter()


@router.get("/curriculum", response_model=Curriculum)
def get_curriculum(current_user: User = Depends(get_current_active_user)):
    """The units in order with pattern names, for the teacher's assign dialog."""
    return curriculum()


@router.get("/path", response_model=PhonicsPath)
def get_my_path(
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Every unit with the child's status on each pattern, and the next one."""
    return phonics_path(pattern_statuses(db, [current_user.id])[current_user.id])


@router.get("/assignments", response_model=list[StudentAssignment])
def get_my_assignments(
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """What the child's teachers have assigned, in curriculum order."""
    return assignment_crud.student_assignments(db, current_user.id)


@router.post("/sessions", response_model=SessionOut)
def start_session(
    body: PatternSessionStart,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Resume the child's unfinished session for the pattern, or start one."""
    if get_pattern(body.pattern_slug) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="That phonics pattern doesn't exist.")
    session = start_pattern_session(db, current_user.id, body.pattern_slug)
    return SessionOut.model_validate(session)
