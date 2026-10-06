# SpeechOcean762 Accuracy Benchmark Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the cache-and-replay benchmark from `docs/superpowers/specs/2026-10-05-speechocean-accuracy-benchmark-design.md` and record a verified dev-half baseline, so the Round 0 flag sweep and the agent rounds have something trustworthy to measure against.

**Architecture:** The slow stages (preprocessing, ONNX logits, Deepgram words) run once per clip through the real request path with recording wrappers around the models. Each recorded call stores a hash of the exact audio the model received. Scoring runs the real production pipeline again with replay wrappers that return the cached outputs and refuse to continue when the audio they receive no longer matches (any front-end change). Pure metric code turns the outputs plus speechocean762's expert labels into word-level F0.5 and the other numbers in the spec, and a paired speaker bootstrap decides whether one configuration beats another.

**Tech Stack:** Python 3.11 (backend venv), numpy, soundfile, onnxruntime, transformers (tokenizer only during replay), psutil, `unittest` (the repo's test runner; pytest is not installed), multiprocessing with the `spawn` context.

**Scope:** This plan ends with the baseline recorded. The agent-round runbook (agent prompts, worktree setup, review gate) is a second plan, written after the baseline numbers exist, because the prompts depend on what the baseline shows.

---

## Conventions for every task

- All commands run from `backend/` in Git Bash. Always prefix Python with `PYTHONIOENCODING=utf-8` (the Windows console is cp1252 and dies on IPA).
- Python is `venv/Scripts/python.exe`.
- Run one test module with `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.benchmark.test_<name> -v`.
- Benchmark modules use relative imports (`from . import common`). Test modules use absolute imports (`from tests.benchmark import metrics as M`).
- `tests/benchmark/common.py` puts `backend/` on `sys.path` and must stay free of `core` imports, because several `WWAI_*` flags are read once when `core` modules are imported.
- Commit after every task with the message shown, plus a `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` trailer.
- Writing in READMEs and docs follows Bruce's rules in `~/.claude/CLAUDE.md`. Never use "gap", "choice" as a noun, "ceiling", "leak" or "split". Say "half" for the dev/test halves.

## File map

**New benchmark package** `backend/tests/benchmark/`

| File | Responsibility |
|---|---|
| `__init__.py` | Package marker |
| `.gitignore` | Keeps data, caches and exploratory results out of git |
| `common.py` | Paths, env overrides, flag handling, `quiet()`, `git_sha()`, shared exceptions |
| `metrics.py` | Pure metrics (mistake definitions, confusion counts, F0.5, Pearson, thresholds, speaker bootstrap) |
| `phones.py` | ARPAbet to IPA, canonical-to-system phone mapping, per-phone error flags |
| `dataset.py` | Download, parse, speaker check, fixed subsets, CLI |
| `pipeline.py` | One clip through the production request path with pluggable models |
| `stage_cache.py` | Recording wrappers, cache entries, parallel cache builder, CLI |
| `replay.py` | Replay wrappers with the stale-input check |
| `scoring.py` | Joins outcomes with labels into items and computes the summary |
| `run.py` | Scores one configuration, test-half lock and ledger, CLI |
| `compare.py` | Paired comparison and acceptance conditions 1 to 4, CLI |
| `human_reference.py` | Annotator-vs-annotator agreement, CLI |
| `speed.py` | Serial latency and memory measurement and budget check, CLI |
| `sweep.py` | Round 0 greedy flag sweep, CLI |
| `README.md` | How to use all of the above |
| `test_runs.log` | Committed ledger of every test-half run |
| `testutil.py` | Shared test helpers and fakes |
| `fixtures/mini_speechocean/` | Tiny dataset in the real layout |
| `fixtures/onnx_golden_test_case_02.json` | Extractor output recorded before the logits refactor |
| `subsets/smoke_dev.txt`, `subsets/speed_dev.txt` | Fixed clip lists (created in Task 20) |
| `results/` | Committed summaries, baseline, speed and human-reference files |
| `test_common.py`, `test_metrics.py`, `test_phones.py`, `test_dataset.py`, `test_pipeline.py`, `test_stage_cache.py`, `test_replay.py`, `test_scoring.py`, `test_run.py`, `test_compare.py`, `test_human_reference.py`, `test_speed.py`, `test_sweep.py`, `test_live_parity.py` | Tests |

**New production module** `backend/core/request_audio.py` holds the quality gates and the single preprocessing pass, lifted out of the router so the benchmark runs the same gates.

**Modified production files**

| File | Change |
|---|---|
| `backend/core/grapheme_to_phoneme.py` | Add `clean_sentence()` |
| `backend/core/phoneme_assistant.py` | Use `clean_sentence()` |
| `backend/routers/handlers/audio_processing_handler.py` | Call `gate_and_preprocess()` and turn `AudioRejected` into a 400 |
| `backend/core/phoneme_feedback_formatter.py` | Hoist `HIGH_PER_THRESHOLD` to module level |
| `backend/core/phoneme_extractor_onnx.py` | Add `decode_logits()` and `extract_logits()`, wire the model pin |
| `backend/core/model_registry.py` | Pin `PHONEME_IPA_ONNX` |

**New production tests** in `backend/tests/` are `test_clean_sentence.py`, `test_request_audio.py`, `test_feedback_threshold.py`, `test_onnx_logits_split.py` and `test_onnx_pin_wiring.py`.

---

### Task 1: Benchmark package scaffolding

**Files:**
- Create: `backend/tests/benchmark/__init__.py`
- Create: `backend/tests/benchmark/.gitignore`
- Create: `backend/tests/benchmark/common.py`
- Create: `backend/tests/benchmark/testutil.py`
- Create: `backend/tests/benchmark/test_runs.log`
- Test: `backend/tests/benchmark/test_common.py`

- [ ] **Step 1: Create the package marker, gitignore and ledger**

`backend/tests/benchmark/__init__.py`:

```python
"""speechocean762 accuracy benchmark. See README.md in this folder."""
```

`backend/tests/benchmark/.gitignore`:

```
data/
cache/
results/*.json
!results/*.summary.json
!results/baseline_dev.json
!results/*_speed.json
!results/human_reference_*.json
```

`backend/tests/benchmark/test_runs.log`:

```
# Every run against the sealed test half is appended here by tests/benchmark/run.py.
# timestamp	git sha	config	reason
```

- [ ] **Step 2: Write the failing tests**

`backend/tests/benchmark/test_common.py`:

```python
import io
import os
import pickle
import unittest
from contextlib import redirect_stdout
from unittest import mock

from tests.benchmark import common


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

    def test_front_end_cache_name(self):
        self.assertEqual(common.front_end_cache_name({}), "baseline")
        self.assertEqual(common.front_end_cache_name({"WWAI_WEIGHTED_PER": "1"}), "baseline")
        self.assertEqual(
            common.front_end_cache_name({"WWAI_SINGLE_PREPROCESS": "1", "WWAI_WEIGHTED_PER": "1"}),
            "WWAI_SINGLE_PREPROCESS=1",
        )
        self.assertEqual(common.front_end_cache_name({"WWAI_SINGLE_PREPROCESS": ""}), "baseline")

    def test_active_wwai_flags_skips_bench_and_other_vars(self):
        env = {"WWAI_WEIGHTED_PER": "1", "WWAI_BENCH_VERBOSE": "1", "PATH": "x"}
        self.assertEqual(common.active_wwai_flags(env), {"WWAI_WEIGHTED_PER": "1"})

    def test_env_flag(self):
        self.assertTrue(common.env_flag("X", {"X": "TRUE"}))
        self.assertFalse(common.env_flag("X", {"X": "0"}))
        self.assertFalse(common.env_flag("X", {}))

    def test_apply_flags_refuses_after_core_import(self):
        import core.model_registry  # noqa: F401  (any core import counts)

        with self.assertRaises(RuntimeError):
            common.apply_flags({"WWAI_WEIGHTED_PER": "1"})
        common.apply_flags({})  # nothing to apply is always fine


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


class TestExceptions(unittest.TestCase):
    def test_replayed_error_pickles(self):
        err = pickle.loads(pickle.dumps(common.ReplayedError("DeepgramTimeout", "slow")))
        self.assertEqual(err.error_type, "DeepgramTimeout")
        self.assertEqual(err.message, "slow")

    def test_git_sha_is_a_string(self):
        self.assertIsInstance(common.git_sha(), str)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.benchmark.test_common -v`
Expected: ERROR, `ImportError: cannot import name 'common'`.

- [ ] **Step 4: Write `common.py`**

`backend/tests/benchmark/common.py`:

```python
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
        return (ReplayedError, (self.error_type, self.message))


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
    parts = [f"{k}={flags[k]}" for k in sorted(flags) if k in FRONT_END_FLAGS and flags[k] != ""]
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
            ["git", "rev-parse", "HEAD"], cwd=cwd, capture_output=True, text=True, check=True
        ).stdout.strip()
        dirty = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=no"],
            cwd=cwd, capture_output=True, text=True, check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return f"{sha}-dirty" if dirty else sha
```

- [ ] **Step 5: Write `testutil.py`** (helpers used by later tasks; every import inside is lazy)

`backend/tests/benchmark/testutil.py`:

```python
"""Shared helpers and fakes for the benchmark tests. Imports are lazy on purpose."""

from __future__ import annotations

import os
import shutil
import unittest

import numpy as np

from tests.benchmark import common

SAMPLE_WAV = os.path.join(common.BACKEND_ROOT, "tests", "system", "test_case_02", "audio.wav")
SAMPLE_TEXT = "the quick brown fox jumped over the lazy dog"
SAMPLE_IPA = "ðə kwɪk braʊn fɑks ʤəmpt oʊvər ðə leɪzi dɔg"
MINI_DATASET = os.path.join(common.FIXTURES_DIR, "mini_speechocean")


def make_temp_dataset(tmpdir: str) -> str:
    """Copy the mini fixture into tmpdir and give every clip the sample WAV as audio."""
    root = os.path.join(tmpdir, "speechocean762")
    shutil.copytree(MINI_DATASET, root)
    for half in ("train", "test"):
        with open(os.path.join(root, half, "wav.scp"), encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                _utt, rel = line.split()
                dst = os.path.join(root, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy(SAMPLE_WAV, dst)
    return root


def real_processor_or_skip():
    """The real wav2vec2 tokenizer from the local HF cache, or SkipTest."""
    try:
        from transformers import Wav2Vec2Processor
        from core.model_registry import from_pretrained_kwargs, repo_id

        with common.quiet():
            return Wav2Vec2Processor.from_pretrained(
                repo_id("PHONEME_IPA_ONNX"), **from_pretrained_kwargs("PHONEME_IPA_ONNX")
            )
    except Exception as exc:  # noqa: BLE001
        raise unittest.SkipTest(f"wav2vec2 processor unavailable: {exc}")


class FakeOnnx:
    """Stands in for PhonemeExtractorONNX. One-hot logits that decode to `transcription`."""

    def __init__(self, processor, transcription: str = SAMPLE_IPA):
        from core.phoneme_extractor_onnx import default_model_output_processing

        self.processor = processor
        self.model_output_processing = default_model_output_processing
        self._transcription = transcription

    def extract_logits(self, audio, sampling_rate=16000, **_kwargs):
        vocab = self.processor.tokenizer.get_vocab()
        ids = [vocab["|"] if ch == " " else vocab[ch] for ch in self._transcription]
        logits = np.full((1, len(ids), len(vocab)), -10.0, dtype=np.float32)
        logits[0, np.arange(len(ids)), ids] = 10.0
        return logits


class FakeOnnxExtractor:
    """Has extract_phoneme like the real extractor, built on FakeOnnx logits."""

    def __init__(self, processor, transcription: str = SAMPLE_IPA):
        self.inner = FakeOnnx(processor, transcription)

    def extract_phoneme(self, audio, sampling_rate=16000, **_kwargs):
        from core.phoneme_extractor_onnx import decode_logits

        logits = self.inner.extract_logits(audio, sampling_rate)
        return decode_logits(logits, self.inner.processor, self.inner.model_output_processing)


class FakeWords:
    def __init__(self, words=None):
        self.words = list(words if words is not None else SAMPLE_TEXT.split())

    def extract_words(self, audio, sampling_rate=16000, **_kwargs):
        return list(self.words)


def synthetic_clip(utt_id, speaker, age, words, sentence_accuracy=8.0, half="dev"):
    """words: list of (text, accuracy, "ARPA PHONES", [phone accuracies])."""
    from tests.benchmark.dataset import Clip, Word

    return Clip(
        utt_id=utt_id, speaker=speaker, age=age, half=half,
        text=" ".join(w[0] for w in words), wav_path="",
        sentence_accuracy=float(sentence_accuracy),
        words=[Word(t, float(a), p.split(), [float(x) for x in pa]) for t, a, p, pa in words],
    )


def record(word, expected, actual, per, rtype=None):
    expected, actual = list(expected), list(actual)
    return {
        "type": rtype or ("match" if per == 0 else "substitution"),
        "ground_truth_word": word,
        "expected_phonemes": expected,
        "actual_phonemes": actual,
        "per": per,
        "total_errors": int(round(per * len(expected))),
        "total_phonemes": len(expected),
    }


def ok(*records):
    return {"status": "ok", "words": list(records), "error_type": None, "error": None}


def rejected(error_type="AudioRejected"):
    return {"status": "rejected", "words": [], "error_type": error_type, "error": "rejected"}


def results_dict(name, outcomes, half="dev", subset=None, threshold=0.4):
    return {"name": name, "half": half, "subset": subset, "threshold": threshold, "outcomes": outcomes}
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.benchmark.test_common -v`
Expected: `OK` (10 tests).

- [ ] **Step 7: Commit**

```bash
git add tests/benchmark/__init__.py tests/benchmark/.gitignore tests/benchmark/common.py tests/benchmark/testutil.py tests/benchmark/test_runs.log tests/benchmark/test_common.py
git commit -m "Add speechocean762 benchmark scaffolding" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Pure metrics

**Files:**
- Create: `backend/tests/benchmark/metrics.py`
- Test: `backend/tests/benchmark/test_metrics.py`

- [ ] **Step 1: Write the failing tests**

`backend/tests/benchmark/test_metrics.py`:

```python
import unittest

import numpy as np

from tests.benchmark import metrics as M


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


class TestPearson(unittest.TestCase):
    def test_perfect(self):
        self.assertAlmostEqual(M.pearson([1, 2, 3], [2, 4, 6]), 1.0)

    def test_undefined(self):
        self.assertIsNone(M.pearson([1, 1, 1], [1, 2, 3]))
        self.assertIsNone(M.pearson([1], [1]))


class TestBootstrap(unittest.TestCase):
    def test_per_speaker_counts(self):
        counts = M.per_speaker_counts(["a", "a", "b"], [True, False, True], [True, True, False])
        self.assertEqual(counts["a"].tolist(), [1, 1, 0, 0])
        self.assertEqual(counts["b"].tolist(), [0, 0, 1, 0])

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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.benchmark.test_metrics -v`
Expected: ERROR, `ImportError: cannot import name 'metrics'`.

- [ ] **Step 3: Write `metrics.py`**

`backend/tests/benchmark/metrics.py`:

```python
"""Pure metric functions for the benchmark. No I/O and no core imports."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

#: speechocean762 word rubric. 0-6 means phones wrong, the wrong word, or missed.
WORD_MISTAKE_MAX = 6
#: Phone rubric. 0 means incorrect or missed, 1 heavy accent, 2 correct.
PHONE_MISTAKE_MAX = 0
PHONE_MISTAKE_MAX_STRICT = 1
F_BETA = 0.5


def rounded(score: float) -> int:
    """Round half up. Released phone scores are 5-annotator averages such as 1.8."""
    return int(math.floor(float(score) + 0.5))


def word_is_mistake(accuracy: float) -> bool:
    return rounded(accuracy) <= WORD_MISTAKE_MAX


def phone_is_mistake(accuracy: float, strict: bool = False) -> bool:
    return rounded(accuracy) <= (PHONE_MISTAKE_MAX_STRICT if strict else PHONE_MISTAKE_MAX)


def _ratio(num, den) -> float:
    return float(num) / den if den else 0.0


def f_beta_from_counts(counts, beta: float = F_BETA):
    """F-beta from arrays shaped [..., 4] of (tp, fp, fn, tn). 0 where undefined."""
    counts = np.asarray(counts, dtype=np.float64)
    tp, fp, fn = counts[..., 0], counts[..., 1], counts[..., 2]
    b2 = beta * beta
    den = (1 + b2) * tp + b2 * fn + fp
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(den > 0, (1 + b2) * tp / np.where(den > 0, den, 1), 0.0)


@dataclass(frozen=True)
class Counts:
    tp: int = 0
    fp: int = 0
    fn: int = 0
    tn: int = 0

    @property
    def n(self) -> int:
        return self.tp + self.fp + self.fn + self.tn

    @property
    def precision(self) -> float:
        return _ratio(self.tp, self.tp + self.fp)

    @property
    def recall(self) -> float:
        return _ratio(self.tp, self.tp + self.fn)

    @property
    def false_alarm_rate(self) -> float:
        """Share of correctly read items that the system flagged."""
        return _ratio(self.fp, self.fp + self.tn)

    def f_beta(self, beta: float = F_BETA) -> float:
        return float(f_beta_from_counts([self.tp, self.fp, self.fn, self.tn], beta))


def confusion(labels, flags) -> Counts:
    if len(labels) != len(flags):
        raise ValueError(f"labels ({len(labels)}) and flags ({len(flags)}) differ in length")
    tp = fp = fn = tn = 0
    for label, flag in zip(labels, flags):
        if label and flag:
            tp += 1
        elif flag:
            fp += 1
        elif label:
            fn += 1
        else:
            tn += 1
    return Counts(tp, fp, fn, tn)


def flags_at(scores, threshold: float) -> list[bool]:
    return [s >= threshold for s in scores]


def best_threshold(labels, scores, beta: float = F_BETA):
    """(threshold, F-beta) maximizing F-beta, flagging score >= threshold.

    Ties go to the higher threshold, which flags fewer words. Returns (None, 0.0) when no
    threshold gives a positive F-beta.
    """
    best_t, best_f = None, 0.0
    for t in sorted(set(scores), reverse=True):
        f = confusion(labels, flags_at(scores, t)).f_beta(beta)
        if f > best_f:
            best_t, best_f = t, f
    return best_t, best_f


def pr_curve(labels, scores) -> list[dict]:
    points = []
    for t in sorted(set(scores)):
        c = confusion(labels, flags_at(scores, t))
        points.append({
            "threshold": t,
            "precision": c.precision,
            "recall": c.recall,
            "false_alarm_rate": c.false_alarm_rate,
        })
    return points


def pearson(x, y):
    """Pearson r, or None when undefined (fewer than 2 points or zero variance)."""
    if len(x) != len(y):
        raise ValueError("x and y differ in length")
    if len(x) < 2:
        return None
    xa, ya = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    if xa.std() == 0 or ya.std() == 0:
        return None
    return float(np.corrcoef(xa, ya)[0, 1])


def per_speaker_counts(speakers, labels, flags) -> dict[str, np.ndarray]:
    out: dict[str, np.ndarray] = {}
    for speaker, label, flag in zip(speakers, labels, flags):
        arr = out.setdefault(speaker, np.zeros(4, dtype=np.int64))
        arr[0 if (label and flag) else 1 if flag else 2 if label else 3] += 1
    return out


def bootstrap_fbeta_delta(base_counts, cand_counts, n_resamples=2000, seed=0, beta=F_BETA):
    """Paired speaker bootstrap of F-beta(candidate) minus F-beta(base).

    Speakers are resampled with replacement and the same resample is applied to both
    systems. Clips from one speaker are correlated, so resampling clips instead would
    make noise look like signal.
    """
    speakers = sorted(set(base_counts) | set(cand_counts))
    if not speakers:
        raise ValueError("no speakers to resample")
    zero = np.zeros(4, dtype=np.int64)
    base = np.stack([base_counts.get(s, zero) for s in speakers])
    cand = np.stack([cand_counts.get(s, zero) for s in speakers])
    rng = np.random.default_rng(seed)
    picks = rng.integers(0, len(speakers), size=(n_resamples, len(speakers)))
    return f_beta_from_counts(cand[picks].sum(axis=1), beta) - f_beta_from_counts(base[picks].sum(axis=1), beta)


def percentile_interval(values, level: float = 0.95) -> tuple[float, float]:
    alpha = (1.0 - level) / 2.0
    lo, hi = np.quantile(np.asarray(values, dtype=float), [alpha, 1.0 - alpha])
    return float(lo), float(hi)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.benchmark.test_metrics -v`
Expected: `OK` (19 tests).

- [ ] **Step 5: Commit**

```bash
git add tests/benchmark/metrics.py tests/benchmark/test_metrics.py
git commit -m "Add benchmark metrics with speaker bootstrap" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Phone mapping helpers

**Files:**
- Create: `backend/tests/benchmark/phones.py`
- Test: `backend/tests/benchmark/test_phones.py`

- [ ] **Step 1: Write the failing tests**

`backend/tests/benchmark/test_phones.py`:

```python
import unittest

from tests.benchmark import phones as P


class TestArpabet(unittest.TestCase):
    def test_strips_stress(self):
        self.assertEqual(P.arpabet_to_ipa("IY0"), "i")
        self.assertEqual(P.arpabet_to_ipa("AH1"), "ə")

    def test_unknown_phone(self):
        with self.assertRaises(ValueError):
            P.arpabet_to_ipa("QQ")

    def test_matches_eng_to_ipa(self):
        import eng_to_ipa

        cases = {
            "cat": "K AE1 T", "church": "CH ER1 CH", "judge": "JH AH1 JH", "boy": "B OY1",
            "house": "HH AW1 S", "yes": "Y EH1 S", "measure": "M EH1 ZH ER0", "thin": "TH IH1 N",
            "sing": "S IH1 NG", "food": "F UW1 D", "go": "G OW1", "day": "D EY1", "my": "M AY1",
            "book": "B UH1 K", "father": "F AA1 DH ER0", "caught": "K AO1 T", "this": "DH IH1 S",
            "ship": "SH IH1 P", "see": "S IY1", "hat": "HH AE1 T",
        }
        for word, arpa in cases.items():
            with self.subTest(word=word):
                expected = eng_to_ipa.convert(word).replace("ˈ", "").replace("ˌ", "")
                self.assertEqual("".join(P.canonical_ipa(arpa.split())), expected)


class TestMapping(unittest.TestCase):
    def test_legacy_tokenization_splits_diphthongs(self):
        self.assertEqual(P.map_canonical_to_system(["m", "aɪ"], ["m", "a", "ɪ"]), [[0], [1, 2]])

    def test_normalized_tokenization(self):
        self.assertEqual(P.map_canonical_to_system(["m", "aɪ"], ["m", "aɪ"]), [[0], [1]])

    def test_missing_system_phone_is_unmapped(self):
        self.assertEqual(P.map_canonical_to_system(["k", "æ", "t"], ["k", "æ"]), [[0], [1], []])

    def test_unknown_marker_carries_no_sounds(self):
        self.assertEqual(P.map_canonical_to_system(["k", "æ", "t"], ["<unk>"]), [[], [], []])

    def test_g2p_agrees_ignores_tokenization(self):
        self.assertTrue(P.g2p_agrees(["m", "aɪ"], ["m", "a", "ɪ"]))
        self.assertFalse(P.g2p_agrees(["m", "aɪ"], ["m", "a"]))


class TestErrorFlags(unittest.TestCase):
    def test_substitution_and_deletion(self):
        self.assertEqual(P.gt_error_flags(["k", "æ", "t"], ["k", "ɛ"]), [False, True, True])

    def test_deleted_word(self):
        self.assertEqual(P.gt_error_flags(["k", "æ", "t"], []), [True, True, True])

    def test_insertions_are_not_expected_phones(self):
        self.assertEqual(P.gt_error_flags(["k", "æ", "t"], ["k", "æ", "æ", "t"]), [False, False, False])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.benchmark.test_phones -v`
Expected: ERROR, `ImportError: cannot import name 'phones'`.

- [ ] **Step 3: Write `phones.py`**

`backend/tests/benchmark/phones.py`:

```python
"""ARPAbet to IPA helpers and phone-position mapping for phone-level scoring.

speechocean762 labels canonical phones in ARPAbet with stress digits. Production G2P
emits IPA through eng_to_ipa, tokenized one codepoint per phoneme (legacy) or
longest-match (WWAI_PHONEME_NORMALIZATION). Mapping works on characters, so it holds
for either tokenization.
"""

from __future__ import annotations

from . import common  # noqa: F401  (puts backend/ on sys.path)
from core.gt_alignment import align_sequences

# Matches eng_to_ipa's conventions, checked against eng_to_ipa.convert in the tests.
# AH is ə in every stress position, ER is ər, CH and JH use the ʧ/ʤ ligatures, Y is j.
ARPABET_TO_IPA = {
    "AA": "ɑ", "AE": "æ", "AH": "ə", "AO": "ɔ", "AW": "aʊ", "AY": "aɪ",
    "B": "b", "CH": "ʧ", "D": "d", "DH": "ð", "EH": "ɛ", "ER": "ər",
    "EY": "eɪ", "F": "f", "G": "g", "HH": "h", "IH": "ɪ", "IY": "i",
    "JH": "ʤ", "K": "k", "L": "l", "M": "m", "N": "n", "NG": "ŋ",
    "OW": "oʊ", "OY": "ɔɪ", "P": "p", "R": "r", "S": "s", "SH": "ʃ",
    "T": "t", "TH": "θ", "UH": "ʊ", "UW": "u", "V": "v", "W": "w",
    "Y": "j", "Z": "z", "ZH": "ʒ",
}


def arpabet_to_ipa(phone: str) -> str:
    base = phone.strip().upper().rstrip("012")
    try:
        return ARPABET_TO_IPA[base]
    except KeyError:
        raise ValueError(f"unknown ARPAbet phone {phone!r}") from None


def canonical_ipa(phones) -> list[str]:
    return [arpabet_to_ipa(p) for p in phones]


def _chars(tokens) -> tuple[list[str], list[int]]:
    chars: list[str] = []
    owners: list[int] = []
    for index, token in enumerate(tokens):
        if token.startswith("<"):  # strict G2P's "<unk>" carries no sounds
            continue
        for ch in token:
            chars.append(ch)
            owners.append(index)
    return chars, owners


def g2p_agrees(canonical, system) -> bool:
    """True when G2P produced the same sounds as the expert canonical phones."""
    return "".join(_chars(canonical)[0]) == "".join(_chars(system)[0])


def map_canonical_to_system(canonical, system) -> list[list[int]]:
    """For each canonical phone, the indices of the system phones aligned to it."""
    c_chars, c_owner = _chars(canonical)
    s_chars, s_owner = _chars(system)
    mapping = [set() for _ in canonical]
    i = j = 0
    for op, _gt, _pred in align_sequences(c_chars, s_chars):
        if op in ("match", "substitution"):
            mapping[c_owner[i]].add(s_owner[j])
            i += 1
            j += 1
        elif op == "deletion":
            i += 1
        else:  # insertion
            j += 1
    return [sorted(m) for m in mapping]


def gt_error_flags(expected, actual) -> list[bool]:
    """Per expected phoneme, True when production's alignment marks it wrong or missing.

    Uses the same Levenshtein alignment that fills each word's ``missed`` and
    ``substituted`` lists (gt_alignment.align_sequences is behaviorally identical to
    process_audio.align_sequences), so positions agree with what production reported.
    """
    flags = []
    for op, _gt, _pred in align_sequences(list(expected), list(actual)):
        if op != "insertion":
            flags.append(op != "match")
    return flags
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.benchmark.test_phones -v`
Expected: `OK` (11 tests). If `test_matches_eng_to_ipa` fails for a word, eng_to_ipa uses a different symbol than the table. Change the table entry to eng_to_ipa's symbol and rerun.

- [ ] **Step 5: Commit**

```bash
git add tests/benchmark/phones.py tests/benchmark/test_phones.py
git commit -m "Add ARPAbet-to-IPA and phone mapping for phone-level scoring" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Dataset parsing, fixture and subsets

**Files:**
- Create: `backend/tests/benchmark/fixtures/mini_speechocean/` (files listed in Step 1)
- Create: `backend/tests/benchmark/dataset.py`
- Test: `backend/tests/benchmark/test_dataset.py`

- [ ] **Step 1: Create the fixture in the real speechocean762 layout**

`fixtures/mini_speechocean/train/wav.scp`:

```
000010011 WAVE/SPEAKER0001/000010011.WAV
000020022 WAVE/SPEAKER0002/000020022.WAV
```

`fixtures/mini_speechocean/train/utt2spk`:

```
000010011 0001
000020022 0002
```

`fixtures/mini_speechocean/train/spk2age`:

```
0001 6
0002 30
```

`fixtures/mini_speechocean/train/text`:

```
000010011 WE CALL IT BEAR
000020022 THE QUICK BROWN FOX JUMPED OVER THE LAZY DOG
```

`fixtures/mini_speechocean/test/wav.scp`:

```
000030033 WAVE/SPEAKER0003/000030033.WAV
```

`fixtures/mini_speechocean/test/utt2spk`:

```
000030033 0003
```

`fixtures/mini_speechocean/test/spk2age`:

```
0003 9
```

`fixtures/mini_speechocean/test/text`:

```
000030033 IT IS A CAT
```

`fixtures/mini_speechocean/scores.json`:

```json
{
  "000010011": {
    "text": "WE CALL IT BEAR", "accuracy": 8, "completeness": 10.0, "fluency": 9, "prosodic": 9, "total": 8,
    "words": [
      {"text": "WE", "accuracy": 10, "stress": 10, "total": 10, "phones": "W IY0", "phones-accuracy": [2.0, 2.0]},
      {"text": "CALL", "accuracy": 10, "stress": 10, "total": 10, "phones": "K AO0 L", "phones-accuracy": [2.0, 2.0, 2.0]},
      {"text": "IT", "accuracy": 10, "stress": 10, "total": 10, "phones": "IH0 T", "phones-accuracy": [2.0, 2.0]},
      {"text": "BEAR", "accuracy": 6, "stress": 10, "total": 6, "phones": "B EH0 R", "phones-accuracy": [2.0, 1.6, 0.4]}
    ]
  },
  "000020022": {
    "text": "THE QUICK BROWN FOX JUMPED OVER THE LAZY DOG", "accuracy": 9, "completeness": 10.0, "fluency": 9, "prosodic": 9, "total": 9,
    "words": [
      {"text": "THE", "accuracy": 10, "stress": 10, "total": 10, "phones": "DH AH0", "phones-accuracy": [2.0, 2.0]},
      {"text": "QUICK", "accuracy": 10, "stress": 10, "total": 10, "phones": "K W IH0 K", "phones-accuracy": [2.0, 2.0, 2.0, 2.0]},
      {"text": "BROWN", "accuracy": 10, "stress": 10, "total": 10, "phones": "B R AW0 N", "phones-accuracy": [2.0, 2.0, 2.0, 2.0]},
      {"text": "FOX", "accuracy": 10, "stress": 10, "total": 10, "phones": "F AA0 K S", "phones-accuracy": [2.0, 2.0, 2.0, 2.0]},
      {"text": "JUMPED", "accuracy": 10, "stress": 10, "total": 10, "phones": "JH AH0 M P T", "phones-accuracy": [2.0, 2.0, 2.0, 2.0, 2.0]},
      {"text": "OVER", "accuracy": 10, "stress": 10, "total": 10, "phones": "OW0 V ER0", "phones-accuracy": [2.0, 2.0, 2.0]},
      {"text": "THE", "accuracy": 10, "stress": 10, "total": 10, "phones": "DH AH0", "phones-accuracy": [2.0, 2.0]},
      {"text": "LAZY", "accuracy": 10, "stress": 10, "total": 10, "phones": "L EY0 Z IY0", "phones-accuracy": [2.0, 2.0, 2.0, 2.0]},
      {"text": "DOG", "accuracy": 5, "stress": 10, "total": 5, "phones": "D AO0 G", "phones-accuracy": [2.0, 0.2, 2.0]}
    ]
  },
  "000030033": {
    "text": "IT IS A CAT", "accuracy": 7, "completeness": 10.0, "fluency": 8, "prosodic": 8, "total": 7,
    "words": [
      {"text": "IT", "accuracy": 10, "stress": 10, "total": 10, "phones": "IH0 T", "phones-accuracy": [2.0, 2.0]},
      {"text": "IS", "accuracy": 10, "stress": 10, "total": 10, "phones": "IH0 Z", "phones-accuracy": [2.0, 2.0]},
      {"text": "A", "accuracy": 10, "stress": 10, "total": 10, "phones": "AH0", "phones-accuracy": [2.0]},
      {"text": "CAT", "accuracy": 7, "stress": 10, "total": 7, "phones": "K AE0 T", "phones-accuracy": [2.0, 2.0, 1.0]}
    ]
  }
}
```

`fixtures/mini_speechocean/scores-detail.json`:

```json
{
  "000010011": {
    "text": "WE CALL IT BEAR", "accuracy": [7.0, 9.0, 8.0, 8.0, 9.0],
    "words": [
      {"text": "WE", "accuracy": [10.0, 10.0, 10.0, 10.0, 10.0], "ref-phones": "W IY0", "phones": ["W IY0", "W IY0", "W IY0", "W IY0", "W IY0"]},
      {"text": "CALL", "accuracy": [10.0, 10.0, 9.0, 10.0, 10.0], "ref-phones": "K AO0 L", "phones": ["K AO0 L", "K AO0 L", "K AO0 L", "K AO0 L", "K AO0 L"]},
      {"text": "IT", "accuracy": [10.0, 10.0, 10.0, 10.0, 10.0], "ref-phones": "IH0 T", "phones": ["IH0 T", "IH0 T", "IH0 T", "IH0 T", "IH0 T"]},
      {"text": "BEAR", "accuracy": [6.0, 5.0, 6.0, 7.0, 6.0], "ref-phones": "B EH0 R", "phones": ["B EH0 R", "B EH0 R", "B EH0 R", "B EH0 R", "B EH0 R"]}
    ]
  },
  "000020022": {
    "text": "THE QUICK BROWN FOX JUMPED OVER THE LAZY DOG", "accuracy": [9.0, 9.0, 8.0, 9.0, 10.0],
    "words": [
      {"text": "THE", "accuracy": [10.0, 10.0, 10.0, 10.0, 10.0], "ref-phones": "DH AH0", "phones": ["DH AH0", "DH AH0", "DH AH0", "DH AH0", "DH AH0"]},
      {"text": "QUICK", "accuracy": [10.0, 10.0, 10.0, 10.0, 10.0], "ref-phones": "K W IH0 K", "phones": ["K W IH0 K", "K W IH0 K", "K W IH0 K", "K W IH0 K", "K W IH0 K"]},
      {"text": "BROWN", "accuracy": [10.0, 10.0, 10.0, 10.0, 10.0], "ref-phones": "B R AW0 N", "phones": ["B R AW0 N", "B R AW0 N", "B R AW0 N", "B R AW0 N", "B R AW0 N"]},
      {"text": "FOX", "accuracy": [10.0, 10.0, 10.0, 10.0, 10.0], "ref-phones": "F AA0 K S", "phones": ["F AA0 K S", "F AA0 K S", "F AA0 K S", "F AA0 K S", "F AA0 K S"]},
      {"text": "JUMPED", "accuracy": [10.0, 10.0, 10.0, 10.0, 10.0], "ref-phones": "JH AH0 M P T", "phones": ["JH AH0 M P T", "JH AH0 M P T", "JH AH0 M P T", "JH AH0 M P T", "JH AH0 M P T"]},
      {"text": "OVER", "accuracy": [10.0, 10.0, 10.0, 10.0, 10.0], "ref-phones": "OW0 V ER0", "phones": ["OW0 V ER0", "OW0 V ER0", "OW0 V ER0", "OW0 V ER0", "OW0 V ER0"]},
      {"text": "THE", "accuracy": [10.0, 10.0, 10.0, 10.0, 10.0], "ref-phones": "DH AH0", "phones": ["DH AH0", "DH AH0", "DH AH0", "DH AH0", "DH AH0"]},
      {"text": "LAZY", "accuracy": [10.0, 10.0, 10.0, 10.0, 10.0], "ref-phones": "L EY0 Z IY0", "phones": ["L EY0 Z IY0", "L EY0 Z IY0", "L EY0 Z IY0", "L EY0 Z IY0", "L EY0 Z IY0"]},
      {"text": "DOG", "accuracy": [5.0, 4.0, 5.0, 6.0, 9.0], "ref-phones": "D AO0 G", "phones": ["D AO0 G", "D AO0 G", "D AO0 G", "D AO0 G", "D AO0 G"]}
    ]
  },
  "000030033": {
    "text": "IT IS A CAT", "accuracy": [7.0, 7.0, 6.0, 8.0, 7.0],
    "words": [
      {"text": "IT", "accuracy": [10.0, 10.0, 10.0, 10.0, 10.0], "ref-phones": "IH0 T", "phones": ["IH0 T", "IH0 T", "IH0 T", "IH0 T", "IH0 T"]},
      {"text": "IS", "accuracy": [10.0, 10.0, 10.0, 10.0, 10.0], "ref-phones": "IH0 Z", "phones": ["IH0 Z", "IH0 Z", "IH0 Z", "IH0 Z", "IH0 Z"]},
      {"text": "A", "accuracy": [10.0, 10.0, 10.0, 10.0, 10.0], "ref-phones": "AH0", "phones": ["AH0", "AH0", "AH0", "AH0", "AH0"]},
      {"text": "CAT", "accuracy": [7.0, 6.0, 7.0, 8.0, 7.0], "ref-phones": "K AE0 T", "phones": ["K AE0 T", "K AE0 T", "K AE0 T", "K AE0 T", "K AE0 T"]}
    ]
  }
}
```

- [ ] **Step 2: Write the failing tests**

`backend/tests/benchmark/test_dataset.py`:

```python
import os
import tempfile
import unittest

from tests.benchmark import dataset as D
from tests.benchmark import testutil as U


class TestParse(unittest.TestCase):
    def setUp(self):
        self.root = U.MINI_DATASET

    def test_dev_half(self):
        dev = D.load_half(self.root, "dev")
        self.assertEqual([c.utt_id for c in dev], ["000010011", "000020022"])
        child, adult = dev
        self.assertEqual((child.speaker, child.age, child.is_child), ("0001", 6, True))
        self.assertFalse(adult.is_child)
        self.assertEqual(child.text, "WE CALL IT BEAR")
        self.assertTrue(os.path.isabs(child.wav_path))
        self.assertTrue(child.wav_path.endswith(os.path.join("SPEAKER0001", "000010011.WAV")))
        bear = child.words[3]
        self.assertEqual((bear.text, bear.accuracy, bear.phones), ("BEAR", 6.0, ["B", "EH0", "R"]))
        self.assertEqual(bear.phone_accuracy, [2.0, 1.6, 0.4])
        self.assertEqual(child.sentence_accuracy, 8.0)

    def test_test_half(self):
        self.assertEqual([c.utt_id for c in D.load_half(self.root, "test")], ["000030033"])

    def test_unknown_half(self):
        with self.assertRaises(ValueError):
            D.load_half(self.root, "train")

    def test_phones_may_be_a_list(self):
        self.assertEqual(D._phones(["W", "IY0"]), ["W", "IY0"])
        self.assertEqual(D._phones("W IY0"), ["W", "IY0"])


class TestRootAndChecks(unittest.TestCase):
    def test_find_nested_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = U.make_temp_dataset(tmp)
            self.assertEqual(D.find_dataset_root(tmp), root)

    def test_missing_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                D.find_dataset_root(tmp)

    def test_speaker_overlap_is_fatal(self):
        a = U.synthetic_clip("1", "0001", 6, [("A", 10, "AH0", [2])])
        b = U.synthetic_clip("2", "0001", 6, [("A", 10, "AH0", [2])], half="test")
        with self.assertRaises(ValueError):
            D.check_speaker_disjoint([a], [b])

    def test_check_on_complete_dataset(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = D.check(U.make_temp_dataset(tmp))
        self.assertEqual(report["problems"], [])
        self.assertEqual((report["dev_clips"], report["test_clips"]), (2, 1))
        self.assertEqual(report["dev_children"], 1)

    def test_check_reports_missing_audio(self):
        report = D.check(U.MINI_DATASET)  # fixture ships no audio
        self.assertTrue(any("missing audio" in p for p in report["problems"]))


class TestSubsets(unittest.TestCase):
    def setUp(self):
        self.clips = [U.synthetic_clip(f"c{i:02d}", f"s{i}", 8 if i < 10 else 30, [("A", 10, "AH0", [2])]) for i in range(20)]

    def test_stratified(self):
        picked = D.make_subset(self.clips, 10, seed=1)
        by_id = {c.utt_id: c for c in self.clips}
        self.assertEqual(len(picked), 10)
        self.assertEqual(sum(by_id[u].is_child for u in picked), 5)

    def test_seeded(self):
        self.assertEqual(D.make_subset(self.clips, 7, seed=3), D.make_subset(self.clips, 7, seed=3))

    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            D.write_subset("smoke", ["b", "a"], directory=tmp)
            self.assertEqual(D.read_subset("smoke", directory=tmp), ["a", "b"])

    def test_load_clips_with_subset(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = U.make_temp_dataset(tmp)
            D.write_subset("one", ["000020022"], directory=tmp)
            clips = D.load_clips("dev", "one", root=root, subsets_dir=tmp)
            self.assertEqual([c.utt_id for c in clips], ["000020022"])
            D.write_subset("bad", ["999"], directory=tmp)
            with self.assertRaises(ValueError):
                D.load_clips("dev", "bad", root=root, subsets_dir=tmp)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.benchmark.test_dataset -v`
Expected: ERROR, `ImportError: cannot import name 'dataset'`.

- [ ] **Step 4: Write `dataset.py`**

`backend/tests/benchmark/dataset.py`:

```python
"""speechocean762: download, parse, check, and fixed clip subsets.

The dataset's own ``train`` half is this benchmark's dev half. Its ``test`` half is the
sealed test half (run.py enforces the unlock rule).

    python -m tests.benchmark.dataset download      # ~520 MB from OpenSLR
    python -m tests.benchmark.dataset check
    python -m tests.benchmark.dataset make-subsets
"""

from __future__ import annotations

import argparse
import json
import os
import random
import tarfile
import urllib.request
from dataclasses import dataclass, field

from . import common

MIRRORS = (
    "https://openslr.trmal.net/resources/101/speechocean762.tar.gz",
    "https://openslr.elda.org/resources/101/speechocean762.tar.gz",
    "https://openslr.magicdatatech.com/resources/101/speechocean762.tar.gz",
)
HALF_DIRS = {"dev": "train", "test": "test"}
CHILD_MAX_AGE = 17  # a child is a speaker under 18
SMOKE_SUBSET = ("smoke_dev", 250, 1234)
SPEED_SUBSET = ("speed_dev", 200, 5678)


@dataclass
class Word:
    text: str
    accuracy: float
    phones: list[str]
    phone_accuracy: list[float]


@dataclass
class Clip:
    utt_id: str
    speaker: str
    age: int
    half: str
    text: str
    wav_path: str
    sentence_accuracy: float
    words: list[Word] = field(default_factory=list)

    @property
    def is_child(self) -> bool:
        return self.age <= CHILD_MAX_AGE


def find_dataset_root(base: str | None = None) -> str:
    base = base or common.data_dir()
    for candidate in (base, os.path.join(base, "speechocean762")):
        if all(os.path.isdir(os.path.join(candidate, d)) for d in HALF_DIRS.values()):
            return candidate
    raise FileNotFoundError(
        f"speechocean762 not found under {base}. Run: python -m tests.benchmark.dataset download"
    )


def find_resource(root: str, name: str) -> str:
    for path in (os.path.join(root, name), os.path.join(root, "resource", name)):
        if os.path.isfile(path):
            return path
    raise FileNotFoundError(f"{name} not found in {root} or {root}/resource")


def _read_kaldi_map(path: str) -> dict[str, str]:
    out: dict[str, str] = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            parts = line.strip().split(None, 1)
            if parts:
                out[parts[0]] = parts[1].strip() if len(parts) > 1 else ""
    return out


def load_scores(root: str) -> dict:
    with open(find_resource(root, "scores.json"), encoding="utf-8") as fh:
        return json.load(fh)


def _phones(value) -> list[str]:
    return value.split() if isinstance(value, str) else list(value)


def load_half(root: str, half: str, scores: dict | None = None) -> list[Clip]:
    if half not in HALF_DIRS:
        raise ValueError(f"half must be one of {sorted(HALF_DIRS)}, got {half!r}")
    directory = os.path.join(root, HALF_DIRS[half])
    wav = _read_kaldi_map(os.path.join(directory, "wav.scp"))
    utt2spk = _read_kaldi_map(os.path.join(directory, "utt2spk"))
    spk2age = _read_kaldi_map(os.path.join(directory, "spk2age"))
    scores = scores if scores is not None else load_scores(root)
    clips = []
    for utt_id in sorted(wav):
        entry = scores[utt_id]
        speaker = utt2spk[utt_id]
        path = wav[utt_id]
        if not os.path.isabs(path):
            path = os.path.normpath(os.path.join(root, path))
        words = [
            Word(
                text=w["text"],
                accuracy=float(w["accuracy"]),
                phones=_phones(w["phones"]),
                phone_accuracy=[float(a) for a in w["phones-accuracy"]],
            )
            for w in entry["words"]
        ]
        clips.append(Clip(
            utt_id=utt_id, speaker=speaker, age=int(spk2age[speaker]), half=half,
            text=entry["text"], wav_path=path, sentence_accuracy=float(entry["accuracy"]),
            words=words,
        ))
    return clips


def check_speaker_disjoint(dev, test) -> None:
    overlap = sorted({c.speaker for c in dev} & {c.speaker for c in test})
    if overlap:
        more = "..." if len(overlap) > 10 else ""
        raise ValueError(f"speakers appear in both halves: {overlap[:10]}{more}")


def subset_path(name: str, directory: str | None = None) -> str:
    return os.path.join(directory or common.SUBSETS_DIR, f"{name}.txt")


def read_subset(name: str, directory: str | None = None) -> list[str]:
    with open(subset_path(name, directory), encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip()]


def write_subset(name: str, utt_ids, directory: str | None = None) -> str:
    path = subset_path(name, directory)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(sorted(utt_ids)) + "\n")
    return path


def make_subset(clips, n: int, seed: int) -> list[str]:
    """n clip ids, stratified so children and adults keep their proportions."""
    if not clips:
        return []
    rng = random.Random(seed)
    children = sorted(c.utt_id for c in clips if c.is_child)
    adults = sorted(c.utt_id for c in clips if not c.is_child)
    n = min(n, len(clips))
    n_child = min(round(n * len(children) / len(clips)), len(children))
    picked = rng.sample(children, n_child) + rng.sample(adults, min(n - n_child, len(adults)))
    return sorted(picked)


def load_clips(half: str, subset: str | None = None, root: str | None = None,
               subsets_dir: str | None = None) -> list[Clip]:
    clips = load_half(root or find_dataset_root(), half)
    if subset:
        wanted = set(read_subset(subset, subsets_dir))
        clips = [c for c in clips if c.utt_id in wanted]
        missing = wanted - {c.utt_id for c in clips}
        if missing:
            raise ValueError(f"subset {subset!r} names {len(missing)} clip(s) not in the {half} half")
    return clips


def check(root: str) -> dict:
    scores = load_scores(root)
    dev, test = load_half(root, "dev", scores), load_half(root, "test", scores)
    check_speaker_disjoint(dev, test)
    problems = []
    for clip in dev + test:
        if not os.path.isfile(clip.wav_path):
            problems.append(f"{clip.utt_id}: missing audio {clip.wav_path}")
        if len(clip.text.split()) != len(clip.words):
            problems.append(f"{clip.utt_id}: {len(clip.text.split())} text tokens but {len(clip.words)} scored words")
        for w in clip.words:
            if len(w.phones) != len(w.phone_accuracy):
                problems.append(f"{clip.utt_id}/{w.text}: {len(w.phones)} phones but {len(w.phone_accuracy)} scores")
    return {
        "dev_clips": len(dev),
        "test_clips": len(test),
        "dev_speakers": len({c.speaker for c in dev}),
        "test_speakers": len({c.speaker for c in test}),
        "dev_children": sum(c.is_child for c in dev),
        "test_children": sum(c.is_child for c in test),
        "problems": problems,
    }


def download(dest: str | None = None, mirrors=MIRRORS) -> str:
    dest = dest or common.data_dir()
    os.makedirs(dest, exist_ok=True)
    archive = os.path.join(dest, "speechocean762.tar.gz")
    if not os.path.isfile(archive):
        last_error = None
        for url in mirrors:
            tmp = archive + ".part"
            try:
                print(f"Downloading {url} (~520 MB)...")
                with urllib.request.urlopen(url, timeout=60) as resp, open(tmp, "wb") as out:
                    total = int(resp.headers.get("Content-Length") or 0)
                    done = 0
                    while True:
                        chunk = resp.read(1 << 20)
                        if not chunk:
                            break
                        out.write(chunk)
                        done += len(chunk)
                        if total:
                            print(f"\r  {done * 100 // total}%", end="", flush=True)
                print()
                os.replace(tmp, archive)
                break
            except OSError as exc:
                print(f"  failed: {exc}")
                last_error = exc
        else:
            raise RuntimeError(f"all mirrors failed: {last_error}")
    try:
        return find_dataset_root(dest)
    except FileNotFoundError:
        pass
    print("Extracting...")
    with tarfile.open(archive, "r:gz") as tar:
        tar.extractall(dest, filter="data")
    return find_dataset_root(dest)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m tests.benchmark.dataset")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("download")
    sub.add_parser("check")
    sub.add_parser("make-subsets")
    args = parser.parse_args(argv)

    if args.cmd == "download":
        print(f"Dataset ready at {download()}")
        return 0
    root = find_dataset_root()
    if args.cmd == "check":
        report = check(root)
        for key, value in report.items():
            if key != "problems":
                print(f"{key:16s} {value}")
        for line in report["problems"][:50]:
            print("PROBLEM", line)
        print(f"{len(report['problems'])} problem(s)")
        return 1 if report["problems"] else 0
    dev = load_half(root, "dev")
    for name, n, seed in (SMOKE_SUBSET, SPEED_SUBSET):
        print(f"wrote {write_subset(name, make_subset(dev, n, seed))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.benchmark.test_dataset -v`
Expected: `OK` (13 tests).

- [ ] **Step 6: Commit**

```bash
git add tests/benchmark/dataset.py tests/benchmark/test_dataset.py tests/benchmark/fixtures/mini_speechocean
git commit -m "Add speechocean762 parser, checks and fixed subsets" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Shared sentence cleanup (production)

**Files:**
- Modify: `backend/core/grapheme_to_phoneme.py` (add a function just above `grapheme_to_phoneme`)
- Modify: `backend/core/phoneme_assistant.py:10` and `:273-279`
- Test: `backend/tests/test_clean_sentence.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/test_clean_sentence.py`:

```python
"""clean_sentence is the cleanup PhonemeAssistant.process_audio applies before G2P.

Run from backend/:  PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.test_clean_sentence -v
"""

import os
import sys
import unittest

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from core.grapheme_to_phoneme import clean_sentence  # noqa: E402


class TestCleanSentence(unittest.TestCase):
    def test_matches_historical_cleanup(self):
        self.assertEqual(clean_sentence("  It's a CAT, isn't it?! "), "its a cat isnt it")

    def test_periods(self):
        self.assertEqual(clean_sentence("WE CALL IT BEAR."), "we call it bear")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it to verify it fails**

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.test_clean_sentence -v`
Expected: ERROR, `ImportError: cannot import name 'clean_sentence'`.

- [ ] **Step 3: Add `clean_sentence` to `core/grapheme_to_phoneme.py`**, directly above `def grapheme_to_phoneme(`:

```python
def clean_sentence(sentence: str) -> str:
    """The cleanup PhonemeAssistant.process_audio applies to a sentence before G2P.

    Shared with the accuracy benchmark (backend/tests/benchmark) so both score the
    exact same ground truth.
    """
    return (
        sentence.strip().lower()
        .replace(".", "")
        .replace(",", "")
        .replace("?", "")
        .replace("!", "")
        .replace("'", "")
    )
```

- [ ] **Step 4: Use it in `core/phoneme_assistant.py`**

Change line 10 from `from core.grapheme_to_phoneme import grapheme_to_phoneme` to:

```python
from core.grapheme_to_phoneme import clean_sentence, grapheme_to_phoneme
```

Replace the block at lines 273-279:

```python
        # clean the sentence
        attempted_sentence = (
            (attempted_sentence.strip().lower().replace(".", "").replace(",", ""))
            .replace("?", "")
            .replace("!", "")
            .replace("'", "")
        )
```

with:

```python
        # clean the sentence
        attempted_sentence = clean_sentence(attempted_sentence)
```

- [ ] **Step 5: Run the new test and the G2P tests**

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.test_clean_sentence tests.test_grapheme_to_phoneme -v`
Expected: `OK`.

- [ ] **Step 6: Commit**

```bash
git add core/grapheme_to_phoneme.py core/phoneme_assistant.py tests/test_clean_sentence.py
git commit -m "Extract sentence cleanup into clean_sentence()" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: Quality gates move into `core/request_audio.py` (production)

**Files:**
- Create: `backend/core/request_audio.py`
- Modify: `backend/routers/handlers/audio_processing_handler.py:13-19` (imports) and `:150-239` (gate and preprocess block)
- Test: `backend/tests/test_request_audio.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/test_request_audio.py`:

```python
"""Quality gates and the single preprocessing pass (core/request_audio.py).

Run from backend/:  PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.test_request_audio -v
"""

import contextlib
import io
import os
import sys
import unittest
from unittest import mock

import numpy as np
import soundfile as sf

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from core import request_audio as R  # noqa: E402

SAMPLE_WAV = os.path.join(BACKEND_ROOT, "tests", "system", "test_case_02", "audio.wav")


def _quiet():
    return contextlib.redirect_stdout(io.StringIO())


class TestGates(unittest.TestCase):
    def setUp(self):
        self._saved = os.environ.pop("WWAI_SOFT_QUALITY_GATES", None)
        self.speech, self.sr = sf.read(SAMPLE_WAV, dtype="float32")

    def tearDown(self):
        os.environ.pop("WWAI_SOFT_QUALITY_GATES", None)
        if self._saved is not None:
            os.environ["WWAI_SOFT_QUALITY_GATES"] = self._saved

    def test_real_speech_passes_hard_gates(self):
        out = {}
        with _quiet():
            info = R.gate_audio(self.speech, self.sr, quality_out=out)
        self.assertIn("snr_db", info)
        self.assertIs(out["quality_info"], info)

    def test_hard_gates_reject_low_snr(self):
        # Mocked report: the legacy analyzer measures 60 dB SNR and 0% silence on
        # all-zero audio, so real silence does not reach the hard SNR/silence gates.
        report = {"quality_level": "poor", "quality_score": 10.0, "snr_db": 2.0,
                  "clipping_percentage": 0.0, "silence_percentage": 0.0,
                  "issues": [], "recommendations": []}
        with mock.patch.object(R.AudioQualityAnalyzer, "analyze_audio_quality", return_value=report), \
             _quiet(), self.assertRaises(R.AudioRejected) as ctx:
            R.gate_audio(self.speech, self.sr)
        self.assertIn("SNR", str(ctx.exception))

    def test_digital_silence_rejected_by_soft_gates(self):
        os.environ["WWAI_SOFT_QUALITY_GATES"] = "1"
        with _quiet(), self.assertRaises(R.AudioRejected):
            R.gate_audio(np.zeros(32000, dtype=np.float32), 16000)

    def test_rejection_is_a_value_error(self):
        self.assertTrue(issubclass(R.AudioRejected, ValueError))

    def test_gate_and_preprocess_normalizes(self):
        with _quiet():
            out = R.gate_and_preprocess(self.speech, self.sr)
        self.assertEqual(len(out), len(self.speech))
        self.assertAlmostEqual(float(np.max(np.abs(out))), 1.0, places=5)

    def test_apply_gates_false_skips_the_gates(self):
        with mock.patch.object(R, "gate_audio") as gate, _quiet():
            R.gate_and_preprocess(self.speech, self.sr, apply_gates=False)
        gate.assert_not_called()


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it to verify it fails**

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.test_request_audio -v`
Expected: ERROR, `ImportError: cannot import name 'request_audio'`.

- [ ] **Step 3: Write `core/request_audio.py`** (the gate code is moved verbatim from the handler, with `HTTPException` replaced by `AudioRejected`)

`backend/core/request_audio.py`:

```python
"""Quality gates and the single preprocessing pass for an uploaded recording.

Lifted out of routers/handlers/audio_processing_handler.py so the request path and the
accuracy benchmark (backend/tests/benchmark) run exactly the same gates. Raises
AudioRejected instead of an HTTP error, and the handler turns that into a 400.
"""

import time

import numpy as np

from .audio_preprocessing import preprocess_audio
from .audio_quality_analyzer import (
    AudioQualityAnalyzer,
    assess_processability,
    build_quality_warning,
    soft_quality_gates_enabled,
)


class AudioRejected(ValueError):
    """The recording cannot be analyzed. ``str(exc)`` is the message shown to the child."""


def gate_audio(audio_array: np.ndarray, sample_rate: int, quality_out: dict | None = None) -> dict:
    """Analyze recording quality and apply the soft or hard gates. Returns the quality report."""
    print("🔍 Analyzing audio quality...")
    quality_start = time.time()
    analyzer = AudioQualityAnalyzer(sr=sample_rate)
    quality_info = analyzer.analyze_audio_quality(audio_array)
    print(f"⏱️  Quality analysis took {time.time() - quality_start:.3f}s")

    # Log quality metrics
    print(f"📊 Audio Quality Report:")
    print(f"   - Quality Level: {quality_info['quality_level'].upper()}")
    print(f"   - Quality Score: {quality_info['quality_score']:.1f}/100")
    print(f"   - SNR: {quality_info['snr_db']:.1f} dB")
    print(f"   - Clipping: {quality_info['clipping_percentage']:.2f}%")
    print(f"   - Silence: {quality_info['silence_percentage']:.1f}%")
    print(f"   - Metrics mode: {quality_info.get('metrics_mode', 'legacy')}")

    if quality_out is not None:
        quality_out['quality_info'] = quality_info

    if soft_quality_gates_enabled():
        # SOFT GATES (WWAI_SOFT_QUALITY_GATES=1)
        #
        # Reject only audio we genuinely cannot process: nothing received, or
        # true digital silence. A noisy, clipped or pause-heavy recording is
        # still a child's honest attempt -- analyze it and pass a gentle hint
        # back to the frontend instead of refusing it.
        is_processable, reason = assess_processability(audio_array)
        if not is_processable:
            raise AudioRejected(reason)

        quality_warning = build_quality_warning(quality_info)
        if quality_warning is not None:
            print("⚠️  Soft quality gate: proceeding with a quality warning attached")
            for hint in quality_warning['hints']:
                print(f"   - {hint}")
            if quality_out is not None:
                quality_out['quality_warning'] = quality_warning
    else:
        # HARD GATES (default). Unchanged behavior.
        if quality_info['snr_db'] < 5.0:
            raise AudioRejected(
                f"Audio quality too low (SNR: {quality_info['snr_db']:.1f} dB). "
                "Please record in a quieter environment or use a better microphone."
            )

        if quality_info['clipping_percentage'] > 10.0:
            raise AudioRejected(
                f"Audio is severely clipped ({quality_info['clipping_percentage']:.1f}% of samples). "
                "Please reduce microphone gain or speak further from the microphone."
            )

        if quality_info['silence_percentage'] > 85.0:
            raise AudioRejected(
                f"Audio is mostly silence ({quality_info['silence_percentage']:.1f}%). "
                "Please ensure you are speaking into the microphone."
            )

    # Warn about quality issues but continue processing
    if quality_info['issues']:
        print(f"⚠️  Quality issues detected:")
        for issue in quality_info['issues']:
            print(f"   - {issue}")

    if quality_info['recommendations']:
        print(f"💡 Recommendations:")
        for rec in quality_info['recommendations']:
            print(f"   - {rec}")

    return quality_info


def gate_and_preprocess(audio_array: np.ndarray, sample_rate: int, audio_duration: float | None = None,
                        quality_out: dict | None = None, apply_gates: bool = True) -> np.ndarray:
    """Gate the recording, then run THE preprocessing pass for this request.

    The caller must ``mark_preprocessed()`` the result in its own context
    (asyncio.to_thread runs on a copied context, so a mark set in here is lost).
    ``apply_gates=False`` is for the benchmark's cache builder, which records model
    outputs for every clip and applies the gates later at scoring time.
    """
    if apply_gates:
        gate_audio(audio_array, sample_rate, quality_out)
    if audio_duration is None:
        audio_duration = len(audio_array) / sample_rate
    print("🔊 Starting audio preprocessing...")
    return preprocess_audio(
        audio_array, sr=sample_rate, audio_length_seconds=audio_duration,
        use_adaptive=True, already_preprocessed=False,
    )
```

- [ ] **Step 4: Make the handler call it**

In `backend/routers/handlers/audio_processing_handler.py`, replace everything from the line `    # QUALITY VALIDATION: Analyze audio quality before preprocessing` (line 150) through the line `    mark_preprocessed(audio_array)` (line 239) with:

```python
    # QUALITY GATES + THE preprocessing pass (core/request_audio.py), off the event loop.
    try:
        audio_array = await asyncio.to_thread(
            gate_and_preprocess, audio_array, sample_rate, audio_duration, quality_out
        )
    except AudioRejected as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    # This is THE preprocessing pass for this request. Record it here (not inside
    # the worker thread - asyncio.to_thread runs on a copied context, so a mark
    # set in there would be discarded) so later stages can skip redundant noise
    # reduction / normalization when WWAI_SINGLE_PREPROCESS is enabled.
    from core.audio_preprocessing import mark_preprocessed
    mark_preprocessed(audio_array)
```

Then fix the imports at the top of the file. Run
`grep -n "AudioQualityAnalyzer\|assess_processability\|build_quality_warning\|soft_quality_gates_enabled\|preprocess_audio(" routers/handlers/audio_processing_handler.py`.
`soft_quality_gates_enabled` is still used further down (around line 348), so keep it. Remove every name the grep no longer finds outside the import lines. Expected result for lines 13-19:

```python
from core.audio_quality_analyzer import soft_quality_gates_enabled
from core.request_audio import AudioRejected, gate_and_preprocess
```

(`from core.audio_preprocessing import preprocess_audio` goes away if grep shows no other use.)

- [ ] **Step 5: Run the new test and the existing gate tests**

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.test_request_audio tests.test_soft_quality_gates tests.test_single_preprocess tests.test_phase1_audio_quality -v`
Expected: `OK`. `test_soft_quality_gates` drives `load_and_preprocess_audio_bytes` end to end, so it proves the handler still returns 400s with the same messages.

- [ ] **Step 6: Commit**

```bash
git add core/request_audio.py routers/handlers/audio_processing_handler.py tests/test_request_audio.py
git commit -m "Move quality gates into core/request_audio.py" -m "The benchmark needs to run the same gates as the request path. The handler now converts AudioRejected into the same 400 responses as before." -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 7: Module-level `HIGH_PER_THRESHOLD` (production)

**Files:**
- Modify: `backend/core/phoneme_feedback_formatter.py` (add a constant after the imports and remove the local one at line 335)
- Test: `backend/tests/test_feedback_threshold.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/test_feedback_threshold.py`:

```python
"""The focus-word PER cutoff is a module constant the benchmark can read.

Run from backend/:  PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.test_feedback_threshold -v
"""

import os
import sys
import unittest
from unittest import mock

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from core import phoneme_feedback_formatter as fmt  # noqa: E402


class TestThreshold(unittest.TestCase):
    DATA = [{"ground_truth_word": "cat", "per": 0.5, "total_errors": 1}]
    ERRORS = {"k": [{"word": "cat"}]}

    def test_value(self):
        self.assertEqual(fmt.HIGH_PER_THRESHOLD, 0.4)

    def test_focus_reads_the_module_constant(self):
        self.assertEqual(fmt._focus_from_high_per_words(self.DATA, self.ERRORS), "k")
        with mock.patch.object(fmt, "HIGH_PER_THRESHOLD", 0.6):
            self.assertIsNone(fmt._focus_from_high_per_words(self.DATA, self.ERRORS))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it to verify it fails**

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.test_feedback_threshold -v`
Expected: FAIL/ERROR, `AttributeError: module 'core.phoneme_feedback_formatter' has no attribute 'HIGH_PER_THRESHOLD'`.

- [ ] **Step 3: Hoist the constant**

Add after the imports at the top of `core/phoneme_feedback_formatter.py` (after `from typing import Optional`):

```python

#: Words at or above this PER count as clearly mispronounced when picking the focus
#: phoneme. Module level so the accuracy benchmark scores the same cutoff.
HIGH_PER_THRESHOLD = 0.4
```

Delete this line inside `_focus_from_high_per_words` (line 335), along with the blank line after it:

```python
    HIGH_PER_THRESHOLD = 0.4
```

- [ ] **Step 4: Run the test**

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.test_feedback_threshold -v`
Expected: `OK` (2 tests).

- [ ] **Step 5: Commit**

```bash
git add core/phoneme_feedback_formatter.py tests/test_feedback_threshold.py
git commit -m "Hoist HIGH_PER_THRESHOLD to module level" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 8: Separate logits from decoding in the ONNX extractor (production)

**Files:**
- Create: `backend/tests/benchmark/fixtures/onnx_golden_test_case_02.json` (recorded before the change)
- Modify: `backend/core/phoneme_extractor_onnx.py:12-35` (add `decode_logits`) and `:136-200` (`extract_logits` / `extract_phoneme`)
- Test: `backend/tests/test_onnx_logits_split.py`

- [ ] **Step 1: Record today's output as a golden file, BEFORE editing the extractor**

Run:

```bash
WWAI_PHONEME_NORMALIZATION= PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -c "
import json, contextlib, io, soundfile as sf
from core.phoneme_extractor_onnx import PhonemeExtractorONNX
a, _ = sf.read('tests/system/test_case_02/audio.wav', dtype='float32')
with contextlib.redirect_stdout(io.StringIO()):
    out = PhonemeExtractorONNX().extract_phoneme(a, 16000)
with open('tests/benchmark/fixtures/onnx_golden_test_case_02.json', 'w', encoding='utf-8') as fh:
    json.dump(out, fh, ensure_ascii=False)
print(out)
"
```

Expected: a printed list of phoneme lists (roughly nine word groups for "the quick brown fox jumped over the lazy dog"), and the JSON file written.

- [ ] **Step 2: Write the failing test**

`backend/tests/test_onnx_logits_split.py`:

```python
"""extract_phoneme == decode_logits(extract_logits(...)), with output unchanged by the refactor.

Needs the ONNX model in the local HuggingFace cache; skips otherwise.
Run from backend/:  PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.test_onnx_logits_split -v
"""

import contextlib
import io
import json
import os
import sys
import unittest

import soundfile as sf

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

SAMPLE_WAV = os.path.join(BACKEND_ROOT, "tests", "system", "test_case_02", "audio.wav")
GOLDEN = os.path.join(BACKEND_ROOT, "tests", "benchmark", "fixtures", "onnx_golden_test_case_02.json")


class TestLogitsSplit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._saved = os.environ.pop("WWAI_PHONEME_NORMALIZATION", None)
        try:
            from core.phoneme_extractor_onnx import PhonemeExtractorONNX, decode_logits

            with contextlib.redirect_stdout(io.StringIO()):
                cls.extractor = PhonemeExtractorONNX()
        except Exception as exc:  # noqa: BLE001
            raise unittest.SkipTest(f"ONNX model unavailable: {exc}")
        cls.decode_logits = staticmethod(decode_logits)
        cls.audio, _ = sf.read(SAMPLE_WAV, dtype="float32")

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "_saved", None) is not None:
            os.environ["WWAI_PHONEME_NORMALIZATION"] = cls._saved

    def test_logits_shape(self):
        logits = self.extractor.extract_logits(self.audio, 16000)
        self.assertEqual(logits.ndim, 3)
        self.assertEqual(logits.shape[0], 1)
        self.assertEqual(logits.shape[2], len(self.extractor.processor.tokenizer.get_vocab()))

    def test_extract_phoneme_is_decode_of_logits(self):
        logits = self.extractor.extract_logits(self.audio, 16000)
        decoded = self.decode_logits(logits, self.extractor.processor, self.extractor.model_output_processing)
        self.assertEqual(decoded, self.extractor.extract_phoneme(self.audio, 16000))

    def test_output_unchanged_by_refactor(self):
        with open(GOLDEN, encoding="utf-8") as fh:
            golden = json.load(fh)
        self.assertEqual(self.extractor.extract_phoneme(self.audio, 16000), golden)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run it to verify it fails**

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.test_onnx_logits_split -v`
Expected: SKIP or ERROR mentioning `cannot import name 'decode_logits'` (setUpClass turns the ImportError into a skip, so look for `skipped 'ONNX model unavailable: cannot import name 'decode_logits'...'`).

- [ ] **Step 4: Add `decode_logits` to `core/phoneme_extractor_onnx.py`**, directly after `default_model_output_processing` (after line 34):

```python


def decode_logits(logits, processor, model_output_processing=default_model_output_processing):
    """Greedy CTC decode. Argmax per frame, collapse with the processor, group into words.

    ``PhonemeExtractorONNX.extract_phoneme`` is exactly this applied to
    ``extract_logits``. The accuracy benchmark caches logits and calls this to replay.
    """
    predicted_ids = np.argmax(logits, axis=-1)
    transcription = processor.batch_decode(predicted_ids)
    return model_output_processing(transcription)
```

- [ ] **Step 5: Replace `extract_phoneme` (lines 136-200) with `extract_logits` plus a thin `extract_phoneme`**

```python
    def extract_logits(self, audio, sampling_rate=16000, use_optimized_preprocessing=True):
        """
        Validate and condition the audio, then run the acoustic model.

        Returns:
            Raw logits, shape (1, frames, vocab).

        Raises:
            ValueError: If audio is invalid
        """
        # Validate audio input
        if audio is None or len(audio) == 0:
            raise ValueError("❌ Audio is empty - cannot extract phonemes")

        audio_duration = len(audio) / sampling_rate

        if audio_duration < 0.3:
            raise ValueError(f"❌ Audio too short ({audio_duration:.2f}s) - need at least 0.3s")

        audio_rms = np.sqrt(np.mean(audio ** 2))
        if audio_rms < 0.001:
            raise ValueError(f"❌ Audio appears to be silent (RMS: {audio_rms:.6f})")

        if self._performance_logging:
            print(f"[INFO] Audio validation: duration={audio_duration:.2f}s, RMS={audio_rms:.4f}, samples={len(audio)}")

        # Optimize audio preprocessing if enabled
        if use_optimized_preprocessing:
            # Format conditioning ONLY (mono / sample-rate reconciliation /
            # silence trim / float32). Noise reduction and peak normalization
            # belong to core.audio_preprocessing.preprocess_audio and must not
            # be repeated here - normalize=False is explicit for that reason.
            # A sample-rate mismatch is now resampled rather than silently
            # relabelled as target_sr.
            audio, sampling_rate = self.audio_preprocessor.preprocess_audio(
                audio, sr=sampling_rate, normalize=False, trim_silence=True
            )

        # Tokenize the audio file
        processor_outputs = self.processor(audio, sampling_rate=sampling_rate, return_tensors="np")
        input_values = processor_outputs.input_values

        # Run ONNX inference
        onnx_inputs = {self.session.get_inputs()[0].name: input_values.astype(np.float32)}
        return self.session.run(None, onnx_inputs)[0]

    def extract_phoneme(self, audio, sampling_rate=16000, use_optimized_preprocessing=True):
        """
        Extract phonemes from audio using ONNX Runtime.

        Args:
            audio: Audio data as numpy array
            sampling_rate: Sample rate of the audio (default: 16000)
            use_optimized_preprocessing: Whether to use optimized audio preprocessing

        Returns:
            Processed phoneme transcription

        Raises:
            ValueError: If audio is invalid
        """
        start_time = time.time() if self._performance_logging else None

        logits = self.extract_logits(audio, sampling_rate, use_optimized_preprocessing)
        transcription = decode_logits(logits, self.processor, self.model_output_processing)

        if self._performance_logging and start_time:
            inference_time = time.time() - start_time
            print(f"ONNX phoneme extraction took {inference_time:.3f}s")

        return transcription
```

- [ ] **Step 6: Run the new test and the inventory test (it checks this file's source)**

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.test_onnx_logits_split tests.test_phoneme_inventory -v`
Expected: `OK` (3 tests in the new file run, not skipped).

- [ ] **Step 7: Commit**

```bash
git add core/phoneme_extractor_onnx.py tests/test_onnx_logits_split.py tests/benchmark/fixtures/onnx_golden_test_case_02.json
git commit -m "Separate ONNX logits from greedy decoding" -m "extract_phoneme is now decode_logits(extract_logits(...)) with identical output, which a golden test pins. The benchmark caches logits and replays decoding." -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 9: Pin the shared ONNX model revision (production)

**Files:**
- Modify: `backend/core/model_registry.py:97-108` (`PHONEME_IPA_ONNX` revision)
- Modify: `backend/core/phoneme_extractor_onnx.py:1-10` (import) and `:81-87` (loader)
- Test: `backend/tests/test_onnx_pin_wiring.py`

- [ ] **Step 1: Confirm which revision to pin**

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m core.model_registry --resolve`
Expected: a block for `PHONEME_IPA_ONNX` printing `revision="e3f5690ebe6cf47f514b34c6e27aec4a61e01569",`, which is the snapshot in the local HuggingFace cache (`~/.cache/huggingface/hub/models--Bobcat9--wav2vec2-timit-ipa-onnx/snapshots/`).
**If the printed SHA is different, stop and ask Bruce** which revision production runs before pinning anything.

- [ ] **Step 2: Write the failing test**

`backend/tests/test_onnx_pin_wiring.py`:

```python
"""PhonemeExtractorONNX loads the revision pinned in core/model_registry.py.

No network and no model: the loaders are mocked.
Run from backend/:  PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.test_onnx_pin_wiring -v
"""

import os
import sys
import unittest
from unittest import mock

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from core import phoneme_extractor_onnx as onnx_mod  # noqa: E402
from core.model_registry import get  # noqa: E402

CONFIG = {"model_cache_enabled": False, "warmup_runs": 0, "enable_performance_logging": False}
REPO = "Bobcat9/wav2vec2-timit-ipa-onnx"


class TestPinWiring(unittest.TestCase):
    def setUp(self):
        self._saved = {k: os.environ.pop(k, None) for k in ("WWAI_IGNORE_MODEL_PINS", "WWAI_PIN_PHONEME_IPA_ONNX")}

    def tearDown(self):
        for key, value in self._saved.items():
            os.environ.pop(key, None)
            if value is not None:
                os.environ[key] = value

    def _load(self):
        with mock.patch.object(onnx_mod, "Wav2Vec2Processor") as proc, \
             mock.patch("huggingface_hub.hf_hub_download", return_value="model.onnx") as hub, \
             mock.patch.object(onnx_mod.ort, "InferenceSession"):
            onnx_mod.PhonemeExtractorONNX(optimization_config=CONFIG)
        return proc, hub

    def test_revision_is_pinned(self):
        self.assertIsNotNone(get("PHONEME_IPA_ONNX").revision)

    def test_loader_passes_the_pin(self):
        pin = get("PHONEME_IPA_ONNX").revision
        proc, hub = self._load()
        proc.from_pretrained.assert_called_once_with(REPO, revision=pin)
        hub.assert_called_once_with(repo_id=REPO, filename="model.onnx", revision=pin)

    def test_global_escape_hatch(self):
        os.environ["WWAI_IGNORE_MODEL_PINS"] = "true"
        proc, hub = self._load()
        proc.from_pretrained.assert_called_once_with(REPO)
        hub.assert_called_once_with(repo_id=REPO, filename="model.onnx")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run it to verify it fails**

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.test_onnx_pin_wiring -v`
Expected: FAIL on `test_revision_is_pinned` and `test_loader_passes_the_pin`.

- [ ] **Step 4: Pin it in `core/model_registry.py`**

In the `PHONEME_IPA_ONNX` entry, replace

```python
        revision=UNPINNED,  # TODO(pin): run `python -m core.model_registry --resolve`
```

with

```python
        # Pinned 2026-10-05 to the snapshot the accuracy benchmark baseline was built on.
        revision="e3f5690ebe6cf47f514b34c6e27aec4a61e01569",
```

- [ ] **Step 5: Wire the pin into the ONNX loader**

In `core/phoneme_extractor_onnx.py`, add after `from .optimization_config import config`:

```python
from .model_registry import from_pretrained_kwargs, key_for_repo
```

Replace these lines in `__init__`:

```python
                # Load processor (for tokenization)
                self.processor = Wav2Vec2Processor.from_pretrained(model_name)
                
                # Load ONNX model
                from huggingface_hub import hf_hub_download
                onnx_path = hf_hub_download(repo_id=model_name, filename="model.onnx")
```

with:

```python
                # Pinned revision from core/model_registry.py ({} when unpinned or overridden)
                pin_key = key_for_repo(model_name)
                pin_kwargs = from_pretrained_kwargs(pin_key) if pin_key else {}

                # Load processor (for tokenization)
                self.processor = Wav2Vec2Processor.from_pretrained(model_name, **pin_kwargs)

                # Load ONNX model
                from huggingface_hub import hf_hub_download
                onnx_path = hf_hub_download(repo_id=model_name, filename="model.onnx", **pin_kwargs)
```

- [ ] **Step 6: Run the pin test, the logits test and the regression suite**

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.test_onnx_pin_wiring tests.test_onnx_logits_split tests.regression.test_regression -v`
Expected: `OK` (skips allowed in the regression suite, no failures). `python -m core.model_registry --check` now lists `PHONEME_IPA_ONNX` with the SHA. It still exits 1 because the other models are unpinned, which is expected.

- [ ] **Step 7: Commit**

```bash
git add core/model_registry.py core/phoneme_extractor_onnx.py tests/test_onnx_pin_wiring.py
git commit -m "Pin the server ONNX phoneme model revision" -m "The browser still loads it unpinned. That path is out of scope for the benchmark." -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 10: One clip through the production request path

**Files:**
- Create: `backend/tests/benchmark/pipeline.py`
- Test: `backend/tests/benchmark/test_pipeline.py`

- [ ] **Step 1: Write the failing tests**

`backend/tests/benchmark/test_pipeline.py`:

```python
import os
import unittest
from unittest import mock

import numpy as np

from tests.benchmark import common
from tests.benchmark import pipeline as PL
from tests.benchmark import testutil as U


class _ListPhonemes:
    def __init__(self, lists):
        self.lists = lists

    def extract_phoneme(self, audio, sampling_rate=16000, **_kwargs):
        return [list(p) for p in self.lists]


class _Raises:
    def __init__(self, exc):
        self.exc = exc

    def extract_phoneme(self, audio, sampling_rate=16000, **_kwargs):
        raise self.exc


class TestAnalyzeClip(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from core.grapheme_to_phoneme import grapheme_to_phoneme

        cls.audio = PL.load_audio(U.SAMPLE_WAV)
        cls.perfect = [list(p) for _, p in grapheme_to_phoneme(U.SAMPLE_TEXT)]

    def test_perfect_reading(self):
        outcome = PL.analyze_clip(self.audio, U.SAMPLE_TEXT.upper(), _ListPhonemes(self.perfect), U.FakeWords())
        self.assertEqual(outcome.status, "ok")
        words = [w for w in outcome.words if w["type"] != "insertion"]
        self.assertEqual(len(words), 9)
        self.assertTrue(all(w["per"] == 0 for w in words))

    def test_gate_rejection_is_an_outcome(self):
        # Soft gates reject digital silence. The legacy hard gates do not (they measure
        # 60 dB SNR and 0% silence on all-zero audio), which Round 0 will quantify.
        silence = np.zeros(32000, dtype=np.float32)
        with mock.patch.dict(os.environ, {"WWAI_SOFT_QUALITY_GATES": "1"}):
            outcome = PL.analyze_clip(silence, U.SAMPLE_TEXT, _ListPhonemes(self.perfect), U.FakeWords())
        self.assertEqual((outcome.status, outcome.error_type), ("rejected", "AudioRejected"))

    def test_stale_cache_propagates(self):
        with self.assertRaises(common.StaleCacheError):
            PL.analyze_clip(self.audio, U.SAMPLE_TEXT, _Raises(common.StaleCacheError("x")), U.FakeWords())

    def test_replayed_error_keeps_original_type(self):
        outcome = PL.analyze_clip(self.audio, U.SAMPLE_TEXT, _Raises(common.ReplayedError("DeepgramTimeout", "slow")), U.FakeWords())
        self.assertEqual(outcome.error_type, "DeepgramTimeout")

    def test_to_dict_keeps_only_scoring_fields(self):
        outcome = PL.analyze_clip(self.audio, U.SAMPLE_TEXT, _ListPhonemes(self.perfect), U.FakeWords())
        record = outcome.to_dict()["words"][0]
        self.assertEqual(set(record), set(PL.RECORD_FIELDS))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.benchmark.test_pipeline -v`
Expected: ERROR, `ImportError: cannot import name 'pipeline'`.

- [ ] **Step 3: Write `pipeline.py`**

`backend/tests/benchmark/pipeline.py`:

```python
"""One clip through the production request path, with pluggable acoustic models.

Mirrors a server-path analysis request:
  load_and_preprocess_audio_bytes  -> core.request_audio.gate_and_preprocess, mark_preprocessed
  PhonemeAssistant.process_audio   -> clean_sentence -> grapheme_to_phoneme -> process_audio_array
Only the two model objects differ between stage_cache (recording the real models),
run (replaying cached outputs) and speed (live ONNX, cached transcripts).
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

import numpy as np

from . import common

SAMPLE_RATE = 16000
#: The per-word fields scoring needs. Everything else in a record is display data.
RECORD_FIELDS = (
    "type", "ground_truth_word", "expected_phonemes", "actual_phonemes",
    "per", "total_errors", "total_phonemes",
)


def compact_record(record: dict) -> dict:
    out = {}
    for key in RECORD_FIELDS:
        value = record.get(key)
        out[key] = list(value) if isinstance(value, (list, tuple)) else value
    return out


@dataclass
class ClipOutcome:
    status: str  # "ok" or "rejected"
    words: list = field(default_factory=list)
    error_type: str | None = None
    error: str | None = None

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "words": [compact_record(w) for w in self.words],
            "error_type": self.error_type,
            "error": self.error,
        }


def load_audio(path: str) -> np.ndarray:
    import soundfile as sf

    audio, sr = sf.read(path, dtype="float32")
    if audio.ndim == 2:
        audio = audio.mean(axis=1)
    if sr != SAMPLE_RATE:
        import librosa

        audio = librosa.resample(audio, orig_sr=sr, target_sr=SAMPLE_RATE)
    return np.ascontiguousarray(audio, dtype=np.float32)


async def _analyze(audio, text, phoneme_model, word_model, apply_gates):
    from core.audio_preprocessing import mark_preprocessed, reset_preprocessing_state
    from core.grapheme_to_phoneme import clean_sentence, grapheme_to_phoneme
    from core.process_audio import process_audio_array
    from core.request_audio import gate_and_preprocess

    reset_preprocessing_state()
    audio = gate_and_preprocess(audio, SAMPLE_RATE, len(audio) / SAMPLE_RATE, apply_gates=apply_gates)
    mark_preprocessed(audio)
    ground_truth = grapheme_to_phoneme(clean_sentence(text))
    return await process_audio_array(
        ground_truth_phonemes=ground_truth,
        audio_array=audio,
        sampling_rate=SAMPLE_RATE,
        phoneme_extraction_model=phoneme_model,
        word_extraction_model=word_model,
    )


def analyze_clip(audio, text, phoneme_model, word_model, apply_gates=True) -> ClipOutcome:
    """Run one clip. Pipeline failures become a 'rejected' outcome; a stale cache is re-raised."""
    try:
        with common.quiet():
            words = asyncio.run(_analyze(audio, text, phoneme_model, word_model, apply_gates))
    except common.StaleCacheError:
        raise
    except Exception as exc:  # noqa: BLE001 - every pipeline failure is something the child would see
        error_type = getattr(exc, "error_type", None) or type(exc).__name__
        return ClipOutcome("rejected", [], error_type, str(exc)[:300])
    return ClipOutcome("ok", list(words or []))
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.benchmark.test_pipeline -v`
Expected: `OK` (5 tests). If `test_perfect_reading` reports a nonzero PER, print `outcome.words` with `WWAI_BENCH_VERBOSE=1` and check whether the word regrouping in `process_audio_array` changed. Do not loosen the assertion.

- [ ] **Step 5: Commit**

```bash
git add tests/benchmark/pipeline.py tests/benchmark/test_pipeline.py
git commit -m "Add benchmark pipeline that mirrors the server request path" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 11: Cache builder

**Files:**
- Create: `backend/tests/benchmark/stage_cache.py`
- Test: `backend/tests/benchmark/test_stage_cache.py`

- [ ] **Step 1: Write the failing tests**

`backend/tests/benchmark/test_stage_cache.py`:

```python
import json
import os
import tempfile
import unittest
from unittest import mock

import numpy as np

from tests.benchmark import stage_cache as SC
from tests.benchmark import testutil as U


class TestAudioSha(unittest.TestCase):
    def test_deterministic_and_rate_sensitive(self):
        a = np.arange(10, dtype=np.float32)
        self.assertEqual(SC.audio_sha(a, 16000), SC.audio_sha(a.copy(), 16000))
        self.assertNotEqual(SC.audio_sha(a, 16000), SC.audio_sha(a, 8000))
        self.assertNotEqual(SC.audio_sha(a, 16000), SC.audio_sha(a * 2, 16000))


class _FailingWords:
    def extract_words(self, audio, sampling_rate=16000, **_kwargs):
        raise TimeoutError("deepgram slow")


class TestRecordClip(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.processor = U.real_processor_or_skip()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = U.make_temp_dataset(self.tmp.name)
        self.wav = os.path.join(self.root, "WAVE", "SPEAKER0002", "000020022.WAV")
        self.cache = os.path.join(self.tmp.name, "cache")

    def tearDown(self):
        self.tmp.cleanup()

    def test_writes_entry(self):
        utt, status, word_error = SC.record_clip(
            "000020022", self.wav, U.SAMPLE_TEXT, self.cache, U.FakeOnnx(self.processor), U.FakeWords()
        )
        self.assertEqual((utt, status, word_error), ("000020022", "ok", False))
        with open(os.path.join(self.cache, "000020022.json"), encoding="utf-8") as fh:
            meta = json.load(fh)
        self.assertEqual(len(meta["phoneme_calls"]), 1)
        self.assertEqual(meta["phoneme_calls"][0]["logits_key"], "logits_0")
        self.assertEqual(meta["word_calls"][0]["words"], U.SAMPLE_TEXT.split())
        with np.load(os.path.join(self.cache, "000020022.npz")) as data:
            self.assertEqual(data["logits_0"].dtype, np.float32)

    def test_word_errors_are_recorded(self):
        _utt, status, word_error = SC.record_clip(
            "000020022", self.wav, U.SAMPLE_TEXT, self.cache, U.FakeOnnx(self.processor), _FailingWords()
        )
        self.assertEqual((status, word_error), ("rejected", True))
        with open(os.path.join(self.cache, "000020022.json"), encoding="utf-8") as fh:
            meta = json.load(fh)
        self.assertEqual(meta["word_calls"][0]["error_type"], "TimeoutError")
        self.assertTrue(SC.entry_has_word_error(meta))

    def test_gates_are_not_applied_when_recording(self):
        from core import request_audio

        with mock.patch.object(request_audio, "gate_audio", side_effect=request_audio.AudioRejected("no")):
            _utt, status, _ = SC.record_clip(
                "000020022", self.wav, U.SAMPLE_TEXT, self.cache, U.FakeOnnx(self.processor), U.FakeWords()
            )
        self.assertEqual(status, "ok")  # a gate that would reject was never consulted


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.benchmark.test_stage_cache -v`
Expected: ERROR, `ImportError: cannot import name 'stage_cache'`.

- [ ] **Step 3: Write `stage_cache.py`**

`backend/tests/benchmark/stage_cache.py`:

```python
"""Run the slow, deterministic stages once per clip and save what the models returned.

For every model call the production pipeline makes on a clip, this records a hash of
the exact audio passed in plus the model's output (raw ONNX logits for the phoneme
model, the word list for Deepgram). replay.py feeds those back and raises
StaleCacheError if the current code would pass the models different audio.

Gates are not applied while recording, so every clip has model outputs. run.py applies
the gates at scoring time, which lets gate flags change without a new cache.

    python -m tests.benchmark.stage_cache --half dev
    python -m tests.benchmark.stage_cache --half dev --flag WWAI_SINGLE_PREPROCESS=1
    python -m tests.benchmark.stage_cache --half dev --retry-errors
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from multiprocessing import get_context

import numpy as np

from . import common

CACHE_META = "_cache_meta.json"
_models: dict = {}


def audio_sha(audio, sampling_rate) -> str:
    digest = hashlib.sha1()
    digest.update(np.ascontiguousarray(audio, dtype=np.float32).tobytes())
    digest.update(str(int(sampling_rate)).encode())
    return digest.hexdigest()


def cache_dir(half: str, name: str) -> str:
    return os.path.join(common.cache_root(), half, name)


class RecordingPhonemeExtractor:
    """Wraps PhonemeExtractorONNX and records the logits of every call."""

    def __init__(self, inner):
        self.inner = inner
        self.calls: list[dict] = []
        self.logits: list[np.ndarray] = []

    def extract_phoneme(self, audio, sampling_rate=16000, **_kwargs):
        from core.phoneme_extractor_onnx import decode_logits

        call = {"input_sha": audio_sha(audio, sampling_rate)}
        self.calls.append(call)
        try:
            logits = self.inner.extract_logits(audio, sampling_rate=sampling_rate)
        except Exception as exc:
            call.update(error_type=type(exc).__name__, error=str(exc))
            raise
        call["logits_key"] = f"logits_{len(self.logits)}"
        self.logits.append(np.asarray(logits, dtype=np.float32))
        return decode_logits(logits, self.inner.processor, self.inner.model_output_processing)


class RecordingWordExtractor:
    """Wraps the word extractor (Deepgram) and records every call's words or error."""

    def __init__(self, inner):
        self.inner = inner
        self.calls: list[dict] = []

    def extract_words(self, audio, sampling_rate=16000, **_kwargs):
        call = {"input_sha": audio_sha(audio, sampling_rate)}
        self.calls.append(call)
        try:
            words = self.inner.extract_words(audio, sampling_rate=sampling_rate)
        except Exception as exc:
            call.update(error_type=type(exc).__name__, error=str(exc))
            raise
        call["words"] = None if words is None else [str(w) for w in words]
        return words


def entry_has_word_error(meta: dict) -> bool:
    return any("error_type" in call for call in meta.get("word_calls", []))


def write_entry(directory, utt_id, phon: RecordingPhonemeExtractor, words: RecordingWordExtractor,
                recorded_status: str, seconds: float) -> None:
    os.makedirs(directory, exist_ok=True)
    if phon.logits:
        np.savez(os.path.join(directory, f"{utt_id}.npz"),
                 **{f"logits_{i}": arr for i, arr in enumerate(phon.logits)})
    meta = {
        "utt_id": utt_id,
        "phoneme_calls": phon.calls,
        "word_calls": words.calls,
        "recorded_status": recorded_status,
        "seconds": round(seconds, 3),
    }
    tmp = os.path.join(directory, f"{utt_id}.json.tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False)
    os.replace(tmp, os.path.join(directory, f"{utt_id}.json"))  # the .json marks the entry complete


def record_clip(utt_id, wav_path, text, directory, phoneme_inner, word_inner):
    """Record one clip with the given real (or fake) models. Returns (utt_id, status, word_error)."""
    from .pipeline import analyze_clip, load_audio

    phon = RecordingPhonemeExtractor(phoneme_inner)
    words = RecordingWordExtractor(word_inner)
    start = time.perf_counter()
    outcome = analyze_clip(load_audio(wav_path), text, phon, words, apply_gates=False)
    write_entry(directory, utt_id, phon, words, outcome.status, time.perf_counter() - start)
    return utt_id, outcome.status, entry_has_word_error({"word_calls": words.calls})


def write_meta(directory: str, half: str, name: str, flags: dict) -> dict:
    from core.model_registry import repo_id, resolve_revision

    path = os.path.join(directory, CACHE_META)
    meta = {
        "half": half,
        "name": name,
        "model_repo": repo_id("PHONEME_IPA_ONNX"),
        "model_revision": resolve_revision("PHONEME_IPA_ONNX"),
        "flags": flags,
        "git_sha": common.git_sha(),
        "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as fh:
            existing = json.load(fh)
        if existing.get("model_revision") != meta["model_revision"]:
            raise SystemExit(
                f"{directory} was built with model revision {existing.get('model_revision')}, "
                f"current is {meta['model_revision']}. Use a new --name."
            )
        return existing
    os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2, sort_keys=True)
    return meta


def _load_deepgram_key() -> None:
    """Load only DEEPGRAM_KEY from backend/.env, never any WWAI_* flag that might be there."""
    if os.getenv("DEEPGRAM_KEY"):
        return
    from dotenv import dotenv_values

    key = dotenv_values(os.path.join(common.BACKEND_ROOT, ".env")).get("DEEPGRAM_KEY")
    if key:
        os.environ["DEEPGRAM_KEY"] = key


def _init_worker() -> None:
    _load_deepgram_key()
    with common.quiet():
        from core.phoneme_extractor_onnx import PhonemeExtractorONNX
        from core.word_extractor import WordExtractorOnline

        _models["phoneme"] = PhonemeExtractorONNX()
        _models["words"] = WordExtractorOnline()


def _record_task(task):
    utt_id, wav_path, text, directory = task
    return record_clip(utt_id, wav_path, text, directory, _models["phoneme"], _models["words"])


def build(half, name, flags, workers, retry_errors=False, subset=None, limit=None) -> dict:
    from .dataset import load_clips

    clips = load_clips(half, subset)
    if limit:
        clips = clips[:limit]
    directory = cache_dir(half, name)
    write_meta(directory, half, name, flags)
    todo = []
    for clip in clips:
        meta_path = os.path.join(directory, f"{clip.utt_id}.json")
        if os.path.isfile(meta_path):
            if not retry_errors:
                continue
            with open(meta_path, encoding="utf-8") as fh:
                if not entry_has_word_error(json.load(fh)):
                    continue
        todo.append((clip.utt_id, clip.wav_path, clip.text, directory))
    print(f"{len(clips)} clips, {len(clips) - len(todo)} cached, {len(todo)} to record into {directory}")

    statuses = {"ok": 0, "rejected": 0}
    word_errors = []
    if todo:
        with get_context("spawn").Pool(processes=workers, initializer=_init_worker) as pool:
            for i, (utt_id, status, word_error) in enumerate(pool.imap_unordered(_record_task, todo, chunksize=4), 1):
                statuses[status] += 1
                if word_error:
                    word_errors.append(utt_id)
                if i % 50 == 0 or i == len(todo):
                    print(f"  {i}/{len(todo)} recorded ({len(word_errors)} word-extraction errors)")
    return {"cache": directory, "recorded": len(todo), "statuses": statuses, "word_errors": sorted(word_errors)}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m tests.benchmark.stage_cache")
    parser.add_argument("--half", choices=["dev", "test"], default="dev")
    parser.add_argument("--name", help="cache name (default: derived from front-end flags)")
    parser.add_argument("--flag", action="append", default=[], metavar="WWAI_NAME=VALUE")
    parser.add_argument("--subset")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--retry-errors", action="store_true")
    args = parser.parse_args(argv)

    common.apply_flags(common.parse_flag_args(args.flag))
    active = common.active_wwai_flags()
    name = args.name or common.front_end_cache_name(active)
    summary = build(args.half, name, active, args.workers, args.retry_errors, args.subset, args.limit)
    print(json.dumps(summary, indent=2))
    return 1 if summary["word_errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.benchmark.test_stage_cache -v`
Expected: `OK` (4 tests).

- [ ] **Step 5: Commit**

```bash
git add tests/benchmark/stage_cache.py tests/benchmark/test_stage_cache.py
git commit -m "Add benchmark cache builder with per-call input hashes" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 12: Replay

**Files:**
- Create: `backend/tests/benchmark/replay.py`
- Test: `backend/tests/benchmark/test_replay.py`

- [ ] **Step 1: Write the failing tests**

`backend/tests/benchmark/test_replay.py`:

```python
import json
import os
import tempfile
import unittest

import numpy as np

from tests.benchmark import common
from tests.benchmark import pipeline as PL
from tests.benchmark import replay as R
from tests.benchmark import stage_cache as SC
from tests.benchmark import testutil as U


class TestReplay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.processor = U.real_processor_or_skip()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = U.make_temp_dataset(self.tmp.name)
        self.wav = os.path.join(root, "WAVE", "SPEAKER0002", "000020022.WAV")
        self.cache = os.path.join(self.tmp.name, "cache")
        SC.record_clip("u1", self.wav, U.SAMPLE_TEXT, self.cache, U.FakeOnnx(self.processor), U.FakeWords())
        self.audio = PL.load_audio(self.wav)

    def tearDown(self):
        self.tmp.cleanup()

    def _replay(self, entry=None):
        entry = entry or R.CacheEntry(self.cache, "u1")
        return PL.analyze_clip(self.audio, U.SAMPLE_TEXT, R.ReplayPhonemeExtractor(entry, self.processor), R.ReplayWordExtractor(entry))

    def test_replay_matches_a_direct_run(self):
        direct = PL.analyze_clip(self.audio, U.SAMPLE_TEXT, U.FakeOnnxExtractor(self.processor), U.FakeWords())
        self.assertEqual(self._replay().to_dict(), direct.to_dict())
        self.assertEqual(direct.status, "ok")

    def test_replay_is_deterministic(self):
        self.assertEqual(self._replay().to_dict(), self._replay().to_dict())

    def test_changed_input_is_stale(self):
        replay = R.ReplayPhonemeExtractor(R.CacheEntry(self.cache, "u1"), self.processor)
        with self.assertRaises(common.StaleCacheError):
            replay.extract_phoneme(np.ones(16000, dtype=np.float32), 16000)

    def test_extra_call_is_stale(self):
        entry = R.CacheEntry(self.cache, "u1")
        words = R.ReplayWordExtractor(entry, check_inputs=False)
        words.extract_words(self.audio)
        with self.assertRaises(common.StaleCacheError):
            words.extract_words(self.audio)

    def test_missing_entry_is_stale(self):
        with self.assertRaises(common.StaleCacheError):
            R.CacheEntry(self.cache, "nope")

    def test_recorded_errors_replay_with_their_type(self):
        path = os.path.join(self.cache, "u1.json")
        with open(path, encoding="utf-8") as fh:
            meta = json.load(fh)
        meta["word_calls"][0] = {"input_sha": meta["word_calls"][0]["input_sha"], "error_type": "ValueError", "error": "bad"}
        meta["phoneme_calls"][0]["error_type"] = "DeepgramAuthError"
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(meta, fh)
        entry = R.CacheEntry(self.cache, "u1")
        with self.assertRaises(ValueError):
            R.ReplayWordExtractor(entry, check_inputs=False).extract_words(self.audio)
        with self.assertRaises(common.ReplayedError):
            R.ReplayPhonemeExtractor(entry, self.processor, check_inputs=False).extract_phoneme(self.audio)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.benchmark.test_replay -v`
Expected: ERROR, `ImportError: cannot import name 'replay'`.

- [ ] **Step 3: Write `replay.py`**

`backend/tests/benchmark/replay.py`:

```python
"""Feed cached model outputs back into the real pipeline.

Each replayed call checks that the audio it receives hashes to what was recorded. Any
front-end change (preprocessing code, chunking, a front-end flag) therefore stops the
run with StaleCacheError instead of silently scoring outputs for different audio.
"""

from __future__ import annotations

import builtins
import json
import os

import numpy as np

from . import common
from .stage_cache import audio_sha


class CacheEntry:
    def __init__(self, directory: str, utt_id: str):
        meta_path = os.path.join(directory, f"{utt_id}.json")
        if not os.path.isfile(meta_path):
            raise common.StaleCacheError(
                f"no cache entry for {utt_id} in {directory}; build it with tests.benchmark.stage_cache"
            )
        with open(meta_path, encoding="utf-8") as fh:
            self.meta = json.load(fh)
        self._npz_path = os.path.join(directory, f"{utt_id}.npz")
        self._logits: dict | None = None

    @property
    def utt_id(self) -> str:
        return self.meta.get("utt_id", "?")

    @property
    def phoneme_calls(self) -> list:
        return self.meta["phoneme_calls"]

    @property
    def word_calls(self) -> list:
        return self.meta["word_calls"]

    def logits(self, key: str) -> np.ndarray:
        if self._logits is None:
            with np.load(self._npz_path) as data:
                self._logits = {k: data[k] for k in data.files}
        return self._logits[key]


def load_processor():
    from transformers import Wav2Vec2Processor
    from core.model_registry import from_pretrained_kwargs, repo_id

    return Wav2Vec2Processor.from_pretrained(
        repo_id("PHONEME_IPA_ONNX"), **from_pretrained_kwargs("PHONEME_IPA_ONNX")
    )


def _raise_recorded(call: dict):
    error_type, message = call["error_type"], call.get("error", "")
    exc_cls = getattr(builtins, error_type, None)
    if isinstance(exc_cls, type) and issubclass(exc_cls, Exception):
        raise exc_cls(message)  # builtins keep their type, so `except ValueError` still matches
    raise common.ReplayedError(error_type, message)


class _Replay:
    kind = ""

    def __init__(self, entry: CacheEntry, calls: list, check_inputs: bool = True):
        self.entry = entry
        self._calls = calls
        self._next = 0
        self.check_inputs = check_inputs

    def _take(self, audio, sampling_rate) -> dict:
        if self._next >= len(self._calls):
            raise common.StaleCacheError(
                f"{self.entry.utt_id}: the pipeline made more {self.kind} calls than were recorded; rebuild the cache"
            )
        call = self._calls[self._next]
        self._next += 1
        if self.check_inputs and audio_sha(audio, sampling_rate) != call["input_sha"]:
            raise common.StaleCacheError(
                f"{self.entry.utt_id}: audio sent to the {self.kind} model differs from the cached run "
                "(front-end code or flags changed); build a new cache with tests.benchmark.stage_cache"
            )
        if "error_type" in call:
            _raise_recorded(call)
        return call


class ReplayPhonemeExtractor(_Replay):
    kind = "phoneme"

    def __init__(self, entry: CacheEntry, processor, check_inputs: bool = True):
        super().__init__(entry, entry.phoneme_calls, check_inputs)
        self.processor = processor

    def extract_phoneme(self, audio, sampling_rate=16000, **_kwargs):
        from core.phoneme_extractor_onnx import decode_logits

        call = self._take(audio, sampling_rate)
        return decode_logits(self.entry.logits(call["logits_key"]), self.processor)


class ReplayWordExtractor(_Replay):
    kind = "word"

    def __init__(self, entry: CacheEntry, check_inputs: bool = True):
        super().__init__(entry, entry.word_calls, check_inputs)

    def extract_words(self, audio, sampling_rate=16000, **_kwargs):
        call = self._take(audio, sampling_rate)
        return None if call["words"] is None else list(call["words"])
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.benchmark.test_replay -v`
Expected: `OK` (6 tests). If `test_replay_matches_a_direct_run` raises StaleCacheError, preprocessing is not deterministic between runs. Stop and investigate with superpowers:systematic-debugging, because the whole cache design depends on it.

- [ ] **Step 5: Commit**

```bash
git add tests/benchmark/replay.py tests/benchmark/test_replay.py
git commit -m "Add cache replay with stale-input detection" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 13: Scoring (outcomes plus labels into metrics)

**Files:**
- Create: `backend/tests/benchmark/scoring.py`
- Test: `backend/tests/benchmark/test_scoring.py`

- [ ] **Step 1: Write the failing tests**

`backend/tests/benchmark/test_scoring.py`:

```python
import unittest

from tests.benchmark import scoring as S
from tests.benchmark import testutil as U


def _clips():
    good = U.synthetic_clip("c1", "s1", 7, [
        ("CAT", 10, "K AE1 T", [2, 2, 2]),
        ("DOG", 3, "D AO1 G", [2, 0, 2]),
    ], sentence_accuracy=6)
    rejected = U.synthetic_clip("c2", "s2", 30, [("A", 10, "AH0", [2])])
    mismatch = U.synthetic_clip("c3", "s3", 30, [("A", 10, "AH0", [2]), ("B", 10, "B IY1", [2, 2])])
    return [good, rejected, mismatch]


def _outcomes():
    return {
        "c1": U.ok(
            U.record("cat", ["k", "æ", "t"], ["k", "æ", "t"], 0.0),
            U.record("", [], ["ʌ"], 0.0, rtype="insertion"),
            U.record("dog", ["d", "ɔ", "g"], ["d", "ɑ", "g"], 0.3333),
        ),
        "c2": U.rejected("AudioRejected"),
        "c3": U.ok(U.record("a", ["ə"], ["ə"], 0.0)),
    }


class TestBuildItems(unittest.TestCase):
    def setUp(self):
        self.items = S.build_items(_clips(), _outcomes())

    def test_counts(self):
        self.assertEqual((self.items.clips, self.items.rejected, self.items.word_count_mismatch), (3, 1, 1))
        self.assertEqual(self.items.rejected_by_type, {"AudioRejected": 1})

    def test_words(self):
        self.assertEqual([(w.text, w.is_mistake, w.per) for w in self.items.words],
                         [("CAT", False, 0.0), ("DOG", True, 0.3333)])
        self.assertTrue(self.items.words[0].is_child)

    def test_phones(self):
        self.assertEqual(len(self.items.phones), 6)
        dog_vowel = self.items.phones[4]
        self.assertTrue(dog_vowel.is_mistake)
        self.assertTrue(dog_vowel.system_error)
        self.assertFalse(any(p.system_error for p in self.items.phones[:3]))

    def test_g2p_and_sentence(self):
        self.assertEqual((self.items.g2p_agree, self.items.g2p_total), (2, 2))
        self.assertAlmostEqual(self.items.sentences[0].sentence_per, 1 / 6, places=3)

    def test_missing_outcome(self):
        with self.assertRaises(KeyError):
            S.build_items(_clips(), {"c1": _outcomes()["c1"]})


class TestSummarize(unittest.TestCase):
    def test_summary(self):
        summary = S.summarize(S.build_items(_clips(), _outcomes()), threshold=0.3)
        word = summary["word"]["all"]
        self.assertEqual(word["counts"], [1, 0, 0, 1])
        self.assertAlmostEqual(word["f05"], 1.0)
        self.assertAlmostEqual(summary["rejection_rate"], 1 / 3)
        self.assertEqual(summary["word"]["adults"]["n"], 0)
        self.assertEqual(summary["best_threshold"]["threshold"], 0.3333)
        self.assertEqual(summary["phone"]["all"]["counts"], [1, 0, 0, 5])
        self.assertIn("sentence", summary["pearson"])

    def test_threshold_above_score_misses(self):
        summary = S.summarize(S.build_items(_clips(), _outcomes()), threshold=0.4)
        self.assertEqual(summary["word"]["all"]["counts"], [0, 0, 1, 1])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.benchmark.test_scoring -v`
Expected: ERROR, `ImportError: cannot import name 'scoring'`.

- [ ] **Step 3: Write `scoring.py`**

`backend/tests/benchmark/scoring.py`:

```python
"""Join pipeline outcomes with speechocean762 labels and compute the benchmark summary."""

from __future__ import annotations

from dataclasses import dataclass, field

from . import metrics as M
from .phones import canonical_ipa, g2p_agrees, gt_error_flags, map_canonical_to_system


@dataclass
class WordItem:
    utt_id: str
    speaker: str
    is_child: bool
    text: str
    human_accuracy: float
    is_mistake: bool
    per: float


@dataclass
class PhoneItem:
    utt_id: str
    speaker: str
    is_child: bool
    human_accuracy: float
    is_mistake: bool
    is_mistake_strict: bool
    system_error: bool


@dataclass
class SentenceItem:
    utt_id: str
    speaker: str
    is_child: bool
    human_accuracy: float
    sentence_per: float


@dataclass
class ItemSet:
    words: list = field(default_factory=list)
    phones: list = field(default_factory=list)
    sentences: list = field(default_factory=list)
    clips: int = 0
    rejected: int = 0
    rejected_by_type: dict = field(default_factory=dict)
    word_count_mismatch: int = 0
    g2p_agree: int = 0
    g2p_total: int = 0
    phones_unmapped: int = 0


def build_items(clips, outcomes: dict) -> ItemSet:
    items = ItemSet()
    for clip in clips:
        if clip.utt_id not in outcomes:
            raise KeyError(f"no outcome for clip {clip.utt_id}")
        outcome = outcomes[clip.utt_id]
        items.clips += 1
        if outcome["status"] != "ok":
            items.rejected += 1
            key = outcome.get("error_type") or "unknown"
            items.rejected_by_type[key] = items.rejected_by_type.get(key, 0) + 1
            continue
        records = [r for r in outcome["words"] if r.get("type") != "insertion"]
        if len(records) != len(clip.words):
            items.word_count_mismatch += 1
            continue
        total_phonemes = sum(r.get("total_phonemes") or 0 for r in outcome["words"])
        total_errors = sum(r.get("total_errors") or 0 for r in outcome["words"])
        items.sentences.append(SentenceItem(
            clip.utt_id, clip.speaker, clip.is_child, clip.sentence_accuracy,
            total_errors / total_phonemes if total_phonemes else 0.0,
        ))
        for word, record in zip(clip.words, records):
            items.words.append(WordItem(
                clip.utt_id, clip.speaker, clip.is_child, word.text, word.accuracy,
                M.word_is_mistake(word.accuracy), float(record.get("per") or 0.0),
            ))
            expected = list(record.get("expected_phonemes") or [])
            canonical = canonical_ipa(word.phones)
            items.g2p_total += 1
            items.g2p_agree += int(g2p_agrees(canonical, expected))
            errors = gt_error_flags(expected, record.get("actual_phonemes") or [])
            for k, system_idx in enumerate(map_canonical_to_system(canonical, expected)):
                if not system_idx:
                    items.phones_unmapped += 1
                    continue
                accuracy = word.phone_accuracy[k]
                items.phones.append(PhoneItem(
                    clip.utt_id, clip.speaker, clip.is_child, accuracy,
                    M.phone_is_mistake(accuracy), M.phone_is_mistake(accuracy, strict=True),
                    any(errors[j] for j in system_idx),
                ))
    return items


SLICES = {
    "all": lambda item: True,
    "children": lambda item: item.is_child,
    "adults": lambda item: not item.is_child,
}


def _metrics(labels, flags) -> dict:
    c = M.confusion(labels, flags)
    return {
        "n": c.n,
        "mistakes": int(sum(labels)),
        "f05": c.f_beta(),
        "precision": c.precision,
        "recall": c.recall,
        "false_alarm_rate": c.false_alarm_rate,
        "counts": [c.tp, c.fp, c.fn, c.tn],
    }


def word_slice_metrics(words, threshold: float) -> dict:
    return _metrics([w.is_mistake for w in words], M.flags_at([w.per for w in words], threshold))


def phone_slice_metrics(phones, strict: bool) -> dict:
    labels = [p.is_mistake_strict if strict else p.is_mistake for p in phones]
    return _metrics(labels, [p.system_error for p in phones])


def summarize(items: ItemSet, threshold: float) -> dict:
    out = {
        "threshold": threshold,
        "clips": items.clips,
        "rejected": items.rejected,
        "rejection_rate": items.rejected / items.clips if items.clips else 0.0,
        "rejected_by_type": dict(sorted(items.rejected_by_type.items())),
        "word_count_mismatch": items.word_count_mismatch,
        "g2p_disagreement_rate": 1 - items.g2p_agree / items.g2p_total if items.g2p_total else 0.0,
        "phones_unmapped": items.phones_unmapped,
        "word": {},
        "phone": {},
        "phone_strict": {},
    }
    for name, keep in SLICES.items():
        words = [w for w in items.words if keep(w)]
        phones = [p for p in items.phones if keep(p)]
        out["word"][name] = word_slice_metrics(words, threshold)
        out["phone"][name] = phone_slice_metrics(phones, strict=False)
        out["phone_strict"][name] = phone_slice_metrics(phones, strict=True)
    labels = [w.is_mistake for w in items.words]
    scores = [w.per for w in items.words]
    best_t, best_f = M.best_threshold(labels, scores)
    out["best_threshold"] = {"threshold": best_t, "f05": best_f}
    out["pr_curve"] = M.pr_curve(labels, scores)
    out["pearson"] = {
        "word": M.pearson([w.human_accuracy for w in items.words], [-w.per for w in items.words]),
        "phone": M.pearson([p.human_accuracy for p in items.phones],
                           [0.0 if p.system_error else 1.0 for p in items.phones]),
        "sentence": M.pearson([s.human_accuracy for s in items.sentences],
                              [-s.sentence_per for s in items.sentences]),
    }
    return out
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.benchmark.test_scoring -v`
Expected: `OK` (7 tests).

- [ ] **Step 5: Commit**

```bash
git add tests/benchmark/scoring.py tests/benchmark/test_scoring.py
git commit -m "Add benchmark scoring that joins outcomes with expert labels" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 14: `run.py` with the test-half lock

**Files:**
- Create: `backend/tests/benchmark/run.py`
- Test: `backend/tests/benchmark/test_run.py`

- [ ] **Step 1: Write the failing tests**

`backend/tests/benchmark/test_run.py`:

```python
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
            SC.record_clip(clip.utt_id, clip.wav_path, clip.text, directory, U.FakeOnnx(self.processor), U.FakeWords())

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.benchmark.test_run -v`
Expected: ERROR, `ImportError: cannot import name 'run'`.

- [ ] **Step 3: Write `run.py`**

`backend/tests/benchmark/run.py`:

```python
"""Score one configuration against speechocean762 using cached model outputs.

    python -m tests.benchmark.run --name baseline
    python -m tests.benchmark.run --name weighted --flag WWAI_WEIGHTED_PER=1
    python -m tests.benchmark.run --name quick --subset smoke_dev

The test half needs WWAI_BENCH_UNLOCK_TEST=1 and --reason, and every such run is
appended to test_runs.log. Exit codes: 0 ok, 2 usage error or locked, 3 stale or
missing cache.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from multiprocessing import get_context

from . import common

EXIT_STALE = 3
_worker: dict = {}


def check_test_unlock(half: str, reason, env=None) -> None:
    if half != "test":
        return
    if not common.env_flag(common.UNLOCK_ENV, env):
        raise PermissionError(
            f"the test half is sealed. Set {common.UNLOCK_ENV}=1 and pass --reason; "
            "every run is logged to tests/benchmark/test_runs.log"
        )
    if not (reason or "").strip():
        raise PermissionError("test-half runs need --reason")


def append_ledger(name: str, reason: str, sha: str, path: str = common.TEST_RUNS_LOG) -> None:
    with open(path, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')}\t{sha}\t{name}\t{reason.strip()}\n")


def production_threshold() -> float:
    from core.phoneme_feedback_formatter import HIGH_PER_THRESHOLD

    return float(HIGH_PER_THRESHOLD)


def check_cache(directory: str) -> dict:
    from .stage_cache import CACHE_META

    meta_path = os.path.join(directory, CACHE_META)
    if not os.path.isfile(meta_path):
        raise common.StaleCacheError(f"no cache at {directory}; build it with tests.benchmark.stage_cache")
    with open(meta_path, encoding="utf-8") as fh:
        meta = json.load(fh)
    from core.model_registry import resolve_revision

    current = resolve_revision("PHONEME_IPA_ONNX")
    if meta.get("model_revision") != current:
        raise common.StaleCacheError(
            f"cache was built with model revision {meta.get('model_revision')}, current is {current}"
        )
    return meta


def _init_worker() -> None:
    with common.quiet():
        from .replay import load_processor

        _worker["processor"] = load_processor()


def _score_task(task):
    utt_id, wav_path, text, directory = task
    from .pipeline import analyze_clip, load_audio
    from .replay import CacheEntry, ReplayPhonemeExtractor, ReplayWordExtractor

    entry = CacheEntry(directory, utt_id)
    outcome = analyze_clip(
        load_audio(wav_path), text,
        ReplayPhonemeExtractor(entry, _worker["processor"]), ReplayWordExtractor(entry),
    )
    return utt_id, outcome.to_dict()


def score_clips(clips, directory: str, workers: int) -> dict:
    tasks = [(c.utt_id, c.wav_path, c.text, directory) for c in clips]
    outcomes = {}
    if workers <= 1:
        _init_worker()
        for task in tasks:
            utt_id, outcome = _score_task(task)
            outcomes[utt_id] = outcome
    else:
        with get_context("spawn").Pool(processes=workers, initializer=_init_worker) as pool:
            for utt_id, outcome in pool.imap_unordered(_score_task, tasks, chunksize=8):
                outcomes[utt_id] = outcome
    return dict(sorted(outcomes.items()))


def write_results(results: dict, out_path: str) -> tuple[str, str]:
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(results, fh, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    base = out_path[:-5] if out_path.endswith(".json") else out_path
    summary_path = base + ".summary.json"
    with open(summary_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump({k: v for k, v in results.items() if k != "outcomes"}, fh,
                  ensure_ascii=False, sort_keys=True, indent=2)
    return out_path, summary_path


def format_summary(summary: dict) -> str:
    lines = [
        f"clips {summary['clips']}   rejected {summary['rejected']} ({summary['rejection_rate']:.1%})   "
        f"word-count mismatches {summary['word_count_mismatch']}   threshold {summary['threshold']}",
        f"{'word':10s} {'F0.5':>7s} {'prec':>7s} {'recall':>7s} {'FAR':>7s} {'n':>7s}",
    ]
    for name in ("all", "children", "adults"):
        m = summary["word"][name]
        lines.append(f"{name:10s} {m['f05']:7.4f} {m['precision']:7.4f} {m['recall']:7.4f} "
                     f"{m['false_alarm_rate']:7.4f} {m['n']:7d}")
    best = summary["best_threshold"]
    lines.append(f"best threshold on this half {best['threshold']} (F0.5 {best['f05']:.4f})")
    lines.append("pearson  " + "  ".join(
        f"{k} {v:.3f}" if v is not None else f"{k} n/a" for k, v in summary["pearson"].items()))
    lines.append(f"g2p disagreement {summary['g2p_disagreement_rate']:.1%}   rejected by type {summary['rejected_by_type']}")
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m tests.benchmark.run")
    parser.add_argument("--name", default="unnamed", help="configuration name, used in output file names")
    parser.add_argument("--half", choices=["dev", "test"], default="dev")
    parser.add_argument("--subset", help="name of a list in tests/benchmark/subsets/")
    parser.add_argument("--cache", help="cache name (default: derived from front-end flags)")
    parser.add_argument("--flag", action="append", default=[], metavar="WWAI_NAME=VALUE")
    parser.add_argument("--threshold", type=float, help="override production's HIGH_PER_THRESHOLD")
    parser.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) // 2))
    parser.add_argument("--out", help="results path (default: tests/benchmark/results/<name>_<half>.json)")
    parser.add_argument("--reason", help="required for --half test")
    args = parser.parse_args(argv)

    try:
        flags = common.parse_flag_args(args.flag)
        check_test_unlock(args.half, args.reason)
    except (ValueError, PermissionError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    common.apply_flags(flags)
    active = common.active_wwai_flags()

    from .dataset import load_clips
    from .scoring import build_items, summarize
    from .stage_cache import cache_dir

    cache_name = args.cache or common.front_end_cache_name(active)
    directory = cache_dir(args.half, cache_name)
    clips = load_clips(args.half, args.subset)
    sha = common.git_sha()
    if args.half == "test":
        append_ledger(args.name, args.reason, sha)

    start = time.time()
    try:
        cache_meta = check_cache(directory)
        threshold = args.threshold if args.threshold is not None else production_threshold()
        outcomes = score_clips(clips, directory, args.workers)
    except common.StaleCacheError as exc:
        print(f"stale cache: {exc}", file=sys.stderr)
        return EXIT_STALE

    summary = summarize(build_items(clips, outcomes), threshold)
    results = {
        "name": args.name,
        "half": args.half,
        "subset": args.subset,
        "cache": cache_name,
        "cache_model_revision": cache_meta.get("model_revision"),
        "git_sha": sha,
        "flags": active,
        "threshold": threshold,
        "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "seconds": round(time.time() - start, 1),
        "summary": summary,
        "outcomes": outcomes,
    }
    suffix = f"_{args.subset}" if args.subset else ""
    out = args.out or os.path.join(common.results_dir(), f"{args.name}_{args.half}{suffix}.json")
    full, short = write_results(results, out)
    print(format_summary(summary))
    print(f"wrote {full}\n      {short}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.benchmark.test_run -v`
Expected: `OK` (10 tests).

- [ ] **Step 5: Commit**

```bash
git add tests/benchmark/run.py tests/benchmark/test_run.py
git commit -m "Add benchmark runner with sealed test half and ledger" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 15: `compare.py` and the acceptance rule

**Files:**
- Create: `backend/tests/benchmark/compare.py`
- Test: `backend/tests/benchmark/test_compare.py`

- [ ] **Step 1: Write the failing tests**

`backend/tests/benchmark/test_compare.py`:

```python
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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.benchmark.test_compare -v`
Expected: ERROR, `ImportError: cannot import name 'compare'`.

- [ ] **Step 3: Write `compare.py`**

`backend/tests/benchmark/compare.py`:

```python
"""Paired comparison of two run.py results files, applying acceptance conditions 1 to 4.

    python -m tests.benchmark.compare results/baseline_dev.json results/candidate_dev.json

Conditions 5 (speed and memory, see speed.py) and 6 (tests pass) are checked separately
at review time. Exit codes: 0 all four pass, 1 at least one fails, 2 inputs not comparable.
"""

from __future__ import annotations

import argparse
import json
import sys

from . import common
from . import metrics as M
from .scoring import build_items, summarize

FAR_TOLERANCE = 0.005
REJECTION_TOLERANCE = 0.01
N_RESAMPLES = 2000
SEED = 0
_EPS = 1e-12


class NotComparable(ValueError):
    """The two results files cannot be compared (different half, subset or clips)."""


def load_results(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _word_counts(items, threshold):
    words = items.words
    return M.per_speaker_counts([w.speaker for w in words], [w.is_mistake for w in words],
                                M.flags_at([w.per for w in words], threshold))


def compare_results(base: dict, cand: dict, clips, n_resamples: int = N_RESAMPLES, seed: int = SEED) -> dict:
    if base["half"] != cand["half"] or base.get("subset") != cand.get("subset"):
        raise NotComparable(
            f"base is {base['half']}/{base.get('subset')}, candidate is {cand['half']}/{cand.get('subset')}"
        )
    if set(base["outcomes"]) != set(cand["outcomes"]):
        raise NotComparable("the two results cover different clips")

    base_items = build_items(clips, base["outcomes"])
    cand_items = build_items(clips, cand["outcomes"])
    bs = summarize(base_items, base["threshold"])
    cs = summarize(cand_items, cand["threshold"])
    deltas = M.bootstrap_fbeta_delta(_word_counts(base_items, base["threshold"]),
                                     _word_counts(cand_items, cand["threshold"]), n_resamples, seed)
    lo, hi = M.percentile_interval(deltas)

    child_delta = cs["word"]["children"]["f05"] - bs["word"]["children"]["f05"]
    far_delta = cs["word"]["all"]["false_alarm_rate"] - bs["word"]["all"]["false_alarm_rate"]
    rej_delta = cs["rejection_rate"] - bs["rejection_rate"]
    checks = [
        {"name": "real improvement", "rule": "95% CI of word F0.5 difference above 0",
         "value": f"[{lo:+.4f}, {hi:+.4f}]", "passed": lo > 0},
        {"name": "children not worse", "rule": "children F0.5 difference >= 0",
         "value": f"{child_delta:+.4f}", "passed": child_delta >= -_EPS},
        {"name": "no more wrong corrections", "rule": f"false-alarm rate rises <= {FAR_TOLERANCE:.3f}",
         "value": f"{far_delta:+.4f}", "passed": far_delta <= FAR_TOLERANCE + _EPS},
        {"name": "no hiding", "rule": f"rejection rate rises <= {REJECTION_TOLERANCE:.2f}",
         "value": f"{rej_delta:+.4f}", "passed": rej_delta <= REJECTION_TOLERANCE + _EPS},
    ]
    return {
        "base": base["name"],
        "candidate": cand["name"],
        "half": base["half"],
        "f05_delta": cs["word"]["all"]["f05"] - bs["word"]["all"]["f05"],
        "f05_ci": [lo, hi],
        "children_f05_delta": child_delta,
        "false_alarm_delta": far_delta,
        "rejection_delta": rej_delta,
        "base_summary": bs,
        "candidate_summary": cs,
        "checks": checks,
        "passed": all(c["passed"] for c in checks),
    }


def format_comparison(c: dict) -> str:
    b, k = c["base_summary"]["word"], c["candidate_summary"]["word"]
    rows = [f"{c['base']}  ->  {c['candidate']}   ({c['half']} half)",
            f"{'':24s} {'base':>8s} {'cand':>8s} {'diff':>8s}"]
    for name in ("all", "children", "adults"):
        rows.append(f"{'F0.5 ' + name:24s} {b[name]['f05']:8.4f} {k[name]['f05']:8.4f} "
                    f"{k[name]['f05'] - b[name]['f05']:+8.4f}")
    for key, label in (("precision", "precision"), ("recall", "recall"), ("false_alarm_rate", "false-alarm rate")):
        rows.append(f"{label:24s} {b['all'][key]:8.4f} {k['all'][key]:8.4f} {k['all'][key] - b['all'][key]:+8.4f}")
    rb, rk = c["base_summary"]["rejection_rate"], c["candidate_summary"]["rejection_rate"]
    rows.append(f"{'rejection rate':24s} {rb:8.4f} {rk:8.4f} {rk - rb:+8.4f}")
    rows.append(f"F0.5 difference, 95% CI [{c['f05_ci'][0]:+.4f}, {c['f05_ci'][1]:+.4f}] (speaker bootstrap)")
    rows.append("")
    for chk in c["checks"]:
        rows.append(f"{'PASS' if chk['passed'] else 'FAIL'}  {chk['name']:28s} {chk['value']:>20s}   ({chk['rule']})")
    rows.append("ACCEPT on conditions 1-4 (speed and tests are checked separately)" if c["passed"] else "REJECT")
    return "\n".join(rows)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m tests.benchmark.compare")
    parser.add_argument("base")
    parser.add_argument("candidate")
    parser.add_argument("--resamples", type=int, default=N_RESAMPLES)
    parser.add_argument("--json", help="also write the full comparison here")
    args = parser.parse_args(argv)

    base, cand = load_results(args.base), load_results(args.candidate)
    if "test" in (base["half"], cand["half"]) and not common.env_flag(common.UNLOCK_ENV):
        print(f"error: comparing test-half results needs {common.UNLOCK_ENV}=1", file=sys.stderr)
        return 2
    try:
        from .dataset import load_clips

        result = compare_results(base, cand, load_clips(base["half"], base.get("subset")), args.resamples)
    except NotComparable as exc:
        print(f"not comparable: {exc}", file=sys.stderr)
        return 2
    print(format_comparison(result))
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(result, fh, ensure_ascii=False, indent=2, sort_keys=True)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.benchmark.test_compare -v`
Expected: `OK` (6 tests).

- [ ] **Step 5: Commit**

```bash
git add tests/benchmark/compare.py tests/benchmark/test_compare.py
git commit -m "Add paired comparison with the precision-first acceptance rule" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 16: Human agreement reference

**Files:**
- Create: `backend/tests/benchmark/human_reference.py`
- Test: `backend/tests/benchmark/test_human_reference.py`

- [ ] **Step 1: Write the failing tests**

`backend/tests/benchmark/test_human_reference.py`:

```python
import unittest

from tests.benchmark import human_reference as H
from tests.benchmark import testutil as U

DETAIL = {
    "a": {"accuracy": [8.0, 8.0, 7.0, 9.0, 8.0], "words": [
        {"text": "CAT", "accuracy": [10.0, 10.0, 10.0, 10.0, 10.0]},
        {"text": "DOG", "accuracy": [3.0, 3.0, 3.0, 3.0, 9.0]},
    ]},
    "b": {"accuracy": [5.0, 6.0, 5.0, 4.0, 6.0], "words": [
        {"text": "SUN", "accuracy": [10.0, 9.0, 10.0, 10.0, 10.0]},
        {"text": "HAT", "accuracy": [2.0, 3.0, 2.0, 2.0, 8.0]},
    ]},
}


class TestAgreement(unittest.TestCase):
    def test_leave_one_out(self):
        result = H.annotator_agreement(DETAIL, ["a", "b"])
        f05 = [p["word_f05"] for p in result["per_annotator"]]
        # Annotators 0-3 agree with the others' median; annotator 4 misses both mistakes.
        self.assertEqual(f05, [1.0, 1.0, 1.0, 1.0, 0.0])
        self.assertAlmostEqual(result["mean"]["word_f05"], 0.8)
        self.assertEqual(result["per_annotator"][4]["recall"], 0.0)
        self.assertIsNotNone(result["per_annotator"][0]["word_pearson"])

    def test_loads_fixture(self):
        detail = H.load_detail(U.MINI_DATASET)
        self.assertEqual(sorted(detail), ["000010011", "000020022", "000030033"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.benchmark.test_human_reference -v`
Expected: ERROR, `ImportError: cannot import name 'human_reference'`.

- [ ] **Step 3: Write `human_reference.py`**

`backend/tests/benchmark/human_reference.py`:

```python
"""How well one expert agrees with the other four, on the benchmark's own word metrics.

Each annotator's word scores are treated as a "system" and scored against the median of
the other four annotators, using the same 0-6 mistake rule. The mean over annotators
shows what expert-level agreement looks like on these metrics.

    python -m tests.benchmark.human_reference --half dev
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time

from . import common
from . import metrics as M
from .dataset import find_dataset_root, find_resource, load_half

N_ANNOTATORS = 5
_KEYS = ("word_f05", "precision", "recall", "false_alarm_rate", "word_pearson", "sentence_pearson")


def load_detail(root: str) -> dict:
    with open(find_resource(root, "scores-detail.json"), encoding="utf-8") as fh:
        return json.load(fh)


def _others(scores, a):
    return statistics.median([s for i, s in enumerate(scores) if i != a])


def annotator_agreement(detail: dict, utt_ids, n_annotators: int = N_ANNOTATORS) -> dict:
    per = []
    for a in range(n_annotators):
        labels, flags, ref_scores, own_scores, sent_ref, sent_own = [], [], [], [], [], []
        for utt in utt_ids:
            entry = detail[utt]
            if len(entry.get("accuracy", [])) == n_annotators:
                sent_ref.append(_others(entry["accuracy"], a))
                sent_own.append(entry["accuracy"][a])
            for word in entry["words"]:
                scores = word["accuracy"]
                if len(scores) != n_annotators:
                    continue
                ref = _others(scores, a)
                labels.append(M.word_is_mistake(ref))
                flags.append(M.word_is_mistake(scores[a]))
                ref_scores.append(ref)
                own_scores.append(scores[a])
        c = M.confusion(labels, flags)
        per.append({
            "annotator": a,
            "words": c.n,
            "word_f05": c.f_beta(),
            "precision": c.precision,
            "recall": c.recall,
            "false_alarm_rate": c.false_alarm_rate,
            "word_pearson": M.pearson(ref_scores, own_scores),
            "sentence_pearson": M.pearson(sent_ref, sent_own),
        })
    mean = {}
    for key in _KEYS:
        values = [p[key] for p in per if p[key] is not None]
        mean[key] = sum(values) / len(values) if values else None
    return {"per_annotator": per, "mean": mean}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m tests.benchmark.human_reference")
    parser.add_argument("--half", choices=["dev", "test"], default="dev")
    args = parser.parse_args(argv)
    if args.half == "test" and not common.env_flag(common.UNLOCK_ENV):
        print(f"error: the test half needs {common.UNLOCK_ENV}=1", file=sys.stderr)
        return 2

    root = find_dataset_root()
    result = annotator_agreement(load_detail(root), [c.utt_id for c in load_half(root, args.half)])
    result.update(half=args.half, created=time.strftime("%Y-%m-%dT%H:%M:%S"))
    print(f"{'annotator':10s} {'F0.5':>7s} {'prec':>7s} {'recall':>7s} {'FAR':>7s} {'word r':>7s} {'sent r':>7s}")
    for row in result["per_annotator"] + [dict(result["mean"], annotator="mean")]:
        def fmt(v):
            return f"{v:7.4f}" if v is not None else "    n/a"
        print(f"{str(row['annotator']):10s} {fmt(row['word_f05'])} {fmt(row['precision'])} {fmt(row['recall'])} "
              f"{fmt(row['false_alarm_rate'])} {fmt(row['word_pearson'])} {fmt(row['sentence_pearson'])}")
    os.makedirs(common.results_dir(), exist_ok=True)
    out = os.path.join(common.results_dir(), f"human_reference_{args.half}.json")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(result, fh, indent=2, sort_keys=True)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.benchmark.test_human_reference -v`
Expected: `OK` (2 tests).

- [ ] **Step 5: Commit**

```bash
git add tests/benchmark/human_reference.py tests/benchmark/test_human_reference.py
git commit -m "Add annotator agreement reference for the benchmark" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 17: Speed and memory measurement

**Files:**
- Create: `backend/tests/benchmark/speed.py`
- Test: `backend/tests/benchmark/test_speed.py`

- [ ] **Step 1: Write the failing tests**

`backend/tests/benchmark/test_speed.py`:

```python
import os
import tempfile
import unittest

from tests.benchmark import speed as SP
from tests.benchmark import stage_cache as SC
from tests.benchmark import testutil as U


class TestBudget(unittest.TestCase):
    BASE = {"p95_s": 1.0, "peak_rss_mb": 2000.0}

    def test_within_budget(self):
        self.assertTrue(SP.compare_speed(self.BASE, {"p95_s": 1.09, "peak_rss_mb": 2140.0})["passed"])

    def test_too_slow(self):
        result = SP.compare_speed(self.BASE, {"p95_s": 1.11, "peak_rss_mb": 2000.0})
        self.assertFalse(result["checks"][0]["passed"])

    def test_too_much_memory(self):
        result = SP.compare_speed(self.BASE, {"p95_s": 1.0, "peak_rss_mb": 2151.0})
        self.assertFalse(result["checks"][1]["passed"])

    def test_peak_rss_is_positive(self):
        self.assertGreater(SP.peak_rss_mb(), 0)


class TestMeasure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.processor = U.real_processor_or_skip()

    def test_measure_on_fixture(self):
        from tests.benchmark.dataset import load_half

        with tempfile.TemporaryDirectory() as tmp:
            root = U.make_temp_dataset(tmp)
            clips = load_half(root, "dev")
            cache = os.path.join(tmp, "cache")
            for clip in clips:
                SC.record_clip(clip.utt_id, clip.wav_path, clip.text, cache, U.FakeOnnx(self.processor), U.FakeWords())
            result = SP.measure(clips, cache, repeats=1, extractor=U.FakeOnnxExtractor(self.processor))
        self.assertEqual(result["clips"], 2)
        self.assertGreaterEqual(result["p95_s"], result["p50_s"])
        self.assertGreater(result["p50_s"], 0)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.benchmark.test_speed -v`
Expected: ERROR, `ImportError: cannot import name 'speed'`.

- [ ] **Step 3: Write `speed.py`**

`backend/tests/benchmark/speed.py`:

```python
"""Serial latency and memory of the local pipeline, measured the same way every time.

Live ONNX plus live preprocessing, gates, alignment and scoring. Deepgram is replaced by
cached transcripts because network time is not something this project can optimize.
Run it with nothing else heavy running (no agents, no other benchmark runs).

    python -m tests.benchmark.speed --name baseline
    python -m tests.benchmark.speed --compare results/baseline_speed.json results/cand_speed.json
"""

from __future__ import annotations

import argparse
import json
import os
import time

import numpy as np

from . import common

P95_BUDGET = 1.10
RSS_BUDGET_MB = 150.0
SUBSET = "speed_dev"
REPEATS = 2


def peak_rss_mb() -> float:
    import psutil

    info = psutil.Process().memory_info()
    peak = getattr(info, "peak_wset", None)  # Windows
    if peak is not None:
        return peak / (1024 * 1024)
    import resource

    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0  # Linux reports KiB


def measure(clips, directory: str, repeats: int = REPEATS, extractor=None) -> dict:
    from .pipeline import analyze_clip, load_audio
    from .replay import CacheEntry, ReplayWordExtractor

    if extractor is None:
        from core.phoneme_extractor_onnx import PhonemeExtractorONNX

        with common.quiet():
            extractor = PhonemeExtractorONNX()
    audios = {c.utt_id: load_audio(c.wav_path) for c in clips}
    entries = {c.utt_id: CacheEntry(directory, c.utt_id) for c in clips}

    first = clips[0]
    analyze_clip(audios[first.utt_id], first.text, extractor,
                 ReplayWordExtractor(entries[first.utt_id], check_inputs=False))  # warmup

    p50s, p95s = [], []
    for _ in range(repeats):
        latencies = []
        for clip in clips:
            words = ReplayWordExtractor(entries[clip.utt_id], check_inputs=False)
            start = time.perf_counter()
            analyze_clip(audios[clip.utt_id], clip.text, extractor, words)
            latencies.append(time.perf_counter() - start)
        p50s.append(float(np.percentile(latencies, 50)))
        p95s.append(float(np.percentile(latencies, 95)))
    return {
        "clips": len(clips),
        "repeats": repeats,
        "p50_s": sum(p50s) / len(p50s),
        "p95_s": sum(p95s) / len(p95s),
        "peak_rss_mb": peak_rss_mb(),
    }


def compare_speed(base: dict, cand: dict) -> dict:
    ratio = cand["p95_s"] / base["p95_s"]
    rss_delta = cand["peak_rss_mb"] - base["peak_rss_mb"]
    checks = [
        {"name": "p95 latency", "rule": f"<= {P95_BUDGET:.2f}x baseline", "value": f"{ratio:.3f}x",
         "passed": ratio <= P95_BUDGET},
        {"name": "peak memory", "rule": f"<= +{RSS_BUDGET_MB:.0f} MB", "value": f"{rss_delta:+.1f} MB",
         "passed": rss_delta <= RSS_BUDGET_MB},
    ]
    return {"checks": checks, "passed": all(c["passed"] for c in checks)}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m tests.benchmark.speed")
    parser.add_argument("--name", default="unnamed")
    parser.add_argument("--cache", help="cache holding the Deepgram transcripts (default: from flags)")
    parser.add_argument("--flag", action="append", default=[], metavar="WWAI_NAME=VALUE")
    parser.add_argument("--subset", default=SUBSET)
    parser.add_argument("--repeats", type=int, default=REPEATS)
    parser.add_argument("--out")
    parser.add_argument("--compare", nargs=2, metavar=("BASE", "CANDIDATE"))
    args = parser.parse_args(argv)

    if args.compare:
        with open(args.compare[0], encoding="utf-8") as fh:
            base = json.load(fh)
        with open(args.compare[1], encoding="utf-8") as fh:
            cand = json.load(fh)
        result = compare_speed(base, cand)
        for chk in result["checks"]:
            print(f"{'PASS' if chk['passed'] else 'FAIL'}  {chk['name']:12s} {chk['value']:>10s}   ({chk['rule']})")
        return 0 if result["passed"] else 1

    common.apply_flags(common.parse_flag_args(args.flag))
    active = common.active_wwai_flags()
    from .dataset import load_clips
    from .stage_cache import cache_dir

    clips = load_clips("dev", args.subset)
    result = measure(clips, cache_dir("dev", args.cache or common.front_end_cache_name(active)), args.repeats)
    result.update(name=args.name, flags=active, git_sha=common.git_sha(),
                  created=time.strftime("%Y-%m-%dT%H:%M:%S"))
    os.makedirs(common.results_dir(), exist_ok=True)
    out = args.out or os.path.join(common.results_dir(), f"{args.name}_speed.json")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(result, fh, indent=2, sort_keys=True)
    print(f"p50 {result['p50_s']:.3f}s   p95 {result['p95_s']:.3f}s   peak memory {result['peak_rss_mb']:.0f} MB")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.benchmark.test_speed -v`
Expected: `OK` (5 tests).

- [ ] **Step 5: Commit**

```bash
git add tests/benchmark/speed.py tests/benchmark/test_speed.py
git commit -m "Add serial speed and memory measurement with budget check" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 18: Round 0 flag sweep

**Files:**
- Create: `backend/tests/benchmark/sweep.py`
- Test: `backend/tests/benchmark/test_sweep.py`

- [ ] **Step 1: Write the failing tests**

`backend/tests/benchmark/test_sweep.py`:

```python
import unittest

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

    def test_config_name(self):
        self.assertEqual(SW.config_name({}), "sweep_baseline")
        self.assertEqual(SW.config_name({"WWAI_WEIGHTED_PER": "1", "WWAI_G2P_STRICT": "1"}),
                         "sweep_g2p_strict+weighted_per")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.benchmark.test_sweep -v`
Expected: ERROR, `ImportError: cannot import name 'sweep'`.

- [ ] **Step 3: Write `sweep.py`**

`backend/tests/benchmark/sweep.py`:

```python
"""Round 0. Measure every default-OFF accuracy flag on the dev half, then combine greedily.

    python -m tests.benchmark.sweep
    python -m tests.benchmark.sweep --subset smoke_dev      # quick look, not for decisions

Each configuration runs in a fresh interpreter, because several flags are read at import
time. A configuration whose front-end flags need a cache that does not exist yet is
reported with the stage_cache command that builds it, then skipped.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

from . import common

CANDIDATES = (
    {"name": "gt_anchored", "flags": {"WWAI_GT_ANCHORED_ALIGNMENT": "1"}},
    {"name": "normalization", "flags": {"WWAI_PHONEME_NORMALIZATION": "1"}},
    {"name": "g2p_strict", "flags": {"WWAI_G2P_STRICT": "1"}},
    {"name": "normalization+g2p_strict", "flags": {"WWAI_PHONEME_NORMALIZATION": "1", "WWAI_G2P_STRICT": "1"}},
    {"name": "weighted_per", "flags": {"WWAI_WEIGHTED_PER": "1"}},
    {"name": "single_preprocess", "flags": {"WWAI_SINGLE_PREPROCESS": "1"}},
    {"name": "soft_quality_gates", "flags": {"WWAI_SOFT_QUALITY_GATES": "1"}},
    {"name": "chunk_preserve_pauses", "flags": {"WWAI_CHUNK_PRESERVE_PAUSES": "1"}},
)


def greedy_select(candidates, evaluate):
    """evaluate(base_flags, trial_flags) returns a compare_results dict, or None if it could not run.

    Each round tries every remaining candidate on top of what is already selected and
    keeps the passing one with the highest CI lower bound (then the highest gain).
    Returns (steps, selected_flags).
    """
    selected: dict[str, str] = {}
    remaining = list(candidates)
    steps = []
    while remaining:
        round_results = [(cand, evaluate(dict(selected), {**selected, **cand["flags"]})) for cand in remaining]
        passing = [(c, r) for c, r in round_results if r is not None and r["passed"]]
        best = max(passing, key=lambda cr: (cr[1]["f05_ci"][0], cr[1]["f05_delta"]))[0] if passing else None
        steps.append({
            "selected_before": dict(selected),
            "chosen": best["name"] if best else None,
            "results": [{
                "name": c["name"],
                "skipped": r is None,
                "passed": bool(r and r["passed"]),
                "f05_delta": r["f05_delta"] if r else None,
                "f05_ci": r["f05_ci"] if r else None,
            } for c, r in round_results],
        })
        if best is None:
            break
        selected.update(best["flags"])
        remaining = [c for c in remaining if not all(selected.get(k) == v for k, v in c["flags"].items())]
    return steps, selected


def config_name(flags: dict) -> str:
    if not flags:
        return "sweep_baseline"
    return "sweep_" + "+".join(sorted(k[len("WWAI_"):].lower() for k in flags))


def run_config(flags: dict, half: str, subset, memo: dict):
    """Run run.py for one flag set in a fresh interpreter. Returns the results path, or None."""
    key = tuple(sorted(flags.items()))
    if key in memo:
        return memo[key]
    from .run import EXIT_STALE

    name = config_name(flags)
    suffix = f"_{subset}" if subset else ""
    out = os.path.join(common.results_dir(), f"{name}_{half}{suffix}.json")
    cmd = [sys.executable, "-m", "tests.benchmark.run", "--name", name, "--half", half, "--out", out]
    for k, v in sorted(flags.items()):
        cmd += ["--flag", f"{k}={v}"]
    if subset:
        cmd += ["--subset", subset]
    env = {k: v for k, v in os.environ.items() if not (k.startswith("WWAI_") and not k.startswith("WWAI_BENCH_"))}
    env["PYTHONIOENCODING"] = "utf-8"
    print(f"  running {name} ...", flush=True)
    proc = subprocess.run(cmd, cwd=common.BACKEND_ROOT, env=env, capture_output=True, text=True, encoding="utf-8")
    if proc.returncode == EXIT_STALE:
        front = " ".join(f"--flag {k}={v}" for k, v in sorted(flags.items()) if k in common.FRONT_END_FLAGS)
        print(f"  needs a cache: python -m tests.benchmark.stage_cache --half {half} {front}")
        memo[key] = None
        return None
    if proc.returncode != 0:
        raise RuntimeError(f"run.py failed for {name}:\n{proc.stdout}\n{proc.stderr}")
    memo[key] = out
    return out


def make_evaluator(half: str, subset):
    from .compare import compare_results, load_results
    from .dataset import load_clips

    clips = load_clips(half, subset)
    memo: dict = {}

    def evaluate(base_flags, trial_flags):
        base_path = run_config(base_flags, half, subset, memo)
        trial_path = run_config(trial_flags, half, subset, memo)
        if base_path is None or trial_path is None:
            return None
        return compare_results(load_results(base_path), load_results(trial_path), clips)

    return evaluate


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m tests.benchmark.sweep")
    parser.add_argument("--subset", help="for a quick look only; acceptance uses the full dev half")
    args = parser.parse_args(argv)

    steps, selected = greedy_select(CANDIDATES, make_evaluator("dev", args.subset))
    for i, step in enumerate(steps, 1):
        print(f"\nround {i} on top of {step['selected_before'] or 'baseline'}")
        for r in step["results"]:
            if r["skipped"]:
                print(f"  {r['name']:26s} skipped (needs a cache)")
            else:
                lo, hi = r["f05_ci"]
                print(f"  {r['name']:26s} {'PASS' if r['passed'] else 'fail'}  F0.5 {r['f05_delta']:+.4f}  CI [{lo:+.4f}, {hi:+.4f}]")
        print(f"  chosen: {step['chosen']}")
    print(f"\nselected flags: {selected or 'none'}")
    suffix = f"_{args.subset}" if args.subset else ""
    out = os.path.join(common.results_dir(), f"sweep_dev{suffix}.summary.json")
    os.makedirs(common.results_dir(), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"steps": steps, "selected": selected, "git_sha": common.git_sha(),
                   "created": time.strftime("%Y-%m-%dT%H:%M:%S")}, fh, indent=2, sort_keys=True)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.benchmark.test_sweep -v`
Expected: `OK` (3 tests).

- [ ] **Step 5: Commit**

```bash
git add tests/benchmark/sweep.py tests/benchmark/test_sweep.py
git commit -m "Add Round 0 greedy flag sweep" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 19: Documentation

**Files:**
- Create: `backend/tests/benchmark/README.md`
- Modify: `backend/tests/README.md` (add a section after "Regression harness")
- Modify: `CLAUDE.md` (Development Commands, Backend block)

- [ ] **Step 1: Write `backend/tests/benchmark/README.md`**

````markdown
# speechocean762 accuracy benchmark

Measures how well Word Wiz AI's pronunciation scoring agrees with expert human judgments.
Design and reasoning are in `docs/superpowers/specs/2026-10-05-speechocean-accuracy-benchmark-design.md`.

All commands run from `backend/` with `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m ...`.

## One-time setup

```bash
python -m tests.benchmark.dataset download        # ~520 MB from OpenSLR, gitignored
python -m tests.benchmark.dataset check           # counts, audio present, no shared speakers
python -m tests.benchmark.stage_cache --half dev  # ONNX + Deepgram once per clip
python -m tests.benchmark.stage_cache --half test
```

The cache build calls Deepgram once per clip (a few dollars for both halves) and takes
roughly 10 to 20 minutes per half. Clips whose Deepgram call failed are retried with
`--retry-errors`.

## Everyday use

```bash
python -m tests.benchmark.run --name baseline                       # full dev half
python -m tests.benchmark.run --name quick --subset smoke_dev       # 250 clips, fast look
python -m tests.benchmark.run --name weighted --flag WWAI_WEIGHTED_PER=1
python -m tests.benchmark.compare tests/benchmark/results/baseline_dev.json tests/benchmark/results/weighted_dev.json
```

`compare` exits 0 only when all four accuracy conditions pass. Speed is checked
separately, by one person, with nothing else running.

```bash
python -m tests.benchmark.speed --name candidate
python -m tests.benchmark.speed --compare tests/benchmark/results/baseline_speed.json tests/benchmark/results/candidate_speed.json
```

## What counts as a mistake

| Level | Mistake | Not a mistake (flagging it is a false alarm) |
|---|---|---|
| Word | human score 0 to 6 | 7 to 10 (correct, or correct with an accent) |
| Phone | score 0 (rounded) | 1 to 2 |

The headline number is word-level F0.5 at production's own cutoff (`HIGH_PER_THRESHOLD`
in `core/phoneme_feedback_formatter.py`).

## How the cache stays honest

Each cached model call stores a hash of the exact audio the pipeline passed to the
model. Replay checks that hash on every call. If you change preprocessing, chunking or
a front-end flag, `run` stops with exit code 3 and tells you to build a new cache, so
it never scores old model outputs against new audio. Decoding, alignment, G2P, scoring
and gate changes need no new cache.

## The sealed test half

`run --half test` needs `WWAI_BENCH_UNLOCK_TEST=1` and `--reason`, and appends a line
to `test_runs.log`. Agents never unlock it. The plan is to look at it twice, once for
the original baseline and once for the final system.

## Tests

```bash
python -m unittest discover -s tests/benchmark -t . -v
```
````

- [ ] **Step 2: Add a section to `backend/tests/README.md`** directly after the "Regression harness" section:

````markdown

## Accuracy benchmark

`benchmark/` scores the pipeline against expert labels from speechocean762, a public
dataset of children and adults reading English. Where the regression harness tells you
whether numbers moved, this tells you whether they got better.

```bash
PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m tests.benchmark.run --name baseline
```

Setup, commands and the acceptance rule are in [`benchmark/README.md`](benchmark/README.md).
````

- [ ] **Step 3: Add the benchmark commands to `CLAUDE.md`**, in the "Backend (from `/backend`)" code block, after the system tests line:

```bash
python -m tests.benchmark.run --name <config>           # Accuracy benchmark (see tests/benchmark/README.md)
python -m tests.benchmark.compare <base.json> <cand.json>  # Accept/reject a change
```

- [ ] **Step 4: Run every benchmark test**

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest discover -s tests/benchmark -t . -v`
Expected: `OK`, roughly 100 tests and no failures. If discovery reports `ImportError: Start directory is not importable`, run the modules explicitly instead: `-m unittest tests.benchmark.test_common tests.benchmark.test_metrics tests.benchmark.test_phones tests.benchmark.test_dataset tests.benchmark.test_pipeline tests.benchmark.test_stage_cache tests.benchmark.test_replay tests.benchmark.test_scoring tests.benchmark.test_run tests.benchmark.test_compare tests.benchmark.test_human_reference tests.benchmark.test_speed tests.benchmark.test_sweep`, and put that command in the README instead.

- [ ] **Step 5: Commit**

```bash
git add tests/benchmark/README.md tests/README.md ../CLAUDE.md
git commit -m "Document the accuracy benchmark" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 20: Real data download, check and subsets

**Files:**
- Create: `backend/tests/benchmark/subsets/smoke_dev.txt`, `backend/tests/benchmark/subsets/speed_dev.txt`

- [ ] **Step 1: Download**

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m tests.benchmark.dataset download`
Expected: progress to 100%, then `Dataset ready at ...tests/benchmark/data/speechocean762` (or `.../data` if the archive has no top folder).

- [ ] **Step 2: Check**

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m tests.benchmark.dataset check`
Expected: `dev_clips 2500`, `test_clips 2500`, `dev_speakers 125`, `test_speakers 125`, children counts near half, `0 problem(s)`.
If the layout differs from the fixture (for example `scores.json` sits somewhere other than the root or `resource/`, or `wav.scp` paths are formatted differently), fix `find_resource` or `load_half`, mirror the real layout in `fixtures/mini_speechocean`, rerun `tests.benchmark.test_dataset`, and commit that fix separately. If `check` reports text-token mismatches, print a few and decide with Bruce whether to drop those clips, before going further.

- [ ] **Step 3: Create the fixed subsets**

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m tests.benchmark.dataset make-subsets`
Expected: `wrote ...subsets/smoke_dev.txt` and `wrote ...subsets/speed_dev.txt`. Check them with `wc -l tests/benchmark/subsets/*.txt`, which should show 250 and 200.

- [ ] **Step 4: Commit**

```bash
git add tests/benchmark/subsets
git commit -m "Add fixed smoke and speed subsets of the dev half" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 21: Build the caches

This task spends Deepgram credit (a few dollars in total, approved in the spec). Do the small run first.

- [ ] **Step 1: Five-clip trial**

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m tests.benchmark.stage_cache --half dev --limit 5 --workers 2`
Expected: `5 clips, 0 cached, 5 to record`, then a JSON summary with `"word_errors": []` and exit code 0. Look at one entry with `head -c 600 tests/benchmark/cache/dev/baseline/<utt>.json` and confirm `phoneme_calls` has a `logits_key` and `word_calls` has a real word list.

- [ ] **Step 2: Full dev half**

Run (in the background, it takes a while): `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m tests.benchmark.stage_cache --half dev --workers 6`
Expected: progress lines every 50 clips and a final summary. If `word_errors` is not empty, run again with `--retry-errors` until it is empty or the same few clips keep failing. Write down any clips that keep failing. Those get scored as rejections, which matches what production does.

- [ ] **Step 3: Full test half** (records model outputs only and computes no scores)

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m tests.benchmark.stage_cache --half test --workers 6`
Expected: same as Step 2. Retry errors the same way.

Nothing to commit (caches are gitignored).

---

### Task 22: Replay matches a live run on real clips

**Files:**
- Create: `backend/tests/benchmark/test_live_parity.py`

- [ ] **Step 1: Write the parity test** (skips when the data, cache or model is missing)

`backend/tests/benchmark/test_live_parity.py`:

```python
"""Replay of the real dev cache equals a live ONNX run on the same clips.

Skips unless the dataset, the dev baseline cache and the ONNX model are all present.
"""

import os
import unittest

from tests.benchmark import common
from tests.benchmark import pipeline as PL

N_CLIPS = 10


class TestLiveParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from tests.benchmark.dataset import load_clips
            from tests.benchmark.replay import load_processor
            from tests.benchmark.stage_cache import cache_dir
            from core.phoneme_extractor_onnx import PhonemeExtractorONNX

            cls.clips = load_clips("dev", "smoke_dev")[:N_CLIPS]
            cls.directory = cache_dir("dev", "baseline")
            if not os.path.isdir(cls.directory):
                raise FileNotFoundError(cls.directory)
            with common.quiet():
                cls.live = PhonemeExtractorONNX()
                cls.processor = load_processor()
        except Exception as exc:  # noqa: BLE001
            raise unittest.SkipTest(f"real data, cache or model unavailable: {exc}")

    def test_replay_equals_live(self):
        from tests.benchmark.replay import CacheEntry, ReplayPhonemeExtractor, ReplayWordExtractor

        for clip in self.clips:
            with self.subTest(utt=clip.utt_id):
                audio = PL.load_audio(clip.wav_path)
                live = PL.analyze_clip(audio, clip.text, self.live, ReplayWordExtractor(CacheEntry(self.directory, clip.utt_id)))
                entry = CacheEntry(self.directory, clip.utt_id)
                replay = PL.analyze_clip(audio, clip.text, ReplayPhonemeExtractor(entry, self.processor), ReplayWordExtractor(entry))
                self.assertEqual(replay.to_dict(), live.to_dict())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it**

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.benchmark.test_live_parity -v`
Expected: `OK` (1 test, 10 subtests, not skipped). A failure means replay does not reproduce production. Stop and debug with superpowers:systematic-debugging before recording any baseline.

- [ ] **Step 3: Commit**

```bash
git add tests/benchmark/test_live_parity.py
git commit -m "Check that cache replay matches a live ONNX run on real clips" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 23: Record the dev baseline

- [ ] **Step 1: Baseline run**

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m tests.benchmark.run --name baseline`
Expected: a summary table (clips 2500, word F0.5 for all/children/adults, best threshold, Pearson values, rejection breakdown) and `wrote .../results/baseline_dev.json`.

- [ ] **Step 2: Determinism check**

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m tests.benchmark.run --name baseline_repeat`
Then:

```bash
PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -c "
import json, sys
a, b = (json.load(open(p, encoding='utf-8')) for p in sys.argv[1:3])
for d in (a, b):
    for k in ('name', 'created', 'seconds', 'git_sha'):
        d.pop(k, None)
print('IDENTICAL' if a == b else 'DIFFERENT')
" tests/benchmark/results/baseline_dev.json tests/benchmark/results/baseline_repeat_dev.json
```

Expected: `IDENTICAL`. If `DIFFERENT`, find the source of nondeterminism with superpowers:systematic-debugging and fix it before going further (spec, "Determinism precondition").

- [ ] **Step 3: Speed baseline** (close other heavy programs first)

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m tests.benchmark.speed --name baseline`
Expected: `p50 ...s   p95 ...s   peak memory ... MB` and `wrote .../results/baseline_speed.json`.

- [ ] **Step 4: Human agreement reference**

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m tests.benchmark.human_reference --half dev`
Expected: a five-row table plus a mean row, and `wrote .../results/human_reference_dev.json`.

- [ ] **Step 5: Commit the baseline**

```bash
git add tests/benchmark/results/baseline_dev.json tests/benchmark/results/baseline_dev.summary.json tests/benchmark/results/baseline_speed.json tests/benchmark/results/human_reference_dev.json
git commit -m "Record the speechocean762 dev-half baseline" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 24: Full verification

- [ ] **Step 1: Every backend unit test touched by this plan, plus the regression harness**

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest discover -s tests/benchmark -t . -v`
Expected: `OK`.

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.test_clean_sentence tests.test_request_audio tests.test_feedback_threshold tests.test_onnx_logits_split tests.test_onnx_pin_wiring tests.test_soft_quality_gates tests.test_single_preprocess tests.test_phoneme_inventory tests.test_grapheme_to_phoneme tests.test_gt_anchored_alignment tests.test_weighted_per tests.regression.test_regression -v`
Expected: `OK` (skips allowed, no failures or errors).

- [ ] **Step 2: Request a code review** with superpowers:requesting-code-review against the spec and this plan.

- [ ] **Step 3: Report to Bruce** with the baseline table (word F0.5 overall, children, adults, false-alarm rate, rejection rate and its breakdown), the human agreement mean, the speed baseline and anything surprising, such as a high rejection rate from the hard quality gates or a high G2P disagreement rate. Those findings feed straight into Plan 2 (the agent-round runbook) and the Round 0 sweep.

---

## Next: Plan 2 (written after Task 23)

Plan 2 covers running `sweep.py` and merging what passes, removing the 11 stale worktrees in `.claude/worktrees/` after checking they hold no unmerged work, the six agent prompts (built from the baseline findings), the review gate procedure, and the week-4 freeze with one unlocked test-half run and `BENCHMARK.md`.
