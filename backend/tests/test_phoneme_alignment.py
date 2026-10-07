"""
Tests for the per-phoneme ``phoneme_alignment`` field on word records.

Run with (from the ``backend`` directory):

    PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.test_phoneme_alignment -v

No network, no models, no audio -- every fixture is hand written IPA.
"""

import os
import sys
import unittest

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from core.gt_alignment import align_sequences, phoneme_alignment_records  # noqa: E402


def op(type_, expected, actual):
    return {"type": type_, "expected": expected, "actual": actual}


class TestPhonemeAlignmentRecords(unittest.TestCase):

    def test_clean_word_is_all_matches(self):
        ops = align_sequences(['k', 'æ', 't'], ['k', 'æ', 't'])
        self.assertEqual(phoneme_alignment_records(ops), [
            op("match", "k", "k"), op("match", "æ", "æ"), op("match", "t", "t"),
        ])

    def test_substitution_keeps_its_position(self):
        ops = align_sequences(['k', 'æ', 't'], ['k', 'ɛ', 't'])
        self.assertEqual(phoneme_alignment_records(ops), [
            op("match", "k", "k"), op("substitution", "æ", "ɛ"), op("match", "t", "t"),
        ])

    def test_missed_phoneme_is_a_deletion_with_no_actual(self):
        ops = align_sequences(['k', 'æ', 't'], ['k', 't'])
        self.assertEqual(phoneme_alignment_records(ops), [
            op("match", "k", "k"), op("deletion", "æ", None), op("match", "t", "t"),
        ])

    def test_added_phoneme_is_an_insertion_with_no_expected(self):
        ops = align_sequences(['k', 'æ', 't'], ['k', 'æ', 't', 's'])
        self.assertEqual(phoneme_alignment_records(ops), [
            op("match", "k", "k"), op("match", "æ", "æ"), op("match", "t", "t"),
            op("insertion", None, "s"),
        ])

    def test_empty_inputs(self):
        self.assertEqual(phoneme_alignment_records(align_sequences([], [])), [])
        self.assertEqual(
            phoneme_alignment_records(align_sequences(['ð', 'ə'], [])),
            [op("deletion", "ð", None), op("deletion", "ə", None)],
        )
        self.assertEqual(
            phoneme_alignment_records(align_sequences([], ['b', 'ɪ'])),
            [op("insertion", None, "b"), op("insertion", None, "ɪ")],
        )


THE = ('the', ['ð', 'ə'])
CAT = ('cat', ['k', 'æ', 't'])
SAT = ('sat', ['s', 'æ', 't'])
ON = ('on', ['ɑ', 'n'])
MAT = ('mat', ['m', 'æ', 't'])
GT_SHORT = [THE, CAT, SAT]
GT_LONG = [THE, CAT, SAT, ON, THE, MAT]


class AlignmentAgreesMixin:

    def assert_alignment_agrees(self, record):
        """The ordered list holds exactly the errors the unordered buckets do."""
        pa = record["phoneme_alignment"]
        self.assertIsInstance(pa, list)
        for entry in pa:
            self.assertEqual(set(entry), {"type", "expected", "actual"})
            self.assertIn(entry["type"], {"match", "substitution", "deletion", "insertion"})
        self.assertEqual(
            [e["expected"] for e in pa if e["type"] == "deletion"], list(record["missed"]))
        self.assertEqual(
            [e["actual"] for e in pa if e["type"] == "insertion"], list(record["added"]))
        self.assertEqual(
            [(e["expected"], e["actual"]) for e in pa if e["type"] == "substitution"],
            [tuple(s) for s in record["substituted"]])
        if record["type"] != "insertion":
            self.assertEqual(
                sum(e["type"] != "match" for e in pa), record["total_errors"])


class TestLegacyPath(AlignmentAgreesMixin, unittest.TestCase):
    """process_audio._process_word_alignment, the default path."""

    def run_alignment(self, predicted_words, phoneme_predictions):
        from core.process_audio import _process_word_alignment
        return _process_word_alignment(
            ground_truth_words=[w for w, _ in GT_SHORT],
            ground_truth_phonemes=GT_SHORT,
            predicted_words=predicted_words,
            phoneme_predictions=phoneme_predictions,
        )

    def test_errors_inside_words_are_ordered(self):
        results = self.run_alignment(
            ['the', 'cat', 'sat'], [['ð', 'ə'], ['k', 'ɛ', 't'], ['s', 'æ']])
        cat, sat = results[1], results[2]
        self.assertEqual(cat["phoneme_alignment"], [
            op("match", "k", "k"), op("substitution", "æ", "ɛ"), op("match", "t", "t"),
        ])
        self.assertEqual(sat["phoneme_alignment"], [
            op("match", "s", "s"), op("match", "æ", "æ"), op("deletion", "t", None),
        ])
        for r in results:
            self.assert_alignment_agrees(r)

    def test_skipped_word_is_all_deletions(self):
        results = self.run_alignment(['the', 'sat'], [['ð', 'ə'], ['s', 'æ', 't']])
        cat = [r for r in results if r["ground_truth_word"] == "cat"][0]
        self.assertEqual(cat["type"], "deletion")
        self.assertEqual(cat["phoneme_alignment"], [
            op("deletion", "k", None), op("deletion", "æ", None), op("deletion", "t", None),
        ])
        for r in results:
            self.assert_alignment_agrees(r)

    def test_extra_word_is_all_insertions(self):
        results = self.run_alignment(
            ['the', 'big', 'cat', 'sat'],
            [['ð', 'ə'], ['b', 'ɪ', 'g'], ['k', 'æ', 't'], ['s', 'æ', 't']])
        big = [r for r in results if r["type"] == "insertion"][0]
        self.assertEqual(big["phoneme_alignment"], [
            op("insertion", None, "b"), op("insertion", None, "ɪ"), op("insertion", None, "g"),
        ])
        for r in results:
            self.assert_alignment_agrees(r)


class TestGroundTruthAnchoredPath(AlignmentAgreesMixin, unittest.TestCase):
    """gt_alignment.align_to_ground_truth, behind WWAI_GT_ANCHORED_ALIGNMENT."""

    def test_every_record_type_carries_an_agreeing_alignment(self):
        # "the cat sat on the mat" read as "the tat sat on the", plus a
        # spurious ASR word: all four record types in one result set.
        from core.gt_alignment import align_to_ground_truth
        flat = ['ð', 'ə', 't', 'æ', 't', 's', 'æ', 't', 'ɑ', 'n', 'ð', 'ə']
        asr = ['the', 'cat', 'sat', 'on', 'the', 'mat', 'now']
        results = align_to_ground_truth(flat, GT_LONG, asr)
        self.assertEqual(
            {r["type"] for r in results}, {"match", "substitution", "deletion", "insertion"})
        for r in results:
            self.assert_alignment_agrees(r)

        cat = [r for r in results if r["ground_truth_word"] == "cat"][0]
        self.assertEqual(cat["phoneme_alignment"], [
            op("substitution", "k", "t"), op("match", "æ", "æ"), op("match", "t", "t"),
        ])
        mat = [r for r in results if r["ground_truth_word"] == "mat"][0]
        self.assertEqual(mat["type"], "deletion")
        self.assertEqual(
            [e["type"] for e in mat["phoneme_alignment"]], ["deletion"] * 3)
        extra = [r for r in results if r["type"] == "insertion"][0]
        self.assertEqual(extra["phoneme_alignment"], [])


if __name__ == "__main__":
    unittest.main()
