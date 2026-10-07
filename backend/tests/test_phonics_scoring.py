"""Tests for core/phonics_scoring.py (no database).

Run from backend/:  python -m unittest tests.test_phonics_scoring
"""

import unittest

from tests.phonics_helpers import analysis

from core.phonics_scoring import is_mastered, line_index, score_readings  # noqa: E402

PATTERN = {
    "words": ["cat", "hat", "that"],
    "word_line_count": 1,
    "lines": ["cat hat that", "That cat has a hat."],
}


class LineIndexTest(unittest.TestCase):
    def test_matches_ignoring_case_and_spacing(self):
        self.assertEqual(line_index(PATTERN, "  CAT hat   that "), 0)
        self.assertEqual(line_index(PATTERN, "that cat has a hat."), 1)
        self.assertIsNone(line_index(PATTERN, "Something else."))


class ScoreReadingsTest(unittest.TestCase):
    def test_every_word_on_a_word_line_counts_and_inserted_sounds_do_not(self):
        reading = ("cat hat that", analysis([("cat", 0.0), ("hat", 0.4), ("that", 0.1)], inserted=1))
        self.assertEqual(score_readings(PATTERN, [reading]), (2, 3))

    def test_sentence_lines_count_only_the_pattern_words(self):
        words = [("that", 0.0), ("cat", 0.2), ("has", 0.9), ("a", 0.9), ("hat.", 0.0)]
        reading = ("That cat has a hat.", analysis(words))
        self.assertEqual(score_readings(PATTERN, [reading]), (2, 3))

    def test_only_the_first_reading_of_a_line_counts(self):
        first = ("cat hat that", analysis([("cat", 0.9), ("hat", 0.9), ("that", 0.9)]))
        again = ("cat hat that", analysis([("cat", 0.0), ("hat", 0.0), ("that", 0.0)]))
        self.assertEqual(score_readings(PATTERN, [first, again]), (0, 3))

    def test_readings_of_other_sentences_are_ignored(self):
        stray = ("The quick brown fox.", analysis([("quick", 0.0)]))
        self.assertEqual(score_readings(PATTERN, [stray]), (0, 0))

    def test_cutoff_matches_the_green_word_badge(self):
        reading = ("cat hat that", analysis([("cat", 0.149), ("hat", 0.15), ("that", None)]))
        self.assertEqual(score_readings(PATTERN, [reading]), (1, 3))


class MasteryTest(unittest.TestCase):
    def test_eighty_percent_is_mastered(self):
        self.assertTrue(is_mastered(8, 10))
        self.assertFalse(is_mastered(7, 10))
        self.assertFalse(is_mastered(0, 0))
        self.assertFalse(is_mastered(None, None))


if __name__ == "__main__":
    unittest.main()
