from fastapi import APIRouter, Depends, Form, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, List

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


@router.get("/user/mistake-type-phonemes", response_model=Dict[str, int])
def get_mistake_type_phonemes_for_user(
    mistake_type: str = Query(
        ...,
        description="Type of mistake to filter by: 'insertion', 'deletion', or 'substitution'",
    ),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if (
        mistake_type != "insertion"
        and mistake_type != "deletion"
        and mistake_type != "substitution"
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid mistake type. Must be 'insertion', 'deletion', or 'substitution'.",
        )
    feedback_entries = get_feedback_entries_by_user(
        db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
    )
    mistakes = []
    for entry in feedback_entries:
        # Assume phoneme_analysis is a dict with a "substitution" key for phoneme substitutions
        mistake_entry = None
        if isinstance(entry.phoneme_analysis, dict):
            match mistake_type:
                case "insertion":
                    phoneme_lists = entry.phoneme_analysis.get(
                        "pronunciation_dataframe", {}
                    ).get("added", {})
                    mistake_entry = [
                        item
                        for sublist in (phoneme_lists.values() if phoneme_lists else [])
                        for pair in (sublist if isinstance(sublist, list) else [])
                        if pair
                        for item in pair
                        if item
                    ]
                case "deletion":
                    phoneme_lists = entry.phoneme_analysis.get(
                        "pronunciation_dataframe", {}
                    ).get("missed", {})
                    mistake_entry = [
                        item
                        for sublist in (phoneme_lists.values() if phoneme_lists else [])
                        for pair in (sublist if isinstance(sublist, list) else [])
                        if pair
                        for item in pair
                        if item
                    ]
                case "substitution":
                    substituted = entry.phoneme_analysis.get(
                        "pronunciation_dataframe", {}
                    ).get("substituted", {})
                    mistake_entry = [
                        pair[0]
                        for sublist in (substituted.values() if substituted else [])
                        for pair in (sublist if isinstance(sublist, list) else [])
                        if pair
                    ]
        if mistake_entry is not None:
            mistakes.extend(mistake_entry)

    # turn the mistakes into {phoneme: string: count: number} dict
    mistake_counts = {}
    for mistake in mistakes:
        if isinstance(mistake, str):
            mistake_counts[mistake] = mistake_counts.get(mistake, 0) + 1
    return mistake_counts
