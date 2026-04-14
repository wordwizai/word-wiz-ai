"""
Phoneme Feedback Formatter

Generates natural-language feedback text and SSML from phoneme analysis data.
Pure function — no network calls, no GPT.

TTS provider: Google Cloud TTS, which supports <phoneme alphabet="ipa" ph="...">
tags. The tag wraps a demo syllable so TTS produces the target sound in isolation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class FeedbackResult:
    text: str   # Plain-text feedback for display
    ssml: str   # SSML-enhanced feedback for Google Cloud TTS


# ── Display names ──────────────────────────────────────────────────────────────

# Maps IPA phoneme → human-readable letter combination for plain text
_IPA_TO_DISPLAY: dict[str, str] = {
    "θ":  "th",
    "ð":  "th",
    "ʃ":  "sh",
    "tʃ": "ch",
    "ʧ":  "ch",
    "dʒ": "j",
    "ʤ":  "j",
    "ŋ":  "ng",
    "ʒ":  "zh",
    "j":  "y",
    "ɹ":  "r",
    "r":  "r",
    "æ":  "short a",
    "a":  "short a",   # bare 'a' from wav2vec2-TIMIT — same sound as /æ/
    "ɑ":  "ah",
    "ɑː": "ah",
    "ə":  "uh",
    "ɚ":  "er",
    "ɛ":  "eh",
    "e":  "eh",        # TIMIT bare 'e'
    "ɪ":  "short i",
    "i":  "short i",   # TIMIT bare 'i'
    "iː": "long ee",
    "ɔ":  "aw",
    "ɔː": "aw",
    "ʊ":  "short oo",
    "u":  "long oo",   # TIMIT bare 'u'
    "uː": "long oo",
    "ʌ":  "short u",
    "o":  "long o",    # TIMIT bare 'o'
    "aɪ": "long i",
    "aʊ": "ow",
    "eɪ": "long a",
    "ɔɪ": "oy",
    "oʊ": "long o",
    "p": "p", "b": "b", "t": "t", "d": "d",
    "k": "k", "ɡ": "g", "g": "g", "f": "f", "v": "v",
    "s": "s", "z": "z", "h": "h", "m": "m",
    "n": "n", "l": "l", "w": "w",
}


# ── Google Cloud TTS phoneme tags ──────────────────────────────────────────────

# Maps IPA phoneme → (ph attribute, demo syllable) for <phoneme> tags.
#
# Google Cloud TTS supported IPA:
#   Consonants: p b t d k ɡ m n ŋ f v s z θ ð ʃ ʒ h l ɹ ʧ ʤ j w
#   Vowels:     æ ɑː ə ɚ ɛ ɪ iː ɔː ʊ uː ʌ aɪ aʊ eɪ ɔɪ oʊ
#
# IMPORTANT: Bare consonant IPA (e.g. ph="θ") is nearly inaudible — TTS cannot
# produce a consonant without vowel context.  Every consonant entry below is
# backed with a schwa (ə) so Google TTS renders a clear, audible demo syllable.
# Vowels and diphthongs are pure sounds and need no backing.
# Special case: /ŋ/ cannot open a syllable in English, so use final position "ɪŋ".
_IPA_DEMO: dict[str, tuple[str, str]] = {
    # Stops — must have vowel context or they are completely silent
    "p":  ("pə",   "puh"),
    "b":  ("bə",   "buh"),
    "t":  ("tə",   "tuh"),
    "d":  ("də",   "duh"),
    "k":  ("kə",   "kuh"),
    "ɡ":  ("ɡə",   "guh"),
    "g":  ("ɡə",   "guh"),
    # Nasals
    "m":  ("mə",   "muh"),
    "n":  ("nə",   "nuh"),
    "ŋ":  ("ɪŋ",   "ing"),   # /ŋ/ never opens a syllable in English
    # Fricatives — schwa backing makes the burst clearly audible
    "f":  ("fə",   "fuh"),
    "v":  ("və",   "vuh"),
    "s":  ("sə",   "suh"),
    "z":  ("zə",   "zuh"),
    "θ":  ("θə",   "thuh"),
    "ð":  ("ðə",   "thuh"),
    "ʃ":  ("ʃə",   "shuh"),
    "ʒ":  ("ʒə",   "zhuh"),
    "h":  ("hə",   "huh"),
    # Liquids / glides
    "l":  ("lə",   "luh"),
    "ɹ":  ("ɹə",   "ruh"),
    "r":  ("ɹə",   "ruh"),
    "j":  ("jə",   "yuh"),
    "w":  ("wə",   "wuh"),
    # Affricates
    "ʧ":  ("ʧə",   "chuh"),
    "tʃ": ("ʧə",   "chuh"),
    "ʤ":  ("ʤə",   "juh"),
    "dʒ": ("ʤə",   "juh"),
    # Vowels and diphthongs — pure sounds, no backing needed
    # Also include bare TIMIT vowel symbols the model may output
    "æ":  ("æ",    "ah"),
    "a":  ("æ",    "ah"),   # TIMIT bare 'a' → same sound
    "ɑ":  ("ɑː",   "ah"),
    "ɑː": ("ɑː",   "ah"),
    "e":  ("ɛ",    "eh"),   # TIMIT bare 'e'
    "i":  ("ɪ",    "ih"),   # TIMIT bare 'i'
    "o":  ("oʊ",   "oh"),   # TIMIT bare 'o'
    "u":  ("uː",   "oo"),   # TIMIT bare 'u'
    "ə":  ("ə",    "uh"),
    "ɚ":  ("ɚ",    "er"),
    "ɛ":  ("ɛ",    "eh"),
    "ɪ":  ("ɪ",    "ih"),
    "iː": ("iː",   "ee"),
    "ɔː": ("ɔː",   "aw"),
    "ʊ":  ("ʊ",    "oo"),
    "uː": ("uː",   "oo"),
    "ʌ":  ("ʌ",    "uh"),
    "aɪ": ("aɪ",   "eye"),
    "aʊ": ("aʊ",   "ow"),
    "eɪ": ("eɪ",   "ay"),
    "ɔɪ": ("ɔɪ",   "oy"),
    "oʊ": ("oʊ",   "oh"),
}


# ── Grapheme tips ──────────────────────────────────────────────────────────────

# Tips keyed by grapheme cluster (what the student SAW in the word).
# These are preferred over phoneme tips when we can identify the grapheme.
GRAPHEME_TIPS: dict[str, str] = {
    "th":  "When you see 'th', put your tongue lightly between your teeth and blow air out gently — like in 'think' or 'three'.",
    "oo":  "When you see two O's together, they usually make an 'oo' sound — like in 'food' or 'moon'.",
    "ch":  "When you see 'ch', press your tongue to the roof of your mouth and release with a puff of air — like in 'chair' or 'chin'.",
    "sh":  "When you see 'sh', round your lips slightly and push air through — like telling someone to be quiet, as in 'ship' or 'fish'.",
    "ph":  "When you see 'ph', it makes an 'f' sound — like in 'phone' or 'photo'.",
    "ck":  "When you see 'ck' at the end of a word, it makes a 'k' sound — like in 'back' or 'duck'.",
    "ng":  "When you see 'ng', it makes a nasal sound from the back of your throat — like in 'sing' or 'ring'.",
    "wh":  "When you see 'wh', it usually makes a 'w' sound — like in 'where' or 'when'.",
    "ea":  "When you see 'ea', it often makes a long 'ee' sound — like in 'read' or 'beach'.",
    "ai":  "When you see 'ai', it usually makes a long 'a' sound — like in 'rain' or 'sail'.",
    "ay":  "When you see 'ay', it makes a long 'a' sound — like in 'day' or 'play'.",
    "igh": "When you see 'igh', it makes a long 'i' sound — like in 'night' or 'light'.",
    "ow":  "When you see 'ow', it can make an 'oh' sound like in 'snow', or an 'ow' sound like in 'cow'.",
    "ou":  "When you see 'ou', it often makes an 'ow' sound — like in 'out' or 'house'.",
    "oi":  "When you see 'oi', it makes an 'oy' sound — like in 'coin' or 'join'.",
    "oy":  "When you see 'oy', it makes an 'oy' sound — like in 'boy' or 'toy'.",
    "ew":  "When you see 'ew', it usually makes a long 'oo' sound — like in 'new' or 'flew'.",
    "ue":  "When you see 'ue', it often makes a long 'oo' or 'yoo' sound — like in 'blue' or 'cue'.",
    "ie":  "When you see 'ie', it often makes a long 'ee' sound — like in 'piece' or 'field'.",
    "gh":  "When you see 'gh' after a vowel, it's usually silent — like in 'night' or 'through'. Sometimes it makes an 'f' sound, like in 'enough'.",
    "kn":  "When you see 'kn' at the start of a word, the 'k' is silent — like in 'knee' or 'know'.",
    "wr":  "When you see 'wr' at the start of a word, the 'w' is silent — like in 'write' or 'wrong'.",
    "dge": "When you see 'dge', it makes a 'j' sound — like in 'bridge' or 'judge'.",
    "tch": "When you see 'tch', it makes a 'ch' sound — like in 'catch' or 'witch'.",
    "ge":  "When you see 'ge' at the end of a word, it often makes a 'j' sound — like in 'age' or 'large'.",
    "ce":  "When you see 'ce', it usually makes an 's' sound — like in 'face' or 'mice'.",
    "ci":  "When you see 'ci', it often makes a 'sh' sound — like in 'special' or 'ancient'.",
}

PHONEME_TO_GRAPHEME: dict[str, str] = {
    "θ": "th", "ð": "th", "ʃ": "sh", "ʧ": "ch", "ŋ": "ng",
    "uː": "oo", "eɪ": "ay", "aɪ": "igh", "ɔɪ": "oi",
}


# ── Phoneme tips (fallback when grapheme can't be identified) ──────────────────

PRONUNCIATION_TIPS: dict[str, str] = {
    "θ":  "For the 'th' sound, put your tongue lightly between your teeth and blow air out gently.",
    "ð":  "For the voiced 'th' sound, put your tongue between your teeth and use your voice — like in 'the' or 'this'.",
    "ʃ":  "For the 'sh' sound, round your lips slightly and push air through — like telling someone to be quiet.",
    "ŋ":  "The 'ng' sound comes from the back of your throat with your mouth open — like the end of 'sing'.",
    "ɹ":  "For the 'r' sound, curl your tongue back slightly without touching the roof of your mouth.",
    "r":  "For the 'r' sound, curl your tongue back slightly without touching the roof of your mouth.",
    "æ":  "This vowel sounds like 'ah' but with your mouth more spread sideways — like in 'cat' or 'hat'.",
    "ɛ":  "This is a short 'eh' sound — like in 'bed' or 'said'.",
    "ɪ":  "This is a short 'ih' sound — like in 'bit' or 'him', not the long 'ee'.",
    "iː": "This is the long 'ee' sound — like in 'feet' or 'sleep'.",
    "uː": "This is the long 'oo' sound — like in 'food' or 'moon'.",
    "ʊ":  "This is a short 'oo' sound — like in 'book' or 'put', not the long 'oo'.",
    "ʌ":  "This is a short 'uh' sound — like in 'cup' or 'fun'.",
    "aɪ": "This sound starts with 'ah' and glides to 'ee' — like in 'bite' or 'fly'.",
    "eɪ": "This sound starts with 'eh' and glides to 'ee' — like in 'date' or 'say'.",
    "oʊ": "This sound starts with 'oh' and glides closed — like in 'go' or 'home'.",
    "ʧ":  "The 'ch' sound — press your tongue to the roof of your mouth and release with a puff of air.",
    "tʃ": "The 'ch' sound — press your tongue to the roof of your mouth and release with a puff of air.",
    "ʤ":  "The 'j' sound — same as 'ch' but use your voice.",
    "dʒ": "The 'j' sound — same as 'ch' but use your voice.",
    "ʒ":  "This sound is like 'sh' but voiced — like the middle of 'measure' or 'vision'.",
    "v":  "The 'v' sound — bite your lower lip lightly and use your voice, like 'f' but voiced.",
    "z":  "The 'z' sound — same as 's' but use your voice.",
    "f":  "The 'f' sound — bite your lower lip lightly and blow air out.",
}


# ── Grapheme detection ─────────────────────────────────────────────────────────

# Maps IPA phoneme → candidate grapheme clusters to search for in the word,
# ordered from longest/most specific to shortest (avoids "sh" matching before "tch").
_PHONEME_TO_GRAPHEMES: dict[str, list[str]] = {
    "θ":  ["tch", "th"],          # voiceless th: think, three, month
    "ð":  ["th"],                  # voiced th: the, this, breathe
    "ʃ":  ["tch", "sh", "ci", "ti"],
    "ʧ":  ["tch", "ch"],
    "tʃ": ["tch", "ch"],
    "ʤ":  ["dge", "ge", "j"],
    "dʒ": ["dge", "ge", "j"],
    "ŋ":  ["ng"],
    "ʒ":  ["ge", "ci"],
    "f":  ["ph", "gh", "f"],       # phone, rough, fun
    "k":  ["ck", "k", "c"],
    "j":  ["y"],                   # yes, year
    "w":  ["wh", "w"],             # where, water
    "ɹ":  ["wr", "r"],             # write, run
    "r":  ["wr", "r"],
    "n":  ["kn", "n"],             # knee, no
    "uː": ["oo", "ew", "ue"],      # food, flew, blue
    "u":  ["oo", "ew", "ue"],      # TIMIT bare 'u'
    "ʊ":  ["oo", "u"],             # book, put
    "iː": ["ee", "ea", "ie"],      # feet, beach, field
    "i":  ["ee", "ea", "ie", "y"], # TIMIT bare 'i'
    "eɪ": ["ai", "ay", "ea"],      # rain, day, break
    "e":  ["ea", "ai", "ay"],      # TIMIT bare 'e'
    "aɪ": ["igh", "ie", "y"],      # night, pie, fly
    "a":  ["ai", "ay", "a"],       # TIMIT bare 'a' — short-a spelling
    "oʊ": ["ow", "oa"],            # snow, boat
    "o":  ["ow", "oa", "o"],       # TIMIT bare 'o'
    "aʊ": ["ou", "ow"],            # out, cow
    "ɔɪ": ["oi", "oy"],            # coin, boy
}


def _find_grapheme_in_word(phoneme: str, word: str) -> Optional[str]:
    """
    Scan word (case-insensitive) for the most specific grapheme cluster
    that commonly produces the given phoneme.

    Returns the matched grapheme string, or None if no candidate is found.
    """
    candidates = _PHONEME_TO_GRAPHEMES.get(phoneme)
    if not candidates:
        return None
    word_lower = word.lower()
    for grapheme in candidates:
        if grapheme in word_lower:
            return grapheme
    return None


def _tip_for_phoneme(phoneme: str, error_words: list[str]) -> str:
    """
    Return the best available tip for a phoneme, preferring grapheme-centric tips.

    Strategy:
    1. Check each error word for a known grapheme cluster → use GRAPHEME_TIPS.
    2. If no grapheme found in any word, fall back to PRONUNCIATION_TIPS.
    """
    for word in error_words:
        grapheme = _find_grapheme_in_word(phoneme, word)
        if grapheme and grapheme in GRAPHEME_TIPS:
            return GRAPHEME_TIPS[grapheme]

    # Fallback: phoneme-based tip
    return PRONUNCIATION_TIPS.get(phoneme, "")


# ── Formatting helpers ─────────────────────────────────────────────────────────

def _display_name(phoneme: str) -> str:
    return _IPA_TO_DISPLAY.get(phoneme, phoneme)


def _phoneme_tag(phoneme: str) -> str:
    """Return a Google Cloud TTS <phoneme> tag that plays the target sound."""
    if phoneme in _IPA_DEMO:
        ph_attr, demo_text = _IPA_DEMO[phoneme]
        return f'<phoneme alphabet="ipa" ph="{ph_attr}">{demo_text}</phoneme>'
    return f"'{_display_name(phoneme)}'"


def _oxford_list(words: list[str]) -> str:
    if len(words) == 1:
        return words[0]
    if len(words) == 2:
        return f"{words[0]} and {words[1]}"
    return ", ".join(words[:-1]) + f", and {words[-1]}"


def _words_for_phoneme(
    phoneme: str,
    phoneme_to_error_words: dict,
    max_words: int = 4,
) -> list[str]:
    seen: set[str] = set()
    words: list[str] = []
    for entry in phoneme_to_error_words.get(phoneme, []):
        w = (entry.get("word") or "").strip()
        if w and w not in seen:
            seen.add(w)
            words.append(w)
            if len(words) == max_words:
                break
    return words


def _focus_from_high_per_words(
    pronunciation_data: list[dict],
    phoneme_to_error_words: dict[str, list[dict]],
) -> Optional[str]:
    """
    Pick the best focus phoneme by walking words from worst PER to least-bad.

    Iterates high-PER words (PER ≥ 0.4) from worst to best and returns the
    most-errored phoneme found in the first word that has phoneme errors.
    This ensures the single worst word always wins rather than a common phoneme
    that happens to appear in multiple mildly-wrong words (e.g. schwa in 'the').
    """
    HIGH_PER_THRESHOLD = 0.4

    # Sort clearly mispronounced words worst-first.
    # Use total_errors (absolute count) as the primary key so a short word like
    # "the" (2 phonemes → 100% PER from 1 mistake) doesn't beat a longer word
    # with more actual errors (e.g. "dog"→"doge" = 2-3 errors).
    # PER is the tiebreaker for words with the same error count.
    high_per_words = sorted(
        [w for w in pronunciation_data if (w.get("per") or 0) >= HIGH_PER_THRESHOLD],
        key=lambda w: ((w.get("total_errors") or 0), (w.get("per") or 0)),
        reverse=True,
    )
    if not high_per_words:
        return None

    # Walk worst → less-bad; return as soon as we find a word with phoneme errors
    for word_entry in high_per_words:
        word_name = (word_entry.get("ground_truth_word") or "").strip().lower()
        if not word_name:
            continue

        candidates: dict[str, int] = {}
        for phoneme, entries in phoneme_to_error_words.items():
            count = sum(
                1 for e in entries
                if (e.get("word") or "").strip().lower() == word_name
            )
            if count:
                candidates[phoneme] = count

        if candidates:
            return max(candidates, key=lambda p: candidates[p])

    return None


def _ordered_phonemes(
    phoneme_to_error_words: dict[str, list[dict]],
    problem_summary: dict,
) -> list[str]:
    """Return phonemes with errors: recommended_focus first, others by error count."""
    recommended = problem_summary.get("recommended_focus_phoneme")
    focus: Optional[str] = None
    if recommended and isinstance(recommended, (list, tuple)) and len(recommended) >= 1:
        focus = str(recommended[0])
    if not focus:
        error_counts = problem_summary.get("phoneme_error_counts", {})
        if error_counts:
            focus = max(error_counts, key=lambda k: error_counts[k])
    if not focus and phoneme_to_error_words:
        focus = next(iter(phoneme_to_error_words))

    error_counts = problem_summary.get("phoneme_error_counts", {})
    others = sorted(
        [p for p in phoneme_to_error_words if p != focus],
        key=lambda p: (-error_counts.get(p, 0), -len(phoneme_to_error_words.get(p, []))),
    )
    result: list[str] = []
    if focus and focus in phoneme_to_error_words:
        result.append(focus)
    result.extend(others)
    return result


# ── Public API ─────────────────────────────────────────────────────────────────

def build_phoneme_to_error_words(pronunciation_data: list[dict]) -> dict[str, list[dict]]:
    """
    Build a mapping of phoneme → list of error word entries from pronunciation data.

    Each entry is {"word": str, "error_type": "missed"|"added"|"substituted"}.
    Only words with per > 0 are included.
    """
    phoneme_to_error_words: dict[str, list[dict]] = {}

    for word_data in pronunciation_data:
        if (word_data.get("per") or 0) <= 0:
            continue

        word = (word_data.get("ground_truth_word") or "").strip()

        for phoneme in (word_data.get("missed") or []):
            phoneme_to_error_words.setdefault(phoneme, []).append(
                {"word": word, "error_type": "missed"}
            )
        for phoneme in (word_data.get("added") or []):
            phoneme_to_error_words.setdefault(phoneme, []).append(
                {"word": word, "error_type": "added"}
            )
        for sub in (word_data.get("substituted") or []):
            expected = sub[0] if isinstance(sub, (list, tuple)) and len(sub) > 0 else sub
            phoneme_to_error_words.setdefault(expected, []).append(
                {"word": word, "error_type": "substituted"}
            )

    return phoneme_to_error_words


def generate_feedback(
    problem_summary: dict,
    per_summary: dict,
    pronunciation_data: list[dict],
) -> FeedbackResult:
    """
    Generate feedback text and SSML from phoneme analysis data.

    Pure function — no network calls. Returns instantly.

    Tips are grapheme-centric when possible: the formatter scans each error word
    for a known grapheme cluster that produces the target phoneme (e.g., "th" in
    "think" for /θ/), then uses a tip that references the letters the student saw.
    Falls back to a phoneme-level tip when no matching grapheme is found.

    Args:
        problem_summary: From analyze_results(). May contain phoneme_to_error_words;
                         if absent it is built from pronunciation_data.
        per_summary:     From analyze_results() — contains sentence_per.
        pronunciation_data: Raw pronunciation records
                            (pronunciation_dataframe.to_dict('records')).

    Returns:
        FeedbackResult with .text (plain) and .ssml (Google Cloud TTS SSML).
    """
    phoneme_to_error_words: dict = (
        problem_summary.get("phoneme_to_error_words")
        or build_phoneme_to_error_words(pronunciation_data)
    )

    sentence_per: float = (per_summary or {}).get("sentence_per", 0.0)

    if not phoneme_to_error_words and sentence_per <= 0.2:
        return FeedbackResult(text="Great job!", ssml="Great job!")

    # Priority: phonemes from clearly mispronounced words (PER ≥ 0.4) first.
    # This prevents a high-frequency consonant like 't' from dominating just
    # because it appears many times across the sentence with tiny errors.
    focus_phoneme = _focus_from_high_per_words(pronunciation_data, phoneme_to_error_words)

    if not focus_phoneme:
        # No word was clearly wrong (nothing cleared the 0.4 PER threshold).
        # If the overall sentence is also low-error, all mistakes are minor —
        # praise the child rather than nitpicking a barely-wrong word.
        if sentence_per <= 0.2:
            return FeedbackResult(text="Great job!", ssml="Great job!")

        ordered = _ordered_phonemes(phoneme_to_error_words, problem_summary)
        if not ordered:
            return FeedbackResult(text="Keep practicing!", ssml="Keep practicing!")
        focus_phoneme = ordered[0]
    words = _words_for_phoneme(focus_phoneme, phoneme_to_error_words, max_words=3)
    if not words:
        return FeedbackResult(text="Keep practicing!", ssml="Keep practicing!")

    focus_word = words[0]
    display = _display_name(focus_phoneme)
    tag = _phoneme_tag(focus_phoneme)

    # Find the grapheme cluster the child saw in the specific mispronounced word.
    grapheme = _find_grapheme_in_word(focus_phoneme, focus_word)
    if not grapheme:
        grapheme = PHONEME_TO_GRAPHEME.get(focus_phoneme)

    tip = (GRAPHEME_TIPS.get(grapheme) if grapheme else None) or PRONUNCIATION_TIPS.get(focus_phoneme)

    # Build full-word IPA from expected_phonemes in pronunciation_data so we can
    # wrap the focus word in a <phoneme> tag — this gives Google TTS the correct
    # pronunciation of the whole word, not just the isolated sound.
    word_ipa: Optional[str] = None
    for entry in pronunciation_data:
        w = (entry.get("ground_truth_word") or "").strip().lower()
        if w == focus_word.lower():
            phonemes = entry.get("expected_phonemes")
            if isinstance(phonemes, list) and phonemes:
                word_ipa = "".join(phonemes)
            break

    def _word_ssml(word: str, ipa: Optional[str]) -> str:
        if ipa:
            return f'<phoneme alphabet="ipa" ph="{ipa}">{word}</phoneme>'
        return word

    # Build a word-specific intro: lead with the word they saw, then name the
    # letters (grapheme) using <say-as spell-out> so TTS spells them out clearly,
    # then demo the isolated sound via the schwa-backed phoneme tag.
    if grapheme and grapheme in focus_word.lower():
        grapheme_ssml = f'<say-as interpret-as="spell-out">{grapheme}</say-as>'
        intro_text = (
            f"In the word '{focus_word}', the letters '{grapheme}' make the '{display}' sound."
        )
        intro_ssml = (
            f'In the word {_word_ssml(focus_word, word_ipa)}, '
            f'the letters {grapheme_ssml} make the '
            f'<break time="400ms"/>{tag}<break time="300ms"/> sound.'
        )
    else:
        intro_text = f"Watch the '{display}' sound in '{focus_word}'."
        intro_ssml = (
            f'Watch the <break time="400ms"/>{tag}<break time="300ms"/> '
            f'sound in {_word_ssml(focus_word, word_ipa)}.'
        )

    text = f"{intro_text} {tip}" if tip else intro_text
    ssml = f"{intro_ssml} {tip}" if tip else intro_ssml

    return FeedbackResult(text=text, ssml=ssml)
