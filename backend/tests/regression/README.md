# Scoring regression harness

The thing that tells an improvement from a regression.

Word Wiz AI's scoring is full of tuned constants — the Phase 3 `align_phonemes_to_words`
flexibility, length-ratio and confidence numbers most of all — and until now there were
exactly two end-to-end test cases and no pinned expectations, so nobody could safely
change any of them. This harness runs a corpus of cases through the pipeline and answers
three questions.

## The three assertions

| # | Assertion | What it catches |
|---|---|---|
| 1 | **Determinism** — same input twice, byte-identical analysis out | hidden state, dict/set ordering, unseeded randomness |
| 2 | **Path agreement** — the client-phoneme path and the server-extraction path score the same audio the same way | the biggest bug class in this codebase: the same clip scoring differently depending on which path ran |
| 3 | **Drift** — aggregate and per-case PER have not moved from a pinned baseline by more than an epsilon | any scoring change, intended or not |

Plus **model pinning** checks over `core/model_registry.py` (below).

## Running it

From `backend/`:

```bash
# the unit suite (this is the one to run in CI and before merging anything)
PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.regression.test_regression -v

# the human-readable report
PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m tests.regression.run_regression

# what is in the corpus
PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m tests.regression.run_regression --list

# re-pin expectations after an INTENDED scoring change
PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m tests.regression.run_regression --update-baseline
```

`PYTHONIOENCODING=utf-8` is not optional on Windows — the console is cp1252 and dies on
IPA characters.

Typical output:

```
case id                                    client   server    paths     base    drift  status
----------------------------------------------------------------------------------------------------
case_synth_01_clean                        0.0000   0.0000   0.0000   0.0000   0.0000  ok
case_synth_02_regroup_skew                 0.1429   0.0000   0.1429   0.1429   0.0000  ok
case_synth_03_oov_word                     0.1765   0.1765   0.0000   0.0000   0.0000  ok
case_synth_04_ligature_mismatch            0.6667   0.6667   0.0000   0.0000   0.0000  ok
case_synth_05_one_word_rejected          REJECTED REJECTED   0.0000   0.0000   0.0000  ok
system_test_case_02                        0.1143   0.1143   0.0000   0.0000   0.0000  ok
system_test_case_03                        0.1111   0.1111   0.0000   0.0000   0.0000  ok
```

`client` / `server` are the two paths' sentence PER, `paths` is the divergence between
them, `base` is the pinned divergence, `drift` is the move from baseline.

## Comparing two branches

The number to watch is `mean client sentence_per` on the last line, plus any case whose
status is not `ok`. Run the harness on each branch and diff:

```bash
PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m tests.regression.run_regression \
    --report ../scratch/branch-a.json
```

The JSON report has per-word PER deltas for every case, so "this change improved word
alignment but made vowel scoring worse" is answerable rather than a guess.

## No network, no models, no cost

By default nothing is downloaded and nothing is called. Cases carry a `fixture.json`
holding the recorded acoustic-model output, so the harness exercises everything
*downstream* of the models — which is where every tunable constant lives — offline and in
milliseconds. Model-backed runs are opt-in (`--with-models` /
`WWAI_REGRESSION_USE_MODELS=1`) and need network, weights and a paid Deepgram key.

## Skipping, not failing

Every check degrades to a skip when the environment cannot support it: no venv, no torch,
no fixtures, no frontend sources, no baselines. Verified: with the pipeline import forced
to fail, the suite reports `0 errors, 0 failures, 4 skipped` and the registry checks still
run. A suite that goes red for environmental reasons is a suite people learn to ignore,
and this one has to stay trustworthy.

## Configuration

| Env var | Default | Effect |
|---|---|---|
| `WWAI_REGRESSION_PER_EPSILON` | `0.02` | how far PER may move from baseline |
| `WWAI_REGRESSION_PATH_EPSILON` | `0.02` | how much worse client/server divergence may get |
| `WWAI_REGRESSION_STRICT_PATHS` | unset | demand *exact* client/server parity (the goal state) |
| `WWAI_REGRESSION_USE_MODELS` | unset | run the real acoustic models (network + cost) |
| `WWAI_REGRESSION_VERBOSE` | unset | stop swallowing the pipeline's `print()` noise |
| `WWAI_REQUIRE_MODEL_PINS` | unset | fail if any model in the registry is unpinned |

## Model pinning

`backend/core/model_registry.py` declares every model id and revision in one place, for
both backend and frontend. Every revision is currently `UNPINNED`, which means a push to
any of those HuggingFace repos changes everyone's scores with no deploy. To fix that:

```bash
PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m core.model_registry --resolve
```

Paste the printed SHAs into `_MODELS`, then `--check` to confirm and re-run this harness
to confirm scores did not move. `from_pretrained_kwargs()` returns `{}` while unpinned, so
wiring the registry into a loader is a no-op until a revision is actually declared.

The registry tests also assert that `Bobcat9/wav2vec2-timit-ipa-onnx` — loaded by **both**
the browser and the server — resolves to the same revision on both sides. A skew there
would reproduce the client/server scoring divergence on its own.

## Adding cases

See [`corpus/README.md`](corpus/README.md). Short version: a folder with `sentence.txt`
and a `fixture.json`, then `--update-baseline`. Target is 30–50 real clips including
deliberately bad ones; there are 7 today.

## What this harness does NOT cover

Read this before trusting a green run.

* **The acoustic models themselves.** Default runs replay recorded output. If wav2vec2 or
  Deepgram changes what it emits, only a `--with-models` run notices — and that is exactly
  what pinning revisions is for.
* **Audio preprocessing.** The server-path stubs ignore the audio, so the three separate
  preprocessing passes (`audio_processing_handler`, `process_audio_array`,
  `phoneme_extractor_onnx`) are not exercised at all.
* **The real browser.** "Client path" here means the server-side function that consumes
  client phonemes, not Transformers.js in a browser. A bug in the TypeScript extractor is
  invisible to this suite.
* **GPT feedback, TTS, and the WebSocket layer.** Deliberately out of scope: they cost
  money and are non-deterministic.
* **Audio chunking.** `use_chunking=False` on the stubbed path, and no corpus case is over
  8 seconds yet.
* **Corpus breadth.** Seven cases, five of them hand-written. The two real clips are both
  clean adult reads of easy sentences. This suite currently proves *stability*, not
  *quality* — it will tell you a change moved the numbers, not that the numbers were ever
  right.
