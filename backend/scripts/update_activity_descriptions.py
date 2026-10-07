"""Give the original activities their own descriptions.

Six of the first story activities shared one placeholder description,
"Dive into this classic fairy tail with a personalized twist." (with the
typo), and Unlimited Practice said "Test your skills in this basic unlimited
practice mode". This replaces each with a short description of its own, in
the same style as the activities in new_activities.json.

    cd backend
    python scripts/update_activity_descriptions.py           # dry run
    python scripts/update_activity_descriptions.py --apply   # write them

The database comes from DATABASE_URL, the same as the app, so with the usual
backend/.env this writes to production. To try it on the local dev database
first:

    DATABASE_URL=sqlite:///dev/dev.db python scripts/update_activity_descriptions.py --apply

Rows are matched by title and only changed while they still have one of the
old placeholder descriptions, so running it twice changes nothing the second
time and a description someone has since edited by hand is left alone.
"""

import argparse
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from database import SessionLocal, engine  # noqa: E402
from models import Activity  # noqa: E402

OLD_DESCRIPTIONS = {
    "Dive into this classic fairy tail with a personalized twist.",
    "Test your skills in this basic unlimited practice mode",
}

NEW_DESCRIPTIONS = {
    "Unlimited Practice": "New sentences that keep coming, each one built around the sounds your child is still working on.",
    "Little Red Riding Hood": "Little Red Riding Hood is taking a basket to Grandma's house. A wolf in the woods has other plans.",
    "Cinderella": "Cinderella does all the chores while her stepsisters go to the ball. Then her fairy godmother shows up.",
    "Goldilocks and the Three Bears": "Goldilocks walks into an empty house and tries everything inside. Then the three bears come home.",
    "The Tortoise and the Hare": "A speedy hare laughs at a slow tortoise and agrees to a race. He's so sure he'll win that he takes a nap.",
    "Hansel and Gretel": "Hansel and Gretel get lost in the forest and find a house made of candy. The woman who lives there is not so sweet.",
    "Jack and the Beanstalk": "Jack trades the family cow for a handful of beans. By morning, a beanstalk has grown up past the clouds.",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--apply", action="store_true", help="write the descriptions (default is a dry run)"
    )
    args = parser.parse_args()

    print(f"Database: {engine.url.render_as_string(hide_password=True)}\n")

    db = SessionLocal()
    try:
        to_update = []
        for title, description in NEW_DESCRIPTIONS.items():
            rows = db.query(Activity).filter(Activity.title == title).all()
            if not rows:
                print(f"  skip    {title} (not in the table)")
            for row in rows:
                if row.description in OLD_DESCRIPTIONS:
                    print(f"  update  {title}")
                    to_update.append((row, description))
                else:
                    print(f"  skip    {title} (description already changed)")

        if not to_update:
            print("\nNothing to update.")
        elif not args.apply:
            print(f"\nDry run. Re-run with --apply to update {len(to_update)} activities.")
        else:
            for row, description in to_update:
                row.description = description
            db.commit()
            print(f"\nUpdated {len(to_update)} activities.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
