"""Score one configuration against speechocean762 using cached model outputs.

    python -m tests.benchmark.run --name baseline
    python -m tests.benchmark.run --name weighted --flag WWAI_WEIGHTED_PER=1
    python -m tests.benchmark.run --name quick --subset smoke_dev

The test half needs WWAI_BENCH_UNLOCK_TEST=1 and --reason, and every such run is
appended to test_runs.log. Exit codes are 0 for ok, 2 for a usage error or a locked
half, 3 for a stale or missing cache, and 4 when clips failed with unexpected errors
(the results are still written so the failures can be inspected).
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
EXIT_UNEXPECTED = 4
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
    ]
    if summary["unexpected_failures"] > 0:
        lines.append(f"unexpected failures {summary['unexpected_failures']}")
    lines.append(f"{'word':10s} {'F0.5':>7s} {'prec':>7s} {'recall':>7s} {'FAR':>7s} {'n':>7s}")
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
