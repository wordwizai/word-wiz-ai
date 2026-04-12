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


# Maps IPA phoneme symbols to human-readable letter combinations for plain text
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
    # Simple consonants — use as-is
    "p": "p", "b": "b", "t": "t", "d": "d",
    "k": "k", "ɡ": "g", "g": "g", "f": "f", "v": "v",
    "s": "s", "z": "z", "h": "h", "m": "m",
    "n": "n", "l": "l", "w": "w",
}

# Maps IPA phoneme → (ph_attribute, demo_syllable) for Google Cloud TTS <phoneme> tags.
# The demo syllable is wrapped in <phoneme ph="..."> so TTS produces the target sound.
# Google's supported IPA consonants: p b t d k ɡ m n ŋ f v s z θ ð ʃ ʒ h l ɹ ʧ ʤ j w
# Google's supported IPA vowels: æ ɑː ə ɚ ɛ ɪ iː ɔː ʊ uː ʌ aɪ aʊ eɪ ɔɪ oʊ
_IPA_DEMO: dict[str, tuple[str, str]] = {
    # Consonants
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
    # Vowels
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

PRONUNCIATION_TIPS: dict[str, str] = {
    "uː": "When you see two O's next to each other, they usually make an 'oo' sound, like in food or moon.",
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
    "ʊ":  "This is a short 'oo' sound — like in 'book' or 'put', not the long 'oo'.",
    "ʌ":  "This is a short 'uh' sound — like in 'cup' or 'fun'.",
    "aɪ": "This diphthong starts with 'ah' and glides to 'ee' — like in 'bite' or 'fly'.",
    "eɪ": "This diphthong starts with 'eh' and glides to 'ee' — like in 'date' or 'say'.",
    "oʊ": "This diphthong starts with 'oh' and glides closed — like in 'go' or 'home'.",
    "ʧ":  "The 'ch' sound — press your tongue to the roof of your mouth and release with a puff of air.",
    "tʃ": "The 'ch' sound — press your tongue to the roof of your mouth and release with a puff of air.",
    "ʤ":  "The 'j' sound — same as 'ch' but use your voice.",
    "dʒ": "The 'j' sound — same as 'ch' but use your voice.",
    "ʒ":  "This sound is like 'sh' but voiced — like the middle of 'measure' or 'vision'.",
    "v":  "The 'v' sound — bite your lower lip lightly and use your voice, like 'f' but voiced.",
    "z":  "The 'z' sound — same as 's' but use your voice.",
}


def _display_name(phoneme: str) -> str:
    """Return a human-readable letter name for an IPA phoneme."""
    return _IPA_TO_DISPLAY.get(phoneme, phoneme)


def _phoneme_tag(phoneme: str) -> str:
    """
    Return a Google Cloud TTS <phoneme> tag that plays the target sound in isolation.
    Falls back to a quoted display name if the phoneme isn't in the demo table.
    """
    if phoneme in _IPA_DEMO:
        ph_attr, demo_text = _IPA_DEMO[phoneme]
        return f'<phoneme alphabet="ipa" ph="{ph_attr}">{demo_text}</phoneme>'
    return f"'{_display_name(phoneme)}'"


def _oxford_list(words: list[str]) -> str:
    """Format a word list with Oxford comma: 'a', 'a and b', 'a, b, and c'."""
    if len(words) == 1:
        return words[0]
    if len(words) == 2:
        return f"{words[0]} and {words[1]}"
    return ", ".join(words[:-1]) + f", and {words[-1]}"


def _words_for_phoneme(phoneme: str, phoneme_to_error_words: dict, max_words: int = 4) -> list[str]:
    """Return up to max_words unique words that had errors with this phoneme."""
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
    """
    Return phonemes with errors in pedagogical order:
    recommended_focus_phoneme first, then others sorted by error count descending.
    """
    recommended = problem_summary.get("recommended_focus_phoneme")
    focus: Optional[str] = None
    if recommended and isinstance(recommended, (list, tuple)) and len(recommended) >= 1:
        focus = str(recommended[0])
    # Fallback: highest error count
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

        # ground_truth_word can be None for insertion-type alignment entries
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
            # substituted entries are (expected_phoneme, actual_phoneme) pairs
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

    Feedback covers all problem phonemes (recommended focus first, then others
    by error count). A pronunciation tip is appended for the focus phoneme only.

    Args:
        problem_summary: From analyze_results() — contains recommended_focus_phoneme,
                         phoneme_error_counts, etc. phoneme_to_error_words is built
                         here if not already present.
        per_summary:     From analyze_results() — contains sentence_per.
        pronunciation_data: Raw pronunciation records (pronunciation_dataframe.to_dict('records')).

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

        # ── Plain text ──────────────────────────────────────────────────────
        if i == 0:
            text_parts.append(
                f"You had trouble with the '{display}' sound — "
                f"you missed it in {word_list}."
            )
        else:
            text_parts.append(
                f"You also had trouble with the '{display}' sound in {word_list}."
            )

        # ── SSML ─────────────────────────────────────────────────────────────
        tag = _phoneme_tag(phoneme)
        if i == 0:
            ssml_parts.append(
                f"You had trouble with the {tag} sound — "
                f"you missed it in <break time=\"200ms\"/> {word_list}."
            )
        else:
            ssml_parts.append(
                f"You also had trouble with the {tag} sound in "
                f"<break time=\"200ms\"/> {word_list}."
            )

    if not text_parts:
        return FeedbackResult(text="Keep practicing!", ssml="Keep practicing!")

    # Append pronunciation tip for the focus phoneme (first in ordered list)
    tip = PRONUNCIATION_TIPS.get(ordered[0], "")
    if tip:
        text_parts.append(tip)
        ssml_parts.append(tip)

    text = " ".join(text_parts)
    ssml = " ".join(ssml_parts)

    return FeedbackResult(text=text, ssml=ssml)
