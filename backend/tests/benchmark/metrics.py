"""Pure metric functions for the benchmark. No I/O and no core imports."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

#: speechocean762 word rubric. 0-6 means phones wrong, the wrong word, or missed.
WORD_MISTAKE_MAX = 6
#: Phone rubric. 0 means incorrect or missed, 1 heavy accent, 2 correct.
PHONE_MISTAKE_MAX = 0
PHONE_MISTAKE_MAX_STRICT = 1
F_BETA = 0.5


def rounded(score: float) -> int:
    """Round half up. Released phone scores are 5-annotator averages such as 1.8."""
    return math.floor(float(score) + 0.5)


def word_is_mistake(accuracy: float) -> bool:
    return rounded(accuracy) <= WORD_MISTAKE_MAX


def phone_is_mistake(accuracy: float, strict: bool = False) -> bool:
    return rounded(accuracy) <= (PHONE_MISTAKE_MAX_STRICT if strict else PHONE_MISTAKE_MAX)


def _ratio(num, den) -> float:
    return float(num) / den if den else 0.0


def f_beta_from_counts(counts, beta: float = F_BETA):
    """F-beta from arrays shaped [..., 4] of (tp, fp, fn, tn). 0 where undefined."""
    counts = np.asarray(counts, dtype=np.float64)
    tp, fp, fn = counts[..., 0], counts[..., 1], counts[..., 2]
    b2 = beta * beta
    den = (1 + b2) * tp + b2 * fn + fp
    return np.where(den > 0, (1 + b2) * tp / np.where(den > 0, den, 1), 0.0)


@dataclass(frozen=True)
class Counts:
    tp: int = 0
    fp: int = 0
    fn: int = 0
    tn: int = 0

    @property
    def n(self) -> int:
        return self.tp + self.fp + self.fn + self.tn

    @property
    def precision(self) -> float:
        return _ratio(self.tp, self.tp + self.fp)

    @property
    def recall(self) -> float:
        return _ratio(self.tp, self.tp + self.fn)

    @property
    def false_alarm_rate(self) -> float:
        """Share of correctly read items that the system flagged."""
        return _ratio(self.fp, self.fp + self.tn)

    def f_beta(self, beta: float = F_BETA) -> float:
        return float(f_beta_from_counts([self.tp, self.fp, self.fn, self.tn], beta))


def _cell(label, flag) -> int:
    """Confusion cell index, 0 tp, 1 fp, 2 fn, 3 tn."""
    return 0 if (label and flag) else 1 if flag else 2 if label else 3


def confusion(labels, flags) -> Counts:
    """Confusion counts of boolean labels against boolean flags."""
    if len(labels) != len(flags):
        raise ValueError(f"labels ({len(labels)}) and flags ({len(flags)}) differ in length")
    cells = [0, 0, 0, 0]
    for label, flag in zip(labels, flags):
        cells[_cell(label, flag)] += 1
    return Counts(*cells)


def flags_at(scores, threshold: float) -> list[bool]:
    """Flag when score >= threshold."""
    return [s >= threshold for s in scores]


#: pr_curve keeps at most this many points so results files stay small with continuous scores.
PR_CURVE_MAX_POINTS = 200


def _sweep(labels, scores):
    """Distinct thresholds in descending order, with [T, 4] (tp, fp, fn, tn) counts for flagging score >= t."""
    s = np.asarray(scores, dtype=float)
    y = np.asarray(labels, dtype=bool)
    if s.shape != y.shape:
        raise ValueError(f"labels ({y.size}) and scores ({s.size}) differ in length")
    if s.size == 0:
        return np.empty(0), np.empty((0, 4), dtype=np.int64)
    order = np.argsort(-s, kind="stable")
    s, y = s[order], y[order]
    tp, fp = np.cumsum(y), np.cumsum(~y)
    last = np.r_[s[1:] != s[:-1], True]
    tp, fp = tp[last], fp[last]
    pos = int(y.sum())
    return s[last], np.stack([tp, fp, pos - tp, (y.size - pos) - fp], axis=-1)


def best_threshold(labels, scores, beta: float = F_BETA):
    """(threshold, F-beta) maximizing F-beta, flagging score >= threshold.

    Ties go to the higher threshold, which flags fewer words. Returns (None, 0.0) when no
    threshold gives a positive F-beta.
    """
    thresholds, counts = _sweep(labels, scores)
    if thresholds.size == 0:
        return None, 0.0
    f = f_beta_from_counts(counts, beta)
    # argmax returns the first maximum, and thresholds are descending, so ties pick the highest.
    i = int(np.argmax(f))
    return (float(thresholds[i]), float(f[i])) if f[i] > 0 else (None, 0.0)


def pr_curve(labels, scores, max_points: int = PR_CURVE_MAX_POINTS) -> list[dict]:
    """Precision, recall and false-alarm rate per threshold, ascending, thinned to max_points."""
    thresholds, counts = _sweep(labels, scores)
    thresholds, counts = thresholds[::-1], counts[::-1]
    n = thresholds.size
    if n > max_points:
        keep = np.unique(np.linspace(0, n - 1, max_points).round().astype(int))
        thresholds, counts = thresholds[keep], counts[keep]
    points = []
    for t, row in zip(thresholds, counts):
        c = Counts(*(int(v) for v in row))
        points.append({
            "threshold": float(t),
            "precision": c.precision,
            "recall": c.recall,
            "false_alarm_rate": c.false_alarm_rate,
        })
    return points


def pearson(x, y):
    """Pearson r, or None when undefined (fewer than 2 points, non-finite values or zero variance)."""
    if len(x) != len(y):
        raise ValueError("x and y differ in length")
    if len(x) < 2:
        return None
    xa, ya = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    if not (np.isfinite(xa).all() and np.isfinite(ya).all()):
        return None
    if np.ptp(xa) == 0 or np.ptp(ya) == 0:
        return None
    return float(np.corrcoef(xa, ya)[0, 1])


def per_speaker_counts(speakers, labels, flags) -> dict[str, np.ndarray]:
    """Counts per speaker in (tp, fp, fn, tn) order."""
    if not (len(speakers) == len(labels) == len(flags)):
        raise ValueError(
            f"speakers ({len(speakers)}), labels ({len(labels)}) and flags ({len(flags)}) differ in length"
        )
    out: dict[str, np.ndarray] = {}
    for speaker, label, flag in zip(speakers, labels, flags):
        arr = out.setdefault(speaker, np.zeros(4, dtype=np.int64))
        arr[_cell(label, flag)] += 1
    return out


def _paired_speaker_resamples(base_counts, cand_counts, n_resamples, seed, width):
    """Summed per-speaker counts of both systems for each resample, shaped [n_resamples, width].

    Speakers are resampled with replacement and the same resample is applied to both
    systems. Clips from one speaker are correlated, so resampling clips instead would
    make noise look like signal.
    """
    if n_resamples < 1:
        raise ValueError("n_resamples must be >= 1")
    speakers = sorted(set(base_counts) | set(cand_counts))
    if not speakers:
        raise ValueError("no speakers to resample")
    zero = np.zeros(width, dtype=np.int64)
    base = np.stack([base_counts.get(s, zero) for s in speakers])
    cand = np.stack([cand_counts.get(s, zero) for s in speakers])
    rng = np.random.default_rng(seed)
    picks = rng.integers(0, len(speakers), size=(n_resamples, len(speakers)))
    return base[picks].sum(axis=1), cand[picks].sum(axis=1)


def bootstrap_fbeta_delta(base_counts, cand_counts, n_resamples=2000, seed=0, beta=F_BETA):
    """Paired speaker bootstrap of F-beta(candidate) minus F-beta(base), from (tp, fp, fn, tn) per speaker."""
    base, cand = _paired_speaker_resamples(base_counts, cand_counts, n_resamples, seed, 4)
    return f_beta_from_counts(cand, beta) - f_beta_from_counts(base, beta)


def ratio_from_counts(counts):
    """numerator / denominator from arrays shaped [..., 2]. 0 where the denominator is 0."""
    counts = np.asarray(counts, dtype=np.float64)
    num, den = counts[..., 0], counts[..., 1]
    return np.where(den > 0, num / np.where(den > 0, den, 1), 0.0)


def bootstrap_ratio_delta(base_counts, cand_counts, n_resamples=2000, seed=0):
    """Paired speaker bootstrap of a pooled rate, candidate minus base.

    The counts are (numerator, denominator) per speaker, and each resample pools them before
    dividing, so the rate is over clips and not an average of speakers' rates. The resampling
    is the one bootstrap_fbeta_delta uses, with the same seed giving the same draws. A resample
    whose denominator is 0 counts as rate 0, as f_beta_from_counts does for undefined F-beta.
    """
    base, cand = _paired_speaker_resamples(base_counts, cand_counts, n_resamples, seed, 2)
    return ratio_from_counts(cand) - ratio_from_counts(base)


def percentile_interval(values, level: float = 0.95) -> tuple[float, float]:
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        raise ValueError("no values to summarize")
    alpha = (1.0 - level) / 2.0
    lo, hi = np.quantile(arr, [alpha, 1.0 - alpha])
    return float(lo), float(hi)
