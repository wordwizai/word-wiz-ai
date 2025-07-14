from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from auth.auth_handler import get_current_user
from database import get_db
from crud.feedback_entry import get_feedback_entries_by_user
from schemas.feedback_entry import FeedbackEntryOut
from models.user import User

router = APIRouter()


@router.get("/user/entries", response_model=List[FeedbackEntryOut])
def read_feedback_entries_for_user(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_feedback_entries_by_user(
        db, user_id=current_user.id, skip=skip, limit=limit
    )


@router.get("/user/sentence-pers", response_model=List[dict])
def get_sentence_pers_for_user(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    feedback_entries = get_feedback_entries_by_user(
        db, user_id=current_user.id, skip=skip, limit=limit
    )
    pers = []
    for entry in feedback_entries:
        # Assume phoneme_analysis is a dict with a "per" key for sentence PER
        per_entry = None
        if isinstance(entry.phoneme_analysis, dict):
            per_entry = {
                "date": entry.created_at,
                "per": entry.phoneme_analysis.get("per_summary", "").get(
                    "sentence_per", 0
                ),
            }
        if per_entry is not None:
            pers.append(per_entry)
    return pers
