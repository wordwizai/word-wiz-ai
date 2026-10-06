"""Score one configuration against speechocean762 using cached model outputs.

    python -m tests.benchmark.run --name baseline
    python -m tests.benchmark.run --name weighted --flag WWAI_WEIGHTED_PER=1
    python -m tests.benchmark.run --name quick --subset smoke_dev

The test half needs WWAI_BENCH_UNLOCK_TEST=1, --reason and a clean git tree (every look
has to be reproducible from its recorded SHA), and every such run that gets as far as
scoring is appended to test_runs.log. A results file that git tracks, such as the committed
baseline, is only overwritten with --force. Exit codes are 0 for ok, 2 for a usage error or
a locked half, 3 for a stale or missing cache, and 4 when clips failed with unexpected
errors (the results are still written so the failures can be inspected).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context

from . import common

EXIT_STALE = 3
EXIT_UNEXPECTED = 4
_NAME = re.compile(r"[\w.\-]+")
_worker: dict = {}
_init_error: str | None = None


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


def _one_line(text) -> str:
    """Collapse tabs, newlines and runs of spaces so free text cannot break the TSV."""
    return " ".join(str(text).split())


def append_ledger(name: str, reason: str, sha: str, path: str | None = None, flags=None, threshold=None) -> None:
    """Append one look at the test half: time, sha, name, reason, active flags (JSON) and threshold."""
    path = path or common.TEST_RUNS_LOG  # looked up here, so patching common.TEST_RUNS_LOG redirects it
    flags_json = json.dumps(flags or {}, sort_keys=True, separators=(",", ":"))
    shown = "" if threshold is None else str(threshold)
    with open(path, "a", encoding="utf-8", newline="\n") as fh:
        fh.write("\t".join([time.strftime("%Y-%m-%dT%H:%M:%S"), _one_line(sha), _one_line(name),
                            _one_line(reason), flags_json, shown]) + "\n")


def production_threshold() -> float:
    from core.phoneme_feedback_formatter import HIGH_PER_THRESHOLD

    return float(HIGH_PER_THRESHOLD)


def check_cache(directory: str, half: str | None = None) -> dict:
    """The cache's metadata, or StaleCacheError when it is missing, unreadable, built for another
    half than ``half`` or built with another model revision than the current pin."""
    from .stage_cache import CACHE_META

    meta_path = os.path.join(directory, CACHE_META)
    if not os.path.isfile(meta_path):
        raise common.StaleCacheError(f"no cache at {directory}; build it with tests.benchmark.stage_cache")
    try:
        with open(meta_path, encoding="utf-8") as fh:
            meta = json.load(fh)
        if not isinstance(meta, dict):
            raise ValueError("not a JSON object")
    except ValueError as exc:
        raise common.StaleCacheError(f"{meta_path} is unreadable ({exc}); rebuild the cache") from exc
    if half is not None and meta.get("half") != half:
        raise common.StaleCacheError(
            f"cache at {directory} was built for the {meta.get('half')} half, not the {half} half"
        )
    from core.model_registry import resolve_revision

    current = resolve_revision("PHONEME_IPA_ONNX")
    if meta.get("model_revision") != current:
        raise common.StaleCacheError(
            f"cache was built with model revision {meta.get('model_revision')}, current is {current}"
        )
    return meta


def _init_worker() -> None:
    """Load the processor once per worker.

    An initializer that raises only breaks the pool with a generic BrokenProcessPool and loses
    the cause. The failure is recorded here instead, and the first task raises it with its cause.
    """
    global _init_error
    _init_error = None
    try:
        with common.quiet():
            from .replay import load_processor

            _worker["processor"] = load_processor()
    except Exception as exc:  # noqa: BLE001 - reported by the first task, see the docstring
        _init_error = f"{type(exc).__name__}: {exc}"


def _score_task(task):
    if _init_error is not None:
        raise RuntimeError(f"benchmark worker could not load the wav2vec2 processor: {_init_error}")
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
        # Workers inherit this. Under WWAI_BENCH_VERBOSE with redirected output, the pipeline's emoji
        # prints would otherwise raise UnicodeEncodeError, a ValueError that counts as a rejection.
        os.environ.setdefault("PYTHONIOENCODING", "utf-8")
        # A worker that dies hard raises BrokenProcessPool here instead of hanging. A task that
        # raises (StaleCacheError, a failed initializer) stops the run, and map() cancels the rest.
        with ProcessPoolExecutor(max_workers=workers, mp_context=get_context("spawn"),
                                 initializer=_init_worker) as pool:
            for utt_id, outcome in pool.map(_score_task, tasks, chunksize=8):
                outcomes[utt_id] = outcome
    return dict(sorted(outcomes.items()))


def summary_path(out_path: str) -> str:
    base = out_path[:-5] if out_path.endswith(".json") else out_path
    return base + ".summary.json"


def _tracked_by_git(path: str) -> bool:
    """True when git tracks this file. A file outside the repository, or no git at all, is not tracked."""
    try:
        done = subprocess.run(["git", "ls-files", "--error-unmatch", os.path.abspath(path)],
                              cwd=common.REPO_ROOT, capture_output=True)
    except OSError:
        return False
    return done.returncode == 0


def write_results(results: dict, out_path: str) -> tuple[str, str]:
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(results, fh, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    short = summary_path(out_path)
    with open(short, "w", encoding="utf-8", newline="\n") as fh:
        json.dump({k: v for k, v in results.items() if k != "outcomes"}, fh,
                  ensure_ascii=False, sort_keys=True, indent=2)
    return out_path, short


def format_summary(summary: dict) -> str:
    lines = [
        f"clips {summary['clips']}   rejected {summary['rejected']} ({summary['rejection_rate']:.1%})   "
        f"word-count mismatches {summary['word_count_mismatch']}   unscored {summary['unscored_rate']:.1%}   "
        f"threshold {summary['threshold']}",
    ]
    if summary["unexpected_failures"] > 0:
        lines.append(f"unexpected failures {summary['unexpected_failures']}")
    lines.append(f"{'word':10s} {'F0.5':>7s} {'prec':>7s} {'recall':>7s} {'FAR':>7s} {'n':>7s}")
    for name in ("all", "children", "adults"):
        m = summary["word"][name]
        lines.append(f"{name:10s} {m['f05']:7.4f} {m['precision']:7.4f} {m['recall']:7.4f} "
                     f"{m['false_alarm_rate']:7.4f} {m['n']:7d}")
    best = summary["best_threshold"]
    lines.append(f"best threshold on this half {best['threshold']} (F0.5 {best['f05']:.4f}), "
                 f"flagging every word {summary['flag_all_f05']:.4f}")
    lines.append("pearson  " + "  ".join(
        f"{k} {v:.3f}" if v is not None else f"{k} n/a" for k, v in summary["pearson"].items()))
    g2p = summary["g2p_disagreement_rate"]
    lines.append(f"g2p disagreement {'n/a' if g2p is None else format(g2p, '.1%')}   "
                 f"rejected by type {summary['rejected_by_type']}")
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
    parser.add_argument("--force", action="store_true", help="overwrite a results file that git tracks")
    args = parser.parse_args(argv)

    # core loads backend/.env on import, so WWAI_* flags set there would apply without being recorded.
    dotenv_keys = common.dotenv_wwai_keys()
    if dotenv_keys:
        print(f"error: backend/.env sets {', '.join(dotenv_keys)}; "
              "remove them and pass flags with --flag so they are recorded", file=sys.stderr)
        return 2

    try:
        flags = common.parse_flag_args(args.flag)
        check_test_unlock(args.half, args.reason)
    except (ValueError, PermissionError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    for option, value in (("--name", args.name), ("--cache", args.cache)):
        if value is not None and not _NAME.fullmatch(value):
            print(f"error: {option} {value!r} may only contain letters, digits, _ . and -", file=sys.stderr)
            return 2

    suffix = f"_{args.subset}" if args.subset else ""
    out = args.out or os.path.join(common.results_dir(), f"{args.name}_{args.half}{suffix}.json")
    tracked = [p for p in (out, summary_path(out)) if os.path.exists(p) and _tracked_by_git(p)]
    if tracked and not args.force:
        print(f"error: {', '.join(tracked)} is tracked by git, so a run would overwrite committed results. "
              "Use another --name or --out, or pass --force", file=sys.stderr)
        return 2

    sha = common.git_sha()
    if args.half == "test" and (sha == "unknown" or sha.endswith("-dirty")):
        print(f"error: the test half needs a clean git tree, but the state is {sha!r}. Commit first, so that "
              "every look can be reproduced from its recorded SHA", file=sys.stderr)
        return 2

    common.apply_flags(flags)
    active = common.active_wwai_flags()

    from .dataset import load_clips
    from .scoring import build_items, summarize
    from .stage_cache import cache_dir

    try:
        cache_name = args.cache or common.front_end_cache_name(active)
        directory = cache_dir(args.half, cache_name)
        clips = load_clips(args.half, args.subset)
    except (ValueError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    start = time.time()
    try:
        # Neither of these reads labels, so a stale cache does not use up a look on the test half.
        cache_meta = check_cache(directory, args.half)
        threshold = args.threshold if args.threshold is not None else production_threshold()
        if args.half == "test":
            append_ledger(args.name, args.reason, sha, flags=active, threshold=threshold)
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
    full, short = write_results(results, out)
    print(format_summary(summary))
    print(f"wrote {full}\n      {short}")
    if summary["unexpected_failures"] > 0:
        types = sorted(k for k in summary["rejected_by_type"] if k.startswith("unexpected:"))
        print(
            f"WARNING: {summary['unexpected_failures']} clip(s) failed with unexpected errors "
            f"({', '.join(types)}). These are harness bugs or production crashes, not child-facing "
            "rejections, so these numbers may not be reliable until they are fixed.",
            file=sys.stderr,
        )
        return EXIT_UNEXPECTED
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
