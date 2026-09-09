"""
Tests for backend/core/grapheme_to_phoneme.py.

Covers the two production bugs:
  1. out-of-vocabulary words fail open and return their SPELLING as "phonemes"
  2. zip() silently truncates the ground truth when eng_to_ipa's token count
     differs from grapheme.split(" ")

and the guarantees of the new WWAI_G2P_STRICT path (explicit unknown marker,
word-count preservation, punctuation handling, memoisation).

These run against the real eng_to_ipa package -- no network, no models.

Run with:
    PYTHONIOENCODING=utf-8 python -m unittest tests.test_grapheme_to_phoneme -v
(from the backend/ directory)
"""

import os
import sys
import unittest

backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

import eng_to_ipa  # noqa: E402

from core.grapheme_to_phoneme import (  # noqa: E402
    UNKNOWN_PHONEME,
    G2PWord,
    cache_info,
    clear_cache,
    grapheme_to_phoneme,
    grapheme_to_phoneme_detailed,
    oov_words,
)


def legacy_reference(grapheme):
    """Verbatim re-implementation of the ORIGINAL function, as the oracle for
    'flag off must be byte-identical'."""
    unfiltered_phonemes = eng_to_ipa.convert(grapheme)
    normalized = unfiltered_phonemes.split(" ")
    output = []
    for word, phonemes in zip(grapheme.split(" "), normalized):
        output.append(
            (
                word,
                list(
                    phonemes.replace("ˈ", "")
                    .replace("ˌ", "")
                    .replace("*", "")
                    .replace(",", "")
                    .replace("'", "")
                ),
            )
        )
    return output


SENTENCES = [
    "the cat sat",
    "hello world",
    "the quick brown fox jumped over the lazy dog",
    "my day goes",
    "the church judged",
    "zyzzyva blorp",
    "wordwiz is fun",
    "the  cat",  # double space
    "a  b   c",  # multiple runs of spaces
    "well-known word",
    "don't stop",
    "Hello, world!",
    "cat.",
    "I read a book",
    "mother-in-law's hat",
    "  leading and trailing  ",
    "3 blind mice",
]


class TestLegacyBehaviourUnchanged(unittest.TestCase):
    """With WWAI_G2P_STRICT unset, values must be identical to the old code."""

    def setUp(self):
        os.environ.pop("WWAI_G2P_STRICT", None)
        clear_cache()

    def test_default_matches_original_implementation(self):
        for sentence in SENTENCES:
            with self.subTest(sentence=sentence):
                got = grapheme_to_phoneme(sentence)
                expected = legacy_reference(sentence)
                self.assertEqual(len(got), len(expected))
                for g, e in zip(got, expected):
                    self.assertEqual(tuple(g), tuple(e))
                    self.assertEqual(g[0], e[0])
                    self.assertEqual(g[1], e[1])

    def test_env_flag_off_explicitly(self):
        os.environ["WWAI_G2P_STRICT"] = "false"
        clear_cache()
        self.assertEqual(
            [tuple(x) for x in grapheme_to_phoneme("zyzzyva blorp")],
            [tuple(x) for x in legacy_reference("zyzzyva blorp")],
        )

    def test_legacy_still_returns_spelling_but_flags_it(self):
        """Bug 1 is *reported* even in legacy mode, without changing values."""
        result = grapheme_to_phoneme("wordwiz is fun")
        self.assertEqual(result[0][1], list("wordwiz"))  # unchanged, letters
        self.assertTrue(result[0].oov)
        self.assertEqual(result[0].source, "spelling")
        self.assertFalse(result[1].oov)
        self.assertEqual(oov_words("wordwiz is fun"), ["wordwiz"])

    def test_legacy_truncation_still_present_by_default(self):
        """Bug 2 documented: legacy drops the trailing word after a double space."""
        sentence = "the  cat sat"
        legacy = grapheme_to_phoneme(sentence)
        self.assertEqual(
            [tuple(x) for x in legacy], [tuple(x) for x in legacy_reference(sentence)]
        )
        legacy_words = [w for w, _ in legacy]
        self.assertNotEqual(legacy_words, sentence.split())
        self.assertNotIn("sat", legacy_words)  # silently lost
        self.assertIn("", legacy_words)  # bogus empty slot
        # strict mode keeps every word
        self.assertEqual(
            [w.word for w in grapheme_to_phoneme(sentence, strict=True)],
            ["the", "cat", "sat"],
        )


class TestG2PWordCompatibility(unittest.TestCase):
    def setUp(self):
        clear_cache()

    def test_is_a_two_tuple(self):
        entry = grapheme_to_phoneme("the cat sat")[1]
        self.assertIsInstance(entry, tuple)
        self.assertEqual(len(entry), 2)
        word, phonemes = entry  # tuple unpacking, as all callers do
        self.assertEqual(word, "cat")
        self.assertIsInstance(phonemes, list)
        self.assertEqual(entry, ("cat", phonemes))  # equality with a plain tuple

    def test_phoneme_lists_are_not_shared_between_calls(self):
        """Memoisation must not hand out mutable cached state."""
        first = grapheme_to_phoneme("the cat sat")
        first[0][1].append("XXX")
        second = grapheme_to_phoneme("the cat sat")
        self.assertNotIn("XXX", second[0][1])

    def test_g2pword_construction(self):
        w = G2PWord(("cat", ["k", "æ", "t"]), oov=False, source="cmudict")
        self.assertEqual(w.word, "cat")
        self.assertEqual(w.phonemes, ["k", "æ", "t"])
        with self.assertRaises(ValueError):
            G2PWord(("a", "b", "c"))


class TestStrictOOV(unittest.TestCase):
    def setUp(self):
        clear_cache()

    def test_oov_no_longer_returns_spelling(self):
        result = grapheme_to_phoneme("zyzzyva blorp", strict=True)
        self.assertEqual(len(result), 2)
        for entry in result:
            self.assertTrue(entry.oov)
            self.assertEqual(entry[1], [UNKNOWN_PHONEME])
            self.assertEqual(entry.source, "unknown")
        # the letters-as-phonemes behaviour is gone
        self.assertNotEqual(result[0][1], list("zyzzyva"))

    def test_known_words_unaffected_by_strict(self):
        result = grapheme_to_phoneme("the cat sat", strict=True)
        self.assertEqual([w.word for w in result], ["the", "cat", "sat"])
        self.assertEqual([w.oov for w in result], [False, False, False])
        self.assertEqual("".join(result[1][1]), "kæt")

    def test_numerals_are_oov_not_digits_as_phonemes(self):
        result = grapheme_to_phoneme("3 blind mice", strict=True)
        self.assertEqual(result[0][1], [UNKNOWN_PHONEME])
        self.assertTrue(result[0].oov)
        self.assertFalse(result[1].oov)

    def test_mixed_sentence_flags_only_the_unknown_word(self):
        result = grapheme_to_phoneme("wordwiz is fun", strict=True)
        self.assertEqual([w.oov for w in result], [True, False, False])
        self.assertEqual(oov_words("wordwiz is fun", strict=True), ["wordwiz"])

    def test_detailed_view(self):
        detailed = grapheme_to_phoneme_detailed("wordwiz is fun", strict=True)
        self.assertEqual(detailed[0]["word"], "wordwiz")
        self.assertTrue(detailed[0]["oov"])
        self.assertEqual(detailed[0]["source"], "unknown")
        self.assertFalse(detailed[1]["oov"])

    def test_env_flag_turns_strict_on(self):
        os.environ["WWAI_G2P_STRICT"] = "true"
        clear_cache()
        try:
            result = grapheme_to_phoneme("zyzzyva blorp")
            self.assertEqual(result[0][1], [UNKNOWN_PHONEME])
        finally:
            os.environ.pop("WWAI_G2P_STRICT", None)
            clear_cache()


class TestStrictNeverTruncates(unittest.TestCase):
    def setUp(self):
        clear_cache()

    def test_word_count_preserved_property(self):
        for sentence in SENTENCES:
            with self.subTest(sentence=sentence):
                expected_words = sentence.split()
                result = grapheme_to_phoneme(sentence, strict=True)
                self.assertEqual(len(result), len(expected_words))
                self.assertEqual([w.word for w in result], expected_words)

    def test_double_space_no_longer_drops_words(self):
        result = grapheme_to_phoneme("a  b   c", strict=True)
        self.assertEqual([w.word for w in result], ["a", "b", "c"])
        self.assertEqual("".join(result[0][1]), "ə")

    def test_double_space_is_broken_in_legacy_mode(self):
        """Sanity check that the property test above is actually testing something."""
        legacy = grapheme_to_phoneme("a  b   c", strict=False)
        self.assertNotEqual([w.word for w in legacy], ["a", "b", "c"])
        self.assertNotIn("c", [w.word for w in legacy])

    def test_empty_and_whitespace_input(self):
        self.assertEqual(grapheme_to_phoneme("", strict=True), [])
        self.assertEqual(grapheme_to_phoneme("   ", strict=True), [])
        # legacy shape preserved for empty string
        self.assertEqual([tuple(x) for x in grapheme_to_phoneme("")], [("", [])])

    def test_leading_and_trailing_whitespace(self):
        result = grapheme_to_phoneme("  leading and trailing  ", strict=True)
        self.assertEqual([w.word for w in result], ["leading", "and", "trailing"])


class TestStrictPunctuationAndWordShapes(unittest.TestCase):
    def setUp(self):
        clear_cache()

    def test_trailing_punctuation_is_not_a_phoneme(self):
        result = grapheme_to_phoneme("Hello, world!", strict=True)
        self.assertEqual([w.word for w in result], ["Hello,", "world!"])
        for entry in result:
            self.assertFalse(entry.oov)
            self.assertNotIn(",", entry[1])
            self.assertNotIn("!", entry[1])
        self.assertEqual("".join(result[1][1]), "wərld")

    def test_period_stripped(self):
        result = grapheme_to_phoneme("cat.", strict=True)
        self.assertEqual("".join(result[0][1]), "kæt")
        self.assertNotIn(".", result[0][1])
        # legacy leaves the period in as a "phoneme"
        self.assertIn(".", grapheme_to_phoneme("cat.")[0][1])

    def test_stress_marks_stripped(self):
        result = grapheme_to_phoneme("tomato potato", strict=True)
        for entry in result:
            self.assertNotIn("ˈ", entry[1])
            self.assertNotIn("ˌ", entry[1])

    def test_contractions(self):
        result = grapheme_to_phoneme("don't stop", strict=True)
        self.assertEqual([w.word for w in result], ["don't", "stop"])
        self.assertEqual([w.oov for w in result], [False, False])
        self.assertEqual("".join(result[0][1]), "doʊnt")
        self.assertNotIn("'", result[0][1])

    def test_hyphenated_word_in_dictionary(self):
        result = grapheme_to_phoneme("well-known word", strict=True)
        self.assertEqual(len(result), 2)
        self.assertFalse(result[0].oov)
        self.assertEqual("".join(result[0][1]), "wɛlnoʊn")

    def test_hyphenated_word_not_in_dictionary_falls_back_to_parts(self):
        # "mother-in-law's" is not a CMUdict entry, but every hyphen part is.
        result = grapheme_to_phoneme("mother-in-law's hat", strict=True)
        self.assertEqual([w.word for w in result], ["mother-in-law's", "hat"])
        self.assertFalse(result[0].oov)
        self.assertEqual(result[0].source, "cmudict:hyphen-split")
        self.assertNotIn(UNKNOWN_PHONEME, result[0][1])
        self.assertNotIn("-", result[0][1])

    def test_pure_punctuation_token_keeps_its_slot(self):
        result = grapheme_to_phoneme("cat -- dog", strict=True)
        self.assertEqual([w.word for w in result], ["cat", "--", "dog"])
        self.assertEqual(result[1][1], [])
        self.assertEqual(result[1].source, "punctuation")


class TestMemoisation(unittest.TestCase):
    def setUp(self):
        clear_cache()

    def test_repeated_conversion_hits_cache(self):
        sentence = "the quick brown fox jumped over the lazy dog"
        grapheme_to_phoneme(sentence)
        before = cache_info()["sentences"]
        for _ in range(25):
            grapheme_to_phoneme(sentence)
        after = cache_info()["sentences"]
        self.assertEqual(after.misses, before.misses)
        self.assertEqual(after.hits, before.hits + 25)

    def test_strict_and_legacy_cached_separately(self):
        clear_cache()
        legacy = grapheme_to_phoneme("zyzzyva blorp", strict=False)
        strict = grapheme_to_phoneme("zyzzyva blorp", strict=True)
        self.assertNotEqual(legacy[0][1], strict[0][1])


if __name__ == "__main__":
    unittest.main(verbosity=2)
