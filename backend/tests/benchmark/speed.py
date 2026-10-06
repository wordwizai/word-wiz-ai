"""Serial latency and memory of the local pipeline, measured the same way every time.

Live ONNX plus live preprocessing, gates, alignment and scoring. Deepgram is replaced by
cached transcripts because network time is not something this project can optimize.
Run it with nothing else heavy running (no agents, no other benchmark runs).

Only clips that finish are timed. A clip that fails (a gate rejects it, say) usually
fails fast, so counting it would make a worse pipeline look quicker. The result reports
clips_ok and clips_failed next to the latencies, and compare_speed fails a candidate that
succeeds on fewer clips than the baseline did.

    python -m tests.benchmark.speed --name baseline
    python -m tests.benchmark.speed --compare results/baseline_speed.json results/cand_speed.json

Exit codes are 0 for ok, 2 for a usage error, 3 for a stale or missing cache and 4 when no
clip succeeded. With --compare they are 0 when every check passes and 1 when one fails.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np

from . import common
from .run import _NAME, _tracked_by_git

P95_BUDGET = 1.10
RSS_BUDGET_MB = 150.0
SUBSET = "speed_dev"
REPEATS = 2
EXIT_STALE = 3
EXIT_NO_CLIPS = 4


class MeasurementError(RuntimeError):
    """The measurement cannot be reported, for example because no clip succeeded."""


def peak_rss_mb() -> float:
    import psutil

    info = psutil.Process().memory_info()
    peak = getattr(info, "peak_wset", None)  # Windows
    if peak is not None:
        return peak / (1024 * 1024)
    import resource

    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0  # Linux reports KiB


def latency_stats(passes) -> dict:
    """Latency percentiles and clip counts from timed passes.

    ``passes`` has one list of (succeeded, seconds) per repeat. Only the clips that
    succeeded are in the percentiles. ``clips_ok`` is the smallest number that succeeded in
    any repeat, so a clip that failed even once counts as failed.
    """
    if not passes:
        raise MeasurementError("nothing was measured")
    timed = [[seconds for ok, seconds in one if ok] for one in passes]
    clips_ok = min(len(times) for times in timed)
    if clips_ok == 0:
        raise MeasurementError("no clip succeeded, so there is no latency to report")
    return {
        "clips_ok": clips_ok,
        "clips_failed": len(passes[0]) - clips_ok,
        "p50_s": sum(float(np.percentile(times, 50)) for times in timed) / len(timed),
        "p95_s": sum(float(np.percentile(times, 95)) for times in timed) / len(timed),
    }


def measure(clips, directory: str, repeats: int = REPEATS, extractor=None) -> dict:
    from .pipeline import analyze_clip, load_audio
    from .replay import CacheEntry, ReplayWordExtractor

    if not clips:
        raise ValueError("no clips to measure")
    if repeats < 1:
        raise ValueError("repeats must be at least 1")
    if extractor is None:
        from core.phoneme_extractor_onnx import PhonemeExtractorONNX

        with common.quiet():
            extractor = PhonemeExtractorONNX()
    audios = {c.utt_id: load_audio(c.wav_path) for c in clips}
    entries = {c.utt_id: CacheEntry(directory, c.utt_id) for c in clips}

    first = clips[0]
    analyze_clip(audios[first.utt_id], first.text, extractor,
                 ReplayWordExtractor(entries[first.utt_id], check_inputs=False))  # warmup

    passes = []
    for _ in range(repeats):
        timed = []
        for clip in clips:
            words = ReplayWordExtractor(entries[clip.utt_id], check_inputs=False)
            start = time.perf_counter()
            outcome = analyze_clip(audios[clip.utt_id], clip.text, extractor, words)
            timed.append((outcome.status == "ok", time.perf_counter() - start))
        passes.append(timed)
    return {
        "clips": len(clips),
        "repeats": repeats,
        **latency_stats(passes),
        "peak_rss_mb": peak_rss_mb(),
    }


def compare_speed(base: dict, cand: dict) -> dict:
    ratio = cand["p95_s"] / base["p95_s"]
    rss_delta = cand["peak_rss_mb"] - base["peak_rss_mb"]
    base_ok, cand_ok = base.get("clips_ok"), cand.get("clips_ok")
    if base_ok is None or cand_ok is None:
        # Results from before failed clips were left out of the timing cannot be trusted.
        clips_value, clips_passed = "clips_ok missing", False
    else:
        clips_value, clips_passed = f"{cand_ok} vs {base_ok}", cand_ok >= base_ok
    checks = [
        {"name": "p95 latency", "rule": f"<= {P95_BUDGET:.2f}x baseline", "value": f"{ratio:.3f}x",
         "passed": ratio <= P95_BUDGET},
        {"name": "peak memory", "rule": f"<= +{RSS_BUDGET_MB:.0f} MB", "value": f"{rss_delta:+.1f} MB",
         "passed": rss_delta <= RSS_BUDGET_MB},
        # Failed clips are not timed, so a candidate that fails more of them looks faster.
        {"name": "same clips succeed", "rule": "at least as many clips succeed as in the baseline",
         "value": clips_value, "passed": clips_passed},
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
    parser.add_argument("--force", action="store_true", help="overwrite a results file that git tracks")
    parser.add_argument("--compare", nargs=2, metavar=("BASE", "CANDIDATE"))
    args = parser.parse_args(argv)

    if args.compare:
        with open(args.compare[0], encoding="utf-8") as fh:
            base = json.load(fh)
        with open(args.compare[1], encoding="utf-8") as fh:
            cand = json.load(fh)
        result = compare_speed(base, cand)
        for chk in result["checks"]:
            print(f"{'PASS' if chk['passed'] else 'FAIL'}  {chk['name']:18s} {chk['value']:>16s}   ({chk['rule']})")
        return 0 if result["passed"] else 1

    # core loads backend/.env on import, so WWAI_* flags set there would apply without being recorded.
    dotenv_keys = common.dotenv_wwai_keys()
    if dotenv_keys:
        print(f"error: backend/.env sets {', '.join(dotenv_keys)}; "
              "remove them and pass flags with --flag so they are recorded", file=sys.stderr)
        return 2
    if args.repeats < 1:
        print("error: --repeats must be at least 1", file=sys.stderr)
        return 2
    for option, value in (("--name", args.name), ("--cache", args.cache)):
        if value is not None and not _NAME.fullmatch(value):
            print(f"error: {option} {value!r} may only contain letters, digits, _ . and -", file=sys.stderr)
            return 2
    try:
        flags = common.parse_flag_args(args.flag)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    out = args.out or os.path.join(common.results_dir(), f"{args.name}_speed.json")
    if os.path.exists(out) and _tracked_by_git(out) and not args.force:
        print(f"error: {out} is tracked by git, so a measurement would overwrite committed results. "
              "Use another --name or --out, or pass --force", file=sys.stderr)
        return 2

    common.apply_flags(flags)
    active = common.active_wwai_flags()
    from .dataset import load_clips
    from .stage_cache import cache_dir

    try:
        cache_name = args.cache or common.front_end_cache_name(active)
        directory = cache_dir("dev", cache_name)
        clips = load_clips("dev", args.subset)
    except (ValueError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    try:
        result = measure(clips, directory, args.repeats)
    except common.StaleCacheError as exc:
        print(f"stale cache: {exc}", file=sys.stderr)
        return EXIT_STALE
    except MeasurementError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_NO_CLIPS
    result.update(name=args.name, subset=args.subset, cache=cache_name, flags=active,
                  git_sha=common.git_sha(), created=time.strftime("%Y-%m-%dT%H:%M:%S"))
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(result, fh, indent=2, sort_keys=True)
    print(f"p50 {result['p50_s']:.3f}s   p95 {result['p95_s']:.3f}s   peak memory {result['peak_rss_mb']:.0f} MB   "
          f"({result['clips_ok']} of {result['clips']} clips timed)")
    if result["clips_failed"]:
        print(f"warning: {result['clips_failed']} clip(s) failed and were left out of the timing", file=sys.stderr)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
