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

    def test_double_quotes_colons_and_semicolons_go(self):
        cases = {
            '"Let\'s go!" said Sam.': "let's go said sam",
            "“Let’s go!” said Sam.": "let's go said sam",
            "Wait: the cat ran; the dog sat.": "wait the cat ran the dog sat",
        }
        for sentence, cleaned in cases.items():
            with self.subTest(sentence=sentence):
                self.assertEqual(clean_sentence(sentence), cleaned)

    def test_dashes_become_spaces(self):
        cases = {
            "cat-dog": "cat dog",
            "The cat–dog ran—fast.": "the cat dog ran fast",
            "Wait - stop -- now": "wait stop now",
        }
        for sentence, cleaned in cases.items():
            with self.subTest(sentence=sentence):
                self.assertEqual(clean_sentence(sentence), cleaned)

    def test_runs_of_whitespace_collapse(self):
        self.assertEqual(clean_sentence(" The  cat \t sat\n"), "the cat sat")

    def test_g2p_gets_one_entry_per_cleaned_word(self):
        # The default G2P splits on single spaces, so a leftover double space would
        # misalign the ground truth.
        from core.grapheme_to_phoneme import grapheme_to_phoneme

        cleaned = clean_sentence('"Wait: the cat-dog ran — fast; ok," she said.')
        self.assertEqual(cleaned, "wait the cat dog ran fast ok she said")
        words = grapheme_to_phoneme(cleaned, strict=False)
        self.assertEqual([w.word for w in words], cleaned.split())
        self.assertFalse(any(w.oov for w in words), words)

    def test_kill_switch_output_is_unchanged(self):
        def historical(sentence):
            return (sentence.strip().lower().replace(".", "").replace(",", "")
                    .replace("?", "").replace("!", "").replace("'", ""))

        os.environ[LEGACY_SENTENCE_CLEANING_FLAG] = "1"
        for sentence in ('"Let\'s go!" said Sam.', "“Let’s go!” said Sam.",
                         "Wait: the cat-dog ran—fast; ok", "cat-dog", " The  cat \t sat\n"):
            with self.subTest(sentence=sentence):
                self.assertEqual(clean_sentence(sentence), historical(sentence))


if __name__ == "__main__":
    unittest.main()
