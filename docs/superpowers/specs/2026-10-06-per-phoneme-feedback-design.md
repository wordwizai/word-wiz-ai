# Per-phoneme feedback in the jigsaw view

## Goal

After a reading, pressing the jigsaw (Puzzle) button in practice mode should show
each word split into its sounds, with each sound marked as read correctly,
read as a different sound, left out, or added. That is the same
match/substitution/deletion/insertion logic the backend already applies to
whole words, applied to the phonemes inside each word.

## Why the backend needs a new field

Every word row of the analysis dataframe already reaches the frontend with
`missed`, `added` and `substituted`. Those are unordered buckets, so they cannot
say *where* in the word an error happened. The ordered edit-distance ops that
produce them are computed and then thrown away. This change keeps them.

## Backend

### Field

Each word record gets `phoneme_alignment`, an ordered list:

```json
[
  {"type": "match",        "expected": "k", "actual": "k"},
  {"type": "substitution", "expected": "æ", "actual": "ɛ"},
  {"type": "deletion",     "expected": "t", "actual": null},
  {"type": "insertion",    "expected": null, "actual": "s"}
]
```

`type` uses the four names the word-level `type` column already uses.

### Where it is built

- `core/gt_alignment.py` gets a helper, `phoneme_alignment_records(ops)`, that
  turns `align_sequences` output into the list above. That module is stdlib only,
  so `process_audio` can import it without a cycle.
- `process_audio._process_word_alignment` (the default path, also used by the
  client-phoneme path) builds the field from the `phoneme_ops` it already
  computes. Matched and substituted words get the full list, skipped words get
  one `deletion` per expected phoneme, and extra words get one `insertion` per
  predicted phoneme.
- `gt_alignment.align_to_ground_truth` (behind `WWAI_GT_ANCHORED_ALIGNMENT`)
  does the same. `_phoneme_errors` is reworked to share one op list with the new
  field, so `missed`/`added`/`substituted` and `phoneme_alignment` always agree.
  Its extra-word records carry no phonemes, so their list is `[]`.

### Invariant

For every record, the `deletion` entries of `phoneme_alignment` are exactly
`missed` (in order), the `insertion` entries are exactly `added`, and the
`substitution` entries are exactly `substituted`. For the expected words that
means the non-`match` count equals `total_errors`, so the tile colors never
disagree with the PER that colors the whole word. (Extra-word records keep
`total_errors` at 0 as they do today, so the count rule does not apply to them.)

### What else sees it

- The `analysis` event already sends `pronunciation_dataframe.to_dict()`, so the
  field reaches the client with no handler change.
- GPT prompts build their own summaries and never include the dataframe, so
  prompt size is unchanged.
- Stored feedback entries keep the dataframe, so rows grow slightly. Older rows
  simply lack the field.

## Frontend

### Types and data flow

- `practice/types.ts`: `pronunciation_dataframe.phoneme_alignment?:
  Record<number, PhonemeOp[] | null>`, with
  `PhonemeOp = { type: "match" | "substitution" | "deletion" | "insertion";
  expected: string | null; actual: string | null }`.
- `WordBadgeRow` looks up each word's row (it already has `analysisIdx`) and
  passes the list to `WordBadge` as `phonemeAlignment`.

### When sound tiles show

`WordBadge` shows sound tiles when the jigsaw is on, the word has a non-empty
`phonemeAlignment`, and it is not an extra (inserted) word. Otherwise it keeps
today's behaviour (letter chunks with the jigsaw on, the plain word with it off).
In particular, before the first reading the jigsaw still shows letter chunks.

### Tile labels

The label comes from `lib/phonemeLabels.ts`, shortened to fit a tile:

- "short x" → `x`
- "long x" → `x` with a macron (`ā ē ī ō`), the mark phonics teaching uses,
  except "long oo" → `oo`
- everything else as written (`th`, `sh`, `ch`, `ng`, `ah`, `aw`, `er`, `oo`,
  `ow`, `oy`, `uh`, consonants)
- an IPA symbol with no label → the symbol itself

Substitution and deletion tiles are labelled with the expected sound. Insertion
tiles are labelled with the sound that was added.

### Vowels written as two symbols

eng_to_ipa and the TIMIT model both write the diphthongs as two symbols
(`e ɪ`, `a ɪ`, `o ʊ`, `a ʊ`, `ɔ ɪ`), and the backend scores them as two
phonemes. A child hears one sound, so `lib/soundTiles.ts` joins each adjacent
pair into one tile before drawing (`ā ī ō ow oy`). Scoring is unchanged. If the
two halves have the same result the tile keeps it. If they differ, half the
vowel was wrong, so the tile shows "said a different sound". An added sound
never joins an expected one.

Both sources also use a bare `i` for the long e in "see" (ARPAbet `iy`), so
`phonemeLabels.ts` labels it long e (`ē`), not short i.

### Tile styles

In sound-tile mode the badge drops its PER color and goes neutral, and the tiles
carry the result. Each status changes shape as well as color:

| type         | look                                                      |
|--------------|-----------------------------------------------------------|
| match        | mint fill                                                 |
| substitution | pink fill, solid pink border                              |
| deletion     | no fill, dashed pink border, faded, struck through        |
| insertion    | smaller, no fill, dashed muted border, italic, muted text |

Tapping the badge still reads the word slowly. A button's own label hides its
children from screen readers, so the per-sound result is appended to the badge's
`aria-label` instead, e.g. "Hear "cat", almost. Sounds: k said right, short a
said a different sound, t left out".

## Testing

- Unit tests for `phoneme_alignment_records`.
- Tests for both alignment paths: a clean word, a substitution, a dropped
  phoneme, an added phoneme, a skipped word and an extra word, each checking the
  invariant above.
- Add `phoneme_alignment` to `CONTRACT_KEYS` in `tests/test_gt_anchored_alignment.py`.
- Run the existing backend unit tests and the analysis tests.
- Frontend `npm run lint` and `npm run build`, then render tiles in the browser
  from a sample analysis payload.

## Out of scope

- Mapping sounds back onto the spelled letters.
- Changing word-level scoring, PER or the spoken feedback.
