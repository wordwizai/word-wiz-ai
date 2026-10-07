# Phonics Curriculum and Teacher Assignments Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the 113 practice-word patterns into an ordered 18-unit phonics path that any signed-in child can work through, and let teachers assign patterns or units to a class or chosen students and see who has mastered each sound.

**Architecture:** The unit order lives in a new `frontend/src/data/phonicsCurriculum.json`. An export script copies the patterns, units and reading lines into `backend/data/phonics_patterns.json`. A new `phonics-pattern` mode reads fixed lines with no GPT, scores the pattern's words when the last line is read, and stores the score on a new `pattern_sessions` table. `assignments` and `assignment_students` tables record what teachers asked for. Status (not started, in progress, mastered, needs practice) is always computed from sessions.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, Python `unittest`; React 19 + TypeScript, Tailwind v4, shadcn/Radix, `node --test`.

**Spec:** `docs/superpowers/specs/2026-10-06-phonics-curriculum-assignments-design.md`

---

## Working environment (read first)

- Work happens in the worktree `C:\Users\bruce\Coding\word-wiz-ai\.claude\worktrees\phonics-curriculum` on branch `feat/phonics-curriculum`. All paths below are relative to it.
- The worktree has no Python venv. Use the main checkout's interpreter, always with UTF-8 output (log lines contain emoji and crash on the Windows code page otherwise):
  `PYTHONUTF8=1 /c/Users/bruce/Coding/word-wiz-ai/backend/venv/Scripts/python.exe`
- Backend tests run from `backend/` with `-m unittest tests.<module>`. They use in-memory SQLite and must never touch `backend/.env`'s `DATABASE_URL` (that is the shared production RDS database).
- The worktree has no `node_modules`. Task 11 makes a junction to the main checkout's; the last task removes it with `cmd /c rmdir` so a recursive delete can never follow it.
- `npm run typecheck` already reports **9 errors** on `dev` (3 of them in `src/api.ts` lines 28, 47 and 56). The count must stay 9.
- Commit only files this plan touches. Commit messages are plain sentences and end with:
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

## File map

**Backend, new**
- `backend/scripts/export_phonics_data.py` (renamed from `export_guest_sentences.py`), builds `backend/data/phonics_patterns.json`
- `backend/core/phonics_data.py`, read-only loader for that JSON
- `backend/core/phonics_scoring.py`, pure scoring of a session's readings
- `backend/core/modes/phonics_pattern.py`, the fixed-line mode
- `backend/models/pattern_session.py`, `backend/models/assignment.py`
- `backend/alembic/versions/c4d5e6f7a8b9_add_phonics_curriculum_tables.py`
- `backend/crud/phonics_sessions.py` (start, resume, finish), `backend/crud/phonics_progress.py` (status, path, curriculum), `backend/crud/assignment_crud.py`
- `backend/schemas/phonics.py`
- `backend/routers/phonics.py` (student), `backend/routers/assignments.py` (teacher)
- Tests: `backend/tests/phonics_helpers.py`, `test_phonics_data.py`, `test_phonics_models.py`, `test_phonics_scoring.py`, `test_phonics_sessions.py`, `test_phonics_mode.py`, `test_phonics_progress.py`, `test_assignments_api.py`, `test_phonics_api.py`

**Backend, modified**
- `backend/routers/guest.py`, `backend/tests/test_guest_router.py` (new data file and script name)
- `backend/models/__init__.py`, `backend/models/session.py`, `backend/models/class_model.py`
- `backend/schemas/session.py`
- `backend/routers/handlers/audio_processing_handler.py` (`session_complete` event)
- `backend/routers/ai.py`, `backend/routers/session.py`, `backend/routers/activities.py`, `backend/main.py`
- `backend/dev_server.py` (seed a teacher and class)

**Backend, deleted:** `backend/data/guest_sentences.json`

**Frontend, new**
- `frontend/src/data/phonicsCurriculum.json`
- `frontend/src/lib/phonics.ts` + `frontend/src/lib/phonics.test.ts`
- `frontend/src/hooks/usePhonics.ts`
- `frontend/src/components/practice/PatternFinish.tsx`
- `frontend/src/components/phonics/PatternStatusChip.tsx`, `TeacherAssignments.tsx`, `PhonicsPathView.tsx`, `ContinuePathCard.tsx`
- `frontend/src/pages/PhonicsPathPage.tsx`
- `frontend/src/components/classes/AssignPracticeDialog.tsx`, `AssignmentsPanel.tsx`, `PhonicsGrid.tsx`, `StudentPhonicsPath.tsx`

**Frontend, modified**
- `frontend/src/api.ts`, `frontend/src/services/audioTransport.ts`, `frontend/src/hooks/useAudioTransport.ts`
- `frontend/src/components/practice/BasePractice.tsx`, `GenericPractice.tsx`, `frontend/src/pages/PracticeRouter.tsx`
- `frontend/src/config/practiceTypes.ts`, `frontend/src/lib/activities.ts`
- `frontend/src/pages/Dashboard.tsx`, `frontend/src/pages/PracticeDashboard.tsx`, `frontend/src/App.tsx`
- `frontend/src/components/classes/ClassDetailView.tsx`, `StudentDetailView.tsx`

**Docs:** `CLAUDE.md`

---

### Task 1: Curriculum data, export script and loader

**Files:**
- Create: `frontend/src/data/phonicsCurriculum.json`
- Rename + rewrite: `backend/scripts/export_guest_sentences.py` → `backend/scripts/export_phonics_data.py`
- Create (generated): `backend/data/phonics_patterns.json`
- Delete: `backend/data/guest_sentences.json`
- Create: `backend/core/phonics_data.py`
- Modify: `backend/routers/guest.py`, `backend/tests/test_guest_router.py`
- Test: `backend/tests/test_phonics_data.py`

- [ ] **Step 1: Write the curriculum file**

Create `frontend/src/data/phonicsCurriculum.json`:

```json
{
  "units": [
    { "id": "short-a", "title": "Short a word families", "grade": "Kindergarten",
      "patterns": ["at-family", "an-family", "ap-family", "ad-family", "ag-family", "am-family", "ab-family"] },
    { "id": "short-i", "title": "Short i word families", "grade": "Kindergarten",
      "patterns": ["ig-family", "in-family", "ip-family", "it-family", "id-family"] },
    { "id": "short-o", "title": "Short o word families", "grade": "Kindergarten",
      "patterns": ["op-family", "ot-family", "og-family", "ob-family", "ox-family"] },
    { "id": "short-u", "title": "Short u word families", "grade": "Kindergarten",
      "patterns": ["ug-family", "un-family", "ut-family", "ub-family", "um-family", "up-family"] },
    { "id": "short-e", "title": "Short e word families", "grade": "Kindergarten",
      "patterns": ["ed-family", "en-family", "et-family", "eg-family"] },
    { "id": "digraphs", "title": "Digraphs", "grade": "Kindergarten–Grade 1",
      "patterns": ["sh-digraph", "ch-digraph", "th-digraph", "wh-digraph", "ph-digraph", "ash-family", "unch-family"] },
    { "id": "ck-tch", "title": "ck and tch", "grade": "Kindergarten–Grade 1",
      "patterns": ["ck-digraph", "ack-family", "eck-family", "ick-family", "ock-family", "uck-family", "atch-family"] },
    { "id": "double-letters", "title": "Double letters", "grade": "Kindergarten–Grade 1",
      "patterns": ["ill-family", "ell-family", "oss-family", "uff-family"] },
    { "id": "s-blends", "title": "S-blends", "grade": "Kindergarten–Grade 1",
      "patterns": ["st-blend", "sp-blend", "sk-blend", "sm-blend", "sn-blend", "sw-blend", "sc-blend", "tw-blend"] },
    { "id": "l-blends", "title": "L-blends", "grade": "Grade 1",
      "patterns": ["bl-blend", "cl-blend", "fl-blend", "gl-blend", "pl-blend", "sl-blend"] },
    { "id": "r-blends", "title": "R-blends", "grade": "Grade 1",
      "patterns": ["br-blend", "cr-blend", "dr-blend", "fr-blend", "gr-blend", "pr-blend", "tr-blend"] },
    { "id": "ending-nd-nt-mp", "title": "Ending blends -nd, -nt, -mp", "grade": "Grade 1",
      "patterns": ["and-family", "end-family", "ond-family", "ent-family", "amp-family", "imp-family", "ump-family"] },
    { "id": "ending-st-ft-lt", "title": "Ending blends -st, -ft, -lt", "grade": "Grade 1",
      "patterns": ["ast-family", "est-family", "ist-family", "ust-family", "ift-family", "oft-family", "elt-family", "ilt-family"] },
    { "id": "glued-sounds", "title": "Glued sounds ng and nk", "grade": "Grade 1",
      "patterns": ["ng-digraph", "ang-family", "ing-family", "ong-family", "ank-family", "ink-family", "unk-family"] },
    { "id": "silent-e", "title": "Silent e", "grade": "Grade 1",
      "patterns": ["a-e-magic-e", "i-e-magic-e", "o-e-magic-e", "u-e-magic-e"] },
    { "id": "r-controlled", "title": "R-controlled vowels", "grade": "Grade 1–2",
      "patterns": ["ar-r-controlled", "or-r-controlled", "er-r-controlled", "ir-r-controlled", "ur-r-controlled"] },
    { "id": "long-vowel-teams", "title": "Long vowel teams", "grade": "Grade 1–2",
      "patterns": ["ai-vowel-team", "ay-vowel-team", "ee-vowel-team", "ea-vowel-team", "oa-vowel-team", "oe-vowel-team", "ie-vowel-team", "ue-vowel-team", "ui-vowel-team"] },
    { "id": "other-vowel-teams", "title": "Other vowel teams", "grade": "Grade 1–2",
      "patterns": ["oo-vowel-team", "ow-vowel-team", "ou-vowel-team", "oi-vowel-team", "oy-vowel-team", "au-vowel-team", "aw-vowel-team"] }
  ]
}
```

- [ ] **Step 2: Write the failing tests**

Create `backend/tests/test_phonics_data.py`:

```python
"""Tests for the phonics data export (scripts/export_phonics_data.py) and loader.

Run from backend/:  python -m unittest tests.test_phonics_data
"""

import importlib.util
import sys
import unittest
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from core import phonics_data  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "export_phonics_data", BACKEND / "scripts" / "export_phonics_data.py"
)
export = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(export)


def sizes(lines):
    return [len(line.split()) for line in lines]


class WordLinesTest(unittest.TestCase):
    def test_deals_words_evenly_into_lines_of_five_or_fewer(self):
        self.assertEqual(sizes(export.word_lines([f"w{i}" for i in range(14)])), [5, 5, 4])
        self.assertEqual(sizes(export.word_lines([f"w{i}" for i in range(11)])), [4, 4, 3])
        self.assertEqual(sizes(export.word_lines([f"w{i}" for i in range(16)])), [4, 4, 4, 4])

    def test_short_list_is_one_line_in_order(self):
        self.assertEqual(export.word_lines(["cat", "hat", "bat"]), ["cat hat bat"])
        self.assertEqual(export.word_lines(list("abcdef")), ["a b c", "d e f"])


class UnitsTest(unittest.TestCase):
    PATTERNS = {"at-family": {}, "an-family": {}}

    def curriculum(self, *unit_patterns):
        return {
            "units": [
                {"id": f"u{i}", "title": f"Unit {i}", "grade": "K", "patterns": list(p)}
                for i, p in enumerate(unit_patterns)
            ]
        }

    def test_unknown_pattern_is_refused(self):
        with self.assertRaisesRegex(ValueError, "unknown pattern nope"):
            export.build_units(self.curriculum(["at-family", "an-family", "nope"]), self.PATTERNS)

    def test_pattern_in_two_units_is_refused(self):
        with self.assertRaisesRegex(ValueError, "at-family is in both u0 and u1"):
            export.build_units(self.curriculum(["at-family", "an-family"], ["at-family"]), self.PATTERNS)

    def test_pattern_in_no_unit_is_refused(self):
        with self.assertRaisesRegex(ValueError, "in no unit: an-family"):
            export.build_units(self.curriculum(["at-family"]), self.PATTERNS)


class BuildTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = export.build()

    def test_every_pattern_is_placed_in_curriculum_order(self):
        self.assertEqual(len(self.data["units"]), 18)
        self.assertEqual(len(self.data["patterns"]), 113)
        positions = [p["position"] for p in self.data["patterns"].values()]
        self.assertEqual(positions, list(range(113)))

    def test_at_family_reads_word_lines_then_sentences(self):
        at = self.data["patterns"]["at-family"]
        self.assertEqual(at["display_name"], "-at Word Family")
        self.assertEqual(at["unit"], "short-a")
        self.assertEqual(at["word_line_count"], 3)
        self.assertEqual(at["lines"][0], "cat hat bat mat rat")
        self.assertEqual(at["lines"][3:], at["sentences"])


class LoaderTest(unittest.TestCase):
    def test_reads_patterns_and_units(self):
        self.assertEqual(phonics_data.get_pattern("sh-digraph")["unit"], "digraphs")
        self.assertIsNone(phonics_data.get_pattern("nope"))
        self.assertEqual(phonics_data.units()[0]["id"], "short-a")
        self.assertEqual(next(iter(phonics_data.all_patterns())), "at-family")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the tests to make sure they fail**

Run: `cd backend && PYTHONUTF8=1 /c/Users/bruce/Coding/word-wiz-ai/backend/venv/Scripts/python.exe -m unittest tests.test_phonics_data`
Expected: ERROR, `ImportError: cannot import name 'phonics_data' from 'core'`.

- [ ] **Step 4: Rename and rewrite the export script**

Run: `git mv backend/scripts/export_guest_sentences.py backend/scripts/export_phonics_data.py`

Replace the whole of `backend/scripts/export_phonics_data.py` with:

```python
"""Export the phonics patterns and curriculum that the backend needs.

The words and sentences live in frontend/src/data/phonicsPatterns.ts and the
unit order in frontend/src/data/phonicsCurriculum.json. The backend container
never sees the frontend, so this script copies what the backend needs into
backend/data/phonics_patterns.json. Two things read that file.

- routers/guest.py only scores sentences from the practice-word pages, so the
  public "try it" route can't be used as a free speech recognizer.
- core/phonics_data.py serves the phonics path and pattern sessions.

Run it after editing either frontend file, then redeploy the backend:

    python scripts/export_phonics_data.py          # rewrite the JSON
    python scripts/export_phonics_data.py --check  # exit 1 if it's stale

It refuses a curriculum that leaves a pattern out, lists one twice or names
one that doesn't exist. tests/test_guest_router.py runs the --check
comparison, so a stale file fails the backend tests.
"""

import json
import math
import re
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_DIR.parent / "frontend" / "src" / "data"
PATTERNS_SOURCE = DATA_DIR / "phonicsPatterns.ts"
CURRICULUM_SOURCE = DATA_DIR / "phonicsCurriculum.json"
TARGET = BACKEND_DIR / "data" / "phonics_patterns.json"

# Word lines are read like sentences, so keep them short for young readers.
MAX_WORDS_PER_LINE = 5

_BLOCK = re.compile(r'^\s*slug:\s*"([^"]+)"(.*?)^\s*relatedSlugs:', re.M | re.S)
_DISPLAY_NAME = re.compile(r'displayName:\s*"((?:[^"\\]|\\.)*)"')
_WORDS = re.compile(r"\bwords:\s*\[(.*?)\]", re.S)
_SENTENCES = re.compile(r"sampleSentences:\s*\[(.*?)\]", re.S)
_STRING = re.compile(r'"((?:[^"\\]|\\.)*)"')


def _strings(body: str) -> list[str]:
    return [json.loads(f'"{s}"') for s in _STRING.findall(body)]


def extract_patterns(source_text: str) -> dict[str, dict]:
    """Map each pattern slug to its name, words and sentences, in file order."""
    patterns: dict[str, dict] = {}
    for slug, body in _BLOCK.findall(source_text):
        name = _DISPLAY_NAME.search(body)
        if not name:
            raise ValueError(f"{slug} has no displayName")
        fields = {"display_name": json.loads(f'"{name.group(1)}"')}
        for key, regex in (("words", _WORDS), ("sentences", _SENTENCES)):
            match = regex.search(body)
            values = _strings(match.group(1)) if match else []
            if not values:
                raise ValueError(f"{slug} has no {key}")
            fields[key] = values
        patterns[slug] = fields
    if not patterns:
        raise ValueError(f"No patterns found in {PATTERNS_SOURCE}")
    return patterns


def word_lines(words: list[str], per_line: int = MAX_WORDS_PER_LINE) -> list[str]:
    """Deal the words, in order, into the fewest lines of at most `per_line`.

    The lines are as even as possible, so 14 words become 5, 5 and 4 rather
    than leaving a lonely word on the last line.
    """
    if not words:
        return []
    count = math.ceil(len(words) / per_line)
    base, extra = divmod(len(words), count)
    lines, start = [], 0
    for i in range(count):
        size = base + (1 if i < extra else 0)
        lines.append(" ".join(words[start:start + size]))
        start += size
    return lines


def build_units(curriculum: dict, patterns: dict) -> list[dict]:
    """Check the curriculum places every pattern exactly once and copy it."""
    placed: dict[str, str] = {}
    units = []
    for unit in curriculum["units"]:
        for slug in unit["patterns"]:
            if slug not in patterns:
                raise ValueError(f"Unit {unit['id']} lists unknown pattern {slug}")
            if slug in placed:
                raise ValueError(f"{slug} is in both {placed[slug]} and {unit['id']}")
            placed[slug] = unit["id"]
        units.append({
            "id": unit["id"],
            "title": unit["title"],
            "grade": unit["grade"],
            "patterns": list(unit["patterns"]),
        })
    missing = [slug for slug in patterns if slug not in placed]
    if missing:
        raise ValueError(f"Patterns in no unit: {', '.join(missing)}")
    return units


def build() -> dict:
    patterns = extract_patterns(PATTERNS_SOURCE.read_text(encoding="utf-8"))
    curriculum = json.loads(CURRICULUM_SOURCE.read_text(encoding="utf-8"))
    units = build_units(curriculum, patterns)

    ordered: dict[str, dict] = {}
    for unit in units:
        for slug in unit["patterns"]:
            pattern = patterns[slug]
            lines = word_lines(pattern["words"])
            ordered[slug] = {
                "display_name": pattern["display_name"],
                "unit": unit["id"],
                "position": len(ordered),
                "words": pattern["words"],
                "sentences": pattern["sentences"],
                "word_line_count": len(lines),
                "lines": lines + pattern["sentences"],
            }
    return {
        "source": "frontend/src/data/phonicsPatterns.ts and phonicsCurriculum.json",
        "note": "Generated by backend/scripts/export_phonics_data.py. Do not edit by hand.",
        "units": units,
        "patterns": ordered,
    }


def main() -> int:
    data = build()
    rendered = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if "--check" in sys.argv:
        current = TARGET.read_text(encoding="utf-8") if TARGET.exists() else ""
        # git may check the file out with CRLF endings on Windows.
        if current.replace("\r\n", "\n") != rendered:
            print(f"{TARGET} is stale. Run: python scripts/export_phonics_data.py")
            return 1
        print(f"{TARGET} is up to date ({len(data['patterns'])} patterns).")
        return 0
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(rendered, encoding="utf-8")
    print(f"Wrote {TARGET} ({len(data['units'])} units, {len(data['patterns'])} patterns).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Generate the data file and remove the old one**

Run:
```bash
cd backend && PYTHONUTF8=1 /c/Users/bruce/Coding/word-wiz-ai/backend/venv/Scripts/python.exe scripts/export_phonics_data.py && git rm -q data/guest_sentences.json
```
Expected: `Wrote ...phonics_patterns.json (18 units, 113 patterns).`

- [ ] **Step 6: Write the loader**

Create `backend/core/phonics_data.py`:

```python
"""The phonics patterns and curriculum, read from data/phonics_patterns.json.

That file is generated from the frontend data by scripts/export_phonics_data.py.
Everything here is read-only and loaded once per process.
"""

import json
from functools import lru_cache
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "phonics_patterns.json"

# Every pattern session belongs to the one activity of this type.
PHONICS_ACTIVITY_TYPE = "phonics-pattern"


@lru_cache(maxsize=1)
def _data() -> dict:
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def get_pattern(slug: str) -> dict | None:
    """A pattern's name, unit, position, words, sentences and reading lines."""
    return _data()["patterns"].get(slug)


def all_patterns() -> dict[str, dict]:
    """Every pattern by slug, in curriculum order."""
    return _data()["patterns"]


def units() -> list[dict]:
    """The units in order, each with id, title, grade and pattern slugs."""
    return _data()["units"]
```

- [ ] **Step 7: Point the guest route at the new file**

In `backend/routers/guest.py`:

Replace the docstring line
```
- only scores sentences from the practice-word pages (data/guest_sentences.json),
```
with
```
- only scores sentences from the practice-word pages (data/phonics_patterns.json),
```

Replace
```python
import asyncio
import json
from pathlib import Path

from core.guest_limits import SlidingWindowLimiter, client_ip, normalize_sentence
```
with
```python
import asyncio
import json

from core.guest_limits import SlidingWindowLimiter, client_ip, normalize_sentence
from core.phonics_data import all_patterns
```

Replace
```python
_SENTENCES_FILE = Path(__file__).resolve().parent.parent / "data" / "guest_sentences.json"


def _load_allowed_sentences() -> set[str]:
    data = json.loads(_SENTENCES_FILE.read_text(encoding="utf-8"))
    return {
        normalize_sentence(sentence)
        for sentences in data["patterns"].values()
        for sentence in sentences
    }
```
with
```python
def _load_allowed_sentences() -> set[str]:
    return {
        normalize_sentence(sentence)
        for pattern in all_patterns().values()
        for sentence in pattern["sentences"]
    }
```

In `backend/tests/test_guest_router.py` replace `"export_guest_sentences.py"` with `"export_phonics_data.py"`.

- [ ] **Step 8: Run the tests**

Run: `cd backend && PYTHONUTF8=1 /c/Users/bruce/Coding/word-wiz-ai/backend/venv/Scripts/python.exe -m unittest tests.test_phonics_data tests.test_guest_router`
Expected: `OK` (8 phonics data tests, 16 guest tests).

- [ ] **Step 9: Commit**

```bash
git add frontend/src/data/phonicsCurriculum.json backend/scripts/export_phonics_data.py backend/data/phonics_patterns.json backend/core/phonics_data.py backend/routers/guest.py backend/tests/test_guest_router.py backend/tests/test_phonics_data.py
git commit -m "$(cat <<'EOF'
Order the phonics patterns into 18 units and export them for the backend

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
)"
```
(`git rm` in Step 5 already staged the deletion of `guest_sentences.json`.)

---

### Task 2: Tables, migration and test helpers

**Files:**
- Create: `backend/models/pattern_session.py`, `backend/models/assignment.py`
- Modify: `backend/models/__init__.py`, `backend/models/session.py`, `backend/models/class_model.py`, `backend/schemas/session.py`
- Create: `backend/alembic/versions/c4d5e6f7a8b9_add_phonics_curriculum_tables.py`
- Create: `backend/tests/phonics_helpers.py`
- Test: `backend/tests/test_phonics_models.py`

- [ ] **Step 1: Write the shared test helpers**

Create `backend/tests/phonics_helpers.py`:

```python
"""Shared setup for the phonics tests.

Importing this module first points DATABASE_URL at in-memory SQLite, so
database.py (imported by the models) can never reach the shared RDS database
in .env. Each test then builds its own throwaway database with make_db().
"""

import itertools
import os
import sys
from pathlib import Path
from types import SimpleNamespace

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

import models  # noqa: E402,F401  (registers every table on Base)
from database import Base  # noqa: E402
from models import Class, ClassMembership, FeedbackEntry, User  # noqa: E402

_join_codes = itertools.count(1)


def make_db():
    """A sessionmaker for a fresh in-memory database.

    StaticPool keeps a single connection, so FastAPI's TestClient threads all
    see the same tables.
    """
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def make_user(db, name: str) -> User:
    handle = name.lower().replace(" ", ".")
    user = User(
        full_name=name,
        username=handle,
        email=f"{handle}@example.test",
        hashed_password="not-a-real-hash",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def make_class(db, teacher: User, *students: User, name: str = "Room 4") -> Class:
    cls = Class(name=name, join_code=f"T{next(_join_codes):05d}", teacher_id=teacher.id)
    db.add(cls)
    db.commit()
    for student in students:
        join(db, cls, student)
    db.refresh(cls)
    return cls


def join(db, cls: Class, student: User) -> None:
    db.add(ClassMembership(class_id=cls.id, student_id=student.id))
    db.commit()


def analysis(words, inserted: int = 0) -> dict:
    """A saved phoneme_analysis with (expected word, per) rows.

    Same shape the audio stream stores: pandas' to_dict() of the
    pronunciation dataframe, keyed by row number. Inserted sounds have no
    expected word.
    """
    rows = list(words) + [(None, 0.0)] * inserted
    return {
        "pronunciation_dataframe": {
            "ground_truth_word": {str(i): word for i, (word, _) in enumerate(rows)},
            "per": {str(i): per for i, (_, per) in enumerate(rows)},
        }
    }


def add_reading(db, session, sentence: str, per: float = 0.0, next_sentence: str = "") -> None:
    """Save one reading of `sentence` where every word scored `per`."""
    words = [(word.strip(".,!?").lower(), per) for word in sentence.split()]
    db.add(FeedbackEntry(
        session_id=session.id,
        sentence=sentence,
        phoneme_analysis=analysis(words),
        gpt_response={"sentence": next_sentence},
    ))
    db.commit()


def make_client(SessionLocal, *routes):
    """A TestClient for (prefix, router) pairs. Returns as_user(user) -> client.

    The signed-in user is a plain namespace holding the id, so no ORM object
    crosses into the TestClient's thread.
    """
    from auth.auth_handler import get_current_active_user
    from database import get_db
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    app = FastAPI()
    for prefix, router in routes:
        app.include_router(router, prefix=prefix)
    signed_in = {}

    def override_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_active_user] = lambda: signed_in["user"]
    client = TestClient(app)

    def as_user(user):
        signed_in["user"] = SimpleNamespace(id=user.id, full_name=user.full_name)
        return client

    return as_user
```

- [ ] **Step 2: Write the failing tests**

Create `backend/tests/test_phonics_models.py`:

```python
"""Tests for the phonics tables, SessionOut's pattern fields and the migration.

Run from backend/:  python -m unittest tests.test_phonics_models
"""

import importlib.util
import unittest

from tests.phonics_helpers import BACKEND, make_db, make_user

from alembic.migration import MigrationContext  # noqa: E402
from alembic.operations import Operations  # noqa: E402
from sqlalchemy import create_engine, inspect  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from database import Base  # noqa: E402
from models import Activity, PatternSession, Session  # noqa: E402
from schemas.session import SessionOut  # noqa: E402

MIGRATION = BACKEND / "alembic" / "versions" / "c4d5e6f7a8b9_add_phonics_curriculum_tables.py"
NEW_TABLES = {"pattern_sessions", "assignments", "assignment_students"}


class SessionPatternTest(unittest.TestCase):
    def setUp(self):
        self.db = make_db()()
        self.addCleanup(self.db.close)
        self.child = make_user(self.db, "Maya")

    def make_session(self, activity_type, slug=None):
        activity = Activity(title="A", description="d", activity_type=activity_type, activity_settings={})
        self.db.add(activity)
        self.db.commit()
        session = Session(user_id=self.child.id, activity_id=activity.id)
        if slug:
            session.pattern = PatternSession(pattern_slug=slug)
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return SessionOut.model_validate(session)

    def test_session_out_carries_the_pattern(self):
        out = self.make_session("phonics-pattern", "at-family")
        self.assertEqual((out.pattern_slug, out.pattern_name), ("at-family", "-at Word Family"))

    def test_other_sessions_have_no_pattern(self):
        out = self.make_session("unlimited")
        self.assertEqual((out.pattern_slug, out.pattern_name), (None, None))

    def test_a_pattern_missing_from_the_data_has_no_name(self):
        out = self.make_session("phonics-pattern", "gone-family")
        self.assertEqual((out.pattern_slug, out.pattern_name), ("gone-family", None))


class MigrationTest(unittest.TestCase):
    def engine(self):
        return create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )

    def run_upgrade(self, engine):
        spec = importlib.util.spec_from_file_location("phonics_migration", MIGRATION)
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)
        with engine.begin() as conn:
            with Operations.context(MigrationContext.configure(conn)):
                migration.upgrade()

    def test_creates_the_new_tables(self):
        engine = self.engine()
        old = [t for name, t in Base.metadata.tables.items() if name not in NEW_TABLES]
        Base.metadata.create_all(bind=engine, tables=old)
        self.run_upgrade(engine)
        self.assertTrue(NEW_TABLES <= set(inspect(engine).get_table_names()))

    def test_does_nothing_when_create_all_made_them_first(self):
        engine = self.engine()
        Base.metadata.create_all(bind=engine)
        self.run_upgrade(engine)  # must not fail with "table already exists"


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the tests to make sure they fail**

Run: `cd backend && PYTHONUTF8=1 /c/Users/bruce/Coding/word-wiz-ai/backend/venv/Scripts/python.exe -m unittest tests.test_phonics_models`
Expected: ERROR, `ImportError: cannot import name 'PatternSession' from 'models'`.

- [ ] **Step 4: Add the models**

Create `backend/models/pattern_session.py`:

```python
from database import Base
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship


class PatternSession(Base):
    """The phonics pattern a session practises, and its score once finished.

    It sits beside `sessions` instead of adding columns to it. main.py's
    create_all makes missing tables at startup but never adds columns, so a
    new table can't break session queries if the Alembic step is missed.
    """

    __tablename__ = "pattern_sessions"
    session_id = Column(
        Integer, ForeignKey("sessions.id", ondelete="CASCADE"), primary_key=True
    )
    pattern_slug = Column(String(64), nullable=False, index=True)
    words_correct = Column(Integer, nullable=True)
    words_total = Column(Integer, nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    session = relationship("Session", back_populates="pattern")
```

Create `backend/models/assignment.py`:

```python
from database import Base
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class Assignment(Base):
    """A phonics pattern a teacher gave to their class or to chosen students.

    One row per class and pattern. Progress is never stored here; it comes
    from the students' sessions (crud/phonics_progress.py).
    """

    __tablename__ = "assignments"
    id = Column(Integer, primary_key=True)
    class_id = Column(Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)
    pattern_slug = Column(String(64), nullable=False)
    # On: everyone in the class when it's read. Off: only assignment_students.
    whole_class = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    class_obj = relationship("Class", back_populates="assignments")
    students = relationship(
        "AssignmentStudent", back_populates="assignment", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("class_id", "pattern_slug", name="unique_class_pattern"),
    )


class AssignmentStudent(Base):
    __tablename__ = "assignment_students"
    id = Column(Integer, primary_key=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    assignment = relationship("Assignment", back_populates="students")

    __table_args__ = (
        UniqueConstraint("assignment_id", "student_id", name="unique_assignment_student"),
    )
```

Replace `backend/models/session.py` with:

```python
from core.phonics_data import get_pattern
from database import Base
from sqlalchemy import Column, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class Session(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_completed = Column(Integer, default=0)  # 0: not completed, 1: completed

    user = relationship("User", back_populates="sessions")
    activity = relationship("Activity", back_populates="sessions")
    feedback_entries = relationship("FeedbackEntry", back_populates="session")
    # Only phonics pattern sessions have one (models/pattern_session.py).
    pattern = relationship(
        "PatternSession",
        back_populates="session",
        uselist=False,
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    @property
    def pattern_slug(self) -> str | None:
        return self.pattern.pattern_slug if self.pattern else None

    @property
    def pattern_name(self) -> str | None:
        found = get_pattern(self.pattern_slug) if self.pattern_slug else None
        return found["display_name"] if found else None
```

In `backend/models/class_model.py` add after the `memberships` relationship:

```python
    assignments = relationship("Assignment", back_populates="class_obj", cascade="all, delete-orphan")
```

Replace `backend/models/__init__.py` with:

```python
from .activity import Activity
from .assignment import Assignment, AssignmentStudent
from .class_membership import ClassMembership
from .class_model import Class
from .feedback_entry import FeedbackEntry
from .pattern_session import PatternSession
from .session import Session
from .theme_mode import ThemeMode
from .user import User
from .user_settings import UserSettings

__all__ = [
    "User", "ThemeMode", "UserSettings", "Activity", "Session", "FeedbackEntry",
    "Class", "ClassMembership", "PatternSession", "Assignment", "AssignmentStudent",
]
```

In `backend/schemas/session.py`, replace the `SessionOut` class with:

```python
class SessionOut(SessionBase):
    id: int
    created_at: datetime  # ISO format date string
    is_completed: bool  # True for completed, False for not completed
    activity: ActivityOut
    # Phonics pattern sessions only, read from Session's properties.
    pattern_slug: str | None = None
    pattern_name: str | None = None

    model_config = {"from_attributes": True}
```

- [ ] **Step 5: Add the migration**

Create `backend/alembic/versions/c4d5e6f7a8b9_add_phonics_curriculum_tables.py`:

```python
"""add phonics curriculum tables

Revision ID: c4d5e6f7a8b9
Revises: b2c3d4e5f6g7
Create Date: 2026-10-06 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4d5e6f7a8b9'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6g7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(name: str) -> bool:
    # main.py runs create_all at startup, so a deployed backend may already
    # have made these tables by the time this migration runs.
    return sa.inspect(op.get_bind()).has_table(name)


def upgrade() -> None:
    """Create pattern_sessions, assignments and assignment_students."""
    if not _has_table('pattern_sessions'):
        op.create_table(
            'pattern_sessions',
            sa.Column('session_id', sa.Integer(), nullable=False),
            sa.Column('pattern_slug', sa.String(length=64), nullable=False),
            sa.Column('words_correct', sa.Integer(), nullable=True),
            sa.Column('words_total', sa.Integer(), nullable=True),
            sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('session_id'),
        )
        op.create_index(op.f('ix_pattern_sessions_pattern_slug'), 'pattern_sessions', ['pattern_slug'], unique=False)

    if not _has_table('assignments'):
        op.create_table(
            'assignments',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('class_id', sa.Integer(), nullable=False),
            sa.Column('pattern_slug', sa.String(length=64), nullable=False),
            sa.Column('whole_class', sa.Boolean(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
            sa.ForeignKeyConstraint(['class_id'], ['classes.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('class_id', 'pattern_slug', name='unique_class_pattern'),
        )
        op.create_index(op.f('ix_assignments_class_id'), 'assignments', ['class_id'], unique=False)

    if not _has_table('assignment_students'):
        op.create_table(
            'assignment_students',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('assignment_id', sa.Integer(), nullable=False),
            sa.Column('student_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['assignment_id'], ['assignments.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('assignment_id', 'student_id', name='unique_assignment_student'),
        )
        op.create_index(op.f('ix_assignment_students_assignment_id'), 'assignment_students', ['assignment_id'], unique=False)
        op.create_index(op.f('ix_assignment_students_student_id'), 'assignment_students', ['student_id'], unique=False)


def downgrade() -> None:
    """Drop the phonics curriculum tables."""
    op.drop_index(op.f('ix_assignment_students_student_id'), table_name='assignment_students')
    op.drop_index(op.f('ix_assignment_students_assignment_id'), table_name='assignment_students')
    op.drop_table('assignment_students')
    op.drop_index(op.f('ix_assignments_class_id'), table_name='assignments')
    op.drop_table('assignments')
    op.drop_index(op.f('ix_pattern_sessions_pattern_slug'), table_name='pattern_sessions')
    op.drop_table('pattern_sessions')
```

- [ ] **Step 6: Run the tests**

Run: `cd backend && PYTHONUTF8=1 /c/Users/bruce/Coding/word-wiz-ai/backend/venv/Scripts/python.exe -m unittest tests.test_phonics_models tests.test_guest_router`
Expected: `OK` (5 + 16 tests).

- [ ] **Step 7: Commit**

```bash
git add backend/models backend/schemas/session.py backend/alembic/versions/c4d5e6f7a8b9_add_phonics_curriculum_tables.py backend/tests/phonics_helpers.py backend/tests/test_phonics_models.py
git commit -m "$(cat <<'EOF'
Add tables for pattern sessions and teacher assignments

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: Scoring a pattern session

**Files:**
- Create: `backend/core/phonics_scoring.py`
- Test: `backend/tests/test_phonics_scoring.py`

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_phonics_scoring.py`:

```python
"""Tests for core/phonics_scoring.py (no database).

Run from backend/:  python -m unittest tests.test_phonics_scoring
"""

import unittest

from tests.phonics_helpers import analysis

from core.phonics_scoring import is_mastered, line_index, score_readings  # noqa: E402

PATTERN = {
    "words": ["cat", "hat", "that"],
    "word_line_count": 1,
    "lines": ["cat hat that", "That cat has a hat."],
}


class LineIndexTest(unittest.TestCase):
    def test_matches_ignoring_case_and_spacing(self):
        self.assertEqual(line_index(PATTERN, "  CAT hat   that "), 0)
        self.assertEqual(line_index(PATTERN, "that cat has a hat."), 1)
        self.assertIsNone(line_index(PATTERN, "Something else."))


class ScoreReadingsTest(unittest.TestCase):
    def test_every_word_on_a_word_line_counts_and_inserted_sounds_do_not(self):
        reading = ("cat hat that", analysis([("cat", 0.0), ("hat", 0.4), ("that", 0.1)], inserted=1))
        self.assertEqual(score_readings(PATTERN, [reading]), (2, 3))

    def test_sentence_lines_count_only_the_pattern_words(self):
        words = [("that", 0.0), ("cat", 0.2), ("has", 0.9), ("a", 0.9), ("hat.", 0.0)]
        reading = ("That cat has a hat.", analysis(words))
        self.assertEqual(score_readings(PATTERN, [reading]), (2, 3))

    def test_only_the_first_reading_of_a_line_counts(self):
        first = ("cat hat that", analysis([("cat", 0.9), ("hat", 0.9), ("that", 0.9)]))
        again = ("cat hat that", analysis([("cat", 0.0), ("hat", 0.0), ("that", 0.0)]))
        self.assertEqual(score_readings(PATTERN, [first, again]), (0, 3))

    def test_readings_of_other_sentences_are_ignored(self):
        stray = ("The quick brown fox.", analysis([("quick", 0.0)]))
        self.assertEqual(score_readings(PATTERN, [stray]), (0, 0))

    def test_cutoff_matches_the_green_word_badge(self):
        reading = ("cat hat that", analysis([("cat", 0.149), ("hat", 0.15), ("that", None)]))
        self.assertEqual(score_readings(PATTERN, [reading]), (1, 3))


class MasteryTest(unittest.TestCase):
    def test_eighty_percent_is_mastered(self):
        self.assertTrue(is_mastered(8, 10))
        self.assertFalse(is_mastered(7, 10))
        self.assertFalse(is_mastered(0, 0))
        self.assertFalse(is_mastered(None, None))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to make sure they fail**

Run: `cd backend && PYTHONUTF8=1 /c/Users/bruce/Coding/word-wiz-ai/backend/venv/Scripts/python.exe -m unittest tests.test_phonics_scoring`
Expected: ERROR, `ModuleNotFoundError: No module named 'core.phonics_scoring'`.

- [ ] **Step 3: Write the scorer**

Create `backend/core/phonics_scoring.py`:

```python
"""Score a phonics pattern session from its saved readings.

Only the words that practise the pattern count. On a word line that is every
word. On a sentence line it is the words on the pattern's word list. Only
the first reading of each line counts, because the mic stays available after
a reading and reading a line again shouldn't move the score.
"""

import re

from core.guest_limits import normalize_sentence

# The same cutoff that turns a word badge green (frontend WordBadge.tsx), so
# the teacher's score matches the green and red words the child saw.
CORRECT_PER = 0.15
# Share of the pattern's words read right that counts as mastered.
MASTERY = 0.8

_NOT_WORD = re.compile(r"[^a-z']")


def normalize_word(word: str) -> str:
    return _NOT_WORD.sub("", word.lower().replace("’", "'"))


def line_index(pattern: dict, sentence: str) -> int | None:
    """Which of the pattern's lines `sentence` is, ignoring case and spacing."""
    target = normalize_sentence(sentence)
    for i, line in enumerate(pattern["lines"]):
        if normalize_sentence(line) == target:
            return i
    return None


def _word_scores(phoneme_analysis: dict | None) -> list[tuple[str, float]]:
    """(expected word, per) for each expected word in one saved reading."""
    frame = (phoneme_analysis or {}).get("pronunciation_dataframe") or {}
    words = frame.get("ground_truth_word") or {}
    pers = frame.get("per") or {}
    scored = []
    for row, word in words.items():
        if not word:
            continue  # an inserted sound, not one of the words on the line
        per = pers.get(row)
        scored.append((word, 1.0 if per is None else float(per)))
    return scored


def score_readings(pattern: dict, readings: list[tuple[str, dict]]) -> tuple[int, int]:
    """(pattern words read right, pattern words) over (sentence, analysis) in reading order."""
    pattern_words = {normalize_word(word) for word in pattern["words"]}
    seen: set[int] = set()
    correct = total = 0
    for sentence, phoneme_analysis in readings:
        index = line_index(pattern, sentence)
        if index is None or index in seen:
            continue
        seen.add(index)
        on_word_line = index < pattern["word_line_count"]
        for word, per in _word_scores(phoneme_analysis):
            if not on_word_line and normalize_word(word) not in pattern_words:
                continue
            total += 1
            if per < CORRECT_PER:
                correct += 1
    return correct, total


def is_mastered(words_correct: int | None, words_total: int | None) -> bool:
    return bool(words_total) and words_correct / words_total >= MASTERY
```

- [ ] **Step 4: Run the tests**

Run: `cd backend && PYTHONUTF8=1 /c/Users/bruce/Coding/word-wiz-ai/backend/venv/Scripts/python.exe -m unittest tests.test_phonics_scoring`
Expected: `OK` (7 tests).

- [ ] **Step 5: Commit**

```bash
git add backend/core/phonics_scoring.py backend/tests/test_phonics_scoring.py
git commit -m "$(cat <<'EOF'
Score a pattern session on the pattern's own words

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: Starting, resuming and finishing pattern sessions

**Files:**
- Create: `backend/crud/phonics_sessions.py`
- Test: `backend/tests/test_phonics_sessions.py`

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_phonics_sessions.py`:

```python
"""Tests for crud/phonics_sessions.py.

Run from backend/:  python -m unittest tests.test_phonics_sessions
"""

import unittest

from tests.phonics_helpers import add_reading, make_db, make_user

from core.phonics_data import get_pattern  # noqa: E402
from crud.phonics_sessions import (  # noqa: E402
    finish_pattern_session,
    get_phonics_activity,
    start_pattern_session,
)
from models import Activity  # noqa: E402

AT = get_pattern("at-family")


class PhonicsSessionsTest(unittest.TestCase):
    def setUp(self):
        self.db = make_db()()
        self.addCleanup(self.db.close)
        self.child = make_user(self.db, "Maya")

    def start(self, slug="at-family"):
        return start_pattern_session(self.db, self.child.id, slug)

    def test_activity_is_made_once(self):
        first = get_phonics_activity(self.db)
        self.assertEqual(get_phonics_activity(self.db).id, first.id)
        self.assertEqual(self.db.query(Activity).count(), 1)
        self.assertEqual(first.activity_type, "phonics-pattern")

    def test_start_resumes_an_unfinished_session_of_the_same_pattern(self):
        first = self.start()
        self.assertEqual(first.pattern_slug, "at-family")
        self.assertEqual(self.start().id, first.id)
        self.assertNotEqual(self.start("an-family").id, first.id)

    def test_start_after_finishing_makes_a_new_session(self):
        first = self.start()
        finish_pattern_session(self.db, first)
        self.assertNotEqual(self.start().id, first.id)

    def test_finish_scores_marks_complete_and_only_runs_once(self):
        session = self.start()
        add_reading(self.db, session, AT["lines"][0], per=0.0)  # 5 words right
        add_reading(self.db, session, AT["lines"][1], per=0.5)  # 5 words wrong
        result = finish_pattern_session(self.db, session)
        self.assertEqual(result, {
            "words_correct": 5,
            "words_total": 10,
            "mastered": False,
            "pattern_name": "-at Word Family",
        })
        self.assertEqual(session.is_completed, 1)

        add_reading(self.db, session, AT["lines"][2], per=0.0)
        self.assertEqual(finish_pattern_session(self.db, session)["words_total"], 10)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to make sure they fail**

Run: `cd backend && PYTHONUTF8=1 /c/Users/bruce/Coding/word-wiz-ai/backend/venv/Scripts/python.exe -m unittest tests.test_phonics_sessions`
Expected: ERROR, `ModuleNotFoundError: No module named 'crud.phonics_sessions'`.

- [ ] **Step 3: Write the crud module**

Create `backend/crud/phonics_sessions.py`:

```python
"""Starting, resuming and finishing phonics pattern sessions."""

from datetime import datetime, timezone

from core.phonics_data import PHONICS_ACTIVITY_TYPE, get_pattern
from core.phonics_scoring import is_mastered, score_readings
from models import Activity, FeedbackEntry, PatternSession, Session
from sqlalchemy.orm import Session as DBSession


def get_phonics_activity(db: DBSession) -> Activity:
    """The one activity every pattern session belongs to, made on first use.

    Making it here means no database needs seeding before the feature works.
    """
    activity = (
        db.query(Activity)
        .filter(Activity.activity_type == PHONICS_ACTIVITY_TYPE)
        .order_by(Activity.id)
        .first()
    )
    if activity is None:
        activity = Activity(
            title="Phonics path",
            description="Practice one phonics pattern at a time, from short a word families to vowel teams.",
            emoji_icon="Blocks",
            activity_type=PHONICS_ACTIVITY_TYPE,
            activity_settings={},
        )
        db.add(activity)
        db.commit()
        db.refresh(activity)
    return activity


def start_pattern_session(db: DBSession, user_id: int, slug: str) -> Session:
    """Resume the user's newest unfinished session for the pattern, or start one.

    The caller checks that the pattern exists.
    """
    existing = (
        db.query(Session)
        .join(PatternSession, PatternSession.session_id == Session.id)
        .filter(
            Session.user_id == user_id,
            Session.is_completed == 0,
            PatternSession.pattern_slug == slug,
        )
        .order_by(Session.created_at.desc(), Session.id.desc())
        .first()
    )
    if existing is not None:
        return existing

    session = Session(user_id=user_id, activity_id=get_phonics_activity(db).id)
    session.pattern = PatternSession(pattern_slug=slug)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def finish_pattern_session(db: DBSession, session: Session) -> dict:
    """Score the session, mark it complete and return the result.

    Safe to call again (if the last line is read twice): a finished session
    keeps its first score.
    """
    row = session.pattern
    pattern = get_pattern(row.pattern_slug)
    if row.completed_at is None:
        entries = (
            db.query(FeedbackEntry)
            .filter(FeedbackEntry.session_id == session.id)
            .order_by(FeedbackEntry.created_at.asc(), FeedbackEntry.id.asc())
            .all()
        )
        correct, total = score_readings(
            pattern, [(entry.sentence or "", entry.phoneme_analysis) for entry in entries]
        )
        row.words_correct = correct
        row.words_total = total
        row.completed_at = datetime.now(timezone.utc)
        session.is_completed = 1
        db.commit()
    return {
        "words_correct": row.words_correct,
        "words_total": row.words_total,
        "mastered": is_mastered(row.words_correct, row.words_total),
        "pattern_name": pattern["display_name"],
    }
```

- [ ] **Step 4: Run the tests**

Run: `cd backend && PYTHONUTF8=1 /c/Users/bruce/Coding/word-wiz-ai/backend/venv/Scripts/python.exe -m unittest tests.test_phonics_sessions`
Expected: `OK` (4 tests).

- [ ] **Step 5: Commit**

```bash
git add backend/crud/phonics_sessions.py backend/tests/test_phonics_sessions.py
git commit -m "$(cat <<'EOF'
Start, resume and finish phonics pattern sessions

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 5: The pattern mode and the `session_complete` event

**Files:**
- Create: `backend/core/modes/phonics_pattern.py`
- Modify: `backend/routers/handlers/audio_processing_handler.py`, `backend/routers/ai.py`
- Test: `backend/tests/test_phonics_mode.py`

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_phonics_mode.py`:

```python
"""Tests for the phonics pattern mode and its end of the audio stream.

Run from backend/:  python -m unittest tests.test_phonics_mode

The stream test stubs audio loading, the model and the audio cache, so it
needs no recording, model or API keys.
"""

import asyncio
import json
import types
import unittest
from unittest import mock

from tests.phonics_helpers import make_db, make_user

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from fastapi import HTTPException  # noqa: E402

from core.modes.phonics_pattern import PhonicsPatternPractice, phonics_mode_for  # noqa: E402
from core.phonics_data import get_pattern  # noqa: E402
from crud.phonics_sessions import start_pattern_session  # noqa: E402
from routers.handlers import audio_processing_handler as handler  # noqa: E402

AT = get_pattern("at-family")


def next_for(sentence, readings_so_far=0):
    session = types.SimpleNamespace(feedback_entries=[object()] * readings_so_far)
    mode = PhonicsPatternPractice(AT)
    return asyncio.run(mode.get_next_sentence(sentence, None, None, session))


class ModeTest(unittest.TestCase):
    def test_gives_the_next_line(self):
        self.assertEqual(
            next_for(AT["lines"][0]),
            {"sentence": AT["lines"][1], "line_index": 1, "line_count": 7},
        )

    def test_reading_a_line_again_does_not_skip_ahead(self):
        self.assertEqual(next_for(AT["lines"][0], readings_so_far=3)["sentence"], AT["lines"][1])

    def test_the_last_line_ends_the_session(self):
        self.assertEqual(
            next_for(AT["lines"][-1], readings_so_far=6),
            {"session_complete": True, "line_index": 6, "line_count": 7},
        )

    def test_an_unknown_sentence_falls_back_to_counting(self):
        self.assertEqual(next_for("Something else.", readings_so_far=2)["sentence"], AT["lines"][3])

    def test_a_missing_pattern_is_a_404(self):
        with self.assertRaises(HTTPException) as caught:
            phonics_mode_for(types.SimpleNamespace(pattern_slug="gone-family"))
        self.assertEqual(caught.exception.status_code, 404)


class FakeAssistant:
    """Scores every word of the sentence at `per`, with no model."""

    def __init__(self, per=0.0):
        self.per = per

    async def process_audio(self, sentence, audio, verbose=False):
        words = [word.strip(".,!?").lower() for word in sentence.split()]
        df = pd.DataFrame([
            {"ground_truth_word": word, "predicted_word": word, "per": self.per,
             "ground_truth_phonemes": ["k"], "predicted_phonemes": ["k"],
             "missed": [], "added": [], "substituted": []}
            for word in words
        ])
        return df, {"word": words[0], "per": self.per}, {"most_common_errors": []}, {"sentence_per": self.per}

    def feedback_to_audio(self, text, ssml=None):
        return {"data": "UklGRg==", "filename": "feedback.wav", "mimetype": "audio/wav"}


class StreamTest(unittest.TestCase):
    def setUp(self):
        async def fake_load(*args, **kwargs):
            return np.ones(16000, dtype="float32"), "cache-id"

        for target, value in [
            ("load_and_preprocess_audio_bytes", fake_load),
            ("check_speech_activity", lambda audio, quality: None),
            ("audio_cache", mock.Mock()),
        ]:
            patcher = mock.patch.object(handler, target, value)
            patcher.start()
            self.addCleanup(patcher.stop)

        self.db = make_db()()
        self.addCleanup(self.db.close)
        self.child = make_user(self.db, "Maya")
        self.session = start_pattern_session(self.db, self.child.id, "at-family")

    def read(self, line):
        async def go():
            return [chunk async for chunk in handler.analyze_audio_file_event_stream(
                phoneme_assistant=FakeAssistant(),
                activity_object=PhonicsPatternPractice(AT),
                audio_bytes=b"x",
                audio_filename="r.wav",
                audio_content_type="audio/wav",
                attempted_sentence=line,
                db=self.db,
                current_user=self.child,
                session=self.session,
            )]
        chunks = asyncio.run(go())
        events = [json.loads(l[6:]) for c in chunks for l in c.splitlines() if l.startswith("data: ")]
        return {event["type"]: event for event in events}

    def test_reads_through_to_the_finish(self):
        for i, line in enumerate(AT["lines"][:-1]):
            events = self.read(line)
            self.assertNotIn("error", events)
            self.assertNotIn("session_complete", events)
            self.assertEqual(
                events["next_sentence"]["data"],
                {"sentence": AT["lines"][i + 1], "line_index": i + 1, "line_count": 7},
            )

        events = self.read(AT["lines"][-1])
        self.assertNotIn("next_sentence", events)
        result = events["session_complete"]["data"]
        self.assertTrue(result["mastered"])
        self.assertEqual(result["words_correct"], result["words_total"])
        self.assertGreater(result["words_total"], len(AT["words"]))
        self.db.refresh(self.session)
        self.assertEqual(self.session.is_completed, 1)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to make sure they fail**

Run: `cd backend && PYTHONUTF8=1 /c/Users/bruce/Coding/word-wiz-ai/backend/venv/Scripts/python.exe -m unittest tests.test_phonics_mode`
Expected: ERROR, `ModuleNotFoundError: No module named 'core.modes.phonics_pattern'`.

- [ ] **Step 3: Write the mode**

Create `backend/core/modes/phonics_pattern.py`:

```python
from typing_extensions import override

from core.modes.base_mode import BaseMode
from core.phonics_data import get_pattern
from core.phonics_scoring import line_index
from fastapi import HTTPException, status


class PhonicsPatternPractice(BaseMode):
    """One phonics pattern: its word list in short lines, then its sentences.

    The lines are fixed, so there is no GPT call. The line just read is found
    by matching the sentence, not by counting readings, because the child can
    read a line again before tapping Next.
    """

    def __init__(self, pattern: dict):
        self.pattern = pattern

    @override
    async def get_next_sentence(self, attempted_sentence, analysis, phoneme_assistant, session) -> dict:
        lines = self.pattern["lines"]
        index = line_index(self.pattern, attempted_sentence)
        if index is None:
            # Not one of this pattern's lines, which the app never sends.
            # Carry on by counting readings instead of failing the reading.
            index = min(len(session.feedback_entries), len(lines) - 1)
        if index >= len(lines) - 1:
            return {"session_complete": True, "line_index": index, "line_count": len(lines)}
        return {"sentence": lines[index + 1], "line_index": index + 1, "line_count": len(lines)}


def phonics_mode_for(session) -> PhonicsPatternPractice:
    """The mode for a pattern session, or a 404 if its pattern was removed."""
    pattern = get_pattern(session.pattern_slug) if session.pattern_slug else None
    if pattern is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This practice isn't available anymore.",
        )
    return PhonicsPatternPractice(pattern)
```

- [ ] **Step 4: Send `session_complete` from the stream**

In `backend/routers/handlers/audio_processing_handler.py`, add this import after the `from crud.feedback_entry import ...` line:

```python
from crud.phonics_sessions import finish_pattern_session
```

Then replace this block (inside `analyze_audio_file_event_stream`):

```python
                if task is gpt_task:
                    sentence_result = result

                    next_sentence_payload = {
                        "type": "next_sentence",
                        "data": {
                            "sentence": sentence_result.get("sentence", ""),
                        },
                    }
                    print("📤 Sending next_sentence payload (GPT)...")
                    yield f"data: {json.dumps(sanitize(next_sentence_payload))}\n\n"
                    await asyncio.sleep(0.01)
```

with:

```python
                if task is gpt_task:
                    sentence_result = result
                    # Pattern sessions end after their last line instead of
                    # getting another sentence (core/modes/phonics_pattern.py).
                    session_complete = bool(sentence_result.get("session_complete"))

                    if not session_complete:
                        next_sentence_data = {"sentence": sentence_result.get("sentence", "")}
                        # Pattern sessions also say which line this is.
                        for key in ("line_index", "line_count"):
                            if key in sentence_result:
                                next_sentence_data[key] = sentence_result[key]
                        next_sentence_payload = {"type": "next_sentence", "data": next_sentence_data}
                        print("📤 Sending next_sentence payload (GPT)...")
                        yield f"data: {json.dumps(sanitize(next_sentence_payload))}\n\n"
                        await asyncio.sleep(0.01)
```

And replace:

```python
                    create_feedback_entry(db, feedback_entry)

                else:
```

with:

```python
                    create_feedback_entry(db, feedback_entry)

                    if session_complete:
                        # Scored after saving, so this reading counts too.
                        complete_payload = {
                            "type": "session_complete",
                            "data": finish_pattern_session(db, session),
                        }
                        print("📤 Sending session_complete payload...")
                        yield f"data: {json.dumps(sanitize(complete_payload))}\n\n"
                        await asyncio.sleep(0.01)

                else:
```

- [ ] **Step 5: Route pattern sessions to the mode**

In `backend/routers/ai.py`, add after `from core.modes.choice_story import ChoiceStoryPractice`:

```python
from core.modes.phonics_pattern import phonics_mode_for
from core.phonics_data import PHONICS_ACTIVITY_TYPE
```

and in `get_activity_object`, replace:

```python
    elif activity_type == "story":
        story_name = session.activity.activity_settings.get("story_name", "")
        return StoryPractice(story_name)
    else:
```

with:

```python
    elif activity_type == "story":
        story_name = session.activity.activity_settings.get("story_name", "")
        return StoryPractice(story_name)
    elif activity_type == PHONICS_ACTIVITY_TYPE:
        return phonics_mode_for(session)
    else:
```

(`routers.ai` loads the phoneme model on import, so it isn't unit tested. Task 15's end-to-end run covers this branch.)

- [ ] **Step 6: Run the tests**

Run: `cd backend && PYTHONUTF8=1 /c/Users/bruce/Coding/word-wiz-ai/backend/venv/Scripts/python.exe -m unittest tests.test_phonics_mode tests.test_guest_router && PYTHONUTF8=1 /c/Users/bruce/Coding/word-wiz-ai/backend/venv/Scripts/python.exe -c "import ast; ast.parse(open('routers/ai.py', encoding='utf-8').read())"`
Expected: `OK` (6 + 16 tests), and the parse prints nothing.

- [ ] **Step 7: Commit**

```bash
git add backend/core/modes/phonics_pattern.py backend/routers/handlers/audio_processing_handler.py backend/routers/ai.py backend/tests/test_phonics_mode.py
git commit -m "$(cat <<'EOF'
Read a pattern's lines in order and score the session after the last one

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 6: Status, path and curriculum

**Files:**
- Create: `backend/crud/phonics_progress.py`
- Modify: `backend/tests/phonics_helpers.py`
- Test: `backend/tests/test_phonics_progress.py`

- [ ] **Step 1: Add a factory for finished sessions**

Append to `backend/tests/phonics_helpers.py`:

```python
def make_pattern_session(db, user, slug, correct=None, total=None, completed_at=None):
    """A pattern session, finished with the given score when completed_at is set."""
    from crud.phonics_sessions import get_phonics_activity
    from models import PatternSession, Session

    session = Session(
        user_id=user.id,
        activity_id=get_phonics_activity(db).id,
        is_completed=int(completed_at is not None),
    )
    session.pattern = PatternSession(
        pattern_slug=slug,
        words_correct=correct,
        words_total=total,
        completed_at=completed_at,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session
```

- [ ] **Step 2: Write the failing tests**

Create `backend/tests/test_phonics_progress.py`:

```python
"""Tests for crud/phonics_progress.py.

Run from backend/:  python -m unittest tests.test_phonics_progress
"""

import unittest
from datetime import datetime, timedelta

from tests.phonics_helpers import make_db, make_pattern_session, make_user

from crud.phonics_progress import (  # noqa: E402
    IN_PROGRESS,
    MASTERED,
    NEEDS_PRACTICE,
    PatternStatus,
    curriculum,
    pattern_statuses,
    phonics_path,
)

DAY = datetime(2026, 10, 1)


class StatusTest(unittest.TestCase):
    def setUp(self):
        self.db = make_db()()
        self.addCleanup(self.db.close)
        self.maya = make_user(self.db, "Maya")
        self.leo = make_user(self.db, "Leo")

    def status(self, user, slug="at-family"):
        return pattern_statuses(self.db, [user.id])[user.id].get(slug)

    def test_untouched_patterns_are_absent(self):
        self.assertEqual(pattern_statuses(self.db, [self.maya.id]), {self.maya.id: {}})

    def test_an_unfinished_session_is_in_progress(self):
        make_pattern_session(self.db, self.maya, "at-family")
        self.assertEqual(self.status(self.maya).status, IN_PROGRESS)

    def test_the_latest_finished_session_decides(self):
        make_pattern_session(self.db, self.maya, "at-family", 9, 10, DAY)
        make_pattern_session(self.db, self.maya, "at-family", 5, 10, DAY + timedelta(days=1))
        status = self.status(self.maya)
        self.assertEqual((status.status, status.words_correct, status.tries), (NEEDS_PRACTICE, 5, 2))

    def test_a_new_unfinished_try_keeps_the_finished_status(self):
        make_pattern_session(self.db, self.maya, "at-family", 8, 10, DAY)
        make_pattern_session(self.db, self.maya, "at-family")
        status = self.status(self.maya)
        self.assertEqual((status.status, status.tries), (MASTERED, 1))

    def test_statuses_are_kept_per_child(self):
        make_pattern_session(self.db, self.maya, "at-family", 8, 10, DAY)
        both = pattern_statuses(self.db, [self.maya.id, self.leo.id])
        self.assertEqual(set(both[self.maya.id]), {"at-family"})
        self.assertEqual(both[self.leo.id], {})


class PathTest(unittest.TestCase):
    def test_next_is_the_first_pattern_not_mastered(self):
        self.assertEqual(phonics_path({})["next_slug"], "at-family")
        path = phonics_path({"at-family": PatternStatus(status=MASTERED, words_correct=9, words_total=10, tries=1)})
        self.assertEqual(path["next_slug"], "an-family")
        first_unit = path["units"][0]
        self.assertEqual(first_unit["mastered_count"], 1)
        self.assertEqual(first_unit["patterns"][0], {
            "slug": "at-family", "name": "-at Word Family", "status": MASTERED,
            "words_correct": 9, "words_total": 10, "tries": 1,
        })
        self.assertEqual(first_unit["patterns"][1]["status"], "not_started")

    def test_curriculum_lists_every_unit_with_names(self):
        units = curriculum()["units"]
        self.assertEqual(len(units), 18)
        self.assertEqual(units[5]["patterns"][0], {"slug": "sh-digraph", "name": "SH Digraph"})


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the tests to make sure they fail**

Run: `cd backend && PYTHONUTF8=1 /c/Users/bruce/Coding/word-wiz-ai/backend/venv/Scripts/python.exe -m unittest tests.test_phonics_progress`
Expected: ERROR, `ModuleNotFoundError: No module named 'crud.phonics_progress'`.

- [ ] **Step 4: Write the module**

Create `backend/crud/phonics_progress.py`:

```python
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
```

- [ ] **Step 5: Run the tests**

Run: `cd backend && PYTHONUTF8=1 /c/Users/bruce/Coding/word-wiz-ai/backend/venv/Scripts/python.exe -m unittest tests.test_phonics_progress`
Expected: `OK` (7 tests).

- [ ] **Step 6: Commit**

```bash
git add backend/crud/phonics_progress.py backend/tests/phonics_helpers.py backend/tests/test_phonics_progress.py
git commit -m "$(cat <<'EOF'
Work out each child's status on each pattern from their sessions

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 7: Teacher assignment endpoints

**Files:**
- Create: `backend/schemas/phonics.py`, `backend/crud/assignment_crud.py`, `backend/routers/assignments.py`
- Modify: `backend/main.py`
- Test: `backend/tests/test_assignments_api.py`

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_assignments_api.py`:

```python
"""Tests for the teacher assignment routes (routers/assignments.py).

Run from backend/:  python -m unittest tests.test_assignments_api
"""

import unittest
from datetime import datetime

from tests.phonics_helpers import (
    join,
    make_class,
    make_client,
    make_db,
    make_pattern_session,
    make_user,
)

from models import Assignment, ClassMembership  # noqa: E402
from routers import assignments  # noqa: E402

DAY = datetime(2026, 10, 1)


class AssignmentsApiTest(unittest.TestCase):
    def setUp(self):
        SessionLocal = make_db()
        self.db = SessionLocal()
        self.addCleanup(self.db.close)
        self.teacher = make_user(self.db, "Ms Rivera")
        self.maya = make_user(self.db, "Maya")
        self.leo = make_user(self.db, "Leo")
        self.cls = make_class(self.db, self.teacher, self.maya, self.leo)
        self.as_user = make_client(SessionLocal, ("/classes", assignments.router))
        self.url = f"/classes/{self.cls.id}/assignments"

    def assign(self, slugs, student_ids=None, user=None):
        return self.as_user(user or self.teacher).post(
            self.url, json={"pattern_slugs": slugs, "student_ids": student_ids}
        )

    def listed(self):
        return self.as_user(self.teacher).get(self.url).json()

    def test_whole_class_assignment_lists_everyone_in_curriculum_order(self):
        r = self.assign(["an-family", "at-family"])
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual([a["pattern_slug"] for a in body], ["at-family", "an-family"])
        self.assertTrue(body[0]["whole_class"])
        self.assertEqual(body[0]["pattern_name"], "-at Word Family")
        self.assertEqual(body[0]["unit_title"], "Short a word families")
        self.assertEqual(body[0]["counts"]["not_started"], 2)
        self.assertEqual({s["full_name"] for s in body[0]["students"]}, {"Maya", "Leo"})

    def test_status_comes_from_sessions(self):
        make_pattern_session(self.db, self.maya, "at-family", 9, 10, DAY)
        body = self.assign(["at-family"]).json()
        maya = next(s for s in body[0]["students"] if s["full_name"] == "Maya")
        self.assertEqual((maya["status"], maya["words_correct"], maya["tries"]), ("mastered", 9, 1))
        self.assertEqual(
            body[0]["counts"],
            {"mastered": 1, "needs_practice": 0, "in_progress": 0, "not_started": 1},
        )

    def test_only_the_teacher_can_assign_or_view(self):
        self.assertEqual(self.assign(["at-family"], user=self.maya).status_code, 403)
        self.assertEqual(self.as_user(self.maya).get(self.url).status_code, 403)
        self.assertEqual(self.as_user(self.teacher).get("/classes/999/assignments").status_code, 404)

    def test_bad_requests_are_refused(self):
        outsider = make_user(self.db, "Sam")
        unknown = self.assign(["at-family", "zz-family"])
        self.assertEqual(unknown.status_code, 400)
        self.assertIn("zz-family", unknown.json()["detail"])
        self.assertEqual(self.assign(["at-family"], [outsider.id]).status_code, 400)
        self.assertEqual(self.assign(["at-family"], []).status_code, 400)
        self.assertEqual(self.assign([]).status_code, 400)
        self.assertEqual(self.listed(), [])

    def test_assigning_again_merges_into_one_assignment(self):
        self.assign(["at-family"], [self.maya.id])
        body = self.assign(["at-family"], [self.leo.id]).json()
        self.assertEqual(len(body), 1)
        self.assertFalse(body[0]["whole_class"])
        self.assertEqual({s["full_name"] for s in body[0]["students"]}, {"Maya", "Leo"})
        self.assertTrue(self.assign(["at-family"]).json()[0]["whole_class"])

    def test_whole_class_work_follows_membership(self):
        self.assign(["at-family"])
        ava = make_user(self.db, "Ava")
        join(self.db, self.cls, ava)
        self.db.query(ClassMembership).filter_by(student_id=self.leo.id).delete()
        self.db.commit()
        names = {s["full_name"] for s in self.listed()[0]["students"]}
        self.assertEqual(names, {"Maya", "Ava"})

    def test_delete(self):
        assignment_id = self.assign(["at-family"]).json()[0]["id"]
        other = make_class(self.db, self.teacher, name="Room 5")
        client = self.as_user(self.teacher)
        self.assertEqual(client.delete(f"/classes/{other.id}/assignments/{assignment_id}").status_code, 404)
        self.assertEqual(client.delete(f"{self.url}/{assignment_id}").status_code, 204)
        self.assertEqual(self.listed(), [])

    def test_a_removed_pattern_shows_as_unavailable(self):
        self.db.add(Assignment(class_id=self.cls.id, pattern_slug="gone-family", whole_class=True))
        self.db.commit()
        body = self.listed()
        self.assertEqual((body[0]["pattern_slug"], body[0]["pattern_name"]), ("gone-family", None))

    def test_class_grid_and_one_student_path(self):
        make_pattern_session(self.db, self.maya, "at-family", 9, 10, DAY)
        client = self.as_user(self.teacher)
        grid = client.get(f"/classes/{self.cls.id}/phonics-progress").json()
        self.assertEqual(len(grid["units"]), 18)
        self.assertEqual(
            {row["full_name"]: row["statuses"] for row in grid["students"]},
            {"Maya": {"at-family": "mastered"}, "Leo": {}},
        )
        path = client.get(f"/classes/{self.cls.id}/students/{self.maya.id}/phonics-path").json()
        self.assertEqual(path["next_slug"], "an-family")

        outsider = make_user(self.db, "Sam")
        self.assertEqual(
            client.get(f"/classes/{self.cls.id}/students/{outsider.id}/phonics-path").status_code, 404
        )
        self.assertEqual(
            self.as_user(self.maya).get(f"/classes/{self.cls.id}/phonics-progress").status_code, 403
        )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to make sure they fail**

Run: `cd backend && PYTHONUTF8=1 /c/Users/bruce/Coding/word-wiz-ai/backend/venv/Scripts/python.exe -m unittest tests.test_assignments_api`
Expected: ERROR, `ImportError: cannot import name 'assignments' from 'routers'`.

- [ ] **Step 3: Write the schemas**

Create `backend/schemas/phonics.py`:

```python
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
```

- [ ] **Step 4: Write the assignment crud**

Create `backend/crud/assignment_crud.py`:

```python
"""Teacher assignments of phonics patterns, and who has each one."""

from collections import Counter

from core.phonics_data import get_pattern, units
from crud.class_membership_crud import get_class_memberships
from crud.phonics_progress import PatternStatus, curriculum, pattern_statuses, status_fields
from models import Assignment, AssignmentStudent, Class, ClassMembership
from sqlalchemy.orm import Session as DBSession

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
        if student_ids is not None and not assignment.whole_class:
            have = {row.student_id for row in assignment.students}
            for student_id in student_ids:
                if student_id not in have:
                    assignment.students.append(AssignmentStudent(student_id=student_id))
    db.commit()


def class_assignments(db: DBSession, class_id: int) -> list[dict]:
    """Every assignment in the class with each recipient's status, in curriculum order."""
    memberships = get_class_memberships(db, class_id)
    students = {m.student_id: m.student for m in memberships}
    statuses = pattern_statuses(db, list(students))
    titles = _unit_titles()
    assignments = db.query(Assignment).filter(Assignment.class_id == class_id).all()

    result = []
    for assignment in sorted(assignments, key=_curriculum_order):
        pattern = get_pattern(assignment.pattern_slug)
        if assignment.whole_class:
            recipients = list(students)
        else:
            recipients = [row.student_id for row in assignment.students if row.student_id in students]
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
```

- [ ] **Step 5: Write the router**

Create `backend/routers/assignments.py`:

```python
"""Teacher routes for assigning phonics patterns (mounted under /classes)."""

from auth.auth_handler import get_current_active_user
from core.phonics_data import get_pattern
from crud import assignment_crud, class_crud, class_membership_crud
from crud.phonics_progress import pattern_statuses, phonics_path
from database import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from models import Class, User
from schemas.phonics import AssignRequest, ClassAssignment, ClassPhonicsProgress, PhonicsPath
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
```

- [ ] **Step 6: Mount it**

In `backend/main.py`, replace

```python
from routers import ai, auth, google_auth, session, user, activities, feedback, health, classes, guest
```
with
```python
from routers import ai, auth, google_auth, session, user, activities, feedback, health, classes, guest, assignments
```

and replace

```python
app.include_router(classes.router, prefix="/classes")
```
with
```python
app.include_router(classes.router, prefix="/classes")
# Teacher assignments of phonics patterns (see routers/assignments.py)
app.include_router(assignments.router, prefix="/classes")
```

- [ ] **Step 7: Run the tests**

Run: `cd backend && PYTHONUTF8=1 /c/Users/bruce/Coding/word-wiz-ai/backend/venv/Scripts/python.exe -m unittest tests.test_assignments_api`
Expected: `OK` (9 tests).

- [ ] **Step 8: Commit**

```bash
git add backend/schemas/phonics.py backend/crud/assignment_crud.py backend/routers/assignments.py backend/main.py backend/tests/test_assignments_api.py
git commit -m "$(cat <<'EOF'
Let teachers assign phonics patterns and see each student's status

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 8: Student phonics endpoints and session route changes

**Files:**
- Create: `backend/routers/phonics.py`
- Modify: `backend/routers/session.py`, `backend/routers/activities.py`, `backend/main.py`
- Test: `backend/tests/test_phonics_api.py`

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_phonics_api.py`:

```python
"""Tests for routers/phonics.py and the phonics parts of the session routes.

Run from backend/:  python -m unittest tests.test_phonics_api
"""

import unittest
from datetime import datetime

from tests.phonics_helpers import (
    add_reading,
    join,
    make_class,
    make_client,
    make_db,
    make_pattern_session,
    make_user,
)

from core.phonics_data import get_pattern  # noqa: E402
from crud.phonics_sessions import get_phonics_activity  # noqa: E402
from models import Activity, Assignment, AssignmentStudent, Session  # noqa: E402
from routers import activities, phonics  # noqa: E402
from routers import session as session_router  # noqa: E402

AT = get_pattern("at-family")


class PhonicsApiTest(unittest.TestCase):
    def setUp(self):
        SessionLocal = make_db()
        self.db = SessionLocal()
        self.addCleanup(self.db.close)
        self.maya = make_user(self.db, "Maya")
        self.as_user = make_client(
            SessionLocal,
            ("/phonics", phonics.router),
            ("/session", session_router.router),
            ("/activities", activities.router),
        )
        self.client = self.as_user(self.maya)

    def start(self, slug="at-family"):
        return self.client.post("/phonics/sessions", json={"pattern_slug": slug})

    def test_start_creates_then_resumes(self):
        r = self.start()
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual((body["pattern_slug"], body["pattern_name"]), ("at-family", "-at Word Family"))
        self.assertEqual(self.start().json()["id"], body["id"])
        self.assertEqual(self.start("zz-family").status_code, 404)

    def test_path_points_at_the_first_pattern_not_mastered(self):
        self.assertEqual(self.client.get("/phonics/path").json()["next_slug"], "at-family")
        make_pattern_session(self.db, self.maya, "at-family", 10, 10, datetime(2026, 10, 1))
        path = self.client.get("/phonics/path").json()
        self.assertEqual(path["next_slug"], "an-family")
        self.assertEqual(path["units"][0]["patterns"][0]["status"], "mastered")

    def test_curriculum(self):
        units = self.client.get("/phonics/curriculum").json()["units"]
        self.assertEqual(len(units), 18)
        self.assertEqual(units[0]["patterns"][0], {"slug": "at-family", "name": "-at Word Family"})

    def test_assignments_reach_the_right_children(self):
        teacher = make_user(self.db, "Ms Rivera")
        leo = make_user(self.db, "Leo")
        cls = make_class(self.db, teacher, self.maya, leo)
        self.db.add(Assignment(class_id=cls.id, pattern_slug="sh-digraph", whole_class=True))
        group = Assignment(class_id=cls.id, pattern_slug="at-family", whole_class=False)
        group.students.append(AssignmentStudent(student_id=leo.id))
        self.db.add(group)
        self.db.add(Assignment(class_id=cls.id, pattern_slug="gone-family", whole_class=True))
        self.db.commit()

        mine = self.client.get("/phonics/assignments").json()
        self.assertEqual([a["pattern_slug"] for a in mine], ["sh-digraph"])
        self.assertEqual((mine[0]["class_name"], mine[0]["status"]), ("Room 4", "not_started"))
        self.assertEqual(mine[0]["unit_title"], "Digraphs")

        leos = self.as_user(leo).get("/phonics/assignments").json()
        self.assertEqual([a["pattern_slug"] for a in leos], ["at-family", "sh-digraph"])

        ava = make_user(self.db, "Ava")
        join(self.db, cls, ava)
        avas = self.as_user(ava).get("/phonics/assignments").json()
        self.assertEqual([a["pattern_slug"] for a in avas], ["sh-digraph"])

    def test_the_phonics_activity_is_hidden_and_needs_a_pattern(self):
        hidden = get_phonics_activity(self.db)
        self.db.add(Activity(title="Free", description="d", activity_type="unlimited", activity_settings={}))
        self.db.commit()
        listed = [a["activity_type"] for a in self.client.get("/activities/").json()]
        self.assertEqual(listed, ["unlimited"])
        self.assertEqual(self.client.post("/session/", json={"activity_id": hidden.id}).status_code, 400)

    def test_current_data_gives_the_line_to_read(self):
        session_id = self.start().json()["id"]
        state = self.client.get(f"/session/{session_id}/current-data").json()
        self.assertEqual(state["type"], "activity-settings")
        self.assertEqual(state["data"]["first_sentence"], AT["lines"][0])
        self.assertEqual((state["line_index"], state["line_count"]), (0, 7))

        session = self.db.get(Session, session_id)
        add_reading(self.db, session, AT["lines"][0], next_sentence=AT["lines"][1])
        state = self.client.get(f"/session/{session_id}/current-data").json()
        self.assertEqual(state["type"], "full-feedback-state")
        self.assertEqual(state["data"]["gpt_response"]["sentence"], AT["lines"][1])
        self.assertEqual((state["line_index"], state["line_count"]), (1, 7))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to make sure they fail**

Run: `cd backend && PYTHONUTF8=1 /c/Users/bruce/Coding/word-wiz-ai/backend/venv/Scripts/python.exe -m unittest tests.test_phonics_api`
Expected: ERROR, `ImportError: cannot import name 'phonics' from 'routers'`.

- [ ] **Step 3: Write the student router**

Create `backend/routers/phonics.py`:

```python
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
```

- [ ] **Step 4: Hide the phonics activity from activity lists**

Replace `backend/routers/activities.py` `get_activities` body. Add the import line after `from auth.auth_handler import get_current_active_user`:

```python
from core.phonics_data import PHONICS_ACTIVITY_TYPE
```

and replace

```python
    activities = db.query(Activity).order_by(Activity.id).all()
```
with
```python
    # Every pattern session hangs off one hidden activity. Children reach
    # them through the phonics path, not the activity lists.
    activities = (
        db.query(Activity)
        .filter(Activity.activity_type != PHONICS_ACTIVITY_TYPE)
        .order_by(Activity.id)
        .all()
    )
```

- [ ] **Step 5: Teach the session routes about pattern sessions**

In `backend/routers/session.py`, add after `from auth.auth_handler import get_current_active_user`:

```python
from core.phonics_data import PHONICS_ACTIVITY_TYPE, get_pattern
from core.phonics_scoring import line_index
```

In `create_session`, replace

```python
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    # Create session
```
with
```python
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    if activity.activity_type == PHONICS_ACTIVITY_TYPE:
        # A pattern session needs its pattern; POST /phonics/sessions makes them.
        raise HTTPException(status_code=400, detail="Start phonics practice from the Phonics path.")
    # Create session
```

Replace the end of `get_current_data_for_session`, from

```python
    # Retrieve feedback entries if they exist
    feedback = getattr(db_session, "feedback_entries", [])
```
to the end of the file, with:

```python
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

    # Retrieve the latest feedback entry based on `created_at`. The id breaks
    # ties, since SQLite stores whole seconds.
    latest_feedback = max(
        feedback, key=lambda f: (getattr(f, "created_at", None), f.id)
    )

    # Return the latest feedback in a structured format
    response = {
        "type": "full-feedback-state",
        "data": latest_feedback,
    }
    if pattern is not None:
        current = (latest_feedback.gpt_response or {}).get("sentence", "")
        response["line_index"] = line_index(pattern, current) or 0
        response["line_count"] = len(pattern["lines"])
    return response
```

- [ ] **Step 6: Mount the router**

In `backend/main.py`, change the routers import to end with `classes, guest, assignments, phonics` and add after the assignments `include_router` line:

```python
app.include_router(phonics.router, prefix="/phonics")
```

- [ ] **Step 7: Run every backend test touched so far**

Run: `cd backend && PYTHONUTF8=1 /c/Users/bruce/Coding/word-wiz-ai/backend/venv/Scripts/python.exe -m unittest tests.test_phonics_api tests.test_assignments_api tests.test_phonics_progress tests.test_phonics_mode tests.test_phonics_sessions tests.test_phonics_scoring tests.test_phonics_models tests.test_phonics_data tests.test_guest_router`
Expected: `OK` (6 + 9 + 7 + 6 + 4 + 7 + 5 + 8 + 16 = 68 tests).

- [ ] **Step 8: Commit**

```bash
git add backend/routers/phonics.py backend/routers/session.py backend/routers/activities.py backend/main.py backend/tests/test_phonics_api.py
git commit -m "$(cat <<'EOF'
Serve the phonics path, a child's assignments and pattern sessions

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 9: Seed a teacher and class for local testing

**Files:**
- Modify: `backend/dev_server.py`

- [ ] **Step 1: Add the constants and docstring line**

In `backend/dev_server.py`, replace

```python
Progress charts all have something to show. Log in with DEMO_EMAIL and
DEMO_PASSWORD below. They only exist inside dev/dev.db.
```
with
```python
Progress charts all have something to show. Log in with DEMO_EMAIL and
DEMO_PASSWORD below. A teacher account (TEACHER_EMAIL) owns a class with the
demo child in it, for trying phonics assignments. Both only exist inside
dev/dev.db.
```

and after `DEMO_NAME = "Maya Okafor"` add:

```python

TEACHER_EMAIL = "teacher@wordwiz.test"
TEACHER_PASSWORD = "wordwiz-dev"
TEACHER_NAME = "Ms. Rivera"
DEV_CLASS_NAME = "Room 4"
DEV_CLASS_CODE = "DEVRM4"
```

- [ ] **Step 2: Seed them**

In `seed()`, replace

```python
    from models import Activity, FeedbackEntry, Session, User
```
with
```python
    from models import Activity, Class, ClassMembership, FeedbackEntry, Session, User
```

and replace

```python
            db.commit()
            print(f"Seeded demo account {DEMO_EMAIL} with {len(HISTORY)} sessions")
    finally:
```
with
```python
            db.commit()
            print(f"Seeded demo account {DEMO_EMAIL} with {len(HISTORY)} sessions")

        if db.query(User).filter(User.email == TEACHER_EMAIL).first() is None:
            teacher = create_user(db, User(
                username="teacher",
                email=TEACHER_EMAIL,
                full_name=TEACHER_NAME,
                hashed_password=get_password_hash(TEACHER_PASSWORD),
            ))
            demo = db.query(User).filter(User.email == DEMO_EMAIL).one()
            room = Class(name=DEV_CLASS_NAME, join_code=DEV_CLASS_CODE, teacher_id=teacher.id)
            db.add(room)
            db.flush()
            db.add(ClassMembership(class_id=room.id, student_id=demo.id))
            db.commit()
            print(f"Seeded teacher account {TEACHER_EMAIL} with class {DEV_CLASS_NAME} ({DEV_CLASS_CODE})")
    finally:
```

- [ ] **Step 3: Check the seed against a fresh dev database**

The worktree has no `backend/dev/dev.db` (it's gitignored), so this creates one there and never touches the main checkout's:

Run:
```bash
cd backend && PYTHONUTF8=1 /c/Users/bruce/Coding/word-wiz-ai/backend/venv/Scripts/python.exe -c "import dev_server as d; d.configure_environment(); d.seed(); d.seed()"
```
Expected: the demo and teacher "Seeded ..." lines print once (the second `seed()` adds nothing), with no traceback.

- [ ] **Step 4: Commit**

```bash
git add backend/dev_server.py
git commit -m "$(cat <<'EOF'
Seed a teacher with the demo child in a class on the dev server

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 10: Frontend API, helpers and hooks

**Files:**
- Modify: `frontend/src/api.ts`
- Create: `frontend/src/lib/phonics.ts`, `frontend/src/lib/phonics.test.ts`, `frontend/src/hooks/usePhonics.ts`

- [ ] **Step 1: Link node_modules into the worktree**

Run (PowerShell, from the worktree root):
```powershell
New-Item -ItemType Junction -Path frontend\node_modules -Target C:\Users\bruce\Coding\word-wiz-ai\frontend\node_modules
```

- [ ] **Step 2: Write the failing helper tests**

Create `frontend/src/lib/phonics.test.ts`:

```ts
import { test } from "node:test";
import assert from "node:assert/strict";
import {
  assignSummary,
  finishMessage,
  lineLabel,
  orderAssignments,
  unitTone,
  type PatternStatus,
} from "./phonics.ts";

test("a mastered session celebrates and gives the count", () => {
  assert.deepEqual(
    finishMessage({ words_correct: 12, words_total: 14, mastered: true, pattern_name: "-at Word Family" }),
    { title: "You've got it!", detail: "You read 12 of 14 words right." },
  );
});

test("a session under the mark stays encouraging and never says needs practice", () => {
  const message = finishMessage({ words_correct: 6, words_total: 14, mastered: false, pattern_name: "x" });
  assert.equal(message.title, "Nice reading!");
  assert.equal(message.detail, "You read 6 of 14 words right. Let's practice these again soon.");
  assert.doesNotMatch(`${message.title} ${message.detail}`, /needs practice/i);
});

test("a session with no scored words still finishes kindly", () => {
  const message = finishMessage({ words_correct: 0, words_total: 0, mastered: false, pattern_name: "x" });
  assert.match(message.detail, /^You read every line\./);
});

test("open assignments come before mastered ones, keeping their order", () => {
  const items: { id: number; status: PatternStatus }[] = [
    { id: 1, status: "mastered" },
    { id: 2, status: "not_started" },
    { id: 3, status: "needs_practice" },
  ];
  assert.deepEqual(orderAssignments(items).map((item) => item.id), [2, 3, 1]);
});

test("grid cells shade by how much of the unit is mastered", () => {
  assert.equal(unitTone(0, 7), "bg-muted text-muted-foreground");
  assert.equal(unitTone(3, 7), "bg-pastel-yellow text-pastel-yellow-foreground");
  assert.equal(unitTone(7, 7), "bg-pastel-mint text-pastel-mint-foreground");
});

test("labels", () => {
  assert.equal(lineLabel(2, 7), "Line 3 of 7");
  assert.equal(assignSummary(1, 1), "Assign 1 pattern to 1 student");
  assert.equal(assignSummary(7, 22), "Assign 7 patterns to 22 students");
});
```

- [ ] **Step 3: Run it to make sure it fails**

Run: `cd frontend && npm test`
Expected: FAIL, `Cannot find module ... phonics.ts`.

- [ ] **Step 4: Write the helpers**

Create `frontend/src/lib/phonics.ts`:

```ts
// Wording and colours for the phonics path and teacher assignments. No
// imports, so the node test runner can load it directly.

export type PatternStatus =
  | "not_started"
  | "in_progress"
  | "mastered"
  | "needs_practice";

// What teachers see.
export const STATUS_LABEL: Record<PatternStatus, string> = {
  not_started: "Not started",
  in_progress: "In progress",
  mastered: "Mastered",
  needs_practice: "Needs practice",
};

// What children (and the parents beside them) see. Gentler, and never
// "Needs practice".
export const STUDENT_LABEL: Record<PatternStatus, string> = {
  not_started: "New",
  in_progress: "Keep going",
  mastered: "Got it",
  needs_practice: "Try again",
};

// Pastel pairs, because they have dark-mode values (see classes/accuracy.ts).
export const STATUS_TONE: Record<PatternStatus, string> = {
  mastered: "bg-pastel-mint text-pastel-mint-foreground",
  needs_practice: "bg-pastel-yellow text-pastel-yellow-foreground",
  in_progress: "bg-pastel-blue text-pastel-blue-foreground",
  not_started: "bg-muted text-muted-foreground",
};

// The `session_complete` event's data (backend crud/phonics_sessions.py).
export interface SessionResult {
  words_correct: number | null;
  words_total: number | null;
  mastered: boolean;
  pattern_name: string;
}

export function finishMessage(result: SessionResult): { title: string; detail: string } {
  const { words_correct: correct, words_total: total } = result;
  const count = total
    ? `You read ${correct ?? 0} of ${total} words right.`
    : "You read every line.";
  return {
    title: result.mastered ? "You've got it!" : "Nice reading!",
    detail: result.mastered ? count : `${count} Let's practice these again soon.`,
  };
}

// Open work first, in the order given (the API's curriculum order), then
// what's already mastered.
export function orderAssignments<T extends { status: PatternStatus }>(items: T[]): T[] {
  return [
    ...items.filter((item) => item.status !== "mastered"),
    ...items.filter((item) => item.status === "mastered"),
  ];
}

// A class grid cell's shade for how much of one unit a student has mastered.
export function unitTone(mastered: number, total: number): string {
  if (total === 0 || mastered === 0) return "bg-muted text-muted-foreground";
  if (mastered === total) return "bg-pastel-mint text-pastel-mint-foreground";
  return "bg-pastel-yellow text-pastel-yellow-foreground";
}

export function lineLabel(index: number, count: number): string {
  return `Line ${index + 1} of ${count}`;
}

export function assignSummary(patterns: number, students: number): string {
  const p = `${patterns} pattern${patterns === 1 ? "" : "s"}`;
  const s = `${students} student${students === 1 ? "" : "s"}`;
  return `Assign ${p} to ${s}`;
}
```

- [ ] **Step 5: Run the tests**

Run: `cd frontend && npm test`
Expected: all tests pass, including the 6 new ones.

- [ ] **Step 6: Add the API types and calls**

In `frontend/src/api.ts`:

Add after `import axios from "axios";`:

```ts
import type { PatternStatus } from "@/lib/phonics";
```

In the `Session` interface, add after `created_at: string;`:

```ts
  // Phonics pattern sessions only (backend models/pattern_session.py).
  pattern_slug?: string | null;
  pattern_name?: string | null;
```

After the `StudentInsights` interface add:

```ts
interface PatternRef {
  slug: string;
  name: string;
}

interface CurriculumUnit {
  id: string;
  title: string;
  grade: string;
  patterns: PatternRef[];
}

interface Curriculum {
  units: CurriculumUnit[];
}

interface PatternProgress extends PatternRef {
  status: PatternStatus;
  words_correct: number | null;
  words_total: number | null;
  tries: number;
}

interface PathUnit {
  id: string;
  title: string;
  grade: string;
  mastered_count: number;
  patterns: PatternProgress[];
}

interface PhonicsPath {
  units: PathUnit[];
  next_slug: string | null;
}

interface StudentAssignment {
  id: number;
  class_id: number;
  class_name: string;
  pattern_slug: string;
  pattern_name: string;
  unit_title: string;
  status: PatternStatus;
  words_correct: number | null;
  words_total: number | null;
  tries: number;
}

interface AssignmentStudentStatus {
  id: number;
  full_name: string | null;
  status: PatternStatus;
  words_correct: number | null;
  words_total: number | null;
  tries: number;
}

interface ClassAssignment {
  id: number;
  pattern_slug: string;
  // Null when the pattern has been removed from the site's data.
  pattern_name: string | null;
  unit_title: string | null;
  whole_class: boolean;
  created_at: string | null;
  counts: Record<PatternStatus, number>;
  students: AssignmentStudentStatus[];
}

interface ClassPhonicsProgress {
  units: CurriculumUnit[];
  students: {
    id: number;
    full_name: string | null;
    // Only patterns the student has touched; the rest are not started.
    statuses: Partial<Record<string, PatternStatus>>;
  }[];
}
```

Before the `export {` block add:

```ts
// Phonics path and teacher assignments (backend routers/phonics.py and
// routers/assignments.py).
const getPhonicsPath = async (token: string): Promise<PhonicsPath> => {
  try {
    const response = await axios.get(`${API_URL}/phonics/path`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return response.data;
  } catch (error) {
    console.error("Fetch phonics path error:", error);
    throw error;
  }
};

const getCurriculum = async (token: string): Promise<Curriculum> => {
  try {
    const response = await axios.get(`${API_URL}/phonics/curriculum`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return response.data;
  } catch (error) {
    console.error("Fetch curriculum error:", error);
    throw error;
  }
};

const getMyAssignments = async (token: string): Promise<StudentAssignment[]> => {
  try {
    const response = await axios.get(`${API_URL}/phonics/assignments`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return response.data;
  } catch (error) {
    console.error("Fetch my assignments error:", error);
    throw error;
  }
};

const startPatternSession = async (token: string, patternSlug: string): Promise<Session> => {
  try {
    const response = await axios.post(
      `${API_URL}/phonics/sessions`,
      { pattern_slug: patternSlug },
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return response.data;
  } catch (error) {
    console.error("Start pattern session error:", error);
    throw error;
  }
};

const getClassAssignments = async (token: string, classId: number): Promise<ClassAssignment[]> => {
  try {
    const response = await axios.get(`${API_URL}/classes/${classId}/assignments`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return response.data;
  } catch (error) {
    console.error("Fetch class assignments error:", error);
    throw error;
  }
};

const assignPatterns = async (
  token: string,
  classId: number,
  patternSlugs: string[],
  studentIds: number[] | null
): Promise<ClassAssignment[]> => {
  try {
    const response = await axios.post(
      `${API_URL}/classes/${classId}/assignments`,
      { pattern_slugs: patternSlugs, student_ids: studentIds },
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return response.data;
  } catch (error) {
    console.error("Assign patterns error:", error);
    throw error;
  }
};

const deleteAssignment = async (token: string, classId: number, assignmentId: number): Promise<void> => {
  try {
    await axios.delete(`${API_URL}/classes/${classId}/assignments/${assignmentId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
  } catch (error) {
    console.error("Delete assignment error:", error);
    throw error;
  }
};

const getClassPhonicsProgress = async (token: string, classId: number): Promise<ClassPhonicsProgress> => {
  try {
    const response = await axios.get(`${API_URL}/classes/${classId}/phonics-progress`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return response.data;
  } catch (error) {
    console.error("Fetch class phonics progress error:", error);
    throw error;
  }
};

const getStudentPhonicsPath = async (
  token: string,
  classId: number,
  studentId: number
): Promise<PhonicsPath> => {
  try {
    const response = await axios.get(
      `${API_URL}/classes/${classId}/students/${studentId}/phonics-path`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return response.data;
  } catch (error) {
    console.error("Fetch student phonics path error:", error);
    throw error;
  }
};
```

Add to the `export {` list, after `getStudentInsights,`:

```ts
  getPhonicsPath,
  getCurriculum,
  getMyAssignments,
  startPatternSession,
  getClassAssignments,
  assignPatterns,
  deleteAssignment,
  getClassPhonicsProgress,
  getStudentPhonicsPath,
```

Add to the `export type {` list, after `StudentInsights,`:

```ts
  PatternRef,
  CurriculumUnit,
  Curriculum,
  PatternProgress,
  PathUnit,
  PhonicsPath,
  StudentAssignment,
  AssignmentStudentStatus,
  ClassAssignment,
  ClassPhonicsProgress,
```

- [ ] **Step 7: Write the hooks**

Create `frontend/src/hooks/usePhonics.ts`:

```ts
import { useContext, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AuthContext } from "@/contexts/AuthContext";
import {
  getMyAssignments,
  getPhonicsPath,
  startPatternSession,
  type PhonicsPath,
  type StudentAssignment,
} from "@/api";
import { showErrorToast } from "@/utils/errorHandling";

export function usePhonicsPath() {
  const { token } = useContext(AuthContext);
  const [path, setPath] = useState<PhonicsPath | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    getPhonicsPath(token)
      .then((data) => {
        if (!cancelled) setPath(data);
      })
      .catch((error: unknown) => {
        console.error("Failed to fetch phonics path:", error);
        if (!cancelled) setFailed(true);
      });
    return () => {
      cancelled = true;
    };
  }, [token]);

  return { path, failed };
}

// A failed request leaves the list empty: most children have no teacher, so
// a missing "From your teacher" section isn't worth an error.
export function useMyAssignments() {
  const { token } = useContext(AuthContext);
  const [assignments, setAssignments] = useState<StudentAssignment[] | null>(null);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    getMyAssignments(token)
      .then((data) => {
        if (!cancelled) setAssignments(data);
      })
      .catch((error: unknown) => {
        console.error("Failed to fetch assignments:", error);
        if (!cancelled) setAssignments([]);
      });
    return () => {
      cancelled = true;
    };
  }, [token]);

  return { assignments };
}

// Like useStartActivity: the tapped pattern shows a pending state and the
// rest are locked until the session exists.
export function useStartPattern() {
  const { token } = useContext(AuthContext);
  const navigate = useNavigate();
  const [startingSlug, setStartingSlug] = useState<string | null>(null);

  const start = async (slug: string) => {
    if (startingSlug !== null) return;
    setStartingSlug(slug);
    try {
      const session = await startPatternSession(token ?? "", slug);
      navigate(`/practice/${session.id}`);
    } catch (error) {
      console.error("Failed to start pattern:", error);
      showErrorToast("Couldn't start that practice. Please try again.");
      setStartingSlug(null);
    }
  };

  return { start, startingSlug };
}
```

- [ ] **Step 8: Typecheck**

Run: `cd frontend && npm run typecheck 2>&1 | grep -c "error TS"`
Expected: `9` (no new errors).

- [ ] **Step 9: Commit**

```bash
git add frontend/src/api.ts frontend/src/lib/phonics.ts frontend/src/lib/phonics.test.ts frontend/src/hooks/usePhonics.ts
git commit -m "$(cat <<'EOF'
Add the phonics API calls, wording helpers and hooks to the frontend

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 11: Practice screen for pattern sessions

**Files:**
- Modify: `frontend/src/services/audioTransport.ts`, `frontend/src/hooks/useAudioTransport.ts`
- Modify: `frontend/src/components/practice/BasePractice.tsx`, `frontend/src/components/practice/GenericPractice.tsx`, `frontend/src/pages/PracticeRouter.tsx`
- Modify: `frontend/src/config/practiceTypes.ts`, `frontend/src/lib/activities.ts`
- Create: `frontend/src/components/practice/PatternFinish.tsx`

- [ ] **Step 1: Add the event type**

In `frontend/src/services/audioTransport.ts`, replace

```ts
    | "complete"          // guest (try-it) stream only: nothing more is coming
```
with
```ts
    | "complete"          // guest (try-it) stream only: nothing more is coming
    | "session_complete"  // pattern sessions only: the last line was read, with the score
```

- [ ] **Step 2: Pass it through the transport hook**

In `frontend/src/hooks/useAudioTransport.ts`:

Add after the imports from `@/utils/errorHandling`:

```ts
import type { SessionResult } from "@/lib/phonics";
```

Replace

```ts
  /** Called when GPT returns the next practice sentence (arrives in parallel with audio). */
  onNextSentence?: (data: { sentence: any }) => void;
```
with
```ts
  /** Called when GPT returns the next practice sentence (arrives in parallel with audio). */
  onNextSentence?: (data: { sentence: any; line_index?: number; line_count?: number }) => void;
  /** Pattern sessions only: the last line was read. Carries the score. */
  onSessionComplete?: (data: SessionResult) => void;
```

Replace

```ts
      case "next_sentence":
        opts.onNextSentence?.(event.data);
        break;
```
with
```ts
      case "next_sentence":
        opts.onNextSentence?.(event.data);
        break;

      case "session_complete":
        opts.onSessionComplete?.(event.data);
        break;
```

- [ ] **Step 3: Track lines and the finish in BasePractice**

In `frontend/src/components/practice/BasePractice.tsx`:

Add after `import { showPracticeErrorToast } from "@/utils/errorHandling";`:

```ts
import type { SessionResult } from "@/lib/phonics";
```

Replace

```ts
  nextSentence: string | null;
  showNextButton: boolean;
}

interface BasePracticeProps {
```
with
```ts
  nextSentence: string | null;
  showNextButton: boolean;
  // Phonics pattern sessions only: where the child is, the score once the
  // last line is read, and whether they've moved on to the finish screen.
  lineInfo: LineInfo | null;
  sessionResult: SessionResult | null;
  finished: boolean;
}

export interface LineInfo {
  index: number;
  count: number;
}

interface BasePracticeProps {
```

Replace

```ts
  const [isProcessing, setIsProcessing] = useState(false);
  const { token } = useContext(AuthContext);
```
with
```ts
  const [isProcessing, setIsProcessing] = useState(false);
  const [lineInfo, setLineInfo] = useState<LineInfo | null>(null);
  const [nextLineInfo, setNextLineInfo] = useState<LineInfo | null>(null);
  const [sessionResult, setSessionResult] = useState<SessionResult | null>(null);
  const [finished, setFinished] = useState(false);
  const { token } = useContext(AuthContext);
```

Replace

```ts
    onNextSentence: (data) => {
      // Arrives after the GPT call (in parallel with TTS audio). This is the
      // sentence the child reads next; it is not spoken aloud.
      setNextSentence(data.sentence);
      setTimeout(() => {
        setShowNextButton(true);
      }, 1000);
    },
```
with
```ts
    onNextSentence: (data) => {
      // Arrives after the GPT call (in parallel with TTS audio). This is the
      // sentence the child reads next; it is not spoken aloud.
      setNextSentence(data.sentence);
      setNextLineInfo(
        data.line_index !== undefined && data.line_count !== undefined
          ? { index: data.line_index, count: data.line_count }
          : null
      );
      setTimeout(() => {
        setShowNextButton(true);
      }, 1000);
    },
    onSessionComplete: (result) => {
      // The last line of a pattern session. The arrow now leads to the
      // finish screen instead of another sentence.
      setSessionResult(result);
      setTimeout(() => {
        setShowNextButton(true);
      }, 1000);
    },
```

Replace

```ts
        const state = await getCurrentSessionState(token ?? "", session.id);
        if (state.type === "full-feedback-state") {
          setCurrentSentence(state.data.gpt_response.sentence);
        } else if (session.activity.activity_settings?.first_sentence) {
          setCurrentSentence(session.activity.activity_settings.first_sentence);
        } else {
```
with
```ts
        const state = await getCurrentSessionState(token ?? "", session.id);
        if (state.line_count !== undefined) {
          setLineInfo({ index: state.line_index ?? 0, count: state.line_count });
        }
        if (state.type === "full-feedback-state") {
          setCurrentSentence(state.data.gpt_response.sentence);
        } else if (state.data?.first_sentence) {
          // The activity's settings, or a pattern session's first line.
          setCurrentSentence(state.data.first_sentence);
        } else {
```

Replace

```ts
  const displayNextSentence = () => {
    setShowHighlightedWords(false);
```
with
```ts
  const displayNextSentence = () => {
    if (sessionResult) {
      feedbackAudio.reset();
      setFinished(true);
      return;
    }
    if (nextLineInfo) setLineInfo(nextLineInfo);
    setNextLineInfo(null);
    setShowHighlightedWords(false);
```

Replace

```ts
    nextSentence,
    showNextButton,
  });
```
with
```ts
    nextSentence,
    showNextButton,
    lineInfo,
    sessionResult,
    finished,
  });
```

- [ ] **Step 4: Write the finish screen**

Create `frontend/src/components/practice/PatternFinish.tsx`:

```tsx
import { useEffect } from "react";
import { Link } from "react-router-dom";
import { motion, useReducedMotion } from "framer-motion";
import { ArrowRight, RotateCcw, Star, Volume2 } from "lucide-react";
import type { Session } from "@/api";
import { Button } from "@/components/ui/button";
import { useSpeechSynthesis } from "@/hooks/useSpeechSynthesis";
import { useStartPattern } from "@/hooks/usePhonics";
import { finishMessage, type SessionResult } from "@/lib/phonics";

// The screen after the last line of a pattern session. It reads its message
// out loud, since the children using it are still learning to read, and it
// never shows the "Needs practice" label teachers see.
const PatternFinish = ({
  session,
  result,
}: {
  session: Session;
  result: SessionResult;
}) => {
  const { start, startingSlug } = useStartPattern();
  const { speak } = useSpeechSynthesis();
  const reduceMotion = useReducedMotion();
  const { title, detail } = finishMessage(result);
  const spoken = `${title} ${detail}`;

  useEffect(() => {
    speak(spoken, { rate: 0.95 });
  }, [speak, spoken]);

  return (
    <main className="flex min-h-dvh items-center justify-center bg-background p-6">
      <section
        aria-labelledby="finish-heading"
        className="w-full max-w-md rounded-3xl bg-card p-8 text-center shadow-sm ring-1 ring-border"
      >
        <motion.span
          initial={reduceMotion ? false : { scale: 0.6, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ type: "spring", stiffness: 260, damping: 16 }}
          className="mx-auto flex size-20 items-center justify-center rounded-full bg-pastel-yellow text-pastel-yellow-foreground"
        >
          <Star className="size-10" aria-hidden />
        </motion.span>
        <p className="mt-6 text-sm font-medium text-muted-foreground">
          {result.pattern_name}
        </p>
        <h1
          id="finish-heading"
          className="mt-1 text-3xl font-bold tracking-tight text-foreground"
        >
          {title}
        </h1>
        <p className="mt-3 text-lg text-foreground/80">{detail}</p>

        <div className="mt-8 flex flex-col gap-3">
          <Button
            size="lg"
            className="h-14 rounded-xl text-base"
            disabled={startingSlug !== null || !session.pattern_slug}
            onClick={() => session.pattern_slug && start(session.pattern_slug)}
          >
            <RotateCcw className="size-5" />
            {startingSlug ? "Starting…" : "Practice again"}
          </Button>
          <Button asChild variant="outline" size="lg" className="h-14 rounded-xl text-base">
            <Link to="/practice">
              Back to practice
              <ArrowRight className="size-5" />
            </Link>
          </Button>
          <Button
            variant="ghost"
            onClick={() => speak(spoken, { rate: 0.95 })}
            className="mx-auto rounded-xl text-muted-foreground"
          >
            <Volume2 className="size-5" />
            Hear it again
          </Button>
        </div>
      </section>
    </main>
  );
};

export default PatternFinish;
```

- [ ] **Step 5: Use it in GenericPractice**

In `frontend/src/components/practice/GenericPractice.tsx`, add after `import { getPracticeConfig } from "@/config/practiceTypes";`:

```ts
import PatternFinish from "@/components/practice/PatternFinish";
import { lineLabel } from "@/lib/phonics";
```

Replace

```tsx
  return (
    <BasePractice
      session={session}
      renderContent={(props) => (
        <>
          <LocalProcessingAlert />
          <PracticeStage
            {...props}
            session={session}
            next={{
              visible: config.features.hasNextButton && props.showNextButton,
              onNext: props.displayNextSentence,
            }}
          />
        </>
      )}
    />
  );
```
with
```tsx
  return (
    <BasePractice
      session={session}
      renderContent={(props) =>
        props.finished && props.sessionResult ? (
          <PatternFinish session={session} result={props.sessionResult} />
        ) : (
          <>
            <LocalProcessingAlert />
            <PracticeStage
              {...props}
              session={session}
              // Pattern sessions show the pattern and "Line 3 of 7".
              title={session.pattern_name ?? undefined}
              subtitle={
                props.lineInfo
                  ? lineLabel(props.lineInfo.index, props.lineInfo.count)
                  : undefined
              }
              next={{
                visible: config.features.hasNextButton && props.showNextButton,
                onNext: props.displayNextSentence,
              }}
            />
          </>
        )
      }
    />
  );
```

- [ ] **Step 6: Give each session fresh state**

In `frontend/src/pages/PracticeRouter.tsx`, replace

```tsx
    <GenericPractice
      session={session}
      activityType={session.activity.activity_type}
    />
```
with
```tsx
    // Keyed so "Practice again" (a new session id) starts with fresh state.
    <GenericPractice
      key={session.id}
      session={session}
      activityType={session.activity.activity_type}
    />
```

- [ ] **Step 7: Register the type**

In `frontend/src/config/practiceTypes.ts`, add after the `"choice-story": { ... },` entry:

```ts
  "phonics-pattern": {
    title: "Phonics path",
    basePracticeComponent: "BasePractice",
    features: {
      hasNextButton: true,
      hasSentenceOptions: false,
    },
  },
```

In `frontend/src/lib/activities.ts`, replace

```ts
  "choice-story": "Choice story",
};
```
with
```ts
  "choice-story": "Choice story",
  "phonics-pattern": "Phonics path",
};
```

- [ ] **Step 8: Typecheck, lint and test**

Run: `cd frontend && npm run typecheck 2>&1 | grep -c "error TS"; npx eslint src/components/practice src/hooks/useAudioTransport.ts src/pages/PracticeRouter.tsx src/lib; npm test`
Expected: `9`; no lint errors (the existing `ChoiceStoryBasePractice` warning may remain); tests pass.

- [ ] **Step 9: Commit**

```bash
git add frontend/src/services/audioTransport.ts frontend/src/hooks/useAudioTransport.ts frontend/src/components/practice/BasePractice.tsx frontend/src/components/practice/GenericPractice.tsx frontend/src/components/practice/PatternFinish.tsx frontend/src/pages/PracticeRouter.tsx frontend/src/config/practiceTypes.ts frontend/src/lib/activities.ts
git commit -m "$(cat <<'EOF'
Show the line count in pattern sessions and a finish screen at the end

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 12: Student screens

**Files:**
- Create: `frontend/src/components/phonics/PatternStatusChip.tsx`, `TeacherAssignments.tsx`, `PhonicsPathView.tsx`, `ContinuePathCard.tsx`
- Create: `frontend/src/pages/PhonicsPathPage.tsx`
- Modify: `frontend/src/App.tsx`, `frontend/src/pages/Dashboard.tsx`, `frontend/src/pages/PracticeDashboard.tsx`

- [ ] **Step 1: Status chip**

Create `frontend/src/components/phonics/PatternStatusChip.tsx`:

```tsx
import { Check } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  STATUS_LABEL,
  STATUS_TONE,
  STUDENT_LABEL,
  type PatternStatus,
} from "@/lib/phonics";

// Teachers see the plain status. Children (and the parents beside them) see
// gentler words, so nothing on their screens says "Needs practice".
const PatternStatusChip = ({
  status,
  audience,
  className,
}: {
  status: PatternStatus;
  audience: "student" | "teacher";
  className?: string;
}) => (
  <span
    className={cn(
      "inline-flex items-center gap-1 whitespace-nowrap rounded-full px-2.5 py-0.5 text-xs font-medium",
      STATUS_TONE[status],
      className
    )}
  >
    {status === "mastered" && <Check className="size-3" aria-hidden />}
    {(audience === "student" ? STUDENT_LABEL : STATUS_LABEL)[status]}
  </span>
);

export default PatternStatusChip;
```

- [ ] **Step 2: "From your teacher" section**

Create `frontend/src/components/phonics/TeacherAssignments.tsx`:

```tsx
import { Link } from "react-router-dom";
import { ArrowRight, ChevronRight, Loader2 } from "lucide-react";
import type { StudentAssignment } from "@/api";
import { SectionHeader } from "@/components/AppPage";
import PatternStatusChip from "@/components/phonics/PatternStatusChip";
import { useStartPattern } from "@/hooks/usePhonics";
import { activityPastel } from "@/lib/activities";
import { orderAssignments, type PatternStatus } from "@/lib/phonics";
import { cn } from "@/lib/utils";

const ACTION: Record<PatternStatus, string> = {
  not_started: "Start",
  in_progress: "Keep going",
  needs_practice: "Practice again",
  mastered: "Read again",
};

// The patterns a teacher assigned, open ones first. Renders nothing for a
// child with no teacher or nothing assigned.
const TeacherAssignments = ({
  assignments,
  onlyOpen = false,
  limit,
}: {
  assignments: StudentAssignment[] | null;
  onlyOpen?: boolean;
  limit?: number;
}) => {
  const { start, startingSlug } = useStartPattern();
  if (!assignments) return null;
  const ordered = orderAssignments(assignments).filter(
    (a) => !onlyOpen || a.status !== "mastered"
  );
  if (ordered.length === 0) return null;
  const shown = limit ? ordered.slice(0, limit) : ordered;

  return (
    <section aria-labelledby="teacher-assignments-heading">
      <SectionHeader
        id="teacher-assignments-heading"
        title="From your teacher"
        action={
          shown.length < ordered.length && (
            <Link
              to="/practice"
              className="inline-flex min-h-11 items-center gap-1 text-sm font-semibold text-primary hover:underline underline-offset-4"
            >
              See all {ordered.length}
              <ChevronRight className="size-4" />
            </Link>
          )
        }
      />
      <ul className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {shown.map((assignment) => {
          const pastel = activityPastel(assignment.id);
          const isStarting = startingSlug === assignment.pattern_slug;
          return (
            <li key={assignment.id}>
              <button
                type="button"
                onClick={() => start(assignment.pattern_slug)}
                disabled={startingSlug !== null}
                aria-busy={isStarting}
                className={cn(
                  "flex h-full w-full flex-col rounded-2xl p-5 text-left",
                  "shadow-sm ring-1 ring-inset ring-black/5",
                  "dark:shadow-black/50 dark:inset-shadow-2xs dark:inset-shadow-white/10",
                  "transition-all duration-200 outline-none",
                  "hover:-translate-y-0.5 hover:shadow-lg active:translate-y-0 active:scale-[0.99]",
                  "focus-visible:ring-[3px] focus-visible:ring-ring/60",
                  "disabled:cursor-default disabled:hover:translate-y-0 disabled:hover:shadow-sm",
                  startingSlug !== null && !isStarting && "opacity-60"
                )}
                style={{ backgroundColor: pastel.background }}
              >
                <span className="flex items-center justify-between gap-2">
                  <span className="truncate text-xs font-medium text-foreground/70">
                    {assignment.class_name}
                  </span>
                  <PatternStatusChip status={assignment.status} audience="student" />
                </span>
                <span
                  className="mt-3 text-lg font-semibold leading-snug"
                  style={{ color: pastel.foreground }}
                >
                  {assignment.pattern_name}
                </span>
                <span className="mt-1 text-sm text-foreground/70">
                  {assignment.unit_title}
                </span>
                <span
                  className="mt-auto inline-flex items-center gap-1.5 pt-4 text-sm font-semibold"
                  style={{ color: pastel.foreground }}
                >
                  {isStarting ? (
                    <>
                      <Loader2 className="size-4 animate-spin" />
                      Starting…
                    </>
                  ) : (
                    <>
                      {ACTION[assignment.status]}
                      <ArrowRight className="size-4" />
                    </>
                  )}
                </span>
              </button>
            </li>
          );
        })}
      </ul>
    </section>
  );
};

export default TeacherAssignments;
```

- [ ] **Step 3: The path view**

Create `frontend/src/components/phonics/PhonicsPathView.tsx`:

```tsx
import { Check, ChevronDown, Loader2 } from "lucide-react";
import type { PatternProgress, PhonicsPath } from "@/api";
import {
  STATUS_LABEL,
  STATUS_TONE,
  STUDENT_LABEL,
} from "@/lib/phonics";
import { cn } from "@/lib/utils";

type Audience = "student" | "teacher";

// The units in order. The unit holding the next pattern starts open; the
// rest show how far along they are and open on tap. Without onStart it is
// read-only (a teacher looking at one student's path).
const PhonicsPathView = ({
  path,
  audience,
  onStart,
  startingSlug = null,
}: {
  path: PhonicsPath;
  audience: Audience;
  onStart?: (slug: string) => void;
  startingSlug?: string | null;
}) => {
  const nextUnit = path.units.find((unit) =>
    unit.patterns.some((p) => p.slug === path.next_slug)
  )?.id;
  const doneWord = audience === "student" ? "done" : "mastered";

  return (
    <ol className="space-y-3">
      {path.units.map((unit, i) => {
        const complete = unit.mastered_count === unit.patterns.length;
        return (
          <li key={unit.id}>
            <details
              open={unit.id === nextUnit}
              className="group rounded-2xl border bg-card shadow-xs"
            >
              <summary className="flex min-h-16 cursor-pointer list-none items-center gap-4 px-4 py-3 sm:px-5 [&::-webkit-details-marker]:hidden">
                <span
                  className={cn(
                    "flex size-9 shrink-0 items-center justify-center rounded-full text-sm font-semibold",
                    complete
                      ? "bg-pastel-mint text-pastel-mint-foreground"
                      : "bg-muted text-muted-foreground"
                  )}
                >
                  {complete ? <Check className="size-4" aria-label="Done" /> : i + 1}
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block font-semibold text-foreground">{unit.title}</span>
                  <span className="block text-sm text-muted-foreground">
                    {unit.grade} · {unit.mastered_count} of {unit.patterns.length} {doneWord}
                  </span>
                </span>
                <ChevronDown
                  className="size-4 shrink-0 text-muted-foreground transition-transform group-open:rotate-180"
                  aria-hidden
                />
              </summary>
              <ul className="flex flex-wrap gap-2 px-4 pb-4 sm:px-5 sm:pb-5">
                {unit.patterns.map((pattern) => (
                  <li key={pattern.slug}>
                    <PatternTile
                      pattern={pattern}
                      audience={audience}
                      isNext={pattern.slug === path.next_slug}
                      onStart={onStart}
                      isStarting={startingSlug === pattern.slug}
                      disabled={startingSlug !== null}
                    />
                  </li>
                ))}
              </ul>
            </details>
          </li>
        );
      })}
    </ol>
  );
};

const PatternTile = ({
  pattern,
  audience,
  isNext,
  onStart,
  isStarting,
  disabled,
}: {
  pattern: PatternProgress;
  audience: Audience;
  isNext: boolean;
  onStart?: (slug: string) => void;
  isStarting: boolean;
  disabled: boolean;
}) => {
  const label = (audience === "student" ? STUDENT_LABEL : STATUS_LABEL)[pattern.status];
  const body = (
    <>
      {isStarting ? (
        <Loader2 className="size-3.5 animate-spin" aria-hidden />
      ) : pattern.status === "mastered" ? (
        <Check className="size-3.5" aria-hidden />
      ) : pattern.status !== "not_started" ? (
        <span className="size-2 rounded-full bg-current" aria-hidden />
      ) : null}
      {pattern.name}
      <span className="sr-only">, {label}</span>
    </>
  );
  const className = cn(
    "inline-flex min-h-11 items-center gap-1.5 rounded-xl px-3 text-sm font-medium",
    STATUS_TONE[pattern.status],
    isNext && "ring-2 ring-primary"
  );

  if (!onStart) return <span className={className}>{body}</span>;
  return (
    <button
      type="button"
      onClick={() => onStart(pattern.slug)}
      disabled={disabled}
      aria-busy={isStarting}
      className={cn(
        className,
        "transition-transform outline-none hover:-translate-y-0.5 focus-visible:ring-[3px] focus-visible:ring-ring/60",
        "disabled:cursor-default disabled:hover:translate-y-0"
      )}
    >
      {body}
    </button>
  );
};

export default PhonicsPathView;
```

- [ ] **Step 4: The Practice page card**

Create `frontend/src/components/phonics/ContinuePathCard.tsx`:

```tsx
import { Link } from "react-router-dom";
import { ArrowRight, Blocks, ChevronRight, PartyPopper } from "lucide-react";
import type { PhonicsPath } from "@/api";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useStartPattern } from "@/hooks/usePhonics";

// The Practice page's way into the phonics path: the next pattern to work
// on, and a link to every unit. Laid out by its own width, like the
// Dashboard's continue card.
const ContinuePathCard = ({ path }: { path: PhonicsPath | null }) => {
  const { start, startingSlug } = useStartPattern();
  if (!path) return <Skeleton className="h-40 rounded-3xl" />;

  const unitIndex = path.units.findIndex((unit) =>
    unit.patterns.some((p) => p.slug === path.next_slug)
  );
  const unit = unitIndex >= 0 ? path.units[unitIndex] : null;
  const pattern = unit?.patterns.find((p) => p.slug === path.next_slug) ?? null;

  return (
    <div className="@container rounded-3xl bg-pastel-mint p-5 shadow-sm ring-1 ring-inset ring-black/5 sm:p-8 dark:shadow-black/50 dark:inset-shadow-2xs dark:inset-shadow-white/10">
      <div className="flex flex-col gap-5 @xl:flex-row @xl:items-center @xl:gap-6">
        <div className="flex min-w-0 flex-1 items-center gap-4 sm:gap-6">
          <span className="flex size-14 shrink-0 items-center justify-center rounded-2xl bg-white/60 text-pastel-mint-foreground sm:size-20 dark:bg-white/10">
            {pattern ? (
              <Blocks className="size-7 sm:size-10" />
            ) : (
              <PartyPopper className="size-7 sm:size-10" />
            )}
          </span>
          <div className="min-w-0">
            <p className="text-sm font-medium text-foreground/70">
              {unit ? `Unit ${unitIndex + 1} · ${unit.title}` : "Phonics path"}
            </p>
            <h3 className="mt-1 text-xl leading-tight font-bold tracking-tight text-pastel-mint-foreground sm:text-3xl">
              {pattern ? pattern.name : "Every unit done!"}
            </h3>
            <p className="mt-1 text-sm text-foreground/70">
              {unit
                ? `${unit.mastered_count} of ${unit.patterns.length} done in this unit`
                : "Pick any pattern to read it again."}
            </p>
          </div>
        </div>
        {pattern && (
          <Button
            size="lg"
            onClick={() => start(pattern.slug)}
            disabled={startingSlug !== null}
            className="h-14 w-full shrink-0 rounded-xl px-8 text-base font-semibold @xl:w-auto active:scale-[0.98]"
          >
            {startingSlug ? "Starting…" : "Start"}
            <ArrowRight className="size-5" />
          </Button>
        )}
      </div>
      <Link
        to="/phonics"
        className="mt-4 inline-flex min-h-11 items-center gap-1 text-sm font-semibold text-pastel-mint-foreground hover:underline underline-offset-4"
      >
        See all {path.units.length} units
        <ChevronRight className="size-4" />
      </Link>
    </div>
  );
};

export default ContinuePathCard;
```

- [ ] **Step 5: The `/phonics` page and route**

Create `frontend/src/pages/PhonicsPathPage.tsx`:

```tsx
import { AppPage, PageHeader } from "@/components/AppPage";
import PhonicsPathView from "@/components/phonics/PhonicsPathView";
import { Skeleton } from "@/components/ui/skeleton";
import { usePhonicsPath, useStartPattern } from "@/hooks/usePhonics";

const PhonicsPathPage = () => {
  const { path, failed } = usePhonicsPath();
  const { start, startingSlug } = useStartPattern();

  return (
    <AppPage title="Phonics path" width="narrow">
      <PageHeader
        title="Phonics path"
        description="The sounds in the order schools teach them, from short a word families to vowel teams. Each pattern is a short set of words and sentences to read out loud."
      />
      {failed ? (
        <div className="rounded-2xl border border-dashed px-6 py-10 text-center">
          <p className="font-medium text-foreground">Couldn't load the phonics path</p>
          <p className="mt-1 text-sm text-muted-foreground">
            Check your connection and refresh the page.
          </p>
        </div>
      ) : path ? (
        <PhonicsPathView
          path={path}
          audience="student"
          onStart={start}
          startingSlug={startingSlug}
        />
      ) : (
        <div className="space-y-3">
          {Array.from({ length: 6 }, (_, i) => (
            <Skeleton key={i} className="h-16 rounded-2xl" />
          ))}
        </div>
      )}
    </AppPage>
  );
};

export default PhonicsPathPage;
```

In `frontend/src/App.tsx`, add after `const PracticeDashboard = lazy(() => import("./pages/PracticeDashboard.tsx"));`:

```tsx
const PhonicsPathPage = lazy(() => import("./pages/PhonicsPathPage.tsx"));
```

and after `<Route path="/practice" element={<PracticeDashboard />} />` add:

```tsx
                    <Route path="/phonics" element={<PhonicsPathPage />} />
```

- [ ] **Step 6: Practice page**

Replace `frontend/src/pages/PracticeDashboard.tsx` with:

```tsx
import { Link } from "react-router-dom";
import { ChevronRight } from "lucide-react";
import { AppPage, PageHeader, SectionHeader } from "@/components/AppPage";
import ActivitiesList from "@/components/ActivitiesList";
import ContinuePathCard from "@/components/phonics/ContinuePathCard";
import TeacherAssignments from "@/components/phonics/TeacherAssignments";
import { useActivities } from "@/hooks/useActivities";
import { useMyAssignments, usePhonicsPath } from "@/hooks/usePhonics";

// Every activity is visible at once, grouped by kind. A carousel hid most
// of them behind arrows, and there are few enough to show in a grid.
const SECTIONS = [
  {
    type: "choice-story",
    title: "Choice stories",
    description: "Your child picks what happens next.",
  },
  {
    type: "story",
    title: "Stories",
    description: "Classic tales, read one sentence at a time.",
  },
  {
    type: "unlimited",
    title: "Free practice",
    description: "New sentences that keep coming, aimed at the sounds your child misses.",
  },
];

const PracticeDashboard = () => {
  const { activities } = useActivities();
  const { assignments } = useMyAssignments();
  const { path, failed: pathFailed } = usePhonicsPath();

  return (
    <AppPage title="Practice">
      <PageHeader
        title="Practice"
        description="Follow the phonics path one sound at a time, or pick a story or free practice. Every activity listens to your child read and points out the sounds to work on."
      />

      <TeacherAssignments assignments={assignments} />

      {!pathFailed && (
        <section aria-labelledby="phonics-heading">
          <SectionHeader
            id="phonics-heading"
            title="Phonics path"
            action={
              <Link
                to="/phonics"
                className="inline-flex min-h-11 items-center gap-1 text-sm font-semibold text-primary hover:underline underline-offset-4"
              >
                All units
                <ChevronRight className="size-4" />
              </Link>
            }
          />
          <p className="-mt-2 mb-4 text-sm text-muted-foreground">
            One sound at a time, in the order schools teach them.
          </p>
          <ContinuePathCard path={path} />
        </section>
      )}

      {SECTIONS.map((section) => {
        const items = activities?.filter(
          (a) => a.activity_type === section.type
        );
        if (items && items.length === 0) return null;
        return (
          <section key={section.type} aria-labelledby={`${section.type}-heading`}>
            <SectionHeader id={`${section.type}-heading`} title={section.title} />
            <p className="-mt-2 mb-4 text-sm text-muted-foreground">
              {section.description}
            </p>
            <ActivitiesList activities={items ?? null} />
          </section>
        );
      })}
    </AppPage>
  );
};

export default PracticeDashboard;
```

- [ ] **Step 7: Dashboard**

In `frontend/src/pages/Dashboard.tsx`:

Add after `import DynamicIcon from "@/components/DynamicIcon";`:

```tsx
import TeacherAssignments from "@/components/phonics/TeacherAssignments";
```

Add after `import { useActivities, useStartActivity } from "@/hooks/useActivities";`:

```tsx
import { useMyAssignments, useStartPattern } from "@/hooks/usePhonics";
```

In the `DashboardSession` interface, add after `is_completed: boolean;`:

```tsx
  pattern_slug?: string | null;
  pattern_name?: string | null;
```

Replace

```tsx
const RECENT_LIMIT = 4;
```
with
```tsx
const RECENT_LIMIT = 4;

// Phonics sessions all share one activity, so they're told apart by pattern.
const recentKey = (s: DashboardSession) =>
  s.pattern_slug ? `pattern:${s.pattern_slug}` : `activity:${s.activity.id}`;
```

Replace

```tsx
  const { start, startingId } = useStartActivity();
```
with
```tsx
  const { start, startingId } = useStartActivity();
  const { start: startPattern, startingSlug } = useStartPattern();
  const { assignments } = useMyAssignments();
```

Replace

```tsx
  // One row per activity. Every "Start" makes a new session, so without this
  // the list filled up with identical "Unlimited Practice · Today" rows.
  const seenActivities = new Set<number>(
    resumable ? [resumable.activity.id] : []
  );
  const recent = (sessions ?? [])
    .filter((s) => {
      if (seenActivities.has(s.activity.id)) return false;
      seenActivities.add(s.activity.id);
      return true;
    })
    .slice(0, RECENT_LIMIT);

  const openSession = (session: DashboardSession) => {
    if (session.is_completed) start(session.activity.id);
    else navigate(`/practice/${session.id}`);
  };
```
with
```tsx
  // One row per activity (per pattern for phonics). Every "Start" makes a new
  // session, so without this the list filled up with identical "Unlimited
  // Practice · Today" rows.
  const seen = new Set<string>(resumable ? [recentKey(resumable)] : []);
  const recent = (sessions ?? [])
    .filter((s) => {
      if (seen.has(recentKey(s))) return false;
      seen.add(recentKey(s));
      return true;
    })
    .slice(0, RECENT_LIMIT);

  const openSession = (session: DashboardSession) => {
    if (!session.is_completed) navigate(`/practice/${session.id}`);
    else if (session.pattern_slug) startPattern(session.pattern_slug);
    else start(session.activity.id);
  };
```

Replace

```tsx
      <section aria-labelledby="picks-heading">
```
with
```tsx
      <TeacherAssignments assignments={assignments} onlyOpen limit={3} />

      <section aria-labelledby="picks-heading">
```

Replace

```tsx
                  isStarting={startingId === session.activity.id}
                  disabled={startingId !== null}
```
with
```tsx
                  isStarting={
                    session.pattern_slug
                      ? startingSlug === session.pattern_slug
                      : startingId === session.activity.id
                  }
                  disabled={startingId !== null || startingSlug !== null}
```

Replace (in `ContinueCard`)

```tsx
            {session.activity.title}
          </h2>
```
with
```tsx
            {session.pattern_name ?? session.activity.title}
          </h2>
```

Replace (in `RecentRow`)

```tsx
        <span className="block truncate font-medium text-foreground">
          {session.activity.title}
        </span>
```
with
```tsx
        <span className="block truncate font-medium text-foreground">
          {session.pattern_name ?? session.activity.title}
        </span>
```

- [ ] **Step 8: Typecheck, lint and test**

Run: `cd frontend && npm run typecheck 2>&1 | grep -c "error TS"; npx eslint src/components/phonics src/pages/PhonicsPathPage.tsx src/pages/PracticeDashboard.tsx src/pages/Dashboard.tsx src/App.tsx; npm test`
Expected: `9`; no lint errors; tests pass.

- [ ] **Step 9: Commit**

```bash
git add frontend/src/components/phonics frontend/src/pages/PhonicsPathPage.tsx frontend/src/pages/PracticeDashboard.tsx frontend/src/pages/Dashboard.tsx frontend/src/App.tsx
git commit -m "$(cat <<'EOF'
Show the phonics path and teacher assignments to children

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 13: Teacher screens

**Files:**
- Create: `frontend/src/components/classes/AssignPracticeDialog.tsx`, `AssignmentsPanel.tsx`, `PhonicsGrid.tsx`, `StudentPhonicsPath.tsx`
- Modify: `frontend/src/components/classes/ClassDetailView.tsx`, `frontend/src/components/classes/StudentDetailView.tsx`

- [ ] **Step 1: Assign dialog**

Create `frontend/src/components/classes/AssignPracticeDialog.tsx`:

```tsx
import { useContext, useEffect, useState } from "react";
import { AuthContext } from "@/contexts/AuthContext";
import {
  assignPatterns,
  getCurriculum,
  type Curriculum,
  type CurriculumUnit,
  type StudentWithStats,
} from "@/api";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { assignSummary } from "@/lib/phonics";

interface AssignPracticeDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  classId: number;
  students: StudentWithStats[];
  onAssigned: () => void;
}

const AssignPracticeDialog = ({
  open,
  onOpenChange,
  classId,
  students,
  onAssigned,
}: AssignPracticeDialogProps) => {
  const { token } = useContext(AuthContext);
  const [curriculum, setCurriculum] = useState<Curriculum | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [wholeClass, setWholeClass] = useState(true);
  const [chosen, setChosen] = useState<Set<number>>(new Set());
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!open || !token || curriculum) return;
    getCurriculum(token)
      .then(setCurriculum)
      .catch(() => setError("Couldn't load the units. Please try again."));
  }, [open, token, curriculum]);

  const reset = () => {
    setSelected(new Set());
    setWholeClass(true);
    setChosen(new Set());
    setError("");
  };

  const handleOpenChange = (next: boolean) => {
    if (!next) reset();
    onOpenChange(next);
  };

  const toggleUnit = (unit: CurriculumUnit) => {
    const all = unit.patterns.every((p) => selected.has(p.slug));
    const next = new Set(selected);
    unit.patterns.forEach((p) => (all ? next.delete(p.slug) : next.add(p.slug)));
    setSelected(next);
  };

  const toggle = <T,>(set: Set<T>, value: T, update: (next: Set<T>) => void) => {
    const next = new Set(set);
    if (next.has(value)) next.delete(value);
    else next.add(value);
    update(next);
  };

  const studentCount = wholeClass ? students.length : chosen.size;
  const canAssign = selected.size > 0 && studentCount > 0 && !saving;

  const handleAssign = async () => {
    if (!curriculum) return;
    setSaving(true);
    setError("");
    try {
      // Curriculum order, so the class's list reads in teaching order.
      const slugs = curriculum.units
        .flatMap((unit) => unit.patterns.map((p) => p.slug))
        .filter((slug) => selected.has(slug));
      await assignPatterns(token ?? "", classId, slugs, wholeClass ? null : [...chosen]);
      reset();
      onAssigned();
      onOpenChange(false);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Couldn't assign that. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="flex max-h-[90dvh] flex-col sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Assign practice</DialogTitle>
          <DialogDescription>
            Pick whole units or single patterns. Each pattern is one short
            session of words and sentences for your students to read.
          </DialogDescription>
        </DialogHeader>

        <div className="min-h-0 flex-1 space-y-6 overflow-y-auto pr-1">
          <fieldset className="space-y-2">
            <legend className="mb-2 text-sm font-semibold text-foreground">Patterns</legend>
            {!curriculum ? (
              Array.from({ length: 5 }, (_, i) => (
                <Skeleton key={i} className="h-11 rounded-xl" />
              ))
            ) : (
              curriculum.units.map((unit, i) => {
                const count = unit.patterns.filter((p) => selected.has(p.slug)).length;
                return (
                  <details key={unit.id} className="rounded-xl border">
                    <summary className="flex min-h-11 cursor-pointer list-none items-center gap-3 px-3 py-2 [&::-webkit-details-marker]:hidden">
                      <input
                        type="checkbox"
                        checked={count === unit.patterns.length}
                        ref={(el) => {
                          if (el) el.indeterminate = count > 0 && count < unit.patterns.length;
                        }}
                        onChange={() => toggleUnit(unit)}
                        aria-label={`All of ${unit.title}`}
                        className="size-4 accent-primary"
                      />
                      <span className="flex-1 text-sm font-medium text-foreground">
                        {i + 1}. {unit.title}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {count > 0 ? `${count} of ${unit.patterns.length}` : unit.grade}
                      </span>
                    </summary>
                    <div className="grid grid-cols-1 gap-1 px-3 pb-3 sm:grid-cols-2">
                      {unit.patterns.map((pattern) => (
                        <label
                          key={pattern.slug}
                          className="flex min-h-9 items-center gap-2 rounded-lg px-2 text-sm hover:bg-muted"
                        >
                          <input
                            type="checkbox"
                            checked={selected.has(pattern.slug)}
                            onChange={() => toggle(selected, pattern.slug, setSelected)}
                            className="size-4 accent-primary"
                          />
                          {pattern.name}
                        </label>
                      ))}
                    </div>
                  </details>
                );
              })
            )}
          </fieldset>

          <fieldset className="space-y-2">
            <legend className="mb-2 text-sm font-semibold text-foreground">Students</legend>
            <label className="flex min-h-9 items-center gap-2 text-sm">
              <input
                type="radio"
                name="assign-to"
                checked={wholeClass}
                onChange={() => setWholeClass(true)}
                className="size-4 accent-primary"
              />
              Whole class ({students.length}), including students who join later
            </label>
            <label className="flex min-h-9 items-center gap-2 text-sm">
              <input
                type="radio"
                name="assign-to"
                checked={!wholeClass}
                onChange={() => setWholeClass(false)}
                className="size-4 accent-primary"
              />
              Chosen students
            </label>
            {!wholeClass && (
              <div className="grid grid-cols-1 gap-1 rounded-xl border p-3 sm:grid-cols-2">
                {students.map((student) => (
                  <label
                    key={student.id}
                    className="flex min-h-9 items-center gap-2 rounded-lg px-2 text-sm hover:bg-muted"
                  >
                    <input
                      type="checkbox"
                      checked={chosen.has(student.id)}
                      onChange={() => toggle(chosen, student.id, setChosen)}
                      className="size-4 accent-primary"
                    />
                    {student.full_name || student.email}
                  </label>
                ))}
              </div>
            )}
          </fieldset>
        </div>

        {students.length === 0 && (
          <p className="text-sm text-muted-foreground">
            No students have joined yet. Share your join code first.
          </p>
        )}
        {error && <p className="text-sm text-destructive">{error}</p>}

        <DialogFooter className="items-center gap-3 sm:justify-between">
          <p className="text-sm text-muted-foreground">
            {assignSummary(selected.size, studentCount)}
          </p>
          <Button onClick={handleAssign} disabled={!canAssign} className="rounded-xl">
            {saving ? "Assigning..." : "Assign"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default AssignPracticeDialog;
```

- [ ] **Step 2: Assignments panel**

Create `frontend/src/components/classes/AssignmentsPanel.tsx`:

```tsx
import { useContext, useEffect, useState } from "react";
import { ChevronDown, Trash2 } from "lucide-react";
import { AuthContext } from "@/contexts/AuthContext";
import { deleteAssignment, getClassAssignments, type ClassAssignment } from "@/api";
import PatternStatusChip from "@/components/phonics/PatternStatusChip";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { STATUS_LABEL, type PatternStatus } from "@/lib/phonics";

const BAR_ORDER: PatternStatus[] = ["mastered", "needs_practice", "in_progress", "not_started"];

// Just the fill colour of each status tone, for the bar segments.
const BAR_FILL: Record<PatternStatus, string> = {
  mastered: "bg-pastel-mint-foreground",
  needs_practice: "bg-pastel-yellow-foreground",
  in_progress: "bg-pastel-blue-foreground",
  not_started: "bg-muted",
};

const AssignmentsPanel = ({
  classId,
  refreshKey,
}: {
  classId: number;
  refreshKey: number;
}) => {
  const { token } = useContext(AuthContext);
  const [assignments, setAssignments] = useState<ClassAssignment[] | null>(null);
  const [error, setError] = useState("");
  const [removingId, setRemovingId] = useState<number | null>(null);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    getClassAssignments(token, classId)
      .then((data) => {
        if (cancelled) return;
        setAssignments(data);
        setError("");
      })
      .catch((err) => {
        if (!cancelled) setError(err.response?.data?.detail || "Couldn't load assignments");
      });
    return () => {
      cancelled = true;
    };
  }, [classId, token, refreshKey]);

  const remove = async (assignmentId: number) => {
    setRemovingId(assignmentId);
    try {
      await deleteAssignment(token ?? "", classId, assignmentId);
      setAssignments((list) => list?.filter((a) => a.id !== assignmentId) ?? null);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Couldn't remove that assignment");
    } finally {
      setRemovingId(null);
    }
  };

  return (
    <Card className="gap-0 rounded-2xl py-0 shadow-xs">
      <div className="p-6">
        <h2 className="text-lg font-bold text-foreground">Assignments</h2>
        <p className="mt-1 mb-4 text-sm text-muted-foreground">
          Status comes from each student's latest finished session for the
          pattern, including practice at home. Reading 80% of the pattern's
          words right counts as mastered.
        </p>
        {error && <p className="mb-4 text-sm text-destructive">{error}</p>}

        {assignments === null ? (
          <div className="space-y-3">
            {Array.from({ length: 3 }, (_, i) => (
              <Skeleton key={i} className="h-16 rounded-xl" />
            ))}
          </div>
        ) : assignments.length === 0 ? (
          <div className="rounded-2xl border border-dashed px-6 py-10 text-center">
            <p className="font-medium text-foreground">Nothing assigned yet</p>
            <p className="mt-1 text-sm text-muted-foreground">
              Choose Assign practice to give the class a unit or a single sound.
            </p>
          </div>
        ) : (
          <ul className="space-y-3">
            {assignments.map((assignment) => {
              const total = assignment.students.length;
              return (
                <li key={assignment.id}>
                  <details className="group rounded-xl border">
                    <summary className="flex cursor-pointer list-none flex-wrap items-center gap-x-4 gap-y-2 px-4 py-3 [&::-webkit-details-marker]:hidden">
                      <span className="min-w-0 flex-1">
                        <span className="block font-medium text-foreground">
                          {assignment.pattern_name ?? "No longer available"}
                        </span>
                        <span className="block text-sm text-muted-foreground">
                          {assignment.unit_title ? `${assignment.unit_title} · ` : ""}
                          {assignment.whole_class
                            ? "Whole class"
                            : `${total} student${total === 1 ? "" : "s"}`}
                        </span>
                      </span>
                      <span className="flex w-full items-center gap-3 sm:w-64">
                        <span className="flex h-2.5 flex-1 overflow-hidden rounded-full bg-muted" aria-hidden>
                          {total > 0 &&
                            BAR_ORDER.map((status) =>
                              assignment.counts[status] > 0 ? (
                                <span
                                  key={status}
                                  className={`h-full ${BAR_FILL[status]}`}
                                  style={{ width: `${(assignment.counts[status] / total) * 100}%` }}
                                />
                              ) : null
                            )}
                        </span>
                        <span className="sr-only">
                          {BAR_ORDER.map(
                            (s) => `${assignment.counts[s]} ${STATUS_LABEL[s].toLowerCase()}`
                          ).join(", ")}
                        </span>
                        <span className="text-xs whitespace-nowrap text-muted-foreground" aria-hidden>
                          {assignment.counts.mastered}/{total} mastered
                        </span>
                      </span>
                      <ChevronDown
                        className="size-4 shrink-0 text-muted-foreground transition-transform group-open:rotate-180"
                        aria-hidden
                      />
                    </summary>

                    <div className="border-t px-4 py-3">
                      {total === 0 ? (
                        <p className="text-sm text-muted-foreground">
                          No one in the class has this right now.
                        </p>
                      ) : (
                        <div className="overflow-x-auto">
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="text-left text-xs text-muted-foreground">
                                <th className="py-1 font-medium">Student</th>
                                <th className="py-1 font-medium">Status</th>
                                <th className="py-1 text-right font-medium">Words right</th>
                                <th className="py-1 text-right font-medium">Tries</th>
                              </tr>
                            </thead>
                            <tbody>
                              {assignment.students.map((student) => (
                                <tr key={student.id} className="border-t">
                                  <td className="py-2 pr-3 text-foreground">
                                    {student.full_name || "Student"}
                                  </td>
                                  <td className="py-2 pr-3">
                                    <PatternStatusChip status={student.status} audience="teacher" />
                                  </td>
                                  <td className="py-2 text-right tabular-nums">
                                    {student.words_total
                                      ? `${student.words_correct}/${student.words_total}`
                                      : "–"}
                                  </td>
                                  <td className="py-2 text-right tabular-nums">{student.tries}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}
                      <div className="mt-3 flex justify-end">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => remove(assignment.id)}
                          disabled={removingId !== null}
                          className="text-muted-foreground hover:text-destructive"
                        >
                          <Trash2 className="size-4" />
                          {removingId === assignment.id ? "Removing…" : "Remove assignment"}
                        </Button>
                      </div>
                    </div>
                  </details>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </Card>
  );
};

export default AssignmentsPanel;
```

- [ ] **Step 3: Class grid**

Create `frontend/src/components/classes/PhonicsGrid.tsx`:

```tsx
import { useContext, useEffect, useState } from "react";
import { AuthContext } from "@/contexts/AuthContext";
import { getClassPhonicsProgress, type ClassPhonicsProgress } from "@/api";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { unitTone } from "@/lib/phonics";
import { cn } from "@/lib/utils";

// Students down the side, units across the top. Each cell is how many of the
// unit's patterns the student has mastered. Scrolls sideways on phones.
const PhonicsGrid = ({
  classId,
  refreshKey,
}: {
  classId: number;
  refreshKey: number;
}) => {
  const { token } = useContext(AuthContext);
  const [data, setData] = useState<ClassPhonicsProgress | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    getClassPhonicsProgress(token, classId)
      .then((progress) => {
        if (!cancelled) setData(progress);
      })
      .catch((err) => {
        if (!cancelled) setError(err.response?.data?.detail || "Couldn't load the phonics path");
      });
    return () => {
      cancelled = true;
    };
  }, [classId, token, refreshKey]);

  return (
    <Card className="gap-0 rounded-2xl py-0 shadow-xs">
      <div className="p-6">
        <h2 className="text-lg font-bold text-foreground">Phonics path</h2>
        <p className="mt-1 mb-4 text-sm text-muted-foreground">
          Patterns mastered in each unit, counting practice at home too.
        </p>

        {error ? (
          <div className="py-8 text-center text-destructive">{error}</div>
        ) : !data ? (
          <Skeleton className="h-40 rounded-xl" />
        ) : data.students.length === 0 ? (
          <div className="py-8 text-center text-muted-foreground">
            No students have joined this class yet.
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="border-separate border-spacing-1 text-sm">
                <thead>
                  <tr>
                    <th
                      scope="col"
                      className="sticky left-0 z-10 bg-card px-2 py-1 text-left text-xs font-medium text-muted-foreground"
                    >
                      Student
                    </th>
                    {data.units.map((unit, i) => (
                      <th
                        key={unit.id}
                        scope="col"
                        className="min-w-12 px-1 py-1 text-center text-xs font-medium text-muted-foreground"
                      >
                        <abbr title={unit.title} className="no-underline">
                          {i + 1}
                        </abbr>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {data.students.map((student) => (
                    <tr key={student.id}>
                      <th
                        scope="row"
                        className="sticky left-0 z-10 max-w-40 truncate bg-card px-2 py-1 text-left font-medium text-foreground"
                      >
                        {student.full_name || "Student"}
                      </th>
                      {data.units.map((unit) => {
                        const mastered = unit.patterns.filter(
                          (p) => student.statuses[p.slug] === "mastered"
                        ).length;
                        return (
                          <td
                            key={unit.id}
                            title={`${unit.title}: ${mastered} of ${unit.patterns.length} mastered`}
                            className={cn(
                              "rounded-lg px-1 py-2 text-center text-xs font-medium tabular-nums",
                              unitTone(mastered, unit.patterns.length)
                            )}
                          >
                            {mastered}/{unit.patterns.length}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <ol className="mt-4 grid grid-cols-1 gap-x-6 gap-y-1 text-xs text-muted-foreground sm:grid-cols-2 lg:grid-cols-3">
              {data.units.map((unit, i) => (
                <li key={unit.id}>
                  {i + 1}. {unit.title}
                </li>
              ))}
            </ol>
          </>
        )}
      </div>
    </Card>
  );
};

export default PhonicsGrid;
```

- [ ] **Step 4: One student's path for the teacher**

Create `frontend/src/components/classes/StudentPhonicsPath.tsx`:

```tsx
import { useContext, useEffect, useState } from "react";
import { AuthContext } from "@/contexts/AuthContext";
import { getStudentPhonicsPath, type PhonicsPath } from "@/api";
import PhonicsPathView from "@/components/phonics/PhonicsPathView";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

const StudentPhonicsPath = ({
  classId,
  studentId,
}: {
  classId: number;
  studentId: number;
}) => {
  const { token } = useContext(AuthContext);
  const [path, setPath] = useState<PhonicsPath | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    getStudentPhonicsPath(token, classId, studentId)
      .then((data) => {
        if (!cancelled) setPath(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err.response?.data?.detail || "Couldn't load the phonics path");
      });
    return () => {
      cancelled = true;
    };
  }, [classId, studentId, token]);

  return (
    <Card className="gap-0 rounded-2xl py-0 shadow-xs">
      <div className="p-6">
        <h2 className="text-lg font-bold text-foreground mb-4">Phonics path</h2>
        {error ? (
          <div className="text-center text-destructive py-8">{error}</div>
        ) : path ? (
          <PhonicsPathView path={path} audience="teacher" />
        ) : (
          <Skeleton className="h-40 rounded-xl" />
        )}
      </div>
    </Card>
  );
};

export default StudentPhonicsPath;
```

In `frontend/src/components/classes/StudentDetailView.tsx`, add after `import RecommendationsCard from "./RecommendationsCard";`:

```tsx
import StudentPhonicsPath from "./StudentPhonicsPath";
```

and replace

```tsx
      {/* Recent Activity */}
```
with
```tsx
      <StudentPhonicsPath classId={classId} studentId={student.id} />

      {/* Recent Activity */}
```

- [ ] **Step 5: Tabs and the Assign button in the class view**

In `frontend/src/components/classes/ClassDetailView.tsx`:

Replace

```tsx
  ChevronDown,
  ChevronUp,
} from "lucide-react";
```
with
```tsx
  ChevronDown,
  ChevronUp,
  ClipboardList,
} from "lucide-react";
```

Replace

```tsx
import { ACCURACY_TONE, perAccuracyLabel, perTone } from "./accuracy";
```
with
```tsx
import { ACCURACY_TONE, perAccuracyLabel, perTone } from "./accuracy";
import AssignPracticeDialog from "./AssignPracticeDialog";
import AssignmentsPanel from "./AssignmentsPanel";
import PhonicsGrid from "./PhonicsGrid";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
```

Replace

```tsx
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");
```
with
```tsx
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");
  const [showAssign, setShowAssign] = useState(false);
  // Bumped after assigning so the open tab refetches.
  const [assignmentsVersion, setAssignmentsVersion] = useState(0);
```

Replace

```tsx
              <p className="text-sm text-muted-foreground mt-1">
                Class Management
              </p>
            </div>
          </div>
```
with
```tsx
              <p className="text-sm text-muted-foreground mt-1">
                Class Management
              </p>
            </div>
            <Button
              onClick={() => setShowAssign(true)}
              className="shrink-0 self-end rounded-xl"
            >
              <ClipboardList />
              Assign practice
            </Button>
          </div>
```

Replace

```tsx
      {/* Student Roster */}
```
with
```tsx
      <Tabs defaultValue="students" className="gap-4">
        <TabsList className="h-11 w-full sm:w-fit">
          <TabsTrigger value="students" className="px-4">Students</TabsTrigger>
          <TabsTrigger value="assignments" className="px-4">Assignments</TabsTrigger>
          <TabsTrigger value="path" className="px-4">Phonics path</TabsTrigger>
        </TabsList>

        <TabsContent value="students">
      {/* Student Roster */}
```

Replace the end of the file

```tsx
        </div>
      </Card>
    </div>
  );
};

export default ClassDetailView;
```
with
```tsx
        </div>
      </Card>
        </TabsContent>

        <TabsContent value="assignments">
          <AssignmentsPanel classId={classId} refreshKey={assignmentsVersion} />
        </TabsContent>

        <TabsContent value="path">
          <PhonicsGrid classId={classId} refreshKey={assignmentsVersion} />
        </TabsContent>
      </Tabs>

      <AssignPracticeDialog
        open={showAssign}
        onOpenChange={setShowAssign}
        classId={classId}
        students={students}
        onAssigned={() => setAssignmentsVersion((v) => v + 1)}
      />
    </div>
  );
};

export default ClassDetailView;
```

Then indent the roster card two levels so it sits inside `TabsContent`:

```bash
cd frontend && /c/Users/bruce/Coding/word-wiz-ai/backend/venv/Scripts/python.exe - <<'EOF'
from pathlib import Path
p = Path("src/components/classes/ClassDetailView.tsx")
lines = p.read_text(encoding="utf-8").split("\n")
start = next(i for i, l in enumerate(lines) if "{/* Student Roster */}" in l)
end = next(i for i in range(start, len(lines)) if lines[i] == "      </Card>")
lines[start:end + 1] = [("    " + l) if l else l for l in lines[start:end + 1]]
p.write_text("\n".join(lines), encoding="utf-8")
EOF
```

- [ ] **Step 6: Typecheck, lint and test**

Run: `cd frontend && npm run typecheck 2>&1 | grep -c "error TS"; npx eslint src/components/classes; npm test`
Expected: `9`; no lint errors; tests pass.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/classes
git commit -m "$(cat <<'EOF'
Let teachers assign units or patterns and follow the class through them

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 14: Document it in CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Add the new pieces**

In `CLAUDE.md`, in the `routers/` list under Backend Architecture, add after the `google_auth.py` line:

```markdown
  - `phonics.py` - The phonics path, a child's assignments, starting pattern sessions
  - `assignments.py` - Teachers assigning phonics patterns to a class (mounted under `/classes`)
```

In the `core/modes/` list add after `choice_story.py`:

```markdown
  - `phonics_pattern.py` - One phonics pattern, word lines then sentences, no GPT
```

After the "Sessions vs. Activities" section under Key Concepts add:

```markdown
### Phonics curriculum
- The 113 practice-word patterns (`frontend/src/data/phonicsPatterns.ts`) are ordered into 18 units in `frontend/src/data/phonicsCurriculum.json`.
- The backend can't see the frontend, so `python scripts/export_phonics_data.py` (from `/backend`) copies both into `backend/data/phonics_patterns.json`. Run it after editing either file and redeploy the backend. `tests/test_guest_router.py` fails while the copy is stale.
- A pattern session reads the word list in lines of up to five words, then the sentences. Its score (pattern words read right) lives in `pattern_sessions`, beside `sessions`.
- Teachers assign patterns with `assignments` and `assignment_students`. Status (not started, in progress, mastered at 80%, needs practice) is always computed from sessions in `crud/phonics_progress.py`, never stored.
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "$(cat <<'EOF'
Describe the phonics curriculum in CLAUDE.md

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 15: Full checks, end-to-end run and merge into dev

- [ ] **Step 1: Every backend test**

Run: `cd backend && PYTHONUTF8=1 /c/Users/bruce/Coding/word-wiz-ai/backend/venv/Scripts/python.exe -m unittest tests.test_phonics_api tests.test_assignments_api tests.test_phonics_progress tests.test_phonics_mode tests.test_phonics_sessions tests.test_phonics_scoring tests.test_phonics_models tests.test_phonics_data tests.test_guest_router`
Expected: `Ran 68 tests ... OK`.

- [ ] **Step 2: Every frontend check**

Run: `cd frontend && npm test && npm run typecheck 2>&1 | grep -c "error TS" && npm run lint 2>&1 | tail -3 && npm run build:only 2>&1 | tail -3`
Expected: tests pass; `9`; lint shows no errors (warnings that exist on `dev` are fine); the Vite build finishes.

- [ ] **Step 3: Start the servers from the worktree**

Check which ports are free first (`netstat -ano | grep -E ":(8000|8001|5173|5174) "`). Another session may hold 8000 or 5174. `dev_server.py` only allows CORS from 5173, 5174 and 127.0.0.1:5173, so the frontend must use one of those.

Add two temporary entries to the worktree's `.claude/launch.json` (do not commit them):

```json
    {
      "name": "phonics-backend",
      "runtimeExecutable": "C:/Users/bruce/Coding/word-wiz-ai/backend/venv/Scripts/python.exe",
      "runtimeArgs": ["backend/dev_server.py", "--port", "8001"],
      "port": 8001
    },
    {
      "name": "phonics-frontend",
      "runtimeExecutable": "npm",
      "runtimeArgs": ["--prefix", "frontend", "run", "dev", "--", "--port", "5174", "--strictPort"],
      "port": 5174,
      "autoPort": false
    }
```

and create `frontend/.env.development.local` containing `VITE_API_URL=http://localhost:8001` (`*.local` env files are gitignored; check with `git check-ignore frontend/.env.development.local`). Start both with `preview_start`, then confirm in `preview_logs` that the backend printed `Seeded teacher account teacher@wordwiz.test` and `[OK] ONNX Runtime backend loaded successfully`.

- [ ] **Step 4: Run the flow in headless Chrome**

Follow the fake-mic recipe in memory (`practice-e2e-testing`): headless Chrome through the frontend's own `puppeteer`, with `--use-fake-ui-for-media-stream --use-fake-device-for-media-stream --use-file-for-fake-audio-capture=C:/Users/bruce/Coding/word-wiz-ai/backend/tests/system/test_case_02/audio.wav --autoplay-policy=no-user-gesture-required`. Write the script in the scratchpad, not the repo. Sign in with the credentials in `backend/dev_server.py` (`TEACHER_*` and `DEMO_*`). Screenshot each numbered point:

1. Teacher → Classes → Teacher view → Room 4 → **Assign practice** → tick unit 1 → Whole class → Assign. The Assignments tab lists the 7 short-a patterns in order, with Maya Not started.
2. Demo child → Dashboard shows **From your teacher** with -at Word Family first. Practice page shows the same section plus the **Phonics path** card ("Unit 1 · Short a word families").
3. Start -at → header reads "-at Word Family" and "Line 1 of 7" → record about 3 s and stop → feedback arrives → Next shows "Line 2 of 7". Repeat through line 7. The fake audio doesn't match the lines, so expect a low score. After line 7, tapping the arrow shows the finish screen ("Nice reading!" and "You read N of M words right."). If the noise gate says "too noisy", retry that line.
4. `/phonics` shows unit 1 open, -at marked "Try again" (or "Got it"), and an-family ringed as next.
5. Teacher → Assignments tab → -at shows Maya with a status and score. Phonics path tab shows the grid with Maya's unit 1 cell.
6. Reload the practice page mid-session once and check it resumes on the same line with the right "Line n of 7".

Send the screenshots to the user with `SendUserFile`. Check `read_console_messages` (or the script's console log) and `preview_logs` for errors.

- [ ] **Step 5: Clean up**

Stop both servers (`preview_stop`), delete `frontend/.env.development.local`, `git checkout .claude/launch.json`, and remove the junction with `cmd /c rmdir frontend\node_modules`. Run `git status` to confirm the tree is clean.

- [ ] **Step 6: Merge into dev**

`dev` is checked out in the main checkout, which often holds other sessions' staged work, so build the merge commit here on a detached `dev` and fast-forward the main checkout to it:

```bash
git checkout --detach dev
git merge --no-ff feat/phonics-curriculum -m "$(cat <<'EOF'
Merge branch 'feat/phonics-curriculum' into dev

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
)"
MERGE_SHA=$(git rev-parse HEAD)
git -C /c/Users/bruce/Coding/word-wiz-ai merge --ff-only "$MERGE_SHA"
git checkout feat/phonics-curriculum
```

If `dev` moved and the fast-forward fails, repeat from `git checkout --detach dev`. Do not push. Pushing `dev` and deploying are the user's decisions, and the backend has to ship (with `alembic upgrade head` against RDS, or startup's `create_all`) before the frontend that calls the new routes.
