# Regression corpus

One folder per case. The harness discovers everything here automatically, plus the legacy
`backend/tests/system/test_case_*` folders (read-only — nothing is ever written back to
them).

## Layout

```
corpus/
  <case_id>/
    sentence.txt     REQUIRED  the text the child was asked to read, one line
    fixture.json     optional  recorded model output — makes the case run with NO models
    audio.wav        optional  16 kHz mono; only needed for `--with-models` runs
    meta.json        optional  {"tags": [...], "notes": "..."}
  _baselines/
    <case_id>.json             generated — the pinned expected output
```

`case_id` is just the folder name. Prefix real recordings with `case_` and keep the name
descriptive (`case_012_noisy_fan_hum`, not `case_012`).

## Why `fixture.json` matters

Downloading wav2vec2 and calling Deepgram costs money and needs network, and most
environments running these tests have neither. A `fixture.json` stores what the acoustic
models *said*, so everything downstream — the alignment, the regrouping heuristics, the
PER maths, all the tuned constants — runs in milliseconds, offline, deterministically.

```json
{
  "words": ["the", "cat", "sat"],
  "phonemes_by_word": [["ð","ə"], ["k","æ","t"], ["s","æ","t"]],
  "phonemes_flat": ["ð","ə","k","æ","t","s","æ","t"],
  "source": "recorded from tests/system/test_case_09 on 2026-09-08"
}
```

* `words` — what the word extractor heard, in order (Deepgram server-side, whisper-tiny
  client-side).
* `phonemes_by_word` — the phoneme stream **as the client groups it**. This is what the
  browser posts.
* `phonemes_flat` — optional. The raw ungrouped stream **as the server sees it** before
  `align_phonemes_to_words` regroups it. Defaults to the concatenation of
  `phonemes_by_word`. Supply it explicitly when the client's word boundaries differ from
  a plain concatenation — that difference is exactly what the path-agreement check exists
  to measure.

## Adding a case — the fast path (no models, ~1 minute)

1. `mkdir corpus/case_012_short_name`
2. Write `sentence.txt`.
3. Write `fixture.json` by hand, or copy the `words` / `phonemes` columns out of an
   existing `result.json`.
4. `python -m tests.regression.run_regression --update-baseline --case case_012_short_name`
5. Read the printed baseline. **If the numbers look wrong, that is a finding, not a
   formality** — write what you expected into `meta.json` before pinning it.

## Adding a case — from a real recording

1. Record with the existing recorder, which already writes the right shape:
   `python tests/record_test_case.py` → mode `system` → it creates
   `tests/system/test_case_NN/{sentence.txt,audio.wav}`.
2. Move (or copy) that folder into `corpus/` and rename it descriptively.
3. Generate the fixture once, with models, network and a Deepgram key available:
   ```
   WWAI_REGRESSION_USE_MODELS=1 PYTHONIOENCODING=utf-8 \
     venv/Scripts/python.exe -m tests.regression.run_regression \
     --with-models --case <case_id> --report ../scratch/live.json
   ```
   Copy `cases[0].model_backed.words` / `.phonemes` into `fixture.json`. From then on the
   case runs offline forever.
4. `--update-baseline --case <case_id>` to pin it.

Cases without a `fixture.json` are listed by `--list` but are **not** regression-checked.

## Growing toward 30–50 clips

Current corpus size is printed by `run_regression.py --list`. Seven cases is a smoke
test, not a regression suite. Aim for 30–50, and spend at least a third of them on
recordings that are supposed to go badly — the good-audio cases already agree with each
other, so they find almost nothing.

Suggested distribution:

| Count | Kind | Tag | What it protects |
|---|---|---|---|
| 10–15 | Clean reads, varied length (3–15 words) | `clean` | The scoring floor |
| 4–6 | Genuine child mispronunciations | `mispronounced` | That real errors stay detected |
| 3–5 | Background noise: TV, fan, siblings | `noisy` | Noise reduction and SNR handling |
| 2–3 | Clipped / too loud (mic peaking) | `clipped` | Preprocessing and validation |
| 2–3 | Near-silent or mic muted | `silent`, `expect-rejection` | That rejection is graceful and stable |
| 2–3 | Too short (< 0.3 s), cut off mid-word | `too-short`, `expect-rejection` | The length guards |
| 2–3 | Child reads the wrong sentence entirely | `wrong-sentence` | Word alignment under total mismatch |
| 2–3 | Proper nouns / out-of-vocabulary words | `oov`, `known-bug` | The eng_to_ipa OOV fallback |
| 2–3 | Long sentences that trigger chunking (> 8 s) | `chunking` | `chunk_audio_at_silence` and merging |
| 2–3 | Same audio recorded on client AND server | `path-parity` | The client/server divergence, for real |

That last row is the most valuable and the most work: capture the browser's
`client_phonemes` / `client_words` from a real session (they are in the WebSocket
`analyze_audio` payload) **and** the server's own extraction from the same clip. Put the
browser's grouping in `phonemes_by_word` and the server's flat stream in `phonemes_flat`.
That turns the path-agreement test from a structural check into a measurement of the
actual production gap.

Tag every case in `meta.json`. `--list` reports the tag histogram, so gaps in coverage
are visible without reading every folder.

## Cases that are supposed to fail

Tag them `expect-rejection`. The harness records the raised exception as
`{"error": "ValueError: ..."}` and pins that string, so "rejects this clip, with this
message, every time" becomes a regression target like any score. Do not delete a case
because it throws.

## Known-bug cases

`case_synth_03_oov_word` and `case_synth_04_ligature_mismatch` pin behaviour that is
currently **wrong** — a bad score caused by the ground-truth generator, not by the child.
They are tagged `known-bug`. When someone fixes the underlying bug these baselines are
*supposed* to move: re-pin them with `--update-baseline` and say so in the PR. Never widen
`WWAI_REGRESSION_PER_EPSILON` to make them quiet.
