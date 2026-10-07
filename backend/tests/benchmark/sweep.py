"""Round 0. Measure every default-OFF accuracy flag on the dev half, then combine greedily.

    python -m tests.benchmark.sweep
    python -m tests.benchmark.sweep --subset smoke_dev      # quick look, not for decisions

Each configuration runs in a fresh interpreter, because several flags are read at import
time. Every flag is compared with whatever the current default is, so a flag that has
since become the default shows no difference and is not selected. A configuration whose
front-end flags need a cache that does not exist yet (run.py exits with 3) is reported
with the stage_cache command that builds it, then skipped. Any other failure of run.py
stops the sweep. Exit codes are 0 for ok, 1 when a run failed, 2 when the dataset is
missing or two results cannot be compared, and 3 when the baseline itself needs a cache.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

from . import common
from .run import EXIT_STALE

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
    """A name run.py accepts for --name (letters, digits, _ . and -), so flags are joined with '-'."""
    if not flags:
        return "sweep_baseline"
    return "sweep_" + "-".join(sorted(k[len("WWAI_"):].lower() for k in flags))


def run_config(flags: dict, half: str, subset, memo: dict):
    """Run run.py for one flag set in a fresh interpreter. Returns the results path, or None.

    None means the configuration needs a cache that does not exist or is stale (exit 3). Any
    other non-zero exit raises RuntimeError. Results are remembered in ``memo``, so a
    configuration runs once however many comparisons use it.
    """
    key = tuple(sorted(flags.items()))
    if key in memo:
        return memo[key]

    name = config_name(flags)
    suffix = f"_{subset}" if subset else ""
    out = os.path.join(common.results_dir(), f"{name}_{half}{suffix}.json")
    # --force because these files are the sweep's own and every sweep rewrites them. The
    # .summary.json ones are not git-ignored, so one that was committed would otherwise
    # make the next sweep stop with run.py's refusal to overwrite committed results.
    cmd = [sys.executable, "-m", "tests.benchmark.run", "--name", name, "--half", half, "--out", out, "--force"]
    for k, v in sorted(flags.items()):
        cmd += ["--flag", f"{k}={v}"]
    if subset:
        cmd += ["--subset", subset]
    # Start from no experiment flags, so only what this configuration passes is on.
    env = {k: v for k, v in os.environ.items() if not common.is_experiment_flag(k)}
    env["PYTHONIOENCODING"] = "utf-8"
    print(f"  running {name} ...", flush=True)
    start = time.time()
    proc = subprocess.run(cmd, cwd=common.BACKEND_ROOT, env=env, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    if proc.returncode == EXIT_STALE:
        front = " ".join(f"--flag {k}={v}" for k, v in sorted(flags.items()) if k in common.FRONT_END_FLAGS)
        lines = [line.strip() for line in (proc.stderr or "").splitlines() if line.strip()]
        reason = next((line for line in lines if line.startswith("stale cache:")), lines[-1] if lines else "")
        if reason:
            print(f"  {reason}")
        print(f"  needs a cache: python -m tests.benchmark.stage_cache --half {half} {front}".rstrip())
        memo[key] = None
        return None
    if proc.returncode != 0:
        raise RuntimeError(
            f"run.py failed for {name} (exit code {proc.returncode}):\n{proc.stdout}\n{proc.stderr}"
        )
    print(f"  {name} took {time.time() - start:.0f}s", flush=True)
    memo[key] = out
    return out


def make_evaluator(half: str, subset, memo: dict | None = None):
    from .compare import compare_results, load_results
    from .dataset import load_clips

    clips = load_clips(half, subset)
    memo = {} if memo is None else memo

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

    memo: dict = {}
    try:
        evaluate = make_evaluator("dev", args.subset, memo)
        # Every comparison starts from this run. Without its cache every candidate would be
        # skipped, and the sweep would end by reporting that no flag helps.
        if run_config({}, "dev", args.subset, memo) is None:
            print("error: the baseline configuration needs a cache, so nothing can be compared. "
                  "Build it with the command above.", file=sys.stderr)
            return EXIT_STALE
        steps, selected = greedy_select(CANDIDATES, evaluate)
    except (ValueError, FileNotFoundError) as exc:  # no dataset, or results that cannot be compared
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

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
