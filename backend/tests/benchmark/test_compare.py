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

    def test_new_unexpected_failure_fails(self):
        crashing = dict(self.cand)
        crashing["u0"] = U.rejected("unexpected:KeyError")
        result = self._compare(self.base, crashing)
        self.assertFalse(result["checks"][4]["passed"])
        self.assertEqual(result["checks"][4]["value"], "+1")
        self.assertFalse(result["passed"])

    def test_not_comparable(self):
        with self.assertRaises(C.NotComparable):
            C.compare_results(U.results_dict("a", self.base), U.results_dict("b", self.base, half="test"), self.clips)
        with self.assertRaises(C.NotComparable):
            C.compare_results(U.results_dict("a", self.base), U.results_dict("b", {"u0": self.base["u0"]}), self.clips)


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
