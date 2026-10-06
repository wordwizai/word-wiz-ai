"""Add the activities in new_activities.json to the database.

    cd backend
    python scripts/add_activities.py           # dry run: list what would be added
    python scripts/add_activities.py --apply   # insert them

The database comes from DATABASE_URL, the same as the app, so with the usual
backend/.env this writes to production. To try it on the local dev database
first:

    DATABASE_URL=sqlite:///dev/dev.db python scripts/add_activities.py --apply

An activity is skipped if one with the same title (or, for stories, the same
story_name) is already in the table, so running it twice adds nothing the
second time. Story activities get their first_sentence from the first line of
their story file, which is where StoryPractice starts reading.
"""

import argparse
import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from database import SessionLocal, engine  # noqa: E402
from models import Activity  # noqa: E402

NEW_ACTIVITIES = Path(__file__).with_name("new_activities.json")
STORY_DIR = BACKEND_DIR / "core" / "story_files"
REQUIRED_SETTINGS = {
    "unlimited": [],
    "story": ["story_name"],
    "choice-story": ["story_context", "first_sentence"],
}


def first_story_sentence(story_name):
    """First sentence of a story file, parsed the same way StoryPractice does."""
    path = STORY_DIR / f"{story_name}.txt"
    if not path.is_file():
        raise ValueError(f"no story file at {path}")

    has_name = False
    in_content = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("NAME:") and line.replace("NAME:", "").strip():
            has_name = True
        elif line.startswith("STORY CONTENT:"):
            in_content = True
        elif in_content and line.strip():
            if not has_name:
                raise ValueError(f"{path.name} has no NAME: line")
            # Existing story activities store it without the final period.
            return line.strip().rstrip(".")
    raise ValueError(f"{path.name} has no sentences after STORY CONTENT:")


def load_activities():
    activities = json.loads(NEW_ACTIVITIES.read_text(encoding="utf-8"))
    errors = []
    seen_titles = set()

    for i, activity in enumerate(activities):
        label = activity.get("title") or f"entry {i}"
        for field in ("title", "description", "emoji_icon", "activity_type"):
            if not str(activity.get(field, "")).strip():
                errors.append(f"{label}: missing {field}")
        if len(activity.get("title", "")) > 225:
            errors.append(f"{label}: title is longer than 225 characters")
        if len(activity.get("emoji_icon", "")) > 100:
            errors.append(f"{label}: emoji_icon is longer than 100 characters")

        title_key = activity.get("title", "").lower()
        if title_key in seen_titles:
            errors.append(f"{label}: title appears twice in {NEW_ACTIVITIES.name}")
        seen_titles.add(title_key)

        activity_type = activity.get("activity_type")
        if activity_type not in REQUIRED_SETTINGS:
            errors.append(f"{label}: unknown activity_type {activity_type!r}")
            continue
        settings = activity.setdefault("activity_settings", {})
        for key in REQUIRED_SETTINGS[activity_type]:
            if not str(settings.get(key, "")).strip():
                errors.append(f"{label}: activity_settings needs {key}")

        if activity_type == "story" and settings.get("story_name"):
            try:
                settings.setdefault(
                    "first_sentence", first_story_sentence(settings["story_name"])
                )
            except ValueError as e:
                errors.append(f"{label}: {e}")

    if errors:
        sys.exit("Fix these before adding anything:\n  " + "\n  ".join(errors))
    return activities


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--apply", action="store_true", help="insert the activities (default is a dry run)"
    )
    args = parser.parse_args()

    activities = load_activities()
    print(f"Database: {engine.url.render_as_string(hide_password=True)}\n")

    db = SessionLocal()
    try:
        existing = db.query(Activity).all()
        existing_titles = {a.title.lower() for a in existing}
        existing_stories = {
            (a.activity_settings or {}).get("story_name")
            for a in existing
            if a.activity_type == "story"
        }

        to_add = []
        for activity in activities:
            story_name = activity["activity_settings"].get("story_name")
            if activity["title"].lower() in existing_titles:
                print(f"  skip  {activity['title']} (title already exists)")
            elif activity["activity_type"] == "story" and story_name in existing_stories:
                print(f"  skip  {activity['title']} ({story_name} already has an activity)")
            else:
                print(f"  add   {activity['title']} [{activity['activity_type']}]")
                to_add.append(activity)

        if not to_add:
            print("\nNothing to add.")
        elif not args.apply:
            print(f"\nDry run. Re-run with --apply to add {len(to_add)} activities.")
        else:
            db.add_all(Activity(**activity) for activity in to_add)
            db.commit()
            print(f"\nAdded {len(to_add)} activities.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
