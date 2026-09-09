# -*- coding: utf-8 -*-
"""Unit tests for core.phoneme_inventory (canonical IPA inventory).

Run from the ``backend/`` directory:

    PYTHONIOENCODING=utf-8 <venv>/python.exe -m unittest tests.test_phoneme_inventory -v

Pure stdlib. Imports no model, downloads nothing.
"""

import os
import sys
import unicodedata
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.phoneme_inventory import (  # noqa: E402
    CANONICAL_PHONEMES,
    CANONICAL_PHONEME_SET,
    MULTI_CHAR_TOKENS,
    NORMALIZATION_ENV_VAR,
    is_canonical,
    normalization_enabled,
    normalize_phonemes,
    normalize_word_phonemes,
    tokenize_ipa,
    unknown_symbols,
)


def levenshtein(a, b):
    """Plain phoneme-level edit distance -- the same quantity PER is built on."""
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(
                min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb))
            )
        prev = cur
    return prev[-1]


class TestLigatureEquivalence(unittest.TestCase):
    """ʧ/ʤ (single codepoint) must equal tʃ/dʒ (two codepoints)."""

    def test_ligature_ch_normalizes_to_digraph(self):
        self.assertEqual(normalize_phonemes("ʧ"), ["tʃ"])

    def test_ligature_jh_normalizes_to_digraph(self):
        self.assertEqual(normalize_phonemes("ʤ"), ["dʒ"])

    def test_church_ligature_equals_church_digraph(self):
        # 'the church judged' -> eng_to_ipa gives 'ðə ʧərʧ ʤəʤd' (ligatures).
        # A checkpoint spelling the affricates out must land in the same place.
        self.assertEqual(
            normalize_phonemes("ʧərʧ"), normalize_phonemes("tʃərtʃ")
        )
        self.assertEqual(normalize_phonemes("ʧərʧ"), ["tʃ", "ə", "r", "tʃ"])

    def test_ligature_counts_as_one_phoneme_not_two(self):
        self.assertEqual(len(normalize_phonemes("ʤəʤd")), 4)  # dʒ ə dʒ d

    def test_affricate_never_matched_before_normalization(self):
        # The bug: raw comparison of the two spellings shares zero symbols.
        legacy_gt = list("ʧərʧ")
        legacy_pred = list("tʃərtʃ")
        self.assertNotEqual(legacy_gt, legacy_pred)
        self.assertGreater(levenshtein(legacy_gt, legacy_pred), 0)
        # After normalization they are identical.
        self.assertEqual(
            levenshtein(normalize_phonemes(legacy_gt), normalize_phonemes(legacy_pred)),
            0,
        )


class TestDiphthongs(unittest.TestCase):
    """Two-codepoint diphthongs must survive as ONE token."""

    CASES = {
        "aɪ": "aɪ",
        "eɪ": "eɪ",
        "oʊ": "oʊ",
        "aʊ": "aʊ",
        "ɔɪ": "ɔɪ",
    }

    def test_each_diphthong_is_one_token(self):
        for text, expected in self.CASES.items():
            with self.subTest(text=text):
                self.assertEqual(tokenize_ipa(text), [expected])
                self.assertEqual(len(tokenize_ipa(text)), 1)

    def test_legacy_list_split_produced_two(self):
        for text in self.CASES:
            with self.subTest(text=text):
                self.assertEqual(len(list(text)), 2)  # the old behaviour

    def test_my_day_goes(self):
        # eng_to_ipa: 'my day goes' -> 'maɪ deɪ goʊz'
        self.assertEqual(tokenize_ipa("maɪ"), ["m", "aɪ"])
        self.assertEqual(tokenize_ipa("deɪ"), ["d", "eɪ"])
        self.assertEqual(tokenize_ipa("goʊz"), ["g", "oʊ", "z"])

    def test_diphthongs_are_canonical(self):
        for expected in self.CASES.values():
            self.assertTrue(is_canonical(expected))

    def test_presplit_diphthong_is_rejoined(self):
        # A sequence that already went through list(str) is repaired.
        self.assertEqual(normalize_phonemes(["m", "a", "ɪ"]), ["m", "aɪ"])

    def test_phoneme_count_is_not_inflated(self):
        legacy = list("maɪ deɪ goʊz".replace(" ", ""))
        normalized = normalize_phonemes("maɪ deɪ goʊz")
        self.assertEqual(len(legacy), 10)
        self.assertEqual(len(normalized), 7)


class TestStressAndLengthMarks(unittest.TestCase):
    def test_primary_stress_dropped(self):
        self.assertEqual(tokenize_ipa("ˈhɛloʊ"), ["h", "ɛ", "l", "oʊ"])

    def test_secondary_stress_dropped(self):
        self.assertEqual(tokenize_ipa("ˌmæn"), ["m", "æ", "n"])

    def test_stress_marks_are_not_phonemes(self):
        # The old ground-truth path only stripped ˈ and ˌ by hand; anything it
        # missed became a standalone "phoneme".
        self.assertNotIn("ˈ", tokenize_ipa("ˈhɛloʊ"))
        self.assertNotIn("ˌ", tokenize_ipa("ˌhɛloʊ"))

    def test_length_mark_attaches_then_is_stripped(self):
        self.assertEqual(tokenize_ipa("uː"), ["uː"])   # attached, not standalone
        self.assertEqual(normalize_phonemes("uː"), ["u"])
        self.assertEqual(normalize_phonemes("huːd"), ["h", "u", "d"])

    def test_length_mark_does_not_become_its_own_phoneme(self):
        self.assertEqual(len(list("huːd")), 4)             # legacy: ː counted
        self.assertEqual(len(normalize_phonemes("huːd")), 3)

    def test_length_marked_equals_unmarked(self):
        self.assertEqual(normalize_phonemes("huːd"), normalize_phonemes("hud"))

    def test_syllable_break_and_delimiters_dropped(self):
        self.assertEqual(tokenize_ipa("hɛ.loʊ"), ["h", "ɛ", "l", "oʊ"])
        self.assertEqual(tokenize_ipa("kæt*"), ["k", "æ", "t"])

    def test_leading_diacritic_with_no_previous_token_is_dropped(self):
        self.assertEqual(tokenize_ipa("ːæ"), ["æ"])


class TestUnicodeNormalization(unittest.TestCase):
    def test_nfd_input_is_folded_to_nfc(self):
        # ẽ arriving decomposed (e + combining tilde) vs precomposed.
        decomposed = "e" + "̃"
        precomposed = unicodedata.normalize("NFC", decomposed)
        self.assertNotEqual(decomposed, precomposed)
        self.assertEqual(
            normalize_phonemes(decomposed), normalize_phonemes(precomposed)
        )

    def test_nasalized_vowel_folds_to_plain_vowel(self):
        self.assertEqual(normalize_phonemes("ɑ̃"), normalize_phonemes("ɑ"))

    def test_script_g_equals_ascii_g(self):
        # IPA ɡ (U+0261) vs the ASCII g (U+0067) both sources actually emit.
        self.assertEqual(ord("ɡ"), 0x0261)
        self.assertEqual(normalize_phonemes("ɡoʊz"), normalize_phonemes("goʊz"))
        self.assertEqual(normalize_phonemes("ɡ"), ["g"])

    def test_ligatures_have_no_unicode_decomposition(self):
        # Why an explicit ALIAS_MAP is required: NFKC does NOT split ʧ into tʃ.
        self.assertEqual(unicodedata.normalize("NFKC", "ʧ"), "ʧ")
        self.assertEqual(unicodedata.normalize("NFKD", "ʤ"), "ʤ")

    def test_tokenizer_output_is_nfc(self):
        for token in tokenize_ipa("ˈtʃɜ̃rtʃ"):
            self.assertEqual(token, unicodedata.normalize("NFC", token))


class TestRhotics(unittest.TestCase):
    def test_turned_r_folds_to_plain_r(self):
        self.assertEqual(normalize_phonemes("ɹ"), ["r"])

    def test_all_rhotic_variants_agree(self):
        for sym in ("ɹ", "ɻ", "ʀ", "ʁ"):
            with self.subTest(sym=sym):
                self.assertEqual(normalize_phonemes(sym), ["r"])

    def test_r_coloured_schwa_expands_to_schwa_plus_r(self):
        # eng_to_ipa spells ARPAbet "er" as ə + r, so ɚ/ɝ must expand to match.
        self.assertEqual(normalize_phonemes("ɚ"), ["ə", "r"])
        self.assertEqual(normalize_phonemes("ɝ"), ["ə", "r"])
        self.assertEqual(normalize_phonemes("bɝd"), normalize_phonemes("bərd"))


class TestInventoryFolding(unittest.TestCase):
    def test_wedge_folds_to_schwa(self):
        # Neither eng_to_ipa nor the model vocab contains ʌ, but fixtures do.
        self.assertNotIn("ʌ", CANONICAL_PHONEME_SET)
        self.assertEqual(normalize_phonemes("ʌ"), ["ə"])

    def test_folding_can_be_disabled(self):
        self.assertEqual(normalize_phonemes("ʌ", fold_inventory=False), ["ʌ"])
        # Alias rewrites still apply with folding off -- they are notation only.
        self.assertEqual(normalize_phonemes("ʧ", fold_inventory=False), ["tʃ"])

    def test_every_canonical_symbol_is_a_fixed_point(self):
        for token in CANONICAL_PHONEMES:
            with self.subTest(token=token):
                self.assertEqual(normalize_phonemes(token), [token])

    def test_normalize_is_idempotent(self):
        for text in ("ʧərʧ", "maɪ", "huːd", "ˈhɛloʊ", "bɝd", "ʌv"):
            once = normalize_phonemes(text)
            with self.subTest(text=text):
                self.assertEqual(normalize_phonemes(once), once)


class TestFeatureFlag(unittest.TestCase):
    def setUp(self):
        self._saved = os.environ.get(NORMALIZATION_ENV_VAR)

    def tearDown(self):
        if self._saved is None:
            os.environ.pop(NORMALIZATION_ENV_VAR, None)
        else:
            os.environ[NORMALIZATION_ENV_VAR] = self._saved

    def test_default_is_off(self):
        os.environ.pop(NORMALIZATION_ENV_VAR, None)
        self.assertFalse(normalization_enabled())

    def test_truthy_values(self):
        for value in ("1", "true", "TRUE", "yes", "on", "Y"):
            with self.subTest(value=value):
                os.environ[NORMALIZATION_ENV_VAR] = value
                self.assertTrue(normalization_enabled())

    def test_falsy_values(self):
        for value in ("", "0", "false", "no", "off", "banana"):
            with self.subTest(value=value):
                os.environ[NORMALIZATION_ENV_VAR] = value
                self.assertFalse(normalization_enabled())


class TestExtractorWiring(unittest.TestCase):
    """default_model_output_processing must be unchanged with the flag unset.

    Reproduces the function body rather than importing phoneme_extractor_onnx,
    which pulls in onnxruntime/transformers (slow, and unnecessary here). The
    duplication is checked against the real source file below.
    """

    def _process(self, transcription):
        import re

        filtered = re.split(r" ", transcription[0])
        words = [w for w in filtered if w != ""]
        if normalization_enabled():
            normalized = [normalize_phonemes(w) for w in words]
            return [w for w in normalized if w]
        return [list(w.replace("ˈ", "")) for w in words]

    def setUp(self):
        self._saved = os.environ.get(NORMALIZATION_ENV_VAR)
        os.environ.pop(NORMALIZATION_ENV_VAR, None)

    def tearDown(self):
        if self._saved is None:
            os.environ.pop(NORMALIZATION_ENV_VAR, None)
        else:
            os.environ[NORMALIZATION_ENV_VAR] = self._saved

    def test_flag_off_is_legacy_behaviour(self):
        out = self._process(["ðə kæt sæt"])
        self.assertEqual(out, [["ð", "ə"], ["k", "æ", "t"], ["s", "æ", "t"]])

    def test_flag_off_still_splits_diphthongs(self):
        self.assertEqual(self._process(["maɪ"]), [["m", "a", "ɪ"]])

    def test_flag_on_keeps_diphthongs_whole(self):
        os.environ[NORMALIZATION_ENV_VAR] = "true"
        self.assertEqual(self._process(["maɪ"]), [["m", "aɪ"]])

    def test_source_file_matches_this_reproduction(self):
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "core",
            "phoneme_extractor_onnx.py",
        )
        with open(path, encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn("if normalization_enabled():", src)
        self.assertIn("[normalize_phonemes(word) for word in words]", src)
        self.assertIn('[list(word.replace("ˈ", "")) for word in words]', src)


class TestRoundTripScoring(unittest.TestCase):
    """A correct pronunciation must score 0 errors after normalization."""

    def test_church_scores_zero_after_normalization(self):
        # Ground truth: eng_to_ipa('the church judged') == 'ðə ʧərʧ ʤəʤd'
        ground_truth = ["ðə", "ʧərʧ", "ʤəʤd"]
        # Prediction from a checkpoint that spells the affricates out. Same
        # pronunciation, different notation.
        predicted = ["ðə", "tʃərtʃ", "dʒədʒd"]

        legacy_errors = sum(
            levenshtein(list(g), list(p)) for g, p in zip(ground_truth, predicted)
        )
        legacy_total = sum(len(list(g)) for g in ground_truth)
        # Every affricate reads as an error, and the digraph spelling also adds
        # an insertion: a perfect reading scores PER 0.8.
        self.assertEqual(legacy_errors, 8)
        self.assertEqual(legacy_total, 10)
        self.assertAlmostEqual(legacy_errors / legacy_total, 0.8)

        norm_errors = sum(
            levenshtein(normalize_phonemes(g), normalize_phonemes(p))
            for g, p in zip(ground_truth, predicted)
        )
        norm_total = sum(len(normalize_phonemes(g)) for g in ground_truth)
        self.assertEqual(norm_errors, 0)
        self.assertEqual(norm_total, 10)

    def test_diphthong_word_denominator_is_correct(self):
        # 'my day goes' read perfectly.
        ground_truth = ["maɪ", "deɪ", "goʊz"]
        predicted = ["maɪ", "deɪ", "goʊz"]
        self.assertEqual(sum(len(list(g)) for g in ground_truth), 10)  # inflated
        self.assertEqual(
            sum(len(normalize_phonemes(g)) for g in ground_truth), 7
        )
        self.assertEqual(
            sum(
                levenshtein(normalize_phonemes(g), normalize_phonemes(p))
                for g, p in zip(ground_truth, predicted)
            ),
            0,
        )

    def test_one_real_error_counts_once_not_twice(self):
        # Child says "my" as "muh": aɪ -> ə. ONE substitution.
        gt, pred = "maɪ", "mə"
        self.assertEqual(levenshtein(list(gt), list(pred)), 2)  # legacy: 2 errors
        self.assertEqual(
            levenshtein(normalize_phonemes(gt), normalize_phonemes(pred)), 1
        )
        self.assertAlmostEqual(
            levenshtein(normalize_phonemes(gt), normalize_phonemes(pred))
            / len(normalize_phonemes(gt)),
            0.5,
        )

    def test_stress_marked_ground_truth_scores_zero(self):
        self.assertEqual(
            levenshtein(
                normalize_phonemes("ˈhɛˌloʊ"), normalize_phonemes("hɛloʊ")
            ),
            0,
        )


class TestMiscApi(unittest.TestCase):
    def test_empty_inputs(self):
        self.assertEqual(tokenize_ipa(""), [])
        self.assertEqual(tokenize_ipa(None), [])
        self.assertEqual(normalize_phonemes(None), [])
        self.assertEqual(normalize_phonemes([]), [])
        self.assertEqual(normalize_word_phonemes([]), [])

    def test_normalize_word_phonemes(self):
        self.assertEqual(
            normalize_word_phonemes([["ð", "ə"], ["m", "a", "ɪ"]]),
            [["ð", "ə"], ["m", "aɪ"]],
        )

    def test_multi_char_tokens_are_all_two_codepoints(self):
        for token in MULTI_CHAR_TOKENS:
            self.assertEqual(len(token), 2, token)

    def test_unknown_symbols_flags_non_ipa_letters(self):
        self.assertEqual(unknown_symbols("kæt"), [])
        self.assertEqual(unknown_symbols("qx"), ["q", "x"])

    def test_unknown_symbols_is_only_a_weak_oov_signal(self):
        # Documented limitation: OOV spellings made of IPA-valid letters pass.
        self.assertEqual(unknown_symbols(list("wordwiz")), [])

    def test_module_imports_no_heavy_dependencies(self):
        for mod in ("numpy", "torch", "transformers", "onnxruntime"):
            self.assertNotIn(mod, sys.modules.get("core.phoneme_inventory").__dict__)


if __name__ == "__main__":
    unittest.main(verbosity=2)
