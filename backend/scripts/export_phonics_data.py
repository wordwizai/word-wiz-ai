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
        if slug in patterns:
            raise ValueError(f"{slug} appears twice in {PATTERNS_SOURCE.name}")
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
    unit_ids: set[str] = set()
    units = []
    for unit in curriculum["units"]:
        if unit["id"] in unit_ids:
            raise ValueError(f"Unit id {unit['id']} is used twice")
        unit_ids.add(unit["id"])
        if not unit["patterns"]:
            raise ValueError(f"Unit {unit['id']} has no patterns")
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
