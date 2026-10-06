"""Join pipeline outcomes with speechocean762 labels and compute the benchmark summary."""

from __future__ import annotations

from dataclasses import dataclass, field

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
class ItemSet:
    words: list = field(default_factory=list)
    phones: list = field(default_factory=list)
    sentences: list = field(default_factory=list)
    clips: int = 0
    rejected: int = 0
    rejected_by_type: dict = field(default_factory=dict)
    word_count_mismatch: int = 0
    g2p_agree: int = 0
    g2p_total: int = 0
    phones_unmapped: int = 0


def build_items(clips, outcomes: dict) -> ItemSet:
    items = ItemSet()
    for clip in clips:
        if clip.utt_id not in outcomes:
            raise KeyError(f"no outcome for clip {clip.utt_id}")
        outcome = outcomes[clip.utt_id]
        items.clips += 1
        if outcome["status"] != "ok":
            items.rejected += 1
            key = outcome.get("error_type") or "unknown"
            items.rejected_by_type[key] = items.rejected_by_type.get(key, 0) + 1
            continue
        records = [r for r in outcome["words"] if r.get("type") != "insertion"]
        if len(records) != len(clip.words):
            items.word_count_mismatch += 1
            continue
        total_phonemes = sum(r.get("total_phonemes") or 0 for r in outcome["words"])
        total_errors = sum(r.get("total_errors") or 0 for r in outcome["words"])
        items.sentences.append(SentenceItem(
            clip.utt_id, clip.speaker, clip.is_child, clip.sentence_accuracy,
            total_errors / total_phonemes if total_phonemes else 0.0,
        ))
        for word, record in zip(clip.words, records):
            items.words.append(WordItem(
                clip.utt_id, clip.speaker, clip.is_child, word.text, word.accuracy,
                M.word_is_mistake(word.accuracy), float(record.get("per") or 0.0),
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


def summarize(items: ItemSet, threshold: float) -> dict:
    out = {
        "threshold": threshold,
        "clips": items.clips,
        "rejected": items.rejected,
        "unexpected_failures": sum(v for k, v in items.rejected_by_type.items() if k.startswith("unexpected:")),
        "rejection_rate": items.rejected / items.clips if items.clips else 0.0,
        "rejected_by_type": dict(sorted(items.rejected_by_type.items())),
        "word_count_mismatch": items.word_count_mismatch,
        "g2p_disagreement_rate": 1 - items.g2p_agree / items.g2p_total if items.g2p_total else 0.0,
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
    out["pr_curve"] = M.pr_curve(labels, scores)
    out["pearson"] = {
        "word": M.pearson([w.human_accuracy for w in items.words], [-w.per for w in items.words]),
        "phone": M.pearson([p.human_accuracy for p in items.phones],
                           [0.0 if p.system_error else 1.0 for p in items.phones]),
        "sentence": M.pearson([s.human_accuracy for s in items.sentences],
                              [-s.sentence_per for s in items.sentences]),
    }
    return out
