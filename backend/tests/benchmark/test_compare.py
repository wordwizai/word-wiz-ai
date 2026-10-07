import io
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


class TestFeedbackRows(unittest.TestCase):
    """Feedback metrics are printed with paired intervals but never decide the outcome."""

    def setUp(self):
        self.clips, self.base, self.cand = _population()

    def _compare(self, base, cand):
        return C.compare_results(U.results_dict("base", base), U.results_dict("cand", cand), self.clips, n_resamples=300)

    def _with(self, outcomes, word):
        # Every clip gets a correction that names `word`. CAT is read correctly, DOG is a mistake.
        return {u: U.with_feedback(o, "correction", [word], "k") for u, o in outcomes.items()}

    def test_rows_and_intervals(self):
        result = self._compare(self._with(self.base, "cat"), self._with(self.cand, "dog"))
        fb = result["feedback"]
        self.assertAlmostEqual(fb["correction_precision"]["delta"], 1.0)
        self.assertEqual(fb["correction_precision"]["ci"], [1.0, 1.0])
        self.assertAlmostEqual(fb["wrong_correction_rate"]["delta"], -1.0)
        self.assertEqual(fb["wrong_correction_rate"]["ci"], [-1.0, -1.0])
        text = C.format_comparison(result)
        lines = text.splitlines()
        word_row = next(i for i, line in enumerate(lines) if line.startswith("false-alarm rate"))
        precision_row = next(i for i, line in enumerate(lines) if line.startswith("correction precision "))
        self.assertGreater(precision_row, word_row)  # after the existing word rows
        self.assertRegex(lines[precision_row], r"0\.0000\s+1\.0000\s+\+1\.0000$")
        self.assertIn("wrong-correction rate", text)
        self.assertIn("correction precision difference, 95% CI [+1.0000, +1.0000]", text)
        self.assertIn("wrong-correction rate difference, 95% CI [-1.0000, -1.0000]", text)

    def test_identical_feedback_gives_a_zero_interval(self):
        same = self._with(self.base, "dog")
        fb = self._compare(same, same)["feedback"]
        self.assertEqual(fb["correction_precision"]["ci"], [0.0, 0.0])
        self.assertEqual(fb["wrong_correction_rate"]["ci"], [0.0, 0.0])

    def test_feedback_never_changes_the_checks(self):
        plain = self._compare(self.base, self.cand)
        # The candidate's feedback is much worse, and the result must not move.
        worse = self._compare(self._with(self.base, "dog"), self._with(self.cand, "cat"))
        self.assertEqual(worse["checks"], plain["checks"])
        self.assertEqual(worse["passed"], plain["passed"])
        self.assertTrue(worse["passed"])
        self.assertEqual(len(worse["checks"]), 5)

    def test_a_file_without_feedback_skips_the_rows(self):
        for base, cand, missing in ((self.base, self._with(self.cand, "dog"), "base"),
                                    (self._with(self.base, "dog"), self.cand, "candidate"),
                                    (self.base, self.cand, "base and candidate")):
            with self.subTest(missing=missing):
                result = self._compare(base, cand)
                self.assertIsNone(result["feedback"])
                text = C.format_comparison(result)
                self.assertNotIn("correction precision", text)
                skipped = [line for line in text.splitlines() if "feedback" in line]
                self.assertEqual(len(skipped), 1)
                self.assertIn(f"the {missing} results", skipped[0])
                self.assertEqual(result["checks"], self._compare(self.base, self.cand)["checks"])

    def test_undefined_precision_prints_as_n_a(self):
        praised = {u: U.with_feedback(o, "praise") for u, o in self.base.items()}
        result = self._compare(praised, self._with(self.cand, "dog"))
        self.assertIsNone(result["base_summary"]["feedback"]["all"]["correction_precision"])
        self.assertIsNone(result["feedback"]["correction_precision"]["delta"])
        self.assertIsNone(result["feedback"]["correction_precision"]["ci"])
        text = C.format_comparison(result)
        row = next(line for line in text.splitlines() if line.startswith("correction precision "))
        self.assertRegex(row, r"n/a\s+1\.0000\s+n/a$")
        self.assertIn("correction precision difference, 95% CI n/a", text)


def _with_flags(outcomes, dog_flag):
    """The outcomes with production's stored decision: CAT never flagged, DOG flagged or not."""
    flagged = {}
    for utt, outcome in outcomes.items():
        cat, dog = outcome["words"]
        flagged[utt] = U.ok(dict(cat, flagged=False), dict(dog, flagged=dog_flag))
    return flagged


class TestFlagRules(unittest.TestCase):
    """Each side is scored, and labelled, by the flag rule of the code that wrote it."""

    def setUp(self):
        self.clips, self.base, self.cand = _population()

    def _compare(self, base, cand):
        return C.compare_results(base, cand, self.clips, n_resamples=300)

    def test_each_sides_rule_is_printed_under_the_header(self):
        result = self._compare(U.results_dict("base", self.base),
                               U.results_dict("cand", _with_flags(self.cand, True), flag_rule="total_errors >= 3"))
        self.assertEqual((result["base_flag_rule"], result["candidate_flag_rule"]),
                         ("per >= 0.4", "total_errors >= 3"))
        lines = C.format_comparison(result).splitlines()
        self.assertEqual(lines[0], "base (server path)  ->  cand (server path)   (dev half)")
        self.assertEqual(lines[1], "flag rule per >= 0.4  ->  total_errors >= 3")

    def test_stored_flags_decide_the_word_metrics(self):
        # The candidate's DOG records have per 0.6667, but production did not flag them, so the
        # candidate is no better than the base. Without stored flags it is a clear win.
        base = U.results_dict("base", self.base)
        unflagged = U.results_dict("cand", _with_flags(self.cand, False), flag_rule="total_errors >= 3")
        result = self._compare(base, unflagged)
        self.assertEqual(result["f05_ci"], [0.0, 0.0])
        self.assertFalse(result["passed"])
        self.assertTrue(self._compare(base, U.results_dict("cand", self.cand))["passed"])
        flagged = U.results_dict("cand", _with_flags(self.base, True), flag_rule="total_errors >= 3")
        self.assertTrue(self._compare(base, flagged)["passed"])  # flags the mistakes whatever the PER

    def test_an_override_file_is_scored_at_its_threshold(self):
        override = U.results_dict("cand", _with_flags(self.cand, False), threshold=0.5,
                                  flag_rule="per >= 0.5 (override)")
        result = self._compare(U.results_dict("base", self.base), override)
        self.assertTrue(result["passed"], C.format_comparison(result))
        self.assertEqual(C.format_comparison(result).splitlines()[1],
                         "flag rule per >= 0.4  ->  per >= 0.5 (override)")


class TestPathGuard(unittest.TestCase):
    """Runs of the server path and the client path measure different request paths."""

    def setUp(self):
        self.clips, self.base, self.cand = _population()

    def _compare(self, base_path, cand_path, **kwargs):
        return C.compare_results(U.results_dict("base", self.base, path=base_path),
                                 U.results_dict("cand", self.cand, path=cand_path),
                                 self.clips, n_resamples=200, **kwargs)

    def test_different_paths_are_not_comparable(self):
        for base_path, cand_path in (("server", "client"), ("client", "server"), (None, "client")):
            with self.subTest(base=base_path, cand=cand_path):
                with self.assertRaises(C.NotComparable) as ctx:
                    self._compare(base_path, cand_path)
                self.assertIn("--allow-path-mismatch", str(ctx.exception))
                self.assertIn("client path", str(ctx.exception))

    def test_a_file_without_a_path_counts_as_the_server_path(self):
        result = self._compare(None, "server")
        self.assertEqual((result["base_path"], result["candidate_path"]), ("server", "server"))
        self.assertIsNone(result["path_warning"])

    def test_the_same_path_compares_without_a_warning(self):
        result = self._compare("client", "client")
        self.assertIsNone(result["path_warning"])
        text = C.format_comparison(result)
        self.assertNotIn("WARNING", text)
        self.assertEqual(text.splitlines()[0], "base (client path)  ->  cand (client path)   (dev half)")

    def test_allowing_a_mismatch_compares_and_prints_one_warning_line(self):
        allowed = self._compare("server", "client", allow_path_mismatch=True)
        plain = self._compare("client", "client")
        self.assertEqual(allowed["checks"], plain["checks"])
        self.assertIn("server path", allowed["path_warning"])
        lines = C.format_comparison(allowed).splitlines()
        self.assertEqual(lines[0], "base (server path)  ->  cand (client path)   (dev half)")
        warnings = [line for line in lines if line.startswith("WARNING")]
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0], "WARNING: " + allowed["path_warning"])

    def test_main_refuses_a_mismatch_unless_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            U.make_temp_dataset(tmp)
            paths = {}
            for name, path in (("server", "server"), ("client", "client")):
                paths[name] = os.path.join(tmp, f"{name}.json")
                with open(paths[name], "w", encoding="utf-8") as fh:
                    json.dump(U.results_dict(name, _mini_outcomes(tmp), path=path), fh, ensure_ascii=False)
            with mock.patch.dict(os.environ, {common.DATA_DIR_ENV: tmp}):
                with mock.patch("sys.stderr", new_callable=io.StringIO) as err:
                    self.assertEqual(C.main([paths["server"], paths["client"], "--resamples", "50"]), 2)
                self.assertIn("--allow-path-mismatch", err.getvalue())
                with mock.patch("sys.stdout", new_callable=io.StringIO) as out:
                    code = C.main([paths["server"], paths["client"], "--resamples", "50", "--allow-path-mismatch"])
                self.assertEqual(code, 1)  # identical outcomes are not an improvement
                self.assertEqual(sum(line.startswith("WARNING") for line in out.getvalue().splitlines()), 1)


def _mini_outcomes(tmp):
    """Perfect outcomes for every dev clip of the mini fixture copied into tmp."""
    from tests.benchmark.dataset import load_half
    from tests.benchmark.phones import canonical_ipa

    outcomes = {}
    for clip in load_half(os.path.join(tmp, "speechocean762"), "dev"):
        records = [U.record(w.text.lower(), canonical_ipa(w.phones), canonical_ipa(w.phones), 0.0) for w in clip.words]
        outcomes[clip.utt_id] = U.ok(*records)
    return outcomes


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

    def test_exit_codes_ignore_feedback_and_survive_a_file_without_it(self):
        def corrections(outcomes, word_index):
            # A correction naming one scored word of each clip (the first or the last).
            from tests.benchmark.dataset import load_half

            clips = {c.utt_id: c for c in load_half(os.path.join(self.tmp.name, "speechocean762"), "dev")}
            return {u: U.with_feedback(o, "correction", [clips[u].words[word_index].text], "k")
                    for u, o in outcomes.items()}

        old_base = self._write("old_base", U.results_dict("base", self._outcomes(False)))
        new_base = self._write("new_base", U.results_dict("base", corrections(self._outcomes(False), 0)))
        good = self._write("good", U.results_dict("good", corrections(self._outcomes(True), -1)))
        with mock.patch("sys.stdout", new_callable=io.StringIO) as out:
            self.assertEqual(C.main([old_base, good, "--resamples", "200"]), 0)
        self.assertIn("the base results", out.getvalue())
        with mock.patch("sys.stdout", new_callable=io.StringIO) as out:
            self.assertEqual(C.main([new_base, good, "--resamples", "200"]), 0)
        self.assertIn("correction precision difference", out.getvalue())
        self.assertEqual(C.main([new_base, new_base, "--resamples", "200"]), 1)


if __name__ == "__main__":
    unittest.main()
