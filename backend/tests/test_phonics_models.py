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
