# Feedback quality

## Goal

Make the spoken and written feedback after a reading correct, short and useful
for a 5 to 7 year old who is learning to decode. Today the local formatter
(`backend/core/phoneme_feedback_formatter.py`) often teaches the wrong phonics
rule, so the first job is to stop that. The second is to make the message
itself better.

## What is wrong today

Running `generate_feedback` on real `grapheme_to_phoneme` output for common
words gives these messages.

| Word  | Feedback today                                                                 |
|-------|--------------------------------------------------------------------------------|
| see   | "the letters 'ee' make the 'short i' sound"                                    |
| rain  | "the letters 'ai' make the 'eh' sound", then a tip that 'ai' says long a       |
| night | "Watch the 'short a' sound in 'night'."                                        |
| cow   | "Watch the 'short a' sound in 'cow'."                                          |
| boy   | "Watch the 'aw' sound in 'boy'."                                               |
| book  | "the letters 'oo' make the 'short oo' sound", then a tip about 'food' and 'moon' |
| think | "the letters 'th' make the 'th' sound", then a mouth-position tip               |
| the   | "Watch the 'uh' sound in 'the'."                                               |
| (skipped "jumped") | "the letters 'j' make the 'j' sound"                                |

The causes are below.

- eng_to_ipa and the TIMIT model write the long vowels as two symbols
  (`e ɪ`, `a ɪ`, `o ʊ`, `a ʊ`, `ɔ ɪ`), and use a bare `i` for the long e in
  "see". The jigsaw view already handles both (`frontend/src/lib/soundTiles.ts`
  and `phonemeLabels.ts`). The formatter does not, so it names half of a vowel,
  and its demo audio plays that wrong sound too.
- Letters are found by a plain substring search with some wrong entries (`tch`
  is listed as a spelling of th).
- When the letters and the sound have the same name, the message repeats itself.
- A skipped word is treated as a misread of its first sound.
- Schwa slips, which are mostly model noise, can become the focus.
- The tips describe mouth position, which is speech therapy advice and not what
  a child who is learning to read usually needs.
- Every good reading gets the same "Great job!".

## Decisions

- Feedback never claims what the child said. It models the right word and
  points at its letters, so a model mishearing can't tell a child they said
  something they didn't.
- Mouth-position tips are dropped. Where the word has a letter pattern worth
  teaching, the feedback gives a short letter-sound rule. Otherwise it models
  the word.
- Feedback stays local and instant. GPT still writes only the next sentence.
- Word and sentence thresholds (PER 0.4 per word, 0.2 per sentence) stay as
  they are. Tuning them belongs with the speechocean benchmark work.

## What the child hears

Each message is at most two short sentences. Text and audio use the same words,
except that the text names a sound ("the long e sound") where the audio plays
it. Corrective messages end in the audio by saying the word once more, slowly.

| Kind       | When                                                       | Text                                                                                   | Audio adds                     |
|------------|------------------------------------------------------------|----------------------------------------------------------------------------------------|--------------------------------|
| `praise`   | nothing worth correcting                                   | "You read 'through' just right!" or a line from the praise pool                        | nothing                        |
| `skipped`  | the chosen word was skipped                                | "Remember to read every word. This one says 'jumped'."                                 | 'jumped', slowly               |
| `pattern`  | a vowel, or a consonant whose letters have another name    | "Almost! Let's try 'tree'. The letters 'ee' make the long e sound."                    | plays ē, then 'tree' slowly    |
| `pattern` (silent e) | the vowel is spelled with a silent e             | "Almost! Let's try 'cake'. The 'a' with a silent e at the end makes the long a sound." | plays ā, then 'cake' slowly    |
| `position` | a consonant whose letters share its name (t, th, sh, r)    | "Almost! Let's try 'cat'. Say the t sound at the end."                                 | plays t, then 'cat' slowly     |
| `listen`   | the word is mostly wrong, irregular, or has no matching letters | "Good try! Listen, then you try 'said'."                                          | 'said', slowly                 |

- One letter is "The letter 'a' makes…", more than one is "The letters 'ee'
  make…".
- The position is "at the start" for the word's first sound, "at the end" for
  its last, and "in the middle" otherwise. Positions count the word's expected
  sounds after joining two-symbol vowels.
- The opener for `pattern` and `position` is "Almost!" or "So close!" when the
  sentence PER is 0.3 or less, and "Good try!" or "Nice try!" otherwise. `listen`
  always opens with "Good try!". `skipped` has no opener.
- The praise pool is "Great job!", "Great reading!", "You read every word!" and
  "Nice, smooth reading!".
- Pool lines are picked from a hash of the sentence text. Tests stay stable and
  different sentences get different lines.
- Specific praise names the cleanly read word with the most sounds, if it has at
  least 4 sounds or one of its sounds is spelled with more than one letter.
  Otherwise praise comes from the pool. A cleanly read word has no ops other
  than `match`.

## Picking the word and the sound

1. For each word, read its `phoneme_alignment` and join two-symbol vowels with
   `merge_diphthongs` (a port of `mergeDiphthongs` in `soundTiles.ts`).
2. A word's real errors are its `substitution` and `deletion` ops, not counting
   schwa (`ə`). Added sounds and extra words still count toward PER, so they can
   stop praise, but they never become the focus, since that would mean claiming
   what the child added.
3. Candidates are words whose PER in the analysis is at least 0.4, with at
   least one real error, plus skipped words (`type == "deletion"`).
4. Rank candidates by real errors (most first), then PER (highest first), then
   position in the sentence (earliest first). A skipped word counts all its
   sounds as errors, so it usually wins. This is the same order as today.
5. If there is no candidate, the message is `praise` when the sentence PER is
   0.2 or less. Above 0.2, use the word with the most real errors in the whole
   sentence. If no word has a real error, the message is `praise`.
6. For the chosen word:
   - skipped gives `skipped`
   - real errors making up at least 2/3 of its expected sounds (after
     joining) give `listen`, since it is more useful to model the whole word
     than to teach one sound
   - an irregular word gives `listen`
   - otherwise the focus sound is its first real error in reading order. No
     matching letters gives `listen`. A vowel, or a consonant whose letters have
     a different name from the sound (after treating a doubled letter as one),
     gives `pattern`. Otherwise it gives `position`.

## Sound names

A new module, `backend/core/phoneme_labels.py`, holds the sound names and
example words from `frontend/src/lib/phonemeLabels.ts`, the diphthong set from
`soundTiles.ts`, and `merge_diphthongs`. The formatter's `_IPA_TO_DISPLAY` is
removed.

There is one deliberate difference from the tiles. When the letter 'o' spells
the vowel in words like "hot" and "dog" (`ɑ` or `ɔ`), the spoken feedback calls
it "short o", the name phonics lessons use, not "ah" or "aw". Those words are
very common in early reading. The tiles keep their labels.

## Letter patterns

A new module, `backend/core/letter_patterns.py`, maps each sound (with
two-symbol vowels joined) to its common spellings, most specific first, and
finds which one a word uses. The main entries are below.

| Sound    | Spellings                                   |
|----------|---------------------------------------------|
| long a   | a…e, ai, ay, eigh, ey, ea, a                |
| long e   | ee, ea, ie, ey, final y, e…e, e             |
| long i   | igh, i…e, ie, y, i                          |
| long o   | o…e, oa, ow, oe, o                          |
| long oo  | oo, ew, ue, u…e, ou, o                      |
| short oo | oo, u                                       |
| ow       | ou, ow                                      |
| oy       | oi, oy                                      |
| short a  | a                                           |
| short e  | ea, e                                       |
| short i  | i, y                                        |
| short u  | u, o                                        |
| ah       | a, o (named short o when spelled o)         |
| aw       | aw, au, a, o (named short o when spelled o) |
| er       | er, ir, ur, or                              |
| th       | th                                          |
| sh       | sh, ti, ci                                  |
| ch       | tch, ch                                     |
| j        | dge, j, g before e/i/y                      |
| ng       | ng, n before k                              |
| f        | ph, gh, f                                   |
| k        | ck, ch, k, c                                |
| s        | c before e/i/y, s                           |
| z        | z, s                                        |
| zh       | s, ge                                       |
| t        | ed at the end, t                            |
| d        | ed at the end, d                            |
| n        | kn, gn, n                                   |
| r        | wr, r                                       |
| w        | wh, w                                       |

Every other consonant is spelled by its own letter, single or doubled.

The matcher follows these rules.

- The word's first sound must match at the start of the word, and its last
  sound must match at the end. A final silent e may follow it.
- `a…e`, `i…e`, `o…e`, `u…e` and `e…e` mean the vowel, one consonant, then a
  final e, optionally followed by s or d (cakes, baked).
- A short list of irregular words always gives `listen`, because letter rules
  mislead there. The list is said, was, of, one, two, you, they, are, were, do,
  to, some, come, have, give, does, what, who, could, would, should.

## Audio

- The whole word is no longer wrapped in a `<phoneme>` tag. Google's own
  pronunciation of a word is more reliable than our g2p IPA, and neither uses
  context, so the tag only adds risk.
- The sound demo keeps its `<phoneme>` tag, with consonants backed by a schwa as
  today. The demo table is fixed so bare `i` plays long e (`iː`), and the joined
  vowels play `eɪ`, `aɪ`, `oʊ`, `aʊ` and `ɔɪ`.
- Corrective messages end with `<break time="400ms"/><prosody rate="slow">word</prosody>`.
- Words are XML-escaped before they go into SSML.

## Data flow

- `generate_feedback(per_summary, pronunciation_data)` drops its
  `problem_summary` argument. Both call sites are in
  `routers/handlers/audio_processing_handler.py`.
- `FeedbackResult` gains `kind` (one of the five kinds above) and
  `focus_phoneme` (the joined sound, or `None` for `praise`, `skipped` and
  `listen`).
- The `feedback` event becomes `{"type": "feedback", "data": {"text", "ssml",
  "kind"}}` on both the signed-in and guest streams.

## Mascot praise

The mascot celebrates when the feedback text is exactly "Great job!"
(`isPraise` in `frontend/src/components/practice/companionMood.ts`). With a
praise pool that would stop most celebrations, so `isPraise` takes the kind as
well. It returns `kind === "praise"` when a kind is given and falls back to the
text match otherwise, so it still works with saved feedback and with a backend
that hasn't been deployed yet. `BasePractice`, `ChoiceStoryBasePractice` and
`TryPage` keep the kind from the `feedback` event next to the text and pass it
to `PracticeStage`.

## Next sentence

`BaseMode.get_next_sentence` gains `feedback: FeedbackResult | None = None`, and
the handler passes the result it already has. `story.py` and `choice_story.py`
accept it and ignore it. `unlimited.py` uses it as follows.

- `praise` sends an empty `phoneme_to_error_words` and `phoneme_error_counts`,
  so the prompt takes its existing no-errors path and writes a slightly harder
  sentence. Today it can say "Great job!" and then drill a slip it chose not to
  mention.
- A `focus_phoneme` becomes `recommended_focus_phoneme`, with its name and
  example word in the reasoning slot, e.g. `["eɪ", "the sound the feedback just
  taught, long a as in 'cake'"]`. No prompt change is needed.
- `skipped` and `listen` keep today's behaviour.

## Testing

- `tests/test_phoneme_feedback_formatter.py`, a table of cases whose expected
  sounds come from real `grapheme_to_phoneme` output, so the tests use the same
  symbols as production. Each case checks the exact text, the kind, and that
  the SSML parses as XML. Cases cover
  - every vowel name, including the joined ones (see, tree, rain, cake, night,
    kite, go, home, cow, boy, book, moon, cat, bed, sit, cup, hot, dog)
  - consonants by position (cat, think, ship) and consonants whose letters have
    another name (phone, duck)
  - a skipped word, a mostly wrong word and an irregular word (said)
  - a schwa-only slip, a slip below the thresholds, specific praise, and added
    sounds only
- Unit tests for `merge_diphthongs` and the letter matcher.
- A parity test that reads `phonemeLabels.ts` and `soundTiles.ts` and checks
  the Python tables match them exactly.
- Update `companionMood.test.ts` for the kind argument.
- Run the existing backend unit tests and the analysis tests. The regression
  harness does not cover feedback, so it should not move.
- Frontend `npm run lint` and `npm run build`.
- Render a handful of cases through Google TTS and listen to the sound demos and
  the slow word at the end.

## Docs

- Point the comment at the top of `phonemeLabels.ts` at
  `core/phoneme_labels.py` and the parity test.
- In `CLAUDE.md`, step 8 of the pipeline still says GPT writes the feedback. It
  should say the feedback is built locally and GPT writes only the next
  sentence, and step 9 should list the `feedback` event.

## Deploying

It might be worth deploying the backend before merging the frontend, as
`CLAUDE.md` suggests. The frontend's fallback means the other order also works,
just without celebrations for the new praise lines until the backend is live.

## Out of scope

- Detection thresholds and false alarms (the speechocean benchmark work).
- The jigsaw tiles.
- The validator's rough count of the target sound in a vowel-focused sentence.
  It only logs warnings.
