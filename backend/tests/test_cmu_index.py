"""
Tests for backend/core/cmu_index.py.

Every test works on a temporary copy of eng_to_ipa's CMU_dict.db. The real
database is never written.

Run with (from the backend/ directory):
    PYTHONIOENCODING=utf-8 python -m unittest tests.test_cmu_index -v
"""

import os
import shutil
import sqlite3
import sys
import tempfile
import unittest

backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from core import cmu_index  # noqa: E402


def _indexes(path):
    con = sqlite3.connect(path)
    try:
        return [
            name for (name,) in con.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index' AND tbl_name = 'dictionary'"
            )
        ]
    finally:
        con.close()


def _query_plan(path):
    con = sqlite3.connect(path)
    try:
        rows = con.execute(
            "EXPLAIN QUERY PLAN SELECT word, phonemes FROM dictionary WHERE word IN (?, ?)",
            ("cat", "dog"),
        ).fetchall()
        return " ".join(str(row[-1]) for row in rows)
    finally:
        con.close()


class TestEnsureIndex(unittest.TestCase):

    def setUp(self):
        self.real_db = cmu_index.cmu_db_path()
        self.assertTrue(os.path.isfile(self.real_db), self.real_db)
        self.tmp = tempfile.mkdtemp(prefix="wwai_cmu_")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.db = os.path.join(self.tmp, "CMU_dict.db")
        shutil.copyfile(self.real_db, self.db)
        # Start from an unindexed copy even if the real database is already indexed.
        con = sqlite3.connect(self.db)
        con.execute(f"DROP INDEX IF EXISTS {cmu_index.INDEX_NAME}")
        con.commit()
        con.close()

    def test_db_path_points_into_the_eng_to_ipa_package(self):
        import eng_to_ipa

        self.assertEqual(
            os.path.dirname(os.path.dirname(self.real_db)),
            os.path.dirname(os.path.abspath(eng_to_ipa.__file__)),
        )
        self.assertEqual(os.path.basename(self.real_db), "CMU_dict.db")

    def test_creates_the_index_and_lookups_use_it(self):
        self.assertNotIn(cmu_index.INDEX_NAME, _indexes(self.db))
        self.assertNotIn(cmu_index.INDEX_NAME, _query_plan(self.db))

        self.assertIs(cmu_index.ensure_index(self.db), True)

        self.assertEqual(_indexes(self.db), [cmu_index.INDEX_NAME])
        self.assertIn(cmu_index.INDEX_NAME, _query_plan(self.db))

    def test_is_idempotent(self):
        self.assertIs(cmu_index.ensure_index(self.db), True)
        self.assertIs(cmu_index.ensure_index(self.db), True)
        self.assertEqual(_indexes(self.db), [cmu_index.INDEX_NAME])

    def test_rows_are_untouched(self):
        def rows():
            con = sqlite3.connect(self.db)
            try:
                return con.execute("SELECT id, word, phonemes FROM dictionary ORDER BY id").fetchall()
            finally:
                con.close()

        before = rows()
        cmu_index.ensure_index(self.db)
        self.assertEqual(rows(), before)

    def test_failures_return_false_without_raising(self):
        missing = os.path.join(self.tmp, "nope", "CMU_dict.db")
        self.assertIs(cmu_index.ensure_index(missing), False)
        self.assertFalse(os.path.exists(missing), "must not create an empty database")

        not_a_db = os.path.join(self.tmp, "junk.db")
        with open(not_a_db, "wb") as fh:
            fh.write(b"this is not sqlite" * 100)
        self.assertIs(cmu_index.ensure_index(not_a_db), False)

        no_table = os.path.join(self.tmp, "empty.db")
        sqlite3.connect(no_table).close()
        self.assertIs(cmu_index.ensure_index(no_table), False)

    def test_a_missing_package_returns_false(self):
        from unittest import mock

        with mock.patch.object(cmu_index, "cmu_db_path", return_value=None):
            self.assertIs(cmu_index.ensure_index(), False)


if __name__ == "__main__":
    unittest.main(verbosity=2)
