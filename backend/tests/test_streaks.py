"""Tests for reading streaks (crud/feedback_entry.py).

Run from backend/:  python -m unittest tests.test_streaks

No database: the streak helpers take plain dates and datetimes.
"""

import os
import sys
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

# database.py builds an engine at import. Point it at in-memory SQLite so
# these tests can never reach the shared RDS instance in .env.
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from crud.class_membership_crud import calculate_student_streak  # noqa: E402
from crud.feedback_entry import (  # noqa: E402
    calculate_streaks,
    local_date,
    resolve_timezone,
)

TODAY = date(2026, 10, 6)


def days_back(*offsets):
    return [TODAY - timedelta(days=n) for n in offsets]


class CalculateStreaksTest(unittest.TestCase):
    def test_no_reading(self):
        self.assertEqual(calculate_streaks([], today=TODAY), (0, 0))

    def test_read_today_and_the_days_before(self):
        self.assertEqual(calculate_streaks(days_back(0, 1, 2), today=TODAY), (3, 3))

    def test_streak_survives_until_today_is_over(self):
        # Read every day up to yesterday, not yet today: the streak is still
        # alive. It used to show 0 every morning.
        self.assertEqual(calculate_streaks(days_back(1, 2, 3), today=TODAY), (3, 3))

    def test_missing_yesterday_ends_the_streak(self):
        self.assertEqual(calculate_streaks(days_back(2, 3, 4), today=TODAY), (0, 3))

    def test_longest_is_kept_after_a_break(self):
        self.assertEqual(
            calculate_streaks(days_back(0, 1, 5, 6, 7, 8), today=TODAY), (2, 4)
        )

    def test_unsorted_and_repeated_dates(self):
        self.assertEqual(calculate_streaks(days_back(2, 0, 1, 0, 1), today=TODAY), (3, 3))


class LocalDateTest(unittest.TestCase):
    def test_evening_in_california_is_still_that_day(self):
        # 6pm Pacific on Oct 6 is 01:00 UTC on Oct 7, stored without a zone.
        stored = datetime(2026, 10, 7, 1, 0)
        la = resolve_timezone("America/Los_Angeles")
        self.assertEqual(local_date(stored, la), date(2026, 10, 6))
        self.assertEqual(local_date(stored, resolve_timezone(None)), date(2026, 10, 7))

    def test_aware_datetimes_are_converted_too(self):
        stored = datetime(2026, 10, 7, 1, 0, tzinfo=timezone.utc)
        self.assertEqual(
            local_date(stored, resolve_timezone("America/New_York")), date(2026, 10, 6)
        )

    def test_bad_timezone_falls_back_to_utc(self):
        for name in (None, "", "Not/AZone", "../../etc/passwd"):
            self.assertEqual(resolve_timezone(name), timezone.utc, name)

    def test_evening_readers_keep_their_streak(self):
        # A family that reads at 4pm one day and 6pm the next, in California.
        # In UTC those land two days apart (23:00 Oct 5, 01:00 Oct 7), which
        # used to break the streak.
        la = resolve_timezone("America/Los_Angeles")
        stored = [datetime(2026, 10, 5, 23, 0), datetime(2026, 10, 7, 1, 0)]
        dates = [local_date(s, la) for s in stored]
        self.assertEqual(calculate_streaks(dates, today=TODAY), (2, 2))


class StudentStreakTest(unittest.TestCase):
    def test_teacher_view_uses_the_same_days(self):
        la = "America/Los_Angeles"
        now = datetime(2026, 10, 7, 2, 0, tzinfo=timezone.utc)  # 7pm Oct 6 in LA
        sessions = [
            SimpleNamespace(created_at=datetime(2026, 10, 5, 23, 0)),
            SimpleNamespace(created_at=datetime(2026, 10, 7, 1, 0)),
        ]
        self.assertEqual(calculate_student_streak(sessions, tz_name=la, now=now), 2)

    def test_no_sessions(self):
        self.assertEqual(calculate_student_streak([]), 0)


if __name__ == "__main__":
    unittest.main()
