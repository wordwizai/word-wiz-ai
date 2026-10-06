"""How well one expert agrees with the other four, on the benchmark's own word metrics.

Each annotator's word scores are treated as a "system" and scored against the median of
the other four annotators, using the same 0-6 mistake rule. The mean over annotators
shows what expert-level agreement looks like on these metrics.

    python -m tests.benchmark.human_reference --half dev

The test half needs WWAI_BENCH_UNLOCK_TEST=1. It reads only the experts' own scores and
no system output, so it cannot be used to tune anything, but it is still the sealed half.
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
