import unittest

from tests.benchmark import scoring as S
from tests.benchmark import testutil as U


def _clips():
    good = U.synthetic_clip("c1", "s1", 7, [
        ("CAT", 10, "K AE1 T", [2, 2, 2]),
        ("DOG", 3, "D AO1 G", [2, 0, 2]),
    ], sentence_accuracy=6)
    rejected = U.synthetic_clip("c2", "s2", 30, [("A", 10, "AH0", [2])])
    mismatch = U.synthetic_clip("c3", "s3", 30, [("A", 10, "AH0", [2]), ("B", 10, "B IY1", [2, 2])])
    return [good, rejected, mismatch]


def _outcomes():
    return {
        "c1": U.ok(
            U.record("cat", ["k", "æ", "t"], ["k", "æ", "t"], 0.0),
            U.record("", [], ["ʌ"], 0.0, rtype="insertion"),
            U.record("dog", ["d", "ɔ", "g"], ["d", "ɑ", "g"], 0.3333),
        ),
        "c2": U.rejected("AudioRejected"),
        "c3": U.ok(U.record("a", ["ə"], ["ə"], 0.0)),
    }


class TestBuildItems(unittest.TestCase):
    def setUp(self):
        self.items = S.build_items(_clips(), _outcomes())

    def test_counts(self):
        self.assertEqual((self.items.clips, self.items.rejected, self.items.word_count_mismatch), (3, 1, 1))
        self.assertEqual(self.items.rejected_by_type, {"AudioRejected": 1})

    def test_words(self):
        self.assertEqual([(w.text, w.is_mistake, w.per) for w in self.items.words],
                         [("CAT", False, 0.0), ("DOG", True, 0.3333)])
        self.assertTrue(self.items.words[0].is_child)

    def test_phones(self):
        self.assertEqual(len(self.items.phones), 6)
        dog_vowel = self.items.phones[4]
        self.assertTrue(dog_vowel.is_mistake)
        self.assertTrue(dog_vowel.system_error)
        self.assertFalse(any(p.system_error for p in self.items.phones[:3]))

    def test_g2p_and_sentence(self):
        self.assertEqual((self.items.g2p_agree, self.items.g2p_total), (2, 2))
        self.assertAlmostEqual(self.items.sentences[0].sentence_per, 1 / 6, places=3)

    def test_missing_outcome(self):
        with self.assertRaises(KeyError):
            S.build_items(_clips(), {"c1": _outcomes()["c1"]})

    def test_a_scored_word_that_differs_from_the_record_is_a_mismatch(self):
        # Same number of records as scored words, but the second one is about a different word.
        outcomes = _outcomes()
        outcomes["c1"] = U.ok(
            U.record("cat", ["k", "æ", "t"], ["k", "æ", "t"], 0.0),
            U.record("bat", ["b", "æ", "t"], ["b", "æ", "t"], 0.0),
        )
        items = S.build_items(_clips(), outcomes)
        self.assertEqual(items.word_count_mismatch, 2)
        self.assertEqual(items.words, [])

    def test_words_are_compared_after_clean_sentence(self):
        clip = U.synthetic_clip("c4", "s4", 30, [("DON'T", 10, "D OW1 N T", [2, 2, 2, 2]), ("GO.", 10, "G OW1", [2, 2])])
        outcome = U.ok(
            U.record("dont", ["d", "oʊ", "n", "t"], ["d", "oʊ", "n", "t"], 0.0),
            U.record("go", ["g", "oʊ"], ["g", "oʊ"], 0.0),
        )
        items = S.build_items([clip], {"c4": outcome})
        self.assertEqual(items.word_count_mismatch, 0)
        self.assertEqual(len(items.words), 2)

    def test_record_words_are_cleaned_too(self):
        # The client path's handler (before it cleaned the sentence) passed the text to G2P as
        # sent, so its records say "IT'S" and "GO." where the server path's say "its" and "go".
        # They are still about the same words.
        clip = U.synthetic_clip("c5", "s5", 30, [("IT'S", 10, "IH1 T S", [2, 2, 2]), ("GO.", 10, "G OW1", [2, 2])])
        outcome = U.ok(
            U.record("IT'S", ["ɪ", "t", "s"], ["ɪ", "t", "s"], 0.0),
            U.record("GO.", ["g", "oʊ"], ["g", "oʊ"], 0.0),
        )
        items = S.build_items([clip], {"c5": outcome})
        self.assertEqual(items.word_count_mismatch, 0)
        self.assertEqual(len(items.words), 2)

    def test_client_fallbacks_are_counted_whatever_the_status(self):
        outcomes = _outcomes()
        outcomes["c1"] = dict(outcomes["c1"], client_fallback=True)
        outcomes["c2"] = dict(outcomes["c2"], client_fallback=True)
        outcomes["c3"] = dict(outcomes["c3"], client_fallback=False)
        items = S.build_items(_clips(), outcomes)
        self.assertEqual(items.client_fallbacks, 2)
        self.assertEqual(S.summarize(items, 0.4)["client_fallbacks"], 2)

    def test_outcomes_without_the_field_have_no_fallbacks(self):
        self.assertEqual(self.items.client_fallbacks, 0)
        self.assertEqual(S.summarize(self.items, 0.4)["client_fallbacks"], 0)


class TestMalformedOutcomes(unittest.TestCase):
    def _items(self, outcome):
        clip = U.synthetic_clip("c9", "s9", 30, [("CAT", 10, "K AE1 T", [2, 2, 2])])
        return S.build_items([clip], {"c9": outcome})

    def test_missing_per_raises_and_names_the_clip(self):
        record = U.record("cat", ["k", "æ", "t"], ["k", "æ", "t"], 0.0)
        record["per"] = None
        with self.assertRaises(ValueError) as ctx:
            self._items(U.ok(record))
        self.assertIn("c9", str(ctx.exception))

    def test_non_finite_per_raises(self):
        for bad in (float("nan"), float("inf"), "0.3"):
            with self.subTest(per=bad):
                record = U.record("cat", ["k", "æ", "t"], ["k", "æ", "t"], 0.0)
                record["per"] = bad
                with self.assertRaises(ValueError):
                    self._items(U.ok(record))

    def test_a_missing_per_raises_even_when_the_clip_is_misaligned(self):
        good = U.record("cat", ["k", "æ", "t"], ["k", "æ", "t"], 0.0)
        bad = U.record("dog", ["d", "ɔ", "g"], ["d", "ɔ", "g"], 0.0)
        bad["per"] = None
        with self.assertRaises(ValueError):
            self._items(U.ok(good, bad))

    def test_an_insertion_without_per_is_fine(self):
        insertion = U.record("", [], ["ʌ"], 0.0, rtype="insertion")
        insertion["per"] = None
        items = self._items(U.ok(U.record("cat", ["k", "æ", "t"], ["k", "æ", "t"], 0.0), insertion))
        self.assertEqual(len(items.words), 1)

    def test_unknown_status_raises_and_names_the_clip(self):
        outcome = U.ok(U.record("cat", ["k", "æ", "t"], ["k", "æ", "t"], 0.0))
        outcome["status"] = "OK"
        with self.assertRaises(ValueError) as ctx:
            self._items(outcome)
        self.assertIn("c9", str(ctx.exception))
        self.assertIn("OK", str(ctx.exception))


class TestSummarize(unittest.TestCase):
    def test_summary(self):
        summary = S.summarize(S.build_items(_clips(), _outcomes()), threshold=0.3)
        word = summary["word"]["all"]
        self.assertEqual(word["counts"], [1, 0, 0, 1])
        self.assertAlmostEqual(word["f05"], 1.0)
        self.assertAlmostEqual(summary["rejection_rate"], 1 / 3)
        self.assertEqual(summary["word"]["adults"]["n"], 0)
        self.assertEqual(summary["best_threshold"]["threshold"], 0.3333)
        self.assertEqual(summary["phone"]["all"]["counts"], [1, 0, 0, 5])
        self.assertIn("sentence", summary["pearson"])

    def test_threshold_above_score_misses(self):
        summary = S.summarize(S.build_items(_clips(), _outcomes()), threshold=0.4)
        self.assertEqual(summary["word"]["all"]["counts"], [0, 0, 1, 1])

    def test_unscored_rate_counts_rejections_and_mismatches(self):
        summary = S.summarize(S.build_items(_clips(), _outcomes()), threshold=0.3)
        # c2 is rejected and c3 does not line up with its scored words.
        self.assertAlmostEqual(summary["unscored_rate"], 2 / 3)
        self.assertAlmostEqual(summary["rejection_rate"], 1 / 3)

    def test_unscored_rate_counts_a_mismatch_that_is_not_a_rejection(self):
        outcomes = _outcomes()
        outcomes["c2"] = U.ok(U.record("a", ["ə"], ["ə"], 0.0))
        summary = S.summarize(S.build_items(_clips(), outcomes), threshold=0.3)
        self.assertEqual(summary["rejection_rate"], 0.0)
        self.assertAlmostEqual(summary["unscored_rate"], 1 / 3)

    def test_empty_summary(self):
        summary = S.summarize(S.build_items([], {}), threshold=0.3)
        self.assertEqual(summary["unscored_rate"], 0.0)
        self.assertEqual(summary["rejection_rate"], 0.0)
        self.assertIsNone(summary["g2p_disagreement_rate"])
        self.assertEqual(summary["flag_all_f05"], 0.0)

    def test_flag_all_f05_is_the_f05_of_flagging_every_word(self):
        summary = S.summarize(S.build_items(_clips(), _outcomes()), threshold=0.3)
        # CAT is correct and DOG is a mistake, so flagging both gives tp 1, fp 1, fn 0.
        # F0.5 = 1.25 * 1 / (1.25 * 1 + 0.25 * 0 + 1) = 5/9.
        self.assertAlmostEqual(summary["flag_all_f05"], 5 / 9)

    def test_flag_all_f05_does_not_depend_on_the_threshold(self):
        items = S.build_items(_clips(), _outcomes())
        self.assertEqual(S.summarize(items, 0.1)["flag_all_f05"], S.summarize(items, 0.9)["flag_all_f05"])

    def test_g2p_disagreement_rate(self):
        summary = S.summarize(S.build_items(_clips(), _outcomes()), threshold=0.3)
        self.assertEqual(summary["g2p_disagreement_rate"], 0.0)

    def test_strict_phone_scoring_counts_heavy_accent_as_a_mistake(self):
        clip = U.synthetic_clip("c5", "s5", 30, [("DOG", 3, "D AO1 G", [2, 1.2, 2])])
        outcome = U.ok(U.record("dog", ["d", "ɔ", "g"], ["d", "ɑ", "g"], 0.3333))
        summary = S.summarize(S.build_items([clip], {"c5": outcome}), threshold=0.3)
        # The vowel scores 1.2, which rounds to 1 (heavy accent). The system flagged it.
        self.assertEqual(summary["phone"]["all"]["counts"], [0, 1, 0, 2])
        self.assertEqual(summary["phone_strict"]["all"]["counts"], [1, 0, 0, 2])
        self.assertNotEqual(summary["phone"]["all"]["f05"], summary["phone_strict"]["all"]["f05"])

    def test_unexpected_failures_are_counted_apart_from_rejections(self):
        outcomes = _outcomes()
        outcomes["c1"] = U.rejected("unexpected:AttributeError")
        outcomes["c2"] = U.rejected("AudioRejected")
        summary = S.summarize(S.build_items(_clips(), outcomes), threshold=0.3)
        self.assertEqual(summary["unexpected_failures"], 1)
        self.assertEqual(summary["rejected"], 2)


def _fb_clip(utt_id, speaker, age, words):
    """A clip from (TEXT, word accuracy) pairs, with an ok outcome whose records line up."""
    clip = U.synthetic_clip(utt_id, speaker, age, [(t, a, "AH0", [2]) for t, a in words])
    records = [U.record(t.lower(), ["ə"], ["ə"], 0.0) for t, _a in words]
    return clip, U.ok(*records)


def _feedback_population():
    """Five clips with feedback and one rejected clip. Accuracy 6 or less is a real mistake."""
    specs = [
        # child. THE appears twice and only the second one is a mistake. Both named words are mistakes.
        ("f1", "s1", 8, [("THE", 10), ("CAT", 3), ("THE", 4)], ("correction", ["the", "cat"])),
        # child, no mistakes. "Dog." and "dog" are one named word after normalizing, read correctly.
        ("f2", "s2", 9, [("DOG", 10), ("SAT", 9)], ("correction", ["Dog.", "dog"])),
        # adult, no mistakes, praised
        ("f3", "s3", 30, [("A", 10), ("B", 10)], ("praise", [])),
        # adult with a mistake, praised anyway
        ("f4", "s4", 40, [("RUN", 2), ("HOME", 10)], ("praise", [])),
        # adult with a mistake, told to keep practicing
        ("f5", "s5", 50, [("SIT", 5), ("UP", 10)], ("generic", [])),
    ]
    clips, outcomes = [], {}
    for utt, spk, age, words, (kind, focus) in specs:
        clip, outcome = _fb_clip(utt, spk, age, words)
        clips.append(clip)
        outcomes[utt] = U.with_feedback(outcome, kind, focus, "k" if focus else None)
    clips.append(U.synthetic_clip("f6", "s6", 30, [("A", 10, "AH0", [2])]))
    outcomes["f6"] = U.rejected()
    return clips, outcomes


class TestFeedbackScoring(unittest.TestCase):
    """Hand-computed feedback metrics. See _feedback_population for the clips."""

    def setUp(self):
        clips, outcomes = _feedback_population()
        self.feedback = S.summarize(S.build_items(clips, outcomes), threshold=0.4)["feedback"]

    def test_all(self):
        m = self.feedback["all"]
        self.assertEqual(m["n_clips"], 5)  # the rejected clip has no feedback
        self.assertEqual(m["kind_share"], {"correction": 0.4, "generic": 0.2, "praise": 0.4})
        self.assertAlmostEqual(m["correction_precision"], 1 / 2)   # f1 yes (THE, via its second occurrence), f2 no
        self.assertAlmostEqual(m["named_word_precision"], 2 / 3)   # the, cat yes; dog no (counted once)
        self.assertAlmostEqual(m["wrong_correction_rate"], 1 / 5)  # f2, out of five clips with feedback
        self.assertAlmostEqual(m["clean_praise_rate"], 1 / 2)      # clean clips f2, f3; f3 praised
        self.assertAlmostEqual(m["false_praise_rate"], 1 / 3)      # clips with a mistake f1, f4, f5; f4 praised
        self.assertEqual(m["counts"]["named_words"], 3)
        self.assertEqual(m["counts"]["first_word_unmatched"], 0)

    def test_children(self):
        m = self.feedback["children"]
        self.assertEqual(m["n_clips"], 2)
        self.assertEqual(m["kind_share"], {"correction": 1.0, "generic": 0.0, "praise": 0.0})
        self.assertAlmostEqual(m["correction_precision"], 1 / 2)
        self.assertAlmostEqual(m["named_word_precision"], 2 / 3)
        self.assertAlmostEqual(m["wrong_correction_rate"], 1 / 2)
        self.assertEqual(m["clean_praise_rate"], 0.0)
        self.assertEqual(m["false_praise_rate"], 0.0)

    def test_adults_with_no_corrections_have_undefined_precision(self):
        m = self.feedback["adults"]
        self.assertEqual(m["n_clips"], 3)
        self.assertEqual(m["kind_share"], {"correction": 0.0, "generic": 1 / 3, "praise": 2 / 3})
        self.assertIsNone(m["correction_precision"])
        self.assertIsNone(m["named_word_precision"])
        self.assertEqual(m["wrong_correction_rate"], 0.0)
        self.assertEqual(m["clean_praise_rate"], 1.0)
        self.assertAlmostEqual(m["false_praise_rate"], 1 / 2)

    def test_results_without_feedback_give_none(self):
        # Results files written before feedback was recorded have no "feedback" key at all.
        summary = S.summarize(S.build_items(_clips(), _outcomes()), threshold=0.3)
        self.assertIn("feedback", summary)
        self.assertIsNone(summary["feedback"])
        self.assertEqual(summary["word"]["all"]["counts"], [1, 0, 0, 1])  # the rest still scores

    def test_feedback_does_not_change_the_word_metrics(self):
        clips, outcomes = _feedback_population()
        bare = {u: {k: v for k, v in o.items() if k != "feedback"} for u, o in outcomes.items()}
        with_fb = S.summarize(S.build_items(clips, outcomes), threshold=0.4)
        without = S.summarize(S.build_items(clips, bare), threshold=0.4)
        self.assertIsNone(without.pop("feedback"))
        with_fb.pop("feedback")
        self.assertEqual(with_fb, without)

    def test_a_named_word_not_in_the_clip_is_neither_a_mistake_nor_correct(self):
        clip, outcome = _fb_clip("g1", "t1", 30, [("CAT", 3), ("DOG", 10)])
        outcome = U.with_feedback(outcome, "correction", ["fish", "cat"], "f")
        m = S.summarize(S.build_items([clip], {"g1": outcome}), 0.4)["feedback"]["all"]
        self.assertEqual(m["correction_precision"], 0.0)
        self.assertEqual(m["wrong_correction_rate"], 0.0)
        self.assertAlmostEqual(m["named_word_precision"], 1 / 2)
        self.assertEqual(m["counts"]["first_word_unmatched"], 1)

    def test_a_misaligned_clip_still_has_its_feedback_scored(self):
        # The words are matched by text, so the feedback is scored even when the word records
        # do not line up with the scored words (and the clip drops out of the word metrics).
        clip, _outcome = _fb_clip("g2", "t2", 30, [("CAT", 3), ("DOG", 10)])
        outcome = U.with_feedback(U.ok(U.record("cat", ["ə"], ["ə"], 0.5)), "correction", ["cat"], "k")
        summary = S.summarize(S.build_items([clip], {"g2": outcome}), 0.4)
        self.assertEqual(summary["word_count_mismatch"], 1)
        self.assertEqual(summary["feedback"]["all"]["n_clips"], 1)
        self.assertEqual(summary["feedback"]["all"]["correction_precision"], 1.0)

    def test_an_unknown_feedback_kind_raises_and_names_the_clip(self):
        clip, outcome = _fb_clip("g3", "t3", 30, [("CAT", 3), ("DOG", 10)])
        with self.assertRaises(ValueError) as ctx:
            S.build_items([clip], {"g3": U.with_feedback(outcome, "Praise")})
        self.assertIn("g3", str(ctx.exception))

    def test_speaker_counts_add_up_to_the_rates(self):
        clips, outcomes = _feedback_population()
        items = S.build_items(clips, outcomes)
        for rate in ("correction_precision", "wrong_correction_rate"):
            counts = S.feedback_rate_counts(items, rate)
            self.assertEqual(sorted(counts), ["s1", "s2", "s3", "s4", "s5"])
            num, den = sum(c[0] for c in counts.values()), sum(c[1] for c in counts.values())
            self.assertAlmostEqual(num / den, self.feedback["all"][rate])

    def test_normalize_word(self):
        self.assertEqual(S.normalize_word("Dog."), "dog")
        self.assertEqual(S.normalize_word("DON'T"), "dont")
        self.assertEqual(S.normalize_word(" the "), "the")


if __name__ == "__main__":
    unittest.main()
