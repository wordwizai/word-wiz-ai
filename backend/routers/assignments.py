"""Teacher routes for assigning phonics patterns (mounted under /classes)."""

from auth.auth_handler import get_current_active_user
from core.phonics_data import get_pattern
from crud import assignment_crud, class_crud, class_membership_crud
from crud.phonics_progress import pattern_statuses, phonics_path
from database import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from models import Class, User
from schemas.phonics import AssignRequest, ClassAssignment, ClassPhonicsProgress, PhonicsPath
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DBSession

router = APIRouter()


def _own_class(db: DBSession, class_id: int, user: User) -> Class:
    db_class = class_crud.get_class_by_id(db, class_id)
    if not db_class:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    if db_class.teacher_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the teacher of this class can manage its practice",
        )
    return db_class


@router.get("/{class_id}/assignments", response_model=list[ClassAssignment])
def list_assignments(
    class_id: int,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Every assignment in the class with each student's status."""
    _own_class(db, class_id, current_user)
    return assignment_crud.class_assignments(db, class_id)


@router.post("/{class_id}/assignments", response_model=list[ClassAssignment])
def create_assignments(
    class_id: int,
    body: AssignRequest,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Assign patterns to the whole class (student_ids null) or chosen students."""
    _own_class(db, class_id, current_user)
    slugs = list(dict.fromkeys(body.pattern_slugs))
    if not slugs:
        raise HTTPException(status_code=400, detail="Pick at least one pattern to assign.")
    unknown = [slug for slug in slugs if get_pattern(slug) is None]
    if unknown:
        raise HTTPException(status_code=400, detail=f"Unknown patterns: {', '.join(unknown)}")
    if body.student_ids is not None:
        if not body.student_ids:
            raise HTTPException(status_code=400, detail="Pick at least one student, or assign to the whole class.")
        if not set(body.student_ids) <= assignment_crud.member_ids(db, class_id):
            raise HTTPException(status_code=400, detail="Some of those students aren't in this class.")
    try:
        assignment_crud.assign_patterns(db, class_id, slugs, body.student_ids)
    except IntegrityError:
        # Another request created the same (class, pattern) row first; retrying merges into it.
        db.rollback()
        assignment_crud.assign_patterns(db, class_id, slugs, body.student_ids)
    return assignment_crud.class_assignments(db, class_id)


@router.delete("/{class_id}/assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_assignment(
    class_id: int,
    assignment_id: int,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    _own_class(db, class_id, current_user)
    if not assignment_crud.delete_assignment(db, class_id, assignment_id):
        raise HTTPException(status_code=404, detail="Assignment not found")
    return None


@router.get("/{class_id}/phonics-progress", response_model=ClassPhonicsProgress)
def class_progress(
    class_id: int,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Students by patterns, for the class's Phonics path grid."""
    _own_class(db, class_id, current_user)
    return assignment_crud.class_phonics_progress(db, class_id)


@router.get("/{class_id}/students/{student_id}/phonics-path", response_model=PhonicsPath)
def student_path(
    class_id: int,
    student_id: int,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """One student's phonics path, as they see it on the Practice page."""
    _own_class(db, class_id, current_user)
    if not class_membership_crud.is_member(db, class_id, student_id):
        raise HTTPException(status_code=404, detail="Student is not a member of this class")
    return phonics_path(pattern_statuses(db, [student_id])[student_id])
