"""Local backend for trying out changes, backed by a throwaway SQLite file.

    cd backend
    venv\\Scripts\\python dev_server.py           # start on :8000 (seeds on first run)
    venv\\Scripts\\python dev_server.py --reset   # wipe dev/dev.db and seed again
    venv\\Scripts\\python dev_server.py --reload  # restart on .py changes (slow: reloads the model)

It never touches the database in .env. DATABASE_URL is set to dev/dev.db
before anything imports database.py, and python-dotenv does not override a
variable that is already set. The process refuses to start if the engine
ends up pointing anywhere other than SQLite.

The seed is the 13 real activities (dev/seed_activities.json) plus a demo
account with five days of reading history, so the dashboard, streak and
Progress charts all have something to show. Log in with DEMO_EMAIL and
DEMO_PASSWORD below. A teacher account (TEACHER_EMAIL) owns a class with the
demo child in it, for trying phonics assignments. Both only exist inside
dev/dev.db.

OpenAI and Google TTS still use the keys in .env, so recording audio in a
practice session makes real (billed) API calls.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
DEV_DIR = BACKEND_DIR / "dev"
DEV_DB = DEV_DIR / "dev.db"
SEED_ACTIVITIES = DEV_DIR / "seed_activities.json"

DEMO_EMAIL = "demo@wordwiz.test"
DEMO_PASSWORD = "wordwiz-dev"
DEMO_NAME = "Maya Okafor"

TEACHER_EMAIL = "teacher@wordwiz.test"
TEACHER_PASSWORD = "wordwiz-dev"
TEACHER_NAME = "Ms. Rivera"
DEV_CLASS_NAME = "Room 4"
DEV_CLASS_CODE = "DEVRM4"


def configure_environment():
    os.environ["DATABASE_URL"] = f"sqlite:///{DEV_DB.as_posix()}"
    # The frontend dev configs in .claude/launch.json use 5173 and 5174.
    os.environ["EXTRA_CORS_ORIGINS"] = "http://localhost:5174,http://127.0.0.1:5173"
    # Log lines contain emoji; on a Windows code page printing them raises
    # UnicodeEncodeError mid-request (it broke the audio WebSocket).
    os.environ["PYTHONUTF8"] = "1"
    os.environ["PYTHONIOENCODING"] = "utf-8"
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    os.chdir(BACKEND_DIR)
    sys.path.insert(0, str(BACKEND_DIR))


# Each story session reads sentences in order; `next` is what the app would
# have asked for after it, which is what the practice page resumes from.
HISTORY = [
    # (activity_id, days_ago, completed, [(sentence, next_sentence, per, errors)])
    (11, 4, True, [
        ("The hare laughed at the slow tortoise.", "The tortoise said they should have a race.", 0.42, {"sub": [("θ", "f")], "missed": ["r"]}),
        ("The tortoise said they should have a race.", "The hare ran fast and then took a nap.", 0.36, {"sub": [("ð", "d")]}),
        ("The hare ran fast and then took a nap.", "The tortoise kept going one step at a time.", 0.38, {"sub": [("r", "w")], "added": ["ə"]}),
        ("The tortoise kept going one step at a time.", "Slow and steady won the race.", 0.30, {"sub": [("θ", "f")]}),
    ]),
    (1, 3, False, [
        ("The cat sat on the mat in the sun.", "Three thin thieves thought they had the thing.", 0.33, {"sub": [("ð", "d")], "missed": ["t"]}),
        ("Three thin thieves thought they had the thing.", "Ruth threw the thick rope through the thorn bush.", 0.27, {"sub": [("θ", "f"), ("θ", "f")]}),
        ("Ruth threw the thick rope through the thorn bush.", "Thank them for the three thick sandwiches.", 0.24, {"sub": [("r", "w")], "missed": ["r"]}),
    ]),
    (2, 2, False, [
        ("Red packed a basket for her grandma.", "She walked down the path into the woods.", 0.26, {"sub": [("r", "w")]}),
        ("She walked down the path into the woods.", "A wolf stepped out from behind a tree.", 0.21, {"sub": [("ʃ", "s")], "added": ["ə"]}),
        ("A wolf stepped out from behind a tree.", "The wolf asked where she was going.", 0.19, {"missed": ["d"]}),
    ]),
    # Choice stories resume from their own state shape, so this one has no
    # readings yet and starts from the activity's first sentence.
    (4, 1, False, []),
    (10, 0, False, [
        ("Goldilocks found a little house in the woods.", "She tried the porridge in the biggest bowl.", 0.17, {"sub": [("l", "w")]}),
        ("She tried the porridge in the biggest bowl.", "It was too hot, so she tried the next one.", 0.15, {"sub": [("r", "w")]}),
    ]),
]


def phoneme_analysis(per, errors):
    # Same keys the Progress endpoints read in routers/feedback.py.
    return {
        "per_summary": {"sentence_per": per},
        "pronunciation_dataframe": {
            "substituted": {str(i): [list(pair)] for i, pair in enumerate(errors.get("sub", []))},
            "missed": {str(i): [[p]] for i, p in enumerate(errors.get("missed", []))},
            "added": {str(i): [[p]] for i, p in enumerate(errors.get("added", []))},
        },
    }


def add_missing_columns(engine, Base):
    """Add columns the models gained since dev.db was made.

    create_all adds new tables but never new columns, so without this a model
    change (users.is_guest, say) breaks every query until --reset.
    """
    from sqlalchemy import inspect
    from sqlalchemy.schema import CreateColumn

    inspector = inspect(engine)
    with engine.begin() as conn:
        for table in Base.metadata.sorted_tables:
            if not inspector.has_table(table.name):
                continue
            have ={c["name"] for c in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name not in have:
                    ddl = CreateColumn(column).compile(dialect=engine.dialect)
                    conn.exec_driver_sql(f"ALTER TABLE {table.name} ADD COLUMN {ddl}")
                    print(f"Added {table.name}.{column.name} to dev.db")


def seed():
    from auth.auth_handler import create_user, get_password_hash
    from database import Base, SessionLocal, engine
    from models import Activity, Class, ClassMembership, FeedbackEntry, Session, User

    if engine.url.get_backend_name() != "sqlite":
        sys.exit(f"Refusing to start: engine points at {engine.url.get_backend_name()}, not SQLite.")

    Base.metadata.create_all(bind=engine)
    add_missing_columns(engine, Base)
    db = SessionLocal()
    try:
        if db.query(Activity).count() == 0:
            for row in json.loads(SEED_ACTIVITIES.read_text(encoding="utf-8")):
                db.add(Activity(**row))
            db.commit()
            print(f"Seeded {db.query(Activity).count()} activities")

        if db.query(User).filter(User.email == DEMO_EMAIL).first() is None:
            user = create_user(db, User(
                username="demo",
                email=DEMO_EMAIL,
                full_name=DEMO_NAME,
                hashed_password=get_password_hash(DEMO_PASSWORD),
            ))
            # Naive UTC, matching what func.now() stores in SQLite.
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            for activity_id, days_ago, completed, readings in HISTORY:
                started = now - timedelta(days=days_ago, minutes=30)
                session = Session(
                    user_id=user.id,
                    activity_id=activity_id,
                    created_at=started,
                    is_completed=int(completed),
                )
                db.add(session)
                db.flush()
                for i, (sentence, next_sentence, per, errors) in enumerate(readings):
                    db.add(FeedbackEntry(
                        session_id=session.id,
                        sentence=sentence,
                        phoneme_analysis=phoneme_analysis(per, errors),
                        gpt_response={"sentence": next_sentence},
                        created_at=started + timedelta(minutes=2 * (i + 1)),
                    ))
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
        db.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--reset", action="store_true", help="delete dev/dev.db and seed again")
    parser.add_argument("--reload", action="store_true", help="restart when .py files change")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    configure_environment()
    if args.reset and DEV_DB.exists():
        DEV_DB.unlink()
        print("Deleted dev/dev.db")
    seed()

    import uvicorn

    print(f"Dev backend on http://localhost:{args.port} using {DEV_DB}")
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=args.port,
        reload=args.reload,
        reload_dirs=[str(BACKEND_DIR)] if args.reload else None,
    )


if __name__ == "__main__":
    main()
