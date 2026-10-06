import io
import logging
import os
import pickle
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock

from tests.benchmark import common


class _SubReplayedError(common.ReplayedError):
    pass


class TestFlags(unittest.TestCase):
    def test_parse_flag_args(self):
        self.assertEqual(
            common.parse_flag_args(["WWAI_WEIGHTED_PER=1", "WWAI_G2P_STRICT=true"]),
            {"WWAI_WEIGHTED_PER": "1", "WWAI_G2P_STRICT": "true"},
        )

    def test_parse_flag_args_rejects_non_wwai(self):
        with self.assertRaises(ValueError):
            common.parse_flag_args(["PATH=x"])
        with self.assertRaises(ValueError):
            common.parse_flag_args(["WWAI_NO_EQUALS"])

    def test_parse_flag_args_rejects_bench_settings(self):
        with self.assertRaises(ValueError):
            common.parse_flag_args(["WWAI_BENCH_DATA_DIR=x"])

    def test_front_end_cache_name(self):
        self.assertEqual(common.front_end_cache_name({}), "baseline")
        self.assertEqual(common.front_end_cache_name({"WWAI_WEIGHTED_PER": "1"}), "baseline")
        self.assertEqual(
            common.front_end_cache_name({"WWAI_SINGLE_PREPROCESS": "1", "WWAI_WEIGHTED_PER": "1"}),
            "WWAI_SINGLE_PREPROCESS=1",
        )
        self.assertEqual(common.front_end_cache_name({"WWAI_SINGLE_PREPROCESS": ""}), "baseline")

    def test_front_end_cache_name_treats_falsy_booleans_as_unset(self):
        for value in ("0", "false", "False", "no", "OFF"):
            self.assertEqual(common.front_end_cache_name({"WWAI_SINGLE_PREPROCESS": value}), "baseline")
            self.assertEqual(common.front_end_cache_name({"WWAI_CHUNK_PRESERVE_PAUSES": value}), "baseline")
        self.assertEqual(
            common.front_end_cache_name({"WWAI_CHUNK_OVERLAP_SECONDS": "0.5"}),
            "WWAI_CHUNK_OVERLAP_SECONDS=0.5",
        )

    def test_front_end_cache_name_rejects_unsafe_values(self):
        for bad in ("..\\x", "a:b", "a*b"):
            with self.assertRaises(ValueError):
                common.front_end_cache_name({"WWAI_CHUNK_OVERLAP_SECONDS": bad})

    def test_active_wwai_flags_skips_bench_and_other_vars(self):
        env = {"WWAI_WEIGHTED_PER": "1", "WWAI_BENCH_VERBOSE": "1", "PATH": "x"}
        self.assertEqual(common.active_wwai_flags(env), {"WWAI_WEIGHTED_PER": "1"})

    def test_active_wwai_flags_skips_deploy_settings(self):
        # CLAUDE.md's deploy section exports these. WWAI_KEY can hold a private key, and the flags
        # are written into _cache_meta.json and the committed results files of a public repo.
        env = {
            "WWAI_HOST": "203.0.113.7", "WWAI_USER": "ubuntu", "WWAI_KEY": "/home/me/key.pem",
            "WWAI_WEIGHTED_PER": "1", "WWAI_BENCH_VERBOSE": "1",
        }
        self.assertEqual(common.active_wwai_flags(env), {"WWAI_WEIGHTED_PER": "1"})

    def test_the_deny_list_names_exactly_the_deploy_settings(self):
        self.assertEqual(set(common._NOT_FLAGS), {"WWAI_HOST", "WWAI_USER", "WWAI_KEY"})

    def test_active_wwai_flags_reads_the_real_environment_by_default(self):
        with mock.patch.dict(os.environ, {"WWAI_KEY": "secret", "WWAI_WEIGHTED_PER": "1"}):
            flags = common.active_wwai_flags()
        self.assertNotIn("WWAI_KEY", flags)
        self.assertEqual(flags["WWAI_WEIGHTED_PER"], "1")

    def test_a_flag_that_only_starts_like_a_deploy_setting_is_still_a_flag(self):
        env = {"WWAI_KEYBOARD": "1", "WWAI_USERNAME": "x", "WWAI_HOSTS": "y"}
        self.assertEqual(common.active_wwai_flags(env), env)

    def test_env_flag(self):
        self.assertTrue(common.env_flag("X", {"X": "TRUE"}))
        self.assertFalse(common.env_flag("X", {"X": "0"}))
        self.assertFalse(common.env_flag("X", {}))

    def test_apply_flags_refuses_after_core_import(self):
        # Leaves core imported for the rest of the process.
        import core.model_registry  # noqa: F401  (any core import counts)

        with self.assertRaises(RuntimeError):
            common.apply_flags({"WWAI_WEIGHTED_PER": "1"})
        common.apply_flags({})  # nothing to apply is always fine

    def test_apply_flags_sets_environment_before_core_import(self):
        with mock.patch.object(common, "_core_imported", return_value=False), mock.patch.dict(os.environ):
            common.apply_flags({"WWAI_WEIGHTED_PER": "1"})
            self.assertEqual(os.environ["WWAI_WEIGHTED_PER"], "1")


class TestDotenvWwaiKeys(unittest.TestCase):
    def test_lists_experiment_flags_and_ignores_the_rest(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, ".env")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("WWAI_WEIGHTED_PER=1\nWWAI_BENCH_VERBOSE=1\nDEEPGRAM_KEY=x\n")
            self.assertEqual(common.dotenv_wwai_keys(path), ["WWAI_WEIGHTED_PER"])

    def test_deploy_settings_are_not_experiment_flags(self):
        # backend/.env is not where the deploy settings live, but if they are there they must not
        # make every benchmark command refuse to start.
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, ".env")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("WWAI_HOST=1.2.3.4\nWWAI_USER=ubuntu\nWWAI_KEY=/k.pem\nWWAI_WEIGHTED_PER=1\n")
            self.assertEqual(common.dotenv_wwai_keys(path), ["WWAI_WEIGHTED_PER"])

    def test_missing_file_is_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(common.dotenv_wwai_keys(os.path.join(tmp, "nope.env")), [])


class TestDirs(unittest.TestCase):
    def test_env_overrides(self):
        with mock.patch.dict(os.environ, {"WWAI_BENCH_DATA_DIR": "/tmp/d", "WWAI_BENCH_CACHE_DIR": "/tmp/c"}):
            self.assertEqual(common.data_dir(), "/tmp/d")
            self.assertEqual(common.cache_root(), "/tmp/c")
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("WWAI_BENCH_DATA_DIR", None)
            self.assertEqual(common.data_dir(), os.path.join(common.BENCH_ROOT, "data"))


class TestQuiet(unittest.TestCase):
    def test_quiet_swallows_print(self):
        outer = io.StringIO()
        with mock.patch.dict(os.environ, {common.VERBOSE_ENV: ""}):
            with redirect_stdout(outer):
                with common.quiet():
                    print("noise")
        self.assertEqual(outer.getvalue(), "")


    def test_quiet_restores_state_after_exception(self):
        disable, out, err = logging.root.manager.disable, sys.stdout, sys.stderr
        with mock.patch.dict(os.environ, {common.VERBOSE_ENV: ""}):
            with self.assertRaises(KeyError):
                with common.quiet():
                    raise KeyError("boom")
        self.assertEqual(logging.root.manager.disable, disable)
        self.assertIs(sys.stdout, out)
        self.assertIs(sys.stderr, err)


class TestExceptions(unittest.TestCase):
    def test_replayed_error_pickles(self):
        err = pickle.loads(pickle.dumps(common.ReplayedError("DeepgramTimeout", "slow")))
        self.assertEqual(err.error_type, "DeepgramTimeout")
        self.assertEqual(err.message, "slow")

    def test_replayed_error_text_is_the_recorded_message(self):
        # analyze_clip stores str(exc), so a replayed rejection reads the same as the live one.
        self.assertEqual(str(common.ReplayedError("EmptyAudioError", "no audio")), "no audio")
        self.assertEqual(str(common.ReplayedValueError("EmptyAudioError", "no audio")), "no audio")

    def test_replayed_error_subclass_pickles_as_subclass(self):
        err = pickle.loads(pickle.dumps(_SubReplayedError("T", "m")))
        self.assertIs(type(err), _SubReplayedError)
        self.assertEqual((err.error_type, err.message), ("T", "m"))

    def test_replayed_value_error_is_both_kinds_and_pickles(self):
        err = common.ReplayedValueError("EmptyAudioError", "no audio")
        self.assertIsInstance(err, ValueError)
        self.assertIsInstance(err, common.ReplayedError)
        back = pickle.loads(pickle.dumps(err))
        self.assertIs(type(back), common.ReplayedValueError)
        self.assertEqual((back.error_type, back.message), ("EmptyAudioError", "no audio"))

    def test_git_sha_format(self):
        self.assertRegex(common.git_sha(), r"^([0-9a-f]{40}(-dirty)?|unknown)$")


class TestRealProcessor(unittest.TestCase):
    def test_real_processor_has_vocab_and_is_memoized(self):
        from tests.benchmark import testutil

        first = testutil.real_processor_or_skip()
        self.assertIn("|", first.tokenizer.get_vocab())
        self.assertIs(testutil.real_processor_or_skip(), first)


if __name__ == "__main__":
    unittest.main()
