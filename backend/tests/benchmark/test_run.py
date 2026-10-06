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
            RUN.append_ledger("final", "freeze", "abc123", path=path, flags={"WWAI_X": "1"}, threshold=0.4)
            with open(path, encoding="utf-8") as fh:
                fields = fh.read().rstrip("\n").split("\t")
        self.assertEqual(fields[1:], ["abc123", "final", "freeze", '{"WWAI_X":"1"}', "0.4"])

    def test_ledger_without_flags_or_threshold_still_has_every_column(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "log")
            RUN.append_ledger("final", "freeze", "abc123", path=path)
            with open(path, encoding="utf-8") as fh:
                fields = fh.read().rstrip("\n").split("\t")
        self.assertEqual(fields[1:], ["abc123", "final", "freeze", "{}", ""])

    def test_ledger_free_text_cannot_break_the_columns(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "log")
            RUN.append_ledger("a\tb\nc", "why\r\nnot\there  now", "abc123", path=path, flags={}, threshold=0.4)
            with open(path, encoding="utf-8", newline="") as fh:
                text = fh.read()
        self.assertEqual(text.count("\n"), 1)
        self.assertNotIn("\r", text)
        fields = text.rstrip("\n").split("\t")
        self.assertEqual(len(fields), 6)
        self.assertEqual(fields[2:4], ["a b c", "why not here now"])

    def test_ledger_path_follows_a_patched_log(self):
        # The default used to be bound when the function was defined, so patching the log did nothing.
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "log")
            with mock.patch.object(common, "TEST_RUNS_LOG", path):
                RUN.append_ledger("final", "freeze", "abc123")
            with open(path, encoding="utf-8") as fh:
                self.assertEqual(len(fh.read().splitlines()), 1)

    def test_main_refuses_locked_test_half(self):
        err = io.StringIO()
        with (
            mock.patch.dict(os.environ, {common.UNLOCK_ENV: ""}),
            mock.patch.object(common, "dotenv_wwai_keys", return_value=[]),
            contextlib.redirect_stderr(err),
        ):
            self.assertEqual(RUN.main(["--half", "test", "--name", "x"]), 2)
        self.assertIn("sealed", err.getvalue())

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


def _write_cache_meta(directory, half, flags=None):
    """A _cache_meta.json for the current model pin, with or without a flags entry."""
    from core.model_registry import resolve_revision

    meta = {"half": half, "model_revision": resolve_revision("PHONEME_IPA_ONNX")}
    if flags is not None:
        meta["flags"] = flags
    with open(os.path.join(directory, SC.CACHE_META), "w", encoding="utf-8") as fh:
        json.dump(meta, fh)


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

    def _write_meta(self, tmp, half):
        _write_cache_meta(tmp, half)

    def test_a_cache_built_for_the_other_half_is_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._write_meta(tmp, "dev")
            with self.assertRaises(common.StaleCacheError) as ctx:
                RUN.check_cache(tmp, "test")
        self.assertIn("dev half", str(ctx.exception))

    def test_a_cache_for_the_requested_half_is_fine(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._write_meta(tmp, "test")
            self.assertEqual(RUN.check_cache(tmp, "test")["half"], "test")

    def test_the_half_is_only_checked_when_asked_for(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._write_meta(tmp, "dev")
            self.assertEqual(RUN.check_cache(tmp)["half"], "dev")

    def test_an_unreadable_meta_file_is_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, SC.CACHE_META), "w", encoding="utf-8") as fh:
                fh.write("{not json")
            with self.assertRaises(common.StaleCacheError):
                RUN.check_cache(tmp, "dev")


class TestRecordingFlags(unittest.TestCase):
    """Flags that change what the models returned. Replaying words recorded under another ASR mode
    is not faithful, and nothing else in the input hash would show it."""

    def _write_meta(self, tmp, flags=None):
        _write_cache_meta(tmp, "dev", flags)

    def test_a_recording_flag_that_differs_is_stale_and_named(self):
        for flag in common.RECORDING_FLAGS:
            for cached, active in (({}, {flag: "1"}), ({flag: "1"}, {}), ({flag: "1"}, {flag: "0"}),
                                   ({flag: "0"}, {})):
                with self.subTest(flag=flag, cached=cached, active=active), tempfile.TemporaryDirectory() as tmp:
                    self._write_meta(tmp, cached)
                    with self.assertRaises(common.StaleCacheError) as ctx:
                        RUN.check_cache(tmp, "dev", active)
                    self.assertIn(flag, str(ctx.exception))

    def test_matching_recording_flags_are_fine(self):
        flags = {"WWAI_ASR_FALLBACK": "0", "WWAI_ASR_TYPED_ERRORS": "0"}
        with tempfile.TemporaryDirectory() as tmp:
            self._write_meta(tmp, flags)
            self.assertEqual(RUN.check_cache(tmp, "dev", dict(flags))["half"], "dev")
            self._write_meta(tmp, {})
            self.assertEqual(RUN.check_cache(tmp, "dev", {})["half"], "dev")

    def test_a_cache_without_a_flags_entry_counts_as_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._write_meta(tmp)  # no "flags" key at all
            self.assertEqual(RUN.check_cache(tmp, "dev", {})["half"], "dev")
            with self.assertRaises(common.StaleCacheError):
                RUN.check_cache(tmp, "dev", {"WWAI_ASR_TYPED_ERRORS": "1"})

    def test_other_flags_are_not_checked_here(self):
        # Gate and scoring flags change no recorded output, and front-end flags are covered by
        # the input hashes and the cache name.
        with tempfile.TemporaryDirectory() as tmp:
            self._write_meta(tmp, {"WWAI_SINGLE_PREPROCESS": "1"})
            self.assertEqual(RUN.check_cache(tmp, "dev", {"WWAI_WEIGHTED_PER": "1"})["half"], "dev")

    def test_the_active_flags_default_to_the_environment(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._write_meta(tmp, {})
            with mock.patch.dict(os.environ, {"WWAI_ASR_FALLBACK": "1"}):
                with self.assertRaises(common.StaleCacheError) as ctx:
                    RUN.check_cache(tmp, "dev")
            self.assertIn("WWAI_ASR_FALLBACK", str(ctx.exception))
            with mock.patch.dict(os.environ):
                for flag in common.RECORDING_FLAGS:
                    os.environ.pop(flag, None)
                self.assertEqual(RUN.check_cache(tmp, "dev")["half"], "dev")


class TestTrackedByGit(unittest.TestCase):
    def test_a_committed_file_is_tracked(self):
        self.assertTrue(RUN._tracked_by_git(os.path.join(common.BENCH_ROOT, "run.py")))

    def test_a_file_outside_the_repository_is_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "baseline_dev.json")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("{}")
            self.assertFalse(RUN._tracked_by_git(path))

    def test_a_missing_git_means_not_tracked(self):
        with mock.patch("subprocess.run", side_effect=FileNotFoundError("git")):
            self.assertFalse(RUN._tracked_by_git(os.path.join(common.BENCH_ROOT, "run.py")))


CLEAN_SHA = "0123456789abcdef0123456789abcdef01234567"


class TestUsageErrors(unittest.TestCase):
    """Bad inputs and a sealed half return 2 with a message, never a traceback, and never use up a look."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        U.make_temp_dataset(self.tmp.name)
        self.ledger = os.path.join(self.tmp.name, "test_runs.log")
        stack = contextlib.ExitStack()
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(stack.close)
        stack.enter_context(mock.patch.dict(os.environ, {
            common.DATA_DIR_ENV: self.tmp.name, common.CACHE_DIR_ENV: os.path.join(self.tmp.name, "cache"),
        }))
        stack.enter_context(mock.patch.object(common, "dotenv_wwai_keys", return_value=[]))
        stack.enter_context(mock.patch.object(common, "git_sha", return_value=CLEAN_SHA))
        stack.enter_context(mock.patch.object(common, "TEST_RUNS_LOG", self.ledger))

    def _main(self, *argv, unlock=False):
        err = io.StringIO()
        with (
            mock.patch.dict(os.environ, {common.UNLOCK_ENV: "1" if unlock else ""}),
            contextlib.redirect_stderr(err),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            code = RUN.main(list(argv))
        return code, err.getvalue()

    def test_a_name_with_a_path_separator_is_refused(self):
        code, err = self._main("--name", "bad/name")
        self.assertEqual(code, 2)
        self.assertIn("--name", err)

    def test_a_cache_name_with_a_path_separator_is_refused(self):
        code, err = self._main("--name", "ok", "--cache", "../elsewhere")
        self.assertEqual(code, 2)
        self.assertIn("--cache", err)

    def test_ordinary_names_are_accepted(self):
        # These get past the name check and stop at the missing cache instead.
        code, _err = self._main("--name", "Weighted-PER_v1.2", "--cache", "base.line-2", "--workers", "1")
        self.assertEqual(code, RUN.EXIT_STALE)

    def test_a_missing_subset_is_a_usage_error(self):
        code, err = self._main("--name", "x", "--subset", "no_such_subset")
        self.assertEqual(code, 2)
        self.assertIn("error:", err)

    def test_a_subset_naming_unknown_clips_is_a_usage_error(self):
        from tests.benchmark import dataset

        with tempfile.TemporaryDirectory() as subsets:
            dataset.write_subset("bad", ["not-a-clip"], subsets)
            with mock.patch.object(common, "SUBSETS_DIR", subsets):
                code, err = self._main("--name", "x", "--subset", "bad")
        self.assertEqual(code, 2)
        self.assertIn("not in the dev half", err)

    def test_a_missing_dataset_is_a_usage_error(self):
        with tempfile.TemporaryDirectory() as empty:
            with mock.patch.dict(os.environ, {common.DATA_DIR_ENV: empty}):
                code, err = self._main("--name", "x")
        self.assertEqual(code, 2)
        self.assertIn("speechocean762 not found", err)

    def test_a_flag_value_that_cannot_name_a_cache_is_a_usage_error(self):
        with mock.patch.dict(os.environ, {"WWAI_CHUNK_OVERLAP_SECONDS": "a/b"}):
            code, err = self._main("--name", "x")
        self.assertEqual(code, 2)
        self.assertIn("WWAI_CHUNK_OVERLAP_SECONDS", err)

    def test_the_test_half_is_refused_when_the_tree_is_dirty(self):
        for sha in (CLEAN_SHA + "-dirty", "unknown"):
            with self.subTest(sha=sha), mock.patch.object(common, "git_sha", return_value=sha):
                code, err = self._main("--half", "test", "--name", "x", "--reason", "final", unlock=True)
                self.assertEqual(code, 2)
                self.assertIn("git", err)
                self.assertFalse(os.path.exists(self.ledger))

    def test_a_dirty_tree_does_not_stop_dev_runs(self):
        with mock.patch.object(common, "git_sha", return_value=CLEAN_SHA + "-dirty"):
            code, _err = self._main("--name", "x", "--workers", "1", "--cache", "nope")
        self.assertEqual(code, RUN.EXIT_STALE)  # it got as far as the cache

    def test_a_bad_subset_on_the_test_half_does_not_use_a_look(self):
        code, _err = self._main("--half", "test", "--name", "x", "--reason", "final",
                                "--subset", "no_such_subset", unlock=True)
        self.assertEqual(code, 2)
        self.assertFalse(os.path.exists(self.ledger))


class TestEndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.processor = U.real_processor_or_skip()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = U.make_temp_dataset(self.tmp.name)
        self.cache_root = os.path.join(self.tmp.name, "cache")
        self.real_ledger = common.TEST_RUNS_LOG
        self.ledger = os.path.join(self.tmp.name, "test_runs.log")
        env = {common.DATA_DIR_ENV: self.tmp.name, common.CACHE_DIR_ENV: self.cache_root}
        self.env = mock.patch.dict(os.environ, env)
        self.env.start()
        self.dotenv = mock.patch.object(common, "dotenv_wwai_keys", return_value=[])
        self.dotenv.start()
        self._record("dev")

    def tearDown(self):
        self.dotenv.stop()
        self.env.stop()
        self.tmp.cleanup()
        RUN._init_error = None

    def _record(self, half, meta_half=None):
        """A valid fake cache for one half of the fixture."""
        from tests.benchmark.dataset import load_half

        directory = SC.cache_dir(half, "baseline")
        SC.write_meta(directory, meta_half or half, "baseline", {})
        for clip in load_half(self.root, half):
            SC.record_clip(clip.utt_id, clip.wav_path, clip.text, directory, U.fake_onnx_extractor(self.processor), U.FakeWords())

    def _main(self, *argv):
        err = io.StringIO()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
            code = RUN.main(list(argv))
        return code, err.getvalue()

    @contextlib.contextmanager
    def _unlocked(self):
        """The environment of a deliberate test-half run, with the ledger redirected into the temp dir."""
        with (
            mock.patch.dict(os.environ, {common.UNLOCK_ENV: "1", "WWAI_LEDGER_TEST_FLAG": "1"}),
            mock.patch.object(common, "git_sha", return_value=CLEAN_SHA),
            mock.patch.object(common, "TEST_RUNS_LOG", self.ledger),
        ):
            yield

    def _ledger_lines(self):
        with open(self.ledger, encoding="utf-8", newline="") as fh:
            return fh.read().splitlines()

    def test_run_writes_results_and_summary(self):
        out = os.path.join(self.tmp.name, "r", "t_dev.json")
        self.assertEqual(RUN.main(["--name", "t", "--workers", "1", "--out", out]), 0)
        with open(out, encoding="utf-8") as fh:
            results = json.load(fh)
        self.assertEqual(sorted(results["outcomes"]), ["000010011", "000020022"])
        self.assertEqual(results["threshold"], 0.4)
        self.assertEqual(results["summary"]["clips"], 2)
        self.assertTrue(os.path.isfile(out[:-5] + ".summary.json"))

    def test_a_recording_flag_that_differs_from_the_cache_is_a_stale_cache(self):
        out = os.path.join(self.tmp.name, "r", "t_dev.json")
        with mock.patch.dict(os.environ, {"WWAI_ASR_TYPED_ERRORS": "1"}):
            code, err = self._main("--name", "t", "--workers", "1", "--out", out)
        self.assertEqual(code, RUN.EXIT_STALE)
        self.assertIn("WWAI_ASR_TYPED_ERRORS", err)
        self.assertFalse(os.path.exists(out))

    def test_a_recording_flag_that_differs_adds_no_ledger_line_on_the_test_half(self):
        self._record("test")
        out = os.path.join(self.tmp.name, "r", "final_test.json")
        with self._unlocked(), mock.patch.dict(os.environ, {"WWAI_ASR_FALLBACK": "1"}):
            code, err = self._main("--half", "test", "--name", "final", "--reason", "first",
                                   "--workers", "1", "--out", out)
        self.assertEqual(code, RUN.EXIT_STALE)
        self.assertIn("WWAI_ASR_FALLBACK", err)
        self.assertFalse(os.path.exists(self.ledger))

    def test_stale_cache_exit_code(self):
        self.assertEqual(RUN.main(["--name", "t", "--workers", "1", "--cache", "nope",
                                   "--out", os.path.join(self.tmp.name, "x.json")]), RUN.EXIT_STALE)

    def test_test_half_run_logs_one_sanitized_look(self):
        self._record("test")
        with open(self.real_ledger, "rb") as fh:
            real_before = fh.read()
        out = os.path.join(self.tmp.name, "r", "final_test.json")
        with self._unlocked():
            code, _err = self._main("--half", "test", "--name", "final", "--workers", "1", "--out", out,
                                    "--reason", "first look\twith a tab\nand a newline")
            expected_flags = common.active_wwai_flags()
        self.assertEqual(code, 0)
        self.assertTrue(os.path.isfile(out))
        self.assertTrue(os.path.isfile(out[:-5] + ".summary.json"))
        with open(out, encoding="utf-8") as fh:
            self.assertEqual(sorted(json.load(fh)["outcomes"]), ["000030033"])
        lines = self._ledger_lines()
        self.assertEqual(len(lines), 1)
        fields = lines[0].split("\t")
        self.assertEqual(len(fields), 6)
        self.assertEqual(fields[1:4], [CLEAN_SHA, "final", "first look with a tab and a newline"])
        self.assertEqual(json.loads(fields[4]), expected_flags)
        self.assertEqual(expected_flags["WWAI_LEDGER_TEST_FLAG"], "1")
        self.assertEqual(float(fields[5]), 0.4)
        with open(self.real_ledger, "rb") as fh:
            self.assertEqual(fh.read(), real_before, "the real test_runs.log must not be touched by tests")

    def test_a_missing_cache_on_the_second_test_half_run_adds_no_ledger_line(self):
        self._record("test")
        out = os.path.join(self.tmp.name, "r", "final_test.json")
        with self._unlocked():
            self.assertEqual(self._main("--half", "test", "--name", "final", "--reason", "first",
                                        "--workers", "1", "--out", out)[0], 0)
            self.assertEqual(len(self._ledger_lines()), 1)
            code, err = self._main("--half", "test", "--name", "final", "--reason", "second",
                                   "--workers", "1", "--cache", "nope", "--out", out)
        self.assertEqual(code, RUN.EXIT_STALE)
        self.assertIn("stale cache", err)
        self.assertEqual(len(self._ledger_lines()), 1)

    def test_a_cache_built_for_the_other_half_adds_no_ledger_line(self):
        self._record("test", meta_half="dev")
        out = os.path.join(self.tmp.name, "r", "final_test.json")
        with self._unlocked():
            code, err = self._main("--half", "test", "--name", "final", "--reason", "first",
                                   "--workers", "1", "--out", out)
        self.assertEqual(code, RUN.EXIT_STALE)
        self.assertIn("dev half", err)
        self.assertFalse(os.path.exists(self.ledger))

    def test_a_scoring_attempt_still_uses_a_look(self):
        # The cache looks valid, so scoring starts, and only then is the missing entry found.
        self._record("test")
        os.remove(os.path.join(SC.cache_dir("test", "baseline"), "000030033.json"))
        out = os.path.join(self.tmp.name, "r", "final_test.json")
        with self._unlocked():
            code, _err = self._main("--half", "test", "--name", "final", "--reason", "first",
                                    "--workers", "1", "--out", out)
        self.assertEqual(code, RUN.EXIT_STALE)
        self.assertEqual(len(self._ledger_lines()), 1)

    def test_two_workers_in_a_real_spawn_pool_match_one_worker(self):
        one = os.path.join(self.tmp.name, "r", "one_dev.json")
        two = os.path.join(self.tmp.name, "r", "two_dev.json")
        # The children inherit this environment. Offline keeps them from asking the network for the processor.
        with mock.patch.dict(os.environ, {"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"}):
            self.assertEqual(self._main("--name", "one", "--workers", "1", "--out", one)[0], 0)
            self.assertEqual(self._main("--name", "two", "--workers", "2", "--out", two)[0], 0)
        results = {}
        for key, path in (("one", one), ("two", two)):
            with open(path, encoding="utf-8") as fh:
                results[key] = json.load(fh)
        self.assertEqual(sorted(results["two"]["outcomes"]), ["000010011", "000020022"])
        self.assertEqual(results["two"]["outcomes"], results["one"]["outcomes"])
        self.assertEqual(results["two"]["summary"], results["one"]["summary"])

    def _existing_results(self):
        out = os.path.join(self.tmp.name, "r", "baseline_dev.json")
        os.makedirs(os.path.dirname(out))
        with open(out, "w", encoding="utf-8") as fh:
            fh.write('{"committed": true}')
        return out

    def test_a_tracked_results_file_is_not_overwritten_without_force(self):
        out = self._existing_results()
        with mock.patch.object(RUN, "_tracked_by_git", return_value=True):
            code, err = self._main("--name", "baseline", "--workers", "1", "--out", out)
        self.assertEqual(code, 2)
        self.assertIn("--force", err)
        with open(out, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), '{"committed": true}')

    def test_force_overwrites_a_tracked_results_file(self):
        out = self._existing_results()
        with mock.patch.object(RUN, "_tracked_by_git", return_value=True):
            code, _err = self._main("--name", "baseline", "--workers", "1", "--out", out, "--force")
        self.assertEqual(code, 0)
        with open(out, encoding="utf-8") as fh:
            self.assertIn("outcomes", json.load(fh))

    def test_a_tracked_summary_file_is_protected_too(self):
        out = os.path.join(self.tmp.name, "r", "baseline_dev.json")
        os.makedirs(os.path.dirname(out))
        with open(out[:-5] + ".summary.json", "w", encoding="utf-8") as fh:
            fh.write("{}")
        with mock.patch.object(RUN, "_tracked_by_git", side_effect=lambda path: path.endswith(".summary.json")):
            code, _err = self._main("--name", "baseline", "--workers", "1", "--out", out)
        self.assertEqual(code, 2)
        self.assertFalse(os.path.exists(out))

    def test_a_tracked_path_that_does_not_exist_yet_is_fine(self):
        out = os.path.join(self.tmp.name, "r", "new_dev.json")
        with mock.patch.object(RUN, "_tracked_by_git", return_value=True):
            code, _err = self._main("--name", "new", "--workers", "1", "--out", out)
        self.assertEqual(code, 0)

    def test_an_untracked_existing_results_file_is_overwritten(self):
        out = self._existing_results()
        code, _err = self._main("--name", "baseline", "--workers", "1", "--out", out)
        self.assertEqual(code, 0)
        with open(out, encoding="utf-8") as fh:
            self.assertIn("outcomes", json.load(fh))

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
