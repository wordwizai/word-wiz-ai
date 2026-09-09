"""
Tests for client-path phoneme realignment + index safety in
`backend/core/process_audio.py`.

Covers two changes:

1. `_process_word_alignment` bounds safety (always on -- crash prevention only).
   The four input lists come from separate upstream stages and are not guaranteed
   to be the same length. Previously `phoneme_predictions[pred_idx]` raised
   IndexError, which surfaced to a child as "AI processing failed: list index out
   of range".

2. `process_audio_with_client_phonemes` optional realignment behind the
   `WWAI_CLIENT_REALIGN` env flag (default OFF). When enabled, the flat client
   phoneme stream is re-segmented against `g2p(" ".join(predicted_words))` using
   the same `align_phonemes_to_words` step the server path uses.

No network, no models: `client_words` is always supplied so word extraction (and
therefore audio preprocessing) is skipped entirely, and `g2p` uses the local
`eng_to_ipa` dictionary.

Run with:
    cd backend
    PYTHONIOENCODING=utf-8 python -m unittest tests.test_client_realign_and_index_safety -v
"""

import asyncio
import json
import os
import sys
import unittest

# Add backend to path
backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from core.process_audio import (  # noqa: E402
    _process_word_alignment,
    process_audio_with_client_phonemes,
)

FLAG = "WWAI_CLIENT_REALIGN"

# --- Fixtures ---------------------------------------------------------------

GT = [("the", ["ð", "ə"]), ("cat", ["k", "æ", "t"]), ("sat", ["s", "æ", "t"])]
GT_WORDS = [w for w, _ in GT]
PRED_WORDS = ["the", "cat", "sat"]
PRED_PH = [["ð", "ə"], ["k", "æ", "t"], ["s", "æ", "t"]]

# Golden outputs captured by running the ORIGINAL (pre-fix) code at commit
# 4cc29aa on these exact inputs. Any diff here is a behavioral regression.
GOLDEN = json.loads(r"""
{"exact_match":[{"type":"match","predicted_word":"the","ground_truth_word":"the","phonemes":["ð","ə"],"ground_truth_phonemes":["ð","ə"],"expected_phonemes":["ð","ə"],"actual_phonemes":["ð","ə"],"per":0.0,"missed":[],"added":[],"substituted":[],"total_phonemes":2,"total_errors":0},{"type":"match","predicted_word":"cat","ground_truth_word":"cat","phonemes":["k","æ","t"],"ground_truth_phonemes":["k","æ","t"],"expected_phonemes":["k","æ","t"],"actual_phonemes":["k","æ","t"],"per":0.0,"missed":[],"added":[],"substituted":[],"total_phonemes":3,"total_errors":0},{"type":"match","predicted_word":"sat","ground_truth_word":"sat","phonemes":["s","æ","t"],"ground_truth_phonemes":["s","æ","t"],"expected_phonemes":["s","æ","t"],"actual_phonemes":["s","æ","t"],"per":0.0,"missed":[],"added":[],"substituted":[],"total_phonemes":3,"total_errors":0}],
 "substitution":[{"type":"match","predicted_word":"the","ground_truth_word":"the","phonemes":["ð","ə"],"ground_truth_phonemes":["ð","ə"],"expected_phonemes":["ð","ə"],"actual_phonemes":["ð","ə"],"per":0.0,"missed":[],"added":[],"substituted":[],"total_phonemes":2,"total_errors":0},{"type":"substitution","predicted_word":"cot","ground_truth_word":"cat","phonemes":["k","ɑ","t"],"ground_truth_phonemes":["k","æ","t"],"expected_phonemes":["k","æ","t"],"actual_phonemes":["k","ɑ","t"],"per":0.3333,"missed":[],"added":[],"substituted":[["æ","ɑ"]],"total_phonemes":3,"total_errors":1},{"type":"match","predicted_word":"sat","ground_truth_word":"sat","phonemes":["s","æ","t"],"ground_truth_phonemes":["s","æ","t"],"expected_phonemes":["s","æ","t"],"actual_phonemes":["s","æ","t"],"per":0.0,"missed":[],"added":[],"substituted":[],"total_phonemes":3,"total_errors":0}],
 "insertion":[{"type":"match","predicted_word":"the","ground_truth_word":"the","phonemes":["ð","ə"],"ground_truth_phonemes":["ð","ə"],"expected_phonemes":["ð","ə"],"actual_phonemes":["ð","ə"],"per":0.0,"missed":[],"added":[],"substituted":[],"total_phonemes":2,"total_errors":0},{"type":"match","predicted_word":"cat","ground_truth_word":"cat","phonemes":["k","æ","t"],"ground_truth_phonemes":["k","æ","t"],"expected_phonemes":["k","æ","t"],"actual_phonemes":["k","æ","t"],"per":0.0,"missed":[],"added":[],"substituted":[],"total_phonemes":3,"total_errors":0},{"type":"match","predicted_word":"sat","ground_truth_word":"sat","phonemes":["s","æ","t"],"ground_truth_phonemes":["s","æ","t"],"expected_phonemes":["s","æ","t"],"actual_phonemes":["s","æ","t"],"per":0.0,"missed":[],"added":[],"substituted":[],"total_phonemes":3,"total_errors":0},{"type":"insertion","predicted_word":"down","ground_truth_word":"","phonemes":["d","a","ʊ","n"],"ground_truth_phonemes":[],"expected_phonemes":[],"actual_phonemes":["d","a","ʊ","n"],"per":0.0,"missed":[],"added":["d","a","ʊ","n"],"substituted":[],"total_phonemes":0,"total_errors":0,"error":"Extra word predicted."}],
 "deletion":[{"type":"match","predicted_word":"the","ground_truth_word":"the","phonemes":["ð","ə"],"ground_truth_phonemes":["ð","ə"],"expected_phonemes":["ð","ə"],"actual_phonemes":["ð","ə"],"per":0.0,"missed":[],"added":[],"substituted":[],"total_phonemes":2,"total_errors":0},{"type":"deletion","predicted_word":"","ground_truth_word":"cat","phonemes":[],"ground_truth_phonemes":["k","æ","t"],"expected_phonemes":["k","æ","t"],"actual_phonemes":[],"per":1.0,"missed":["k","æ","t"],"added":[],"substituted":[],"total_phonemes":3,"total_errors":3,"error":"Word missing in prediction."},{"type":"match","predicted_word":"sat","ground_truth_word":"sat","phonemes":["s","æ","t"],"ground_truth_phonemes":["s","æ","t"],"expected_phonemes":["s","æ","t"],"actual_phonemes":["s","æ","t"],"per":0.0,"missed":[],"added":[],"substituted":[],"total_phonemes":3,"total_errors":0}],
 "client_exact":[{"type":"match","predicted_word":"the","ground_truth_word":"the","phonemes":["ð","ə"],"ground_truth_phonemes":["ð","ə"],"expected_phonemes":["ð","ə"],"actual_phonemes":["ð","ə"],"per":0.0,"missed":[],"added":[],"substituted":[],"total_phonemes":2,"total_errors":0},{"type":"match","predicted_word":"cat","ground_truth_word":"cat","phonemes":["k","æ","t"],"ground_truth_phonemes":["k","æ","t"],"expected_phonemes":["k","æ","t"],"actual_phonemes":["k","æ","t"],"per":0.0,"missed":[],"added":[],"substituted":[],"total_phonemes":3,"total_errors":0},{"type":"match","predicted_word":"sat","ground_truth_word":"sat","phonemes":["s","æ","t"],"ground_truth_phonemes":["s","æ","t"],"expected_phonemes":["s","æ","t"],"actual_phonemes":["s","æ","t"],"per":0.0,"missed":[],"added":[],"substituted":[],"total_phonemes":3,"total_errors":0}],
 "client_more_groups":[{"type":"match","predicted_word":"the","ground_truth_word":"the","phonemes":["ð","ə"],"ground_truth_phonemes":["ð","ə"],"expected_phonemes":["ð","ə"],"actual_phonemes":["ð","ə"],"per":0.0,"missed":[],"added":[],"substituted":[],"total_phonemes":2,"total_errors":0},{"type":"match","predicted_word":"cat","ground_truth_word":"cat","phonemes":["k","æ"],"ground_truth_phonemes":["k","æ","t"],"expected_phonemes":["k","æ","t"],"actual_phonemes":["k","æ"],"per":0.3333,"missed":["t"],"added":[],"substituted":[],"total_phonemes":3,"total_errors":1},{"type":"match","predicted_word":"sat","ground_truth_word":"sat","phonemes":["t"],"ground_truth_phonemes":["s","æ","t"],"expected_phonemes":["s","æ","t"],"actual_phonemes":["t"],"per":0.6667,"missed":["s","æ"],"added":[],"substituted":[],"total_phonemes":3,"total_errors":2}]}
""")


def normalize(results):
    """JSON round-trip so tuples/lists compare equal against the stored golden."""
    return json.loads(json.dumps(results, ensure_ascii=False))


class _FlagMixin(unittest.TestCase):
    """Save/restore WWAI_CLIENT_REALIGN so tests never leak env state."""

    def setUp(self):
        self._saved_flag = os.environ.pop(FLAG, None)

    def tearDown(self):
        os.environ.pop(FLAG, None)
        if self._saved_flag is not None:
            os.environ[FLAG] = self._saved_flag

    def set_flag(self, value):
        os.environ[FLAG] = value

    def run_client(self, client_phonemes, ground_truth=GT, client_words=PRED_WORDS):
        return asyncio.run(
            process_audio_with_client_phonemes(
                client_phonemes=client_phonemes,
                ground_truth_phonemes=ground_truth,
                audio_array=None,          # unused: client_words provided
                sampling_rate=16000,
                client_words=client_words,
            )
        )


class TestProcessWordAlignmentNoRegression(_FlagMixin):
    """Exact-match and normal cases must be byte-identical to the pre-fix code."""

    def test_exact_match_matches_golden(self):
        out = _process_word_alignment(GT_WORDS, GT, PRED_WORDS, PRED_PH)
        self.assertEqual(normalize(out), GOLDEN["exact_match"])

    def test_substitution_matches_golden(self):
        out = _process_word_alignment(
            GT_WORDS, GT, ["the", "cot", "sat"],
            [["ð", "ə"], ["k", "ɑ", "t"], ["s", "æ", "t"]],
        )
        self.assertEqual(normalize(out), GOLDEN["substitution"])

    def test_word_insertion_matches_golden(self):
        out = _process_word_alignment(
            GT_WORDS, GT, ["the", "cat", "sat", "down"],
            [["ð", "ə"], ["k", "æ", "t"], ["s", "æ", "t"], ["d", "a", "ʊ", "n"]],
        )
        self.assertEqual(normalize(out), GOLDEN["insertion"])

    def test_word_deletion_matches_golden(self):
        out = _process_word_alignment(
            GT_WORDS, GT, ["the", "sat"], [["ð", "ə"], ["s", "æ", "t"]],
        )
        self.assertEqual(normalize(out), GOLDEN["deletion"])

    def test_phoneme_list_objects_are_passed_through_unchanged(self):
        """The guards must be transparent: same list objects, not copies."""
        preds = [["ð", "ə"], ["k", "æ", "t"], ["s", "æ", "t"]]
        out = _process_word_alignment(GT_WORDS, GT, PRED_WORDS, preds)
        for i, entry in enumerate(out):
            self.assertIs(entry["phonemes"], preds[i])


class TestProcessWordAlignmentBoundsSafety(_FlagMixin):
    """Out-of-range indices must degrade, never raise."""

    def test_fewer_phoneme_groups_than_words_does_not_raise(self):
        # Pre-fix this raised IndexError: list index out of range
        out = _process_word_alignment(GT_WORDS, GT, PRED_WORDS, [["ð", "ə"], ["k", "æ", "t"]])
        self.assertEqual(len(out), 3)
        # The two in-range words score normally...
        self.assertEqual(out[0]["actual_phonemes"], ["ð", "ə"])
        self.assertEqual(out[0]["per"], 0.0)
        self.assertEqual(out[1]["actual_phonemes"], ["k", "æ", "t"])
        self.assertEqual(out[1]["per"], 0.0)
        # ...and the missing one degrades to an empty phoneme list, PER 1.0.
        self.assertEqual(out[2]["ground_truth_word"], "sat")
        self.assertEqual(out[2]["actual_phonemes"], [])
        self.assertEqual(out[2]["phonemes"], [])
        self.assertEqual(out[2]["per"], 1.0)
        self.assertEqual(out[2]["missed"], ["s", "æ", "t"])
        self.assertEqual(out[2]["total_phonemes"], 3)

    def test_empty_phoneme_predictions_does_not_raise(self):
        out = _process_word_alignment(GT_WORDS, GT, PRED_WORDS, [])
        self.assertEqual(len(out), 3)
        for entry in out:
            self.assertEqual(entry["actual_phonemes"], [])
            self.assertEqual(entry["per"], 1.0)

    def test_short_ground_truth_phonemes_does_not_raise(self):
        """g2p() can silently truncate, leaving fewer gt entries than gt words."""
        short_gt = GT[:2]
        out = _process_word_alignment(GT_WORDS, short_gt, PRED_WORDS, PRED_PH)
        self.assertEqual(len(out), 3)
        self.assertEqual(out[2]["expected_phonemes"], [])
        self.assertEqual(out[2]["actual_phonemes"], ["s", "æ", "t"])
        # No ground truth to score against -> all predicted phonemes are insertions
        self.assertEqual(out[2]["added"], ["s", "æ", "t"])
        self.assertEqual(out[2]["total_phonemes"], 0)

    def test_none_phoneme_group_is_normalized_not_crash(self):
        out = _process_word_alignment(
            GT_WORDS, GT, PRED_WORDS, [["ð", "ə"], None, ["s", "æ", "t"]]
        )
        self.assertEqual(len(out), 3)
        self.assertEqual(out[1]["actual_phonemes"], [])
        self.assertEqual(out[1]["per"], 1.0)

    def test_more_phoneme_groups_than_words_does_not_raise(self):
        out = _process_word_alignment(
            GT_WORDS, GT, PRED_WORDS,
            [["ð", "ə"], ["k", "æ"], ["t"], ["s", "æ", "t"]],
        )
        self.assertEqual(len(out), 3)
        # Extra trailing group is simply never indexed -- no exception.
        self.assertEqual(normalize(out), GOLDEN["client_more_groups"])


class TestClientPathFlagOff(_FlagMixin):
    """With WWAI_CLIENT_REALIGN unset, behavior must be unchanged."""

    def test_exact_match_flag_unset_matches_golden(self):
        self.assertNotIn(FLAG, os.environ)
        out = self.run_client(PRED_PH)
        self.assertEqual(normalize(out), GOLDEN["client_exact"])

    def test_exact_match_flag_false_matches_golden(self):
        self.set_flag("false")
        out = self.run_client(PRED_PH)
        self.assertEqual(normalize(out), GOLDEN["client_exact"])

    def test_more_groups_flag_off_reproduces_old_misalignment(self):
        """Documents the pre-existing (bad) behavior the flag is meant to fix."""
        out = self.run_client([["ð", "ə"], ["k", "æ"], ["t"], ["s", "æ", "t"]])
        self.assertEqual(normalize(out), GOLDEN["client_more_groups"])
        # "sat" was scored against ["t"] -- the wrong word's phonemes.
        self.assertEqual(out[2]["predicted_word"], "sat")
        self.assertEqual(out[2]["actual_phonemes"], ["t"])

    def test_fewer_groups_flag_off_no_longer_raises(self):
        """Only the bounds guard changes here: IndexError -> degraded output."""
        out = self.run_client([["ð", "ə"], ["k", "æ", "t"]])
        self.assertEqual(len(out), 3)
        self.assertEqual(out[2]["actual_phonemes"], [])


class TestClientPathFlagOn(_FlagMixin):
    """With WWAI_CLIENT_REALIGN=true, client phonemes are re-segmented."""

    def test_exact_match_still_correct_with_flag_on(self):
        self.set_flag("true")
        out = self.run_client(PRED_PH)
        for entry in out:
            self.assertEqual(entry["per"], 0.0, entry)
        self.assertEqual([e["actual_phonemes"] for e in out], PRED_PH)

    def test_more_groups_are_regrouped_to_predicted_words(self):
        """The bug case: client split 'cat' across two groups. Realign fixes it."""
        self.set_flag("true")
        out = self.run_client([["ð", "ə"], ["k", "æ"], ["t"], ["s", "æ", "t"]])
        self.assertEqual(len(out), 3)
        self.assertEqual([e["actual_phonemes"] for e in out], PRED_PH)
        for entry in out:
            self.assertEqual(entry["per"], 0.0, entry)

    def test_fewer_groups_are_regrouped_to_predicted_words(self):
        """Client merged all three words into one group."""
        self.set_flag("true")
        out = self.run_client([["ð", "ə", "k", "æ", "t", "s", "æ", "t"]])
        self.assertEqual(len(out), 3)
        self.assertEqual([e["actual_phonemes"] for e in out], PRED_PH)

    def test_result_length_always_matches_word_ops_no_index_error(self):
        self.set_flag("true")
        for groups in (
            [["ð", "ə"], ["k", "æ", "t"]],
            [[], [], []],
            [["ð"], ["ə"], ["k"], ["æ"], ["t"], ["s"], ["æ"], ["t"]],
        ):
            with self.subTest(groups=groups):
                out = self.run_client(groups)
                self.assertEqual(len(out), 3)

    def test_flag_accepts_common_truthy_spellings(self):
        for value in ("1", "true", "TRUE", "yes", "on", " true "):
            with self.subTest(value=value):
                self.set_flag(value)
                out = self.run_client([["ð", "ə", "k", "æ", "t", "s", "æ", "t"]])
                self.assertEqual([e["actual_phonemes"] for e in out], PRED_PH)

    def test_flag_falsy_spellings_leave_grouping_alone(self):
        for value in ("", "0", "false", "off", "no", "maybe"):
            with self.subTest(value=value):
                self.set_flag(value)
                out = self.run_client([["ð", "ə", "k", "æ", "t", "s", "æ", "t"]])
                # Not regrouped: everything landed on the first word.
                self.assertEqual(
                    out[0]["actual_phonemes"], ["ð", "ə", "k", "æ", "t", "s", "æ", "t"]
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
