"""The focus-word PER cutoff is a module constant the benchmark can read, and the spoken
feedback says which sound and words it is about, so the benchmark can score it.

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


def _record(word, per, errors, total, expected, substituted=(), missed=()):
    return {
        "ground_truth_word": word, "per": per, "total_errors": errors, "total_phonemes": total,
        "substituted": list(substituted), "missed": list(missed), "added": [],
        "expected_phonemes": list(expected), "canonical_phonemes": list(expected),
    }


class TestFocusIsReturned(unittest.TestCase):
    """generate_feedback reports the sound and words a correction is about. The text is unchanged."""

    # "think" read as [f i ŋ k]. The text and SSML below are what the formatter produced
    # before the focus fields existed, so they also pin that the wording did not move.
    THINK = [
        _record("i", 0.0, 0, 1, ["aɪ"]),
        _record("think", 0.5, 2, 4, ["θ", "ɪ", "ŋ", "k"], substituted=[("θ", "f"), ("ɪ", "i")]),
    ]
    THINK_TEXT = (
        "In the word 'think', the letters 'th' make the 'th' sound. When you see 'th', put your "
        "tongue lightly between your teeth and blow air out gently — like in 'think' or 'three'."
    )
    THINK_SSML = (
        'In the word <phoneme alphabet="ipa" ph="θɪŋk">think</phoneme>, the letters '
        '<say-as interpret-as="spell-out">th</say-as> make the <break time="400ms"/>'
        '<phoneme alphabet="ipa" ph="θə">thuh</phoneme><break time="300ms"/> sound. '
        "When you see 'th', put your tongue lightly between your teeth and blow air out gently "
        "— like in 'think' or 'three'."
    )

    def test_a_correction_returns_its_sound_and_the_word_it_names(self):
        result = fmt.generate_feedback({}, {"sentence_per": 0.4}, self.THINK)
        self.assertEqual(result.text, self.THINK_TEXT)
        self.assertEqual(result.ssml, self.THINK_SSML)
        self.assertEqual(result.focus_phoneme, "θ")
        self.assertEqual(result.focus_words, ["think"])
        self.assertIn(f"'{result.focus_words[0]}'", result.text)

    # /k/ is wrong in three words. "kite" is the worst word, so /k/ is the focus sound.
    K_WORDS = [
        _record("cat", 0.3333, 1, 3, ["k", "æ", "t"], substituted=[("k", "g")]),
        _record("kite", 0.6667, 2, 3, ["k", "aɪ", "t"], substituted=[("k", "t"), ("aɪ", "a")]),
        _record("cake", 0.3333, 1, 3, ["k", "eɪ", "k"], missed=["k"]),
    ]

    def test_the_text_names_the_word_the_sound_came_from(self):
        # The focus sound comes from the worst word, so that is the word to name. Naming the
        # first word in the sentence with any /k/ error named a mildly wrong word instead (on
        # the speechocean762 benchmark the named word was a real mistake far less often).
        result = fmt.generate_feedback({}, {"sentence_per": 0.44}, self.K_WORDS)
        self.assertEqual(result.text, "In the word 'kite', the letters 'k' make the 'k' sound.")
        self.assertEqual(result.focus_phoneme, "k")
        self.assertEqual(result.focus_words, ["kite", "cat", "cake"])

    def test_the_legacy_switch_names_the_first_word_in_sentence_order(self):
        with mock.patch.dict(os.environ, {fmt.LEGACY_FEEDBACK_FLAG: "1"}):
            result = fmt.generate_feedback({}, {"sentence_per": 0.44}, self.K_WORDS)
        self.assertEqual(result.text, "In the word 'cat', the letters 'c' make the 'k' sound.")
        self.assertEqual(result.focus_words, ["cat", "kite", "cake"])
        self.assertEqual(
            result.focus_words,
            fmt._words_for_phoneme("k", fmt.build_phoneme_to_error_words(self.K_WORDS), max_words=3),
        )

    def test_praise_names_nothing(self):
        perfect = [_record("cat", 0.0, 0, 3, ["k", "æ", "t"])]
        # One mild error in a low-error sentence is praised too, since no word cleared the cutoff.
        mild = [_record("cat", 0.3333, 1, 3, ["k", "æ", "t"], substituted=[("k", "g")])] + [
            _record(w, 0.0, 0, 3, ["a", "b", "c"]) for w in ("a", "b", "c")
        ]
        for name, data, per in (("perfect", perfect, 0.0), ("mild", mild, 1 / 12)):
            with self.subTest(name):
                result = fmt.generate_feedback({}, {"sentence_per": per}, data)
                self.assertEqual((result.text, result.ssml), ("Great job!", "Great job!"))
                self.assertIsNone(result.focus_phoneme)
                self.assertEqual(result.focus_words, [])

    def test_keep_practicing_names_nothing(self):
        result = fmt.generate_feedback({}, {"sentence_per": 0.5}, [_record("cat", 0.0, 0, 3, ["k", "æ", "t"])])
        self.assertEqual((result.text, result.ssml), ("Keep practicing!", "Keep practicing!"))
        self.assertIsNone(result.focus_phoneme)
        self.assertEqual(result.focus_words, [])

    def test_the_new_fields_have_defaults(self):
        a, b = fmt.FeedbackResult("Great job!", "Great job!"), fmt.FeedbackResult(text="x", ssml="y")
        self.assertIsNone(a.focus_phoneme)
        self.assertEqual(a.focus_words, [])
        a.focus_words.append("cat")
        self.assertEqual(b.focus_words, [])  # not one shared list


if __name__ == "__main__":
    unittest.main()
