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
                self.assertEqual(
                    set(r.keys()), legacy_keys[legacy_type],
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

    def test_defaults_off(self):
        self.assertEqual(GT_ANCHORED_FLAG, "WWAI_GT_ANCHORED_ALIGNMENT")
        self.assertFalse(is_gt_anchored_enabled())

    def test_falsy_values_stay_off(self):
        for value in ("", "0", "false", "no", "off", "  ", "maybe"):
            with self.subTest(value=value):
                os.environ[GT_ANCHORED_FLAG] = value
                self.assertFalse(is_gt_anchored_enabled())

    def test_truthy_values_turn_it_on(self):
        for value in ("1", "true", "TRUE", " True ", "yes", "on"):
            with self.subTest(value=value):
                os.environ[GT_ANCHORED_FLAG] = value
                self.assertTrue(is_gt_anchored_enabled())


class TestProcessAudioArrayHook(unittest.TestCase):
    """
    The hook in ``process_audio_array`` must be inert unless the flag is set.

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

    def test_flag_unset_uses_the_legacy_path(self):
        os.environ.pop(GT_ANCHORED_FLAG, None)
        results = self._run()
        # Legacy types come from the ASR word list, so the mispronounced word
        # is still labelled "match" because the ASR spelled it "cat".
        self.assertEqual([r["type"] for r in results], ["match", "match", "match"])

    def test_flag_set_uses_the_anchored_path(self):
        os.environ[GT_ANCHORED_FLAG] = "true"
        results = self._run()
        self.assertEqual([r["type"] for r in results],
                         ["match", "substitution", "match"])
        self.assertEqual(
            results, align_to_ground_truth(
                ['ð', 'ə', 't', 'æ', 't', 's', 'æ', 't'], GT_SHORT,
                ['the', 'cat', 'sat'],
            ),
        )


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
