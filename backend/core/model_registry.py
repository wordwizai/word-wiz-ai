"""
Single source of truth for every ML model this project loads — backend AND frontend.

WHY THIS FILE EXISTS
--------------------
Before this module, model ids were hardcoded in five places with no ``revision=``
argument anywhere:

  * ``backend/core/phoneme_extractor_onnx.py``  -> Bobcat9/wav2vec2-timit-ipa-onnx
  * ``backend/core/phoneme_extractor.py``       -> speech31/wav2vec2-large-TIMIT-IPA
                                                   (+ facebook/wav2vec2-base-960h fast path)
  * ``backend/core/word_extractor.py``          -> jonatasgrosman/wav2vec2-large-xlsr-53-english
  * ``frontend/src/services/phonemeExtractor.ts`` -> Bobcat9/wav2vec2-timit-ipa-onnx
  * ``frontend/src/services/wordExtractor.ts``    -> Xenova/whisper-tiny.en

Two consequences, both real:

1. A push to any of those HuggingFace repos silently changes every user's scores
   with no deploy, no version bump and no signal.
2. ``Bobcat9/wav2vec2-timit-ipa-onnx`` is loaded by BOTH the browser and the server.
   Unpinned, the two can end up on *different revisions of the same model*, which
   alone reproduces the client-vs-server scoring divergence this project is trying
   to eliminate.

SAFETY / DEFAULT BEHAVIOUR
--------------------------
Every revision below is currently ``UNPINNED``. ``from_pretrained_kwargs()`` returns
an EMPTY dict when a model is unpinned, so wiring this module into a loader changes
nothing at all until someone actually fills in a revision. There is deliberately no
guessed or invented commit SHA in this file: a wrong SHA would break every model load.

HOW TO PIN (one command, needs network — run it yourself, no agent ran it)
-------------------------------------------------------------------------
From ``backend/`` with the venv interpreter::

    PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m core.model_registry --resolve

That prints, for each model, the current ``main`` commit SHA and a ready-to-paste
``revision=`` line. Paste the SHAs into ``_MODELS`` below, replacing ``UNPINNED``.
Then re-run ``--check`` to confirm nothing is left unpinned, and re-run the
regression harness (``backend/tests/regression``) to confirm scores did not move.

Per-model environment override (useful for a staged rollout or an emergency
un-pin without a deploy)::

    WWAI_PIN_PHONEME_IPA_ONNX=<sha>       # overrides the declared revision
    WWAI_PIN_PHONEME_IPA_ONNX=main        # explicitly float this one model

Global escape hatch::

    WWAI_IGNORE_MODEL_PINS=true           # ignore every declared pin (back to today)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

# Sentinel meaning "we have not resolved this repo's commit SHA yet".
# Do NOT replace this with a made-up hex string.
UNPINNED: str | None = None

_ENV_PREFIX = "WWAI_PIN_"
_ENV_IGNORE_ALL = "WWAI_IGNORE_MODEL_PINS"


@dataclass(frozen=True)
class ModelPin:
    """One model, declared once, consumed by one or more code paths."""

    key: str
    repo_id: str
    revision: str | None
    purpose: str
    consumers: tuple[str, ...] = field(default_factory=tuple)
    # "backend", "frontend", or "both". "both" models are the dangerous ones:
    # a revision skew between the two sides changes scores asymmetrically.
    side: str = "backend"
    # Extra files fetched from the same repo (hf_hub_download) that must be
    # pinned to the same revision as the processor/config.
    files: tuple[str, ...] = field(default_factory=tuple)

    @property
    def env_var(self) -> str:
        return f"{_ENV_PREFIX}{self.key}"

    @property
    def is_pinned(self) -> bool:
        return bool(self.revision)


# ---------------------------------------------------------------------------
# THE REGISTRY.  Edit revisions HERE and nowhere else.
# ---------------------------------------------------------------------------
_MODELS: dict[str, ModelPin] = {
    # ---- shared by browser AND server: the highest-risk entry in this file ----
    "PHONEME_IPA_ONNX": ModelPin(
        key="PHONEME_IPA_ONNX",
        repo_id="Bobcat9/wav2vec2-timit-ipa-onnx",
        revision=UNPINNED,  # TODO(pin): run `python -m core.model_registry --resolve`
        purpose="wav2vec2-TIMIT-IPA, ONNX. Emits the IPA phonemes that PER is computed on.",
        consumers=(
            "backend/core/phoneme_extractor_onnx.py:PhonemeExtractorONNX.__init__",
            "frontend/src/services/phonemeExtractor.ts:ClientPhonemeExtractor.modelName",
        ),
        side="both",
        files=("model.onnx",),
    ),
    # ---- backend only ----
    "PHONEME_IPA_TORCH": ModelPin(
        key="PHONEME_IPA_TORCH",
        repo_id="speech31/wav2vec2-large-TIMIT-IPA",
        revision=UNPINNED,  # TODO(pin)
        purpose="PyTorch fallback phoneme extractor (used when USE_ONNX_BACKEND=false or ONNX load fails).",
        consumers=("backend/core/phoneme_extractor.py:PhonemeExtractor.__init__",),
        side="backend",
    ),
    "PHONEME_FAST_FALLBACK": ModelPin(
        key="PHONEME_FAST_FALLBACK",
        repo_id="facebook/wav2vec2-base-960h",
        revision=UNPINNED,  # TODO(pin)
        purpose=(
            "Substituted for PHONEME_IPA_TORCH when use_fast_models is on. NOTE: this is a "
            "grapheme ASR model, not an IPA model - it does not emit IPA at all."
        ),
        consumers=("backend/core/phoneme_extractor.py:PhonemeExtractor.__init__ (use_fast_model branch)",),
        side="backend",
    ),
    "WORD_ASR_LOCAL": ModelPin(
        key="WORD_ASR_LOCAL",
        repo_id="jonatasgrosman/wav2vec2-large-xlsr-53-english",
        revision=UNPINNED,  # TODO(pin)
        purpose="Local word/transcript extraction (WordExtractor). Produces the word list PER is scored against.",
        consumers=("backend/core/word_extractor.py:WordExtractor.__init__",),
        side="backend",
    ),
    # ---- frontend only ----
    "WORD_ASR_CLIENT": ModelPin(
        key="WORD_ASR_CLIENT",
        repo_id="Xenova/whisper-tiny.en",
        revision=UNPINNED,  # TODO(pin)
        purpose="Browser-side word extraction via Transformers.js.",
        consumers=("frontend/src/services/wordExtractor.ts:ClientWordExtractor.modelName",),
        side="frontend",
    ),
}


# ---------------------------------------------------------------------------
# Lookup API
# ---------------------------------------------------------------------------
def all_models() -> dict[str, ModelPin]:
    """Every declared model, keyed by registry key."""
    return dict(_MODELS)


def get(key: str) -> ModelPin:
    try:
        return _MODELS[key]
    except KeyError:
        raise KeyError(
            f"Unknown model registry key {key!r}. Known keys: {sorted(_MODELS)}"
        ) from None


def repo_id(key: str) -> str:
    """The HuggingFace repo id for a registry key."""
    return get(key).repo_id


def resolve_revision(key: str) -> str | None:
    """
    Effective revision for a model, honouring env overrides.

    Precedence:  WWAI_IGNORE_MODEL_PINS  >  WWAI_PIN_<KEY>  >  declared revision.
    Returns None when nothing is pinned (which is today's behaviour).
    """
    if os.getenv(_ENV_IGNORE_ALL, "").strip().lower() in ("1", "true", "yes"):
        return None
    pin = get(key)
    override = os.getenv(pin.env_var, "").strip()
    if override:
        return override
    return pin.revision


def from_pretrained_kwargs(key: str) -> dict:
    """
    kwargs to splat into ``*.from_pretrained(...)`` / ``hf_hub_download(...)``.

    Returns ``{}`` when the model is unpinned, so adding this call to a loader is a
    no-op until a revision is actually declared::

        from .model_registry import repo_id, from_pretrained_kwargs
        name = repo_id("PHONEME_IPA_ONNX")
        Wav2Vec2Processor.from_pretrained(name, **from_pretrained_kwargs("PHONEME_IPA_ONNX"))
    """
    rev = resolve_revision(key)
    return {"revision": rev} if rev else {}


def key_for_repo(repo: str) -> str | None:
    """Reverse lookup: registry key for a HuggingFace repo id, or None."""
    for k, pin in _MODELS.items():
        if pin.repo_id == repo:
            return k
    return None


def unpinned_keys() -> list[str]:
    """Keys with no effective revision. Non-empty == scoring can change without a deploy."""
    return sorted(k for k in _MODELS if not resolve_revision(k))


def shared_models() -> list[ModelPin]:
    """Models loaded by BOTH browser and server. These must never skew."""
    return [p for p in _MODELS.values() if p.side == "both"]


def frontend_registry() -> dict:
    """
    Serialisable view of the frontend-visible models, for generating a TS constants
    file so the browser cannot drift from the server. See ``--emit-frontend``.
    """
    return {
        pin.key: {"repoId": pin.repo_id, "revision": resolve_revision(pin.key)}
        for pin in _MODELS.values()
        if pin.side in ("frontend", "both")
    }


# ---------------------------------------------------------------------------
# CLI:  python -m core.model_registry [--check|--resolve|--emit-frontend]
# ---------------------------------------------------------------------------
def _cmd_check() -> int:
    print("Model registry")
    print("=" * 78)
    for pin in _MODELS.values():
        rev = resolve_revision(pin.key)
        state = rev if rev else "UNPINNED  <-- floats with upstream main"
        print(f"  {pin.key:24s} {pin.repo_id}")
        print(f"  {'':24s} side={pin.side:8s} revision={state}")
        for c in pin.consumers:
            print(f"  {'':24s}   used by {c}")
        print()
    missing = unpinned_keys()
    if missing:
        print(f"{len(missing)} model(s) UNPINNED: {', '.join(missing)}")
        print("Run  `python -m core.model_registry --resolve`  to get the SHAs to paste in.")
        return 1
    print("All models pinned.")
    return 0


def _cmd_resolve() -> int:
    """Hits the HuggingFace API. Network required. Never run automatically."""
    try:
        from huggingface_hub import HfApi
    except ImportError:
        print("huggingface_hub is not installed in this interpreter; cannot resolve.")
        return 2
    api = HfApi()
    print("Resolving current `main` commit for each repo (network)...\n")
    failures = 0
    for pin in _MODELS.values():
        try:
            sha = api.model_info(pin.repo_id).sha
        except Exception as exc:  # noqa: BLE001 - report, don't crash the whole sweep
            print(f"  # {pin.key}: FAILED to resolve {pin.repo_id}: {exc}")
            failures += 1
            continue
        print(f'  # {pin.key}  ({pin.repo_id})')
        print(f'  revision="{sha}",')
    print("\nPaste each `revision=` line into the matching ModelPin in _MODELS above,")
    print("replacing `revision=UNPINNED`, then re-run `--check`.")
    return 1 if failures else 0


def _cmd_emit_frontend() -> int:
    """
    Print a TypeScript constants module to stdout. A frontend owner can redirect it to
    ``frontend/src/config/modelRegistry.ts`` and have the services import from it, so the
    browser and the server read the same pins.
    """
    import json

    reg = frontend_registry()
    print("// GENERATED by backend/core/model_registry.py --emit-frontend. Do not edit by hand.")
    print("// Regenerate after changing a pin, so the browser cannot drift from the server.")
    print("export interface ModelPin { repoId: string; revision: string | null }")
    print("export const MODEL_REGISTRY = {")
    for key, val in reg.items():
        rev = json.dumps(val["revision"]) if val["revision"] else "null"
        print(f'  {key}: {{ repoId: {json.dumps(val["repoId"])}, revision: {rev} }},')
    print("} as const satisfies Record<string, ModelPin>;")
    return 0


def main(argv: list[str] | None = None) -> int:
    import sys

    args = list(sys.argv[1:] if argv is None else argv)
    cmd = args[0] if args else "--check"
    if cmd == "--check":
        return _cmd_check()
    if cmd == "--resolve":
        return _cmd_resolve()
    if cmd == "--emit-frontend":
        return _cmd_emit_frontend()
    print(__doc__)
    print("usage: python -m core.model_registry [--check|--resolve|--emit-frontend]")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
