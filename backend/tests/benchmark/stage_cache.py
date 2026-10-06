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
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import logging
import os
import sys
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


def write_entry(directory, utt_id, session: RecordingSession, words: RecordingWordExtractor,
                recorded_status: str, seconds: float) -> None:
    os.makedirs(directory, exist_ok=True)
    if session.logits:
        np.savez(os.path.join(directory, f"{utt_id}.npz"),
                 **{f"logits_{i}": arr for i, arr in enumerate(session.logits)})
    meta = {
        "utt_id": utt_id,
        "phoneme_calls": session.calls,
        "word_calls": words.calls,
        "recorded_status": recorded_status,
        "seconds": round(seconds, 3),
    }
    tmp = os.path.join(directory, f"{utt_id}.json.tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False)
    os.replace(tmp, os.path.join(directory, f"{utt_id}.json"))  # the .json marks the entry complete


def record_clip(utt_id, wav_path, text, directory, phoneme_extractor, word_inner):
    """Record one clip with the given models. Returns (utt_id, status, word_error).

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
    write_entry(directory, utt_id, session, words, outcome.status, time.perf_counter() - start)
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


_init_error: str | None = None


def _init_worker() -> None:
    """Load the models once per worker.

    An initializer that raises makes multiprocessing.Pool respawn the worker forever, so
    imap_unordered never returns. The failure is recorded here and raised by the first task.
    """
    global _init_error
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
        _load_deepgram_key()  # fail fast here for the common case, before any worker starts
        if not os.getenv("DEEPGRAM_KEY"):
            raise SystemExit("DEEPGRAM_KEY is not set (environment or backend/.env)")
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

    dotenv_keys = common.dotenv_wwai_keys()
    if dotenv_keys:
        print(
            f"error: backend/.env sets {', '.join(dotenv_keys)}; "
            "remove them and pass flags with --flag so they are recorded",
            file=sys.stderr,
        )
        return 2

    common.apply_flags(common.parse_flag_args(args.flag))
    active = common.active_wwai_flags()
    name = args.name or common.front_end_cache_name(active)
    summary = build(args.half, name, active, args.workers, args.retry_errors, args.subset, args.limit)
    print(json.dumps(summary, indent=2))
    return 1 if summary["word_errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
