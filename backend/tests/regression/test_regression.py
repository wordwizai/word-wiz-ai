"""
The three assertions that make the rest of the scoring work measurable, plus the
model-pinning checks.

Run from ``backend/``::

    PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.regression.test_regression -v

Everything here SKIPS rather than fails when the environment cannot support it (no venv,
no torch, no fixtures, no network). A suite that is red for environmental reasons is a
suite people learn to ignore, and this one has to stay trustworthy: it is what tells the
other scoring changes apart from each other.
"""

from __future__ import annotations

import os
import re
import sys
import unittest

if __package__ in (None, ""):
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    from tests.regression import harness as H
else:
    from . import harness as H

REPO_ROOT = os.path.abspath(os.path.join(H.BACKEND_ROOT, ".."))
FRONTEND_SRC = os.path.join(REPO_ROOT, "frontend", "src")

#: Set WWAI_REQUIRE_MODEL_PINS=1 once the revisions in core/model_registry.py are filled
#: in, to keep them from silently reverting to unpinned.
REQUIRE_PINS = os.getenv("WWAI_REQUIRE_MODEL_PINS", "").lower() in ("1", "true", "yes")


class _PipelineTestCase(unittest.TestCase):
    """Base class that turns an unimportable pipeline into a skip, not an error."""

    cases: list = []

    @classmethod
    def setUpClass(cls):
        available, reason = H.pipeline_available()
        if not available:
            raise unittest.SkipTest(
                f"scoring pipeline unavailable ({reason}); this is an environment "
                "problem, not a regression"
            )
        cls.cases = H.fixture_cases()
        if not cls.cases:
            raise unittest.SkipTest(
                "no fixture-backed cases in tests/regression/corpus/ or tests/system/; "
                "see corpus/README.md for how to add one"
            )


# ======================================================================================
# ASSERTION 1 - DETERMINISM
# ======================================================================================
class TestDeterminism(_PipelineTestCase):
    """Same input in, byte-identical analysis out. Twice."""

    def test_client_path_is_deterministic(self):
        for case in self.cases:
            with self.subTest(case=case.case_id):
                first = H.safe_run(H.run_client_path, case)
                second = H.safe_run(H.run_client_path, case)
                self.assertEqual(
                    first,
                    second,
                    f"{case.case_id}: the client path produced different analyses for "
                    f"identical input. Something in the scoring path depends on hidden "
                    f"state, ordering, or an unseeded random source.",
                )

    def test_server_path_is_deterministic(self):
        for case in self.cases:
            with self.subTest(case=case.case_id):
                first = H.safe_run(H.run_server_path, case)
                second = H.safe_run(H.run_server_path, case)
                self.assertEqual(
                    first,
                    second,
                    f"{case.case_id}: the server path (including the Phase 3 phoneme "
                    f"regrouping heuristics) produced different analyses for identical "
                    f"input.",
                )

    def test_rejections_are_deterministic(self):
        """Deliberately bad clips must be rejected the same way every time."""
        rejecting = [
            c for c in self.cases
            if "expect-rejection" in (c.meta.get("tags") or [])
        ]
        if not rejecting:
            self.skipTest("no cases tagged 'expect-rejection' in the corpus")
        for case in rejecting:
            with self.subTest(case=case.case_id):
                first = H.safe_run(H.run_client_path, case)
                second = H.safe_run(H.run_client_path, case)
                self.assertTrue(
                    H.is_error(first),
                    f"{case.case_id} is tagged expect-rejection but was scored instead "
                    f"of rejected: {first.get('sentence_per')}",
                )
                self.assertEqual(first, second)


# ======================================================================================
# ASSERTION 2 - PATH AGREEMENT (client-extracted vs server-extracted)
# ======================================================================================
class TestPathAgreement(_PipelineTestCase):
    """
    The client path (browser sends phonemes already grouped by word) and the server path
    (server flattens and regroups onto the ASR word list) must score the same audio the
    same way. Divergence here is the single biggest bug class in this codebase.

    The default assertion is a RATCHET, not an equality: divergence may shrink freely but
    may not grow past the pinned baseline plus PATH_EPSILON. Set
    ``WWAI_REGRESSION_STRICT_PATHS=1`` to demand exact agreement, which is the goal state.
    """

    def test_divergence_has_not_grown(self):
        checked = 0
        for case in self.cases:
            baseline = case.load_baseline()
            if baseline is None or baseline.get("path_divergence") is None:
                continue
            with self.subTest(case=case.case_id):
                checked += 1
                client = H.safe_run(H.run_client_path, case)
                server = H.safe_run(H.run_server_path, case)
                divergence = H.per_delta(client, server)
                pinned = float(baseline["path_divergence"])
                self.assertLessEqual(
                    divergence,
                    pinned + H.PATH_EPSILON,
                    f"{case.case_id}: client-vs-server PER divergence grew from "
                    f"{pinned:.4f} to {divergence:.4f} (epsilon {H.PATH_EPSILON}). "
                    f"The same audio now scores more differently depending on which "
                    f"path ran.",
                )
        if checked == 0:
            self.skipTest("no baselines pinned yet; run run_regression.py --update-baseline")

    def test_no_structural_disagreement(self):
        """
        Beyond PER, the two paths must agree on the SHAPE of the result: the same
        ground-truth words in the same order, each classified the same way. A structural
        difference means one path saw a word the other did not.
        """
        checked = 0
        for case in self.cases:
            baseline = case.load_baseline()
            if baseline is None:
                continue
            with self.subTest(case=case.case_id):
                checked += 1
                client = H.safe_run(H.run_client_path, case)
                server = H.safe_run(H.run_server_path, case)
                if H.is_error(client) or H.is_error(server):
                    self.assertEqual(
                        client,
                        server,
                        f"{case.case_id}: one path rejected the clip and the other did not.",
                    )
                    continue
                now = H.compare(client, server)
                pinned = baseline.get("path_comparison_structural_count")
                allowed = 0 if pinned is None else int(pinned)
                self.assertLessEqual(
                    len(now["structural_diffs"]),
                    allowed,
                    f"{case.case_id}: the two paths now disagree on word structure "
                    f"({len(now['structural_diffs'])} differences, was {allowed}): "
                    f"{now['structural_diffs']}",
                )
        if checked == 0:
            self.skipTest("no baselines pinned yet; run run_regression.py --update-baseline")

    @unittest.skipUnless(H.STRICT_PATHS, "set WWAI_REGRESSION_STRICT_PATHS=1 to demand parity")
    def test_paths_are_identical(self):
        for case in self.cases:
            with self.subTest(case=case.case_id):
                self.assertEqual(
                    H.safe_run(H.run_client_path, case),
                    H.safe_run(H.run_server_path, case),
                    f"{case.case_id}: client and server analyses differ.",
                )


# ======================================================================================
# ASSERTION 3 - DRIFT FROM BASELINE
# ======================================================================================
class TestDrift(_PipelineTestCase):
    """Aggregate and per-case PER must not move away from the pinned baseline."""

    def test_per_case_drift_within_epsilon(self):
        checked = 0
        for case in self.cases:
            baseline = case.load_baseline()
            if baseline is None:
                continue
            with self.subTest(case=case.case_id):
                checked += 1
                for path_name, runner in (
                    ("client_path", H.run_client_path),
                    ("server_path", H.run_server_path),
                ):
                    pinned = baseline.get(path_name)
                    if pinned is None:
                        continue
                    current = H.safe_run(runner, case)
                    drift = H.per_delta(current, pinned)
                    self.assertLessEqual(
                        drift,
                        H.PER_EPSILON,
                        f"{case.case_id} [{path_name}]: sentence PER moved by {drift:.4f} "
                        f"(epsilon {H.PER_EPSILON}): "
                        f"{pinned.get('sentence_per', pinned.get('error'))} -> "
                        f"{current.get('sentence_per', current.get('error'))}. "
                        f"If this change is intended, re-pin with "
                        f"`run_regression.py --update-baseline` and say so in the PR.",
                    )
        if checked == 0:
            self.skipTest("no baselines pinned yet; run run_regression.py --update-baseline")

    def test_aggregate_drift_within_epsilon(self):
        """
        The corpus-wide mean PER. This is the number to watch when comparing branches:
        a single case moving is noise, the mean moving is a behaviour change.
        """
        current_scores, baseline_scores = [], []
        for case in self.cases:
            baseline = case.load_baseline()
            if baseline is None or not baseline.get("client_path"):
                continue
            pinned = baseline["client_path"]
            if H.is_error(pinned):
                continue
            current = H.safe_run(H.run_client_path, case)
            if H.is_error(current):
                self.fail(
                    f"{case.case_id}: previously scored {pinned['sentence_per']}, now "
                    f"rejected outright ({current['error']})."
                )
            current_scores.append(current["sentence_per"])
            baseline_scores.append(pinned["sentence_per"])
        if not baseline_scores:
            self.skipTest("no scored baselines pinned yet")
        now = sum(current_scores) / len(current_scores)
        was = sum(baseline_scores) / len(baseline_scores)
        self.assertLessEqual(
            abs(now - was),
            H.PER_EPSILON,
            f"aggregate mean PER over {len(baseline_scores)} case(s) moved "
            f"{was:.4f} -> {now:.4f} (epsilon {H.PER_EPSILON}).",
        )

    def test_every_fixture_case_has_a_baseline(self):
        """
        A case with no baseline is silently unchecked, which is worse than a red test.
        Remedy is one command, printed in the failure message.
        """
        missing = [c.case_id for c in self.cases if c.load_baseline() is None]
        self.assertEqual(
            missing,
            [],
            "these cases have no pinned baseline and are therefore not regression-"
            f"checked: {missing}. Run: python -m tests.regression.run_regression "
            "--update-baseline",
        )


# ======================================================================================
# MODEL PINNING
# ======================================================================================
class TestModelRegistry(unittest.TestCase):
    """
    Guards ``core/model_registry.py``: the one place model ids and revisions are declared.
    These do not need torch, so they run even where the pipeline cannot be imported.
    """

    @classmethod
    def setUpClass(cls):
        try:
            from core import model_registry
        except Exception as exc:  # noqa: BLE001
            raise unittest.SkipTest(f"core.model_registry not importable: {exc}") from exc
        cls.registry = model_registry

    def test_unpinned_models_are_visible(self):
        """
        Reports which models still float with upstream ``main``. Informational by default
        (they all do today); set ``WWAI_REQUIRE_MODEL_PINS=1`` once pinned to lock it in.
        """
        unpinned = self.registry.unpinned_keys()
        if REQUIRE_PINS:
            self.assertEqual(
                unpinned,
                [],
                f"WWAI_REQUIRE_MODEL_PINS is set but these models are unpinned: {unpinned}. "
                "Run `python -m core.model_registry --resolve` and paste the SHAs in.",
            )
        elif unpinned:
            print(
                f"\n  [model pins] {len(unpinned)} model(s) unpinned: {', '.join(unpinned)}"
                "\n  [model pins] a push to any of those HF repos changes scoring with no "
                "deploy."
                "\n  [model pins] fix: python -m core.model_registry --resolve"
            )

    def test_no_pin_skew_between_client_and_server(self):
        """
        The models loaded by BOTH the browser and the server must resolve to the SAME
        revision on both sides. A skew here reproduces the client-vs-server scoring
        divergence exactly, and would be invisible without this check.
        """
        for pin in self.registry.shared_models():
            with self.subTest(model=pin.key):
                backend_rev = self.registry.resolve_revision(pin.key)
                frontend_rev = self.registry.frontend_registry()[pin.key]["revision"]
                self.assertEqual(
                    backend_rev,
                    frontend_rev,
                    f"{pin.repo_id} resolves to {backend_rev!r} on the backend but "
                    f"{frontend_rev!r} for the frontend. The same audio would score "
                    f"differently depending on which side ran the model.",
                )

    def test_frontend_sources_use_registered_model_ids(self):
        """
        The frontend still hardcodes its model ids in TypeScript. Until it imports the
        generated registry (``python -m core.model_registry --emit-frontend``), at least
        assert the hardcoded ids match what the registry declares, so a change on either
        side is caught.
        """
        if not os.path.isdir(FRONTEND_SRC):
            self.skipTest(f"frontend sources not present at {FRONTEND_SRC}")
        expectations = {
            os.path.join(FRONTEND_SRC, "services", "phonemeExtractor.ts"): "PHONEME_IPA_ONNX",
            os.path.join(FRONTEND_SRC, "services", "wordExtractor.ts"): "WORD_ASR_CLIENT",
        }
        for path, key in expectations.items():
            with self.subTest(file=os.path.basename(path)):
                if not os.path.exists(path):
                    self.skipTest(f"{path} not present")
                with open(path, encoding="utf-8") as fh:
                    source = fh.read()
                match = re.search(r"private\s+modelName\s*=\s*[\"']([^\"']+)[\"']", source)
                self.assertIsNotNone(
                    match, f"could not find a `private modelName = \"...\"` in {path}"
                )
                self.assertEqual(
                    match.group(1),
                    self.registry.repo_id(key),
                    f"{os.path.basename(path)} loads {match.group(1)!r} but the registry "
                    f"declares {self.registry.repo_id(key)!r} for {key}. Update whichever "
                    f"is wrong - they must not drift.",
                )

    def test_backend_sources_use_registered_model_ids(self):
        """Same check for the backend loaders' hardcoded default model names."""
        expectations = {
            os.path.join(H.BACKEND_ROOT, "core", "phoneme_extractor_onnx.py"): "PHONEME_IPA_ONNX",
            os.path.join(H.BACKEND_ROOT, "core", "phoneme_extractor.py"): "PHONEME_IPA_TORCH",
            os.path.join(H.BACKEND_ROOT, "core", "word_extractor.py"): "WORD_ASR_LOCAL",
        }
        for path, key in expectations.items():
            with self.subTest(file=os.path.basename(path)):
                if not os.path.exists(path):
                    self.skipTest(f"{path} not present")
                with open(path, encoding="utf-8") as fh:
                    source = fh.read()
                expected = self.registry.repo_id(key)
                self.assertIn(
                    expected,
                    source,
                    f"{os.path.basename(path)} no longer mentions {expected!r}, which the "
                    f"registry declares for {key}. If the model changed, update "
                    f"core/model_registry.py in the same commit.",
                )

    def test_from_pretrained_kwargs_is_a_noop_while_unpinned(self):
        """
        Safety property: wiring the registry into a loader must not change behaviour until
        a revision is actually declared.
        """
        for key in self.registry.unpinned_keys():
            with self.subTest(model=key):
                self.assertEqual(self.registry.from_pretrained_kwargs(key), {})

    def test_env_override_wins(self):
        key = "PHONEME_IPA_ONNX"
        var = self.registry.get(key).env_var
        previous = os.environ.get(var)
        try:
            os.environ[var] = "deadbeef"
            self.assertEqual(self.registry.resolve_revision(key), "deadbeef")
            self.assertEqual(
                self.registry.from_pretrained_kwargs(key), {"revision": "deadbeef"}
            )
            os.environ["WWAI_IGNORE_MODEL_PINS"] = "true"
            self.assertIsNone(self.registry.resolve_revision(key))
        finally:
            os.environ.pop("WWAI_IGNORE_MODEL_PINS", None)
            if previous is None:
                os.environ.pop(var, None)
            else:
                os.environ[var] = previous


# ======================================================================================
# OPT-IN: model-backed run (network, weights, Deepgram key)
# ======================================================================================
class TestModelBackedRun(_PipelineTestCase):
    """
    The only check that can catch a change in the acoustic model itself. Off by default:
    it downloads weights and calls a paid API.
    """

    @unittest.skipUnless(H.USE_MODELS, "set WWAI_REGRESSION_USE_MODELS=1 (network + cost)")
    def test_model_backed_run_matches_fixture(self):
        with_audio = [c for c in self.cases if c.audio_path]
        if not with_audio:
            self.skipTest("no cases carry audio.wav")
        for case in with_audio:
            with self.subTest(case=case.case_id):
                live = H.safe_run(H.run_server_path_with_models, case)
                replayed = H.safe_run(H.run_server_path, case)
                self.assertLessEqual(
                    H.per_delta(live, replayed),
                    H.PER_EPSILON,
                    f"{case.case_id}: the live model now scores differently from the "
                    f"recorded fixture. Either the model revision moved (pin it) or the "
                    f"fixture is stale (re-record it).",
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
