import unittest

import numpy as np

from tests.benchmark import metrics as M


class TestMistakeDefinitions(unittest.TestCase):
    def test_rounded_is_half_up(self):
        self.assertEqual([M.rounded(x) for x in (1.8, 0.4, 0.5, 6.5, 6.4)], [2, 0, 1, 7, 6])

    def test_word_cutoff_is_six(self):
        self.assertTrue(M.word_is_mistake(6))
        self.assertFalse(M.word_is_mistake(7))
        self.assertFalse(M.word_is_mistake(6.6))
        self.assertTrue(M.word_is_mistake(0))

    def test_phone_cutoffs(self):
        self.assertTrue(M.phone_is_mistake(0.4))
        self.assertFalse(M.phone_is_mistake(0.6))
        self.assertTrue(M.phone_is_mistake(1.2, strict=True))
        self.assertFalse(M.phone_is_mistake(1.6, strict=True))


class TestCounts(unittest.TestCase):
    def setUp(self):
        self.c = M.confusion([True, True, False, False, True], [True, False, True, False, True])

    def test_confusion(self):
        self.assertEqual((self.c.tp, self.c.fp, self.c.fn, self.c.tn), (2, 1, 1, 1))

    def test_rates(self):
        self.assertAlmostEqual(self.c.precision, 2 / 3)
        self.assertAlmostEqual(self.c.recall, 2 / 3)
        self.assertAlmostEqual(self.c.false_alarm_rate, 0.5)

    def test_f_half(self):
        # (1.25 * 2) / (1.25 * 2 + 0.25 * 1 + 1) = 2.5 / 3.75
        self.assertAlmostEqual(self.c.f_beta(), 2.5 / 3.75)

    def test_undefined_is_zero(self):
        empty = M.confusion([False, False], [False, False])
        self.assertEqual(empty.f_beta(), 0.0)
        self.assertEqual(empty.precision, 0.0)

    def test_length_mismatch(self):
        with self.assertRaises(ValueError):
            M.confusion([True], [True, False])

    def test_vectorized_f_beta(self):
        out = M.f_beta_from_counts(np.array([[2, 1, 1, 1], [0, 0, 0, 5]]))
        self.assertAlmostEqual(out[0], 2.5 / 3.75)
        self.assertEqual(out[1], 0.0)


class TestThresholds(unittest.TestCase):
    def test_best_threshold(self):
        t, f = M.best_threshold([True, True, False, False], [0.9, 0.6, 0.5, 0.1])
        self.assertEqual(t, 0.6)
        self.assertAlmostEqual(f, 1.0)

    def test_best_threshold_without_positives(self):
        self.assertEqual(M.best_threshold([False, False], [0.3, 0.7]), (None, 0.0))

    def test_pr_curve_has_one_point_per_threshold(self):
        curve = M.pr_curve([True, False, True], [0.2, 0.5, 0.5])
        self.assertEqual([p["threshold"] for p in curve], [0.2, 0.5])
        self.assertAlmostEqual(curve[1]["precision"], 0.5)


class TestPearson(unittest.TestCase):
    def test_perfect(self):
        self.assertAlmostEqual(M.pearson([1, 2, 3], [2, 4, 6]), 1.0)

    def test_undefined(self):
        self.assertIsNone(M.pearson([1, 1, 1], [1, 2, 3]))
        self.assertIsNone(M.pearson([1], [1]))


class TestBootstrap(unittest.TestCase):
    def test_per_speaker_counts(self):
        counts = M.per_speaker_counts(["a", "a", "b"], [True, False, True], [True, True, False])
        self.assertEqual(counts["a"].tolist(), [1, 1, 0, 0])
        self.assertEqual(counts["b"].tolist(), [0, 0, 1, 0])

    def test_identical_systems_give_zero(self):
        counts = {"a": np.array([1, 1, 1, 5]), "b": np.array([2, 0, 1, 4])}
        deltas = M.bootstrap_fbeta_delta(counts, counts, n_resamples=200)
        self.assertTrue(np.all(deltas == 0))

    def test_clear_win(self):
        base = {s: np.array([0, 0, 2, 8]) for s in "abcd"}
        cand = {s: np.array([2, 0, 0, 8]) for s in "abcd"}
        lo, hi = M.percentile_interval(M.bootstrap_fbeta_delta(base, cand, n_resamples=200))
        self.assertAlmostEqual(lo, 1.0)
        self.assertAlmostEqual(hi, 1.0)

    def test_seeded(self):
        base = {"a": np.array([1, 2, 1, 5]), "b": np.array([0, 1, 2, 6]), "c": np.array([2, 0, 0, 3])}
        cand = {"a": np.array([2, 1, 0, 6]), "b": np.array([1, 1, 1, 6]), "c": np.array([1, 1, 1, 2])}
        a = M.bootstrap_fbeta_delta(base, cand, n_resamples=100, seed=7)
        b = M.bootstrap_fbeta_delta(base, cand, n_resamples=100, seed=7)
        self.assertTrue(np.array_equal(a, b))

    def test_percentile_interval(self):
        lo, hi = M.percentile_interval(np.arange(101), level=0.9)
        self.assertAlmostEqual(lo, 5.0)
        self.assertAlmostEqual(hi, 95.0)


if __name__ == "__main__":
    unittest.main()
