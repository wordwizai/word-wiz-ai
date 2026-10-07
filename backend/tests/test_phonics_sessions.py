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
