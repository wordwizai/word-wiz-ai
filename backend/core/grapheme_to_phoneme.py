"""Grapheme -> phoneme (IPA) conversion for ground-truth generation.

Backed by ``eng_to_ipa`` (a CMUdict lookup).  Two long-standing bugs are
addressed here:

1. **Fail-open on out-of-vocabulary words.**  ``eng_to_ipa`` marks words it
   cannot find with a trailing ``*`` and returns the *original spelling*.  The
   old code stripped the ``*`` and called ``list()`` on the result, so
   ``"wordwiz"`` produced ground-truth "phonemes"
   ``['w','o','r','d','w','i','z']`` -- letters masquerading as sounds.  Every
   name, invented story word, or GPT-generated word was scored against its
   spelling.  Bare numerals (``"3"``) have the same problem without even the
   ``*`` marker.

2. **Silent truncation.**  ``zip(grapheme.split(" "), converted.split(" "))``
   stops at the shorter list.  ``eng_to_ipa`` collapses runs of whitespace, so
   ``"a  b   c"`` produced *three* input tokens paired against the wrong
   phonemes and dropped the tail entirely.  A short ground truth then blows up
   downstream with an IndexError.

Behaviour is gated so production is untouched by default:

* ``WWAI_G2P_STRICT``   (default **off**) -- when off, the returned values are
  byte-identical to the historical implementation.  When on, OOV words become
  an explicit :data:`UNKNOWN_PHONEME` marker, the token count is always
  preserved, and punctuation is stripped properly.
* ``WWAI_G2P_LOG_OOV``  (default **on**) -- loud logging of OOV words and of
  token-count mismatches.  Logging only; it never changes returned values.

Regardless of the flag, every returned element is a :class:`G2PWord` -- a
2-tuple ``(word, phonemes)`` (so ``for word, phonemes in ...`` and equality
against plain tuples still work exactly as before) that additionally carries
``.oov`` and ``.source`` so callers can tell a real transcription from a
fallback.
"""

from __future__ import annotations

import logging
import os
import re
import string
from functools import lru_cache

# idk why I needed to do this this is gonna be a very simple program
# from g2p_en import G2p
import eng_to_ipa as G2p

# ---------------------------------------------------------------------------
# Phoneme tokenizer.
#
# ``backend/core/phoneme_inventory.py`` (owned by another agent) provides
# ``tokenize_ipa()``: a longest-match tokenizer that keeps multi-codepoint IPA
# symbols such as "aɪ", "tʃ" and "oʊ" together instead of splitting them into
# separate characters.  It may not exist yet, so fall back to the historical
# per-codepoint ``list()`` behaviour.
# ---------------------------------------------------------------------------
try:  # pragma: no cover - exercised by whichever import shape is available
    from .phoneme_inventory import tokenize_ipa  # type: ignore

    _HAVE_IPA_TOKENIZER = True
except ImportError:  # pragma: no cover
    try:
        from phoneme_inventory import tokenize_ipa  # type: ignore

        _HAVE_IPA_TOKENIZER = True
    except ImportError:

        def tokenize_ipa(s: str) -> list[str]:
            """Fallback tokenizer: one token per codepoint (legacy behaviour)."""
            return list(s)

        _HAVE_IPA_TOKENIZER = False


logger = logging.getLogger(__name__)

#: Emitted (strict mode only) in place of a word's phonemes when no real
#: transcription is available.  Downstream code should treat a word whose
#: phonemes are ``[UNKNOWN_PHONEME]`` as *unscoreable* rather than as a
#: pronunciation error.
UNKNOWN_PHONEME = "<unk>"

_STRESS_MARKS = "ˈˌ"  # ˈ ˌ

# Characters that are never part of an IPA transcription and must not survive
# into a phoneme list (strict mode).
_NON_PHONEME_CHARS = frozenset(
    _STRESS_MARKS
    + string.punctuation
    + string.whitespace
    + "‘’“”–—…"  # ‘ ’ “ ” – — …
)

# Punctuation that may legitimately hug a word in a sentence.  Internal
# apostrophes/hyphens are kept because CMUdict knows "don't" and "well-known".
_EDGE_PUNCT = string.punctuation + string.whitespace + "‘’“”–—…"

_HAS_ALNUM = re.compile(r"[^\W_]", re.UNICODE)
_HYPHENS = re.compile(r"[-‐‑–—]")

_CACHE_SIZE = 2048


def _env_flag(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _strict_enabled() -> bool:
    """``WWAI_G2P_STRICT`` -- OFF by default (production behaviour unchanged)."""
    return _env_flag("WWAI_G2P_STRICT", False)


def _log_oov_enabled() -> bool:
    """``WWAI_G2P_LOG_OOV`` -- ON by default (logging only, no value change)."""
    return _env_flag("WWAI_G2P_LOG_OOV", True)


class G2PWord(tuple):
    """``(word, phonemes)`` pair that also remembers where the phonemes came from.

    It is a real ``tuple`` of length 2, so all existing consumers
    (``for word, phonemes in ...``, ``gt[i][1]``, ``==`` against plain tuples,
    ``json.dumps``) behave exactly as before.

    Extra attributes:
        oov:    True when ``eng_to_ipa`` had no entry for the word.
        source: "cmudict", "cmudict:hyphen-split", "spelling" (legacy fail-open),
                "punctuation" or "unknown".
    """

    # NOTE: a nonempty __slots__ is not allowed on a tuple subclass, so these
    # instances carry a small __dict__.  The tuple payload itself is unchanged.

    def __new__(cls, pair, oov: bool = False, source: str = "cmudict"):
        self = super().__new__(cls, pair)
        if len(self) != 2:
            raise ValueError(f"G2PWord expects a (word, phonemes) pair, got {pair!r}")
        object.__setattr__(self, "oov", bool(oov))
        object.__setattr__(self, "source", source)
        return self

    @property
    def word(self) -> str:
        return self[0]

    @property
    def phonemes(self) -> list:
        return self[1]


# ---------------------------------------------------------------------------
# eng_to_ipa wrappers (memoised -- these are on the request hot path)
# ---------------------------------------------------------------------------


@lru_cache(maxsize=_CACHE_SIZE)
def _convert_raw(text: str) -> str:
    return G2p.convert(text)


@lru_cache(maxsize=_CACHE_SIZE)
def _isin_cmu(word: str) -> bool:
    try:
        return bool(G2p.isin_cmu(word))
    except Exception:  # pragma: no cover - defensive; never fail the request
        return False


def _legacy_clean(phonemes: str) -> str:
    """The exact character-stripping the original implementation performed."""
    return (
        phonemes.replace("ˈ", "")
        .replace("ˌ", "")
        .replace("*", "")
        .replace(",", "")
        .replace("'", "")
    )


def _strict_clean(phonemes: str) -> str:
    return "".join(ch for ch in phonemes if ch not in _NON_PHONEME_CHARS)


# ---------------------------------------------------------------------------
# Conversion strategies
# ---------------------------------------------------------------------------


def _convert_legacy(grapheme: str) -> tuple:
    """Historical behaviour, preserved byte-for-byte (plus logging)."""
    unfiltered_phonemes = _convert_raw(grapheme)
    normalized = unfiltered_phonemes.split(" ")
    words = grapheme.split(" ")

    if len(words) != len(normalized) and _log_oov_enabled():
        logger.warning(
            "g2p token-count mismatch: %d input tokens vs %d converted tokens for %r. "
            "zip() will silently drop %d trailing word(s) from the ground truth. "
            "Set WWAI_G2P_STRICT=true to preserve word count.",
            len(words),
            len(normalized),
            grapheme,
            max(0, len(words) - len(normalized)),
        )

    output = []
    for word, phonemes in zip(words, normalized):
        oov = "*" in phonemes
        if oov and _log_oov_enabled():
            logger.warning(
                "g2p OOV word %r: eng_to_ipa has no entry, so its SPELLING is being "
                "used as ground-truth phonemes (%r). These are letters, not sounds -- "
                "the learner will be scored against nonsense. "
                "Set WWAI_G2P_STRICT=true to emit %r instead.",
                word,
                _legacy_clean(phonemes),
                UNKNOWN_PHONEME,
            )
        output.append(
            (
                word,
                tuple(list(_legacy_clean(phonemes))),  # remove stress markers
                oov,
                "spelling" if oov else "cmudict",
            )
        )
    return tuple(output)


def _convert_token_strict(token: str) -> tuple[tuple, bool, str]:
    """Convert one whitespace-delimited token.  Never returns spelling-as-phonemes."""
    core = token.strip(_EDGE_PUNCT)

    if not core or not _HAS_ALNUM.search(core):
        # Pure punctuation ("--", "...").  Keep the slot so word count is
        # preserved, but it carries no sounds.
        return (), False, "punctuation"

    raw = _convert_raw(core)
    oov = ("*" in raw) or (not _isin_cmu(core))

    if not oov:
        return tuple(tokenize_ipa(_strict_clean(raw))), False, "cmudict"

    # Recovery: hyphenated compounds where each part is known
    # ("check-up" -> "check" + "up").
    parts = [p for p in _HYPHENS.split(core) if p and _HAS_ALNUM.search(p)]
    if len(parts) > 1:
        converted_parts = []
        for part in parts:
            part_raw = _convert_raw(part)
            if "*" in part_raw or not _isin_cmu(part):
                converted_parts = []
                break
            converted_parts.append(_strict_clean(part_raw))
        if converted_parts:
            joined = "".join(converted_parts)
            return tuple(tokenize_ipa(joined)), False, "cmudict:hyphen-split"

    if _log_oov_enabled():
        logger.warning(
            "g2p OOV word %r: no CMUdict entry. Emitting %r (unscoreable) instead of "
            "its spelling. Downstream scoring should skip this word.",
            token,
            UNKNOWN_PHONEME,
        )
    return (UNKNOWN_PHONEME,), True, "unknown"


def _convert_strict(grapheme: str) -> tuple:
    """Word-count-preserving conversion with explicit OOV handling."""
    tokens = grapheme.split()  # collapses runs of whitespace, drops empties
    output = []
    for token in tokens:
        phonemes, oov, source = _convert_token_strict(token)
        output.append((token, phonemes, oov, source))

    # Invariant: N words in -> N entries out.  Loud rather than silent.
    if len(output) != len(tokens):  # pragma: no cover - defensive
        raise AssertionError(
            f"g2p dropped words: {len(tokens)} in, {len(output)} out for {grapheme!r}"
        )
    return tuple(output)


@lru_cache(maxsize=_CACHE_SIZE)
def _convert_cached(grapheme: str, strict: bool) -> tuple:
    return _convert_strict(grapheme) if strict else _convert_legacy(grapheme)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def grapheme_to_phoneme(grapheme, strict: bool | None = None) -> list[tuple]:
    """
    Converts a string of graphemes into phonemes by removing stress markers and
    returning a list of (word, list of individual phonemes).

    Each element is a :class:`G2PWord`, i.e. a ``(word, phonemes)`` tuple that
    also exposes ``.oov`` and ``.source``.

    Args:
        grapheme: the sentence to convert.
        strict: override ``WWAI_G2P_STRICT``.  ``None`` (default) reads the
            environment variable, which defaults to OFF.

    In strict mode the number of returned entries always equals
    ``len(grapheme.split())`` and out-of-vocabulary words yield
    ``[UNKNOWN_PHONEME]`` rather than their spelling.
    """
    if strict is None:
        strict = _strict_enabled()

    cached = _convert_cached(grapheme, bool(strict))
    # Fresh mutable copies every call -- callers must never see cached state.
    return [
        G2PWord((word, list(phonemes)), oov=oov, source=source)
        for word, phonemes, oov, source in cached
    ]


def grapheme_to_phoneme_detailed(grapheme, strict: bool | None = None) -> list[dict]:
    """Same conversion, returned as plain dicts for callers that prefer data."""
    return [
        {"word": w.word, "phonemes": w.phonemes, "oov": w.oov, "source": w.source}
        for w in grapheme_to_phoneme(grapheme, strict=strict)
    ]


def oov_words(grapheme, strict: bool | None = None) -> list[str]:
    """The words in ``grapheme`` that ``eng_to_ipa`` could not transcribe."""
    return [w.word for w in grapheme_to_phoneme(grapheme, strict=strict) if w.oov]


def clear_cache() -> None:
    """Drop every memoised conversion (used by tests and after flag changes)."""
    _convert_cached.cache_clear()
    _convert_raw.cache_clear()
    _isin_cmu.cache_clear()


def cache_info() -> dict:
    """Memoisation statistics, for diagnostics."""
    return {
        "sentences": _convert_cached.cache_info(),
        "words": _convert_raw.cache_info(),
        "cmudict_lookups": _isin_cmu.cache_info(),
        "ipa_tokenizer": "phoneme_inventory.tokenize_ipa"
        if _HAVE_IPA_TOKENIZER
        else "list() fallback",
    }


if __name__ == "__main__":
    print(grapheme_to_phoneme("hello world"))
    print(grapheme_to_phoneme("wordwiz  is   fun", strict=True))
    print(grapheme_to_phoneme_detailed("zyzzyva blorp", strict=True))
    # extractor = PhonemeExtractor("speech31/wav2vec2-large-english-phoneme-v2", lambda x: x)
    # print(audio_recording.record_and_process_pronunciation("hello world", extraction_model=extractor))
