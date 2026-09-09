"""
Phonetic (featural) distance between English IPA symbols.

WHY THIS EXISTS
---------------
`compute_per` in `process_audio.py` uses an unweighted Levenshtein distance, so
every symbol mismatch costs exactly 1.0.  That means a child who says "water"
with a perfectly normal American flap ([ˈwɔɾɚ] instead of [ˈwɔtər]) is scored
exactly as wrong as a child who reads "cat" as "bat".  That is the documented
"high PER despite good pronunciation" problem, and for a 6-year-old it means
being told they got it wrong when they got it right.

This module supplies two things:

1. A featural distance in [0.0, 1.0] so that phonetically NEAR misses cost less
   than phonetically FAR misses.  /p/ vs /b/ differs only in voicing and is
   cheap; /p/ vs /k/ differs in place and is expensive; /p/ vs /i/ is a
   different segment class entirely and costs the maximum.

2. An explicit, auditable ALLOWED_VARIATIONS table of pairs that cost ~0.
   These are things a fluent adult native speaker does routinely.  They are
   NOT reading errors and must never be scored as such.  Every entry carries a
   written justification so a reviewer (or a speech-language pathologist) can
   audit the list without reading the code.

DESIGN CONSTRAINTS
------------------
* Pure standard library.  No numpy, no torch.  Import must be cheap because
  `process_audio` is imported on the request path.
* `phonetic_distance` is called from inside a Levenshtein inner loop that is
  itself inside an alignment DP loop (O(n*m) per call, called O(m*n*k) times).
  Every lookup is memoised in a plain dict; after warm-up the cost of a call is
  one dict hit.

SCOPE / LIMITS
--------------
* American English inventory only.  Symbols not in the feature table fall back
  to a conservative default (see `_UNKNOWN_DISTANCE`) rather than raising, so a
  novel symbol from a future acoustic model degrades gracefully instead of
  crashing analysis.
* Suprasegmentals (stress, length, tone) are ignored; the upstream extractor
  does not emit them.
* This is a *similarity heuristic*, not a phonological theory. The numbers were
  chosen so the ORDERING is defensible (allowed < near-miss < far-miss <
  cross-class), not because any particular value is canonical.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Feature inventory
# ---------------------------------------------------------------------------

# Place of articulation, front of the mouth -> back, on an arbitrary but
# monotonic 0..10 scale.  Distances between adjacent places are intentionally
# non-uniform: dental/alveolar are genuinely closer to each other than
# bilabial/velar are.
_PLACE = {
    "bilabial": 0.0,
    "labiodental": 1.0,
    "dental": 2.5,
    "alveolar": 3.5,
    "postalveolar": 6.0,
    "retroflex": 6.5,
    "palatal": 7.5,
    "velar": 9.0,
    "labiovelar": 8.5,   # /w/: velar constriction with lip rounding
    "glottal": 10.0,
}
_PLACE_SPAN = 10.0

# Manner distances.  Manner is categorical, not ordinal, so it gets an explicit
# symmetric table instead of a scalar.  Values are in [0, 1].
_MANNER_PAIRS = {
    ("stop", "affricate"): 0.25,        # affricate = stop + fricated release
    ("stop", "fricative"): 0.50,
    ("stop", "nasal"): 0.45,            # same oral closure, velum differs
    ("stop", "tap"): 0.20,              # a tap is a very short stop
    ("stop", "approximant"): 0.80,
    ("stop", "lateral"): 0.85,
    ("stop", "glide"): 0.90,
    ("affricate", "fricative"): 0.25,
    ("affricate", "nasal"): 0.60,
    ("affricate", "tap"): 0.50,
    ("affricate", "approximant"): 0.80,
    ("affricate", "lateral"): 0.85,
    ("affricate", "glide"): 0.90,
    ("fricative", "nasal"): 0.55,
    ("fricative", "approximant"): 0.50,
    ("fricative", "lateral"): 0.55,
    ("fricative", "glide"): 0.50,
    ("fricative", "tap"): 0.55,
    ("nasal", "approximant"): 0.50,
    ("nasal", "lateral"): 0.50,
    ("nasal", "glide"): 0.60,
    ("nasal", "tap"): 0.50,
    ("approximant", "lateral"): 0.20,
    ("approximant", "glide"): 0.20,
    ("approximant", "tap"): 0.25,
    ("lateral", "glide"): 0.40,
    ("lateral", "tap"): 0.35,
    ("glide", "tap"): 0.60,
}
_MANNER_DISTANCE = {}
for (_m1, _m2), _mv in _MANNER_PAIRS.items():
    _MANNER_DISTANCE[(_m1, _m2)] = _mv
    _MANNER_DISTANCE[(_m2, _m1)] = _mv

# Consonant feature weights.  Sum to 1.0 so a consonant/consonant distance can
# never exceed 1.0.
_W_MANNER = 0.38
_W_PLACE = 0.30
_W_VOICE = 0.10
_W_STRIDENT = 0.11   # separates /s/ from /θ/, /f/ from /θ/
_W_ANTERIOR = 0.11   # separates /s/ from /ʃ/, /t/ from /k/

# Vowel feature weights, likewise summing to 1.0.
_W_HEIGHT = 0.40
_W_BACK = 0.30
_W_ROUND = 0.12
_W_RHOTIC = 0.18

_HEIGHT_SPAN = 4.0   # close (0) .. open (4)
_BACK_SPAN = 2.0     # front (0) .. back (2)

# Extra cost for comparing a diphthong against a monophthong. Without it,
# "bite" vs "bat" scores implausibly low because the nuclei are adjacent.
_DIPHTHONG_MISMATCH = 0.15

# Distance between two segments of different classes (consonant vs vowel), and
# the fallback for any symbol not in the table.
_CROSS_CLASS_DISTANCE = 1.0
_UNKNOWN_DISTANCE = 1.0

# Featural distances between two same-class segments naturally top out around
# 0.6, because any two English consonants share most of their features. Left
# unscaled, a child who read a completely different word would score ~0.3 where
# the unweighted metric scores ~1.0, and every downstream threshold calibrated
# on the unweighted scale would become unreachable. This linear stretch keeps
# the two metrics on a comparable range. It is monotonic, so it changes no
# ordering, and it is applied only to pairs that are NOT in ALLOWED_VARIATIONS
# — forgiven variation stays free.
_CONTRAST_SCALE = 1.6


def _c(place, manner, voiced, strident=False):
    """Consonant feature bundle. `anterior` is derived from place."""
    return {
        "type": "C",
        "place": _PLACE[place],
        "manner": manner,
        "voiced": voiced,
        "strident": strident,
        "anterior": _PLACE[place] <= _PLACE["alveolar"],
    }


def _v(height, back, rounded=False, rhotic=False, offglide=None):
    """Vowel feature bundle. `offglide` names the second target of a diphthong."""
    return {
        "type": "V",
        "height": height,
        "back": back,
        "rounded": rounded,
        "rhotic": rhotic,
        "offglide": offglide,
    }


# ---------------------------------------------------------------------------
# The feature table
# ---------------------------------------------------------------------------
# Covers the symbols actually seen in this pipeline: the wav2vec2-TIMIT-IPA
# model output, the `eng_to_ipa` ground truth (which uses the ligatures ʧ/ʤ),
# and common notational variants of both.

PHONEME_FEATURES = {
    # --- stops ---------------------------------------------------------
    "p": _c("bilabial", "stop", False),
    "b": _c("bilabial", "stop", True),
    "t": _c("alveolar", "stop", False),
    "d": _c("alveolar", "stop", True),
    "k": _c("velar", "stop", False),
    "g": _c("velar", "stop", True),
    "ɡ": _c("velar", "stop", True),   # ɡ U+0261, the IPA script g
    "ʔ": _c("glottal", "stop", False),  # ʔ
    # --- taps ----------------------------------------------------------
    "ɾ": _c("alveolar", "tap", True),   # ɾ
    # --- affricates ----------------------------------------------------
    "ʧ": _c("postalveolar", "affricate", False, strident=True),   # ʧ ligature
    "ʤ": _c("postalveolar", "affricate", True, strident=True),    # ʤ ligature
    "tʃ": _c("postalveolar", "affricate", False, strident=True),  # tʃ two-char
    "dʒ": _c("postalveolar", "affricate", True, strident=True),   # dʒ two-char
    # --- fricatives ----------------------------------------------------
    "f": _c("labiodental", "fricative", False, strident=True),
    "v": _c("labiodental", "fricative", True, strident=True),
    "θ": _c("dental", "fricative", False),          # θ
    "ð": _c("dental", "fricative", True),           # ð
    "s": _c("alveolar", "fricative", False, strident=True),
    "z": _c("alveolar", "fricative", True, strident=True),
    "ʃ": _c("postalveolar", "fricative", False, strident=True),   # ʃ
    "ʒ": _c("postalveolar", "fricative", True, strident=True),    # ʒ
    "h": _c("glottal", "fricative", False),
    "x": _c("velar", "fricative", False),
    # --- nasals --------------------------------------------------------
    "m": _c("bilabial", "nasal", True),
    "n": _c("alveolar", "nasal", True),
    "ŋ": _c("velar", "nasal", True),                # ŋ
    # --- liquids and glides --------------------------------------------
    "l": _c("alveolar", "lateral", True),
    "ɫ": _c("velar", "lateral", True),              # ɫ dark l
    "r": _c("postalveolar", "approximant", True),
    "ɹ": _c("postalveolar", "approximant", True),   # ɹ
    "ɻ": _c("retroflex", "approximant", True),      # ɻ
    "j": _c("palatal", "glide", True),
    "w": _c("labiovelar", "glide", True),
    "ʍ": _c("labiovelar", "glide", False),          # ʍ
    # --- monophthongs ---------------------------------------------------
    "i": _v(0.0, 0.0),
    "ɪ": _v(0.6, 0.3),                              # ɪ
    "e": _v(1.0, 0.0),
    "ɛ": _v(2.0, 0.0),                              # ɛ
    "æ": _v(3.0, 0.2),                              # æ
    "a": _v(3.7, 0.3),
    "ɑ": _v(4.0, 2.0),                              # ɑ
    "ɒ": _v(4.0, 2.0, rounded=True),                # ɒ
    "ʌ": _v(2.0, 1.2),                              # ʌ
    "ə": _v(1.8, 1.0),                              # ə
    "ɜ": _v(2.0, 1.0),                              # ɜ
    "ɐ": _v(3.0, 1.0),                              # ɐ
    "ɨ": _v(0.3, 1.0),                              # ɨ
    "ᵻ": _v(0.3, 1.0),                              # ᵻ (reduced high vowel)
    "ɔ": _v(2.0, 1.9, rounded=True),                # ɔ
    "o": _v(1.0, 2.0, rounded=True),
    "ʊ": _v(0.6, 1.7, rounded=True),                # ʊ
    "u": _v(0.0, 2.0, rounded=True),
    # --- r-coloured vowels ----------------------------------------------
    "ɚ": _v(1.8, 1.0, rhotic=True),                 # ɚ
    "ɝ": _v(2.0, 1.0, rhotic=True),                 # ɝ
    # --- diphthongs, when the tokenizer keeps them whole ------------------
    "aɪ": _v(3.7, 0.3, offglide="ɪ"),          # aɪ
    "aʊ": _v(3.7, 0.3, offglide="ʊ"),          # aʊ
    "ɔɪ": _v(2.0, 1.9, rounded=True, offglide="ɪ"),  # ɔɪ
    "eɪ": _v(1.0, 0.0, offglide="ɪ"),          # eɪ
    "oʊ": _v(1.0, 2.0, rounded=True, offglide="ʊ"),       # oʊ
}


# ---------------------------------------------------------------------------
# ALLOWED VARIATION — the audit surface
# ---------------------------------------------------------------------------
# Each entry: frozenset({a, b}) -> (cost, justification)
#
# Cost is 0.0 for "these are the same thing" (notation, or free allophonic
# variation in General American) and a small non-zero value for "this is
# normal connected speech but not literally identical".
#
# RULE FOR ADDING TO THIS TABLE: the variation must be something a competent
# adult native speaker of American English does when reading the word aloud
# correctly.  If a speech-language pathologist would flag it as an articulation
# error, or a teacher would flag it as a decoding error, it does NOT belong
# here — give it a featural cost instead.

_AV = {}


def _allow(a, b, cost, why):
    _AV[frozenset((a, b))] = (cost, why)


# -- notation-only equivalences (same sound, different transcription) --------
_allow("g", "ɡ", 0.0,
       "ASCII 'g' vs IPA script 'ɡ' (U+0261). Identical sound; the ground-truth "
       "generator and the acoustic model happen to use different codepoints.")
_allow("ʧ", "tʃ", 0.0,
       "ʧ ligature vs two-character tʃ. eng_to_ipa emits the ligature, the "
       "wav2vec2-TIMIT-IPA model emits the sequence. Same affricate.")
_allow("ʤ", "dʒ", 0.0,
       "ʤ ligature vs two-character dʒ. Same affricate, different transcription "
       "convention between ground truth and model.")
_allow("r", "ɹ", 0.0,
       "'r' vs 'ɹ'. English /r/ is an approximant; both symbols are used for it "
       "interchangeably across transcription sources.")
_allow("r", "ɻ", 0.0,
       "'r' vs retroflex 'ɻ'. Bunched vs retroflex /r/ are the two normal "
       "articulations of American English /r/ and sound the same.")
_allow("ɹ", "ɻ", 0.0,
       "'ɹ' vs 'ɻ' — see above, both are General American /r/.")
_allow("l", "ɫ", 0.0,
       "Clear 'l' vs dark 'ɫ'. Purely positional allophony (light before "
       "vowels, dark in codas); no English word contrast depends on it.")

# -- vowel reduction in unstressed syllables --------------------------------
_allow("ə", "ʌ", 0.0,
       "ə vs ʌ. In General American these are the same vowel; the two symbols "
       "mark unstressed vs stressed, and stress is not something we score.")
_allow("ə", "ɪ", 0.0,
       "ə vs ɪ in unstressed position. Both are standard reductions of the same "
       "vowel ('roses' as [ɹoʊzɪz] or [ɹoʊzəz]); dialect, not error.")
_allow("ə", "ᵻ", 0.0,
       "ə vs ᵻ. ᵻ is literally the symbol for a reduced vowel between ə and ɪ; "
       "which one the model emits is arbitrary.")
_allow("ə", "ɨ", 0.0,
       "ə vs ɨ. Same reduced-vowel territory as ᵻ; some transcriptions use ɨ.")
_allow("ɪ", "ᵻ", 0.0,
       "ɪ vs ᵻ. Explicitly the same reduced high vowel; the acoustic model "
       "alternates between them mid-utterance on identical audio.")
_allow("ɪ", "ɨ", 0.0,
       "ɪ vs ɨ. Same reduced high vowel as ɪ/ᵻ, written with the other barred "
       "symbol; no English contrast depends on the difference.")
_allow("ə", "ɐ", 0.0,
       "ə vs ɐ. ɐ is the slightly more open central realisation of schwa that "
       "the model tends to output in open syllables.")
_allow("ʌ", "ɐ", 0.0,
       "ʌ vs ɐ. Same central vowel, different transcriber convention.")

# -- t-flapping and glottalisation ------------------------------------------
_allow("t", "ɾ", 0.0,
       "t -> ɾ (flapping). 'water', 'better', 'little' are flapped by virtually "
       "every American speaker. Scoring this as a mispronunciation punishes a "
       "child for sounding native.")
_allow("d", "ɾ", 0.0,
       "d -> ɾ (flapping). Same rule as /t/; intervocalic /d/ flaps too "
       "('ladder').")
_allow("t", "ʔ", 0.05,
       "t -> ʔ (glottalisation). Standard for coda /t/ ('button', 'kitten', "
       "'that one'). Tiny non-zero cost because a fully glottalised onset /t/ "
       "would be unusual, and we do not know the position here.")

# -- r-colouring -------------------------------------------------------------
_allow("ɚ", "ɝ", 0.0,
       "ɚ vs ɝ. Same r-coloured central vowel; the two symbols only encode "
       "unstressed vs stressed, which we do not score.")
_allow("ɚ", "ə", 0.05,
       "ɚ vs ə. The r-colouring on a final unstressed syllable is often barely "
       "measurable ('butter'), and the model drops it inconsistently.")
_allow("ɝ", "ʌ", 0.05,
       "ɝ vs ʌ — the same near-miss as ɚ/ə, in the stressed variant.")
_allow("ɚ", "ɹ", 0.10,
       "ɚ vs ɹ. Syllabic-r versus consonantal-r is a transcription choice; the "
       "audio is the same gesture. Small cost because a bare ɹ where a full "
       "vowel was expected can also indicate a swallowed syllable.")
_allow("ɝ", "ɹ", 0.10,
       "ɝ vs ɹ. Stressed syllabic-r versus consonantal-r, the same gesture "
       "written two ways; small cost for the same reason as ɚ/ɹ above.")

ALLOWED_VARIATIONS = _AV


def allowed_variation_report():
    """Return the audit table as a list of (a, b, cost, justification) rows.

    Intended for a reviewer, a test, or an admin endpoint — anything that needs
    to show a human exactly which mismatches this system forgives and why.
    """
    rows = []
    for pair, (cost, why) in ALLOWED_VARIATIONS.items():
        a, b = sorted(pair)
        rows.append((a, b, cost, why))
    rows.sort()
    return rows


# ---------------------------------------------------------------------------
# Deletion / insertion leniency
# ---------------------------------------------------------------------------

# Final stops in English are very often unreleased ([kʰæt̚]). An unreleased stop
# can be close to inaudible, and a frame-level acoustic model routinely fails to
# emit it even when the child articulated the word correctly. Charging a full
# deletion for that is the single most common way a correct reading loses points.
_FINAL_STOPS = frozenset({"p", "b", "t", "d", "k", "g", "ɡ"})
_UNRELEASED_FINAL_STOP_COST = 0.15

# Cheap-to-insert symbols: things the acoustic model hallucinates rather than
# things the child said.
_CHEAP_INSERTIONS = {
    "ʔ": 0.10,   # ʔ — glottal stops appear at word boundaries constantly
    "h": 0.50,        # breath / aspiration misread as a segment
    "ə": 0.50,   # epenthetic schwa between consonants in a cluster
}


def deletion_cost(phoneme: str, is_final: bool = False) -> float:
    """Cost of the ground-truth `phoneme` being missing from the prediction."""
    if is_final and phoneme in _FINAL_STOPS:
        return _UNRELEASED_FINAL_STOP_COST
    return 1.0


def insertion_cost(phoneme: str) -> float:
    """Cost of an extra predicted `phoneme` that the ground truth did not have."""
    return _CHEAP_INSERTIONS.get(phoneme, 1.0)


# ---------------------------------------------------------------------------
# Distance
# ---------------------------------------------------------------------------

_PAIR_CACHE = {}


def _consonant_distance(fa, fb):
    manner = 0.0
    if fa["manner"] != fb["manner"]:
        manner = _MANNER_DISTANCE.get((fa["manner"], fb["manner"]), 1.0)
    place = abs(fa["place"] - fb["place"]) / _PLACE_SPAN
    voice = 0.0 if fa["voiced"] == fb["voiced"] else 1.0
    strident = 0.0 if fa["strident"] == fb["strident"] else 1.0
    anterior = 0.0 if fa["anterior"] == fb["anterior"] else 1.0
    return (
        _W_MANNER * manner
        + _W_PLACE * place
        + _W_VOICE * voice
        + _W_STRIDENT * strident
        + _W_ANTERIOR * anterior
    )


def _vowel_target_distance(fa, fb):
    height = abs(fa["height"] - fb["height"]) / _HEIGHT_SPAN
    back = abs(fa["back"] - fb["back"]) / _BACK_SPAN
    rounded = 0.0 if fa["rounded"] == fb["rounded"] else 1.0
    rhotic = 0.0 if fa["rhotic"] == fb["rhotic"] else 1.0
    return (
        _W_HEIGHT * height
        + _W_BACK * back
        + _W_ROUND * rounded
        + _W_RHOTIC * rhotic
    )


def _vowel_distance(fa, fb):
    """Diphthongs are scored as 70% nucleus + 30% offglide, plus a penalty when
    only one of the pair is a diphthong at all."""
    nucleus = _vowel_target_distance(fa, fb)
    off_a, off_b = fa["offglide"], fb["offglide"]
    if off_a is None and off_b is None:
        return nucleus

    ga = PHONEME_FEATURES.get(off_a) if off_a else fa
    gb = PHONEME_FEATURES.get(off_b) if off_b else fb
    glide = _vowel_target_distance(ga, gb) if (ga and gb) else 1.0
    dist = 0.70 * nucleus + 0.30 * glide
    if (off_a is None) != (off_b is None):
        dist += _DIPHTHONG_MISMATCH
    return dist


def _compute(a, b):
    if a == b:
        return 0.0

    allowed = ALLOWED_VARIATIONS.get(frozenset((a, b)))
    if allowed is not None:
        return allowed[0]

    fa = PHONEME_FEATURES.get(a)
    fb = PHONEME_FEATURES.get(b)
    if fa is None or fb is None:
        # Unknown symbol (e.g. a raw spelling letter leaking in from an
        # out-of-vocabulary ground-truth word). Be conservative: full cost,
        # same as today's unweighted behaviour.
        return _UNKNOWN_DISTANCE

    if fa["type"] != fb["type"]:
        return _CROSS_CLASS_DISTANCE

    if fa["type"] == "C":
        dist = _consonant_distance(fa, fb)
    else:
        dist = _vowel_distance(fa, fb)

    dist *= _CONTRAST_SCALE

    if dist < 0.0:
        return 0.0
    if dist > 1.0:
        return 1.0
    return dist


def phonetic_distance(a: str, b: str) -> float:
    """Featural substitution cost between two IPA symbols, in [0.0, 1.0].

    0.0  = identical, or an explicitly allowed variation (see ALLOWED_VARIATIONS)
    ~0.1 = a near miss (voicing only, adjacent vowel height)
    ~0.4 = a clearly different segment of the same class (k vs b)
    1.0  = a different segment class entirely (consonant vs vowel), or unknown

    Memoised; after warm-up a call is one dict lookup.
    """
    key = (a, b)
    cached = _PAIR_CACHE.get(key)
    if cached is None:
        cached = _compute(a, b)
        _PAIR_CACHE[key] = cached
        _PAIR_CACHE[(b, a)] = cached
    return cached


# ---------------------------------------------------------------------------
# Sequence normalisation
# ---------------------------------------------------------------------------
# A per-symbol distance cannot express "ər is the same as ɚ", because that is a
# two-symbol vs one-symbol equivalence. This collapses the sequence form to the
# single-symbol form on BOTH sides before comparison, so it never creates or
# hides an error on its own — it only makes the two sides comparable.

_RHOTIC_CONSONANTS = frozenset({"r", "ɹ", "ɻ"})
_REDUCIBLE_BEFORE_R = {
    "ə": "ɚ",   # ə + r -> ɚ
    "ʌ": "ɚ",   # ʌ + r -> ɚ
    "ɜ": "ɝ",   # ɜ + r -> ɝ
}


def normalize_phoneme_sequence(seq):
    """Collapse `ə`+`r` style sequences into their single-symbol r-coloured form.

    'ər', 'ʌɹ' and 'ɜɹ' are the same thing as 'ɚ'/'ɝ'; which form appears is a
    transcription convention, not a difference in what was said. Applied to both
    the ground truth and the prediction, so the comparison stays symmetric.
    """
    if not seq:
        return list(seq)
    out = []
    i = 0
    n = len(seq)
    while i < n:
        cur = seq[i]
        if i + 1 < n and cur in _REDUCIBLE_BEFORE_R and seq[i + 1] in _RHOTIC_CONSONANTS:
            out.append(_REDUCIBLE_BEFORE_R[cur])
            i += 2
            continue
        out.append(cur)
        i += 1
    return out
