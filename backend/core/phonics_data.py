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
