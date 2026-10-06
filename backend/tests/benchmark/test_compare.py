import json
import os
import tempfile
import unittest
from unittest import mock

from tests.benchmark import common
from tests.benchmark import compare as C
from tests.benchmark import testutil as U


def _population(n=10):
    clips, base, cand = [], {}, {}
    for i in range(n):
        utt = f"u{i}"
        clips.append(U.synthetic_clip(utt, f"s{i}", 8 if i % 2 else 30, [
            ("CAT", 10, "K AE1 T", [2, 2, 2]),
            ("DOG", 3, "D AO1 G", [2, 0, 2]),
        ]))
        cat = U.record("cat", ["k", "æ", "t"], ["k", "æ", "t"], 0.0)
        base[utt] = U.ok(cat, U.record("dog", ["d", "ɔ", "g"], ["d", "ɔ", "g"], 0.0))
        cand[utt] = U.ok(cat, U.record("dog", ["d", "ɔ", "g"], ["d", "ɑ", "g"], 0.6667))
    return clips, base, cand


class TestCompareResults(unittest.TestCase):
    def setUp(self):
        self.clips, self.base, self.cand = _population()

    def _compare(self, base, cand):
        return C.compare_results(U.results_dict("base", base), U.results_dict("cand", cand), self.clips, n_resamples=300)

    def test_identical_is_not_an_improvement(self):
        result = self._compare(self.base, self.base)
        self.assertEqual(result["f05_ci"], [0.0, 0.0])
        self.assertFalse(result["checks"][0]["passed"])
        self.assertTrue(all(c["passed"] for c in result["checks"][1:]))
        self.assertFalse(result["passed"])

    def test_clear_win_passes(self):
        result = self._compare(self.base, self.cand)
        self.assertGreater(result["f05_ci"][0], 0)
        self.assertEqual(len(result["checks"]), 5)
        self.assertTrue(all(c["passed"] for c in result["checks"]), C.format_comparison(result))
        self.assertTrue(result["passed"], C.format_comparison(result))

    def test_more_false_alarms_fail(self):
        noisy = {u: U.ok(U.record("cat", ["k", "æ", "t"], ["k", "ɛ", "t"], 0.6667), o["words"][1])
                 for u, o in self.cand.items()}
        result = self._compare(self.base, noisy)
        self.assertFalse(result["checks"][2]["passed"])

    def test_more_rejections_fail(self):
        hiding = dict(self.cand)
        hiding["u0"] = U.rejected()
        result = self._compare(self.base, hiding)
        self.assertFalse(result["checks"][3]["passed"])

    def test_more_misaligned_clips_fail_even_without_more_rejections(self):
        # u0 comes back with one word record for two scored words, so it drops out of every metric.
        hiding = dict(self.cand)
        hiding["u0"] = U.ok(self.cand["u0"]["words"][0])
        result = self._compare(self.base, hiding)
        self.assertEqual(result["rejection_delta"], 0.0)
        self.assertAlmostEqual(result["unscored_delta"], 0.1)
        self.assertFalse(result["checks"][3]["passed"])
        self.assertEqual(result["checks"][3]["name"], "no hiding")
        self.assertEqual(result["checks"][3]["rule"], "unscored rate (rejected or misaligned clips) rises <= 0.01")
        self.assertFalse(result["passed"])

    def test_a_record_about_the_wrong_word_counts_as_misaligned(self):
        hiding = dict(self.cand)
        hiding["u0"] = U.ok(self.cand["u0"]["words"][0], U.record("fox", ["f", "ɑ", "k", "s"], ["f", "ɑ", "k", "s"], 0.0))
        result = self._compare(self.base, hiding)
        self.assertFalse(result["checks"][3]["passed"])

    def test_misaligned_clips_in_both_runs_are_not_a_new_loss(self):
        base, cand = dict(self.base), dict(self.cand)
        base["u0"] = U.ok(self.base["u0"]["words"][0])
        cand["u0"] = U.ok(self.cand["u0"]["words"][0])
        result = self._compare(base, cand)
        self.assertEqual(result["unscored_delta"], 0.0)
        self.assertTrue(result["checks"][3]["passed"])

    def test_format_shows_the_unscored_rate(self):
        text = C.format_comparison(self._compare(self.base, self.cand))
        self.assertIn("unscored rate", text)
        self.assertIn("unscored rate (rejected or misaligned clips) rises <= 0.01", text)

    def test_new_unexpected_failure_fails(self):
        crashing = dict(self.cand)
        crashing["u0"] = U.rejected("unexpected:KeyError")
        result = self._compare(self.base, crashing)
        self.assertFalse(result["checks"][4]["passed"])
        self.assertEqual(result["checks"][4]["value"], "+1")
        self.assertFalse(result["passed"])

    def test_accept_line_names_the_fifth_check(self):
        text = C.format_comparison(self._compare(self.base, self.cand))
        self.assertEqual(
            text.splitlines()[-1],
            "ACCEPT on conditions 1-4 and no new unexpected failures (speed and tests are checked separately)",
        )

    def test_reject_line_when_a_check_fails(self):
        crashing = dict(self.cand)
        crashing["u0"] = U.rejected("unexpected:KeyError")
        self.assertEqual(C.format_comparison(self._compare(self.base, crashing)).splitlines()[-1], "REJECT")

    def test_not_comparable(self):
        with self.assertRaises(C.NotComparable):
            C.compare_results(U.results_dict("a", self.base), U.results_dict("b", self.base, half="test"), self.clips)
        with self.assertRaises(C.NotComparable):
            C.compare_results(U.results_dict("a", self.base), U.results_dict("b", {"u0": self.base["u0"]}), self.clips)


class TestChildrenCheck(unittest.TestCase):
    """Check 2 passes unless the children F0.5 difference is significantly below zero."""

    def setUp(self):
        # 24 clips, so 12 child speakers (odd i) and 12 adults. The candidate of _population
        # flags every wrong DOG, so it is the reference that a worse candidate is compared with.
        self.clips, _unused, self.good = _population(24)
        self.child_ids = [u for u in self.good if int(u[1:]) % 2]

    def _compare(self, base, cand, clips=None):
        return C.compare_results(U.results_dict("base", base), U.results_dict("cand", cand),
                                 clips or self.clips, n_resamples=500)

    def _unflag_dog(self, outcomes, utt_ids):
        worse = dict(outcomes)
        for utt in utt_ids:
            cat, _dog = outcomes[utt]["words"]
            worse[utt] = U.ok(cat, U.record("dog", ["d", "ɔ", "g"], ["d", "ɔ", "g"], 0.0))
        return worse

    def test_slightly_worse_within_noise_passes(self):
        worse = self._unflag_dog(self.good, self.child_ids[:1])
        result = self._compare(self.good, worse)
        self.assertLess(result["children_f05_delta"], 0)  # the point estimate is below zero ...
        low, high = result["children_f05_ci"]
        self.assertGreaterEqual(high, 0)  # ... but the interval still reaches zero
        check = result["checks"][1]
        self.assertTrue(check["passed"], C.format_comparison(result))
        self.assertEqual(check["rule"], "children F0.5 not significantly worse (95% CI upper bound >= 0)")
        self.assertIn(f"{result['children_f05_delta']:+.4f}", check["value"])
        self.assertIn(f"[{low:+.4f}, {high:+.4f}]", check["value"])

    def test_clearly_worse_on_every_child_speaker_fails(self):
        worse = self._unflag_dog(self.good, self.child_ids)
        result = self._compare(self.good, worse)
        self.assertLess(result["children_f05_ci"][1], 0)
        self.assertFalse(result["checks"][1]["passed"])
        self.assertFalse(result["passed"])

    def test_better_on_children_passes(self):
        result = self._compare(self._unflag_dog(self.good, self.child_ids), self.good)
        self.assertGreater(result["children_f05_ci"][0], 0)
        self.assertTrue(result["checks"][1]["passed"])

    def test_identical_results_pass(self):
        result = self._compare(self.good, self.good)
        self.assertEqual(result["children_f05_ci"], [0.0, 0.0])
        self.assertTrue(result["checks"][1]["passed"])

    def test_losing_all_child_clips_fails(self):
        # Every child clip is rejected by the candidate, so no child words are left to score.
        lost = dict(self.good)
        for utt in self.child_ids:
            lost[utt] = U.rejected()
        result = self._compare(self.good, lost)
        self.assertFalse(result["checks"][1]["passed"])

    def test_no_child_words_passes(self):
        adults = [U.synthetic_clip(f"a{i}", f"adult{i}", 30, [
            ("CAT", 10, "K AE1 T", [2, 2, 2]), ("DOG", 3, "D AO1 G", [2, 0, 2])]) for i in range(4)]
        cat = U.record("cat", ["k", "æ", "t"], ["k", "æ", "t"], 0.0)
        outcomes = {c.utt_id: U.ok(cat, U.record("dog", ["d", "ɔ", "g"], ["d", "ɔ", "g"], 0.0)) for c in adults}
        result = self._compare(outcomes, outcomes, clips=adults)
        self.assertEqual(result["checks"][1]["value"], "no child words")
        self.assertTrue(result["checks"][1]["passed"])
        self.assertIsNone(result["children_f05_ci"])
        self.assertEqual(result["children_f05_delta"], 0.0)
        C.format_comparison(result)  # must not choke on the missing interval


class TestMain(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        U.make_temp_dataset(self.tmp.name)
        self.env = mock.patch.dict(os.environ, {common.DATA_DIR_ENV: self.tmp.name})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def _write(self, name, results):
        path = os.path.join(self.tmp.name, f"{name}.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(results, fh, ensure_ascii=False)
        return path

    def _outcomes(self, flag_mistakes):
        from tests.benchmark.dataset import load_half
        from tests.benchmark.phones import canonical_ipa

        outcomes = {}
        for clip in load_half(os.path.join(self.tmp.name, "speechocean762"), "dev"):
            records = []
            for w in clip.words:
                ipa = canonical_ipa(w.phones)
                per = 1.0 if (flag_mistakes and w.accuracy <= 6) else 0.0
                records.append(U.record(w.text.lower(), ipa, [] if per else ipa, per))
            outcomes[clip.utt_id] = U.ok(*records)
        return outcomes

    def test_exit_codes(self):
        base = self._write("base", U.results_dict("base", self._outcomes(False)))
        good = self._write("good", U.results_dict("good", self._outcomes(True)))
        other = self._write("other", U.results_dict("other", self._outcomes(True), half="test"))
        self.assertEqual(C.main([base, good, "--resamples", "200"]), 0)
        self.assertEqual(C.main([base, base, "--resamples", "200"]), 1)
        self.assertEqual(C.main([base, other]), 2)


if __name__ == "__main__":
    unittest.main()
