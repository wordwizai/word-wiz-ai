import unittest

import numpy as np

from tests.benchmark import metrics as M


def _naive_rows(labels, scores):
    for t in sorted(set(scores), reverse=True):
        yield t, M.confusion(labels, M.flags_at(scores, t))


def _naive_best(labels, scores, beta=M.F_BETA):
    best_t, best_f = None, 0.0
    for t, c in _naive_rows(labels, scores):
        f = c.f_beta(beta)
        if f > best_f:
            best_t, best_f = t, f
    return best_t, best_f


def _naive_curve(labels, scores):
    return [
        {"threshold": t, "precision": c.precision, "recall": c.recall, "false_alarm_rate": c.false_alarm_rate}
        for t, c in reversed(list(_naive_rows(labels, scores)))
    ]


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

    def test_best_threshold_tie_goes_to_higher(self):
        labels = [True, True, True, True, False] + [False] * 10
        scores = [0.9, 0.5, 0.1, 0.1, 0.5] + [0.1] * 10
        self.assertEqual(M.best_threshold(labels, scores), (0.9, 0.625))

    def test_matches_brute_force(self):
        rng = np.random.default_rng(0)
        for case in range(200):
            n = int(rng.integers(1, 61))
            labels = [bool(v) for v in rng.integers(0, 2, size=n)]
            if case % 4 == 3:
                scores = [float(v) for v in rng.random(n)]
            else:
                scores = [float(v) for v in rng.choice([0, 0.25, 0.3333, 0.5, 0.75, 1.0], size=n)]
            exp_t, exp_f = _naive_best(labels, scores)
            got_t, got_f = M.best_threshold(labels, scores)
            self.assertEqual(got_t, exp_t)
            self.assertAlmostEqual(got_f, exp_f)
            exp_curve = _naive_curve(labels, scores)
            got_curve = M.pr_curve(labels, scores, max_points=10**6)
            self.assertEqual(len(got_curve), len(exp_curve))
            for g, e in zip(got_curve, exp_curve):
                self.assertEqual(g["threshold"], e["threshold"])
                for k in ("precision", "recall", "false_alarm_rate"):
                    self.assertAlmostEqual(g[k], e[k])

    def test_pr_curve_caps_length(self):
        rng = np.random.default_rng(1)
        scores = [float(v) for v in rng.permutation(1000)]
        labels = [bool(v) for v in rng.integers(0, 2, size=1000)]
        curve = M.pr_curve(labels, scores, max_points=50)
        self.assertLessEqual(len(curve), 50)
        self.assertEqual(curve[0]["threshold"], min(scores))
        self.assertEqual(curve[-1]["threshold"], max(scores))


class TestPearson(unittest.TestCase):
    def test_perfect(self):
        self.assertAlmostEqual(M.pearson([1, 2, 3], [2, 4, 6]), 1.0)

    def test_undefined(self):
        self.assertIsNone(M.pearson([1, 1, 1], [1, 2, 3]))
        self.assertIsNone(M.pearson([1], [1]))
        self.assertIsNone(M.pearson([0.1, 0.1, 0.1], [1, 2, 3]))
        self.assertIsNone(M.pearson([1, float("nan"), 3], [1, 2, 3]))


class TestBootstrap(unittest.TestCase):
    def test_per_speaker_counts(self):
        counts = M.per_speaker_counts(["a", "a", "b"], [True, False, True], [True, True, False])
        self.assertEqual(counts["a"].tolist(), [1, 1, 0, 0])
        self.assertEqual(counts["b"].tolist(), [0, 0, 1, 0])

    def test_per_speaker_counts_length_mismatch(self):
        with self.assertRaises(ValueError):
            M.per_speaker_counts(["a", "b"], [True], [True, False])

    def test_speaker_in_one_system_only(self):
        base = {"a": [1, 0, 0, 1], "b": [0, 0, 1, 1]}
        cand = {"a": [1, 0, 0, 1]}
        deltas = M.bootstrap_fbeta_delta(base, cand, n_resamples=50)
        self.assertEqual(deltas.shape, (50,))
        self.assertTrue(np.all(np.isfinite(deltas)))

    def test_invalid_arguments(self):
        with self.assertRaises(ValueError):
            M.bootstrap_fbeta_delta({"a": [1, 0, 0, 1]}, {"a": [1, 0, 0, 1]}, n_resamples=0)
        with self.assertRaises(ValueError):
            M.percentile_interval([])

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

    def test_fbeta_draws_are_pinned(self):
        # Values from before the resampling was shared with bootstrap_ratio_delta, so the
        # F0.5 intervals in compare stay exactly what they were.
        base = {"a": np.array([1, 2, 1, 5]), "b": np.array([0, 1, 2, 6]), "c": np.array([2, 0, 0, 3])}
        cand = {"a": np.array([2, 1, 0, 6]), "b": np.array([1, 1, 1, 6]), "c": np.array([1, 1, 1, 2])}
        deltas = M.bootstrap_fbeta_delta(base, cand, n_resamples=5, seed=7)
        self.assertEqual(deltas.round(6).tolist(), [-0.269231, -0.269231, 0.131579, 0.131579, 0.088235])


class TestRatioBootstrap(unittest.TestCase):
    """Counts are (numerator, denominator) per speaker, as for the feedback rates."""

    def test_ratio_from_counts(self):
        self.assertEqual(M.ratio_from_counts([[1, 4], [0, 0], [3, 3]]).tolist(), [0.25, 0.0, 1.0])

    def test_identical_systems_give_zero(self):
        counts = {"a": np.array([1, 3]), "b": np.array([2, 2])}
        self.assertTrue(np.all(M.bootstrap_ratio_delta(counts, counts, n_resamples=200) == 0))

    def test_clear_win(self):
        base = {s: np.array([0, 4]) for s in "abcd"}
        cand = {s: np.array([4, 4]) for s in "abcd"}
        lo, hi = M.percentile_interval(M.bootstrap_ratio_delta(base, cand, n_resamples=200))
        self.assertEqual((lo, hi), (1.0, 1.0))

    def test_pools_counts_rather_than_averaging_speaker_ratios(self):
        # One resample that picks a and b once each: (1 + 0) / (1 + 3) = 0.25, not (1 + 0) / 2.
        base = {"a": np.array([0, 1]), "b": np.array([0, 3])}
        cand = {"a": np.array([1, 1]), "b": np.array([0, 3])}
        values = set(np.round(M.bootstrap_ratio_delta(base, cand, n_resamples=500, seed=1), 6).tolist())
        self.assertEqual(values, {0.0, 0.25, 1.0})  # averaging the speakers' ratios would give 0.5

    def test_same_draws_as_the_fbeta_bootstrap(self):
        # Speaker a holds every positive. Both bootstraps resample speakers the same way, so a
        # resample without a has delta 0 in both.
        f_base = {"a": np.array([0, 0, 2, 2]), "b": np.array([0, 0, 0, 4]), "c": np.array([0, 0, 0, 4])}
        f_cand = {"a": np.array([2, 0, 0, 2]), "b": np.array([0, 0, 0, 4]), "c": np.array([0, 0, 0, 4])}
        r_base = {"a": np.array([0, 2]), "b": np.array([0, 0]), "c": np.array([0, 0])}
        r_cand = {"a": np.array([2, 2]), "b": np.array([0, 0]), "c": np.array([0, 0])}
        f = M.bootstrap_fbeta_delta(f_base, f_cand, n_resamples=100, seed=3)
        r = M.bootstrap_ratio_delta(r_base, r_cand, n_resamples=100, seed=3)
        self.assertTrue(np.array_equal(f == 0, r == 0))

    def test_invalid_arguments(self):
        with self.assertRaises(ValueError):
            M.bootstrap_ratio_delta({"a": [1, 1]}, {"a": [1, 1]}, n_resamples=0)
        with self.assertRaises(ValueError):
            M.bootstrap_ratio_delta({}, {})


if __name__ == "__main__":
    unittest.main()
