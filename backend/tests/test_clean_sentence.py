"""clean_sentence is the cleanup PhonemeAssistant.process_audio applies before G2P.

Run from backend/:  PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.test_clean_sentence -v
"""

import os
import sys
import unittest

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from core.grapheme_to_phoneme import clean_sentence  # noqa: E402


class TestCleanSentence(unittest.TestCase):
    def test_matches_historical_cleanup(self):
        self.assertEqual(clean_sentence("  It's a CAT, isn't it?! "), "its a cat isnt it")

    def test_periods(self):
        self.assertEqual(clean_sentence("WE CALL IT BEAR."), "we call it bear")


if __name__ == "__main__":
    unittest.main()
