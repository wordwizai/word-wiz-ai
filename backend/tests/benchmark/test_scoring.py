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

    def test_unexpected_failures_are_counted_apart_from_rejections(self):
        outcomes = _outcomes()
        outcomes["c1"] = U.rejected("unexpected:AttributeError")
        outcomes["c2"] = U.rejected("AudioRejected")
        summary = S.summarize(S.build_items(_clips(), outcomes), threshold=0.3)
        self.assertEqual(summary["unexpected_failures"], 1)
        self.assertEqual(summary["rejected"], 2)


if __name__ == "__main__":
    unittest.main()
