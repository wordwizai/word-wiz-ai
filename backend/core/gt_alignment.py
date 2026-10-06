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
     * the ASR word matched to each expected word is the ``predicted_word``
       label, and when it differs from the expected word it switches off edge
       forgiveness for that word (see 5). It can only take leniency away.
4. Is deterministic. All DP arithmetic is integer (costs are scaled by
   ``_COST_SCALE``) and every tie is broken by an explicit total ordering, so
   the same input always produces byte-identical output.
5. Scores each word against its closest valid pronunciation (word scoring
   v2). Segmentation uses the primary G2P phonemes, but a word is then scored
   against whichever CMUdict pronunciation its segment matches best ("to" read
   as tu is not an error just because G2P picked tɪ), and one inserted
   phoneme at each edge of its segment does not count. The segmenter has to
   hand every acoustic phoneme to some word, so a stray phoneme at a word
   boundary lands on one side or the other and says nothing about how that
   word was read. Longer edge runs and interior insertions still count, and
   nothing at the edges is forgiven when the ASR heard a different word in
   that slot ("sit" for "it"), because then the extra sounds are probably a
   reading miscue. Set ``WWAI_LEGACY_WORD_SCORING`` to go back to
   primary-only scoring with every insertion counted.

The returned value matches the existing contract of
``process_audio._process_word_alignment`` -- same keys, same types -- so
``analyze_results``, ``SpeechProblemClassifier``,
``phoneme_feedback_formatter`` and the frontend need no changes. Every record
also carries two extra keys: ``canonical_phonemes`` (the primary G2P
phonemes, which spoken feedback uses to model the word) and
``edge_insertions`` (the edge phonemes that were forgiven).

FEATURE FLAG
------------
``WWAI_GT_ANCHORED_ALIGNMENT`` -- defaults to ON. Set it to a falsy value
("0", "false", "no", "off") to go back to the legacy ASR-driven alignment.
"""

from __future__ import annotations

import os
import re

# --------------------------------------------------------------------------- #
# Feature flag
# --------------------------------------------------------------------------- #

GT_ANCHORED_FLAG = "WWAI_GT_ANCHORED_ALIGNMENT"

_TRUTHY = frozenset({"1", "true", "t", "yes", "y", "on"})
_FALSY = frozenset({"0", "false", "f", "no", "n", "off"})


def is_gt_anchored_enabled() -> bool:
    """
    True unless ``WWAI_GT_ANCHORED_ALIGNMENT`` is set to a falsy value.

    ON by default: the speechocean762 benchmark accepted it over the legacy
    ASR-driven alignment. An unset, empty or unrecognised value keeps the
    default; only an explicit "0" / "false" / "no" / "off" turns it off.

    Read at call time (not import time) so that it can be toggled in tests and
    so a deploy-time env change does not require a code reload.
    """
    return os.environ.get(GT_ANCHORED_FLAG, "").strip().lower() not in _FALSY


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
# torch via ``phoneme_extractor``. Keeping this module light (stdlib, plus a
# lazy G2P import for pronunciation variants) also keeps its unit tests fast.


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


# --------------------------------------------------------------------------- #
# Word scoring v2: closest valid pronunciation, edge insertions not counted
# --------------------------------------------------------------------------- #

LEGACY_WORD_SCORING_FLAG = "WWAI_LEGACY_WORD_SCORING"

#: Version of the word scoring code, stamped on ``analyze_results``'
#: ``per_summary`` so stored stats can be told apart across scoring changes.
#: 2 = word scoring v2 (closest CMUdict pronunciation, one forgiven edge
#: phoneme per side, the miscue guard). It marks the code release, not the
#: path one request took: the kill switches and the client-phoneme path still
#: produce pre-v2 numbers under it.
SCORING_VERSION = 2


def is_legacy_word_scoring() -> bool:
    """
    True when ``WWAI_LEGACY_WORD_SCORING`` is set to a truthy value.

    Kill switch for word scoring v2. When on, every word is scored against its
    primary G2P phonemes only and every inserted phoneme counts, exactly as
    before. Read at call time, like ``is_gt_anchored_enabled``.
    """
    return os.environ.get(LEGACY_WORD_SCORING_FLAG, "").strip().lower() in _TRUTHY


def _sentence_variants(gt_words: list[str]) -> dict[str, list[list[str]]]:
    """Every CMUdict pronunciation of each word, fetched in one lookup per sentence."""
    try:
        from .grapheme_to_phoneme import sentence_pronunciation_variants
        return sentence_pronunciation_variants(gt_words)
    except Exception:  # no variants is always a safe answer
        return {}


def _pronunciation_candidates(gt_phonemes: list[str], variants) -> list[list[str]]:
    """The primary G2P phonemes first, then every other CMUdict pronunciation."""
    candidates = [list(gt_phonemes)]
    for variant in variants or ():
        if list(variant) not in candidates:
            candidates.append(list(variant))
    return candidates


# (leading, trailing) phonemes to set aside, cheapest first. At most ONE phoneme
# is forgiven at each edge: that covers the stray boundary phoneme the
# segmenter has to hand to some word, while a longer run ("run" read as
# "running", a garbled segment containing the word) still counts.
_EDGE_TRIMS = ((0, 0), (1, 0), (0, 1), (1, 1))


def _counted_ops(
    expected: list[str], segment: list[str], forgive_edges: bool = True,
) -> tuple[int, list[tuple], list[str]]:
    """
    Align ``expected`` with ``segment``, forgiving at most one inserted
    phoneme at each edge.

    Returns ``(counted_errors, ops, edge_insertions)``. ``ops`` aligns
    ``expected`` with the segment minus the forgiven edge phonemes,
    ``counted_errors`` is the number of non-match ops in it, and
    ``edge_insertions`` lists the forgiven phonemes in segment order.
    Interior insertions, substitutions and deletions all still count.

    Forgiving the first phoneme is the same as aligning the rest of the
    segment, so each of the four trims in ``_EDGE_TRIMS`` is aligned and the
    one with the fewest counted errors wins. A trim is used only when it
    strictly lowers the count, so a wrong last phoneme stays a substitution
    instead of turning into a missed phoneme plus a free edge insertion.
    Trimming the segment, rather than the ops of one alignment, also treats a
    doubled first phoneme and a doubled last one alike.

    With ``forgive_edges`` False nothing is set aside, and the count is the
    plain edit distance the pre-v2 scoring used.
    """
    trims = _EDGE_TRIMS if forgive_edges else _EDGE_TRIMS[:1]
    n = len(segment)

    best = None
    for lead, trail in trims:
        if lead + trail > n:
            continue
        ops = align_sequences(expected, segment[lead:n - trail])
        errors = sum(1 for op, _gt, _pred in ops if op != 'match')
        if best is None or errors < best[0]:
            best = (errors, ops, list(segment[:lead]) + list(segment[n - trail:]))
    return best


def _score_word(
    gt_phonemes: list[str], segment: list[str], legacy: bool,
    variants=(), forgive_edges: bool = True,
):
    """
    Return ``(expected, missed, added, substituted, edge_insertions)`` for one
    non-empty segment.

    v2: the primary phonemes and every pronunciation in ``variants`` are
    candidates. Each candidate is aligned with the segment, at most one
    edge insertion per side is set aside (none when ``forgive_edges`` is
    False), and the candidate with the fewest counted errors wins (the earliest
    on a tie, so the primary wins ties). The error lists come from the
    winner's alignment, so forgiven edge phonemes never reach ``added``; they
    are returned as ``edge_insertions`` instead.
    """
    if legacy:
        return (list(gt_phonemes),) + _phoneme_errors(gt_phonemes, segment) + ([],)

    best = None
    for candidate in _pronunciation_candidates(gt_phonemes, variants):
        errors, ops, edges = _counted_ops(candidate, segment, forgive_edges)
        if best is None or errors < best[0]:
            best = (errors, candidate, ops, edges)
    _errors, expected, ops, edges = best

    missed = [gph for op, gph, _pph in ops if op == 'deletion']
    added = [pph for op, _gph, pph in ops if op == 'insertion']
    substituted = [(gph, pph) for op, gph, pph in ops if op == 'substitution']
    return list(expected), missed, added, substituted, list(edges)


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
        "canonical_phonemes": [],
        "edge_insertions": [],
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
        "canonical_phonemes": list(gt_phonemes),
        "edge_insertions": [],
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
        * Word scoring v2 (off under ``WWAI_LEGACY_WORD_SCORING``): a read word
          is scored against its closest CMUdict pronunciation, which becomes
          its ``ground_truth_phonemes`` / ``expected_phonemes`` and sets
          ``total_phonemes``. One phoneme inserted at each edge of its segment
          stays in ``phonemes`` / ``actual_phonemes`` but is left out of
          ``added``, ``total_errors`` and ``per``. Further edge insertions and
          interior insertions still count, so ``per`` can still exceed 1.0.
          When the ASR heard a different word in the slot, no edge phoneme is
          forgiven (the miscue guard).
        * Every record also has ``canonical_phonemes`` (the primary G2P
          phonemes, ``[]`` on an insertion record) and ``edge_insertions``
          (the forgiven edge phonemes, in segment order; always ``[]`` on
          deletion and insertion records and under the kill switch).
    """
    gtp = [(word, list(phs or [])) for word, phs in (ground_truth_phonemes or [])]
    if not gtp:
        return []

    gt_words = [word for word, _ in gtp]
    asr_words = [str(w) for w in (predicted_words or []) if w]
    legacy_scoring = is_legacy_word_scoring()

    skip_hints, pred_labels, insertions = derive_asr_hints(gt_words, asr_words)
    segments = segment_phonemes_by_ground_truth(flat_phonemes, gtp, skip_hints)
    # One dictionary lookup for the whole sentence, before the scoring loop.
    variants = {} if legacy_scoring else _sentence_variants(gt_words)

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

        # Miscue guard. When the ASR heard a different word in this slot
        # ("sit" for "it", "running" for "run"), extra sounds at the word's
        # edge are probably that other word, not segmentation noise, so none
        # are forgiven. This only takes leniency away: the count is never
        # higher than the pre-v2 scoring's.
        asr_heard_other_word = (
            idx in pred_labels
            and _normalize_word(pred_labels[idx]) != _normalize_word(gt_word)
        )
        expected, missed, added, substituted, edge_insertions = _score_word(
            gt_phs, segment, legacy_scoring,
            variants=variants.get(gt_word, ()),
            forgive_edges=not asr_heard_other_word,
        )
        total_errors = len(missed) + len(added) + len(substituted)
        per = total_errors / max(len(expected), 1)

        results.append({
            "type": "match" if total_errors == 0 else "substitution",
            "predicted_word": pred_labels.get(idx, gt_word),
            "ground_truth_word": gt_word,
            "phonemes": list(segment),
            "ground_truth_phonemes": list(expected),
            "expected_phonemes": list(expected),
            "actual_phonemes": list(segment),
            "per": round(per, 4),
            "missed": missed,
            "added": added,
            "substituted": substituted,
            "total_phonemes": len(expected),
            "total_errors": total_errors,
            "canonical_phonemes": list(gt_phs),
            "edge_insertions": edge_insertions,
        })

    for extra in insertions.get(len(gtp), ()):
        results.append(_insertion_record(extra))

    return results
