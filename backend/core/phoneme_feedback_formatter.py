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
    "ɑː": "ah",
    "ə":  "uh",
    "ɚ":  "er",
    "ɛ":  "eh",
    "ɪ":  "short i",
    "iː": "long ee",
    "ɔː": "aw",
    "ʊ":  "short oo",
    "uː": "long oo",
    "ʌ":  "short u",
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
# Google Cloud TTS supported IPA:
#   Consonants: p b t d k ɡ m n ŋ f v s z θ ð ʃ ʒ h l ɹ ʧ ʤ j w
#   Vowels:     æ ɑː ə ɚ ɛ ɪ iː ɔː ʊ uː ʌ aɪ aʊ eɪ ɔɪ oʊ
_IPA_DEMO: dict[str, tuple[str, str]] = {
    "p":  ("p",   "p"),
    "b":  ("b",   "b"),
    "t":  ("t",   "t"),
    "d":  ("d",   "d"),
    "k":  ("k",   "k"),
    "ɡ":  ("ɡ",   "g"),
    "g":  ("ɡ",   "g"),
    "m":  ("m",   "m"),
    "n":  ("n",   "n"),
    "ŋ":  ("ŋ",   "ng"),
    "f":  ("f",   "fff"),
    "v":  ("v",   "v"),
    "s":  ("s",   "sss"),
    "z":  ("z",   "z"),
    "θ":  ("θ",   "th"),
    "ð":  ("ð",   "th"),
    "ʃ":  ("ʃ",   "sh"),
    "ʒ":  ("ʒ",   "zh"),
    "h":  ("h",   "h"),
    "l":  ("l",   "l"),
    "ɹ":  ("ɹ",   "r"),
    "r":  ("ɹ",   "r"),
    "j":  ("j",   "y"),
    "w":  ("w",   "w"),
    "ʧ":  ("ʧ",   "ch"),
    "tʃ": ("ʧ",   "ch"),
    "ʤ":  ("ʤ",   "j"),
    "dʒ": ("ʤ",   "j"),
    "æ":  ("æ",   "ah"),
    "ɑː": ("ɑː",  "ah"),
    "ə":  ("ə",   "uh"),
    "ɚ":  ("ɚ",   "er"),
    "ɛ":  ("ɛ",   "eh"),
    "ɪ":  ("ɪ",   "ih"),
    "iː": ("iː",  "ee"),
    "ɔː": ("ɔː",  "aw"),
    "ʊ":  ("ʊ",   "oo"),
    "uː": ("uː",  "oo"),
    "ʌ":  ("ʌ",   "uh"),
    "aɪ": ("aɪ",  "eye"),
    "aʊ": ("aʊ",  "ow"),
    "eɪ": ("eɪ",  "ay"),
    "ɔɪ": ("ɔɪ",  "oy"),
    "oʊ": ("oʊ",  "oh"),
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
    "ʊ":  ["oo", "u"],             # book, put
    "iː": ["ee", "ea", "ie"],      # feet, beach, field
    "eɪ": ["ai", "ay", "ea"],      # rain, day, break
    "aɪ": ["igh", "ie", "y"],      # night, pie, fly
    "oʊ": ["ow", "oa"],            # snow, boat
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
        if word_data.get("per", 0) <= 0:
            continue

        word = (word_data.get("ground_truth_word") or "").strip()

        for phoneme in word_data.get("missed", []):
            phoneme_to_error_words.setdefault(phoneme, []).append(
                {"word": word, "error_type": "missed"}
            )
        for phoneme in word_data.get("added", []):
            phoneme_to_error_words.setdefault(phoneme, []).append(
                {"word": word, "error_type": "added"}
            )
        for sub in word_data.get("substituted", []):
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

    ordered = _ordered_phonemes(phoneme_to_error_words, problem_summary)

    if not ordered:
        return FeedbackResult(text="Keep practicing!", ssml="Keep practicing!")

    text_parts: list[str] = []
    ssml_parts: list[str] = []

    for i, phoneme in enumerate(ordered):
        words = _words_for_phoneme(phoneme, phoneme_to_error_words, max_words=4)
        if not words:
            continue

        display = _display_name(phoneme)
        word_list = _oxford_list(words)

        # Plain text
        if i == 0:
            text_parts.append(
                f"You had trouble with the '{display}' sound — "
                f"you missed it in {word_list}."
            )
        else:
            text_parts.append(
                f"You also had trouble with the '{display}' sound in {word_list}."
            )

        # SSML
        tag = _phoneme_tag(phoneme)
        if i == 0:
            ssml_parts.append(
                f'You had trouble with the {tag} sound — '
                f'you missed it in <break time="200ms"/> {word_list}.'
            )
        else:
            ssml_parts.append(
                f'You also had trouble with the {tag} sound in '
                f'<break time="200ms"/> {word_list}.'
            )

    if not text_parts:
        return FeedbackResult(text="Keep practicing!", ssml="Keep practicing!")

    # Append tip for focus phoneme only — grapheme-centric if we can identify
    # the grapheme cluster from the error words, phoneme-level tip otherwise.
    focus_phoneme = ordered[0]
    focus_words = _words_for_phoneme(focus_phoneme, phoneme_to_error_words, max_words=4)
    tip = _tip_for_phoneme(focus_phoneme, focus_words)
    if tip:
        text_parts.append(tip)
        ssml_parts.append(tip)

    return FeedbackResult(
        text=" ".join(text_parts),
        ssml=" ".join(ssml_parts),
    )
