"""clean_sentence is the cleanup PhonemeAssistant.process_audio applies before G2P.

Run from backend/:  PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.test_clean_sentence -v
"""

import os
import sys
import unittest
from unittest import mock

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from core.grapheme_to_phoneme import LEGACY_SENTENCE_CLEANING_FLAG, clean_sentence  # noqa: E402


class TestCleanSentence(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.dict(os.environ)
        patcher.start()
        self.addCleanup(patcher.stop)
        os.environ.pop(LEGACY_SENTENCE_CLEANING_FLAG, None)

    def test_keeps_apostrophes_inside_words(self):
        self.assertEqual(clean_sentence("  It's a CAT, isn't it?! "), "it's a cat isn't it")

    def test_kill_switch_matches_historical_cleanup(self):
        os.environ[LEGACY_SENTENCE_CLEANING_FLAG] = "1"
        self.assertEqual(clean_sentence("  It's a CAT, isn't it?! "), "its a cat isnt it")

    def test_periods(self):
        self.assertEqual(clean_sentence("WE CALL IT BEAR."), "we call it bear")


if __name__ == "__main__":
    unittest.main()
