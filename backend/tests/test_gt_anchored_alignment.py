"""
Tests for ground-truth-anchored alignment (``core/gt_alignment.py``).

Run with (from the ``backend`` directory):

    PYTHONIOENCODING=utf-8 python -m unittest tests.test_gt_anchored_alignment -v

The headline test is ``TestAsrCorrectionHidesTheError``: it constructs a child
who makes a real reading error together with an ASR that "corrects" it, and
asserts that the current pipeline loses the error while the ground-truth
anchored path still registers it on the right word.

No network, no models, no audio -- every fixture is hand written IPA.
"""

import os
import sys
import unittest

# Same convention as the other tests in this folder.
BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from core.gt_alignment import (  # noqa: E402
    GT_ANCHORED_FLAG,
    align_to_ground_truth,
    derive_asr_hints,
    is_gt_anchored_enabled,
    segment_phonemes_by_ground_truth,
)

# --------------------------------------------------------------------------- #
# Hand written fixtures (IPA, matching what eng_to_ipa produces for these words)
# --------------------------------------------------------------------------- #

THE = ('the', ['ð', 'ə'])
CAT = ('cat', ['k', 'æ', 't'])
SAT = ('sat', ['s', 'æ', 't'])
ON = ('on', ['ɑ', 'n'])
MAT = ('mat', ['m', 'æ', 't'])
A = ('a', ['ə'])

# "the cat sat"
GT_SHORT = [THE, CAT, SAT]
# "the cat sat on the mat"
GT_LONG = [THE, CAT, SAT, ON, THE, MAT]

# Every key _process_word_alignment puts on a match/substitution record.
CONTRACT_KEYS = {
    "type", "predicted_word", "ground_truth_word", "phonemes",
    "ground_truth_phonemes", "expected_phonemes", "actual_phonemes",
    "per", "missed", "added", "substituted", "total_phonemes", "total_errors",
}


def flatten(word_tuples):
    """Flat acoustic phoneme stream for a perfect reading of these words."""
    return [p for _, phs in word_tuples for p in phs]


def sentence_per(results):
    total_phonemes = sum(r["total_phonemes"] for r in results)
    total_errors = sum(r["total_errors"] for r in results)
    return total_errors / total_phonemes if total_phonemes else 0.0


def by_word(results, word):
    return [r for r in results if r["ground_truth_word"] == word]


def run_current_path(ground_truth_phonemes, flat_phonemes, asr_words, asr_word_phonemes):
    """
    Reproduce exactly what ``process_audio_array`` does today with the flag OFF:
    bucket the acoustic phonemes against g2p(ASR transcript), then compare the
    ground truth to those buckets by word index.

    ``asr_word_phonemes`` stands in for ``g2p(" ".join(predicted_words))`` so
    the test needs neither eng_to_ipa nor the network.
    """
    from core.process_audio import align_phonemes_to_words, _process_word_alignment

    alignment = align_phonemes_to_words(flat_phonemes, asr_word_phonemes)
    buckets = [pred for _, pred, _ in alignment]
    return _process_word_alignment(
        ground_truth_words=[w for w, _ in ground_truth_phonemes],
        ground_truth_phonemes=ground_truth_phonemes,
        predicted_words=asr_words,
        phoneme_predictions=buckets,
    )


class TestAsrCorrectionHidesTheError(unittest.TestCase):
    """
    THE POINT OF THIS WORK.

    A child reading "the cat sat on the mat" skips "cat" entirely -- the single
    most common beginning-reader error. Deepgram nova-2 and whisper-tiny.en are
    language-model decoders: they emit the fluent, expected sentence and put
    "cat" back. The current pipeline then buckets the acoustic phonemes against
    that corrected transcript, and because every bucket is forced to hold at
    least one phoneme, the skip is dissolved: nothing is reported as skipped,
    the leftover schwa of "the" is handed to "cat", and the correctly-read
    "the" is charged with an error it did not make.

    Anchored to the ground truth, the same audio reports exactly one problem:
    "cat" was not read.
    """

    # child said: "the __ sat on the mat"
    FLAT = flatten([THE, SAT, ON, THE, MAT])
    ASR_CORRECTED = ['the', 'cat', 'sat', 'on', 'the', 'mat']

    def test_current_path_loses_the_error(self):
        results = run_current_path(
            GT_LONG, self.FLAT, self.ASR_CORRECTED, GT_LONG
        )

        # 1. The skip is never reported as a skip.
        self.assertEqual(
            [r for r in results if r["type"] == "deletion"], [],
            "current path should (wrongly) report no skipped word",
        )

        # 2. The skipped word is instead reported as a mispronunciation:
        #    it was handed phonemes the child never used for it.
        cat = by_word(results, 'cat')[0]
        self.assertNotEqual(
            cat["actual_phonemes"], [],
            "current path invents phonemes for the word that was skipped",
        )

        # 3. And the error smears backwards onto "the", which was read perfectly.
        first_the = by_word(results, 'the')[0]
        self.assertGreater(
            first_the["per"], 0.0,
            "current path charges a correctly-read word with an error",
        )

    def test_ground_truth_anchored_registers_the_error(self):
        results = align_to_ground_truth(self.FLAT, GT_LONG, self.ASR_CORRECTED)

        self.assertEqual(len(results), len(GT_LONG))

        cat = by_word(results, 'cat')[0]
        self.assertEqual(cat["type"], "deletion")
        self.assertEqual(cat["per"], 1.0)
        self.assertEqual(cat["actual_phonemes"], [])
        self.assertEqual(cat["missed"], ['k', 'æ', 't'])
        self.assertEqual(cat["total_errors"], 3)

        # Every other word was read perfectly and must score perfectly.
        for r in results:
            if r["ground_truth_word"] != 'cat':
                self.assertEqual(
                    r["per"], 0.0,
                    f"{r['ground_truth_word']!r} was read correctly but scored {r['per']}",
                )

        # Sentence PER is exactly the three phonemes of the skipped word.
        self.assertAlmostEqual(sentence_per(results), 3 / 15)

    def test_the_two_paths_actually_disagree(self):
        """Guard against the comparison silently becoming vacuous."""
        current = run_current_path(GT_LONG, self.FLAT, self.ASR_CORRECTED, GT_LONG)
        anchored = align_to_ground_truth(self.FLAT, GT_LONG, self.ASR_CORRECTED)
        self.assertNotEqual(
            [(r["ground_truth_word"], r["type"], r["per"]) for r in current],
            [(r["ground_truth_word"], r["type"], r["per"]) for r in anchored],
        )


class TestWithinWordMispronunciation(unittest.TestCase):
    """A substituted phoneme is pinned to the word that actually carries it."""

    def test_cat_read_as_tat(self):
        flat = ['ð', 'ə', 't', 'æ', 't', 's', 'æ', 't']
        results = align_to_ground_truth(flat, GT_SHORT, ['the', 'cat', 'sat'])

        cat = by_word(results, 'cat')[0]
        self.assertEqual(cat["type"], "substitution")
        self.assertEqual(cat["substituted"], [('k', 't')])
        self.assertEqual(cat["missed"], [])
        self.assertEqual(cat["added"], [])
        self.assertAlmostEqual(cat["per"], 1 / 3, places=4)

        # The neighbours are untouched: the error does not smear.
        self.assertEqual(by_word(results, 'the')[0]["per"], 0.0)
        self.assertEqual(by_word(results, 'sat')[0]["per"], 0.0)

    def test_dropped_initial_consonant(self):
        # "the cat sat" read as "the at sat"
        flat = ['ð', 'ə', 'æ', 't', 's', 'æ', 't']
        results = align_to_ground_truth(flat, GT_SHORT, ['the', 'cat', 'sat'])

        cat = by_word(results, 'cat')[0]
        self.assertEqual(cat["missed"], ['k'])
        self.assertAlmostEqual(cat["per"], 1 / 3, places=4)
        self.assertEqual(by_word(results, 'sat')[0]["per"], 0.0)


# --------------------------------------------------------------------------- #
# Word scoring v2: closest valid pronunciation, edge insertions not counted
# --------------------------------------------------------------------------- #

LEGACY_SCORING_FLAG = "WWAI_LEGACY_WORD_SCORING"

# Keys every ground-truth-anchored record carries on top of
# _process_word_alignment's contract (scoring v2.1).
V21_KEYS = {"canonical_phonemes", "edge_insertions"}


def without_v21_keys(records):
    return [{k: v for k, v in r.items() if k not in V21_KEYS} for r in records]


def pre_v2_align_to_ground_truth(flat_phonemes, ground_truth_phonemes, predicted_words=None):
    """
    Frozen copy of ``align_to_ground_truth`` from before word scoring v2: every
    word scored against its primary G2P phonemes, every inserted phoneme counted.
    The kill switch must reproduce this exactly. Segmentation, ASR hints and the
    deletion/insertion records did not change, so those are reused.
    """
    from core.gt_alignment import (
        _deletion_record, _insertion_record, align_sequences,
    )

    gtp = [(word, list(phs or [])) for word, phs in (ground_truth_phonemes or [])]
    if not gtp:
        return []
    gt_words = [word for word, _ in gtp]
    asr_words = [str(w) for w in (predicted_words or []) if w]
    skip_hints, pred_labels, insertions = derive_asr_hints(gt_words, asr_words)
    segments = segment_phonemes_by_ground_truth(flat_phonemes, gtp, skip_hints)

    results = []
    for idx, (gt_word, gt_phs) in enumerate(gtp):
        for extra in insertions.get(idx, ()):
            results.append(_insertion_record(extra))
        segment = segments[idx] if idx < len(segments) else []
        if not segment:
            results.append(_deletion_record(gt_word, gt_phs))
            continue
        missed, added, substituted = [], [], []
        for pop, gph, pph in align_sequences(gt_phs, segment):
            if pop == 'deletion':
                missed.append(gph)
            elif pop == 'insertion':
                added.append(pph)
            elif pop == 'substitution':
                substituted.append((gph, pph))
        total_errors = len(missed) + len(added) + len(substituted)
        per = total_errors / max(len(gt_phs), 1)
        results.append({
            "type": "match" if total_errors == 0 else "substitution",
            "predicted_word": pred_labels.get(idx, gt_word),
            "ground_truth_word": gt_word,
            "phonemes": list(segment),
            "ground_truth_phonemes": list(gt_phs),
            "expected_phonemes": list(gt_phs),
            "actual_phonemes": list(segment),
            "per": round(per, 4),
            "missed": missed,
            "added": added,
            "substituted": substituted,
            "total_phonemes": len(gt_phs),
            "total_errors": total_errors,
        })
    for extra in insertions.get(len(gtp), ()):
        results.append(_insertion_record(extra))
    # The reused record helpers now add the v2.1 keys, which pre-v2 did not have.
    return without_v21_keys(results)


class _ScoringEnv(unittest.TestCase):
    """Legacy G2P tokenization and v2 word scoring, whatever the shell says."""

    def setUp(self):
        from unittest import mock

        patcher = mock.patch.dict(os.environ)
        patcher.start()
        self.addCleanup(patcher.stop)
        os.environ.pop("WWAI_G2P_STRICT", None)
        os.environ.pop(LEGACY_SCORING_FLAG, None)

    def score_one(self, segment, word_tuple):
        results = align_to_ground_truth(segment, [word_tuple])
        self.assertEqual(len(results), 1)
        return results[0]


class TestClosestValidPronunciation(_ScoringEnv):
    """A correct reading of another CMUdict pronunciation is not an error."""

    def test_to_read_as_tu_is_correct_in_both_g2p_modes(self):
        from core.grapheme_to_phoneme import grapheme_to_phoneme

        for strict in (False, True):
            with self.subTest(strict=strict):
                os.environ["WWAI_G2P_STRICT"] = "true" if strict else "false"
                gt = grapheme_to_phoneme("to", strict=strict)
                self.assertEqual(gt[0][1], ['t', 'ɪ'], "primary G2P form of 'to'")

                r = align_to_ground_truth(['t', 'u'], gt, ['to'])[0]
                self.assertEqual(r["per"], 0.0)
                self.assertEqual(r["type"], "match")
                self.assertEqual(r["expected_phonemes"], ['t', 'u'])
                self.assertEqual(r["ground_truth_phonemes"], ['t', 'u'])
                self.assertEqual(r["total_phonemes"], 2)
                self.assertEqual(r["total_errors"], 0)
                self.assertEqual((r["missed"], r["added"], r["substituted"]), ([], [], []))

    def test_the_primary_wins_a_tie(self):
        # [ð ɪ] is one substitution away from both ðə (primary) and ði.
        r = self.score_one(['ð', 'ɪ'], THE)
        self.assertEqual(r["expected_phonemes"], ['ð', 'ə'])
        self.assertEqual(r["substituted"], [('ə', 'ɪ')])
        self.assertEqual(r["per"], 0.5)

    def test_a_variant_only_wins_with_strictly_fewer_errors(self):
        r = self.score_one(['ð', 'i'], THE)
        self.assertEqual(r["expected_phonemes"], ['ð', 'i'])
        self.assertEqual(r["per"], 0.0)

    def test_variants_are_looked_up_once_per_sentence(self):
        from unittest import mock
        import eng_to_ipa
        import core.grapheme_to_phoneme as g2p_module

        g2p_module.clear_cache()
        self.addCleanup(g2p_module.clear_cache)
        with mock.patch.object(g2p_module.G2p, "ipa_list", wraps=eng_to_ipa.ipa_list) as spy:
            align_to_ground_truth(flatten(GT_LONG), GT_LONG, ['the', 'cat', 'sat', 'on', 'the', 'mat'])
            self.assertEqual(spy.call_count, 1)
            self.assertEqual(sorted(spy.call_args.args[0].split()), ['cat', 'mat', 'on', 'sat', 'the'])

            align_to_ground_truth(flatten(GT_SHORT), GT_SHORT)
            self.assertEqual(spy.call_count, 1)

            os.environ[LEGACY_SCORING_FLAG] = "1"
            g2p_module.clear_cache()
            align_to_ground_truth(flatten(GT_SHORT), GT_SHORT)
            self.assertEqual(spy.call_count, 1)

    def test_segmentation_still_uses_the_primary_phonemes(self):
        cases = [
            (['ð', 'i', 'k', 'æ', 't', 's', 'æ', 't'], GT_SHORT),
            (['ð', 'ə', 'ə', 'k', 'æ', 't', 'h', 's', 'æ', 't', 't'], GT_SHORT),
            (flatten([THE, SAT, ON, THE, MAT]), GT_LONG),
        ]
        for flat, gt in cases:
            with self.subTest(flat=flat):
                v2 = align_to_ground_truth(flat, gt)
                os.environ[LEGACY_SCORING_FLAG] = "1"
                legacy = align_to_ground_truth(flat, gt)
                os.environ.pop(LEGACY_SCORING_FLAG)
                self.assertEqual([r["phonemes"] for r in v2], [r["phonemes"] for r in legacy])
                self.assertEqual(
                    [r["phonemes"] for r in v2],
                    segment_phonemes_by_ground_truth(flat, gt),
                )


class TestEdgeInsertions(_ScoringEnv):
    """Stray phonemes at a segment boundary are segmentation noise, not errors."""

    def test_stray_phoneme_at_either_edge_does_not_count(self):
        for segment in (
            ['h', 'k', 'æ', 't'],        # before
            ['k', 'æ', 't', 's'],        # after
            ['h', 'k', 'æ', 't', 's'],   # both
            ['k', 'k', 'æ', 't'],        # doubled first phoneme
            ['k', 'æ', 't', 't'],        # doubled last phoneme
        ):
            for asr in (None, ['cat']):
                with self.subTest(segment=segment, asr=asr):
                    r = align_to_ground_truth(segment, [CAT], asr)[0]
                    self.assertEqual(r["per"], 0.0)
                    self.assertEqual(r["added"], [])
                    self.assertEqual(r["total_errors"], 0)
                    self.assertEqual(r["type"], "match")
                    self.assertEqual(r["total_phonemes"], 3)
                    # Every acoustic phoneme is still reported on the record.
                    self.assertEqual(r["phonemes"], segment)
                    self.assertEqual(r["actual_phonemes"], segment)

    def test_up_to_three_phonemes_are_forgiven_at_each_edge(self):
        # Segment boundaries often spill two or three phonemes of the next word.
        for segment in (
            ['ə', 'h', 'k', 'æ', 't'],
            ['ʌ', 'ə', 'h', 'k', 'æ', 't'],
            ['k', 'æ', 't', 's', 'z'],
            ['k', 'æ', 't', 's', 'z', 'ʃ'],
            ['ʌ', 'ə', 'h', 'k', 'æ', 't', 's', 'z', 'ʃ'],
        ):
            with self.subTest(segment=segment):
                r = self.score_one(segment, CAT)
                self.assertEqual((r["added"], r["per"]), ([], 0.0))

    def test_a_fourth_edge_phoneme_counts(self):
        # The outer three are set aside, and the one next to the word counts.
        r = self.score_one(['z', 'ʌ', 'ə', 'h', 'k', 'æ', 't'], CAT)
        self.assertEqual((r["missed"], r["added"], r["substituted"]), ([], ['h'], []))
        self.assertEqual(r["per"], round(1 / 3, 4))

        r = self.score_one(['k', 'æ', 't', 's', 'z', 'ʃ', 'ʒ'], CAT)
        self.assertEqual(r["added"], ['s'])
        self.assertEqual(r["per"], round(1 / 3, 4))

        r = self.score_one(['z', 'ʌ', 'ə', 'h', 'k', 'æ', 't', 's', 'z', 'ʃ', 'ʒ'], CAT)
        self.assertEqual(r["added"], ['h', 's'])
        self.assertEqual(r["per"], round(2 / 3, 4))

    def test_one_stray_phoneme_on_a_two_phoneme_word(self):
        # The motivating false alarm. Each of these used to score PER 0.5 on "the".
        for segment in (['ð', 'ə', 'n'], ['ð', 'ə', 'ə'], ['t', 'ð', 'ə']):
            for asr in (None, ['the']):
                with self.subTest(segment=segment, asr=asr):
                    self.assertEqual(align_to_ground_truth(segment, [THE], asr)[0]["per"], 0.0)

    def test_stray_phonemes_between_words_do_not_count(self):
        flat = ['ð', 'ə', 'ə', 'k', 'æ', 't', 'h', 's', 'æ', 't', 't']
        results = align_to_ground_truth(flat, GT_SHORT, ['the', 'cat', 'sat'])
        self.assertEqual([r["per"] for r in results], [0.0, 0.0, 0.0])
        self.assertEqual([r["added"] for r in results], [[], [], []])
        self.assertEqual([p for r in results for p in r["phonemes"]], flat)
        self.assertEqual(sentence_per(results), 0.0)

    def test_an_interior_insertion_still_counts(self):
        for segment in (['k', 'æ', 's', 't'], ['h', 'k', 'æ', 's', 't', 's']):
            with self.subTest(segment=segment):
                r = self.score_one(segment, CAT)
                self.assertEqual(r["added"], ['s'])
                self.assertEqual(r["total_errors"], 1)
                self.assertEqual(r["per"], round(1 / 3, 4))
                self.assertEqual(r["type"], "substitution")

    def test_a_genuine_substitution_still_counts(self):
        r = self.score_one(['k', 'ɪ', 't'], CAT)
        self.assertEqual(r["substituted"], [('æ', 'ɪ')])
        self.assertEqual(r["per"], round(1 / 3, 4))
        self.assertEqual(r["type"], "substitution")

        # A wrong last phoneme stays a substitution; it is not re-read as a
        # missed phoneme plus a free edge insertion.
        r = self.score_one(['k', 'æ', 'd'], CAT)
        self.assertEqual((r["missed"], r["added"], r["substituted"]), ([], [], [('t', 'd')]))
        self.assertEqual(r["per"], round(1 / 3, 4))

        r = self.score_one(['t', 'æ', 't', 's'], CAT)
        self.assertEqual(r["substituted"], [('k', 't')])
        self.assertEqual(r["added"], [])

    def test_a_missed_phoneme_still_counts(self):
        r = self.score_one(['h', 'k', 'æ'], CAT)
        self.assertEqual(r["missed"], ['t'])
        self.assertEqual(r["per"], round(1 / 3, 4))

    def test_a_run_of_interior_insertions_counts_in_full(self):
        # Ending the word early and calling the rest edge noise must not hide
        # them behind one made-up substitution.
        r = self.score_one(['k', 'æ', 's', 's', 't'], CAT)
        self.assertEqual((r["missed"], r["added"], r["substituted"]), ([], ['s', 's'], []))
        self.assertEqual(r["total_errors"], 2)
        self.assertEqual(r["per"], round(2 / 3, 4))

        r = self.score_one(['h', 'k', 'æ', 's', 's', 's', 's', 't', 'h'], CAT)
        self.assertEqual(r["added"], ['s', 's', 's', 's'])
        self.assertEqual(r["per"], round(4 / 3, 4))

    def test_a_wholly_wrong_reading_scores_one(self):
        r = self.score_one(['z', 'z', 'z', 'z', 'z'], CAT)
        self.assertEqual(r["per"], 1.0)
        self.assertEqual(r["total_errors"], 3)
        self.assertEqual(r["added"], [])


def g2p_flat(sentence):
    """The flat phoneme stream of a perfect reading of ``sentence`` (real G2P)."""
    from core.grapheme_to_phoneme import grapheme_to_phoneme
    return [p for _, phs in grapheme_to_phoneme(sentence) for p in phs]


class TestReadingMiscues(_ScoringEnv):
    """
    Reading a different word that adds sounds at an edge is a real mistake.

    speechocean762 speakers always attempt the right word, so the benchmark
    cannot show these. Forgiving edge runs scored every one of them 0.0 and the
    child heard "Great job!". The miscue guard counts the edge sounds when the
    ASR heard a different word AND that word fits the sounds at least as well as
    the expected word does with its edges forgiven.
    """

    # (sentence to read, what the child read, the word that was misread)
    MISCUES = [
        ("it is big", "sit is big", "it"),
        ("we run home", "we running home", "run"),
        ("go to the top", "go to the stop", "top"),
        ("an egg", "man egg", "an"),
        ("i see it", "i seeing it", "see"),
        ("put it on", "put it upon", "on"),
        ("the dog ran", "the dogs ran", "dog"),
        ("i can jump", "i can jumped", "jump"),
        ("i can jump", "my can jump", "i"),
    ]

    def _score(self, sentence, flat, asr):
        from core.grapheme_to_phoneme import grapheme_to_phoneme
        return align_to_ground_truth(flat, grapheme_to_phoneme(sentence), asr)

    def _legacy(self, sentence, flat, asr):
        os.environ[LEGACY_SCORING_FLAG] = "1"
        try:
            return self._score(sentence, flat, asr)
        finally:
            os.environ.pop(LEGACY_SCORING_FLAG)

    def test_no_forgiveness_when_the_asr_heard_another_word(self):
        for target, read, word in self.MISCUES:
            with self.subTest(target=target, read=read):
                flat = g2p_flat(read)
                v2 = by_word(self._score(target, flat, read.split()), word)[0]
                old = by_word(self._legacy(target, flat, read.split()), word)[0]
                self.assertNotEqual(v2["predicted_word"], word)
                self.assertGreater(v2["per"], 0.0)
                self.assertEqual(v2["type"], "substitution")
                # The ASR can only take leniency away. It never adds errors
                # beyond what the pre-v2 scoring counted.
                self.assertLessEqual(v2["per"], old["per"])

    def test_the_miscue_guard_only_touches_the_misheard_slot(self):
        for target, read, word in self.MISCUES:
            with self.subTest(target=target, read=read):
                flat = g2p_flat(read)
                heard = self._score(target, flat, read.split())
                agreed = self._score(target, flat, target.split())
                self.assertEqual(
                    [r["per"] for r in heard if r["ground_truth_word"] != word],
                    [r["per"] for r in agreed if r["ground_truth_word"] != word],
                )

    def test_the_best_variant_still_applies_under_the_guard(self):
        # "an" read as "man": counted against æn (one insertion), not ən (two errors).
        r = by_word(self._score("an egg", g2p_flat("man egg"), ["man", "egg"]), "an")[0]
        self.assertEqual(r["expected_phonemes"], ['æ', 'n'])
        self.assertEqual(r["added"], ['m'])
        self.assertEqual(r["per"], 0.5)

        # "to" read correctly as tu, with the ASR writing "two": no insertion to
        # forgive, and tu is still a valid pronunciation of "to".
        r = self._score("go to", g2p_flat("go") + ['t', 'u'], ["go", "two"])[1]
        self.assertEqual((r["ground_truth_word"], r["predicted_word"]), ("to", "two"))
        self.assertEqual(r["expected_phonemes"], ['t', 'u'])
        self.assertEqual(r["per"], 0.0)

    def test_the_guard_needs_the_asr_word_to_fit_the_sounds(self):
        # An ASR that misheard a correct reading does not take the forgiveness
        # away. "then" is [ð ɛ n], which fits [ð ə n] worse than "the" does with
        # the stray [n] forgiven, so this still scores 0.
        r = align_to_ground_truth(['ð', 'ə', 'n'], [THE], ['then'])[0]
        self.assertEqual((r["predicted_word"], r["per"], r["edge_insertions"]), ("then", 0.0, ['n']))

        # When the sounds really are "then", the [n] counts.
        r = align_to_ground_truth(['ð', 'ɛ', 'n'], [THE], ['then'])[0]
        self.assertEqual(r["edge_insertions"], [])
        self.assertEqual(r["total_errors"], 2)
        self.assertEqual(r["per"], 1.0)

    def test_an_asr_word_with_no_pronunciation_leaves_the_forgiveness(self):
        for asr in (['zzxqv'], ['42']):
            with self.subTest(asr=asr):
                r = align_to_ground_truth(['ð', 'ə', 'n'], [THE], asr)[0]
                self.assertEqual(r["per"], 0.0)

    def test_without_the_asr_a_short_miscue_is_forgiven(self):
        # The guard's known limit. When the ASR is missing or wrote the expected
        # word, up to three extra edge sounds are forgiven, so these score 0. A
        # child who really says "running" is almost always heard as "running",
        # which the guard catches (see above).
        cases = [
            ("we run home", g2p_flat("we running home"), "run"),
            ("i see it", g2p_flat("i seeing it"), "see"),
            ("the cat sat", g2p_flat("the") + g2p_flat("scatter") + g2p_flat("sat"), "cat"),
        ]
        for target, flat, word in cases:
            for asr in (None, target.split()):
                with self.subTest(target=target, asr=asr):
                    self.assertEqual(by_word(self._score(target, flat, asr), word)[0]["per"], 0.0)

    def test_a_long_garbled_run_around_the_word_counts(self):
        # Four phonemes after the word: the outer three are forgiven, one counts.
        flat = g2p_flat("the") + g2p_flat("cat") + list("ɹʌnɪ") + g2p_flat("sat")
        for asr in (None, ["the", "cat", "sat"]):
            with self.subTest(asr=asr):
                r = by_word(self._score("the cat sat", flat, asr), "cat")[0]
                self.assertGreater(r["per"], 0.0)


class TestLegacyWordScoringKillSwitch(_ScoringEnv):
    """WWAI_LEGACY_WORD_SCORING brings back the pre-v2 numbers exactly."""

    CASES = [
        (['ð', 'ə', 'n'], [THE], None),
        (['h', 'k', 'æ', 't', 's'], [CAT], ['cat']),
        (['k', 'æ', 't', 't'], [CAT], ['cat']),
        (['k', 'æ', 's', 't'], [CAT], ['cat']),
        (['t', 'u'], [('to', ['t', 'ɪ'])], ['to']),
        (['z', 'z', 'z', 'z', 'z'], [CAT], None),
        (['ð', 'ə', 'ə', 'k', 'æ', 't', 'h', 's', 'æ', 't', 't'], GT_SHORT, ['the', 'cat', 'sat', 'now']),
        (flatten([THE, SAT, ON, THE, MAT]), GT_LONG, ['the', 'cat', 'sat', 'on', 'the', 'mat']),
        (['ð', 'ə', 't', 'æ', 't', 's', 'æ', 't', 'ɑ', 'n', 'ð', 'ə'], GT_LONG,
         ['the', 'cat', 'sat', 'on', 'the', 'mat', 'now']),
        ([], GT_SHORT, None),
        # Reading miscues, with and without the ASR hearing the other word.
        (['s', 'ɪ', 't'], [('it', ['ɪ', 't'])], ['sit']),
        (['ð', 'ə', 's', 'k', 'æ', 't', 'ə', 'r', 's', 'æ', 't'], GT_SHORT, ['the', 'scatter', 'sat']),
        (['ð', 'ə', 's', 'k', 'æ', 't', 'ə', 'r', 's', 'æ', 't'], GT_SHORT, None),
        (['ə', 'h', 'k', 'æ', 't'], [CAT], ['cat']),
    ]

    def test_kill_switch_matches_the_pre_v2_function(self):
        for value in ("1", "true", " YES "):
            os.environ[LEGACY_SCORING_FLAG] = value
            for flat, gt, asr in self.CASES:
                with self.subTest(value=value, flat=flat):
                    records = align_to_ground_truth(list(flat), gt, asr)
                    self.assertEqual(
                        without_v21_keys(records),
                        pre_v2_align_to_ground_truth(list(flat), gt, asr),
                    )
                    # The added keys say nothing new: nothing is forgiven, and
                    # the canonical pronunciation is the one scored against.
                    for r in records:
                        self.assertEqual(r["edge_insertions"], [])
                        if r["type"] != "insertion":
                            self.assertEqual(r["canonical_phonemes"], r["expected_phonemes"])

    def test_falsy_kill_switch_keeps_v2(self):
        for value in ("", "0", "false", "off"):
            os.environ[LEGACY_SCORING_FLAG] = value
            with self.subTest(value=value):
                self.assertEqual(self.score_one(['ð', 'ə', 'n'], THE)["per"], 0.0)

    def test_the_comparison_is_not_vacuous(self):
        changed = [
            flat for flat, gt, asr in self.CASES
            if without_v21_keys(align_to_ground_truth(list(flat), gt, asr))
            != pre_v2_align_to_ground_truth(list(flat), gt, asr)
        ]
        self.assertGreaterEqual(len(changed), 6)
        old = pre_v2_align_to_ground_truth(['ð', 'ə', 'n'], [THE])[0]
        self.assertEqual((old["per"], old["added"]), (0.5, ['n']))


class TestFeedbackFormatterOnV2Records(_ScoringEnv):
    """The formatter consumes per / missed / added / substituted / expected_phonemes."""

    def setUp(self):
        super().setUp()
        os.environ.pop("WWAI_LEGACY_FEEDBACK", None)  # the current feedback rules, whatever the shell says

    def test_formatter_runs_and_ignores_forgiven_edge_noise(self):
        from core.phoneme_feedback_formatter import build_phoneme_to_error_words, generate_feedback
        from core.process_audio import analyze_results

        # "the cat sat" with a stray [ə] after "the" (forgiven) and "cat" read as "deb", three
        # wrong sounds, so it is clearly wrong and gets corrected.
        flat = ['ð', 'ə', 'ə', 'd', 'ɛ', 'b', 's', 'æ', 't']
        records = align_to_ground_truth(flat, GT_SHORT, ['the', 'cat', 'sat'])
        _df, _highest, problems, per_summary = analyze_results(records)

        error_words = build_phoneme_to_error_words(records)
        self.assertEqual(set(error_words), {'k', 'æ', 't'})
        self.assertNotIn('ə', error_words)
        feedback = generate_feedback(problems, per_summary, records)
        self.assertIn("cat", feedback.text)
        self.assertIn('ph="kæt"', feedback.ssml)

    def test_formatter_models_the_word_with_its_canonical_pronunciation(self):
        from core.phoneme_feedback_formatter import generate_feedback
        from core.process_audio import analyze_results

        # "to" read as [d u]: one substitution from "tu", two from the primary "tɪ".
        # The record is scored against "tu", but the spoken feedback models the
        # word with its canonical (primary G2P) pronunciation, "tɪ".
        gt = [('go', ['g', 'o', 'ʊ']), ('to', ['t', 'ɪ'])]
        records = align_to_ground_truth(['g', 'o', 'ʊ', 'd', 'u'], gt, ['go', 'to'])
        to = by_word(records, 'to')[0]
        self.assertEqual(to["expected_phonemes"], ['t', 'u'])
        self.assertEqual(to["canonical_phonemes"], ['t', 'ɪ'])
        self.assertEqual(to["substituted"], [('t', 'd')])
        self.assertEqual(to["per"], 0.5)

        _df, _highest, problems, per_summary = analyze_results(records)
        # One wrong sound is not a clear mistake, so the current rules praise this reading.
        # Only the old rule (the kill switch) corrects "to", and how a named word is modelled
        # does not depend on the rule.
        self.assertEqual(generate_feedback(problems, per_summary, records).text, "Great job!")
        os.environ["WWAI_LEGACY_FEEDBACK"] = "1"  # restored by _ScoringEnv
        feedback = generate_feedback(problems, per_summary, records)
        self.assertIn("'to'", feedback.text)
        self.assertIn('ph="tɪ">to</phoneme>', feedback.ssml)

        # The same records through a DataFrame round trip, as the handler does.
        df, _highest, problems, per_summary = analyze_results(records)
        feedback = generate_feedback(problems, per_summary, df.to_dict('records'))
        self.assertIn('ph="tɪ">to</phoneme>', feedback.ssml)

    def test_a_repeated_word_is_modelled_from_its_worst_occurrence(self):
        from core.phoneme_feedback_formatter import generate_feedback

        def record(per, errors, substituted, expected, canonical=None, added=()):
            r = {
                "type": "substitution", "ground_truth_word": "the", "predicted_word": "the",
                "per": per, "total_errors": errors, "total_phonemes": 2,
                "missed": [], "added": list(added), "substituted": substituted,
                "expected_phonemes": expected, "ground_truth_phonemes": expected,
            }
            if canonical is not None:
                r["canonical_phonemes"] = canonical
            return r

        # Records without canonical_phonemes (the legacy path): the IPA comes from
        # the occurrence with the highest per, not from the first one. That one has
        # three errors, so it is clearly wrong and gets corrected.
        records = [
            record(0.5, 1, [('ə', 'ɪ')], ['ð', 'i']),
            record(1.5, 3, [('ð', 'd'), ('ə', 'ɪ')], ['ð', 'ə'], added=['n']),
        ]
        feedback = generate_feedback({}, {"sentence_per": 0.75}, records)
        self.assertIn('ph="ðə">the</phoneme>', feedback.ssml)
        self.assertNotIn('ph="ði"', feedback.ssml)

        # canonical_phonemes, when present, wins over expected_phonemes.
        records = [
            record(0.5, 1, [('ə', 'ɪ')], ['ð', 'i'], canonical=['ð', 'ə']),
            record(1.5, 3, [('ð', 'd'), ('i', 'ɪ')], ['ð', 'i'], canonical=['ð', 'ə'], added=['n']),
        ]
        feedback = generate_feedback({}, {"sentence_per": 0.75}, records)
        self.assertIn('ph="ðə">the</phoneme>', feedback.ssml)


class TestCanonicalPhonemesAndEdgeInsertions(_ScoringEnv):
    """What a record was scored against, and what was forgiven, stay visible."""

    def test_records_carry_the_canonical_phonemes_and_forgiven_edges(self):
        r = self.score_one(['h', 'k', 'æ', 't', 's'], CAT)
        self.assertEqual(r["canonical_phonemes"], ['k', 'æ', 't'])
        self.assertEqual(r["edge_insertions"], ['h', 's'])
        self.assertEqual(r["added"], [])

        r = self.score_one(['z', 'ʌ', 'ə', 'h', 'k', 'æ', 't'], CAT)
        self.assertEqual(r["edge_insertions"], ['z', 'ʌ', 'ə'])
        self.assertEqual(r["added"], ['h'])

        r = self.score_one(['k', 'æ', 't'], CAT)
        self.assertEqual(r["edge_insertions"], [])

    def test_canonical_is_the_primary_even_when_a_variant_is_scored(self):
        r = align_to_ground_truth(['t', 'u', 'n'], [('to', ['t', 'ɪ'])], ['to'])[0]
        self.assertEqual(r["expected_phonemes"], ['t', 'u'])
        self.assertEqual(r["canonical_phonemes"], ['t', 'ɪ'])
        self.assertEqual(r["edge_insertions"], ['n'])
        self.assertEqual(r["per"], 0.0)

    def test_nothing_is_forgiven_under_the_miscue_guard(self):
        r = align_to_ground_truth(['s', 'ɪ', 't'], [('it', ['ɪ', 't'])], ['sit'])[0]
        self.assertEqual(r["edge_insertions"], [])
        self.assertEqual(r["added"], ['s'])
        self.assertEqual(r["canonical_phonemes"], ['ɪ', 't'])

    def test_every_record_type_carries_the_keys(self):
        flat = ['ð', 'ə', 't', 'æ', 't', 's', 'æ', 't', 'ɑ', 'n', 'ð', 'ə']
        results = align_to_ground_truth(flat, GT_LONG, ['the', 'cat', 'sat', 'on', 'the', 'mat', 'now'])
        self.assertEqual({r["type"] for r in results}, {"match", "substitution", "deletion", "insertion"})
        for r in results:
            with self.subTest(record=r["type"], word=r["ground_truth_word"]):
                self.assertTrue(V21_KEYS.issubset(r.keys()))
                self.assertIsInstance(r["canonical_phonemes"], list)
                self.assertIsInstance(r["edge_insertions"], list)
        deletion = [r for r in results if r["type"] == "deletion"][0]
        self.assertEqual((deletion["canonical_phonemes"], deletion["edge_insertions"]), (['m', 'æ', 't'], []))
        insertion = [r for r in results if r["type"] == "insertion"][0]
        self.assertEqual((insertion["canonical_phonemes"], insertion["edge_insertions"]), ([], []))

    def test_records_do_not_share_lists(self):
        r = self.score_one(['h', 'k', 'æ', 't'], CAT)
        r["canonical_phonemes"].append('x')
        r["edge_insertions"].append('y')
        self.assertEqual(CAT[1], ['k', 'æ', 't'])
        again = self.score_one(['h', 'k', 'æ', 't'], CAT)
        self.assertEqual((again["canonical_phonemes"], again["edge_insertions"]), (['k', 'æ', 't'], ['h']))


class TestContractions(_ScoringEnv):
    """An ASR contraction matches the expected contraction, curly apostrophe or not."""

    def test_normalize_word_keeps_one_apostrophe_form(self):
        from core.gt_alignment import _normalize_word
        for word in ("it's", "It's", "it\u2019s", "IT\u2018S"):
            with self.subTest(word=word):
                self.assertEqual(_normalize_word(word), "it's")

    def test_a_contraction_read_right_is_not_a_misheard_slot(self):
        from core.grapheme_to_phoneme import clean_sentence, grapheme_to_phoneme
        gt = grapheme_to_phoneme(clean_sentence("It's a dog."))
        flat = ['ɪ', 't', 's', 'z'] + ['ə'] + ['d', 'ɔ', 'g']
        for asr in (["it's", "a", "dog"], ["It\u2019s", "a", "dog"]):
            with self.subTest(asr=asr):
                r = align_to_ground_truth(flat, gt, asr)[0]
                self.assertEqual(r["ground_truth_word"], "it's")
                self.assertEqual(r["per"], 0.0)


class TestScoringVersion(unittest.TestCase):

    def test_per_summary_carries_the_scoring_version(self):
        from core.gt_alignment import SCORING_VERSION
        from core.process_audio import analyze_results

        self.assertEqual(SCORING_VERSION, 2)
        records = align_to_ground_truth(flatten(GT_SHORT), GT_SHORT, ['the', 'cat', 'sat'])
        _df, _highest, _problems, per_summary = analyze_results(records)
        self.assertEqual(per_summary["scoring_version"], 2)
        self.assertEqual(per_summary["sentence_per"], 0.0)


class TestSkippedWords(unittest.TestCase):

    def test_trailing_word_skipped(self):
        # "the cat sat" read as "the cat" (trailed off), ASR restored "sat"
        flat = flatten([THE, CAT])
        results = align_to_ground_truth(flat, GT_SHORT, ['the', 'cat', 'sat'])

        self.assertEqual([r["type"] for r in results],
                         ["match", "match", "deletion"])
        self.assertEqual(by_word(results, 'sat')[0]["missed"], ['s', 'æ', 't'])

    def test_skipped_word_does_not_shift_later_words(self):
        # Skip each word of "the cat sat on the mat" in turn. Whichever word is
        # skipped, every OTHER word must still score 0.0 -- that is the whole
        # point of allowing an empty segment.
        for skipped in range(len(GT_LONG)):
            kept = [w for i, w in enumerate(GT_LONG) if i != skipped]
            flat = flatten(kept)
            asr = [w for w, _ in GT_LONG]  # ASR "restores" the skipped word

            with self.subTest(skipped=GT_LONG[skipped][0], index=skipped):
                results = align_to_ground_truth(flat, GT_LONG, asr)
                self.assertEqual(len(results), len(GT_LONG))
                self.assertEqual(results[skipped]["type"], "deletion")
                self.assertEqual(results[skipped]["per"], 1.0)
                for i, r in enumerate(results):
                    if i != skipped:
                        self.assertEqual(
                            r["per"], 0.0,
                            f"skipping {GT_LONG[skipped][0]!r} disturbed {r['ground_truth_word']!r}",
                        )

    def test_every_word_skipped(self):
        results = align_to_ground_truth([], GT_SHORT, ['the', 'cat', 'sat'])
        self.assertEqual([r["type"] for r in results], ["deletion"] * 3)
        self.assertEqual(sentence_per(results), 1.0)


class TestInsertedWords(unittest.TestCase):

    def test_extra_asr_word_becomes_an_insertion_record(self):
        flat = flatten(GT_SHORT)
        results = align_to_ground_truth(flat, GT_SHORT, ['the', 'cat', 'sat', 'down'])

        self.assertEqual(len(results), 4)
        extra = results[-1]
        self.assertEqual(extra["type"], "insertion")
        self.assertEqual(extra["predicted_word"], 'down')
        self.assertEqual(extra["ground_truth_word"], "")
        self.assertEqual(extra["total_phonemes"], 0)
        self.assertEqual(extra["total_errors"], 0)
        self.assertEqual(extra["per"], 0.0)

        # The insertion must not disturb the expected words.
        self.assertEqual([r["per"] for r in results[:3]], [0.0, 0.0, 0.0])

    def test_insertion_is_emitted_in_position(self):
        flat = flatten(GT_SHORT)
        results = align_to_ground_truth(flat, GT_SHORT, ['um', 'the', 'cat', 'sat'])
        self.assertEqual(results[0]["type"], "insertion")
        self.assertEqual(results[0]["predicted_word"], 'um')
        self.assertEqual([r["ground_truth_word"] for r in results[1:]],
                         ['the', 'cat', 'sat'])


class TestAsrIsOnlySecondary(unittest.TestCase):
    """The ASR must never move a segment boundary on unambiguous input."""

    def test_segmentation_is_identical_across_wildly_different_transcripts(self):
        flat = ['ð', 'ə', 't', 'æ', 't', 's', 'æ', 't']
        transcripts = [
            ['the', 'cat', 'sat'],          # "corrected"
            ['the', 'that', 'sat'],         # heard a different word
            ['duh', 'tat', 'sat', 'down'],  # garbled, plus a spurious word
            ['the', 'sat'],                 # dropped a token
            [],                             # no transcript at all
            None,
        ]
        baseline = None
        for asr in transcripts:
            with self.subTest(asr=asr):
                results = align_to_ground_truth(flat, GT_SHORT, asr)
                # Compare only the acoustic verdict, not the ASR-derived labels.
                verdict = [
                    (r["ground_truth_word"], r["phonemes"], r["per"])
                    for r in results if r["type"] != "insertion"
                ]
                if baseline is None:
                    baseline = verdict
                self.assertEqual(verdict, baseline)

    def test_skip_hint_only_breaks_a_genuine_tie(self):
        # Deliberately ambiguous: "the" ends in a schwa and the next expected
        # word IS a schwa, so [ð, ə] can be read as "the" or as "the"+"a".
        gt = [THE, A, CAT]
        flat = ['ð', 'ə', 'k', 'æ', 't']

        # With no hint the DP splits the schwa off (both readings cost the same).
        self.assertEqual(
            segment_phonemes_by_ground_truth(flat, gt),
            [['ð'], ['ə'], ['k', 'æ', 't']],
        )
        # The ASR heard no separate "a", which breaks the tie the right way.
        self.assertEqual(
            segment_phonemes_by_ground_truth(flat, gt, {1}),
            [['ð', 'ə'], [], ['k', 'æ', 't']],
        )
        # ...and a hint cannot flip an unambiguous reading.
        clear = flatten(GT_SHORT)
        self.assertEqual(
            segment_phonemes_by_ground_truth(clear, GT_SHORT, {0, 1, 2}),
            segment_phonemes_by_ground_truth(clear, GT_SHORT),
        )

    def test_hints_never_outweigh_acoustic_evidence(self):
        # The ASR insists the child read NOTHING; the audio says otherwise.
        # Acoustic evidence must win for every word, no matter how many hints.
        flat = flatten(GT_LONG)
        self.assertEqual(
            segment_phonemes_by_ground_truth(flat, GT_LONG, set(range(len(GT_LONG)))),
            [list(phs) for _, phs in GT_LONG],
        )
        results = align_to_ground_truth(flat, GT_LONG, ['what'])
        self.assertEqual(
            [r["per"] for r in results if r["type"] != "insertion"],
            [0.0] * len(GT_LONG),
        )

    def test_derive_asr_hints_skip(self):
        skip_hints, labels, insertions = derive_asr_hints(
            ['the', 'cat', 'sat'], ['The', 'sat!'],
        )
        self.assertEqual(skip_hints, {1})                # "cat" was not heard
        self.assertEqual(labels, {0: 'The', 2: 'sat!'})   # punctuation/case ignored
        self.assertEqual(insertions, {})

    def test_derive_asr_hints_insertion(self):
        skip_hints, labels, insertions = derive_asr_hints(
            ['the', 'cat', 'sat'], ['the', 'cat', 'sat', 'down'],
        )
        self.assertEqual(skip_hints, set())
        self.assertEqual(labels, {0: 'the', 1: 'cat', 2: 'sat'})
        self.assertEqual(insertions, {3: ['down']})       # trailing extra word

    def test_no_hints_without_a_transcript(self):
        self.assertEqual(derive_asr_hints(['the', 'cat'], None), (set(), {}, {}))
        self.assertEqual(derive_asr_hints(['the', 'cat'], []), (set(), {}, {}))


class TestDeterminism(unittest.TestCase):
    """Anchoring to a fixed target means the same audio always scores the same."""

    CASES = [
        (flatten(GT_SHORT), GT_SHORT, ['the', 'cat', 'sat']),
        (['ð', 'ə', 't', 'æ', 't', 's', 'æ', 't'], GT_SHORT, ['the', 'cat', 'sat']),
        (flatten([THE, SAT, ON, THE, MAT]), GT_LONG, ['the', 'cat', 'sat', 'on', 'the', 'mat']),
        (['x', 'y', 'z'], GT_LONG, ['what']),
        ([], GT_SHORT, None),
    ]

    def test_repeated_calls_are_identical(self):
        for flat, gt, asr in self.CASES:
            with self.subTest(flat=flat):
                first = align_to_ground_truth(list(flat), gt, asr)
                second = align_to_ground_truth(list(flat), gt, asr)
                third = align_to_ground_truth(list(flat), gt, asr)
                self.assertEqual(first, second)
                self.assertEqual(second, third)

    def test_result_does_not_depend_on_input_object_identity(self):
        flat = ['ð', 'ə', 't', 'æ', 't', 's', 'æ', 't']
        a = align_to_ground_truth(flat, GT_SHORT, ['the', 'cat', 'sat'])
        b = align_to_ground_truth(
            [str(p) for p in flat],
            [(w, list(phs)) for w, phs in GT_SHORT],
            ['the', 'cat', 'sat'],
        )
        self.assertEqual(a, b)

    def test_pers_are_plain_floats(self):
        # numpy scalars leak into JSON serialisation and compare oddly.
        results = align_to_ground_truth(flatten(GT_SHORT), GT_SHORT, ['the', 'cat', 'sat'])
        for r in results:
            self.assertIs(type(r["per"]), float)
            self.assertIs(type(r["total_phonemes"]), int)
            self.assertIs(type(r["total_errors"]), int)


class TestOutputContract(unittest.TestCase):
    """Downstream consumers depend on this shape; it must not drift."""

    def test_exact_match(self):
        results = align_to_ground_truth(flatten(GT_SHORT), GT_SHORT, ['the', 'cat', 'sat'])
        self.assertEqual([r["type"] for r in results], ["match"] * 3)
        self.assertEqual([r["per"] for r in results], [0.0, 0.0, 0.0])
        self.assertEqual(sentence_per(results), 0.0)
        for r, (word, phs) in zip(results, GT_SHORT):
            self.assertEqual(r["ground_truth_word"], word)
            self.assertEqual(r["ground_truth_phonemes"], phs)
            self.assertEqual(r["expected_phonemes"], phs)
            self.assertEqual(r["actual_phonemes"], phs)
            self.assertEqual(r["phonemes"], phs)
            self.assertEqual(r["missed"], [])
            self.assertEqual(r["added"], [])
            self.assertEqual(r["substituted"], [])

    def test_all_record_types_carry_the_contract_keys(self):
        # "the cat sat on the mat" read as "the tat sat on the" -- one
        # mispronunciation, one skipped word, plus a spurious ASR word. That is
        # one result set containing all four record types.
        flat = ['ð', 'ə', 't', 'æ', 't', 's', 'æ', 't', 'ɑ', 'n', 'ð', 'ə']
        asr = ['the', 'cat', 'sat', 'on', 'the', 'mat', 'now']
        results = align_to_ground_truth(flat, GT_LONG, asr)
        seen = {r["type"] for r in results}
        self.assertEqual(seen, {"match", "substitution", "deletion", "insertion"})
        for r in results:
            self.assertTrue(CONTRACT_KEYS.issubset(r.keys()), f"missing keys in {r}")
            self.assertIsInstance(r["ground_truth_word"], str)
            self.assertIsInstance(r["predicted_word"], str)
            self.assertIsInstance(r["missed"], list)
            self.assertIsInstance(r["added"], list)
            self.assertIsInstance(r["substituted"], list)

    def test_keys_match_the_existing_implementation(self):
        """Compare key-for-key against _process_word_alignment's own output."""
        from core.process_audio import _process_word_alignment

        legacy = _process_word_alignment(
            ground_truth_words=['the', 'cat', 'sat'],
            ground_truth_phonemes=GT_SHORT,
            predicted_words=['the', 'down'],           # forces all four op types
            phoneme_predictions=[['ð', 'ə'], ['d', 'aʊ', 'n']],
        )
        legacy_keys = {}
        for r in legacy:
            legacy_keys.setdefault(r["type"], set(r.keys()))

        mine = align_to_ground_truth(
            ['ð', 'ə', 't', 'æ', 't'], GT_SHORT, ['the', 'cat', 'down'],
        )
        for r in mine:
            # "match" and "substitution" share one record shape in the legacy code.
            legacy_type = 'match' if r["type"] == 'substitution' else r["type"]
            if legacy_type in legacy_keys:
                # The anchored records add exactly the scoring v2.1 keys.
                self.assertEqual(
                    set(r.keys()), legacy_keys[legacy_type] | V21_KEYS,
                    f"key drift for record type {r['type']!r}",
                )

    def test_analyze_results_accepts_the_output(self):
        from core.process_audio import analyze_results

        results = align_to_ground_truth(
            ['ð', 'ə', 't', 'æ', 't'], GT_SHORT, ['the', 'cat', 'down'],
        )
        df, highest_per, problems, per_summary = analyze_results(results)
        self.assertEqual(len(df), len(results))
        self.assertIn("sentence_per", per_summary)
        self.assertIsInstance(problems, dict)
        self.assertIn("ground_truth_word", highest_per)


class TestFeatureFlag(unittest.TestCase):

    def setUp(self):
        self._saved = os.environ.get(GT_ANCHORED_FLAG)
        os.environ.pop(GT_ANCHORED_FLAG, None)

    def tearDown(self):
        os.environ.pop(GT_ANCHORED_FLAG, None)
        if self._saved is not None:
            os.environ[GT_ANCHORED_FLAG] = self._saved

    def test_defaults_on(self):
        self.assertEqual(GT_ANCHORED_FLAG, "WWAI_GT_ANCHORED_ALIGNMENT")
        self.assertTrue(is_gt_anchored_enabled())

    def test_falsy_values_turn_it_off(self):
        for value in ("0", "false", "FALSE", " False ", "no", "off", "n", "f"):
            with self.subTest(value=value):
                os.environ[GT_ANCHORED_FLAG] = value
                self.assertFalse(is_gt_anchored_enabled())

    def test_truthy_values_keep_it_on(self):
        for value in ("1", "true", "TRUE", " True ", "yes", "on"):
            with self.subTest(value=value):
                os.environ[GT_ANCHORED_FLAG] = value
                self.assertTrue(is_gt_anchored_enabled())

    def test_empty_or_unknown_values_keep_the_default(self):
        for value in ("", "  ", "maybe"):
            with self.subTest(value=value):
                os.environ[GT_ANCHORED_FLAG] = value
                self.assertTrue(is_gt_anchored_enabled())


class TestProcessAudioArrayHook(unittest.TestCase):
    """
    The hook in ``process_audio_array`` is on by default and the flag turns it off.

    Everything expensive is stubbed: no model, no audio preprocessing, no g2p,
    no network.
    """

    LEXICON = {'the': ['ð', 'ə'], 'cat': ['k', 'æ', 't'], 'sat': ['s', 'æ', 't']}

    class _FakePhonemeExtractor:
        def extract_phoneme(self, audio=None, sampling_rate=None):
            # the child read "the cat sat" as "the tat sat"
            return [['ð', 'ə'], ['t', 'æ', 't'], ['s', 'æ', 't']]

    class _FakeWordExtractor:
        def extract_words(self, audio=None, sampling_rate=None):
            return ['the', 'cat', 'sat']   # the ASR "corrected" tat -> cat

    def setUp(self):
        import numpy as np
        import core.process_audio as pa

        self.np = np
        self.pa = pa
        self._saved_flag = os.environ.get(GT_ANCHORED_FLAG)
        self._saved_preprocess = pa.preprocess_audio
        self._saved_g2p = pa.g2p
        # **kwargs so this stub survives signature changes in the real
        # preprocess_audio (e.g. already_preprocessed, added by the
        # single-preprocessing-pass work).
        pa.preprocess_audio = lambda audio=None, sr=None, audio_length_seconds=None, **kwargs: audio
        pa.g2p = lambda text: [(w, self.LEXICON[w]) for w in text.split()]

    def tearDown(self):
        self.pa.preprocess_audio = self._saved_preprocess
        self.pa.g2p = self._saved_g2p
        os.environ.pop(GT_ANCHORED_FLAG, None)
        if self._saved_flag is not None:
            os.environ[GT_ANCHORED_FLAG] = self._saved_flag

    def _run(self):
        import asyncio
        return asyncio.run(self.pa.process_audio_array(
            GT_SHORT,
            self.np.zeros(16000, dtype=self.np.float32),
            16000,
            self._FakePhonemeExtractor(),
            self._FakeWordExtractor(),
            use_chunking=False,
        ))

    def test_flag_off_uses_the_legacy_path(self):
        os.environ[GT_ANCHORED_FLAG] = "false"
        results = self._run()
        # Legacy types come from the ASR word list, so the mispronounced word
        # is still labelled "match" because the ASR spelled it "cat".
        self.assertEqual([r["type"] for r in results], ["match", "match", "match"])

    def _assert_anchored(self, results):
        self.assertEqual([r["type"] for r in results],
                         ["match", "substitution", "match"])
        self.assertEqual(
            results, align_to_ground_truth(
                ['ð', 'ə', 't', 'æ', 't', 's', 'æ', 't'], GT_SHORT,
                ['the', 'cat', 'sat'],
            ),
        )

    def test_flag_unset_uses_the_anchored_path(self):
        os.environ.pop(GT_ANCHORED_FLAG, None)
        self._assert_anchored(self._run())

    def test_flag_set_uses_the_anchored_path(self):
        os.environ[GT_ANCHORED_FLAG] = "true"
        self._assert_anchored(self._run())


class TestClientPhonemesHook(unittest.TestCase):
    """
    ``process_audio_with_client_phonemes`` (phonemes sent by the browser) scores
    them exactly like ``process_audio_array`` does: flattened, then
    ``align_to_ground_truth``. The flag turns it off, and the legacy client path
    is pinned against the pre-change function in
    tests/test_client_realign_and_index_safety.py.
    """

    REALIGN_FLAG = "WWAI_CLIENT_REALIGN"
    WORDS = ['the', 'cat', 'sat']
    # (client groups, client words, ground truth)
    CASES = {
        "exact": ([['ð', 'ə'], ['k', 'æ', 't'], ['s', 'æ', 't']], WORDS, GT_SHORT),
        "asr_corrects_tat": ([['ð', 'ə'], ['t', 'æ', 't'], ['s', 'æ', 't']], WORDS, GT_SHORT),
        "split_group": ([['ð', 'ə'], ['k', 'æ'], ['t'], ['s', 'æ', 't']], WORDS, GT_SHORT),
        "merged_group": ([['ð', 'ə', 'k', 'æ', 't', 's', 'æ', 't']], WORDS, GT_SHORT),
        "skipped_word": ([['ð', 'ə'], ['s', 'æ', 't']], ['the', 'sat'], GT_SHORT),
        "extra_word": ([['ð', 'ə'], ['k', 'æ', 't'], ['s', 'æ', 't'], ['d', 'a', 'ʊ', 'n']],
                       ['the', 'cat', 'sat', 'down'], GT_SHORT),
        "long": ([['ð', 'ə'], ['k', 'æ', 't', 's', 'æ'], ['t'], ['ɑ', 'n', 'ð', 'ə'], ['m', 'æ', 't']],
                 ['the', 'cat', 'sat', 'on', 'the', 'mat'], GT_LONG),
    }

    def setUp(self):
        self._saved = {k: os.environ.get(k) for k in (GT_ANCHORED_FLAG, self.REALIGN_FLAG)}
        for key in self._saved:
            os.environ.pop(key, None)

    def tearDown(self):
        for key, value in self._saved.items():
            os.environ.pop(key, None)
            if value is not None:
                os.environ[key] = value

    def _run(self, groups, words, gt=GT_SHORT, **kwargs):
        import asyncio
        import contextlib
        import io
        from core.process_audio import process_audio_with_client_phonemes

        with contextlib.redirect_stdout(io.StringIO()):
            return asyncio.run(process_audio_with_client_phonemes(
                client_phonemes=groups, ground_truth_phonemes=gt, audio_array=None,
                sampling_rate=16000, client_words=words, **kwargs,
            ))

    def _assert_anchored_for_every_case(self):
        for name, (groups, words, gt) in self.CASES.items():
            with self.subTest(case=name):
                flat = [p for group in groups for p in group]
                self.assertEqual(self._run(groups, words, gt), align_to_ground_truth(flat, gt, words))

    def test_flag_unset_scores_like_align_to_ground_truth(self):
        self._assert_anchored_for_every_case()

    def test_flag_set_scores_like_align_to_ground_truth(self):
        os.environ[GT_ANCHORED_FLAG] = "true"
        self._assert_anchored_for_every_case()

    def test_the_client_grouping_no_longer_matters(self):
        # The same phonemes, grouped three ways by the client, score the same.
        outputs = [self._run(self.CASES[name][0], self.WORDS) for name in ("exact", "split_group", "merged_group")]
        self.assertEqual(outputs[0], outputs[1])
        self.assertEqual(outputs[0], outputs[2])
        self.assertTrue(all(r["per"] == 0 for r in outputs[0]))

    def test_the_mispronunciation_the_asr_corrected_is_found(self):
        groups, words, gt = self.CASES["asr_corrects_tat"]
        self.assertEqual([r["type"] for r in self._run(groups, words, gt)], ["match", "substitution", "match"])
        os.environ[GT_ANCHORED_FLAG] = "false"
        self.assertEqual([r["type"] for r in self._run(groups, words, gt)], ["match", "match", "match"])

    def test_realignment_is_skipped_under_gt_anchoring(self):
        from unittest import mock
        import core.process_audio as pa

        os.environ[self.REALIGN_FLAG] = "true"
        groups, words, gt = self.CASES["split_group"]
        with mock.patch.object(pa, "align_phonemes_to_words", side_effect=AssertionError("realigned")):
            results = self._run(groups, words, gt)
        self.assertEqual(results, align_to_ground_truth([p for g in groups for p in g], gt, words))

    def test_the_guards_come_first_and_in_order(self):
        # Ground truth length first, even with nothing to score.
        with self.assertRaises(ValueError) as ctx:
            self._run([], None, gt=[THE], word_extraction_model=self._Words(None))
        self.assertIn("ground_truth_phonemes", str(ctx.exception))
        # Then no speech, when there is at most one word.
        with self.assertRaises(ValueError) as ctx:
            self._run([['ð', 'ə']], ['the'])
        self.assertEqual(str(ctx.exception), "The audio provided has no speech inside")

    class _Words:
        def __init__(self, words):
            self.words = words

        def extract_words(self, audio=None, sampling_rate=None):
            return self.words

    def test_server_words_are_used_when_the_client_sends_none(self):
        # The hybrid mode: the server's ASR heard an extra word, which becomes an insertion record.
        from unittest import mock
        import core.process_audio as pa

        groups = self.CASES["exact"][0]
        with mock.patch.object(pa, "preprocess_audio", side_effect=lambda audio=None, **_kw: audio):
            results = self._run(groups, None, word_extraction_model=self._Words(['the', 'cat', 'sat', 'down']))
        self.assertEqual(results, align_to_ground_truth(
            [p for g in groups for p in g], GT_SHORT, ['the', 'cat', 'sat', 'down']))
        self.assertEqual([r["type"] for r in results][-1], "insertion")


class TestRobustness(unittest.TestCase):
    """Nothing here may raise inside the live analysis pipeline."""

    def test_empty_ground_truth(self):
        self.assertEqual(align_to_ground_truth(['a', 'b'], [], ['x']), [])

    def test_far_more_phonemes_than_expected(self):
        flat = flatten(GT_SHORT) * 4
        results = align_to_ground_truth(flat, GT_SHORT, ['the', 'cat', 'sat'])
        self.assertEqual(len(results), 3)
        # Every acoustic phoneme is still accounted for somewhere.
        self.assertEqual(
            [p for r in results for p in r["phonemes"]], flat,
        )

    def test_far_fewer_phonemes_than_expected(self):
        results = align_to_ground_truth(['ð'], GT_LONG, ['the'])
        self.assertEqual(len(results), len(GT_LONG))
        self.assertEqual(sum(len(r["phonemes"]) for r in results), 1)

    def test_completely_unrelated_phonemes(self):
        results = align_to_ground_truth(['z', 'z', 'z'], GT_SHORT, ['zzz'])
        self.assertEqual(len(results), 3)
        for r in results:
            self.assertGreater(r["per"], 0.0)

    def test_word_with_no_ground_truth_phonemes(self):
        gt = [THE, ('', []), CAT]
        results = align_to_ground_truth(flatten([THE, CAT]), gt, ['the', 'cat'])
        self.assertEqual(len(results), 3)
        self.assertEqual(results[1]["total_phonemes"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
