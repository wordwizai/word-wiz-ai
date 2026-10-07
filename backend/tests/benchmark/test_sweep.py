import contextlib
import io
import itertools
import json
import os
import tempfile
import types
import unittest
from unittest import mock

from tests.benchmark import common
from tests.benchmark import run as RUN
from tests.benchmark import sweep as SW

GAINS = {"WWAI_GT_ANCHORED_ALIGNMENT": 0.03, "WWAI_WEIGHTED_PER": 0.02}


def fake_evaluate(base, trial):
    added = {k for k in trial if k not in base}
    if "WWAI_SINGLE_PREPROCESS" in added:
        return None  # pretend its cache does not exist yet
    gain = sum(GAINS.get(k, -0.01) for k in added)
    if added == {"WWAI_WEIGHTED_PER"} and "WWAI_GT_ANCHORED_ALIGNMENT" in base:
        gain = 0.01  # smaller once alignment is already fixed
    return {"passed": gain > 0, "f05_delta": gain, "f05_ci": [gain - 0.005, gain + 0.005]}


class TestGreedy(unittest.TestCase):
    def test_selects_in_order_of_conservative_gain(self):
        steps, selected = SW.greedy_select(SW.CANDIDATES, fake_evaluate)
        self.assertEqual(selected, {"WWAI_GT_ANCHORED_ALIGNMENT": "1", "WWAI_WEIGHTED_PER": "1"})
        self.assertEqual(len(steps), 3)
        self.assertEqual(steps[0]["chosen"], "gt_anchored")
        self.assertEqual(steps[1]["chosen"], "weighted_per")
        self.assertIsNone(steps[2]["chosen"])

    def test_skipped_candidates_are_reported(self):
        steps, _ = SW.greedy_select(SW.CANDIDATES, fake_evaluate)
        skipped = [r["name"] for r in steps[0]["results"] if r["skipped"]]
        self.assertEqual(skipped, ["single_preprocess"])

    def test_nothing_passing_selects_nothing(self):
        steps, selected = SW.greedy_select(SW.CANDIDATES, lambda base, trial: {
            "passed": False, "f05_delta": -0.01, "f05_ci": [-0.02, 0.0]})
        self.assertEqual((len(steps), selected), (1, {}))
        self.assertIsNone(steps[0]["chosen"])


class TestConfigName(unittest.TestCase):
    def test_config_name(self):
        self.assertEqual(SW.config_name({}), "sweep_baseline")
        self.assertEqual(SW.config_name({"WWAI_WEIGHTED_PER": "1"}), "sweep_weighted_per")
        self.assertEqual(SW.config_name({"WWAI_WEIGHTED_PER": "1", "WWAI_G2P_STRICT": "1"}),
                         "sweep_g2p_strict-weighted_per")

    def test_every_name_is_one_that_run_py_accepts(self):
        # run.py refuses a --name with anything but letters, digits, _ . and -. A "+" joiner
        # made every configuration of two or more flags fail with exit code 2.
        flags = [f for cand in SW.CANDIDATES for f in cand["flags"]]
        for size in range(len(flags) + 1):
            for combo in itertools.combinations(sorted(set(flags)), size):
                name = SW.config_name({f: "1" for f in combo})
                self.assertIsNotNone(RUN._NAME.fullmatch(name), name)

    def test_names_do_not_collide(self):
        flags = sorted({f for cand in SW.CANDIDATES for f in cand["flags"]})
        names = [SW.config_name({f: "1" for f in combo})
                 for size in range(len(flags) + 1) for combo in itertools.combinations(flags, size)]
        self.assertEqual(len(names), len(set(names)))


class FakeRun:
    """Stands in for subprocess.run, one canned CompletedProcess per call."""

    def __init__(self, *results):
        self.results = list(results)
        self.calls = []

    def __call__(self, cmd, **kwargs):
        self.calls.append((cmd, kwargs))
        returncode, stdout, stderr = self.results.pop(0)
        return types.SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)


class TestRunConfig(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.results = mock.patch.object(common, "results_dir", return_value=self.tmp.name)
        self.results.start()
        self.addCleanup(self.results.stop)

    def run_config(self, fake, flags, subset=None, memo=None, env=None):
        memo = {} if memo is None else memo
        stdout = io.StringIO()
        with mock.patch.object(SW.subprocess, "run", fake), \
                mock.patch.dict(os.environ, env or {}), \
                contextlib.redirect_stdout(stdout):
            path = SW.run_config(flags, "dev", subset, memo)
        return path, stdout.getvalue()

    def test_runs_run_py_with_the_flags_and_returns_its_results_path(self):
        fake = FakeRun((0, "", ""))
        path, _ = self.run_config(fake, {"WWAI_WEIGHTED_PER": "1", "WWAI_G2P_STRICT": "1"})
        self.assertEqual(path, os.path.join(self.tmp.name, "sweep_g2p_strict-weighted_per_dev.json"))
        cmd, kwargs = fake.calls[0]
        self.assertEqual(cmd[1:4], ["-m", "tests.benchmark.run", "--name"])
        self.assertEqual(cmd[cmd.index("--name") + 1], "sweep_g2p_strict-weighted_per")
        self.assertEqual(cmd[cmd.index("--half") + 1], "dev")
        self.assertEqual(cmd[cmd.index("--out") + 1], path)
        flag_args = [cmd[i + 1] for i, a in enumerate(cmd) if a == "--flag"]
        self.assertEqual(flag_args, ["WWAI_G2P_STRICT=1", "WWAI_WEIGHTED_PER=1"])
        self.assertNotIn("--subset", cmd)
        self.assertEqual(kwargs["cwd"], common.BACKEND_ROOT)

    def test_overwrites_its_own_results_even_when_git_tracks_a_summary(self):
        # The per-configuration .summary.json files are not ignored, so one may be committed.
        # Without --force a second sweep would exit 2 on it.
        fake = FakeRun((0, "", ""))
        self.run_config(fake, {})
        self.assertIn("--force", fake.calls[0][0])

    def test_a_subset_is_passed_and_named_in_the_file(self):
        fake = FakeRun((0, "", ""))
        path, _ = self.run_config(fake, {}, subset="smoke_dev")
        self.assertEqual(os.path.basename(path), "sweep_baseline_dev_smoke_dev.json")
        cmd = fake.calls[0][0]
        self.assertEqual(cmd[cmd.index("--subset") + 1], "smoke_dev")

    def test_the_child_starts_from_a_clean_flag_environment(self):
        fake = FakeRun((0, "", ""))
        env = {"WWAI_WEIGHTED_PER": "1", "WWAI_BENCH_DATA_DIR": "somewhere", "WWAI_HOST": "10.0.0.1"}
        self.run_config(fake, {"WWAI_G2P_STRICT": "1"}, env=env)
        child_env = fake.calls[0][1]["env"]
        self.assertNotIn("WWAI_WEIGHTED_PER", child_env)  # only what the configuration sets is on
        self.assertEqual(child_env["WWAI_BENCH_DATA_DIR"], "somewhere")
        self.assertEqual(child_env["WWAI_HOST"], "10.0.0.1")  # a deploy setting, not an experiment flag
        self.assertEqual(child_env["PYTHONIOENCODING"], "utf-8")

    def test_exit_3_means_the_configuration_needs_a_cache(self):
        fake = FakeRun((3, "", "stale cache: no cache at X\n"))
        path, out = self.run_config(fake, {"WWAI_SINGLE_PREPROCESS": "1", "WWAI_WEIGHTED_PER": "1"})
        self.assertIsNone(path)
        self.assertIn("no cache at X", out)  # why, as run.py said it
        self.assertIn("python -m tests.benchmark.stage_cache --half dev --flag WWAI_SINGLE_PREPROCESS=1", out)
        self.assertNotIn("WWAI_WEIGHTED_PER", out)  # not a front-end flag, so not part of the cache

    def test_any_other_failure_is_an_error_with_the_childs_output(self):
        for code in (1, 2, 4):
            fake = FakeRun((code, "the summary", "something broke"))
            with self.assertRaises(RuntimeError) as ctx:
                self.run_config(fake, {"WWAI_WEIGHTED_PER": "1"})
            message = str(ctx.exception)
            self.assertIn("sweep_weighted_per", message)
            self.assertIn(f"exit code {code}", message)
            self.assertIn("something broke", message)

    def test_each_configuration_runs_once(self):
        fake = FakeRun((0, "", ""), (3, "", "stale cache: x"))
        memo = {}
        first, _ = self.run_config(fake, {"WWAI_G2P_STRICT": "1"}, memo=memo)
        again, _ = self.run_config(fake, {"WWAI_G2P_STRICT": "1"}, memo=memo)
        self.assertEqual(first, again)
        stale, _ = self.run_config(fake, {"WWAI_SINGLE_PREPROCESS": "1"}, memo=memo)
        stale_again, _ = self.run_config(fake, {"WWAI_SINGLE_PREPROCESS": "1"}, memo=memo)
        self.assertIsNone(stale)
        self.assertIsNone(stale_again)
        self.assertEqual(len(fake.calls), 2)


class TestEvaluator(unittest.TestCase):
    def evaluator(self, paths):
        patches = [
            mock.patch("tests.benchmark.dataset.load_clips", return_value=["clip"]),
            mock.patch("tests.benchmark.compare.load_results", side_effect=lambda path: {"loaded": path}),
            mock.patch("tests.benchmark.compare.compare_results", return_value={"passed": True}),
            mock.patch.object(SW, "run_config", side_effect=lambda flags, half, subset, memo: paths.get(
                tuple(sorted(flags)))),
        ]
        mocks = [p.start() for p in patches]
        for p in patches:
            self.addCleanup(p.stop)
        return SW.make_evaluator("dev", None), mocks[2]

    def test_compares_the_two_results(self):
        evaluate, compare = self.evaluator({(): "base.json", ("WWAI_G2P_STRICT",): "trial.json"})
        self.assertEqual(evaluate({}, {"WWAI_G2P_STRICT": "1"}), {"passed": True})
        compare.assert_called_once_with({"loaded": "base.json"}, {"loaded": "trial.json"}, ["clip"])

    def test_a_missing_cache_on_either_side_means_it_could_not_run(self):
        evaluate, compare = self.evaluator({(): "base.json"})
        self.assertIsNone(evaluate({}, {"WWAI_G2P_STRICT": "1"}))
        evaluate, compare = self.evaluator({("WWAI_G2P_STRICT",): "trial.json"})
        self.assertIsNone(evaluate({}, {"WWAI_G2P_STRICT": "1"}))
        compare.assert_not_called()


class TestMain(unittest.TestCase):
    PASSING = {"passed": True, "f05_delta": 0.02, "f05_ci": [0.01, 0.03]}

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        stack = contextlib.ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(mock.patch.object(common, "results_dir", return_value=self.tmp.name))
        stack.enter_context(mock.patch.object(common, "git_sha", return_value="abc123"))
        self.run_config = stack.enter_context(
            mock.patch.object(SW, "run_config", return_value=os.path.join(self.tmp.name, "base.json")))
        self.make_evaluator = stack.enter_context(mock.patch.object(SW, "make_evaluator"))
        self.make_evaluator.return_value = lambda base, trial: (
            self.PASSING if "WWAI_WEIGHTED_PER" in trial and "WWAI_WEIGHTED_PER" not in base else
            {"passed": False, "f05_delta": -0.01, "f05_ci": [-0.02, 0.0]})

    def run_main(self, *argv):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = SW.main(list(argv))
        return code, stdout.getvalue(), stderr.getvalue()

    def test_prints_the_rounds_and_writes_a_summary(self):
        code, stdout, _ = self.run_main()
        self.assertEqual(code, 0)
        self.assertIn("chosen: weighted_per", stdout)
        self.assertIn("selected flags: {'WWAI_WEIGHTED_PER': '1'}", stdout)
        with open(os.path.join(self.tmp.name, "sweep_dev.summary.json"), encoding="utf-8") as fh:
            summary = json.load(fh)
        self.assertEqual(summary["selected"], {"WWAI_WEIGHTED_PER": "1"})
        self.assertEqual(summary["git_sha"], "abc123")
        self.assertEqual(summary["steps"][0]["chosen"], "weighted_per")

    def test_a_subset_names_the_summary(self):
        code, _, _ = self.run_main("--subset", "smoke_dev")
        self.assertEqual(code, 0)
        self.assertTrue(os.path.isfile(os.path.join(self.tmp.name, "sweep_dev_smoke_dev.summary.json")))
        self.assertEqual(self.make_evaluator.call_args.args[:2], ("dev", "smoke_dev"))

    def test_a_missing_baseline_cache_stops_the_sweep(self):
        # Otherwise every candidate would be skipped and the sweep would end by reporting
        # that no flag helps, which is not what happened.
        self.run_config.return_value = None
        code, stdout, stderr = self.run_main()
        self.assertEqual(code, RUN.EXIT_STALE)
        self.assertIn("baseline", stderr)
        self.assertNotIn("selected flags", stdout)
        self.assertFalse(os.path.exists(os.path.join(self.tmp.name, "sweep_dev.summary.json")))

    def test_a_failed_run_is_reported_without_a_traceback(self):
        self.run_config.side_effect = RuntimeError("run.py failed for sweep_baseline (exit code 4)")
        code, _, stderr = self.run_main()
        self.assertEqual(code, 1)
        self.assertIn("exit code 4", stderr)


if __name__ == "__main__":
    unittest.main()
