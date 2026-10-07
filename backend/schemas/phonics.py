from datetime import datetime

from pydantic import BaseModel


class PatternSessionStart(BaseModel):
    pattern_slug: str


class PatternRef(BaseModel):
    slug: str
    name: str


class CurriculumUnit(BaseModel):
    id: str
    title: str
    grade: str
    patterns: list[PatternRef]


class Curriculum(BaseModel):
    units: list[CurriculumUnit]


class PatternProgress(PatternRef):
    status: str
    words_correct: int | None = None
    words_total: int | None = None
    tries: int = 0


class PathUnit(BaseModel):
    id: str
    title: str
    grade: str
    mastered_count: int
    patterns: list[PatternProgress]


class PhonicsPath(BaseModel):
    units: list[PathUnit]
    next_slug: str | None


class StudentAssignment(BaseModel):
    id: int
    class_id: int
    class_name: str
    pattern_slug: str
    pattern_name: str
    unit_title: str
    status: str
    words_correct: int | None = None
    words_total: int | None = None
    tries: int = 0


class AssignRequest(BaseModel):
    pattern_slugs: list[str]
    # None means the whole class, now and as it changes.
    student_ids: list[int] | None = None


class AssignmentStudentStatus(BaseModel):
    id: int
    full_name: str | None
    status: str
    words_correct: int | None = None
    words_total: int | None = None
    tries: int = 0


class StatusCounts(BaseModel):
    mastered: int = 0
    needs_practice: int = 0
    in_progress: int = 0
    not_started: int = 0


class ClassAssignment(BaseModel):
    id: int
    pattern_slug: str
    # None when the pattern has been removed from the data.
    pattern_name: str | None
    unit_title: str | None
    whole_class: bool
    created_at: datetime | None
    counts: StatusCounts
    students: list[AssignmentStudentStatus]


class StudentGridRow(BaseModel):
    id: int
    full_name: str | None
    statuses: dict[str, str]


class ClassPhonicsProgress(BaseModel):
    units: list[CurriculumUnit]
    students: list[StudentGridRow]
