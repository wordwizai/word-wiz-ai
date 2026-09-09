"""
Regression harness for the Word Wiz AI scoring pipeline.

WHAT THIS IS FOR
----------------
The scoring code (``core/process_audio.py``) is full of tuned constants — the Phase 3
``align_phonemes_to_words`` flexibility/length-ratio/confidence numbers being the worst
offenders — and there has been no way to tell an improvement from a regression. This
harness runs a corpus of recorded cases through the pipeline and answers three questions:

  1. DETERMINISM   — same input twice, byte-identical analysis out?
  2. PATH AGREEMENT— does the client-phoneme path score the same as the server-extraction
                     path on the same acoustic output?
  3. DRIFT         — has aggregate PER moved away from a pinned baseline?

DESIGN CONSTRAINT: NO NETWORK, NO MODELS BY DEFAULT
---------------------------------------------------
Downloading wav2vec2 or calling Deepgram/OpenAI costs money and is rate limited, and CI
boxes have neither the venv nor the weights. So a case can carry a ``fixture.json``
holding the *recorded model output* (the predicted word list and the predicted phoneme
stream). With a fixture, everything downstream of the acoustic model — which is where all
the tunable, breakable logic lives — runs in milliseconds with no network at all.

Model-backed runs are opt-in via ``WWAI_REGRESSION_USE_MODELS=1`` and are the only way to
catch a change in the acoustic model itself. See "Coverage and limits" in README.md.

CASE LAYOUT (see corpus/README.md)
----------------------------------
    corpus/<case_id>/
        sentence.txt     required   the text the child was asked to read
        fixture.json     optional   recorded model output; makes the case model-free
        audio.wav        optional   16 kHz mono; only needed for model-backed runs
        meta.json        optional   {"tags": ["noisy"], "notes": "..."}
    corpus/_baselines/<case_id>.json   generated, pinned expected output

Legacy ``backend/tests/system/test_case_*`` folders are discovered automatically and their
fixtures are derived from the committed ``result.json``, so the harness works today
without anyone re-recording anything. Those folders are never written to.
"""

from __future__ import annotations

import contextlib
import copy
import io
import json
import os
import sys
from dataclasses import dataclass, field
from typing import Any

# --------------------------------------------------------------------------------------
# Paths / sys.path, following the convention in tests/system/run_system_tests.py
# --------------------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
TESTS_ROOT = os.path.abspath(os.path.join(HERE, ".."))
BACKEND_ROOT = os.path.abspath(os.path.join(TESTS_ROOT, ".."))
CORPUS_DIR = os.path.join(HERE, "corpus")
BASELINE_DIR = os.path.join(CORPUS_DIR, "_baselines")
LEGACY_SYSTEM_DIR = os.path.join(TESTS_ROOT, "system")

if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

# --------------------------------------------------------------------------------------
# Tunables (all env-overridable; every default is chosen so an untouched repo is green)
# --------------------------------------------------------------------------------------
#: How far aggregate sentence PER may move from the pinned baseline before we call it drift.
PER_EPSILON = float(os.getenv("WWAI_REGRESSION_PER_EPSILON", "0.02"))
#: How much WORSE client-vs-server divergence may get than the pinned baseline divergence.
PATH_EPSILON = float(os.getenv("WWAI_REGRESSION_PATH_EPSILON", "0.02"))
#: Aspirational mode: require the two paths to agree exactly. Off by default because they
#: currently do not, and a permanently-red suite is a suite people learn to ignore.
STRICT_PATHS = os.getenv("WWAI_REGRESSION_STRICT_PATHS", "").lower() in ("1", "true", "yes")
#: Opt-in: actually load wav2vec2 / call the word extractor. Needs network + venv + money.
USE_MODELS = os.getenv("WWAI_REGRESSION_USE_MODELS", "").lower() in ("1", "true", "yes")
#: The pipeline is extremely chatty on stdout. Swallow it unless asked not to.
VERBOSE = os.getenv("WWAI_REGRESSION_VERBOSE", "").lower() in ("1", "true", "yes")


@contextlib.contextmanager
def quiet():
    """Swallow the pipeline's print() noise so harness output stays readable."""
    if VERBOSE:
        yield
        return
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        yield


class HarnessUnavailable(RuntimeError):
    """Raised when the pipeline cannot be imported. Callers should SKIP, not fail."""


# --------------------------------------------------------------------------------------
# Lazy pipeline import. torch/transformers pull ~16s on a cold start, and are absent in
# any environment without the venv — so import on demand and degrade to a skip.
# --------------------------------------------------------------------------------------
_pipeline: dict[str, Any] | None = None
_pipeline_error: str | None = None


def load_pipeline() -> dict[str, Any]:
    """Import the scoring pipeline, or raise HarnessUnavailable with the reason."""
    global _pipeline, _pipeline_error
    if _pipeline is not None:
        return _pipeline
    if _pipeline_error is not None:
        raise HarnessUnavailable(_pipeline_error)
    try:
        from core.grapheme_to_phoneme import grapheme_to_phoneme
        from core.process_audio import (
            align_phonemes_to_words,
            analyze_results,
            process_audio_array,
            process_audio_with_client_phonemes,
        )
    except Exception as exc:  # noqa: BLE001 - any import failure means "skip", not "fail"
        _pipeline_error = f"{type(exc).__name__}: {exc}"
        raise HarnessUnavailable(_pipeline_error) from exc
    _pipeline = {
        "g2p": grapheme_to_phoneme,
        "analyze_results": analyze_results,
        "process_audio_array": process_audio_array,
        "process_audio_with_client_phonemes": process_audio_with_client_phonemes,
        "align_phonemes_to_words": align_phonemes_to_words,
    }
    return _pipeline


def pipeline_available() -> tuple[bool, str]:
    """(available, reason_if_not) — for tests that want to skip rather than error."""
    try:
        load_pipeline()
        return True, ""
    except HarnessUnavailable as exc:
        return False, str(exc)


# --------------------------------------------------------------------------------------
# Case model
# --------------------------------------------------------------------------------------
@dataclass
class Fixture:
    """Recorded acoustic-model output for one case. This is what makes cases model-free."""

    #: What the word-extraction model heard, in order.
    words: list[str]
    #: Predicted phonemes grouped per word, exactly as the CLIENT sends them.
    phonemes_by_word: list[list[str]]
    #: The raw ungrouped phoneme stream, as the SERVER sees it before regrouping.
    #: Defaults to the concatenation of phonemes_by_word.
    phonemes_flat: list[str] = field(default_factory=list)
    source: str = ""

    def __post_init__(self):
        if not self.phonemes_flat:
            self.phonemes_flat = [p for word in self.phonemes_by_word for p in word]

    def to_dict(self) -> dict:
        return {
            "words": self.words,
            "phonemes_by_word": self.phonemes_by_word,
            "phonemes_flat": self.phonemes_flat,
            "source": self.source,
        }


@dataclass
class RegressionCase:
    case_id: str
    sentence: str
    directory: str
    fixture: Fixture | None = None
    audio_path: str | None = None
    meta: dict = field(default_factory=dict)
    legacy: bool = False

    @property
    def baseline_path(self) -> str:
        # Baselines always live under corpus/_baselines/, never inside tests/system/,
        # so the harness never writes to another suite's fixtures.
        return os.path.join(BASELINE_DIR, f"{self.case_id}.json")

    def load_baseline(self) -> dict | None:
        if not os.path.exists(self.baseline_path):
            return None
        with open(self.baseline_path, encoding="utf-8") as fh:
            return json.load(fh)


# --------------------------------------------------------------------------------------
# Discovery
# --------------------------------------------------------------------------------------
def _read_text(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read().strip()


def _read_json(path: str) -> Any:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def derive_fixture_from_result_json(result_path: str) -> Fixture | None:
    """
    Reconstruct a Fixture from a legacy ``tests/system/test_case_*/result.json``.

    ``result.json`` stores the analysis DataFrame column-wise. The ``predicted_word`` and
    ``phonemes`` columns together are exactly the recorded acoustic output, once rows that
    represent a DELETION (a ground-truth word the model never produced) are dropped —
    those rows have no predicted word and no predicted phonemes to contribute.
    """
    try:
        data = _read_json(result_path)
    except (OSError, json.JSONDecodeError):
        return None
    table = data.get("words_phonemes")
    if not isinstance(table, dict):
        return None
    types = table.get("type", {})
    pred_words = table.get("predicted_word", {})
    phonemes = table.get("phonemes", {})
    if not pred_words or not phonemes:
        return None

    # Column dicts are keyed by stringified row index; restore row order numerically.
    try:
        row_keys = sorted(pred_words.keys(), key=lambda k: int(k))
    except (TypeError, ValueError):
        row_keys = sorted(pred_words.keys())

    words: list[str] = []
    grouped: list[list[str]] = []
    for key in row_keys:
        if types.get(key) == "deletion":
            continue  # nothing was predicted for this row
        word = pred_words.get(key)
        phs = phonemes.get(key)
        if not word:
            continue
        words.append(str(word))
        grouped.append([str(p) for p in (phs or [])])
    if not words:
        return None
    return Fixture(
        words=words,
        phonemes_by_word=grouped,
        source=os.path.relpath(result_path, BACKEND_ROOT).replace("\\", "/"),
    )


def _load_corpus_case(directory: str) -> RegressionCase | None:
    sentence_path = os.path.join(directory, "sentence.txt")
    if not os.path.exists(sentence_path):
        return None
    case_id = os.path.basename(directory)
    fixture = None
    fixture_path = os.path.join(directory, "fixture.json")
    if os.path.exists(fixture_path):
        raw = _read_json(fixture_path)
        fixture = Fixture(
            words=[str(w) for w in raw.get("words", [])],
            phonemes_by_word=[[str(p) for p in w] for w in raw.get("phonemes_by_word", [])],
            phonemes_flat=[str(p) for p in raw.get("phonemes_flat", [])],
            source=raw.get("source", os.path.relpath(fixture_path, BACKEND_ROOT)),
        )
    audio_path = os.path.join(directory, "audio.wav")
    meta_path = os.path.join(directory, "meta.json")
    return RegressionCase(
        case_id=case_id,
        sentence=_read_text(sentence_path),
        directory=directory,
        fixture=fixture,
        audio_path=audio_path if os.path.exists(audio_path) else None,
        meta=_read_json(meta_path) if os.path.exists(meta_path) else {},
    )


def _load_legacy_case(directory: str) -> RegressionCase | None:
    sentence_path = os.path.join(directory, "sentence.txt")
    if not os.path.exists(sentence_path):
        return None
    result_path = os.path.join(directory, "result.json")
    fixture = derive_fixture_from_result_json(result_path) if os.path.exists(result_path) else None
    audio_path = os.path.join(directory, "audio.wav")
    return RegressionCase(
        case_id=f"system_{os.path.basename(directory)}",
        sentence=_read_text(sentence_path),
        directory=directory,
        fixture=fixture,
        audio_path=audio_path if os.path.exists(audio_path) else None,
        meta={"tags": ["legacy-system-case"]},
        legacy=True,
    )


def discover_cases(include_legacy: bool = True) -> list[RegressionCase]:
    """All runnable cases, sorted by id. Missing directories are simply empty, not fatal."""
    cases: list[RegressionCase] = []
    if os.path.isdir(CORPUS_DIR):
        for name in sorted(os.listdir(CORPUS_DIR)):
            if name.startswith("_") or name.startswith("."):
                continue
            path = os.path.join(CORPUS_DIR, name)
            if os.path.isdir(path):
                case = _load_corpus_case(path)
                if case:
                    cases.append(case)
    if include_legacy and os.path.isdir(LEGACY_SYSTEM_DIR):
        for name in sorted(os.listdir(LEGACY_SYSTEM_DIR)):
            if not name.startswith("test_case_"):
                continue
            path = os.path.join(LEGACY_SYSTEM_DIR, name)
            if os.path.isdir(path):
                case = _load_legacy_case(path)
                if case:
                    cases.append(case)
    return sorted(cases, key=lambda c: c.case_id)


def fixture_cases(cases: list[RegressionCase] | None = None) -> list[RegressionCase]:
    """Cases that can run with no models and no network."""
    return [c for c in (cases if cases is not None else discover_cases()) if c.fixture]


# --------------------------------------------------------------------------------------
# Normalisation — one canonical, JSON-safe shape that both paths and the baseline share
# --------------------------------------------------------------------------------------
def normalize_analysis(pronunciation_data: list[dict]) -> dict:
    """
    Turn raw ``_process_word_alignment`` output into a stable comparison record.

    Only fields that are meaningful to compare are kept. Floats are rounded to 6 dp so
    that an irrelevant last-bit difference never shows up as a regression.
    """
    pipeline = load_pipeline()
    # analyze_results is called for its real side effects/validation, not just its return
    # value, so that anything it would raise in production also fires here.
    with quiet():
        _df, highest_per_word, problem_summary, per_summary = pipeline["analyze_results"](
            pronunciation_data
        )
    words = []
    for row in pronunciation_data:
        words.append(
            {
                "type": row.get("type"),
                "ground_truth_word": row.get("ground_truth_word", ""),
                "predicted_word": row.get("predicted_word", ""),
                "ground_truth_phonemes": list(row.get("ground_truth_phonemes") or []),
                "phonemes": list(row.get("phonemes") or []),
                "per": round(float(row.get("per", 0.0)), 6),
                "total_phonemes": int(row.get("total_phonemes", 0)),
                "total_errors": int(row.get("total_errors", 0)),
                "missed": list(row.get("missed") or []),
                "added": list(row.get("added") or []),
                "substituted": [list(pair) for pair in (row.get("substituted") or [])],
            }
        )
    return {
        "sentence_per": round(float(per_summary.get("sentence_per", 0.0)), 6),
        "total_phonemes": int(per_summary.get("total_phonemes", 0)),
        "total_errors": int(per_summary.get("total_errors", 0)),
        "highest_per_word": str(highest_per_word.get("ground_truth_word", "")),
        "problem_types": sorted(problem_summary.keys()) if isinstance(problem_summary, dict) else [],
        "words": words,
    }


# --------------------------------------------------------------------------------------
# The two paths
# --------------------------------------------------------------------------------------
def _ground_truth(sentence: str):
    pipeline = load_pipeline()
    cleaned = (
        sentence.strip().lower().replace(".", "").replace(",", "")
        .replace("?", "").replace("!", "").replace("'", "")
    )
    return cleaned, pipeline["g2p"](cleaned)


def run_client_path(case: RegressionCase) -> dict:
    """
    The path taken when the browser did the extraction:
    client sends phonemes ALREADY GROUPED BY WORD, plus its own word list, and the server
    aligns them as-is. No regrouping happens.
    """
    import asyncio

    pipeline = load_pipeline()
    if case.fixture is None:
        raise HarnessUnavailable(f"case {case.case_id} has no fixture")
    _, gt = _ground_truth(case.sentence)
    with quiet():
        data = asyncio.run(
            pipeline["process_audio_with_client_phonemes"](
                client_phonemes=copy.deepcopy(case.fixture.phonemes_by_word),
                ground_truth_phonemes=gt,
                audio_array=None,  # unused when client_words are supplied
                sampling_rate=16000,
                word_extraction_model=None,
                client_words=list(case.fixture.words),
            )
        )
    return normalize_analysis(data)


class _StubPhonemeExtractor:
    """Replays a recorded phoneme stream. Ignores audio entirely."""

    def __init__(self, phonemes_flat: list[str]):
        # process_audio_array immediately re-flattens, so the grouping we hand back here
        # is irrelevant; one group keeps the >1-element guard happy.
        self._payload = [list(phonemes_flat)] if phonemes_flat else []
        self.calls = 0

    def extract_phoneme(self, audio=None, sampling_rate=16000, **_kwargs):
        self.calls += 1
        # Two "words" so the len(...) <= 1 guard in process_audio_array passes.
        flat = self._payload[0] if self._payload else []
        half = max(1, len(flat) // 2)
        return [flat[:half], flat[half:]]


class _StubWordExtractor:
    """Replays a recorded word list. Ignores audio entirely."""

    def __init__(self, words: list[str]):
        self._words = list(words)
        self.calls = 0

    def extract_words(self, audio=None, sampling_rate=16000, **_kwargs):
        self.calls += 1
        return list(self._words)


def _synthetic_audio(seconds: float = 1.0, sampling_rate: int = 16000):
    """
    Deterministic non-silent audio for the server path.

    The stub extractors never look at it; it exists only to satisfy the preprocessing and
    chunking code in ``process_audio_array``. A fixed waveform keeps runs reproducible,
    and 1 s keeps ``should_use_chunking`` on the non-chunked branch.
    """
    import numpy as np

    t = np.arange(int(seconds * sampling_rate), dtype=np.float64) / sampling_rate
    return (0.1 * np.sin(2 * np.pi * 220.0 * t)).astype(np.float32)


def run_server_path(case: RegressionCase) -> dict:
    """
    The path taken when the SERVER did the extraction: the flat phoneme stream is
    regrouped onto the ASR's word list via ``align_phonemes_to_words`` before alignment.

    This calls the real ``process_audio_array`` with stub extractors, so the Phase 3
    regrouping heuristics are genuinely exercised rather than reimplemented here.
    """
    import asyncio

    pipeline = load_pipeline()
    if case.fixture is None:
        raise HarnessUnavailable(f"case {case.case_id} has no fixture")
    _, gt = _ground_truth(case.sentence)
    with quiet():
        data = asyncio.run(
            pipeline["process_audio_array"](
                ground_truth_phonemes=gt,
                audio_array=_synthetic_audio(),
                sampling_rate=16000,
                phoneme_extraction_model=_StubPhonemeExtractor(case.fixture.phonemes_flat),
                word_extraction_model=_StubWordExtractor(case.fixture.words),
                use_chunking=False,
            )
        )
    return normalize_analysis(data)


def run_server_path_with_models(case: RegressionCase) -> dict:
    """
    Full model-backed run. Downloads weights and calls the real extractors.

    Guarded by ``WWAI_REGRESSION_USE_MODELS=1`` because it needs network, RAM and (for
    ``WordExtractorOnline``) a paid Deepgram key. Never runs in the default suite.
    """
    import asyncio

    import soundfile as sf

    pipeline = load_pipeline()
    if not USE_MODELS:
        raise HarnessUnavailable("WWAI_REGRESSION_USE_MODELS is not set")
    if not case.audio_path:
        raise HarnessUnavailable(f"case {case.case_id} has no audio.wav")

    from core.phoneme_extractor_onnx import PhonemeExtractorONNX
    from core.word_extractor import WordExtractor

    audio, sr = sf.read(case.audio_path)
    if audio.ndim > 1:
        audio = audio[:, 0]
    if sr != 16000:
        raise HarnessUnavailable(f"{case.case_id}: audio is {sr} Hz, expected 16000")

    _, gt = _ground_truth(case.sentence)
    with quiet():
        data = asyncio.run(
            pipeline["process_audio_array"](
                ground_truth_phonemes=gt,
                audio_array=audio,
                sampling_rate=16000,
                phoneme_extraction_model=PhonemeExtractorONNX(),
                word_extraction_model=WordExtractor(),
            )
        )
    return normalize_analysis(data)


def safe_run(runner, case: RegressionCase) -> dict:
    """
    Run one path and normalise a raised exception into a comparable record.

    Deliberately-bad clips (silent, too short, one word, no speech) are supposed to be
    REJECTED, and "rejected the same way every time" is exactly as much a regression
    target as "scored the same every time". So an exception becomes
    ``{"error": "<ExcType>: <message>"}`` rather than blowing up the run.
    """
    try:
        return runner(case)
    except HarnessUnavailable:
        raise
    except Exception as exc:  # noqa: BLE001 - the exception IS the result for bad clips
        return {"error": f"{type(exc).__name__}: {exc}"}


def is_error(record: dict) -> bool:
    return "error" in record


# --------------------------------------------------------------------------------------
# Comparison / drift reporting
# --------------------------------------------------------------------------------------
def per_delta(a: dict, b: dict) -> float:
    """
    Absolute difference in aggregate sentence PER between two analyses.

    Two records that both represent a rejection have no PER to compare: identical
    rejections are 0 drift, mismatched ones are treated as maximal (1.0) drift.
    """
    if is_error(a) or is_error(b):
        return 0.0 if a == b else 1.0
    return abs(float(a.get("sentence_per", 0.0)) - float(b.get("sentence_per", 0.0)))


def word_deltas(a: dict, b: dict) -> list[dict]:
    """
    Per-word PER differences, matched on ground-truth word position.

    Deletion/insertion rows shift row indices, so we key on the ground-truth word sequence
    rather than raw row index; rows with no ground-truth word (insertions) are reported
    separately as structural differences.
    """
    def by_gt(rec: dict) -> list[tuple[str, dict]]:
        return [(w["ground_truth_word"], w) for w in rec.get("words", []) if w["ground_truth_word"]]

    left, right = by_gt(a), by_gt(b)
    out: list[dict] = []
    for idx in range(max(len(left), len(right))):
        lw = left[idx][1] if idx < len(left) else None
        rw = right[idx][1] if idx < len(right) else None
        out.append(
            {
                "index": idx,
                "word": (lw or rw or {}).get("ground_truth_word", ""),
                "left_per": None if lw is None else lw["per"],
                "right_per": None if rw is None else rw["per"],
                "delta": (
                    None if lw is None or rw is None else round(abs(lw["per"] - rw["per"]), 6)
                ),
                "structural": lw is None or rw is None
                or lw["ground_truth_word"] != rw["ground_truth_word"],
            }
        )
    return out


def compare(a: dict, b: dict) -> dict:
    """Full comparison record: aggregate delta, per-word deltas, identity flag."""
    if is_error(a) or is_error(b):
        return {
            "identical": a == b,
            "sentence_per_delta": 0.0,
            "max_word_per_delta": 0.0,
            "structural_diffs": [] if a == b else [{"error_mismatch": [a, b]}],
            "word_deltas": [],
            "left_sentence_per": a.get("error", a.get("sentence_per")),
            "right_sentence_per": b.get("error", b.get("sentence_per")),
        }
    deltas = word_deltas(a, b)
    numeric = [d["delta"] for d in deltas if d["delta"] is not None]
    return {
        "identical": a == b,
        "sentence_per_delta": round(per_delta(a, b), 6),
        "max_word_per_delta": round(max(numeric), 6) if numeric else 0.0,
        "structural_diffs": [d for d in deltas if d["structural"]],
        "word_deltas": deltas,
        "left_sentence_per": a.get("sentence_per"),
        "right_sentence_per": b.get("sentence_per"),
    }


# --------------------------------------------------------------------------------------
# Baselines
# --------------------------------------------------------------------------------------
BASELINE_FORMAT_VERSION = 1


def build_baseline(case: RegressionCase) -> dict:
    """Run both paths and package the pinned expectation for one case."""
    client = safe_run(run_client_path, case)
    server = safe_run(run_server_path, case)
    return {
        "format_version": BASELINE_FORMAT_VERSION,
        "case_id": case.case_id,
        "sentence": case.sentence,
        "fixture": case.fixture.to_dict() if case.fixture else None,
        "client_path": client,
        "server_path": server,
        # Pinned divergence between the two paths. The path-agreement test ratchets on
        # this: divergence may shrink freely, but may not grow past PATH_EPSILON.
        "path_divergence": round(per_delta(client, server), 6),
        # How many words the two paths currently disagree about structurally. Also a
        # ratchet: it may go down, never up.
        "path_comparison_structural_count": len(compare(client, server)["structural_diffs"]),
    }


def write_baseline(case: RegressionCase, baseline: dict) -> str:
    os.makedirs(BASELINE_DIR, exist_ok=True)
    with open(case.baseline_path, "w", encoding="utf-8") as fh:
        json.dump(baseline, fh, indent=2, ensure_ascii=False, sort_keys=True)
        fh.write("\n")
    return case.baseline_path


def corpus_summary(cases: list[RegressionCase] | None = None) -> dict:
    cases = cases if cases is not None else discover_cases()
    runnable = fixture_cases(cases)
    with_baseline = [c for c in runnable if os.path.exists(c.baseline_path)]
    tags: dict[str, int] = {}
    for case in cases:
        for tag in case.meta.get("tags", []) or []:
            tags[tag] = tags.get(tag, 0) + 1
    return {
        "total_cases": len(cases),
        "model_free_runnable": len(runnable),
        "with_baseline": len(with_baseline),
        "with_audio": len([c for c in cases if c.audio_path]),
        "tags": tags,
        "target_corpus_size": "30-50 clips incl. noisy/clipped/silent/short/mispronounced",
    }
