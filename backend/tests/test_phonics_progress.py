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
