"""Score a phonics pattern session from its saved readings.

Only the words that practise the pattern count. On a word line that is every
word. On a sentence line it is the words on the pattern's word list. Only
the first reading of each line counts, because the mic stays available after
a reading and reading a line again shouldn't move the score.
"""

import re

from core.guest_limits import normalize_sentence

# The same cutoff that turns a word badge green (frontend WordBadge.tsx), so
# the teacher's score matches the green and red words the child saw.
CORRECT_PER = 0.15
# Share of the pattern's words read right that counts as mastered.
MASTERY = 0.8

_NOT_WORD = re.compile(r"[^a-z']")


def normalize_word(word: str) -> str:
    return _NOT_WORD.sub("", word.lower().replace("’", "'"))


def line_index(pattern: dict, sentence: str) -> int | None:
    """Which of the pattern's lines `sentence` is, ignoring case and spacing."""
    target = normalize_sentence(sentence)
    for i, line in enumerate(pattern["lines"]):
        if normalize_sentence(line) == target:
            return i
    return None


def _word_scores(phoneme_analysis: dict | None) -> list[tuple[str, float]]:
    """(expected word, per) for each expected word in one saved reading."""
    frame = (phoneme_analysis or {}).get("pronunciation_dataframe") or {}
    words = frame.get("ground_truth_word") or {}
    pers = frame.get("per") or {}
    scored = []
    for row, word in words.items():
        if not word:
            continue  # an inserted sound, not one of the words on the line
        per = pers.get(row)
        scored.append((word, 1.0 if per is None else float(per)))
    return scored


def score_readings(pattern: dict, readings: list[tuple[str, dict]]) -> tuple[int, int]:
    """(pattern words read right, pattern words) over (sentence, analysis) in reading order."""
    pattern_words = {normalize_word(word) for word in pattern["words"]}
    seen: set[int] = set()
    correct = total = 0
    for sentence, phoneme_analysis in readings:
        index = line_index(pattern, sentence)
        if index is None or index in seen:
            continue
        seen.add(index)
        on_word_line = index < pattern["word_line_count"]
        for word, per in _word_scores(phoneme_analysis):
            if not on_word_line and normalize_word(word) not in pattern_words:
                continue
            total += 1
            if per < CORRECT_PER:
                correct += 1
    return correct, total


def is_mastered(words_correct: int | None, words_total: int | None) -> bool:
    return bool(words_total) and words_correct / words_total >= MASTERY
