"""
Ground-truth-anchored phoneme -> word alignment.

WHY THIS MODULE EXISTS
----------------------
Today the Phoneme Error Rate is computed against whatever a general purpose ASR
*guessed* the child said:

    predicted_words_phonemes = g2p(" ".join(predicted_words))   # ASR's guess
    alignment = align_phonemes_to_words(flat_phonemes, predicted_words_phonemes)

Both ASRs in the pipeline (Deepgram ``nova-2`` on the server,
``Xenova/whisper-tiny.en`` on the client) are language-model driven: their whole
purpose is to emit the *intended* word regardless of how it was pronounced. A
child who reads "cat" as "tat", or who skips a word entirely, gets a clean,
grammatical transcript back. The acoustic phonemes are then regrouped against
that corrected transcript, so the real reading error is either dissolved or
smeared into the neighbouring words. It also makes scoring path dependent: the
two ASRs disagree with each other, so the same recording scores differently
depending on whether client-side extraction was enabled.

The correct target was available all along: ``ground_truth_phonemes``, derived
from ``attempted_sentence`` -- the text the child was actually asked to read.

WHAT THIS MODULE DOES
---------------------
1. Segments the flat acoustic phoneme stream directly against
   ``ground_truth_phonemes`` with a dynamic program that minimises the total
   phoneme edit distance. The ground truth -- never the ASR -- defines the
   buckets, so every expected word keeps its slot.
2. Allows a word to receive an EMPTY segment. That is how a skipped word is
   represented: it scores as fully missed instead of stealing phonemes from its
   neighbours and cascading the misalignment through the rest of the sentence.
3. Uses the ASR word list only as a SECONDARY signal:
     * words the ASR did not hear at all are preferred as skips ONLY when the
       acoustics leave the choice exactly tied -- the ASR sits in the last
       position of the cost tuple, so no number of ASR hints can outweigh a
       single phoneme of real acoustic evidence,
     * words the ASR heard that are not in the sentence are reported as
       ``insertion`` records,
     * the ASR word matched to each expected word is used only as the
       ``predicted_word`` label.
4. Is deterministic. All DP arithmetic is integer (costs are scaled by
   ``_COST_SCALE``) and every tie is broken by an explicit total ordering, so
   the same input always produces byte-identical output.

The returned value matches the existing contract of
``process_audio._process_word_alignment`` exactly -- same keys, same types --
so ``analyze_results``, ``SpeechProblemClassifier``,
``phoneme_feedback_formatter`` and the frontend need no changes.

FEATURE FLAG
------------
``WWAI_GT_ANCHORED_ALIGNMENT`` -- defaults to OFF. Nothing in this module runs
unless it is explicitly enabled.
"""

from __future__ import annotations

import os
import re

# --------------------------------------------------------------------------- #
# Feature flag
# --------------------------------------------------------------------------- #

GT_ANCHORED_FLAG = "WWAI_GT_ANCHORED_ALIGNMENT"

_TRUTHY = frozenset({"1", "true", "t", "yes", "y", "on"})


def is_gt_anchored_enabled() -> bool:
    """
    True when ``WWAI_GT_ANCHORED_ALIGNMENT`` is set to a truthy value.

    Read at call time (not import time) so that it can be toggled in tests and
    so a deploy-time env change does not require a code reload.
    """
    return os.environ.get(GT_ANCHORED_FLAG, "").strip().lower() in _TRUTHY


# --------------------------------------------------------------------------- #
# Tunables
# --------------------------------------------------------------------------- #

# All DP costs are integers scaled by this factor, so ties are exact and the
# result never depends on floating point rounding.
_COST_SCALE = 100

# Extra phonemes, beyond the length-ratio-scaled expectation, that a single
# ground-truth word is allowed to absorb.
_SEGMENT_SLACK = 6

# Unreachable marker for the DP table.
_UNREACHABLE = None

_WORD_NORM_RE = re.compile(r"[^a-z0-9']+")


# --------------------------------------------------------------------------- #
# Sequence alignment (self-contained copy)
# --------------------------------------------------------------------------- #
#
# Copied from ``process_audio.align_sequences`` rather than imported: importing
# ``process_audio`` from here would be circular, and ``process_audio`` drags in
# torch via ``phoneme_extractor``. Keeping this module dependency-free (stdlib
# only) also keeps its unit tests fast.


def align_sequences(gt: list, pred: list) -> list[tuple]:
    """
    Align two sequences with Levenshtein DP.

    Returns a list of ``(op, gt_item, pred_item)`` where ``op`` is one of
    ``match`` / ``substitution`` / ``deletion`` / ``insertion``. For a deletion
    the predicted item is ``None``; for an insertion the ground truth item is
    ``None``.

    Behaviourally identical to ``process_audio.align_sequences``.
    """
    m, n = len(gt), len(pred)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if gt[i - 1] == pred[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,          # deletion
                dp[i][j - 1] + 1,          # insertion
                dp[i - 1][j - 1] + cost,   # substitution or match
            )

    operations = []
    i, j = m, n
    while i > 0 or j > 0:
        if i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + (0 if gt[i - 1] == pred[j - 1] else 1):
            if gt[i - 1] == pred[j - 1]:
                operations.append(('match', gt[i - 1], pred[j - 1]))
            else:
                operations.append(('substitution', gt[i - 1], pred[j - 1]))
            i -= 1
            j -= 1
        elif i > 0 and dp[i][j] == dp[i - 1][j] + 1:
            operations.append(('deletion', gt[i - 1], None))
            i -= 1
        elif j > 0 and dp[i][j] == dp[i][j - 1] + 1:
            operations.append(('insertion', None, pred[j - 1]))
            j -= 1
    operations.reverse()
    return operations


# --------------------------------------------------------------------------- #
# Secondary ASR signal
# --------------------------------------------------------------------------- #


def _normalize_word(word) -> str:
    """Lowercase and strip punctuation, for comparing ASR words to expected words."""
    return _WORD_NORM_RE.sub("", str(word).lower())


def derive_asr_hints(
    ground_truth_words: list[str],
    predicted_words: list[str] | None,
) -> tuple[set[int], dict[int, str], dict[int, list[str]]]:
    """
    Turn the ASR word list into hints. It is NEVER allowed to drive segmentation.

    Returns:
        skip_hints:  indices of ground-truth words the ASR did not hear at all.
        pred_labels: ground-truth index -> the ASR word matched to it.
        insertions:  ground-truth index -> ASR words with no expected counterpart,
                     to be emitted immediately before that index. The key
                     ``len(ground_truth_words)`` holds trailing insertions.
    """
    skip_hints: set[int] = set()
    pred_labels: dict[int, str] = {}
    insertions: dict[int, list[str]] = {}

    words = [str(w) for w in (predicted_words or []) if w]
    if not words:
        # No secondary signal at all. Emit no hints rather than pretending the
        # ASR reported every word as skipped.
        return skip_hints, pred_labels, insertions

    ops = align_sequences(
        [_normalize_word(w) for w in ground_truth_words],
        [_normalize_word(w) for w in words],
    )

    gt_idx, pred_idx = 0, 0
    for op, _gt_item, _pred_item in ops:
        if op in ('match', 'substitution'):
            if gt_idx < len(ground_truth_words) and pred_idx < len(words):
                pred_labels[gt_idx] = words[pred_idx]
            gt_idx += 1
            pred_idx += 1
        elif op == 'insertion':
            if pred_idx < len(words):
                insertions.setdefault(gt_idx, []).append(words[pred_idx])
            pred_idx += 1
        elif op == 'deletion':
            skip_hints.add(gt_idx)
            gt_idx += 1

    return skip_hints, pred_labels, insertions


# --------------------------------------------------------------------------- #
# Ground-truth-anchored segmentation
# --------------------------------------------------------------------------- #


def segment_phonemes_by_ground_truth(
    flat_phonemes: list[str],
    ground_truth_phonemes: list[tuple[str, list[str]]],
    skip_hints: set[int] | frozenset = frozenset(),
) -> list[list[str]]:
    """
    Split the flat acoustic phoneme stream into one contiguous segment per
    EXPECTED word, minimising total phoneme edit distance.

    Unlike ``process_audio.align_phonemes_to_words`` this:
      * targets the ground truth sentence, not the ASR's transcript,
      * permits an empty segment, which is how a skipped word is represented,
      * uses integer costs and an explicit tie-break, so it is deterministic.

    Every acoustic phoneme is assigned to exactly one word (the segments
    partition the stream in order), matching the existing contract that no
    predicted phoneme is silently dropped.

    Args:
        flat_phonemes: the acoustic phoneme stream, flattened.
        ground_truth_phonemes: ``[(word, [phonemes]), ...]`` for the sentence
            the child was asked to read.
        skip_hints: indices the ASR also reports as missing (secondary signal).

    Returns:
        One list of phonemes per ground-truth word, same order and length as
        ``ground_truth_phonemes``.
    """
    flat = [str(p) for p in (flat_phonemes or [])]
    words = [list(phs or []) for _, phs in (ground_truth_phonemes or [])]

    m = len(words)
    n = len(flat)
    if m == 0:
        return []
    if n == 0:
        return [[] for _ in words]

    total_expected = sum(len(w) for w in words) or 1
    ratio = n / total_expected

    # Longest segment any single word may absorb. Scaling by the length ratio
    # guarantees sum(max_len) >= n, so full coverage is always reachable.
    max_len = [
        min(n, max(_SEGMENT_SLACK, int(len(w) * max(1.0, ratio)) + _SEGMENT_SLACK))
        for w in words
    ]

    # dp[i][j]: best accumulated cost of covering the first i expected words
    # with flat[:j], as the triple
    #     (scaled_edit_cost, imperfect_word_count, -asr_agreed_skips)
    # compared lexicographically:
    #   1. minimise total phoneme edit distance -- the acoustic evidence;
    #   2. on an exact tie, prefer the reading that blames FEWER words. This is
    #      what makes a skipped word register as one skipped word instead of
    #      smearing a small error across two or three neighbours, which is the
    #      most common way the current pipeline misdiagnoses a child;
    #   3. still tied, prefer the reading that agrees with the ASR about which
    #      words were skipped.
    # Putting the ASR last is what keeps it a SECONDARY signal: it is consulted
    # only when the acoustics are genuinely ambiguous, and no number of ASR
    # hints can outweigh a single phoneme of real evidence.
    dp: list[list] = [[_UNREACHABLE] * (n + 1) for _ in range(m + 1)]
    # key[i][j]: full tie-break key of the winning candidate for dp[i][j].
    key: list[list] = [[None] * (n + 1) for _ in range(m + 1)]
    # back[i][j]: the split point k, i.e. word i took flat[k:j].
    back: list[list[int]] = [[-1] * (n + 1) for _ in range(m + 1)]

    dp[0][0] = (0, 0, 0)
    key[0][0] = (0, 0, 0, 0, 0)

    for i in range(1, m + 1):
        gt_phs = words[i - 1]
        g = len(gt_phs)
        limit = max_len[i - 1]
        skip_cost = _COST_SCALE * g
        # -1 because the tuple is minimised: agreeing with the ASR is preferred.
        skip_agrees = -1 if (i - 1) in skip_hints else 0

        row_prev = dp[i - 1]
        row_cur = dp[i]
        key_cur = key[i]
        back_cur = back[i]

        for k in range(0, n + 1):
            base = row_prev[k]
            if base is _UNREACHABLE:
                continue
            base_cost, base_bad, base_agree = base

            # --- empty segment: this word was skipped -------------------- #
            _relax(
                row_cur, key_cur, back_cur, k, k,
                base_cost + skip_cost, base_bad + (1 if g else 0),
                base_agree + skip_agrees, 0, g,
            )

            # --- non-empty segments, extending one phoneme at a time ----- #
            # ``col`` is the edit-distance column between gt_phs and
            # flat[k:j]; extending j by one costs O(g) instead of O(g * len).
            col = list(range(g + 1))
            upper = min(n, k + limit)
            for j in range(k + 1, upper + 1):
                p = flat[j - 1]
                new = [col[0] + 1] + [0] * g
                for t in range(1, g + 1):
                    new[t] = min(
                        col[t - 1] + (0 if gt_phs[t - 1] == p else 1),  # sub/match
                        col[t] + 1,                                    # deletion
                        new[t - 1] + 1,                                # insertion
                    )
                col = new
                edits = col[g]
                _relax(
                    row_cur, key_cur, back_cur, k, j,
                    base_cost + edits * _COST_SCALE, base_bad + (1 if edits else 0),
                    base_agree, j - k, g,
                )

    if dp[m][n] is _UNREACHABLE:
        # Should be unreachable by construction; keep a deterministic fallback
        # rather than raising inside the analysis pipeline.
        return _proportional_segments(flat, words)

    segments: list[list[str]] = [[] for _ in range(m)]
    j = n
    for i in range(m, 0, -1):
        k = back[i][j]
        if k < 0:
            k = j
        segments[i - 1] = flat[k:j]
        j = k

    return segments


def _relax(
    row_cur, key_cur, back_cur,
    k: int, j: int, cost: int, bad_words: int, agree: int, seg_len: int, g: int,
) -> None:
    """
    Record a candidate for dp[i][j] if it beats the incumbent.

    Tie-break key is ``(cost, bad_words, agree, |seg_len - expected_len|, k)``:
    cheapest total edit distance first, then the reading that blames the fewest
    words, then agreement with the ASR about skipped words, then the segment
    length closest to what the word should be, then the earliest split point.
    Every component is an integer, so the ordering is total and the result is
    fully deterministic.
    """
    candidate = (cost, bad_words, agree, abs(seg_len - g), k)
    incumbent = key_cur[j]
    if incumbent is None or candidate < incumbent:
        key_cur[j] = candidate
        row_cur[j] = (cost, bad_words, agree)
        back_cur[j] = k


def _proportional_segments(flat: list[str], words: list[list[str]]) -> list[list[str]]:
    """Deterministic last-resort split, proportional to expected word lengths."""
    total_expected = sum(len(w) for w in words) or 1
    segments = []
    start = 0
    for idx, w in enumerate(words):
        if idx == len(words) - 1:
            end = len(flat)
        else:
            end = min(len(flat), start + int(round(len(flat) * len(w) / total_expected)))
        segments.append(flat[start:end])
        start = max(start, end)
    return segments


# --------------------------------------------------------------------------- #
# Result construction (matches _process_word_alignment's contract exactly)
# --------------------------------------------------------------------------- #


def _phoneme_errors(gt_phonemes: list[str], pred_phonemes: list[str]):
    """Return ``(missed, added, substituted)`` for one word."""
    missed, added, substituted = [], [], []
    for pop, gph, pph in align_sequences(gt_phonemes, pred_phonemes):
        if pop == 'deletion':
            missed.append(gph)
        elif pop == 'insertion':
            added.append(pph)
        elif pop == 'substitution':
            substituted.append((gph, pph))
    return missed, added, substituted


def _insertion_record(pred_word: str) -> dict:
    """An ASR word with no counterpart in the sentence the child was asked to read."""
    return {
        "type": "insertion",
        "predicted_word": pred_word,
        "ground_truth_word": "",
        "phonemes": [],
        "ground_truth_phonemes": [],
        "expected_phonemes": [],
        "actual_phonemes": [],
        "per": 0.0,   # insertion is not a mispronunciation of an expected word
        "missed": [],
        "added": [],
        "substituted": [],
        "total_phonemes": 0,
        "total_errors": 0,
        "error": "Extra word predicted.",
    }


def _deletion_record(gt_word: str, gt_phonemes: list[str]) -> dict:
    """An expected word the child did not read at all."""
    gt_phonemes = list(gt_phonemes)
    return {
        "type": "deletion",
        "predicted_word": "",
        "ground_truth_word": gt_word,
        "phonemes": [],
        "ground_truth_phonemes": gt_phonemes,
        "expected_phonemes": list(gt_phonemes),
        "actual_phonemes": [],
        "per": 1.0,
        "missed": list(gt_phonemes),   # every phoneme in the word was missed
        "added": [],
        "substituted": [],
        "total_phonemes": len(gt_phonemes),
        "total_errors": len(gt_phonemes),
        "error": "Word missing in prediction.",
    }


def align_to_ground_truth(
    flat_phonemes: list[str],
    ground_truth_phonemes: list[tuple[str, list[str]]],
    predicted_words: list[str] | None = None,
) -> list[dict]:
    """
    Ground-truth-anchored replacement for
    ``align_phonemes_to_words`` + ``_process_word_alignment``.

    Args:
        flat_phonemes: the flattened acoustic phoneme stream.
        ground_truth_phonemes: ``[(word, [phonemes]), ...]`` for the sentence
            the child was asked to read.
        predicted_words: the ASR word list. Optional, and used only as a
            secondary signal (skip hints, insertion records, display labels).

    Returns:
        The same ``list[dict]`` shape ``_process_word_alignment`` returns, with
        one record per expected word (in sentence order) plus ``insertion``
        records for ASR words that are not in the sentence.

    Notes:
        * ``type`` is ``match`` when the word was read with zero phoneme errors
          and ``substitution`` otherwise. Downstream
          (``SpeechProblemClassifier``) treats the two identically; the
          distinction is now driven by the acoustics rather than by whether the
          ASR happened to emit the same spelling.
        * ``predicted_word`` is the ASR word matched to this slot when there is
          one, otherwise the expected word.
    """
    gtp = [(word, list(phs or [])) for word, phs in (ground_truth_phonemes or [])]
    if not gtp:
        return []

    gt_words = [word for word, _ in gtp]
    asr_words = [str(w) for w in (predicted_words or []) if w]

    skip_hints, pred_labels, insertions = derive_asr_hints(gt_words, asr_words)
    segments = segment_phonemes_by_ground_truth(flat_phonemes, gtp, skip_hints)

    results: list[dict] = []
    for idx, (gt_word, gt_phs) in enumerate(gtp):
        for extra in insertions.get(idx, ()):
            results.append(_insertion_record(extra))

        segment = segments[idx] if idx < len(segments) else []

        if not segment:
            # Word skipped entirely. Scoring it as fully missed here is what
            # keeps every later word aligned to its own audio.
            results.append(_deletion_record(gt_word, gt_phs))
            continue

        missed, added, substituted = _phoneme_errors(gt_phs, segment)
        total_errors = len(missed) + len(added) + len(substituted)
        per = total_errors / max(len(gt_phs), 1)

        results.append({
            "type": "match" if total_errors == 0 else "substitution",
            "predicted_word": pred_labels.get(idx, gt_word),
            "ground_truth_word": gt_word,
            "phonemes": list(segment),
            "ground_truth_phonemes": list(gt_phs),
            "expected_phonemes": list(gt_phs),
            "actual_phonemes": list(segment),
            "per": round(per, 4),
            "missed": missed,
            "added": added,
            "substituted": substituted,
            "total_phonemes": len(gt_phs),
            "total_errors": total_errors,
        })

    for extra in insertions.get(len(gtp), ()):
        results.append(_insertion_record(extra))

    return results
