"""Teacher assignments of phonics patterns, and who has each one."""

from collections import Counter

from core.phonics_data import get_pattern, units
from crud.class_membership_crud import get_class_memberships
from crud.phonics_progress import PatternStatus, curriculum, pattern_statuses, status_fields
from models import Assignment, AssignmentStudent, Class, ClassMembership
from sqlalchemy.orm import Session as DBSession, selectinload

# Assignments whose pattern was removed from the data sort last.
_GONE = 10**6


def _unit_titles() -> dict[str, str]:
    return {unit["id"]: unit["title"] for unit in units()}


def _curriculum_order(assignment: Assignment) -> tuple[int, int]:
    pattern = get_pattern(assignment.pattern_slug)
    return (pattern["position"] if pattern else _GONE, assignment.id)


def member_ids(db: DBSession, class_id: int) -> set[int]:
    rows = db.query(ClassMembership.student_id).filter(ClassMembership.class_id == class_id).all()
    return {row[0] for row in rows}


def assign_patterns(db: DBSession, class_id: int, slugs: list[str], student_ids: list[int] | None) -> None:
    """Create or merge one assignment per pattern.

    Assigning a pattern the class already has adds the new students to it,
    and assigning it to the whole class (student_ids None) turns whole_class on.
    A whole-class assignment stays whole-class when it's assigned again to chosen students, since they already have it.
    """
    for slug in dict.fromkeys(slugs):
        assignment = (
            db.query(Assignment)
            .filter(Assignment.class_id == class_id, Assignment.pattern_slug == slug)
            .first()
        )
        if assignment is None:
            assignment = Assignment(class_id=class_id, pattern_slug=slug, whole_class=student_ids is None)
            db.add(assignment)
        elif student_ids is None:
            assignment.whole_class = True
            assignment.students.clear()
        if student_ids is not None and not assignment.whole_class:
            have = {row.student_id for row in assignment.students}
            for student_id in dict.fromkeys(student_ids):
                if student_id not in have:
                    assignment.students.append(AssignmentStudent(student_id=student_id))
                    have.add(student_id)
    db.commit()


def class_assignments(db: DBSession, class_id: int) -> list[dict]:
    """Every assignment in the class with each recipient's status, in curriculum order."""
    memberships = get_class_memberships(db, class_id)
    students = {m.student_id: m.student for m in memberships}
    statuses = pattern_statuses(db, list(students))
    titles = _unit_titles()
    assignments = (
        db.query(Assignment)
        .options(selectinload(Assignment.students))
        .filter(Assignment.class_id == class_id)
        .all()
    )

    result = []
    for assignment in sorted(assignments, key=_curriculum_order):
        pattern = get_pattern(assignment.pattern_slug)
        if assignment.whole_class:
            recipients = list(students)
        else:
            chosen = {row.student_id for row in assignment.students}
            recipients = [sid for sid in students if sid in chosen]
        counts = Counter()
        rows = []
        for student_id in recipients:
            status = statuses[student_id].get(assignment.pattern_slug, PatternStatus())
            counts[status.status] += 1
            rows.append({"id": student_id, "full_name": students[student_id].full_name, **status_fields(status)})
        result.append({
            "id": assignment.id,
            "pattern_slug": assignment.pattern_slug,
            "pattern_name": pattern["display_name"] if pattern else None,
            "unit_title": titles.get(pattern["unit"]) if pattern else None,
            "whole_class": assignment.whole_class,
            "created_at": assignment.created_at,
            "counts": dict(counts),
            "students": rows,
        })
    return result


def student_assignments(db: DBSession, student_id: int) -> list[dict]:
    """Every assignment a child has across their classes, in curriculum order."""
    rows = (
        db.query(Assignment, Class)
        .options(selectinload(Assignment.students))
        .join(Class, Class.id == Assignment.class_id)
        .join(
            ClassMembership,
            (ClassMembership.class_id == Assignment.class_id)
            & (ClassMembership.student_id == student_id),
        )
        .all()
    )
    statuses = pattern_statuses(db, [student_id])[student_id]
    titles = _unit_titles()

    result = []
    for assignment, cls in sorted(rows, key=lambda row: _curriculum_order(row[0])):
        pattern = get_pattern(assignment.pattern_slug)
        if pattern is None:
            continue
        if not assignment.whole_class and student_id not in {s.student_id for s in assignment.students}:
            continue
        status = statuses.get(assignment.pattern_slug, PatternStatus())
        result.append({
            "id": assignment.id,
            "class_id": cls.id,
            "class_name": cls.name,
            "pattern_slug": assignment.pattern_slug,
            "pattern_name": pattern["display_name"],
            "unit_title": titles[pattern["unit"]],
            **status_fields(status),
        })
    return result


def class_phonics_progress(db: DBSession, class_id: int) -> dict:
    """The units, and each student's status on every pattern they've touched."""
    memberships = get_class_memberships(db, class_id)
    statuses = pattern_statuses(db, [m.student_id for m in memberships])
    return {
        "units": curriculum()["units"],
        "students": [
            {
                "id": m.student_id,
                "full_name": m.student.full_name,
                "statuses": {slug: s.status for slug, s in statuses[m.student_id].items()},
            }
            for m in memberships
        ],
    }


def delete_assignment(db: DBSession, class_id: int, assignment_id: int) -> bool:
    """Remove an assignment. Students' sessions and scores are kept."""
    assignment = (
        db.query(Assignment)
        .filter(Assignment.id == assignment_id, Assignment.class_id == class_id)
        .first()
    )
    if assignment is None:
        return False
    db.delete(assignment)
    db.commit()
    return True
