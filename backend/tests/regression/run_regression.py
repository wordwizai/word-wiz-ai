"""
Regression harness CLI.

Run from ``backend/``::

    PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m tests.regression.run_regression

Common flags::

    --list                 show the corpus and stop
    --update-baseline      (re-)pin expected outputs for every case; prints a diff first
    --case <id>            restrict to one case id
    --report <path.json>   also dump the full machine-readable report
    --with-models          model-backed run (network + weights + Deepgram key; opt-in)

Exit code is 0 when nothing drifted, 1 when something did, 2 when the pipeline could
not be imported at all (environment problem, not a code problem).
"""

from __future__ import annotations

import argparse
import json
import os
import sys

if __package__ in (None, ""):
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    from tests.regression import harness as H
else:
    from . import harness as H


def _fmt(value) -> str:
    if value is None:
        return "   --  "
    if isinstance(value, str):
        return value[:8]
    return f"{value:7.4f}"


def _score_cell(record: dict) -> str:
    """A record is either a score or a rejection; both need one narrow column."""
    if H.is_error(record):
        return "REJECTED"
    return _fmt(record.get("sentence_per"))


def cmd_list() -> int:
    cases = H.discover_cases()
    summary = H.corpus_summary(cases)
    print(f"{'case id':40s} {'fixture':8s} {'audio':6s} {'baseline':9s} tags")
    print("-" * 100)
    for case in cases:
        print(
            f"{case.case_id:40s} "
            f"{'yes' if case.fixture else 'NO':8s} "
            f"{'yes' if case.audio_path else 'no':6s} "
            f"{'yes' if os.path.exists(case.baseline_path) else 'MISSING':9s} "
            f"{','.join(case.meta.get('tags', []) or [])}"
        )
    print()
    print(json.dumps(summary, indent=2))
    if summary["total_cases"] < 30:
        print(
            f"\nCorpus is {summary['total_cases']} case(s). Target is 30-50 real clips "
            "including deliberately bad ones. See corpus/README.md for how to add them."
        )
    return 0


def cmd_update_baseline(only: str | None) -> int:
    cases = [c for c in H.fixture_cases() if only is None or c.case_id == only]
    if not cases:
        print("No fixture-backed cases matched; nothing to pin.")
        return 1
    for case in cases:
        old = case.load_baseline()
        new = H.build_baseline(case)
        if old:
            drift = H.per_delta(
                old.get("client_path", {}), new.get("client_path", {})
            )
            flag = "CHANGED" if old.get("client_path") != new.get("client_path") else "same"
            print(f"  {case.case_id:40s} {flag:8s} client PER delta {drift:.4f}")
        else:
            print(f"  {case.case_id:40s} NEW")
        path = H.write_baseline(case, new)
        print(f"      -> {os.path.relpath(path, H.BACKEND_ROOT)}")
    print(f"\nPinned {len(cases)} baseline(s). Review the diff before committing.")
    return 0


def cmd_run(only: str | None, report_path: str | None, with_models: bool) -> int:
    cases = [c for c in H.fixture_cases() if only is None or c.case_id == only]
    if not cases:
        print("No fixture-backed cases found. Nothing to check.")
        print("Add cases under tests/regression/corpus/ - see corpus/README.md.")
        return 0

    rows = []
    failures = 0
    print(
        f"{'case id':40s} {'client':>8s} {'server':>8s} {'paths':>8s} "
        f"{'base':>8s} {'drift':>8s}  status"
    )
    print("-" * 100)
    for case in cases:
        client = H.safe_run(H.run_client_path, case)
        server = H.safe_run(H.run_server_path, case)
        client2 = H.safe_run(H.run_client_path, case)

        baseline = case.load_baseline()
        path_div = H.per_delta(client, server)
        base_client = (baseline or {}).get("client_path")
        drift = H.per_delta(client, base_client) if base_client else None
        base_div = (baseline or {}).get("path_divergence")

        problems = []
        if client != client2:
            problems.append("NON-DETERMINISTIC")
        if baseline is None:
            problems.append("no-baseline")
        else:
            if drift is not None and drift > H.PER_EPSILON:
                problems.append(f"DRIFT>{H.PER_EPSILON}")
            if base_div is not None and path_div > base_div + H.PATH_EPSILON:
                problems.append("PATH-DIVERGENCE-WORSE")
        if H.STRICT_PATHS and client != server:
            problems.append("PATHS-DIFFER(strict)")

        status = "ok" if not problems else " ".join(problems)
        if problems and problems != ["no-baseline"]:
            failures += 1

        print(
            f"{case.case_id:40s} "
            f"{_score_cell(client):>8s} "
            f"{_score_cell(server):>8s} "
            f"{path_div:8.4f} "
            f"{_fmt(base_div):>8s} "
            f"{_fmt(drift):>8s}  {status}"
        )

        row = {
            "case_id": case.case_id,
            "tags": case.meta.get("tags", []),
            "client_path": client,
            "server_path": server,
            "deterministic": client == client2,
            "path_divergence": round(path_div, 6),
            "baseline_path_divergence": base_div,
            "baseline_drift": None if drift is None else round(drift, 6),
            "path_comparison": H.compare(client, server),
            "status": status,
        }
        if with_models:
            try:
                row["model_backed"] = H.safe_run(H.run_server_path_with_models, case)
            except H.HarnessUnavailable as exc:
                row["model_backed"] = {"skipped": str(exc)}
        rows.append(row)

    # Corpus-level aggregate: the single number to watch across the ten agents' branches.
    scored = [r for r in rows if "sentence_per" in r["client_path"]]
    aggregate = (
        round(sum(r["client_path"]["sentence_per"] for r in scored) / len(scored), 6)
        if scored
        else None
    )
    print("-" * 100)
    print(f"cases: {len(rows)}   scored: {len(scored)}   mean client sentence_per: {aggregate}")
    print(f"epsilons: PER={H.PER_EPSILON} PATH={H.PATH_EPSILON} strict_paths={H.STRICT_PATHS}")
    if failures:
        print(f"\n{failures} case(s) need attention.")
    else:
        print("\nNo drift detected.")

    if report_path:
        payload = {
            "aggregate_mean_client_per": aggregate,
            "per_epsilon": H.PER_EPSILON,
            "path_epsilon": H.PATH_EPSILON,
            "corpus": H.corpus_summary(),
            "cases": rows,
        }
        os.makedirs(os.path.dirname(os.path.abspath(report_path)) or ".", exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False, sort_keys=True)
        print(f"report written to {report_path}")

    return 1 if failures else 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Word Wiz AI scoring regression harness")
    parser.add_argument("--list", action="store_true", help="show the corpus and exit")
    parser.add_argument("--update-baseline", action="store_true", help="(re-)pin expectations")
    parser.add_argument("--case", default=None, help="restrict to one case id")
    parser.add_argument("--report", default=None, help="write a JSON report here")
    parser.add_argument(
        "--with-models",
        action="store_true",
        help="also run the real acoustic models (network, weights, Deepgram key)",
    )
    args = parser.parse_args(argv)

    if args.with_models:
        os.environ["WWAI_REGRESSION_USE_MODELS"] = "1"
        H.USE_MODELS = True

    available, reason = H.pipeline_available()
    if not available:
        print("SKIP: the scoring pipeline could not be imported, so nothing was checked.")
        print(f"      reason: {reason}")
        print("      This is an environment problem (missing venv/deps), not a regression.")
        return 2

    if args.list:
        return cmd_list()
    if args.update_baseline:
        return cmd_update_baseline(args.case)
    return cmd_run(args.case, args.report, args.with_models)


if __name__ == "__main__":
    raise SystemExit(main())
