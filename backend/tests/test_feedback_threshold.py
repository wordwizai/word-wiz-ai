"""The feedback corrects a word only when it is clearly wrong, and the rule is in module
constants the benchmark can read. The spoken feedback says which sound and words it is
about, so the benchmark can score it.

A word is clearly wrong when at least MIN_FOCUS_ERRORS (3) of its sounds were wrong.
WWAI_LEGACY_FEEDBACK=1 brings back the old rule (PER at least HIGH_PER_THRESHOLD) and the
old fallback.

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


def _legacy(on=True):
    """The kill switch on (or off), whatever the shell says."""
    return mock.patch.dict(os.environ, {fmt.LEGACY_FEEDBACK_FLAG: "1" if on else ""})


class _CurrentRules(unittest.TestCase):
    """The current feedback rules, whatever the shell says."""

    def setUp(self):
        patcher = _legacy(False)
        patcher.start()
        self.addCleanup(patcher.stop)


class TestThreshold(_CurrentRules):
    DATA = [{"ground_truth_word": "cat", "per": 0.5, "total_errors": 1,
             "expected_phonemes": ["k", "æ", "t"], "substituted": [("k", "g")], "missed": [], "added": []}]
    ERRORS = {"k": [{"word": "cat", "error_type": "substituted"}]}

    def test_value(self):
        self.assertEqual(fmt.HIGH_PER_THRESHOLD, 0.4)
        self.assertEqual(fmt.MIN_FOCUS_ERRORS, 3)

    def test_focus_reads_the_module_constant(self):
        # One error is not a clear mistake, however high the word's PER, unless the constant says so.
        self.assertIsNone(fmt._focus_from_high_per_words(self.DATA, self.ERRORS))
        with mock.patch.object(fmt, "MIN_FOCUS_ERRORS", 1):
            self.assertEqual(fmt._focus_from_high_per_words(self.DATA, self.ERRORS), "k")

    def test_the_legacy_switch_reads_the_per_constant(self):
        with _legacy():
            self.assertEqual(fmt._focus_from_high_per_words(self.DATA, self.ERRORS), "k")
            with mock.patch.object(fmt, "HIGH_PER_THRESHOLD", 0.6):
                self.assertIsNone(fmt._focus_from_high_per_words(self.DATA, self.ERRORS))


class TestIsClearMistake(_CurrentRules):
    """is_clear_mistake is the one test of whether a word may be corrected."""

    def test_three_errors_are_a_clear_mistake_and_two_are_not(self):
        for errors, expected in ((0, False), (1, False), (2, False), (3, True), (4, True)):
            with self.subTest(errors=errors):
                # PER 1.0 throughout, since it no longer decides.
                self.assertIs(fmt.is_clear_mistake({"per": 1.0, "total_errors": errors}), expected)

    def test_a_record_without_a_count_is_not(self):
        for record in ({}, {"per": 1.0}, {"per": 1.0, "total_errors": None}):
            with self.subTest(record=record):
                self.assertIs(fmt.is_clear_mistake(record), False)

    def test_an_inserted_word_never_is(self):
        # An ASR word that is not in the sentence. Its count is 0 anyway, but the type decides.
        self.assertIs(fmt.is_clear_mistake({"type": "insertion", "per": 0.0, "total_errors": 5}), False)
        with _legacy():
            self.assertIs(fmt.is_clear_mistake({"type": "insertion", "per": 0.0, "total_errors": 0}), False)

    def test_the_legacy_switch_brings_back_the_per_rule(self):
        with _legacy():
            self.assertIs(fmt.is_clear_mistake({"per": 0.4, "total_errors": 1}), True)
            self.assertIs(fmt.is_clear_mistake({"per": 0.3999, "total_errors": 5}), False)
            self.assertIs(fmt.is_clear_mistake({"total_errors": 5}), False)

    def test_dataframe_records_give_a_plain_bool(self):
        # The router passes DataFrame records, whose numbers are numpy scalars.
        import pandas as pd

        records = pd.DataFrame([{"per": 1.0, "total_errors": 3}, {"per": 0.5, "total_errors": 2}]).to_dict("records")
        for legacy, expected in ((False, [True, False]), (True, [True, True])):
            with self.subTest(legacy=legacy), _legacy(legacy):
                flags = [fmt.is_clear_mistake(r) for r in records]
                self.assertEqual(flags, expected)
                self.assertTrue(all(type(flag) is bool for flag in flags))

    def test_flag_rule_describes_the_rule_in_use(self):
        self.assertEqual(fmt.flag_rule(), "total_errors >= 3")
        with _legacy():
            self.assertEqual(fmt.flag_rule(), "per >= 0.4")
        with mock.patch.object(fmt, "MIN_FOCUS_ERRORS", 4), mock.patch.object(fmt, "HIGH_PER_THRESHOLD", 0.5):
            self.assertEqual(fmt.flag_rule(), "total_errors >= 4")
            with _legacy():
                self.assertEqual(fmt.flag_rule(), "per >= 0.5")


def _record(word, per, errors, total, expected, substituted=(), missed=()):
    return {
        "ground_truth_word": word, "per": per, "total_errors": errors, "total_phonemes": total,
        "substituted": list(substituted), "missed": list(missed), "added": [],
        "expected_phonemes": list(expected), "canonical_phonemes": list(expected),
    }


class TestFocusIsReturned(_CurrentRules):
    """generate_feedback reports the sound and words a correction is about. The text is unchanged."""

    # "think" read as [f i ŋ g], three wrong sounds. The text and SSML below are what the
    # formatter produced before the focus fields existed, so they also pin that the wording
    # did not move.
    THINK = [
        _record("i", 0.0, 0, 1, ["aɪ"]),
        _record("think", 0.75, 3, 4, ["θ", "ɪ", "ŋ", "k"], substituted=[("θ", "f"), ("ɪ", "i"), ("k", "g")]),
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
        _record("kite", 1.0, 3, 3, ["k", "aɪ", "t"], substituted=[("k", "t"), ("aɪ", "a"), ("t", "d")]),
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
        # One mild error in a low-error sentence is praised too, since no word is clearly wrong.
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


# The data the tests above used before the clear-mistake rule: "think" read as [f i ŋ k]
# (two wrong sounds), and "kite" with two wrong sounds as the worst /k/ word.
THINK_2 = [
    _record("i", 0.0, 0, 1, ["aɪ"]),
    _record("think", 0.5, 2, 4, ["θ", "ɪ", "ŋ", "k"], substituted=[("θ", "f"), ("ɪ", "i")]),
]
K_WORDS_2 = [
    _record("cat", 0.3333, 1, 3, ["k", "æ", "t"], substituted=[("k", "g")]),
    _record("kite", 0.6667, 2, 3, ["k", "aɪ", "t"], substituted=[("k", "t"), ("aɪ", "a")]),
    _record("cake", 0.3333, 1, 3, ["k", "eɪ", "k"], missed=["k"]),
]
# One mild error (/k/ in "cat") in a sentence of twelve phonemes.
MILD = [_record("cat", 0.3333, 1, 3, ["k", "æ", "t"], substituted=[("k", "g")])] + [
    _record(w, 0.0, 0, 3, ["a", "b", "c"]) for w in ("a", "b", "c")
]
PERFECT = [_record("cat", 0.0, 0, 3, ["k", "æ", "t"])]


class TestOnlyClearMistakesAreCorrected(_CurrentRules):
    """One or two wrong sounds are mostly recognizer noise, so they are not corrected."""

    def _assert_names_nothing(self, result, text):
        self.assertEqual((result.text, result.ssml), (text, text))
        self.assertIsNone(result.focus_phoneme)
        self.assertEqual(result.focus_words, [])

    def test_a_word_with_two_errors_is_not_corrected_and_one_with_three_is(self):
        self._assert_names_nothing(fmt.generate_feedback({}, {"sentence_per": 0.4}, THINK_2), "Keep practicing!")
        result = fmt.generate_feedback({}, {"sentence_per": 0.4}, TestFocusIsReturned.THINK)
        self.assertEqual((result.focus_phoneme, result.focus_words), ("θ", ["think"]))

    def test_a_short_word_wrong_in_every_sound_is_not_corrected(self):
        # "the" read as [d ɪ]: PER 1.0, far above the old cutoff, but only two errors.
        the = [_record("the", 1.0, 2, 2, ["ð", "ə"], substituted=[("ð", "d"), ("ə", "ɪ")]),
               _record("cat", 0.0, 0, 3, ["k", "æ", "t"])]
        self._assert_names_nothing(fmt.generate_feedback({}, {"sentence_per": 0.4}, the), "Keep practicing!")

    def test_three_errors_beat_a_short_word_with_a_higher_per(self):
        data = [_record("the", 1.0, 2, 2, ["ð", "ə"], substituted=[("ð", "d"), ("ə", "ɪ")])] + TestFocusIsReturned.THINK
        result = fmt.generate_feedback({}, {"sentence_per": 0.71}, data)
        self.assertEqual((result.focus_phoneme, result.focus_words), ("θ", ["think"]))

    def test_only_mild_errors_get_keep_practicing_or_praise_and_name_nothing(self):
        # The classifier's focus sound is not used. Falling back to it named a mildly wrong
        # word, which on the speechocean762 benchmark was usually one read correctly.
        summary = {"recommended_focus_phoneme": ("k", "most errors"), "phoneme_error_counts": {"k": 3}}
        for per, text in ((0.44, "Keep practicing!"), (0.21, "Keep practicing!"),
                          (0.2, "Great job!"), (0.1, "Great job!")):
            with self.subTest(sentence_per=per):
                self._assert_names_nothing(fmt.generate_feedback(summary, {"sentence_per": per}, K_WORDS_2[:2]), text)
        self._assert_names_nothing(fmt.generate_feedback({}, {"sentence_per": 0.25}, MILD), "Keep practicing!")


def _added(word, expected, added, errors=None):
    """A word whose only errors are sounds added after it (nothing wrong with its own sounds)."""
    rec = _record(word, round(len(added) / len(expected), 4), errors if errors is not None else len(added),
                  len(expected), expected)
    rec["added"] = list(added)
    return rec


class TestNamingUsesTheWordsOwnSounds(_CurrentRules):
    """The feedback only names a sound the word contains, counted on that word alone."""

    def test_an_extra_sound_is_never_named_as_the_words_sound(self):
        # The live bug: an extra word's sounds [k w a] landed on "the", and the feedback said
        # "Watch the 'w' sound in 'the'". "park" lost three of its own sounds.
        data = [_added("the", ["ð", "ə"], ["k", "w", "a"]),
                _record("park", 0.75, 3, 4, ["p", "ɑ", "r", "k"], missed=["ɑ", "r", "k"])]
        result = fmt.generate_feedback({}, {"sentence_per": 0.5}, data)
        self.assertEqual(result.focus_phoneme, "ɑ")
        self.assertEqual(result.focus_words[0], "park")
        self.assertNotIn("'the'", result.text)

    def test_a_word_with_only_extra_sounds_is_passed_over(self):
        data = [_added("the", ["ð", "ə"], ["k", "w", "a"]), _record("cat", 0.0, 0, 3, ["k", "æ", "t"])]
        result = fmt.generate_feedback({}, {"sentence_per": 0.6}, data)
        self.assertEqual((result.text, result.focus_phoneme, result.focus_words), ("Keep practicing!", None, []))

    def test_other_occurrences_of_the_word_do_not_vote(self):
        # Counting by word text pooled both "cat"s, so the first one's /t/ outvoted the
        # second's own errors. Only the clearly wrong "cat" counts, and its first wrong
        # sound in word order is the focus.
        data = [_record("cat", 0.3333, 1, 3, ["k", "æ", "t"], substituted=[("t", "d")]),
                _record("cat", 1.0, 3, 3, ["k", "æ", "t"], substituted=[("k", "g"), ("æ", "ɛ"), ("t", "d")])]
        result = fmt.generate_feedback({}, {"sentence_per": 0.67}, data)
        self.assertEqual((result.focus_phoneme, result.focus_words[0]), ("k", "cat"))

    def test_the_named_words_had_that_sound_wrong(self):
        # /k/ was only added after "the"; it must not appear among the words named for /k/.
        data = [_added("the", ["ð", "ə"], ["k"], errors=1),
                _record("kite", 1.0, 3, 3, ["k", "aɪ", "t"], substituted=[("k", "t"), ("aɪ", "a")], missed=["t"])]
        result = fmt.generate_feedback({}, {"sentence_per": 0.8}, data)
        self.assertEqual(result.focus_words, ["kite"])


class TestRepeatedSounds(_CurrentRules):
    """A sound that is wrong in at least three different words is named, as a pattern."""

    # The screenshot: the short a was wrong in "cat", "chat" and "bat", one sound each.
    CAT_CHAT_BAT = [
        _record("the", 0.0, 0, 2, ["ð", "ə"]),
        _record("cat", 0.3333, 1, 3, ["k", "æ", "t"], substituted=[("æ", "a")]),
        _record("can", 0.0, 0, 3, ["k", "æ", "n"]),
        _record("chat", 0.6667, 2, 3, ["ʧ", "æ", "t"], substituted=[("æ", "a"), ("t", "d")]),
        _record("with", 0.0, 0, 3, ["w", "ɪ", "θ"]),
        _record("a", 0.0, 0, 1, ["ə"]),
        _record("bat", 0.3333, 1, 3, ["b", "æ", "t"], substituted=[("æ", "a")]),
    ]

    def test_a_sound_wrong_in_three_words_is_named_with_those_words(self):
        result = fmt.generate_feedback({}, {"sentence_per": 0.22}, self.CAT_CHAT_BAT)
        self.assertEqual(result.focus_phoneme, "æ")
        self.assertEqual(result.focus_words, ["cat", "chat", "bat"])
        display = fmt._display_name("æ")
        self.assertTrue(result.text.startswith(f"Watch the '{display}' sound in 'cat', 'chat', and 'bat'."), result.text)
        for word in ("cat", "chat", "bat"):
            self.assertIn(f">{word}</phoneme>", result.ssml)

    def test_k_wrong_in_three_words(self):
        result = fmt.generate_feedback({}, {"sentence_per": 0.44}, K_WORDS_2)
        self.assertEqual((result.focus_phoneme, result.focus_words), ("k", ["cat", "kite", "cake"]))

    def test_a_pattern_is_named_even_when_the_sentence_is_mostly_right(self):
        data = self.CAT_CHAT_BAT + [_record(w, 0.0, 0, 3, ["a", "b", "c"]) for w in "defghijk"]
        result = fmt.generate_feedback({}, {"sentence_per": 0.09}, data)
        self.assertEqual(result.focus_phoneme, "æ")

    def test_two_words_are_not_a_pattern(self):
        result = fmt.generate_feedback({}, {"sentence_per": 0.4}, K_WORDS_2[:2])
        self.assertEqual((result.text, result.focus_phoneme), ("Keep practicing!", None))

    def test_the_same_word_three_times_is_not_a_pattern(self):
        thes = [_record("the", 0.5, 1, 2, ["ð", "ə"], substituted=[("ð", "d")]) for _ in range(3)]
        result = fmt.generate_feedback({}, {"sentence_per": 0.5}, thes)
        self.assertEqual((result.text, result.focus_phoneme), ("Keep practicing!", None))

    def test_extra_sounds_and_skipped_words_do_not_count(self):
        # A skipped two-sound word: not clearly wrong (two errors), and skipping is not a wrong sound.
        skipped = {**_record("key", 1.0, 2, 2, ["k", "i"], missed=["k", "i"]), "type": "deletion"}
        data = [_added("the", ["ð", "ə"], ["k"], errors=1), skipped,
                _record("cat", 0.3333, 1, 3, ["k", "æ", "t"], substituted=[("k", "g")]),
                _record("cake", 0.3333, 1, 3, ["k", "eɪ", "k"], missed=["k"])]
        result = fmt.generate_feedback({}, {"sentence_per": 0.5}, data)
        self.assertEqual((result.text, result.focus_phoneme), ("Keep practicing!", None))

    def test_a_clearly_wrong_word_still_comes_first(self):
        result = fmt.generate_feedback({}, {"sentence_per": 0.5}, self.CAT_CHAT_BAT + TestFocusIsReturned.THINK)
        self.assertEqual((result.focus_phoneme, result.focus_words[0]), ("θ", "think"))

    def test_the_legacy_switch_ignores_patterns(self):
        # One wrong sound in each word: the old rule sees no word at PER 0.4 or more and,
        # with a low sentence PER, praises.
        one_each = [_record(w, 0.3333, 1, 3, [c, "æ", "t"], substituted=[("æ", "a")])
                    for w, c in (("cat", "k"), ("hat", "h"), ("bat", "b"))]
        one_each += [_record(w, 0.0, 0, 3, ["a", "b", "c"]) for w in "defghijk"]
        with _legacy():
            self.assertEqual(fmt.generate_feedback({}, {"sentence_per": 0.09}, one_each).text, "Great job!")
        self.assertEqual(fmt.generate_feedback({}, {"sentence_per": 0.09}, one_each).focus_phoneme, "æ")


class TestLegacySwitch(_CurrentRules):
    """WWAI_LEGACY_FEEDBACK=1 gives the earlier feedback on the data the earlier tests used."""

    def test_a_two_error_word_is_corrected_word_for_word_as_before(self):
        with _legacy():
            result = fmt.generate_feedback({}, {"sentence_per": 0.4}, THINK_2)
        self.assertEqual((result.text, result.ssml),
                         (TestFocusIsReturned.THINK_TEXT, TestFocusIsReturned.THINK_SSML))
        self.assertEqual((result.focus_phoneme, result.focus_words), ("θ", ["think"]))

    def test_the_worst_word_by_the_per_rule_and_the_first_word_named(self):
        with _legacy():
            result = fmt.generate_feedback({}, {"sentence_per": 0.44}, K_WORDS_2)
        self.assertEqual(result.text, "In the word 'cat', the letters 'c' make the 'k' sound.")
        self.assertEqual((result.focus_phoneme, result.focus_words), ("k", ["cat", "kite", "cake"]))

    def test_the_old_fallback_still_corrects_a_mild_word(self):
        # No word reaches PER 0.4 and the sentence PER is above 0.2, so the old fallback picks
        # the sound with the most errors and names the first word that has it.
        with _legacy():
            result = fmt.generate_feedback({}, {"sentence_per": 0.25}, MILD)
        self.assertEqual(result.text, "In the word 'cat', the letters 'c' make the 'k' sound.")
        self.assertEqual((result.focus_phoneme, result.focus_words), ("k", ["cat"]))

    def test_praise_and_keep_practicing_are_unchanged(self):
        with _legacy():
            for data, per, text in ((PERFECT, 0.0, "Great job!"), (MILD, 1 / 12, "Great job!"),
                                    (PERFECT, 0.5, "Keep practicing!")):
                with self.subTest(text=text, sentence_per=per):
                    result = fmt.generate_feedback({}, {"sentence_per": per}, data)
                    self.assertEqual((result.text, result.ssml, result.focus_words), (text, text, []))


class TestClearMistakeInTheAnalysis(_CurrentRules):
    """analyze_results' DataFrame, which the router sends as pronunciation_dataframe, carries
    each word's clear_mistake decision, so the frontend can colour words by the feedback's rule."""

    GT = [("the", ["ð", "ə"]), ("cat", ["k", "æ", "t"]), ("sat", ["s", "æ", "t"]),
          ("on", ["ɑ", "n"]), ("the", ["ð", "ə"]), ("mat", ["m", "æ", "t"])]
    # "the cat sat on the mat" read as "the dog sat on the", and the ASR heard an extra "now":
    # a match, a substitution, a deletion and an insertion in one sentence.
    FLAT = ["ð", "ə", "d", "ɔ", "g", "s", "æ", "t", "ɑ", "n", "ð", "ə"]
    ASR = ["the", "cat", "sat", "on", "the", "mat", "now"]

    def setUp(self):
        super().setUp()
        patcher = mock.patch.dict(os.environ)
        patcher.start()
        self.addCleanup(patcher.stop)
        for flag in ("WWAI_G2P_STRICT", "WWAI_LEGACY_WORD_SCORING", "WWAI_GT_ANCHORED_ALIGNMENT"):
            os.environ.pop(flag, None)

    def _records(self):
        from core.gt_alignment import align_to_ground_truth
        return align_to_ground_truth(list(self.FLAT), self.GT, list(self.ASR))

    def test_every_record_carries_the_decision(self):
        from core.process_audio import analyze_results

        records = self._records()
        self.assertEqual({r["type"] for r in records}, {"match", "substitution", "deletion", "insertion"})
        df, _highest, _problems, _per = analyze_results(records)
        rows = df.to_dict("records")
        self.assertEqual([r["clear_mistake"] for r in rows], [fmt.is_clear_mistake(r) for r in records])
        self.assertEqual([r["clear_mistake"] for r in rows], [False, True, False, False, False, True, False])
        # What the router sends is column-oriented and must stay JSON with plain booleans.
        column = df.to_dict()["clear_mistake"]
        self.assertTrue(all(type(flag) is bool for flag in column.values()))

    def test_it_follows_the_legacy_feedback_switch(self):
        from core.process_audio import analyze_results

        records = self._records()
        with _legacy():
            df, _highest, _problems, _per = analyze_results(records)
            expected = [fmt.is_clear_mistake(r) for r in records]
        self.assertEqual(list(df["clear_mistake"]), expected)
        self.assertEqual(expected, [bool(r["per"] >= fmt.HIGH_PER_THRESHOLD) for r in records])

    def test_it_is_additive(self):
        import copy
        import pandas as pd
        from core.process_audio import analyze_results

        records = self._records()
        before = copy.deepcopy(records)
        df, highest, problems, per_summary = analyze_results(records)
        self.assertEqual(records, before)  # the records themselves are not changed
        self.assertEqual(list(df.columns), list(pd.DataFrame(before).columns) + ["clear_mistake"])
        pd.testing.assert_frame_equal(df.drop(columns="clear_mistake"), pd.DataFrame(before))
        self.assertEqual(per_summary["total_errors"], sum(r["total_errors"] for r in before))

    def test_the_feedback_names_only_words_marked_clear_mistakes(self):
        from core.process_audio import analyze_results

        df, _highest, problems, per_summary = analyze_results(self._records())
        rows = df.to_dict("records")
        result = fmt.generate_feedback(problems, per_summary, rows)
        self.assertTrue(result.focus_words)
        marked = {r["ground_truth_word"] for r in rows if r["clear_mistake"]}
        self.assertLessEqual(set(result.focus_words), marked)


if __name__ == "__main__":
    unittest.main()
