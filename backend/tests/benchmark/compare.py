"""Paired comparison of two run.py results files, applying acceptance conditions 1 to 4.

    python -m tests.benchmark.compare results/baseline_dev.json results/candidate_dev.json

Conditions 5 (speed and memory, see speed.py) and 6 (tests pass) are checked separately
at review time. A fifth check below the four conditions fails a candidate that adds
"unexpected:" failures, which mean harness bugs or production crashes.
Exit codes: 0 all checks pass, 1 at least one fails, 2 inputs not comparable.
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
        {"name": "no new unexpected failures", "rule": "unexpected failures do not increase",
         "value": f"{cs['unexpected_failures'] - bs['unexpected_failures']:+d}",
         "passed": cs["unexpected_failures"] <= bs["unexpected_failures"]},
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
