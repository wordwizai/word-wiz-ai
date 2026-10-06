# Per-phoneme feedback in the jigsaw view — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Return an ordered match/substitution/deletion/insertion list for the phonemes inside each word, and draw it as colored sound tiles when the jigsaw button is on after a reading.

**Architecture:** One stdlib-only helper in `core/gt_alignment.py` turns the existing `align_sequences` op list into `phoneme_alignment` records. Both word-alignment paths (`process_audio._process_word_alignment` and `gt_alignment.align_to_ground_truth`) attach it to every word record, and it reaches the client inside the existing `analysis` event. `WordBadge` renders sound tiles from it, using short labels from `lib/phonemeLabels.ts`.

**Tech Stack:** Python 3.11 + unittest (run with `backend/venv/Scripts/python.exe`, which has torch), React + TypeScript + Tailwind v4 + framer-motion.

Spec: `docs/superpowers/specs/2026-10-06-per-phoneme-feedback-design.md`

---

## Files

| File | Change |
|------|--------|
| `backend/core/gt_alignment.py` | Add `phoneme_alignment_records`; `_phoneme_errors` also returns the records; insertion/deletion records get the field |
| `backend/core/process_audio.py` | `_process_word_alignment` adds `phoneme_alignment` to all three record kinds |
| `backend/tests/test_phoneme_alignment.py` | New. Helper tests and tests for both paths |
| `backend/tests/test_gt_anchored_alignment.py` | Add `phoneme_alignment` to `CONTRACT_KEYS` |
| `frontend/src/components/practice/types.ts` | `PhonemeOp` type, optional `phoneme_alignment` column |
| `frontend/src/lib/phonemeLabels.ts` | `phonemeTileLabel` |
| `frontend/src/components/WordBadgeRow.tsx` | Pass each word's alignment to `WordBadge` |
| `frontend/src/components/WordBadge.tsx` | Render sound tiles |

Both backend paths must change in one commit: `test_keys_match_the_existing_implementation` compares their record keys.

---

### Task 1: The helper

**Files:**
- Modify: `backend/core/gt_alignment.py` (after `align_sequences`, ~line 156)
- Create: `backend/tests/test_phoneme_alignment.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_phoneme_alignment.py`:

```python
"""
Tests for the per-phoneme ``phoneme_alignment`` field on word records.

Run with (from the ``backend`` directory):

    PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.test_phoneme_alignment -v

No network, no models, no audio -- every fixture is hand written IPA.
"""

import os
import sys
import unittest

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from core.gt_alignment import align_sequences, phoneme_alignment_records  # noqa: E402


def op(type_, expected, actual):
    return {"type": type_, "expected": expected, "actual": actual}


class TestPhonemeAlignmentRecords(unittest.TestCase):

    def test_clean_word_is_all_matches(self):
        ops = align_sequences(['k', 'æ', 't'], ['k', 'æ', 't'])
        self.assertEqual(phoneme_alignment_records(ops), [
            op("match", "k", "k"), op("match", "æ", "æ"), op("match", "t", "t"),
        ])

    def test_substitution_keeps_its_position(self):
        ops = align_sequences(['k', 'æ', 't'], ['k', 'ɛ', 't'])
        self.assertEqual(phoneme_alignment_records(ops), [
            op("match", "k", "k"), op("substitution", "æ", "ɛ"), op("match", "t", "t"),
        ])

    def test_missed_phoneme_is_a_deletion_with_no_actual(self):
        ops = align_sequences(['k', 'æ', 't'], ['k', 't'])
        self.assertEqual(phoneme_alignment_records(ops), [
            op("match", "k", "k"), op("deletion", "æ", None), op("match", "t", "t"),
        ])

    def test_added_phoneme_is_an_insertion_with_no_expected(self):
        ops = align_sequences(['k', 'æ', 't'], ['k', 'æ', 't', 's'])
        self.assertEqual(phoneme_alignment_records(ops), [
            op("match", "k", "k"), op("match", "æ", "æ"), op("match", "t", "t"),
            op("insertion", None, "s"),
        ])

    def test_empty_inputs(self):
        self.assertEqual(phoneme_alignment_records(align_sequences([], [])), [])
        self.assertEqual(
            phoneme_alignment_records(align_sequences(['ð', 'ə'], [])),
            [op("deletion", "ð", None), op("deletion", "ə", None)],
        )
        self.assertEqual(
            phoneme_alignment_records(align_sequences([], ['b', 'ɪ'])),
            [op("insertion", None, "b"), op("insertion", None, "ɪ")],
        )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it and confirm it fails**

Run (from `backend`): `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.test_phoneme_alignment -v`
Expected: `ImportError: cannot import name 'phoneme_alignment_records'`

- [ ] **Step 3: Implement the helper**

In `backend/core/gt_alignment.py`, directly after `align_sequences`:

```python
def phoneme_alignment_records(ops: list[tuple]) -> list[dict]:
    """
    Turn ``align_sequences`` output into the ordered per-phoneme list the
    frontend draws as sound tiles, one ``{"type", "expected", "actual"}`` per op.

    ``type`` reuses the word-level names (match / substitution / deletion /
    insertion). ``expected`` is None for an added phoneme and ``actual`` is None
    for a missed one.
    """
    return [
        {"type": op, "expected": gt_item, "actual": pred_item}
        for op, gt_item, pred_item in ops
    ]
```

- [ ] **Step 4: Run the test and confirm it passes**

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.test_phoneme_alignment -v`
Expected: 5 tests, OK

(Commit together with Task 2.)

---

### Task 2: Attach the field in both alignment paths

**Files:**
- Modify: `backend/core/gt_alignment.py` (`_phoneme_errors`, `_insertion_record`, `_deletion_record`, `align_to_ground_truth`)
- Modify: `backend/core/process_audio.py` (imports; `_process_word_alignment` match/substitution, insertion and deletion branches)
- Modify: `backend/tests/test_gt_anchored_alignment.py:50-54`
- Test: `backend/tests/test_phoneme_alignment.py`

- [ ] **Step 1: Write the failing tests**

Append to `backend/tests/test_phoneme_alignment.py`, above the `if __name__` block:

```python
THE = ('the', ['ð', 'ə'])
CAT = ('cat', ['k', 'æ', 't'])
SAT = ('sat', ['s', 'æ', 't'])
ON = ('on', ['ɑ', 'n'])
MAT = ('mat', ['m', 'æ', 't'])
GT_SHORT = [THE, CAT, SAT]
GT_LONG = [THE, CAT, SAT, ON, THE, MAT]


class AlignmentAgreesMixin:

    def assert_alignment_agrees(self, record):
        """The ordered list holds exactly the errors the unordered buckets do."""
        pa = record["phoneme_alignment"]
        self.assertIsInstance(pa, list)
        for entry in pa:
            self.assertEqual(set(entry), {"type", "expected", "actual"})
            self.assertIn(entry["type"], {"match", "substitution", "deletion", "insertion"})
        self.assertEqual(
            [e["expected"] for e in pa if e["type"] == "deletion"], list(record["missed"]))
        self.assertEqual(
            [e["actual"] for e in pa if e["type"] == "insertion"], list(record["added"]))
        self.assertEqual(
            [(e["expected"], e["actual"]) for e in pa if e["type"] == "substitution"],
            [tuple(s) for s in record["substituted"]])
        if record["type"] != "insertion":
            self.assertEqual(
                sum(e["type"] != "match" for e in pa), record["total_errors"])


class TestLegacyPath(AlignmentAgreesMixin, unittest.TestCase):
    """process_audio._process_word_alignment, the default path."""

    def run_alignment(self, predicted_words, phoneme_predictions):
        from core.process_audio import _process_word_alignment
        return _process_word_alignment(
            ground_truth_words=[w for w, _ in GT_SHORT],
            ground_truth_phonemes=GT_SHORT,
            predicted_words=predicted_words,
            phoneme_predictions=phoneme_predictions,
        )

    def test_errors_inside_words_are_ordered(self):
        results = self.run_alignment(
            ['the', 'cat', 'sat'], [['ð', 'ə'], ['k', 'ɛ', 't'], ['s', 'æ']])
        cat, sat = results[1], results[2]
        self.assertEqual(cat["phoneme_alignment"], [
            op("match", "k", "k"), op("substitution", "æ", "ɛ"), op("match", "t", "t"),
        ])
        self.assertEqual(sat["phoneme_alignment"], [
            op("match", "s", "s"), op("match", "æ", "æ"), op("deletion", "t", None),
        ])
        for r in results:
            self.assert_alignment_agrees(r)

    def test_skipped_word_is_all_deletions(self):
        results = self.run_alignment(['the', 'sat'], [['ð', 'ə'], ['s', 'æ', 't']])
        cat = [r for r in results if r["ground_truth_word"] == "cat"][0]
        self.assertEqual(cat["type"], "deletion")
        self.assertEqual(cat["phoneme_alignment"], [
            op("deletion", "k", None), op("deletion", "æ", None), op("deletion", "t", None),
        ])
        for r in results:
            self.assert_alignment_agrees(r)

    def test_extra_word_is_all_insertions(self):
        results = self.run_alignment(
            ['the', 'big', 'cat', 'sat'],
            [['ð', 'ə'], ['b', 'ɪ', 'g'], ['k', 'æ', 't'], ['s', 'æ', 't']])
        big = [r for r in results if r["type"] == "insertion"][0]
        self.assertEqual(big["phoneme_alignment"], [
            op("insertion", None, "b"), op("insertion", None, "ɪ"), op("insertion", None, "g"),
        ])
        for r in results:
            self.assert_alignment_agrees(r)


class TestGroundTruthAnchoredPath(AlignmentAgreesMixin, unittest.TestCase):
    """gt_alignment.align_to_ground_truth, behind WWAI_GT_ANCHORED_ALIGNMENT."""

    def test_every_record_type_carries_an_agreeing_alignment(self):
        # "the cat sat on the mat" read as "the tat sat on the", plus a
        # spurious ASR word: all four record types in one result set.
        from core.gt_alignment import align_to_ground_truth
        flat = ['ð', 'ə', 't', 'æ', 't', 's', 'æ', 't', 'ɑ', 'n', 'ð', 'ə']
        asr = ['the', 'cat', 'sat', 'on', 'the', 'mat', 'now']
        results = align_to_ground_truth(flat, GT_LONG, asr)
        self.assertEqual(
            {r["type"] for r in results}, {"match", "substitution", "deletion", "insertion"})
        for r in results:
            self.assert_alignment_agrees(r)

        cat = [r for r in results if r["ground_truth_word"] == "cat"][0]
        self.assertEqual(cat["phoneme_alignment"], [
            op("substitution", "k", "t"), op("match", "æ", "æ"), op("match", "t", "t"),
        ])
        mat = [r for r in results if r["ground_truth_word"] == "mat"][0]
        self.assertEqual(mat["type"], "deletion")
        self.assertEqual(
            [e["type"] for e in mat["phoneme_alignment"]], ["deletion"] * 3)
        extra = [r for r in results if r["type"] == "insertion"][0]
        self.assertEqual(extra["phoneme_alignment"], [])
```

In `backend/tests/test_gt_anchored_alignment.py`, extend `CONTRACT_KEYS`:

```python
CONTRACT_KEYS = {
    "type", "predicted_word", "ground_truth_word", "phonemes",
    "ground_truth_phonemes", "expected_phonemes", "actual_phonemes",
    "per", "missed", "added", "substituted", "total_phonemes", "total_errors",
    "phoneme_alignment",
}
```

- [ ] **Step 2: Run them and confirm they fail**

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.test_phoneme_alignment tests.test_gt_anchored_alignment`
Expected: the four new path tests and `test_all_record_types_carry_the_contract_keys` fail with `KeyError: 'phoneme_alignment'` or a missing-keys assertion.

- [ ] **Step 3: Implement the GT-anchored path**

In `backend/core/gt_alignment.py`, replace `_phoneme_errors`:

```python
def _phoneme_errors(gt_phonemes: list[str], pred_phonemes: list[str]):
    """
    Return ``(missed, added, substituted, phoneme_alignment)`` for one word,
    all read off one op list so they always agree.
    """
    ops = align_sequences(gt_phonemes, pred_phonemes)
    missed, added, substituted = [], [], []
    for pop, gph, pph in ops:
        if pop == 'deletion':
            missed.append(gph)
        elif pop == 'insertion':
            added.append(pph)
        elif pop == 'substitution':
            substituted.append((gph, pph))
    return missed, added, substituted, phoneme_alignment_records(ops)
```

In `_insertion_record`, after `"substituted": [],` add:

```python
        "phoneme_alignment": [],
```

In `_deletion_record`, after `"substituted": [],` add:

```python
        "phoneme_alignment": phoneme_alignment_records(align_sequences(gt_phonemes, [])),
```

In `align_to_ground_truth`, change the unpacking and the record:

```python
        missed, added, substituted, phoneme_alignment = _phoneme_errors(gt_phs, segment)
```

and after `"substituted": substituted,` add:

```python
            "phoneme_alignment": phoneme_alignment,
```

- [ ] **Step 4: Implement the legacy path**

In `backend/core/process_audio.py`, add to the imports (after line 11, `from .audio_preprocessing import preprocess_audio`):

```python
from .gt_alignment import phoneme_alignment_records
```

In `_process_word_alignment`:

match/substitution branch, after `"substituted": substituted,`:

```python
                "phoneme_alignment": phoneme_alignment_records(phoneme_ops),
```

insertion branch, after `"substituted": [],`:

```python
                "phoneme_alignment": phoneme_alignment_records(
                    align_sequences([], list(pred_phonemes or []))
                ),
```

deletion branch, after `"substituted": [],`:

```python
                "phoneme_alignment": phoneme_alignment_records(
                    align_sequences(gt_phonemes_del, [])
                ),
```

- [ ] **Step 5: Run the tests and confirm they pass**

Run: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.test_phoneme_alignment tests.test_gt_anchored_alignment tests.test_client_realign_and_index_safety tests.test_none_ground_truth_word`
Expected: all OK (53 existing + 9 new = 62)

- [ ] **Step 6: Commit**

```bash
git add backend/core/gt_alignment.py backend/core/process_audio.py backend/tests/test_phoneme_alignment.py backend/tests/test_gt_anchored_alignment.py
git commit -m "Return the ordered per-phoneme result for each word"
```

---

### Task 3: Frontend type and tile labels

**Files:**
- Modify: `frontend/src/components/practice/types.ts:1-12`
- Modify: `frontend/src/lib/phonemeLabels.ts` (end of file)

- [ ] **Step 1: Add the type**

In `types.ts`, replace the `PronunciationAnalysis` block with:

```ts
// One sound inside a word, in reading order. The four names match the
// word-level `type`: read right, read as a different sound, left out, or
// added. `expected` is null for an added sound, `actual` for a left-out one.
export interface PhonemeOp {
  type: "match" | "substitution" | "deletion" | "insertion";
  expected: string | null;
  actual: string | null;
}

// What the backend's `analysis` event carries (a pandas frame as dicts keyed
// by row index).
export interface PronunciationAnalysis {
  pronunciation_dataframe: {
    type: Record<number, string>;
    per: Record<number, number | null>;
    ground_truth_word: Record<number, string | null>;
    predicted_word: Record<number, string | null>;
    // Absent on analyses saved before per-sound results existed.
    phoneme_alignment?: Record<number, PhonemeOp[] | null>;
  };
}
```

- [ ] **Step 2: Add the tile label**

Append to `phonemeLabels.ts`:

```ts
const MACRONS: Record<string, string> = { a: "ā", e: "ē", i: "ī", o: "ō" };

// A label short enough for a sound tile. "short a" becomes "a", "long a"
// becomes "ā" (the mark phonics lessons use) and "long oo" stays "oo".
// IPA with no label shows as itself.
export function phonemeTileLabel(ipa: string) {
  const letters = LABELS[ipa]?.letters;
  if (!letters) return ipa;
  if (letters.startsWith("short ")) return letters.slice("short ".length);
  if (letters.startsWith("long ")) {
    const vowel = letters.slice("long ".length);
    return MACRONS[vowel] ?? vowel;
  }
  return letters;
}
```

- [ ] **Step 3: Typecheck**

Run (from `frontend`): `npm run typecheck`
Expected: no errors

(Commit together with Task 4.)

---

### Task 4: Sound tiles in the word badge

**Files:**
- Modify: `frontend/src/components/WordBadgeRow.tsx`
- Modify: `frontend/src/components/WordBadge.tsx`

- [ ] **Step 1: Pass each word's alignment down**

In `WordBadgeRow.tsx`:
- import `PhonemeOp` alongside `PronunciationAnalysis`;
- add `phonemeAlignment: PhonemeOp[] | null;` to the `displayArray` item type;
- set `phonemeAlignment: null` in the no-analysis branch, the "not found" branch and the insertion branch;
- in the matched branch set
  ```ts
  phonemeAlignment:
    analysisData.pronunciation_dataframe.phoneme_alignment?.[analysisIdx] ?? null,
  ```
- pass `phonemeAlignment={item.phonemeAlignment ?? undefined}` to `WordBadge`.

- [ ] **Step 2: Render the tiles**

In `WordBadge.tsx`:

Imports:

```ts
import { phonemeLabel, phonemeTileLabel } from "@/lib/phonemeLabels";
import type { PhonemeOp } from "./practice/types";
```

After `SCORE_STYLE`:

```ts
// Each sound's result changes the tile's outline as well as its color, so it
// never relies on red versus green alone (same rule as the word badges).
const SOUND_STYLE: Record<PhonemeOp["type"], { className: string; status: string }> = {
  match: {
    className: "border-transparent bg-pastel-mint text-pastel-mint-foreground",
    status: "said right",
  },
  substitution: {
    className: "border-pastel-pink-foreground bg-pastel-pink text-pastel-pink-foreground",
    status: "said a different sound",
  },
  deletion: {
    className:
      "border-dashed border-pastel-pink-foreground/60 text-pastel-pink-foreground/70 line-through",
    status: "left out",
  },
  insertion: {
    className: "border-dashed border-border text-[0.6em] text-muted-foreground italic",
    status: "extra sound",
  },
};
```

Props: add

```ts
  // Per-sound result from the analysis. With splitIntoSounds on, the word
  // shows one tile per sound instead of letter chunks.
  phonemeAlignment?: PhonemeOp[];
```

and destructure `phonemeAlignment`.

In the body, replace the `score`/`scoreStyle` lines with:

```ts
  const showSounds = splitIntoSounds && !isInsertion && !!phonemeAlignment?.length;

  const score =
    showHighlighted && typeof analysisPer === "number"
      ? scoreFor(Math.max(0, Math.min(1, analysisPer)))
      : null;
  const scoreLabel = score ? SCORE_STYLE[score].label : "";
  // With sound tiles the tiles carry the result, so the badge stays neutral.
  const badgeScore = showSounds ? null : score;
  const { label: _badgeLabel, ...scoreStyle } = badgeScore
    ? SCORE_STYLE[badgeScore]
    : { label: "" };

  const sounds = showSounds
    ? phonemeAlignment!.map((op) => {
        const ipa = (op.type === "insertion" ? op.actual : op.expected) ?? "";
        return { ipa, label: phonemeTileLabel(ipa), ...SOUND_STYLE[op.type] };
      })
    : [];
  const soundSummary = sounds
    .map((s) => `${phonemeLabel(s.ipa)?.letters ?? s.ipa} ${s.status}`)
    .join(", ");

  const pieces = showSounds
    ? sounds.map((s) => ({ label: s.label, className: s.className }))
    : chunks.map((chunk) => ({
        label: chunk,
        className: cn(
          "border-transparent",
          badgeScore ? "bg-white/60 dark:bg-black/20" : "bg-secondary",
        ),
      }));
```

`aria-label`:

```ts
      aria-label={`Hear "${word}"${status ? `, ${status}` : ""}${
        soundSummary ? `. Sounds: ${soundSummary}` : ""
      }`}
```

Replace `!score && !isDeletion && !isInsertion &&` with `!badgeScore && !isDeletion && !isInsertion &&`, and the `transitionDelay` condition `score ?` with `badgeScore ?`.

Replace the `chunks.map(...)` inside `AnimatePresence` with `pieces.map((piece, i) => ...)`:
- `key={`${showSounds ? "sound" : "chunk"}-${piece.label}-${i}`}`
- `className={cn("rounded-lg border-2 px-1.5 md:px-2", piece.className)}`
- children `{piece.label}`
(The `initial`/`animate` props stay as they are.)

- [ ] **Step 3: Typecheck and lint**

Run (from `frontend`): `npm run typecheck && npx eslint src/components/WordBadge.tsx src/components/WordBadgeRow.tsx src/lib/phonemeLabels.ts src/components/practice/types.ts`
Expected: no errors. If eslint flags `_badgeLabel` as unused, destructure it away with a different pattern (e.g. pick the style fields) rather than disabling the rule.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/practice/types.ts frontend/src/lib/phonemeLabels.ts frontend/src/components/WordBadgeRow.tsx frontend/src/components/WordBadge.tsx
git commit -m "Show per-sound results as tiles when the jigsaw is on"
```

---

### Task 5: Verify end to end

- [ ] **Step 1: Backend suites**

From `backend`: `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest discover -s tests -p "test_*.py"` and `PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m tests.analysis.run_analysis_tests`. Compare against a run on the parent commit; no new failures.

- [ ] **Step 2: Real payload**

Run `_process_word_alignment` + `analyze_results` + `sanitize(df.to_dict())` + `json.dumps` on a sample sentence and confirm `phoneme_alignment` serializes (no NaN, `null` for missing sides).

- [ ] **Step 3: Frontend build**

From `frontend`: `npm run lint` and `npm run build:only`.

- [ ] **Step 4: Browser**

Start `wordwiz-backend-dev` and `wordwiz-app-dev`, sign in with the dev seed account, open a practice session, inject the Step 2 payload into the practice screen's `analysisData`/`showHighlightedWords` state, toggle the jigsaw, and screenshot. Check light and dark, and phone width.
