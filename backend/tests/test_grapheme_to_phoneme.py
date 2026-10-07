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
    pronunciation_variants,
    sentence_pronunciation_variants,
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


class TestPronunciationVariants(unittest.TestCase):
    """Every CMUdict pronunciation of a word, tokenized like the ground truth."""

    def setUp(self):
        clear_cache()

    def tearDown(self):
        clear_cache()

    def test_function_words_have_their_reduced_and_full_forms(self):
        variants = pronunciation_variants("to", strict=False)
        self.assertIn(["t", "u"], variants)
        self.assertIn(["t", "ɪ"], variants)
        self.assertIn(["ð", "i"], pronunciation_variants("the", strict=False))
        self.assertIn(["ð", "ə"], pronunciation_variants("the", strict=False))

    def test_strict_mode_tokenizes_like_strict_g2p(self):
        self.assertIn(["t", "u"], pronunciation_variants("to", strict=True))
        # Strict keeps the diphthong whole, exactly as grapheme_to_phoneme does.
        self.assertIn(["eɪ"], pronunciation_variants("a", strict=True))
        self.assertIn(["e", "ɪ"], pronunciation_variants("a", strict=False))

    def test_primary_pronunciation_is_always_a_variant(self):
        for strict in (False, True):
            for word in ("to", "the", "and", "a", "that", "can", "cat", "record", "read"):
                with self.subTest(word=word, strict=strict):
                    primary = grapheme_to_phoneme(word, strict=strict)[0][1]
                    self.assertIn(primary, pronunciation_variants(word, strict=strict))

    def test_no_duplicates_and_no_stress_marks(self):
        for strict in (False, True):
            for word in ("record", "present", "the", "to"):
                with self.subTest(word=word, strict=strict):
                    variants = pronunciation_variants(word, strict=strict)
                    self.assertEqual(len(variants), len({tuple(v) for v in variants}))
                    for v in variants:
                        self.assertFalse(set("ˈˌ*") & set("".join(v)))

    def test_out_of_vocabulary_words_have_no_variants(self):
        for strict in (False, True):
            with self.subTest(strict=strict):
                self.assertEqual(pronunciation_variants("wordwiz", strict=strict), [])
                self.assertEqual(pronunciation_variants("3", strict=strict), [])
                self.assertEqual(pronunciation_variants("", strict=strict), [])

    def test_digit_only_tokens_have_no_variants(self):
        # eng_to_ipa marks an unknown word with "*" but returns a bare number
        # unmarked, so numbers are rejected before the lookup.
        from unittest import mock
        import core.grapheme_to_phoneme as g2p_module

        self.assertEqual(eng_to_ipa.ipa_list("2024")[0], ["2024"])
        with mock.patch.object(g2p_module.G2p, "ipa_list", wraps=eng_to_ipa.ipa_list) as spy:
            for strict in (False, True):
                for token in ("3", "2024", "0"):
                    with self.subTest(token=token, strict=strict):
                        self.assertEqual(pronunciation_variants(token, strict=strict), [])
            self.assertEqual(spy.call_count, 0)
            got = sentence_pronunciation_variants(["i", "have", "3", "cats"], strict=False)
        self.assertEqual(got["3"], [])
        self.assertIn(["k", "æ", "t", "s"], got["cats"])

    def test_a_raising_eng_to_ipa_gives_no_variants(self):
        from unittest import mock
        import core.grapheme_to_phoneme as g2p_module

        with mock.patch.object(g2p_module.G2p, "ipa_list", side_effect=RuntimeError("db gone")):
            self.assertEqual(pronunciation_variants("to", strict=False), [])
        clear_cache()
        with mock.patch.object(g2p_module, "tokenize_ipa", side_effect=RuntimeError("bad symbol")):
            self.assertEqual(pronunciation_variants("to", strict=True), [])

    def test_a_failed_lookup_is_not_cached(self):
        # A transient sqlite error must not be remembered as "no variants".
        from unittest import mock
        import core.grapheme_to_phoneme as g2p_module

        for strict in (False, True):
            with self.subTest(strict=strict):
                clear_cache()
                with mock.patch.object(g2p_module.G2p, "ipa_list", side_effect=RuntimeError("db locked")):
                    self.assertEqual(pronunciation_variants("to", strict=strict), [])
                    self.assertEqual(
                        sentence_pronunciation_variants(["go", "to"], strict=strict),
                        {"go": [], "to": []},
                    )
                self.assertIn(["t", "u"], pronunciation_variants("to", strict=strict))
                self.assertIn(["t", "u"], sentence_pronunciation_variants(["go", "to"], strict=strict)["to"])

        clear_cache()
        with mock.patch.object(g2p_module, "tokenize_ipa", side_effect=RuntimeError("bad symbol")):
            self.assertEqual(pronunciation_variants("to", strict=True), [])
        self.assertIn(["t", "u"], pronunciation_variants("to", strict=True))

    def test_strict_none_reads_the_environment(self):
        from unittest import mock

        with mock.patch.dict(os.environ, {"WWAI_G2P_STRICT": "true"}):
            self.assertEqual(pronunciation_variants("a"), pronunciation_variants("a", strict=True))
        with mock.patch.dict(os.environ, {"WWAI_G2P_STRICT": "false"}):
            self.assertEqual(pronunciation_variants("a"), pronunciation_variants("a", strict=False))

    def test_callers_get_fresh_lists(self):
        first = pronunciation_variants("to", strict=False)
        first[0].append("x")
        first.append(["y"])
        self.assertEqual(pronunciation_variants("to", strict=False), [["t", "u"], ["t", "ə"], ["t", "ɪ"]])

        batch = sentence_pronunciation_variants(["to"], strict=False)
        batch["to"][0].append("x")
        self.assertEqual(sentence_pronunciation_variants(["to"], strict=False)["to"][0], ["t", "u"])


class TestSentencePronunciationVariants(unittest.TestCase):
    """One dictionary query per sentence, the same answers as word by word."""

    SENTENCE = "the quick brown fox can read to wordwiz and the lazy dog"

    def setUp(self):
        clear_cache()

    def tearDown(self):
        clear_cache()

    def test_batching_matches_per_word_lookups(self):
        words = self.SENTENCE.split()
        for strict in (False, True):
            with self.subTest(strict=strict):
                clear_cache()
                batch = sentence_pronunciation_variants(words, strict=strict)
                clear_cache()
                per_word = {w: pronunciation_variants(w, strict=strict) for w in words}
                self.assertEqual(batch, per_word)
                self.assertEqual(batch["wordwiz"], [])
                self.assertIn(["t", "u"], batch["to"])

    def test_one_query_per_sentence_and_repeated_words_stay_cached(self):
        from unittest import mock
        import core.grapheme_to_phoneme as g2p_module

        words = self.SENTENCE.split()
        with mock.patch.object(g2p_module.G2p, "ipa_list", wraps=eng_to_ipa.ipa_list) as spy:
            sentence_pronunciation_variants(words, strict=False)
            self.assertEqual(spy.call_count, 1)
            # "the" is asked for once even though the sentence has it twice.
            self.assertEqual(spy.call_args.args[0].split().count("the"), 1)

            sentence_pronunciation_variants(words, strict=False)
            pronunciation_variants("dog", strict=False)
            self.assertEqual(spy.call_count, 1)

            sentence_pronunciation_variants(["the", "big", "dog"], strict=False)
            self.assertEqual(spy.call_count, 2)
            self.assertEqual(spy.call_args.args[0], "big")

    def test_strict_and_legacy_are_cached_separately(self):
        self.assertIn(["e", "ɪ"], sentence_pronunciation_variants(["a"], strict=False)["a"])
        self.assertIn(["eɪ"], sentence_pronunciation_variants(["a"], strict=True)["a"])

    def test_odd_tokens_never_raise(self):
        got = sentence_pronunciation_variants(["", "--", "a b", "to"], strict=False)
        self.assertEqual((got[""], got["--"], got["a b"]), ([], [], []))
        self.assertIn(["t", "u"], got["to"])
        self.assertEqual(sentence_pronunciation_variants([], strict=False), {})


class TestCleanSentenceKeepsContractions(unittest.TestCase):
    """CMUdict knows "it's", "don't" and "didn't" but not "its"-style spellings like "dont",
    so stripping the apostrophe turned contractions into unknown words scored against
    their spelling (166 words on the speechocean762 dev half)."""

    def test_apostrophes_inside_words_stay(self):
        from core.grapheme_to_phoneme import clean_sentence
        cases = {
            "It's a dog.": "it's a dog",
            "Don't go!": "don't go",
            "He didn't see the dog's ball.": "he didn't see the dog's ball",
            "I'm here, you're there?": "i'm here you're there",
        }
        for sentence, cleaned in cases.items():
            with self.subTest(sentence=sentence):
                self.assertEqual(clean_sentence(sentence), cleaned)

    def test_curly_apostrophes_become_straight(self):
        from core.grapheme_to_phoneme import clean_sentence
        self.assertEqual(clean_sentence("It\u2019s fun. Don\u2018t stop"), "it's fun don't stop")

    def test_quotes_and_other_apostrophes_go(self):
        from core.grapheme_to_phoneme import clean_sentence
        cases = {
            "'Hello,' she said.": "hello she said",
            "The dogs' toys.": "the dogs toys",
            "Say 'cat' now": "say cat now",
            "Plain words": "plain words",
        }
        for sentence, cleaned in cases.items():
            with self.subTest(sentence=sentence):
                self.assertEqual(clean_sentence(sentence), cleaned)

    def test_contractions_get_real_pronunciations(self):
        from core.grapheme_to_phoneme import clean_sentence
        words = grapheme_to_phoneme(clean_sentence("He didn't see that it's here."), strict=False)
        self.assertEqual([w.word for w in words], ["he", "didn't", "see", "that", "it's", "here"])
        self.assertFalse(any(w.oov for w in words))
        self.assertEqual(dict(words)["didn't"], ['d', 'ɪ', 'd', 'ə', 'n', 't'])
        self.assertEqual(dict(words)["it's"], ['ɪ', 't', 's'])


if __name__ == "__main__":
    unittest.main(verbosity=2)
