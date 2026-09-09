# -*- coding: utf-8 -*-
"""Canonical IPA phoneme inventory, tokenizer and normalizer for Word Wiz AI.

WHY THIS EXISTS
---------------
Three different phoneme "dialects" meet inside the analysis pipeline and were
previously compared against one another with no normalization layer at all:

1. Ground truth -- ``eng_to_ipa`` (see ``core/grapheme_to_phoneme.py``).
   Its ARPAbet->IPA table (``eng_to_ipa/transcribe.py::cmu_to_ipa``) is exactly::

       a->e  ey->eI  aa->ɑ  ae->æ  ah->ə  ao->ɔ  aw->aʊ  ay->aɪ  ch->ʧ  dh->ð
       eh->ɛ er->ər  hh->h  ih->ɪ  jh->ʤ  ng->ŋ  ow->oʊ  oy->ɔɪ  sh->ʃ  th->θ
       uh->ʊ uw->u   zh->ʒ  iy->i  y->j     (everything else passes through as
                                             the plain ASCII ARPAbet letter)

   So the ground truth uses the LIGATURES ʧ (U+02A7) / ʤ (U+02A4), ASCII ``g``
   (U+0067, not IPA ɡ U+0261), ``r`` (not ɹ), and writes the diphthongs as TWO
   codepoints (aɪ, eɪ, oʊ, aʊ, ɔɪ).  It never emits ʌ, ː, ɚ or ɝ.

2. Predictions -- the ``Bobcat9/wav2vec2-timit-ipa-onnx`` CTC vocabulary.  Its
   44-entry ``vocab.json`` (read directly from the local HuggingFace cache) is::

       a æ b c d e f g h i j k l m n o p q r s t u v w x y z
       ð ŋ ɑ ɔ ə ɛ ɪ ʃ ʊ ʒ ʤ ʧ θ  |  '  [UNK]  [PAD]

   Note carefully: this checkpoint ALSO emits the ligatures ʧ / ʤ -- it does
   *not* emit ``tʃ`` / ``dʒ`` as two codepoints, contrary to what is commonly
   assumed about wav2vec2-TIMIT-IPA checkpoints.  It has no ʌ, no ɹ, no ː, no
   stress marks, and no combined diphthong tokens (aɪ arrives as ``a`` + ``ɪ``).

3. The dead eSpeak->IPA map in
   ``routers/handlers/phoneme_processing_handler.py``, written for a model that
   is no longer used.  It is not consulted by anything in this module.

THE BUG THIS FIXES
------------------
Both sides tokenize with ``list(str)`` / ``split("")``, so the two-codepoint
diphthongs ``aɪ``, ``eɪ``, ``oʊ``, ``aʊ``, ``ɔɪ`` are split into two "phonemes".
That inflates ``total_phonemes`` (the PER denominator) and lets a single real
mispronunciation register as two errors.  ``tokenize_ipa`` replaces that with a
longest-match tokenizer so a diphthong is ONE phoneme on every code path.

DESIGN RULES
------------
* stdlib only -- no numpy, torch, transformers.  Other modules import this at
  module scope, so it must be cheap and side-effect free.
* ``tokenize_ipa`` is deliberately lossless for symbols it does not know: an
  unrecognized character becomes its own token rather than being dropped.  That
  matters because ``eng_to_ipa`` falls back to raw SPELLING for out-of-vocabulary
  words, and the caller (not this module) has to decide what to do about that.
* ``normalize_phonemes`` is where symbols are actually folded together.
"""

import os
import unicodedata

__all__ = [
    "CONSONANTS",
    "MONOPHTHONGS",
    "DIPHTHONGS",
    "CANONICAL_PHONEMES",
    "CANONICAL_PHONEME_SET",
    "MULTI_CHAR_TOKENS",
    "DIACRITICS",
    "IGNORED_CHARS",
    "ALIAS_MAP",
    "INVENTORY_FOLD_MAP",
    "KNOWN_SYMBOLS",
    "unknown_symbols",
    "tokenize_ipa",
    "normalize_phonemes",
    "normalize_word_phonemes",
    "is_canonical",
    "normalization_enabled",
    "NORMALIZATION_ENV_VAR",
]


# --------------------------------------------------------------------------
# 1. The canonical inventory -- the single source of truth.
# --------------------------------------------------------------------------
# General American English.  Chosen so that it is reachable from BOTH sources
# above with notation-only rewrites.  Affricates are written as the two-codepoint
# digraphs tʃ / dʒ (and kept as ONE token by the tokenizer); the ligature forms
# ʧ / ʤ that both current sources actually emit are aliases of these.

CONSONANTS = (
    "p", "b", "t", "d", "k", "g",
    "tʃ", "dʒ",
    "f", "v", "θ", "ð", "s", "z", "ʃ", "ʒ", "h",
    "m", "n", "ŋ",
    "l", "r", "w", "j",
)

MONOPHTHONGS = ("i", "ɪ", "ɛ", "æ", "ə", "u", "ʊ", "ɔ", "ɑ")

DIPHTHONGS = ("aɪ", "eɪ", "ɔɪ", "aʊ", "oʊ")

CANONICAL_PHONEMES = CONSONANTS + MONOPHTHONGS + DIPHTHONGS
CANONICAL_PHONEME_SET = frozenset(CANONICAL_PHONEMES)


# --------------------------------------------------------------------------
# 2. Tokenizer tables.
# --------------------------------------------------------------------------
# Multi-codepoint sequences that must survive as a SINGLE token.  Longest match
# wins, and every entry here is exactly 2 codepoints long (asserted below), which
# lets the tokenizer -- and its TypeScript twin -- use a fixed 2-char lookahead.
MULTI_CHAR_TOKENS = (
    "tʃ", "dʒ",          # affricates, when a source spells them out
    "aɪ", "eɪ", "ɔɪ", "aʊ", "oʊ",   # diphthongs
)
assert all(len(t) == 2 for t in MULTI_CHAR_TOKENS)

# Modifiers that belong to the PRECEDING phoneme.  They are appended to the last
# emitted token by the tokenizer and stripped by the normalizer.
DIACRITICS = frozenset(
    (
        "ː",  # ː  length mark
        "ˑ",  # ˑ  half length
        "ʰ",  # ʰ  aspiration
        "ʲ",  # ʲ  palatalized
        "ʷ",  # ʷ  labialized
        "˞",  # ˞  rhoticity
        "̃",  # ̃  nasalization (combining)
        "̥",  # ̥  voiceless (combining)
        "̬",  # ̬  voiced (combining)
        "̩",  # ̩  syllabic (combining)
        "̯",  # ̯  non-syllabic (combining)
        "͡",  # ͡  tie bar
        "͜",  # ͜  tie bar below
    )
)

# Characters that carry no phonemic content at all and are dropped outright.
IGNORED_CHARS = frozenset(
    (
        "ˈ",  # ˈ  primary stress
        "ˌ",  # ˌ  secondary stress
        ".",  # .  syllable break
        "|",  # |  word delimiter (already handled upstream)
        "‖",  # ‖  utterance break
        "‿",  # ‿  linking
        "'", "’", ",", "*", "-", "–", "—",
        " ", "\t", "\n", "\r",
    )
)


# --------------------------------------------------------------------------
# 3. Normalization maps.
# --------------------------------------------------------------------------
# ALIAS_MAP: pure notation.  Same sound, different spelling.  Applying these can
# never change which sound is meant, only how it is written.
ALIAS_MAP = {
    "ʧ": ("tʃ",),
    "ʤ": ("dʒ",),
    "ʦ": ("t", "s"),
    "ʣ": ("d", "z"),
    "ɡ": ("g",),          # U+0261 -> U+0067, matching both current sources
    "ɹ": ("r",),
    "ɻ": ("r",),
    "ʀ": ("r",),
    "ʁ": ("r",),
    "ɚ": ("ə", "r"),      # eng_to_ipa spells ARPAbet "er" as ə + r
    "ɝ": ("ə", "r"),
    "ɫ": ("l",),
    "ʍ": ("w",),
}

# INVENTORY_FOLD_MAP: symbols with no member of the canonical inventory to map
# onto one-to-one, folded to the nearest one.  These are judgment calls, applied
# only when ``fold_inventory=True`` (the default).  The two most consequential:
#   e -> ɛ   there is no /e/ monophthong in this inventory; eng_to_ipa only ever
#            emits ``e`` as the first half of ``eɪ``, so a stranded ``e`` from
#            the acoustic model can never match ground truth as-is.
#   o -> oʊ  same argument; eng_to_ipa only emits ``o`` inside ``oʊ``.
INVENTORY_FOLD_MAP = {
    "ʌ": ("ə",),
    "ɐ": ("ə",),
    "ɜ": ("ə",),
    "ɘ": ("ə",),
    "ɒ": ("ɑ",),
    "e": ("ɛ",),
    "o": ("oʊ",),
    "ɾ": ("t",),          # alveolar flap is a /t/ allophone in GenAm
    "ɽ": ("r",),
    "ʔ": ("t",),          # glottal stop is normally a /t/ allophone
    "y": ("j",),          # eng_to_ipa maps ARPAbet "y" -> j; model vocab has "y"
    "ɨ": ("ɪ",),
    "ʉ": ("u",),
    "ɯ": ("u",),
    "ø": ("ɛ",),
    "œ": ("ɛ",),
    "ɤ": ("ə",),
    "ɲ": ("n",),
    "ɳ": ("n",),
    "ʎ": ("l",),
    "ç": ("h",),
    "ɣ": ("g",),
    "β": ("v",),
    "ɸ": ("f",),
    "a": ("ɑ",),          # bare open front vowel -> nearest inventory member
}


# --------------------------------------------------------------------------
# 4. Public API.
# --------------------------------------------------------------------------

# Every symbol this module has an opinion about: the canonical inventory plus
# everything it knows how to rewrite.  Anything outside this set that survives
# tokenization is a foreign symbol -- most commonly a raw SPELLING letter from an
# eng_to_ipa out-of-vocabulary word.
KNOWN_SYMBOLS = frozenset(
    set(CANONICAL_PHONEMES) | set(ALIAS_MAP) | set(INVENTORY_FOLD_MAP)
)


NORMALIZATION_ENV_VAR = "WWAI_PHONEME_NORMALIZATION"

_TRUTHY = frozenset(("1", "true", "yes", "on", "y", "t"))


def normalization_enabled(env=None) -> bool:
    """True when ``WWAI_PHONEME_NORMALIZATION`` is set to a truthy value.

    Defaults to False so that, with the flag unset, every caller keeps its
    existing byte-identical behaviour.
    """
    source = os.environ if env is None else env
    return str(source.get(NORMALIZATION_ENV_VAR, "")).strip().lower() in _TRUTHY


def tokenize_ipa(s) -> list:
    """Split an IPA string into phoneme tokens using longest match.

    Replaces ``list(s)`` / ``s.split("")``.  Guarantees:

    * ``aɪ eɪ ɔɪ aʊ oʊ`` and ``tʃ dʒ`` come back as ONE token each.
    * Stress marks and other zero-content characters are dropped.
    * Length / aspiration / nasalization diacritics attach to the preceding
      token instead of becoming phonemes of their own.
    * Anything unrecognized is preserved verbatim as a one-character token, so
      no information is silently destroyed.

    >>> tokenize_ipa("maɪ")
    ['m', 'aɪ']
    >>> tokenize_ipa("ˈʧərʧ")
    ['ʧ', 'ə', 'r', 'ʧ']
    """
    if not s:
        return []
    s = unicodedata.normalize("NFC", str(s))

    tokens = []
    i = 0
    n = len(s)
    while i < n:
        ch = s[i]

        if ch in IGNORED_CHARS:
            i += 1
            continue

        if ch in DIACRITICS:
            if tokens:
                tokens[-1] = tokens[-1] + ch
            i += 1
            continue

        if i + 1 < n:
            pair = s[i:i + 2]
            if pair in MULTI_CHAR_TOKENS:
                tokens.append(pair)
                i += 2
                continue

        # Single recognized phoneme, or an unknown character kept verbatim.
        tokens.append(ch)
        i += 1

    return tokens


def _strip_diacritics(token: str) -> str:
    return "".join(c for c in token if c not in DIACRITICS)


def normalize_phonemes(seq, fold_inventory: bool = True) -> list:
    """Map any phoneme sequence into the canonical inventory.

    ``seq`` may be a raw IPA string or an iterable of tokens (each token may
    itself be multi-character -- it is re-tokenized, so passing the output of an
    old ``list(str)`` tokenization works and is repaired).

    Handles: NFC normalization, stress marks, length marks, ligature affricates
    (ʧ/ʤ -> tʃ/dʒ), rhotics (ɹ/ɻ/ʀ/ʁ -> r, ɚ/ɝ -> ə r), IPA script g -> ASCII g,
    and -- when ``fold_inventory`` is True -- folding of symbols outside the
    inventory onto their nearest member.

    >>> normalize_phonemes("ʧərʧ") == normalize_phonemes("tʃərtʃ")
    True
    >>> normalize_phonemes("maɪ")
    ['m', 'aɪ']
    """
    if seq is None:
        return []

    # A list input is JOINED before tokenizing, not tokenized element by element.
    # That is deliberate: the common case is a sequence that was previously split
    # with ``list(str)``, where ``aɪ`` arrived as ``['a', 'ɪ']``.  Re-joining lets
    # longest match put it back together, and it makes
    # ``normalize_phonemes(list) == normalize_phonemes("".join(list))`` always
    # hold, which is what keeps Python and TypeScript in lockstep.
    if isinstance(seq, str):
        tokens = tokenize_ipa(seq)
    else:
        tokens = tokenize_ipa("".join(str(item) for item in seq if item is not None))

    out = []
    for token in tokens:
        token = unicodedata.normalize("NFC", token)
        base = _strip_diacritics(token)
        if not base:
            continue

        replacement = ALIAS_MAP.get(base)
        if replacement is None and fold_inventory:
            replacement = INVENTORY_FOLD_MAP.get(base)
        if replacement is None:
            replacement = (base,)

        for piece in replacement:
            if piece:
                out.append(piece)
    return out


def normalize_word_phonemes(words, fold_inventory: bool = True) -> list:
    """Apply :func:`normalize_phonemes` to a list-of-words-of-phonemes."""
    if not words:
        return []
    return [normalize_phonemes(w, fold_inventory=fold_inventory) for w in words]


def is_canonical(token: str) -> bool:
    """True when ``token`` is a member of the canonical inventory."""
    return token in CANONICAL_PHONEME_SET


def unknown_symbols(seq) -> list:
    """Tokens in ``seq`` that this module has no opinion about.

    Useful as a *weak* signal that a sequence is not really IPA -- e.g. the raw
    spelling ``eng_to_ipa`` falls back to for out-of-vocabulary words.  It is
    only weak: most ASCII letters (w, o, r, d, i, z ...) are also legitimate IPA
    symbols, so "wordwiz" reports nothing.  It reliably flags only letters with
    no IPA reading in this inventory, such as c, q and x.  Detecting OOV ground
    truth properly needs the ``*`` marker from eng_to_ipa, which lives in
    ``core/grapheme_to_phoneme.py``.
    """
    if isinstance(seq, str):
        tokens = tokenize_ipa(seq)
    else:
        tokens = tokenize_ipa("".join(str(i) for i in (seq or []) if i is not None))
    return [t for t in tokens if _strip_diacritics(t) not in KNOWN_SYMBOLS]


if __name__ == "__main__":  # pragma: no cover - manual smoke check
    for sample in ("ðə ʧərʧ ʤəʤd", "ðə tʃərtʃ dʒədʒd", "maɪ deɪ goʊz", "ˈhɛloʊ"):
        print(sample, "->", [normalize_phonemes(w) for w in sample.split(" ")])
