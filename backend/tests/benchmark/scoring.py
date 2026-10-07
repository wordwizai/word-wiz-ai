"""Join pipeline outcomes with speechocean762 labels and compute the benchmark summary."""

from __future__ import annotations

import math
import numbers
from dataclasses import dataclass, field

import numpy as np

from . import metrics as M
from .phones import canonical_ipa, g2p_agrees, gt_error_flags, map_canonical_to_system


@dataclass
class WordItem:
    utt_id: str
    speaker: str
    is_child: bool
    text: str
    human_accuracy: float
    is_mistake: bool
    per: float


@dataclass
class PhoneItem:
    utt_id: str
    speaker: str
    is_child: bool
    human_accuracy: float
    is_mistake: bool
    is_mistake_strict: bool
    system_error: bool


@dataclass
class SentenceItem:
    utt_id: str
    speaker: str
    is_child: bool
    human_accuracy: float
    sentence_per: float


@dataclass
class FeedbackItem:
    """The spoken feedback of one ok clip, checked against the experts' word labels.

    A word status is "mistake" (the experts scored it 0 to 6), "correct" (7 to 10) or
    "unmatched" (no scored word in the clip has that text).
    """

    utt_id: str
    speaker: str
    is_child: bool
    kind: str  # "correction", "praise" or "generic"
    has_mistake: bool  # at least one scored word in the clip is a real mistake
    first_word: str | None  # status of the first focus word, the one the text names. None unless a correction
    named: list = field(default_factory=list)  # status of each focus word, deduplicated by normalized text


@dataclass
class ItemSet:
    words: list = field(default_factory=list)
    phones: list = field(default_factory=list)
    sentences: list = field(default_factory=list)
    feedback: list = field(default_factory=list)
    clips: int = 0
    rejected: int = 0
    rejected_by_type: dict = field(default_factory=dict)
    word_count_mismatch: int = 0
    g2p_agree: int = 0
    g2p_total: int = 0
    phones_unmapped: int = 0


def _checked_per(clip, record) -> float:
    per = record.get("per")
    if isinstance(per, bool) or not isinstance(per, numbers.Real) or not math.isfinite(per):
        raise ValueError(
            f"clip {clip.utt_id}: word record for {record.get('ground_truth_word')!r} has per {per!r}, "
            "which is not a finite number"
        )
    return float(per)


def _lines_up(clip, records) -> bool:
    """True when the records are, in order, one per scored word and about those words.

    Insertions are not in `records`. The join is by position, so a record about another word
    would score a child's reading against the wrong expert label. production cleans the
    sentence before G2P (clean_sentence), and that is what ground_truth_word holds.
    """
    from core.grapheme_to_phoneme import clean_sentence  # lazy, so importing this module loads no core code

    return len(records) == len(clip.words) and all(
        record.get("ground_truth_word") == clean_sentence(word.text)
        for word, record in zip(clip.words, records)
    )


FEEDBACK_KINDS = ("correction", "generic", "praise")


def normalize_word(text) -> str:
    """Lowercase with punctuation and spaces removed, so "Dog." and "DOG" are the same word."""
    return "".join(ch for ch in str(text).lower() if ch.isalnum())


def _feedback_item(clip, feedback: dict) -> FeedbackItem:
    kind = feedback.get("kind")
    if kind not in FEEDBACK_KINDS:
        raise ValueError(f"clip {clip.utt_id}: feedback kind is {kind!r}, expected one of {FEEDBACK_KINDS}")
    # A named word counts as a real mistake when ANY occurrence of that text in the clip is one.
    # The feedback names a word, not a position, and a repeated word in one sentence is rare
    # (a second "the", say), so this reading gives the feedback the benefit of the doubt.
    mistakes: dict[str, bool] = {}
    for word in clip.words:
        key = normalize_word(word.text)
        mistakes[key] = mistakes.get(key, False) or M.word_is_mistake(word.accuracy)

    def status(text) -> str:
        key = normalize_word(text)
        if key not in mistakes:
            return "unmatched"
        return "mistake" if mistakes[key] else "correct"

    focus = list(feedback.get("focus_words") or []) if kind == "correction" else []
    if kind == "correction" and not focus:
        raise ValueError(f"clip {clip.utt_id}: feedback is a correction but names no words")
    named, seen = [], set()
    for text in focus:
        key = normalize_word(text)
        if key not in seen:
            seen.add(key)
            named.append(status(text))
    return FeedbackItem(
        clip.utt_id, clip.speaker, clip.is_child, kind,
        any(mistakes.values()), status(focus[0]) if focus else None, named,
    )


def build_items(clips, outcomes: dict) -> ItemSet:
    items = ItemSet()
    for clip in clips:
        if clip.utt_id not in outcomes:
            raise KeyError(f"no outcome for clip {clip.utt_id}")
        outcome = outcomes[clip.utt_id]
        status = outcome["status"]
        if status not in ("ok", "rejected"):
            raise ValueError(f"clip {clip.utt_id}: outcome status is {status!r}, expected 'ok' or 'rejected'")
        items.clips += 1
        if status == "rejected":
            items.rejected += 1
            key = outcome.get("error_type") or "unknown"
            items.rejected_by_type[key] = items.rejected_by_type.get(key, 0) + 1
            continue
        records = [r for r in outcome["words"] if r.get("type") != "insertion"]
        pers = [_checked_per(clip, r) for r in records]
        # Results written before feedback was recorded have no "feedback" key. A misaligned clip
        # keeps its feedback, since the words are matched by text and not by position.
        if isinstance(outcome.get("feedback"), dict):
            items.feedback.append(_feedback_item(clip, outcome["feedback"]))
        if not _lines_up(clip, records):
            items.word_count_mismatch += 1
            continue
        total_phonemes = sum(r.get("total_phonemes") or 0 for r in outcome["words"])
        total_errors = sum(r.get("total_errors") or 0 for r in outcome["words"])
        items.sentences.append(SentenceItem(
            clip.utt_id, clip.speaker, clip.is_child, clip.sentence_accuracy,
            total_errors / total_phonemes if total_phonemes else 0.0,
        ))
        for word, record, per in zip(clip.words, records, pers):
            items.words.append(WordItem(
                clip.utt_id, clip.speaker, clip.is_child, word.text, word.accuracy,
                M.word_is_mistake(word.accuracy), per,
            ))
            expected = list(record.get("expected_phonemes") or [])
            canonical = canonical_ipa(word.phones)
            items.g2p_total += 1
            items.g2p_agree += int(g2p_agrees(canonical, expected))
            errors = gt_error_flags(expected, record.get("actual_phonemes") or [])
            for k, system_idx in enumerate(map_canonical_to_system(canonical, expected)):
                if not system_idx:
                    items.phones_unmapped += 1
                    continue
                accuracy = word.phone_accuracy[k]
                items.phones.append(PhoneItem(
                    clip.utt_id, clip.speaker, clip.is_child, accuracy,
                    M.phone_is_mistake(accuracy), M.phone_is_mistake(accuracy, strict=True),
                    any(errors[j] for j in system_idx),
                ))
    return items


SLICES = {
    "all": lambda item: True,
    "children": lambda item: item.is_child,
    "adults": lambda item: not item.is_child,
}


def _metrics(labels, flags) -> dict:
    c = M.confusion(labels, flags)
    return {
        "n": c.n,
        "mistakes": int(sum(labels)),
        "f05": c.f_beta(),
        "precision": c.precision,
        "recall": c.recall,
        "false_alarm_rate": c.false_alarm_rate,
        "counts": [c.tp, c.fp, c.fn, c.tn],
    }


def word_slice_metrics(words, threshold: float) -> dict:
    return _metrics([w.is_mistake for w in words], M.flags_at([w.per for w in words], threshold))


def phone_slice_metrics(phones, strict: bool) -> dict:
    labels = [p.is_mistake_strict if strict else p.is_mistake for p in phones]
    return _metrics(labels, [p.system_error for p in phones])


#: Every feedback rate is a sum of per-clip (numerator, denominator) parts, so the same
#: definitions give the point estimates and the per-speaker counts compare bootstraps.
FEEDBACK_RATES = {
    # Of the corrections, how many name a word the experts marked as a mistake.
    "correction_precision": lambda f: (f.first_word == "mistake", f.kind == "correction"),
    # Of all the words corrections pick for their focus sound, how many are real mistakes.
    "named_word_precision": lambda f: (sum(s == "mistake" for s in f.named), len(f.named)),
    # Of all readings, how often the child is told to fix a word they read correctly.
    "wrong_correction_rate": lambda f: (f.first_word == "correct", 1),
    # Of the readings without a mistake, how many are praised.
    "clean_praise_rate": lambda f: (f.kind == "praise" and not f.has_mistake, not f.has_mistake),
    # Of the readings with at least one mistake, how many are praised anyway.
    "false_praise_rate": lambda f: (f.kind == "praise" and f.has_mistake, f.has_mistake),
}


def _rate_parts(items, rate):
    num = den = 0
    for f in items:
        n, d = FEEDBACK_RATES[rate](f)
        num, den = num + int(n), den + int(d)
    return num, den


def feedback_slice_metrics(items) -> dict:
    """The feedback rates over these clips. A rate with nothing to divide by is None."""
    n = len(items)
    kinds = {kind: sum(f.kind == kind for f in items) for kind in FEEDBACK_KINDS}
    out = {"n_clips": n, "kind_share": {kind: kinds[kind] / n if n else 0.0 for kind in FEEDBACK_KINDS}}
    parts = {rate: _rate_parts(items, rate) for rate in FEEDBACK_RATES}
    for rate, (num, den) in parts.items():
        out[rate] = num / den if den else None
    out["counts"] = {
        **kinds,
        "first_word_mistake": parts["correction_precision"][0],
        "first_word_correct": parts["wrong_correction_rate"][0],
        "first_word_unmatched": sum(f.first_word == "unmatched" for f in items),
        "named_words": parts["named_word_precision"][1],
        "named_mistakes": parts["named_word_precision"][0],
        "named_unmatched": sum(s == "unmatched" for f in items for s in f.named),
        "clean_clips": parts["clean_praise_rate"][1],
        "clean_praised": parts["clean_praise_rate"][0],
        "mistake_clips": parts["false_praise_rate"][1],
        "mistake_praised": parts["false_praise_rate"][0],
    }
    return out


def feedback_rate_counts(items: ItemSet, rate: str) -> dict:
    """Per-speaker (numerator, denominator) of one feedback rate, for metrics.bootstrap_ratio_delta."""
    out: dict[str, np.ndarray] = {}
    for f in items.feedback:
        n, d = FEEDBACK_RATES[rate](f)
        out.setdefault(f.speaker, np.zeros(2, dtype=np.int64))
        out[f.speaker] += (int(n), int(d))
    return out


def summarize(items: ItemSet, threshold: float) -> dict:
    out = {
        "threshold": threshold,
        "clips": items.clips,
        "rejected": items.rejected,
        "unexpected_failures": sum(v for k, v in items.rejected_by_type.items() if k.startswith("unexpected:")),
        "rejection_rate": items.rejected / items.clips if items.clips else 0.0,
        # Clips that drop out of every metric, rejected or misaligned. A candidate must not be
        # able to hide hard clips behind either one.
        "unscored_rate": (items.rejected + items.word_count_mismatch) / items.clips if items.clips else 0.0,
        "rejected_by_type": dict(sorted(items.rejected_by_type.items())),
        "word_count_mismatch": items.word_count_mismatch,
        "g2p_disagreement_rate": 1 - items.g2p_agree / items.g2p_total if items.g2p_total else None,
        "phones_unmapped": items.phones_unmapped,
        "word": {},
        "phone": {},
        "phone_strict": {},
    }
    for name, keep in SLICES.items():
        words = [w for w in items.words if keep(w)]
        phones = [p for p in items.phones if keep(p)]
        out["word"][name] = word_slice_metrics(words, threshold)
        out["phone"][name] = phone_slice_metrics(phones, strict=False)
        out["phone_strict"][name] = phone_slice_metrics(phones, strict=True)
    labels = [w.is_mistake for w in items.words]
    scores = [w.per for w in items.words]
    best_t, best_f = M.best_threshold(labels, scores)
    out["best_threshold"] = {"threshold": best_t, "f05": best_f}
    # The F0.5 of flagging every word, the reference point any threshold has to beat.
    out["flag_all_f05"] = M.confusion(labels, [True] * len(labels)).f_beta()
    out["pr_curve"] = M.pr_curve(labels, scores)
    out["pearson"] = {
        "word": M.pearson([w.human_accuracy for w in items.words], [-w.per for w in items.words]),
        "phone": M.pearson([p.human_accuracy for p in items.phones],
                           [0.0 if p.system_error else 1.0 for p in items.phones]),
        "sentence": M.pearson([s.human_accuracy for s in items.sentences],
                              [-s.sentence_per for s in items.sentences]),
    }
    # The spoken feedback, scored over ok clips that recorded it. None for results files
    # written before it was recorded.
    out["feedback"] = (
        {name: feedback_slice_metrics([f for f in items.feedback if keep(f)]) for name, keep in SLICES.items()}
        if items.feedback else None
    )
    return out
