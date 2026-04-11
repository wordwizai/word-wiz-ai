"""
Phoneme Feedback Formatter

Generates natural-language feedback text and SSML from phoneme analysis data.
Pure function — no network calls, no GPT.

Used to produce feedback immediately after analysis so TTS can run in
parallel with the GPT call for the next sentence.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class FeedbackResult:
    text: str   # Plain-text feedback for display
    ssml: str   # SSML-enhanced feedback for TTS pronunciation


# Maps IPA phoneme symbols to human-readable letter combinations
# Used in plain text ("the 'th' sound") and SSML <say-as> tags
_IPA_TO_DISPLAY: dict[str, str] = {
    "θ": "th",   # voiceless th (think, three)
    "ð": "th",   # voiced th (the, this)
    "ʃ": "sh",   # sh (ship, wish)
    "tʃ": "ch",  # ch (chip, catch)
    "dʒ": "j",   # j (jump, bridge)
    "ŋ": "ng",   # ng (sing, ring)
    "ʒ": "zh",   # zh (measure, vision)
    "j": "y",    # y (yes, you)
    # Simple consonants — use as-is
    "p": "p", "b": "b", "t": "t", "d": "d",
    "k": "k", "g": "g", "f": "f", "v": "v",
    "s": "s", "z": "z", "h": "h", "m": "m",
    "n": "n", "l": "l", "r": "r", "w": "w",
}


def _display_name(phoneme: str) -> str:
    """Return a human-readable letter name for an IPA phoneme."""
    return _IPA_TO_DISPLAY.get(phoneme, phoneme)


def _word_ipa(word: str, pronunciation_data: list[dict]) -> Optional[str]:
    """
    Return the joined IPA string for a word's expected pronunciation.

    Looks up the word in pronunciation_data and joins its expected phonemes.
    Returns None if the word isn't found or has no phoneme data.
    """
    for entry in pronunciation_data:
        entry_word = (entry.get("ground_truth_word") or "").strip()
        if entry_word.lower() == word.lower():
            gt = entry.get("ground_truth_phonemes", [])
            # ground_truth_phonemes can arrive as (word, [phonemes]) tuple
            if isinstance(gt, tuple) and len(gt) == 2:
                gt = gt[1]
            if isinstance(gt, list) and gt:
                return "".join(str(p) for p in gt)
    return None


def build_phoneme_to_error_words(pronunciation_data: list[dict]) -> dict[str, list[dict]]:
    """
    Build a mapping of phoneme → list of error word entries from pronunciation data.

    Each entry is {"word": str, "error_type": "missed"|"added"|"substituted"}.
    Only words with per > 0 are included.

    This logic was previously duplicated across all three mode files.
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

    Args:
        problem_summary: From analyze_results() — contains recommended_focus_phoneme,
                         phoneme_error_counts, etc. phoneme_to_error_words is built
                         here if not already present.
        per_summary:     From analyze_results() — contains sentence_per.
        pronunciation_data: Raw pronunciation records (pronunciation_dataframe.to_dict('records')).
                            Used for IPA lookup for SSML phoneme tags.

    Returns:
        FeedbackResult with .text (plain) and .ssml (for TTS).
    """
    # phoneme_to_error_words may or may not already be in problem_summary
    phoneme_to_error_words: dict = (
        problem_summary.get("phoneme_to_error_words")
        or build_phoneme_to_error_words(pronunciation_data)
    )

    sentence_per: float = (per_summary or {}).get("sentence_per", 0.0)

    # Perfect pronunciation — no errors
    if not phoneme_to_error_words and sentence_per <= 0.2:
        return FeedbackResult(text="Great job!", ssml="Great job!")

    # Determine the focus phoneme
    focus_phoneme: Optional[str] = None

    recommended = problem_summary.get("recommended_focus_phoneme")
    if recommended and isinstance(recommended, (list, tuple)) and len(recommended) >= 1:
        focus_phoneme = str(recommended[0])

    # Fallback to highest-count error phoneme
    if not focus_phoneme:
        error_counts: dict = problem_summary.get("phoneme_error_counts", {})
        if error_counts:
            focus_phoneme = max(error_counts, key=lambda k: error_counts[k])

    # Further fallback: first key in phoneme_to_error_words
    if not focus_phoneme and phoneme_to_error_words:
        focus_phoneme = next(iter(phoneme_to_error_words))

    if not focus_phoneme or focus_phoneme not in phoneme_to_error_words:
        return FeedbackResult(text="Keep practicing!", ssml="Keep practicing!")

    # Collect up to 3 unique words that had errors with the focus phoneme
    seen: set[str] = set()
    words: list[str] = []
    for entry in phoneme_to_error_words[focus_phoneme]:
        w = (entry.get("word") or "").strip()
        if w and w not in seen:
            seen.add(w)
            words.append(w)
        if len(words) == 3:
            break

    if not words:
        return FeedbackResult(text="Keep practicing!", ssml="Keep practicing!")

    display = _display_name(focus_phoneme)

    # ── Plain text ──────────────────────────────────────────────────────────
    if len(words) == 1:
        text = f"You had trouble with the '{display}' sound in '{words[0]}'."
    elif len(words) == 2:
        text = (
            f"You had trouble with the '{display}' sound "
            f"in '{words[0]}' and '{words[1]}'."
        )
    else:
        text = (
            f"You had trouble with the '{display}' sound "
            f"in '{words[0]}', '{words[1]}', and '{words[2]}'."
        )

    # ── SSML ─────────────────────────────────────────────────────────────────
    # Spell out the phoneme name (e.g. "th" → "tee-aitch" via say-as)
    say_as = f'<say-as interpret-as="spell-out">{display}</say-as>'

    def _tag_word(w: str) -> str:
        ipa = _word_ipa(w, pronunciation_data)
        if ipa:
            return f'<phoneme alphabet="ipa" ph="{ipa}">{w}</phoneme>'
        # No IPA found — fall back to plain word (TTS will pronounce it naturally)
        return w

    tagged = [_tag_word(w) for w in words]

    if len(tagged) == 1:
        ssml = f"You had trouble with the {say_as} sound in {tagged[0]}."
    elif len(tagged) == 2:
        ssml = (
            f"You had trouble with the {say_as} sound "
            f"in {tagged[0]} and {tagged[1]}."
        )
    else:
        ssml = (
            f"You had trouble with the {say_as} sound "
            f"in {tagged[0]}, {tagged[1]}, and {tagged[2]}."
        )

    return FeedbackResult(text=text, ssml=ssml)
