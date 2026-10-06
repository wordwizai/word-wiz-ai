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
UNSCORED_TOLERANCE = 0.01
N_RESAMPLES = 2000
SEED = 0
_EPS = 1e-12


class NotComparable(ValueError):
    """The two results files cannot be compared (different half, subset or clips)."""


def load_results(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _word_counts(items, threshold, children_only=False):
    words = [w for w in items.words if w.is_child] if children_only else items.words
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
    base_children = _word_counts(base_items, base["threshold"], children_only=True)
    cand_children = _word_counts(cand_items, cand["threshold"], children_only=True)
    if base_children or cand_children:
        child_lo, child_hi = M.percentile_interval(
            M.bootstrap_fbeta_delta(base_children, cand_children, n_resamples, seed))
        child_ci = [child_lo, child_hi]
        child_check = {"value": f"{child_delta:+.4f} [{child_lo:+.4f}, {child_hi:+.4f}]",
                       "passed": child_hi >= -_EPS}
    else:
        child_ci = None
        child_check = {"value": "no child words", "passed": True}
    far_delta = cs["word"]["all"]["false_alarm_rate"] - bs["word"]["all"]["false_alarm_rate"]
    rej_delta = cs["rejection_rate"] - bs["rejection_rate"]
    unscored_delta = cs["unscored_rate"] - bs["unscored_rate"]
    checks = [
        {"name": "real improvement", "rule": "95% CI of word F0.5 difference above 0",
         "value": f"[{lo:+.4f}, {hi:+.4f}]", "passed": lo > 0},
        # Children are a small slice (about 195 real mistakes in the dev half), so a point
        # estimate would flip on noise. Only a significant drop fails.
        {"name": "children not worse", "rule": "children F0.5 not significantly worse (95% CI upper bound >= 0)",
         **child_check},
        {"name": "no more wrong corrections", "rule": f"false-alarm rate rises <= {FAR_TOLERANCE:.3f}",
         "value": f"{far_delta:+.4f}", "passed": far_delta <= FAR_TOLERANCE + _EPS},
        # Rejected and misaligned clips both drop out of every metric, so both count.
        {"name": "no hiding",
         "rule": f"unscored rate (rejected or misaligned clips) rises <= {UNSCORED_TOLERANCE:.2f}",
         "value": f"{unscored_delta:+.4f}", "passed": unscored_delta <= UNSCORED_TOLERANCE + _EPS},
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
        "children_f05_ci": child_ci,
        "false_alarm_delta": far_delta,
        "rejection_delta": rej_delta,
        "unscored_delta": unscored_delta,
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
    for key, label in (("rejection_rate", "rejection rate"), ("unscored_rate", "unscored rate")):
        rb, rk = c["base_summary"][key], c["candidate_summary"][key]
        rows.append(f"{label:24s} {rb:8.4f} {rk:8.4f} {rk - rb:+8.4f}")
    rows.append(f"F0.5 difference, 95% CI [{c['f05_ci'][0]:+.4f}, {c['f05_ci'][1]:+.4f}] (speaker bootstrap)")
    rows.append("")
    width = max([20] + [len(chk["value"]) for chk in c["checks"]])
    for chk in c["checks"]:
        rows.append(f"{'PASS' if chk['passed'] else 'FAIL'}  {chk['name']:28s} {chk['value']:>{width}s}   ({chk['rule']})")
    rows.append(
        "ACCEPT on conditions 1-4 and no new unexpected failures (speed and tests are checked separately)"
        if c["passed"] else "REJECT"
    )
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
