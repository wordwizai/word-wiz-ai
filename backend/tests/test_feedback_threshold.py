"""The focus-word PER cutoff is a module constant the benchmark can read.

Run from backend/:  PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.test_feedback_threshold -v
"""

import os
import sys
import unittest
from unittest import mock

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from core import phoneme_feedback_formatter as fmt  # noqa: E402


class TestThreshold(unittest.TestCase):
    DATA = [{"ground_truth_word": "cat", "per": 0.5, "total_errors": 1}]
    ERRORS = {"k": [{"word": "cat"}]}

    def test_value(self):
        self.assertEqual(fmt.HIGH_PER_THRESHOLD, 0.4)

    def test_focus_reads_the_module_constant(self):
        self.assertEqual(fmt._focus_from_high_per_words(self.DATA, self.ERRORS), "k")
        with mock.patch.object(fmt, "HIGH_PER_THRESHOLD", 0.6):
            self.assertIsNone(fmt._focus_from_high_per_words(self.DATA, self.ERRORS))


if __name__ == "__main__":
    unittest.main()
