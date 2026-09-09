# -*- coding: utf-8 -*-
"""
Tests for phonetically weighted PER (WWAI_WEIGHTED_PER) and core/phonetic_distance.py.

Run from the `backend/` directory:

    PYTHONIOENCODING=utf-8 <venv>/python.exe -m unittest tests.test_weighted_per -v

The single most important test here is `TestFlagOffRegression` — with the flag
unset, compute_per must be bit-identical to the original unweighted
implementation. Everything else is new behaviour behind the flag.
"""

import os
import random
import sys
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from core import process_audio
from core.process_audio import compute_per
from core.phonetic_distance import (
    ALLOWED_VARIATIONS,
    PHONEME_FEATURES,
    allowed_variation_report,
    deletion_cost,
    insertion_cost,
    normalize_phoneme_sequence,
    phonetic_distance,
)


def reference_compute_per(gt_phonemes, pred_phonemes):
    """Verbatim copy of the ORIGINAL unweighted compute_per, kept here as a
    frozen oracle so a future refactor of the real one cannot silently drift."""
    if not gt_phonemes and not pred_phonemes:
        return 0.0
    if not gt_phonemes:
        return 1.0
    if not pred_phonemes:
        return 1.0

    m, n = len(gt_phonemes), len(pred_phonemes)

    if gt_phonemes == pred_phonemes:
        return 0.0

    dp = np.zeros((m + 1, n + 1), dtype=np.uint16)
    for i in range(m + 1):
        dp[i, 0] = i
    for j in range(n + 1):
        dp[0, j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if gt_phonemes[i - 1] == pred_phonemes[j - 1]:
                dp[i, j] = dp[i - 1, j - 1]
            else:
                dp[i, j] = 1 + min(dp[i - 1, j], dp[i, j - 1], dp[i - 1, j - 1])
    return dp[m, n] / max(m, 1)


INVENTORY = [
    "p", "b", "t", "d", "k", "g", "f", "v", "θ", "ð", "s", "z", "ʃ", "ʒ",
    "h", "m", "n", "ŋ", "l", "ɹ", "j", "w", "ɾ", "ʔ",
    "i", "ɪ", "e", "ɛ", "æ", "ə", "ʌ", "ɑ", "ɔ", "o", "ʊ", "u", "ɚ", "ɝ",
]

# "The cat sat on the mat and the dog ran after it." — a plausible practice
# sentence, ground truth flattened the way align_phonemes_to_words sees it.
SENTENCE_GT = [
    "ð", "ə", "k", "æ", "t", "s", "æ", "t", "ɔ", "n", "ð", "ə", "m", "æ", "t",
    "æ", "n", "d", "ð", "ə", "d", "ɔ", "g", "ɹ", "æ", "n", "æ", "f", "t", "ə",
    "ɹ", "ɪ", "t",
]
# Same sentence as a real extractor tends to render it: flapped /t/, reduced
# vowels, a dropped final stop, a stray glottal stop.
SENTENCE_PRED = [
    "ð", "ə", "k", "æ", "t", "s", "æ", "ɾ", "ɔ", "n", "ð", "ə", "m", "æ", "t",
    "ə", "n", "ʔ", "ð", "ə", "d", "ɔ", "g", "ɹ", "æ", "n", "æ", "f", "t", "ɚ",
    "ɪ", "t",
]


class FlagSwitch(unittest.TestCase):
    """Base class that always restores the flag, whatever the test does."""

    def setUp(self):
        self._saved = process_audio._WEIGHTED_PER

    def tearDown(self):
        process_audio.set_weighted_per(self._saved)


class TestFlagOffRegression(FlagSwitch):
    """THE critical guard: flag off => identical to the original behaviour."""

    def test_default_is_off(self):
        self.assertFalse(
            process_audio._WEIGHTED_PER,
            "WWAI_WEIGHTED_PER must default to OFF; env var was %r"
            % os.getenv("WWAI_WEIGHTED_PER"),
        )

    def test_flag_off_matches_reference_exactly(self):
        process_audio.set_weighted_per(False)
        rng = random.Random(20240917)
        cases = [
            ([], []),
            ([], ["k"]),
            (["k"], []),
            (["k", "æ", "t"], ["k", "æ", "t"]),
            (["k", "æ", "t"], ["b", "æ", "t"]),
            (["w", "ɔ", "t", "ə", "ɹ"], ["w", "ɔ", "ɾ", "ɚ"]),
            (SENTENCE_GT, SENTENCE_PRED),
        ]
        for _ in range(500):
            m = rng.randint(0, 9)
            n = rng.randint(0, 9)
            cases.append(
                (
                    [rng.choice(INVENTORY) for _ in range(m)],
                    [rng.choice(INVENTORY) for _ in range(n)],
                )
            )

        for gt, pred in cases:
            with self.subTest(gt=gt, pred=pred):
                self.assertEqual(
                    float(compute_per(gt, pred)),
                    float(reference_compute_per(gt, pred)),
                    "unweighted path drifted from the frozen reference",
                )

    def test_flag_off_still_lets_per_exceed_one(self):
        """Documents the pre-existing behaviour we deliberately did NOT change
        when the flag is off: insertions divide by len(gt) only."""
        process_audio.set_weighted_per(False)
        per = compute_per(["k"], ["k", "æ", "t", "s", "ə", "p"])
        self.assertGreater(per, 1.0)


class TestAllophonicVariationIsForgiven(FlagSwitch):

    def _weighted(self, gt, pred):
        process_audio.set_weighted_per(True)
        return compute_per(gt, pred)

    def _unweighted(self, gt, pred):
        process_audio.set_weighted_per(False)
        return compute_per(gt, pred)

    def test_water_with_flap_and_r_coloring(self):
        gt = ["w", "ɔ", "t", "ə", "ɹ"]      # "water" as the g2p writes it
        pred = ["w", "ɔ", "ɾ", "ɚ"]         # "water" as an American says it
        w = self._weighted(gt, pred)
        u = self._unweighted(gt, pred)
        self.assertAlmostEqual(w, 0.0, places=6, msg="flapped 'water' should be free")
        self.assertGreater(u, 0.5, "sanity: today this is scored as a bad error")

    def test_unreleased_final_stop(self):
        gt = ["k", "æ", "t"]
        pred = ["k", "æ"]                    # release not audible / not emitted
        w = self._weighted(gt, pred)
        u = self._unweighted(gt, pred)
        self.assertLess(w, 0.06)
        self.assertAlmostEqual(u, 1.0 / 3.0, places=6)

    def test_schwa_reduction(self):
        gt = ["ɹ", "oʊ", "z", "ə", "z"]
        pred = ["ɹ", "oʊ", "z", "ɪ", "z"]
        self.assertAlmostEqual(self._weighted(gt, pred), 0.0, places=6)
        self.assertGreater(self._unweighted(gt, pred), 0.0)

    def test_ligature_vs_two_character_affricate(self):
        gt = ["ʧ", "ɝ", "ʧ"]                 # eng_to_ipa ligatures
        pred = ["tʃ", "ɝ", "tʃ"]             # model's two-character form
        self.assertAlmostEqual(self._weighted(gt, pred), 0.0, places=6)
        self.assertAlmostEqual(self._unweighted(gt, pred), 2.0 / 3.0, places=6)

    def test_genuine_substitution_still_penalised(self):
        gt = ["k", "æ", "t"]
        pred = ["b", "æ", "t"]               # a real decoding error
        w = self._weighted(gt, pred)
        allophonic = self._weighted(["w", "ɔ", "t", "ə", "ɹ"], ["w", "ɔ", "ɾ", "ɚ"])
        self.assertGreater(phonetic_distance("k", "b"), 0.4)
        self.assertGreater(w, 0.1)
        self.assertGreater(w, allophonic + 0.1)

    def test_weighted_per_is_clamped_to_one(self):
        process_audio.set_weighted_per(True)
        per = compute_per(["k"], ["k", "æ", "t", "s", "ə", "p", "m", "u"])
        self.assertLessEqual(per, 1.0)
        process_audio.set_weighted_per(False)
        self.assertGreater(compute_per(["k"], ["k", "æ", "t", "s", "ə", "p", "m", "u"]), 1.0)

    def test_totally_wrong_word_still_scores_high(self):
        """A featural metric compresses the top of the range (any two English
        consonants share most of their features), so a completely wrong word
        lands near 0.5 rather than the unweighted 1.0. It must still be clearly
        in 'this was wrong' territory — see the residual-risk note about
        re-calibrating downstream thresholds before enabling the flag."""
        process_audio.set_weighted_per(True)
        per = compute_per(["k", "æ", "t"], ["h", "aʊ", "s"])
        self.assertGreater(per, 0.4)
        good = compute_per(["k", "æ", "t"], ["k", "æ"])
        self.assertGreater(per, 5 * good)


class TestPhoneticDistance(unittest.TestCase):

    def test_identity(self):
        for p in INVENTORY:
            self.assertEqual(phonetic_distance(p, p), 0.0)

    def test_symmetry_and_range(self):
        symbols = list(PHONEME_FEATURES.keys())
        for a in symbols:
            for b in symbols:
                d = phonetic_distance(a, b)
                self.assertGreaterEqual(d, 0.0, (a, b))
                self.assertLessEqual(d, 1.0, (a, b))
                self.assertEqual(d, phonetic_distance(b, a), (a, b))

    def test_voicing_only_is_far_cheaper_than_place_or_class(self):
        pb = phonetic_distance("p", "b")
        pk = phonetic_distance("p", "k")
        pi = phonetic_distance("p", "i")
        self.assertLess(pb, pk)
        self.assertLess(pk, pi)
        self.assertGreater(pk, 3 * pb)
        self.assertEqual(pi, 1.0)

    def test_near_miss_beats_far_miss(self):
        pairs_near_far = [
            (("i", "ɪ"), ("i", "ɑ")),      # adjacent vs opposite corner vowel
            (("s", "z"), ("s", "k")),      # voicing vs place+manner
            (("m", "n"), ("m", "k")),      # nasal place vs class change
            (("t", "d"), ("t", "l")),      # voicing vs manner
            (("ʃ", "ʒ"), ("ʃ", "p")),
        ]
        for near, far in pairs_near_far:
            with self.subTest(near=near, far=far):
                self.assertLess(
                    phonetic_distance(*near),
                    phonetic_distance(*far),
                    "%s should be closer than %s" % (near, far),
                )

    def test_unknown_symbols_are_conservative(self):
        # OOV ground truth leaks raw spelling letters into the phoneme list.
        self.assertEqual(phonetic_distance("q", "k"), 1.0)
        self.assertEqual(phonetic_distance("q", "q"), 0.0)

    def test_allowed_variation_table_is_auditable(self):
        rows = allowed_variation_report()
        self.assertGreaterEqual(len(rows), 20)
        for a, b, cost, why in rows:
            with self.subTest(pair=(a, b)):
                self.assertLessEqual(cost, 0.10, "an 'allowed' pair must be near free")
                self.assertGreaterEqual(cost, 0.0)
                self.assertGreater(len(why), 30, "every entry needs a justification")
                self.assertIn(a, PHONEME_FEATURES)
                self.assertIn(b, PHONEME_FEATURES)

    def test_named_allowed_variations_are_present(self):
        for a, b in [("t", "ɾ"), ("d", "ɾ"), ("ə", "ɪ"), ("ɪ", "ᵻ"),
                     ("ɚ", "ɝ"), ("ə", "ʌ"), ("ʧ", "tʃ")]:
            with self.subTest(pair=(a, b)):
                self.assertIn(frozenset((a, b)), ALLOWED_VARIATIONS)
                self.assertLessEqual(phonetic_distance(a, b), 0.05)

    def test_deletion_and_insertion_costs(self):
        self.assertEqual(deletion_cost("t", is_final=False), 1.0)
        self.assertLess(deletion_cost("t", is_final=True), 0.2)
        self.assertEqual(deletion_cost("s", is_final=True), 1.0)
        self.assertEqual(insertion_cost("k"), 1.0)
        self.assertLess(insertion_cost("ʔ"), 0.2)

    def test_sequence_normalisation(self):
        self.assertEqual(normalize_phoneme_sequence(["b", "ə", "ɹ"]), ["b", "ɚ"])
        self.assertEqual(normalize_phoneme_sequence(["b", "ɚ"]), ["b", "ɚ"])
        self.assertEqual(normalize_phoneme_sequence(["ɹ", "æ", "n"]), ["ɹ", "æ", "n"])
        self.assertEqual(normalize_phoneme_sequence([]), [])


class TestPerformance(FlagSwitch):
    """compute_per sits in the DP inner loop of align_phonemes_to_words, so the
    weighted variant must not be dramatically slower."""

    def _time(self, enabled, pairs, reps):
        process_audio.set_weighted_per(enabled)
        compute_per(pairs[0][0], pairs[0][1])  # warm the memo cache
        start = time.perf_counter()
        for _ in range(reps):
            for gt, pred in pairs:
                compute_per(gt, pred)
        return time.perf_counter() - start

    def test_weighted_is_not_dramatically_slower(self):
        word_pairs = [
            (["ð", "ə"], ["ð", "ə"]),
            (["k", "æ", "t"], ["k", "æ", "t"]),
            (["s", "æ", "t"], ["s", "æ", "ɾ"]),
            (["æ", "f", "t", "ə", "ɹ"], ["æ", "f", "t", "ɚ"]),
            (SENTENCE_GT, SENTENCE_PRED),
        ]
        reps = 300
        u = self._time(False, word_pairs, reps)
        w = self._time(True, word_pairs, reps)
        calls = reps * len(word_pairs)
        print(
            "\n[perf] %d compute_per calls (4 word-sized + 1 %d-phoneme sentence each rep)"
            % (calls, len(SENTENCE_GT))
        )
        print("[perf]   unweighted : %.4f s  (%.1f us/call)" % (u, u / calls * 1e6))
        print("[perf]   weighted   : %.4f s  (%.1f us/call)" % (w, w / calls * 1e6))
        print("[perf]   ratio weighted/unweighted : %.2fx" % (w / u))
        self.assertLess(w, u * 3.0, "weighted PER is more than 3x slower")


if __name__ == "__main__":
    unittest.main(verbosity=2)
