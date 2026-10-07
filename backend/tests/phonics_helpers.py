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
import database  # noqa: E402

# The env var above only works if nothing imported database.py first.
assert database.engine.url.get_backend_name() == "sqlite", "tests must not reach the real database"
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
    pronunciation dataframe, keyed by row number. Inserted sounds have an empty expected word.
    """
    rows = list(words) + [("", 0.0)] * inserted
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
