"""Where each child stands on each phonics pattern.

Status is worked out from sessions every time and never stored. Practice
started from the Practice page and practice from before an assignment both
count, so a child who masters -at at home already shows as Mastered when a
teacher assigns it.
"""

from dataclasses import dataclass
from datetime import datetime

from core.phonics_data import all_patterns, units
from core.phonics_scoring import is_mastered
from models import PatternSession, Session
from sqlalchemy.orm import Session as DBSession

NOT_STARTED = "not_started"
IN_PROGRESS = "in_progress"
MASTERED = "mastered"
NEEDS_PRACTICE = "needs_practice"


@dataclass
class PatternStatus:
    status: str = NOT_STARTED
    words_correct: int | None = None
    words_total: int | None = None
    tries: int = 0  # finished sessions
    last_completed_at: datetime | None = None


def status_fields(status: PatternStatus) -> dict:
    """The parts of a status the API returns."""
    return {
        "status": status.status,
        "words_correct": status.words_correct,
        "words_total": status.words_total,
        "tries": status.tries,
    }


def pattern_statuses(db: DBSession, user_ids: list[int]) -> dict[int, dict[str, PatternStatus]]:
    """user id -> pattern slug -> status, for every pattern the user has a session for.

    Untouched patterns are left out; callers treat them as Not started.
    """
    result: dict[int, dict[str, PatternStatus]] = {user_id: {} for user_id in user_ids}
    if not user_ids:
        return result
    rows = (
        db.query(Session.user_id, PatternSession)
        .join(PatternSession, PatternSession.session_id == Session.id)
        .filter(Session.user_id.in_(user_ids))
        .all()
    )
    for user_id, row in rows:
        status = result[user_id].setdefault(row.pattern_slug, PatternStatus())
        if row.completed_at is None:
            # An open try only shows when nothing has been finished yet.
            if status.tries == 0:
                status.status = IN_PROGRESS
            continue
        status.tries += 1
        if status.last_completed_at is None or row.completed_at >= status.last_completed_at:
            status.last_completed_at = row.completed_at
            status.words_correct = row.words_correct
            status.words_total = row.words_total
            status.status = (
                MASTERED if is_mastered(row.words_correct, row.words_total) else NEEDS_PRACTICE
            )
    return result


def curriculum() -> dict:
    """The units in order with their patterns' names, and no status."""
    patterns = all_patterns()
    return {
        "units": [
            {
                "id": unit["id"],
                "title": unit["title"],
                "grade": unit["grade"],
                "patterns": [
                    {"slug": slug, "name": patterns[slug]["display_name"]}
                    for slug in unit["patterns"]
                ],
            }
            for unit in units()
        ]
    }


def phonics_path(statuses: dict[str, PatternStatus]) -> dict:
    """The units with one child's status on each pattern, and the next to practise."""
    patterns = all_patterns()
    next_slug = None
    path_units = []
    for unit in units():
        items = []
        for slug in unit["patterns"]:
            status = statuses.get(slug, PatternStatus())
            if next_slug is None and status.status != MASTERED:
                next_slug = slug
            items.append({"slug": slug, "name": patterns[slug]["display_name"], **status_fields(status)})
        path_units.append({
            "id": unit["id"],
            "title": unit["title"],
            "grade": unit["grade"],
            "mastered_count": sum(1 for item in items if item["status"] == MASTERED),
            "patterns": items,
        })
    return {"units": path_units, "next_slug": next_slug}
