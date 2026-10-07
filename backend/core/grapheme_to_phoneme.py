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
import threading
from collections import OrderedDict, namedtuple
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


_COUPLING_WARNED = False


def _warn_if_tokenization_uncoupled() -> None:
    """Warn once when the ground-truth and prediction tokenizers disagree.

    Strict mode tokenizes the ground truth with ``phoneme_inventory.tokenize_ipa``,
    which keeps diphthongs whole ('brown' -> b r aʊ n).  The acoustic model emits
    them split (b r a ʊ n) unless WWAI_PHONEME_NORMALIZATION rejoins them.  Enable
    exactly one of the two and every diphthong scores as an error on both sides:

        legacy GT + raw pred        -> PER 0.00   (consistent)
        strict GT + normalized pred -> PER 0.00   (consistent)
        strict GT + raw pred        -> PER 0.50   (broken)
        legacy GT + normalized pred -> PER 0.40   (broken)

    They are a matched pair: flip both, or neither.
    """
    global _COUPLING_WARNED
    if _COUPLING_WARNED:
        return
    strict = _strict_enabled()
    normalized = _env_flag("WWAI_PHONEME_NORMALIZATION", False)
    if strict != normalized:
        _COUPLING_WARNED = True
        logger.warning(
            "TOKENIZATION MISMATCH: WWAI_G2P_STRICT=%s but "
            "WWAI_PHONEME_NORMALIZATION=%s. Ground truth and predictions are "
            "being tokenized differently, so diphthongs (aɪ eɪ oʊ aʊ ɔɪ) will "
            "score as errors and PER will be inflated. Set both or neither.",
            strict, normalized,
        )


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


#: Kill switch for keeping apostrophes inside words. When truthy, clean_sentence strips
#: every straight apostrophe exactly as before ("it's" -> "its"). Read at call time.
LEGACY_SENTENCE_CLEANING_FLAG = "WWAI_LEGACY_SENTENCE_CLEANING"

_APOSTROPHES = str.maketrans({"\u2019": "'", "\u2018": "'", "\u02bc": "'"})
# An apostrophe with a letter on both sides is part of a word ("it's", "don't",
# "dog's"); any other one is a quote mark or a plural possessive ("dogs'").
_STRAY_APOSTROPHE_RE = re.compile(r"(?<![a-z])'|'(?![a-z])")


def clean_sentence(sentence: str) -> str:
    """The cleanup PhonemeAssistant.process_audio applies to a sentence before G2P.

    Lowercases and drops . , ? ! and quote marks, but keeps apostrophes inside
    words: CMUdict knows "it's" and "didn't", while "its"-style spellings like
    "dont" or "didnt" are unknown words that would be scored against their
    spelling. Curly apostrophes become straight ones first.

    Shared with the accuracy benchmark (backend/tests/benchmark) so both score the
    exact same ground truth. WWAI_LEGACY_SENTENCE_CLEANING brings back the old
    cleanup, which stripped every straight apostrophe.
    """
    if os.environ.get(LEGACY_SENTENCE_CLEANING_FLAG, "").strip().lower() in ("1", "true", "yes", "on"):
        return (
            sentence.strip().lower()
            .replace(".", "")
            .replace(",", "")
            .replace("?", "")
            .replace("!", "")
            .replace("'", "")
        )
    cleaned = (
        sentence.strip().lower()
        .translate(_APOSTROPHES)
        .replace(".", "")
        .replace(",", "")
        .replace("?", "")
        .replace("!", "")
    )
    return _STRAY_APOSTROPHE_RE.sub("", cleaned)


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

    _warn_if_tokenization_uncoupled()

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


# ---------------------------------------------------------------------------
# Pronunciation variants (word scoring v2)
#
# eng_to_ipa opens its sqlite database and scans the whole dictionary table on
# every query (core/cmu_index.py adds an index at image build), so variants are
# fetched for a whole sentence in ONE query and cached per word.  Only
# successful lookups are cached: a transient sqlite error must not be
# remembered as "this word has no variants".
# ---------------------------------------------------------------------------

#: A token with no letter at all (a number such as "3", or punctuation).
#: eng_to_ipa marks an unknown word with "*", but hands a bare number back
#: unmarked, so these are rejected before the lookup.
_HAS_LETTER = re.compile(r"[^\W\d_]", re.UNICODE)

_variant_cache: "OrderedDict[tuple[str, bool], tuple]" = OrderedDict()
_variant_cache_lock = threading.Lock()
_variant_stats = {"hits": 0, "misses": 0}

VariantCacheInfo = namedtuple("VariantCacheInfo", "hits misses maxsize currsize")


def _parse_variants(raws, strict: bool) -> tuple:
    """eng_to_ipa's transcriptions of one word -> unique phoneme tuples."""
    variants = []
    for raw in raws:
        if "*" in raw:  # eng_to_ipa's out-of-vocabulary marker
            continue
        if strict:
            phonemes = tuple(tokenize_ipa(_strict_clean(raw)))
        else:
            phonemes = tuple(_legacy_clean(raw))
        if phonemes and phonemes not in variants:
            variants.append(phonemes)
    return tuple(variants)


def _lookup_variants(words: list[str], strict: bool) -> dict[str, tuple]:
    """
    Variants for each distinct word, with at most one dictionary query.

    Raises when that query fails, so nothing is cached for the words it was
    for.  A word whose transcription cannot be tokenized gets ``()`` for this
    call only.
    """
    found: dict[str, tuple] = {}
    missing: list[str] = []
    with _variant_cache_lock:
        for word in words:
            if word in found or word in missing:
                continue
            if not _HAS_LETTER.search(word) or any(ch.isspace() for ch in word):
                found[word] = ()
                continue
            key = (word, strict)
            if key in _variant_cache:
                _variant_cache.move_to_end(key)
                _variant_stats["hits"] += 1
                found[word] = _variant_cache[key]
            else:
                missing.append(word)

    if not missing:
        return found

    per_word = G2p.ipa_list(" ".join(missing))
    if len(per_word) != len(missing):  # pragma: no cover - defensive
        raise ValueError(
            f"eng_to_ipa returned {len(per_word)} entries for {len(missing)} words"
        )

    parsed: dict[str, tuple] = {}
    for word, raws in zip(missing, per_word):
        try:
            parsed[word] = _parse_variants(raws, strict)
        except Exception:  # never fail the request over an optional lookup
            found[word] = ()

    with _variant_cache_lock:
        _variant_stats["misses"] += len(missing)
        for word, variants in parsed.items():
            _variant_cache[(word, strict)] = variants
            _variant_cache.move_to_end((word, strict))
        while len(_variant_cache) > _CACHE_SIZE:
            _variant_cache.popitem(last=False)

    found.update(parsed)
    return found


def sentence_pronunciation_variants(
    words, strict: bool | None = None,
) -> dict[str, list[list[str]]]:
    """:func:`pronunciation_variants` for every word of a sentence at once.

    Words not cached yet are looked up in ONE dictionary query, and repeated
    words are asked for once.  Returns ``{word: variants}`` with a key for
    every word given.  Never raises.  If the lookup fails, those words get
    ``[]`` and nothing is cached, so the next call tries again.

    Args:
        words: already-cleaned words, e.g. the words of the ground truth.
        strict: override ``WWAI_G2P_STRICT``.  ``None`` (default) reads the
            environment variable, like :func:`grapheme_to_phoneme`.
    """
    if strict is None:
        strict = _strict_enabled()
    words = [str(w or "") for w in (words or [])]
    try:
        found = _lookup_variants(words, bool(strict))
    except Exception as exc:  # never fail the request over an optional lookup
        logger.warning(
            "pronunciation variant lookup failed for %d word(s) (%s: %s); "
            "scoring against the primary pronunciation only",
            len(words), type(exc).__name__, exc,
        )
        found = {}
    # Fresh mutable copies every call -- callers must never see cached state.
    return {w: [list(v) for v in found.get(w, ())] for w in words}


def pronunciation_variants(word: str, strict: bool | None = None) -> list[list[str]]:
    """Every CMUdict pronunciation of one already-cleaned word.

    CMUdict lists more than one valid pronunciation for many words ("to" is
    tu / tə / tɪ, "the" is ði / ðə), while :func:`grapheme_to_phoneme` keeps only
    one.  Each variant is tokenized exactly the way ``grapheme_to_phoneme``
    tokenizes the word in the same mode, so the primary pronunciation is always
    one of them.  Order follows ``eng_to_ipa`` and duplicates are dropped.

    Returns ``[]`` for out-of-vocabulary words and numbers, and never raises.
    For a whole sentence, :func:`sentence_pronunciation_variants` makes one
    dictionary query instead of one per word.

    Args:
        word: one word, already cleaned the way the sentence is before G2P.
        strict: override ``WWAI_G2P_STRICT``.  ``None`` (default) reads the
            environment variable, like :func:`grapheme_to_phoneme`.
    """
    word = str(word or "")
    return sentence_pronunciation_variants([word], strict=strict)[word]


def clear_cache() -> None:
    """Drop every memoised conversion (used by tests and after flag changes)."""
    _convert_cached.cache_clear()
    _convert_raw.cache_clear()
    _isin_cmu.cache_clear()
    with _variant_cache_lock:
        _variant_cache.clear()
        _variant_stats.update(hits=0, misses=0)


def cache_info() -> dict:
    """Memoisation statistics, for diagnostics."""
    with _variant_cache_lock:
        variants = VariantCacheInfo(
            _variant_stats["hits"], _variant_stats["misses"], _CACHE_SIZE, len(_variant_cache),
        )
    return {
        "sentences": _convert_cached.cache_info(),
        "words": _convert_raw.cache_info(),
        "cmudict_lookups": _isin_cmu.cache_info(),
        "variants": variants,
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
