import contextlib
import io
import json
import os
import tempfile
import unittest
from unittest import mock

from tests.benchmark import common
from tests.benchmark import run as RUN
from tests.benchmark import stage_cache as SC
from tests.benchmark import testutil as U


class TestLock(unittest.TestCase):
    def test_dev_is_open(self):
        RUN.check_test_unlock("dev", None, env={})

    def test_test_needs_unlock(self):
        with self.assertRaises(PermissionError):
            RUN.check_test_unlock("test", "final run", env={})

    def test_test_needs_reason(self):
        with self.assertRaises(PermissionError):
            RUN.check_test_unlock("test", " ", env={common.UNLOCK_ENV: "1"})

    def test_unlocked(self):
        RUN.check_test_unlock("test", "final run", env={common.UNLOCK_ENV: "1"})

    def test_ledger(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "log")
            RUN.append_ledger("final", "freeze", "abc123", path=path)
            with open(path, encoding="utf-8") as fh:
                fields = fh.read().rstrip("\n").split("\t")
        self.assertEqual(fields[1:], ["abc123", "final", "freeze"])

    def test_main_refuses_locked_test_half(self):
        with mock.patch.dict(os.environ, {common.UNLOCK_ENV: ""}):
            self.assertEqual(RUN.main(["--half", "test", "--name", "x"]), 2)

    def test_main_refuses_wwai_keys_in_dotenv(self):
        err = io.StringIO()
        with mock.patch.object(common, "dotenv_wwai_keys", return_value=["WWAI_X"]):
            with contextlib.redirect_stderr(err):
                self.assertEqual(RUN.main(["--name", "x"]), 2)
        self.assertIn("backend/.env sets WWAI_X", err.getvalue())
        self.assertIn("--flag", err.getvalue())


class TestFormatSummary(unittest.TestCase):
    def _summary(self, clips, outcomes):
        from tests.benchmark import scoring as S

        return S.summarize(S.build_items(clips, outcomes), 0.4)

    def test_a_run_where_every_clip_is_rejected_still_formats(self):
        clip = U.synthetic_clip("c1", "s1", 30, [("CAT", 10, "K AE1 T", [2, 2, 2])])
        text = RUN.format_summary(self._summary([clip], {"c1": U.rejected()}))
        self.assertIn("g2p disagreement n/a", text)
        self.assertIn("unscored 100.0%", text)

    def test_shows_the_flag_every_word_reference(self):
        clip = U.synthetic_clip("c1", "s1", 30, [("CAT", 10, "K AE1 T", [2, 2, 2]), ("DOG", 3, "D AO1 G", [2, 0, 2])])
        outcome = U.ok(U.record("cat", ["k", "æ", "t"], ["k", "æ", "t"], 0.0),
                       U.record("dog", ["d", "ɔ", "g"], ["d", "ɑ", "g"], 0.3333))
        text = RUN.format_summary(self._summary([clip], {"c1": outcome}))
        self.assertIn("flagging every word 0.5556", text)


class TestCacheChecks(unittest.TestCase):
    def test_missing_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(common.StaleCacheError):
                RUN.check_cache(tmp)

    def test_revision_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, SC.CACHE_META), "w", encoding="utf-8") as fh:
                json.dump({"model_revision": "not-the-pin"}, fh)
            with self.assertRaises(common.StaleCacheError):
                RUN.check_cache(tmp)


class TestEndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.processor = U.real_processor_or_skip()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = U.make_temp_dataset(self.tmp.name)
        self.cache_root = os.path.join(self.tmp.name, "cache")
        env = {common.DATA_DIR_ENV: self.tmp.name, common.CACHE_DIR_ENV: self.cache_root}
        self.env = mock.patch.dict(os.environ, env)
        self.env.start()
        directory = SC.cache_dir("dev", "baseline")
        SC.write_meta(directory, "dev", "baseline", {})
        from tests.benchmark.dataset import load_half

        for clip in load_half(self.root, "dev"):
            SC.record_clip(clip.utt_id, clip.wav_path, clip.text, directory, U.fake_onnx_extractor(self.processor), U.FakeWords())

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()
        RUN._init_error = None

    def test_run_writes_results_and_summary(self):
        out = os.path.join(self.tmp.name, "r", "t_dev.json")
        self.assertEqual(RUN.main(["--name", "t", "--workers", "1", "--out", out]), 0)
        with open(out, encoding="utf-8") as fh:
            results = json.load(fh)
        self.assertEqual(sorted(results["outcomes"]), ["000010011", "000020022"])
        self.assertEqual(results["threshold"], 0.4)
        self.assertEqual(results["summary"]["clips"], 2)
        self.assertTrue(os.path.isfile(out[:-5] + ".summary.json"))

    def test_stale_cache_exit_code(self):
        self.assertEqual(RUN.main(["--name", "t", "--workers", "1", "--cache", "nope",
                                   "--out", os.path.join(self.tmp.name, "x.json")]), RUN.EXIT_STALE)

    def _pooled(self, argv):
        with (
            mock.patch.object(RUN, "ProcessPoolExecutor", U.InlineExecutor),
            mock.patch.dict(os.environ),
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            os.environ.pop("PYTHONIOENCODING", None)
            return RUN.main(argv)

    def test_workers_run_in_a_spawn_process_pool(self):
        out = os.path.join(self.tmp.name, "r", "t_dev.json")
        self.assertEqual(self._pooled(["--name", "t", "--workers", "2", "--out", out]), 0)
        pool = U.InlineExecutor.last
        self.assertEqual(pool.max_workers, 2)
        self.assertEqual(pool.mp_context.get_start_method(), "spawn")
        self.assertIs(pool.initializer, RUN._init_worker)
        self.assertEqual(pool.pythonioencoding, "utf-8")
        with open(out, encoding="utf-8") as fh:
            self.assertEqual(sorted(json.load(fh)["outcomes"]), ["000010011", "000020022"])

    def test_a_stale_entry_in_a_worker_reaches_main(self):
        os.remove(os.path.join(SC.cache_dir("dev", "baseline"), "000020022.json"))
        out = os.path.join(self.tmp.name, "r", "t_dev.json")
        self.assertEqual(self._pooled(["--name", "t", "--workers", "2", "--out", out]), RUN.EXIT_STALE)

    def test_a_worker_that_cannot_load_the_processor_gives_a_clear_error(self):
        out = os.path.join(self.tmp.name, "r", "t_dev.json")
        with (
            mock.patch("tests.benchmark.replay.load_processor", side_effect=OSError("processor not found")),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            with self.assertRaises(RuntimeError) as ctx:
                RUN.main(["--name", "t", "--workers", "1", "--out", out])
        self.assertNotIsInstance(ctx.exception, common.StaleCacheError)
        self.assertIn("could not load", str(ctx.exception))
        self.assertIn("OSError: processor not found", str(ctx.exception))

    def test_unexpected_failures_exit_code(self):
        # analyze_clip imports analyze_results from core.process_audio at call time, so patching
        # it there makes every clip fail with an error that is not an expected rejection.
        out = os.path.join(self.tmp.name, "r", "t_dev.json")
        err = io.StringIO()
        with mock.patch("core.process_audio.analyze_results", side_effect=KeyError("boom")):
            with contextlib.redirect_stderr(err):
                code = RUN.main(["--name", "t", "--workers", "1", "--out", out])
        self.assertEqual(code, RUN.EXIT_UNEXPECTED)
        self.assertEqual(RUN.EXIT_UNEXPECTED, 4)
        with open(out, encoding="utf-8") as fh:
            results = json.load(fh)
        self.assertEqual(results["summary"]["unexpected_failures"], 2)
        self.assertEqual(results["summary"]["rejected_by_type"], {"unexpected:KeyError": 2})
        self.assertTrue(os.path.isfile(out[:-5] + ".summary.json"))
        self.assertIn("WARNING", err.getvalue())
        self.assertIn("unexpected:KeyError", err.getvalue())


if __name__ == "__main__":
    unittest.main()
