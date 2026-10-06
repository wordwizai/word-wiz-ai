"""Shared paths, flags and helpers for the speechocean762 accuracy benchmark.

Importing this module puts ``backend/`` on ``sys.path`` so ``core`` imports work from
any entry point. It deliberately imports nothing from ``core``. Several WWAI_* flags are
read once when a ``core`` module is imported, so flags must be applied before that.
"""

from __future__ import annotations

import contextlib
import io
import logging
import os
import re
import subprocess
import sys

BENCH_ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.abspath(os.path.join(BENCH_ROOT, "..", ".."))
REPO_ROOT = os.path.abspath(os.path.join(BACKEND_ROOT, ".."))
SUBSETS_DIR = os.path.join(BENCH_ROOT, "subsets")
FIXTURES_DIR = os.path.join(BENCH_ROOT, "fixtures")
TEST_RUNS_LOG = os.path.join(BENCH_ROOT, "test_runs.log")

UNLOCK_ENV = "WWAI_BENCH_UNLOCK_TEST"
VERBOSE_ENV = "WWAI_BENCH_VERBOSE"
DATA_DIR_ENV = "WWAI_BENCH_DATA_DIR"
CACHE_DIR_ENV = "WWAI_BENCH_CACHE_DIR"

#: Flags that change the audio the acoustic models receive. Each distinct setting of
#: these needs its own cache (replay refuses a cache whose recorded inputs differ).
FRONT_END_FLAGS = (
    "WWAI_SINGLE_PREPROCESS",
    "WWAI_CHUNK_PRESERVE_PAUSES",
    "WWAI_CHUNK_OVERLAP_SECONDS",
    "WWAI_CHUNK_THRESHOLD_SECONDS",
    "WWAI_CHUNK_MAX_DURATION",
    "WWAI_CHUNK_MIN_DURATION",
)

_TRUTHY = {"1", "true", "yes", "on"}
_FALSY = {"", "0", "false", "no", "off"}
_BOOLEAN_FRONT_END_FLAGS = ("WWAI_SINGLE_PREPROCESS", "WWAI_CHUNK_PRESERVE_PAUSES")
_CACHE_NAME_VALUE = re.compile(r"[\w.\-]+")
_STATUS_EXCLUDES = (
    ":(exclude)backend/tests/benchmark/test_runs.log",
    ":(exclude)backend/tests/benchmark/results",
)

if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)


class StaleCacheError(RuntimeError):
    """The cache does not match what the current code feeds the models. Rebuild it."""


class ReplayedError(Exception):
    """An exception recorded while building the cache, raised again during replay."""

    def __init__(self, error_type: str, message: str):
        super().__init__(f"{error_type}: {message}")
        self.error_type = error_type
        self.message = message

    def __reduce__(self):
        return (type(self), (self.error_type, self.message))


class ReplayedValueError(ReplayedError, ValueError):
    """A recorded exception that was a ValueError, replayed so `except ValueError` still matches."""


def data_dir() -> str:
    return os.getenv(DATA_DIR_ENV) or os.path.join(BENCH_ROOT, "data")


def cache_root() -> str:
    return os.getenv(CACHE_DIR_ENV) or os.path.join(BENCH_ROOT, "cache")


def results_dir() -> str:
    return os.path.join(BENCH_ROOT, "results")


def env_flag(name: str, env=None) -> bool:
    source = os.environ if env is None else env
    return str(source.get(name, "")).strip().lower() in _TRUTHY


def parse_flag_args(pairs) -> dict[str, str]:
    """Turn repeated ``--flag WWAI_NAME=VALUE`` arguments into a dict."""
    flags: dict[str, str] = {}
    for pair in pairs or []:
        key, sep, value = pair.partition("=")
        key = key.strip()
        if not sep or not key.startswith("WWAI_"):
            raise ValueError(f"--flag expects WWAI_NAME=VALUE, got {pair!r}")
        if key.startswith("WWAI_BENCH_"):
            raise ValueError(
                f"{key} is a harness setting and must be set as an environment variable, not with --flag"
            )
        flags[key] = value.strip()
    return flags


def _core_imported() -> bool:
    return any(name == "core" or name.startswith("core.") for name in sys.modules)


def apply_flags(flags: dict[str, str]) -> None:
    """Set WWAI_* flags for this process and any child process it spawns."""
    if flags and _core_imported():
        raise RuntimeError(
            "apply_flags() must run before the first core import, "
            "because some WWAI_* flags are read at import time"
        )
    os.environ.update(flags)


def active_wwai_flags(env=None) -> dict[str, str]:
    source = os.environ if env is None else env
    return {
        k: v
        for k, v in sorted(source.items())
        if k.startswith("WWAI_") and not k.startswith("WWAI_BENCH_")
    }


def front_end_cache_name(flags: dict[str, str]) -> str:
    """Default cache for a flag set. 'baseline' unless a front-end flag is set."""
    parts = []
    for key in sorted(flags):
        if key not in FRONT_END_FLAGS:
            continue
        value = str(flags[key])
        if value == "" or (key in _BOOLEAN_FRONT_END_FLAGS and value.strip().lower() in _FALSY):
            continue
        if not _CACHE_NAME_VALUE.fullmatch(value):
            raise ValueError(
                f"{key}={value!r} cannot be part of a cache directory name (allowed characters are letters, digits, _ . -)"
            )
        parts.append(f"{key}={value}")
    return "+".join(parts) if parts else "baseline"


@contextlib.contextmanager
def quiet():
    """Swallow the pipeline's print() and logging noise unless WWAI_BENCH_VERBOSE is set."""
    if env_flag(VERBOSE_ENV):
        yield
        return
    previous = logging.root.manager.disable
    logging.disable(logging.WARNING)
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            yield
    finally:
        logging.disable(previous)


def git_sha(cwd: str = REPO_ROOT) -> str:
    """HEAD commit, with '-dirty' when tracked files have uncommitted changes."""
    try:
        sha = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=cwd, capture_output=True, text=True, encoding="utf-8", check=True
        ).stdout.strip()
        dirty = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=no", "--", ".", *_STATUS_EXCLUDES],
            cwd=cwd, capture_output=True, check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return f"{sha}-dirty" if dirty else sha
