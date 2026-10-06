"""Run the slow, deterministic stages once per clip and save what the models returned.

For every model call the production pipeline makes on a clip, this records a hash of
the exact input plus the model's output. For the phoneme model that is the tensor fed to
the ONNX session (after the extractor's own validation, trimming and feature extraction)
and the raw logits. For Deepgram it is the audio passed to extract_words and the word
list. replay.py feeds those back and raises StaleCacheError if the current code would
pass either model a different input.

Gates are not applied while recording, so every clip has model outputs. run.py applies
the gates at scoring time, which lets gate flags change without a new cache.

    python -m tests.benchmark.stage_cache --half dev
    python -m tests.benchmark.stage_cache --half dev --flag WWAI_SINGLE_PREPROCESS=1
    python -m tests.benchmark.stage_cache --half dev --retry-errors

The exit code is 1 while any clip needs recording again (see entry_needs_retry).
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import hashlib
import json
import logging
import os
import re
import sys
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from concurrent.futures.process import BrokenProcessPool
from multiprocessing import get_context

import numpy as np

from . import common

CACHE_META = "_cache_meta.json"
#: If this many clips complete first and every one needs a word retry, Deepgram is down or
#: the key is wrong, and recording the rest would only spend time.
EARLY_ABORT_CLIPS = 20
#: How core.word_extractor reads WWAI_ASR_FALLBACK.
_ASR_FALLBACK_TRUTHY = {"1", "true", "t", "yes", "y", "on"}
_COMMIT_SHA = re.compile(r"[0-9a-f]{40}")
_models: dict = {}


def audio_sha(audio, sampling_rate) -> str:
    digest = hashlib.sha1()
    digest.update(np.ascontiguousarray(audio, dtype=np.float32).tobytes())
    digest.update(str(int(sampling_rate)).encode())
    return digest.hexdigest()


def cache_dir(half: str, name: str) -> str:
    return os.path.join(common.cache_root(), half, name)


def _atomic_write(path: str, write, binary: bool = False) -> None:
    """Write through a temporary file next to ``path`` and move it into place, so a crash or a
    full disk never leaves a partial file under the real name, or a temporary file behind."""
    tmp = path + ".tmp"
    try:
        with (open(tmp, "wb") if binary else open(tmp, "w", encoding="utf-8")) as fh:
            write(fh)
        os.replace(tmp, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.remove(tmp)
        raise


def _remove(path: str) -> None:
    with contextlib.suppress(FileNotFoundError):
        os.remove(path)


def read_entry(path: str) -> dict:
    """Load a cache entry. Raises ValueError when it is not valid JSON or lacks its call lists."""
    with open(path, encoding="utf-8") as fh:
        meta = json.load(fh)  # JSONDecodeError and UnicodeDecodeError are ValueErrors
    if not isinstance(meta, dict) or not all(
        isinstance(meta.get(key), list) for key in ("phoneme_calls", "word_calls")
    ):
        raise ValueError("it has no phoneme_calls and word_calls lists")
    return meta


def model_input_sha(values) -> str:
    """sha1 of the exact tensor fed to the ONNX session (dtype and shape included)."""
    arr = np.ascontiguousarray(values)
    digest = hashlib.sha1(arr.tobytes())
    digest.update(f"{arr.dtype}|{arr.shape}".encode())
    return digest.hexdigest()


class RecordingSession:
    """Stands in for PhonemeExtractorONNX.session for one clip and records every run().

    Errors the extractor raises before it runs the model (audio too short or silent) are not
    session calls and are not recorded. Replay runs the same extractor code, so they recur.
    """

    def __init__(self, inner):
        self._inner = inner
        self.calls: list[dict] = []
        self.logits: list[np.ndarray] = []

    def get_inputs(self):
        return self._inner.get_inputs()

    def run(self, output_names, feeds):
        values = next(iter(feeds.values()))
        call = {"input_sha": model_input_sha(values)}
        self.calls.append(call)
        try:
            outputs = self._inner.run(output_names, feeds)
        except Exception as exc:
            call.update(error_type=type(exc).__name__, error=str(exc),
                        is_value_error=isinstance(exc, ValueError))
            raise
        call["logits_key"] = f"logits_{len(self.logits)}"
        self.logits.append(np.asarray(outputs[0], dtype=np.float32))
        return outputs


class _AsrFailureCapture(logging.Handler):
    """Collects the structured payloads core.word_extractor attaches to its log records.

    With default flags WordExtractorOnline returns [] for an outage and for a genuine empty
    transcript alike. Only the ``wwai`` payload on its log record tells them apart.
    """

    def __init__(self):
        super().__init__()
        self.payloads: list[dict] = []

    def emit(self, record):
        payload = getattr(record, "wwai", None)
        if isinstance(payload, dict):
            self.payloads.append(payload)

    def last_final_failure(self) -> dict | None:
        failures = [p["final_failure"] for p in self.payloads if isinstance(p.get("final_failure"), dict)]
        return failures[-1] if failures else None


class RecordingWordExtractor:
    """Wraps the word extractor (Deepgram) and records every call's words or error.

    When the extractor logs a final failure, the call also gets ``asr_failure`` (code,
    category, retryable) so entry_has_word_error can tell an outage from an empty transcript.
    """

    def __init__(self, inner):
        self.inner = inner
        self.calls: list[dict] = []

    def extract_words(self, audio, sampling_rate=16000, **_kwargs):
        call = {"input_sha": audio_sha(audio, sampling_rate)}
        self.calls.append(call)
        capture = _AsrFailureCapture()
        word_logger = logging.getLogger("core.word_extractor")
        word_logger.addHandler(capture)
        try:
            words = self.inner.extract_words(audio, sampling_rate=sampling_rate)
        except Exception as exc:
            call.update(error_type=type(exc).__name__, error=str(exc), is_value_error=isinstance(exc, ValueError))
            raise
        finally:
            word_logger.removeHandler(capture)
            failure = capture.last_final_failure()
            if failure is not None:
                call["asr_failure"] = {
                    "code": failure.get("code"),
                    "category": failure.get("category"),
                    "retryable": bool(failure.get("retryable")),
                }
        call["words"] = None if words is None else [str(w) for w in words]
        return words


def entry_has_word_error(meta: dict) -> bool:
    """True when a word call raised, or came back empty after a retryable failure (an outage).

    Deepgram genuinely returns an empty transcript for some young children's speech; those
    are real outcomes and are kept, not retried.
    """
    for call in meta.get("word_calls", []):
        if "error_type" in call:
            return True
        failure = call.get("asr_failure") or {}
        if not call.get("words") and failure.get("retryable"):
            return True
    return False


def entry_needs_retry(meta: dict) -> bool:
    """A cached clip worth recording again: a retryable word failure, an ONNX session error
    that was not a ValueError (memory or runtime failures are usually transient), or an
    outcome the pipeline flagged as unexpected."""
    if entry_has_word_error(meta):
        return True
    for call in meta.get("phoneme_calls", []):
        if "error_type" in call and not call.get("is_value_error"):
            return True
    error_type = (meta.get("outcome") or {}).get("error_type") or ""
    return error_type.startswith("unexpected:")


def write_entry(directory, utt_id, session: RecordingSession, words: RecordingWordExtractor,
                outcome, seconds: float) -> dict:
    os.makedirs(directory, exist_ok=True)
    json_path = os.path.join(directory, f"{utt_id}.json")
    npz_path = os.path.join(directory, f"{utt_id}.npz")
    # A clip recorded again loses its old .json first, so a crash part way through can never
    # leave the old entry next to new logits. The clip then has no entry and is recorded next run.
    _remove(json_path)
    if session.logits:
        arrays = {f"logits_{i}": arr for i, arr in enumerate(session.logits)}
        _atomic_write(npz_path, lambda fh: np.savez(fh, **arrays), binary=True)
    else:
        _remove(npz_path)
    meta = {
        "utt_id": utt_id,
        "phoneme_calls": session.calls,
        "word_calls": words.calls,
        "outcome": {"status": outcome.status, "error_type": outcome.error_type, "error": outcome.error},
        "git_sha": common.git_sha(),
        "seconds": round(seconds, 3),
    }
    # Written last: the .json marks the entry complete.
    _atomic_write(json_path, lambda fh: json.dump(meta, fh, ensure_ascii=False))
    return meta


def record_clip(utt_id, wav_path, text, directory, phoneme_extractor, word_inner) -> dict:
    """Record one clip with the given models. Returns the entry it wrote.

    ``phoneme_extractor`` is a real PhonemeExtractorONNX (or a test double with the same
    attributes). It is shared between clips and never modified: the clip runs on a shallow
    copy whose session records every call.
    """
    from .pipeline import analyze_clip, load_audio

    view = copy.copy(phoneme_extractor)
    view.session = session = RecordingSession(phoneme_extractor.session)
    words = RecordingWordExtractor(word_inner)
    start = time.perf_counter()
    outcome = analyze_clip(load_audio(wav_path), text, view, words, apply_gates=False)
    return write_entry(directory, utt_id, session, words, outcome, time.perf_counter() - start)


def write_meta(directory: str, half: str, name: str, flags: dict) -> dict:
    """Write the cache's _cache_meta.json, or check the existing one against this run.

    A cache holds the outputs of one model revision under one set of flags. The revision must
    be a commit SHA (not None from WWAI_IGNORE_MODEL_PINS, not a branch like "main"), or the
    cache could not say which model made it.
    """
    from core.model_registry import repo_id, resolve_revision

    revision = resolve_revision("PHONEME_IPA_ONNX")
    if not (isinstance(revision, str) and _COMMIT_SHA.fullmatch(revision)):
        raise SystemExit(
            f"the phoneme model revision is {revision!r}, not a 40-character commit SHA "
            "(check WWAI_IGNORE_MODEL_PINS and WWAI_PIN_PHONEME_IPA_ONNX)"
        )
    path = os.path.join(directory, CACHE_META)
    meta = {
        "half": half,
        "name": name,
        "model_repo": repo_id("PHONEME_IPA_ONNX"),
        "model_revision": revision,
        "flags": flags,
        "git_sha": common.git_sha(),
        "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    if os.path.isfile(path):
        try:
            with open(path, encoding="utf-8") as fh:
                existing = json.load(fh)
        except ValueError as exc:
            raise SystemExit(f"{path} is not valid JSON ({exc}). Use a new --name.") from exc
        if existing.get("model_revision") != revision:
            raise SystemExit(
                f"{directory} was built with model revision {existing.get('model_revision')}, "
                f"current is {revision}. Use a new --name."
            )
        cached_flags = existing.get("flags") or {}
        differing = sorted(k for k in set(cached_flags) | set(flags) if cached_flags.get(k) != flags.get(k))
        if differing:
            raise SystemExit(
                f"{directory} was built with different flags ({', '.join(differing)}). Use a new --name."
            )
        return existing
    os.makedirs(directory, exist_ok=True)
    _atomic_write(path, lambda fh: json.dump(meta, fh, indent=2, sort_keys=True))
    return meta


def _load_deepgram_key() -> None:
    """Load only DEEPGRAM_KEY from backend/.env, never any WWAI_* flag that might be there."""
    if os.getenv("DEEPGRAM_KEY"):
        return
    from dotenv import dotenv_values

    key = dotenv_values(os.path.join(common.BACKEND_ROOT, ".env")).get("DEEPGRAM_KEY")
    if key:
        os.environ["DEEPGRAM_KEY"] = key


_init_error: str | None = None


def _init_worker() -> None:
    """Load the models once per worker.

    An initializer that raises only breaks the pool with a generic BrokenProcessPool and loses
    the cause. The failure is recorded here instead, and the first task raises it with its cause.
    """
    global _init_error
    _init_error = None
    try:
        _load_deepgram_key()
        with common.quiet():
            from core.phoneme_extractor_onnx import PhonemeExtractorONNX
            from core.word_extractor import WordExtractorOnline

            _models["phoneme"] = PhonemeExtractorONNX()
            _models["words"] = WordExtractorOnline()
    except Exception as exc:  # noqa: BLE001 - reported by the first task instead of hanging the pool
        _init_error = f"{type(exc).__name__}: {exc}"


def _record_task(task):
    if _init_error is not None:
        raise RuntimeError(f"benchmark worker could not load its models: {_init_error}")
    utt_id, wav_path, text, directory = task
    return record_clip(utt_id, wav_path, text, directory, _models["phoneme"], _models["words"])


def _record_all(todo, workers):
    """Record every task in worker processes and yield each entry as it completes.

    A worker that dies hard (an access violation, an OOM kill) raises BrokenProcessPool here
    instead of hanging the run. When the caller stops early, or a task fails, the tasks that
    have not started are cancelled.
    """
    # Workers inherit this. Under WWAI_BENCH_VERBOSE with redirected output, the pipeline's emoji
    # prints would otherwise raise UnicodeEncodeError, a ValueError that counts as a rejection.
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    with ProcessPoolExecutor(max_workers=workers, mp_context=get_context("spawn"),
                             initializer=_init_worker) as pool:
        futures = [pool.submit(_record_task, task) for task in todo]
        try:
            for future in as_completed(futures):
                yield future.result()
        finally:
            pool.shutdown(wait=False, cancel_futures=True)


def build(half, name, flags, workers, retry_errors=False, subset=None, limit=None) -> dict:
    """Record every clip that has no entry yet (with retry_errors, also those that need a retry).

    The summary counts the outcomes recorded in this run by status and by error type.
    ``needs_retry`` lists the clips recorded in this run that need a retry, plus cached
    clips that need one but were skipped because retry_errors was off.
    """
    from contextlib import closing

    from .dataset import load_clips

    clips = load_clips(half, subset)
    if limit:
        clips = clips[:limit]
    directory = cache_dir(half, name)
    write_meta(directory, half, name, flags)
    todo, needs_retry = [], []
    for clip in clips:
        meta_path = os.path.join(directory, f"{clip.utt_id}.json")
        if os.path.isfile(meta_path):
            try:
                cached = read_entry(meta_path)
            except ValueError:
                cached = None  # unreadable, so it is recorded again like a missing entry
            if cached is not None:
                if not entry_needs_retry(cached):
                    continue
                if not retry_errors:
                    needs_retry.append(clip.utt_id)
                    continue
        todo.append((clip.utt_id, clip.wav_path, clip.text, directory))
    print(f"{len(clips)} clips, {len(clips) - len(todo)} cached, {len(todo)} to record into {directory}")
    if needs_retry:
        print(f"{len(needs_retry)} cached clips need recording again; run with --retry-errors")

    statuses = {"ok": 0, "rejected": 0}
    error_types: Counter = Counter()
    word_errors = []
    if todo:
        _load_deepgram_key()  # fail fast here for the common case, before any worker starts
        if not os.getenv("DEEPGRAM_KEY"):
            raise SystemExit("DEEPGRAM_KEY is not set (environment or backend/.env)")
        i = 0
        with closing(_record_all(todo, workers)) as entries:
            try:
                for i, entry in enumerate(entries, 1):
                    outcome = entry["outcome"]
                    statuses[outcome["status"]] += 1
                    if outcome["error_type"]:
                        error_types[outcome["error_type"]] += 1
                    if entry_has_word_error(entry):
                        word_errors.append(entry["utt_id"])
                    if entry_needs_retry(entry):
                        needs_retry.append(entry["utt_id"])
                    if i == EARLY_ABORT_CLIPS and len(word_errors) == i:
                        raise SystemExit(
                            f"Deepgram failed for every one of the first {i} clips; check the key and balance"
                        )
                    if i % 50 == 0 or i == len(todo):
                        print(f"  {i}/{len(todo)} recorded ({len(needs_retry)} need a retry)")
            except BrokenProcessPool as exc:
                raise SystemExit(
                    f"a worker process died ({exc}), probably out of memory; the {i} entries recorded "
                    "in this run are kept, so run the same command again (with fewer --workers) to continue"
                ) from exc
    return {
        "cache": directory,
        "recorded": len(todo),
        "statuses": statuses,
        "error_types": dict(sorted(error_types.items())),
        "word_errors": sorted(word_errors),
        "needs_retry": sorted(needs_retry),
    }


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

    dotenv_keys = common.dotenv_wwai_keys()
    if dotenv_keys:
        print(
            f"error: backend/.env sets {', '.join(dotenv_keys)}; "
            "remove them and pass flags with --flag so they are recorded",
            file=sys.stderr,
        )
        return 2

    flags = common.parse_flag_args(args.flag)
    fallback = flags.get("WWAI_ASR_FALLBACK", os.environ.get("WWAI_ASR_FALLBACK", ""))
    if fallback.strip().lower() in _ASR_FALLBACK_TRUTHY:
        print(
            "error: WWAI_ASR_FALLBACK is on. It loads a second 1.2 GB wav2vec2 model in every worker, "
            "and it changes the recorded words without changing the cache name. Unset it.",
            file=sys.stderr,
        )
        return 2
    common.apply_flags(flags)
    active = common.active_wwai_flags()
    name = args.name or common.front_end_cache_name(active)
    summary = build(args.half, name, active, args.workers, args.retry_errors, args.subset, args.limit)
    print(json.dumps(summary, indent=2))
    return 1 if summary["needs_retry"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
