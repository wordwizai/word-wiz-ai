import contextlib
import dataclasses
import io
import json
import os
import tempfile
import unittest
from unittest import mock

import numpy as np

from tests.benchmark import common
from tests.benchmark import speed as SP
from tests.benchmark import stage_cache as SC
from tests.benchmark import testutil as U


class TestBudget(unittest.TestCase):
    BASE = {"p95_s": 1.0, "peak_rss_mb": 2000.0, "clips_ok": 200}

    def candidate(self, **overrides):
        return {**self.BASE, **overrides}

    def test_within_budget(self):
        self.assertTrue(SP.compare_speed(self.BASE, self.candidate(p95_s=1.09, peak_rss_mb=2140.0))["passed"])

    def test_too_slow(self):
        result = SP.compare_speed(self.BASE, self.candidate(p95_s=1.11))
        self.assertFalse(result["checks"][0]["passed"])
        self.assertFalse(result["passed"])

    def test_too_much_memory(self):
        result = SP.compare_speed(self.BASE, self.candidate(peak_rss_mb=2151.0))
        self.assertFalse(result["checks"][1]["passed"])
        self.assertFalse(result["passed"])

    def test_losing_a_successful_clip_fails(self):
        # A candidate that fails more clips looks faster, because failures are left out of the timing.
        result = SP.compare_speed(self.BASE, self.candidate(clips_ok=199))
        check = result["checks"][2]
        self.assertEqual(check["name"], "same clips succeed")
        self.assertFalse(check["passed"])
        self.assertFalse(result["passed"])
        self.assertTrue(result["checks"][0]["passed"] and result["checks"][1]["passed"])

    def test_the_same_or_more_successful_clips_pass(self):
        for clips_ok in (200, 201):
            result = SP.compare_speed(self.BASE, self.candidate(clips_ok=clips_ok))
            self.assertTrue(result["checks"][2]["passed"])
            self.assertTrue(result["passed"])

    def test_results_that_do_not_say_how_many_clips_succeeded_fail(self):
        # Older files timed failed clips as well, so their latencies cannot be trusted.
        for base, cand in (({"p95_s": 1.0, "peak_rss_mb": 2000.0}, self.candidate()),
                           (self.BASE, {"p95_s": 1.0, "peak_rss_mb": 2000.0})):
            result = SP.compare_speed(base, cand)
            self.assertFalse(result["checks"][2]["passed"])
            self.assertFalse(result["passed"])

    def test_peak_rss_is_positive(self):
        self.assertGreater(SP.peak_rss_mb(), 0)


class TestLatencyStats(unittest.TestCase):
    def test_only_clips_that_succeeded_are_timed(self):
        # The failing clip is fast (it was rejected up front). Counted, it would pull both
        # percentiles down, so it must be left out of them.
        passes = [
            [(True, 1.0), (False, 0.001), (True, 3.0)],
            [(True, 2.0), (False, 0.002), (True, 4.0)],
        ]
        stats = SP.latency_stats(passes)
        self.assertEqual((stats["clips_ok"], stats["clips_failed"]), (2, 1))
        self.assertAlmostEqual(stats["p50_s"], (2.0 + 3.0) / 2)
        self.assertAlmostEqual(stats["p95_s"], (2.9 + 3.9) / 2)

    def test_a_clip_that_fails_in_a_later_repeat_counts_as_failed(self):
        stats = SP.latency_stats([[(True, 1.0), (True, 1.0)], [(True, 1.0), (False, 0.1)]])
        self.assertEqual((stats["clips_ok"], stats["clips_failed"]), (1, 1))

    def test_all_clips_succeeding(self):
        stats = SP.latency_stats([[(True, 1.0), (True, 2.0)]])
        self.assertEqual((stats["clips_ok"], stats["clips_failed"]), (2, 0))

    def test_no_successful_clip_is_an_error(self):
        with self.assertRaises(SP.MeasurementError):
            SP.latency_stats([[(False, 0.1), (False, 0.2)]])
        with self.assertRaises(SP.MeasurementError):
            SP.latency_stats([[(True, 1.0)], [(False, 0.1)]])


class TestMeasure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.processor = U.real_processor_or_skip()

    def record(self, clips, cache):
        for clip in clips:
            SC.record_clip(clip.utt_id, clip.wav_path, clip.text, cache,
                           U.fake_onnx_extractor(self.processor), U.FakeWords(), git_sha="test")

    def test_measure_on_fixture(self):
        from tests.benchmark.dataset import load_half

        with tempfile.TemporaryDirectory() as tmp:
            root = U.make_temp_dataset(tmp)
            clips = load_half(root, "dev")
            cache = os.path.join(tmp, "cache")
            self.record(clips, cache)
            result = SP.measure(clips, cache, repeats=1, extractor=U.fake_onnx_extractor(self.processor))
        self.assertEqual(result["clips"], 2)
        self.assertEqual((result["clips_ok"], result["clips_failed"]), (2, 0))
        self.assertGreaterEqual(result["p95_s"], result["p50_s"])
        self.assertGreater(result["p50_s"], 0)
        self.assertGreater(result["peak_rss_mb"], 0)

    def test_a_clip_that_fails_is_counted_and_not_timed(self):
        import soundfile as sf
        from tests.benchmark.dataset import load_half

        with tempfile.TemporaryDirectory() as tmp:
            root = U.make_temp_dataset(tmp)
            clips = load_half(root, "dev")
            silent = os.path.join(tmp, "silent.wav")
            sf.write(silent, np.zeros(32000, dtype=np.float32), 16000, subtype="FLOAT")
            # Digital silence is recorded without gates, then rejected when the gates run.
            clips.append(dataclasses.replace(clips[0], utt_id="silent", wav_path=silent))
            cache = os.path.join(tmp, "cache")
            self.record(clips, cache)
            result = SP.measure(clips, cache, repeats=1, extractor=U.fake_onnx_extractor(self.processor))
        self.assertEqual(result["clips"], 3)
        self.assertEqual((result["clips_ok"], result["clips_failed"]), (2, 1))
        self.assertGreater(result["p50_s"], 0)

    def test_a_missing_cache_entry_is_a_stale_cache(self):
        from tests.benchmark.dataset import load_half

        with tempfile.TemporaryDirectory() as tmp:
            clips = load_half(U.make_temp_dataset(tmp), "dev")
            with self.assertRaises(common.StaleCacheError):
                SP.measure(clips, os.path.join(tmp, "nothing"), repeats=1,
                           extractor=U.fake_onnx_extractor(self.processor))


class TestMain(unittest.TestCase):
    RESULT = {"clips": 200, "clips_ok": 199, "clips_failed": 1, "repeats": 2,
              "p50_s": 0.5, "p95_s": 0.9, "peak_rss_mb": 1800.0}

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = os.path.join(self.tmp.name, "t_speed.json")
        stack = contextlib.ExitStack()
        self.addCleanup(stack.close)
        self.addCleanup(self.tmp.cleanup)
        stack.enter_context(mock.patch.dict(os.environ, {"WWAI_SPEED_TEST_FLAG": "1"}))
        stack.enter_context(mock.patch.object(common, "dotenv_wwai_keys", return_value=[]))
        stack.enter_context(mock.patch.object(common, "git_sha", return_value="abc123"))
        stack.enter_context(mock.patch.object(common, "results_dir", return_value=self.tmp.name))
        stack.enter_context(mock.patch("tests.benchmark.dataset.load_clips", return_value=["clip"]))
        self.measure = stack.enter_context(mock.patch.object(SP, "measure", return_value=dict(self.RESULT)))
        self.tracked = stack.enter_context(mock.patch.object(SP, "_tracked_by_git", return_value=False))

    def run_main(self, *argv):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = SP.main(list(argv))
        return code, stdout.getvalue(), stderr.getvalue()

    def test_measures_and_writes_the_result(self):
        code, stdout, stderr = self.run_main("--name", "t", "--out", self.out)
        self.assertEqual(code, 0)
        with open(self.out, encoding="utf-8") as fh:
            written = json.load(fh)
        self.assertEqual((written["name"], written["git_sha"]), ("t", "abc123"))
        self.assertEqual((written["clips_ok"], written["clips_failed"]), (199, 1))
        self.assertEqual(written["flags"]["WWAI_SPEED_TEST_FLAG"], "1")
        self.assertIn("199 of 200", stdout)
        self.assertIn("1 clip", stderr)  # a warning that failed clips were left out of the timing

    def test_default_output_name(self):
        code, _, _ = self.run_main("--name", "base")
        self.assertEqual(code, 0)
        self.assertTrue(os.path.isfile(os.path.join(self.tmp.name, "base_speed.json")))

    def test_a_stale_cache_exits_3(self):
        self.measure.side_effect = common.StaleCacheError("no cache entry for u1")
        code, _, stderr = self.run_main("--name", "t", "--out", self.out)
        self.assertEqual(code, 3)
        self.assertIn("stale cache", stderr)
        self.assertFalse(os.path.exists(self.out))

    def test_no_successful_clip_exits_4(self):
        self.measure.side_effect = SP.MeasurementError("no clip succeeded")
        code, _, stderr = self.run_main("--name", "t", "--out", self.out)
        self.assertEqual(code, 4)
        self.assertIn("no clip succeeded", stderr)
        self.assertFalse(os.path.exists(self.out))

    def test_refuses_flags_set_in_dotenv(self):
        with mock.patch.object(common, "dotenv_wwai_keys", return_value=["WWAI_X"]):
            code, _, stderr = self.run_main("--name", "t", "--out", self.out)
        self.assertEqual(code, 2)
        self.assertIn("WWAI_X", stderr)
        self.measure.assert_not_called()

    def test_refuses_to_overwrite_committed_results_without_force(self):
        self.tracked.return_value = True
        with open(self.out, "w", encoding="utf-8") as fh:
            fh.write("{}")  # the committed baseline
        code, _, stderr = self.run_main("--name", "t", "--out", self.out)
        self.assertEqual(code, 2)
        self.assertIn("tracked by git", stderr)
        self.measure.assert_not_called()
        code, _, _ = self.run_main("--name", "t", "--out", self.out, "--force")
        self.assertEqual(code, 0)

    def test_rejects_a_bad_name_and_a_bad_flag(self):
        self.assertEqual(self.run_main("--name", "../x")[0], 2)
        self.assertEqual(self.run_main("--name", "t", "--flag", "NOT_A_FLAG=1")[0], 2)
        self.measure.assert_not_called()

    def test_compare_exit_codes(self):
        base = {"p95_s": 1.0, "peak_rss_mb": 2000.0, "clips_ok": 200}
        paths = []
        for i, data in enumerate((base, dict(base), dict(base, clips_ok=150))):
            path = os.path.join(self.tmp.name, f"r{i}.json")
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(data, fh)
            paths.append(path)
        code, stdout, _ = self.run_main("--compare", paths[0], paths[1])
        self.assertEqual(code, 0)
        self.assertIn("PASS", stdout)
        code, stdout, _ = self.run_main("--compare", paths[0], paths[2])
        self.assertEqual(code, 1)
        self.assertIn("FAIL  same clips succeed", stdout)
        self.measure.assert_not_called()


if __name__ == "__main__":
    unittest.main()
