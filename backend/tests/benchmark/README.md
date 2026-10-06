# speechocean762 accuracy benchmark

This measures how well Word Wiz AI's word-level pronunciation scoring agrees with expert
human judgments on speechocean762, a public set of 5,000 English clips (children and
adults, 125 speakers in each half) with word and phone scores from five annotators. It
exists so that a change to scoring can be accepted or rejected on evidence.

The design and its reasoning are in
`docs/superpowers/specs/2026-10-05-speechocean-accuracy-benchmark-design.md`. This file
explains how to run the benchmark and how to read what it says. It does not contain results.
Those go in `BENCHMARK.md`.

All commands run from `backend/`. On Windows, set `PYTHONIOENCODING=utf-8` and use
`venv/Scripts/python.exe`, the same as the regression harness. The examples write
plain `python -m tests.benchmark.<command>`.

## What it measures, and why

The benchmark is precision-first. Word Wiz is for children learning to read, and telling a
child they misread a word they read correctly does more harm than missing a mistake. So the
headline number is word-level F0.5, which weights precision more heavily than recall,
measured at production's own cutoff. `run` reads `HIGH_PER_THRESHOLD` from
`core/phoneme_feedback_formatter.py` at run time, so a change to that constant is measured
at its new value.

What counts as a mistake follows the speechocean762 rubric, which was designed so that an
accent alone is never a mistake.

| Level | Real mistake | Not a mistake (flagging it is a false alarm) |
|---|---|---|
| Word | human score 0 to 6 (phones wrong, wrong word, or missed) | 7 to 10 (correct, or correct with an accent) |
| Phone | human score 0 after rounding (incorrect or missed) | 1 to 2 (heavy accent, or correct) |

Phone scores in the dataset are averages over annotators, so they are rounded half up before
the rule is applied. A strict phone variant that also counts a rounded 1 as a mistake is
reported as a secondary number.

Every metric is reported for all speakers, for children (age under 18) and for adults.

Numbers that are reported but not used to accept or reject a change are phone-level
precision, recall and F0.5 (lenient and strict), Pearson correlation with the human scores
at phone, word and sentence level, the rate at which production G2P disagrees with the
experts' canonical phones, the threshold that maximizes F0.5 on that half, and the F0.5 of
flagging every word, which is the number any threshold has to beat.

Messy cases are counted, not dropped.

- **Rejected clips.** When the pipeline raises (no speech detected, a quality gate, one-word
  text), the clip is recorded as rejected with its error type. Production would ask the child
  to try again, so its words are left out of word and phone scoring. The rejection rate is
  reported.
- **Misaligned clips.** When the pipeline's word records cannot be matched one to one with
  the dataset's scored words, the clip's words are left out too and the clip is counted.
- **Unscored rate.** Rejected plus misaligned clips, as a share of all clips. Clips in both
  groups drop out of every metric, so the acceptance rule watches this number.
- **Unexpected failures.** A failure that production would not show a child (an
  onnxruntime error, a harness bug) is reported as `unexpected:<ErrorName>` and is never
  treated as an ordinary rejection.

The benchmark covers the server path only. Production code runs unchanged, from the quality
gates and preprocessing through G2P, decoding, alignment and scoring. Only the wav2vec2 forward
pass and the Deepgram request are replaced with recorded outputs (see "How the cache stays
honest").

## Layout

| Module | What it does |
|---|---|
| `dataset.py` | Downloads and parses speechocean762, checks it, and writes the fixed clip subsets |
| `stage_cache.py` | Runs the two slow models once per clip and records what they returned |
| `replay.py` | Feeds the recorded outputs back into the real production code |
| `pipeline.py` | One clip through the production request path (gates, preprocessing, G2P, `process_audio_array`, `analyze_results`) |
| `run.py` | Scores a whole half and writes a results file |
| `scoring.py`, `metrics.py`, `phones.py` | Join outcomes with the labels, the pure metric functions, and ARPAbet-to-IPA phone mapping |
| `compare.py` | Paired comparison of two results files with the acceptance checks |
| `speed.py` | Serial latency and memory measurement |
| `sweep.py` | Measures each default-off accuracy flag, then combines them greedily |
| `human_reference.py` | How well one expert agrees with the other four |
| `common.py` | Paths, flag handling and cache naming |

Committed alongside the code are `subsets/` (the clip lists), `fixtures/` (a tiny dataset
for tests) and `test_runs.log`. Downloaded data and caches are gitignored. In `results/`, git
tracks the `*.summary.json` files, `baseline_dev.json`, `*_speed.json` and
`human_reference_*.json`, and ignores the other full results files.

## Setup

```bash
python -m tests.benchmark.dataset download         # ~520 MB from OpenSLR into tests/benchmark/data
python -m tests.benchmark.dataset check            # counts, audio readable, no speaker in both halves
python -m tests.benchmark.stage_cache --half dev   # record both models once per dev clip
python -m tests.benchmark.stage_cache --half test  # the same for the sealed half
```

- The download plus the extracted audio takes about 1.2 GB of disk. A cache is under
  100 MB per half. Both are gitignored.
- `dataset check` should end with 0 problems. It lists a few notes about typos in the
  dataset's own sentence text, which are expected. The harness uses the scored words as the
  sentence, so those typos do not reach the pipeline.
- `stage_cache` needs `DEEPGRAM_KEY` (in the environment or `backend/.env`) and calls
  Deepgram once per clip, so it uses real quota. It loads the model in every worker, which
  takes about 2 GB each. The default is 6 workers (`--workers` changes it), and a half takes
  roughly half an hour on a 16-thread machine.
- Recording is resumable. Existing entries are skipped, so after an interruption the same
  command carries on where it stopped.
- The model revision is pinned in `core/model_registry.py`. The first run downloads that exact
  revision from Hugging Face, and every cache records which revision made it.
- Building a test-half cache needs no unlock. It records what the models return and never
  scores anything.
- The clip lists in `subsets/` come from fixed seeds. `dataset make-subsets` rewrites them,
  but results made with a different list cannot be compared with older ones.

Deepgram sometimes fails for a reason that has nothing to do with the clip (a network
problem, an outage, a quota limit). Those clips are recorded as needing a retry, and the
build ends with a nonzero exit code and prints their ids. Running the build again with
`--retry-errors` records those clips again.

```bash
python -m tests.benchmark.stage_cache --half dev --retry-errors
```

Only an empty transcript that Deepgram itself labels `empty_audio` is kept as a real result,
because production would have received the same thing. The summary a build prints includes a
`needs_retry` list, and it might be worth checking that it is empty before trusting the cache.

## Everyday use

### Score a configuration

```bash
python -m tests.benchmark.run --name current                            # full dev half, current defaults
python -m tests.benchmark.run --name quick --subset smoke_dev           # 250 clips, a fast look
python -m tests.benchmark.run --name legacy --flag WWAI_LEGACY_WORD_SCORING=1
python -m tests.benchmark.run --name t05 --threshold 0.5                # another cutoff
```

`run` writes `results/<name>_<half>.json` (the per-clip outcomes and a metrics summary, with
`_<subset>` added for a subset) and a `.summary.json` with the metrics alone, and prints a
table. A results file records the config name, git SHA, cache name, model revision, active
`WWAI_*` flags and threshold.

- `--flag WWAI_NAME=VALUE` sets a flag for that run and records it. Harness settings
  (`WWAI_BENCH_*`) must be set as environment variables instead.
- `backend/.env` must not set any `WWAI_*` experiment flag. `core` loads that file when it is
  imported, so such a flag would apply without being recorded. `run`, `speed` and `stage_cache`
  exit with code 2 if they find one.
- The pipeline's own `print` and logging output is suppressed. `WWAI_BENCH_VERBOSE=1` turns
  it back on.
- A results file that git tracks (a committed `baseline_dev.json`, for example) is only
  overwritten with `--force`, so an experiment cannot silently replace committed numbers. That
  is why the examples use other names.
- Acceptance decisions use the full dev half. A subset is a quick look.

### Compare two runs

```bash
python -m tests.benchmark.compare tests/benchmark/results/current_dev.json tests/benchmark/results/legacy_dev.json
```

The first file is the baseline and the second the candidate, so every difference is
candidate minus baseline. This example asks whether going back to legacy word scoring would
pass. The comparison is paired, so it can see smaller differences than
the intervals of the two runs would suggest. It applies five checks and exits nonzero if any
fails.

| Check | Passes when |
|---|---|
| Real improvement | The 95% confidence interval of the word F0.5 difference is entirely above 0. The interval comes from a paired bootstrap over speakers (2,000 resamples, fixed seed). |
| Children not worse | The children-only F0.5 difference is not significantly negative, meaning the upper end of its interval is at or above 0. The children slice is small, so a point estimate alone would move with noise. |
| No more wrong corrections | The false-alarm rate on words humans scored 7 to 10 rises by at most 0.5 percentage points. |
| No hiding | The unscored rate (rejected or misaligned clips) rises by at most 1 percentage point, so refusing hard clips cannot pass as an improvement. |
| No new unexpected failures | The number of `unexpected:` failures does not go up. |

Two more conditions are checked by whoever reviews a change, not by `compare`. Speed and
memory are checked with `speed.py` below, and the backend unit tests and the regression
harness (`tests/regression/`) must pass. A change that intentionally moves regression scores
should carry the re-pinned baseline and a written reason.

`compare` also takes `--resamples N` and `--json PATH`. Both results must cover the same half,
subset and clips, otherwise it exits with code 2.

### Speed and memory

```bash
python -m tests.benchmark.speed --name candidate
python -m tests.benchmark.speed --compare tests/benchmark/results/baseline_speed.json tests/benchmark/results/candidate_speed.json
```

`speed` runs the live pipeline (preprocessing, ONNX, decode, alignment, scoring) serially over
the 200 clips in `subsets/speed_dev.txt`, after a warmup, and twice by default (`--repeats`).
Deepgram is replaced by cached transcripts, because network time is not something this
project can change. It reports p50 and p95 latency and peak process memory. Run it with
nothing else heavy running, since any other load changes the timings.

Only clips that finish are timed. A clip that fails usually fails fast, and counting it
would make a worse pipeline look quicker. `--compare` passes when all of these hold.

| Check | Passes when |
|---|---|
| p95 latency | At most 1.10 times the baseline |
| Peak memory | At most 150 MB above the baseline |
| Same clips succeed | At least as many clips succeed as in the baseline |

The design also rules out loading a second acoustic model, which is a review item and not
something the script can see.

### Flag sweep

```bash
python -m tests.benchmark.sweep                        # full dev half
python -m tests.benchmark.sweep --subset smoke_dev     # quick look, not for decisions
```

`sweep` measures each accuracy flag in its `CANDIDATES` list (add new flags there), each in a
fresh interpreter because several flags are read at import time. It then does greedy forward
selection. Each round tries every remaining candidate on top of what is already selected,
keeps the best one that passes all five `compare` checks, and repeats until none passes.
Every flag is compared with the current default, so a flag that has since become the default
shows no difference and is not selected.

A configuration whose front-end flags need a cache that does not exist is reported with the
`stage_cache` command that builds it and then skipped. The summary is written to
`results/sweep_dev.summary.json`.

### Human reference

```bash
python -m tests.benchmark.human_reference --half dev
```

Each of the five annotators is scored against the median of the other four, using the same
0 to 6 rule and the same metrics, and the mean over annotators is reported. This shows what
expert-level agreement looks like on these metrics, which is the number a system's score is
easiest to read against. Annotators only partly agree with each other, so it also shows how
much label noise there is. The output goes to `results/human_reference_<half>.json`.

### Subsets

`subsets/smoke_dev.txt` holds 250 dev clips (stratified by child and adult, fixed seed) for
fast iteration. `subsets/speed_dev.txt` holds the 200 clips `speed` times. Subsets only exist
for the dev half. `run`, `stage_cache` and `sweep` take `--subset NAME`, and a subset's results
file carries the subset name so `compare` can refuse to mix it with a full run.

## How the cache stays honest

The slow stages (the wav2vec2 forward pass and the Deepgram request) are deterministic, so
`stage_cache` runs them once per clip and `run` replays them. The risk is that a code change
alters what the models would receive while the cache still holds outputs for the old input.
The cache guards against that with a hash of the exact model input.

- **Recording.** `stage_cache` runs the real request path (preprocessing, chunking, then both
  models) with recording wrappers. The phoneme model is recorded at the ONNX session itself.
  For every `run()` call it stores a hash of the exact tensor fed to the session, with dtype
  and shape, and the raw float32 logits. That tensor is what is left after the extractor's own
  validation, trimming and feature extraction, so those steps are covered by the hash. Deepgram
  is recorded at `extract_words` as a hash of the audio it was given plus the word list or the
  error. Quality gates are not applied while recording, so every clip has model outputs.
- **Replay.** `ReplayPhonemeExtractor` is the production `PhonemeExtractorONNX` with a stub
  session that returns the cached logits. Everything in the extractor and everything after it
  runs as in production, including decoding. The only things replaced are the forward pass
  and the network request. A decoding change in `core/` is therefore what the benchmark
  measures.
- **Any front-end change stops the run.** Each replayed call hashes what the model would
  receive now and compares it with the recorded hash. A difference raises `StaleCacheError`,
  and `run` exits with code 3 and names the clip. This catches changes to preprocessing,
  noise reduction, trimming, chunking, front-end flags and the number of model calls per
  clip, including ones no list of source files would catch.
- **Errors replay faithfully.** A recorded failure is raised again at the same point, as the
  same kind of exception, so a clip production rejects is rejected in replay for the same
  reason.
- **What needs no new cache.** Decoding, alignment, G2P, word scoring, the quality gates and
  the threshold are all applied at scoring time, so changing them needs no new cache.

The cache also records its half, the ONNX model repository and revision (a 40-character
commit SHA), the active flags and the git SHA, in `_cache_meta.json`. `run` refuses a cache
built for the other half, for another model revision, or under another value of
`WWAI_ASR_FALLBACK` or `WWAI_ASR_TYPED_ERRORS`. Those two flags change what Deepgram returns
for the same audio, which no input hash can show, so `stage_cache` will not record with
either one on. `WWAI_ASR_FALLBACK` would also load a second 1.2 GB model in every worker.

What replay cannot see is a change in Deepgram's own behavior, since the transcripts are
frozen at recording time.

## Front-end flags and their caches

These flags change the audio the models receive, so each distinct setting needs its own cache.
They are listed in `FRONT_END_FLAGS` in `common.py`.

- `WWAI_SINGLE_PREPROCESS`
- `WWAI_SOFT_QUALITY_GATES`, which is here because it also switches the SNR measurement that
  drives adaptive noise reduction, so it changes the audio and not only the gates
- `WWAI_CHUNK_PRESERVE_PAUSES`
- `WWAI_CHUNK_OVERLAP_SECONDS`, `WWAI_CHUNK_THRESHOLD_SECONDS`, `WWAI_CHUNK_MAX_DURATION` and
  `WWAI_CHUNK_MIN_DURATION`

A cache lives in `cache/<half>/<name>/`. The name is derived from the effective front-end
settings. A setting's effective value is the one from `--flag` or the environment when there is
one, and otherwise the default the code uses (`FRONT_END_DEFAULTS` in `common.py` holds the
flags that are on by default). A boolean flag that is effectively on appears as `FLAG=1`, a
boolean flag that is off is left out, and a numeric flag that is set appears as `FLAG=value`.
The parts are sorted and joined with `+`. When nothing remains, the name is `baseline`. For
example, with `WWAI_SINGLE_PREPROCESS` and `WWAI_SOFT_QUALITY_GATES` on by default, a plain
command uses the cache named `WWAI_SINGLE_PREPROCESS=1+WWAI_SOFT_QUALITY_GATES=1`, and the
earlier front end, with both switched off, is named `baseline`.

Because the names follow the code's defaults, flipping a default in `core/` changes which
cache a plain `run` reads. If that cache has not been built, `run` stops with exit code 3 and
prints the directory it looked in. `--cache NAME` on `run` and `speed`, and `--name NAME` on
`stage_cache`, override the derived name.

```bash
# the front end with both defaults switched off (named "baseline")
python -m tests.benchmark.stage_cache --half dev --flag WWAI_SINGLE_PREPROCESS=0 --flag WWAI_SOFT_QUALITY_GATES=0
python -m tests.benchmark.run --name original --flag WWAI_SINGLE_PREPROCESS=0 --flag WWAI_SOFT_QUALITY_GATES=0

# a new front-end experiment
python -m tests.benchmark.stage_cache --half dev --flag WWAI_CHUNK_PRESERVE_PAUSES=1
python -m tests.benchmark.run --name pauses --flag WWAI_CHUNK_PRESERVE_PAUSES=1
```

A change to preprocessing code with no flag involved also makes the current cache stale.
Record it under a new name (`stage_cache --name my_preprocessing`, then
`run --cache my_preprocessing`). Reusing the old name would not help, because existing entries
are skipped and not re-checked.

## The sealed test half and test_runs.log

The dataset's own `train` half is the dev half, and its `test` half is sealed. The two share
no speakers, which `dataset check` verifies. A run on the sealed half needs all of these.

- `WWAI_BENCH_UNLOCK_TEST=1` in the environment.
- `--reason "..."` saying why the look is being taken.
- A clean git tree (no uncommitted changes to tracked files), so that every look can be
  reproduced from the SHA it records.

```bash
WWAI_BENCH_UNLOCK_TEST=1 python -m tests.benchmark.run --name final --half test --reason "final system"
```

Each such run appends one tab-separated line to `test_runs.log`, which is committed. The line
holds the time, git SHA, config name, reason, active flags as JSON and the threshold. The
line is written once the cache has been checked and before scoring, so a look that gets as far
as scoring is logged even if it fails, and a stale cache does not use up a look. Comparing
test-half results and running `human_reference --half test` also need the unlock variable.
`human_reference` only reads the experts' own scores and writes no ledger line.

The log makes the number of looks public. The intended number is two, one for the original
baseline and one for the final system. Thresholds and flags are chosen on the dev half and
frozen before either look, and the improvement agents are never given the unlock variable.

## Measuring at an exact commit

Results record the git SHA of `HEAD`, with `-dirty` added when tracked files have uncommitted
changes. To measure a commit exactly while work carries on elsewhere, use a detached worktree
and point it at the shared data and caches, which are large and gitignored.

```bash
# from the main checkout, <sha> being the commit to measure
git worktree add --detach ../measure <sha>
# venv/ and backend/.env are gitignored, so the new worktree has neither. Link or copy them.
cd ../measure/backend
export WWAI_BENCH_DATA_DIR=/path/to/main/backend/tests/benchmark/data
export WWAI_BENCH_CACHE_DIR=/path/to/main/backend/tests/benchmark/cache
python -m tests.benchmark.run --name candidate --out /path/to/candidate_dev.json
git worktree remove ../measure
```

`WWAI_BENCH_DATA_DIR` and `WWAI_BENCH_CACHE_DIR` are harness settings. They are not recorded as
flags. Sharing one cache folder between commits is safe because of the input hashes, since a
commit whose front end differs stops with exit code 3 instead of reading outputs for other
audio.

Results go to the worktree's own `tests/benchmark/results/` unless `--out` says otherwise, so
copy them out before removing the worktree. A sealed-half run from a measurement worktree
appends to that worktree's `test_runs.log`, and that line needs to be copied back to the branch
that gets committed. A detached worktree is also an easy way to meet the clean-tree rule for a
sealed look.

## Exit codes

| Command | 0 | 1 | 2 | 3 | 4 |
|---|---|---|---|---|---|
| `run` | ok | | usage error, locked half, dirty tree on the test half, `WWAI_*` in `backend/.env`, tracked results | stale or missing cache | clips failed with unexpected errors (results are still written) |
| `compare` | all five checks pass | at least one fails | results cannot be compared, or test half not unlocked | | |
| `speed` | ok | | usage error | stale or missing cache | no clip succeeded |
| `speed --compare` | all checks pass | at least one fails | | | |
| `stage_cache` | every clip recorded | a clip still needs a retry, or the build stopped (Deepgram failing, a worker died, a cache that does not match) | refused flags (`WWAI_*` in `backend/.env`, `WWAI_ASR_FALLBACK`, `WWAI_ASR_TYPED_ERRORS`) | | |
| `sweep` | ok | a run failed | dataset missing, or results cannot be compared | the baseline needs a cache | |
| `dataset check` | no problems | problems found | | | |
| `human_reference` | ok | | test half not unlocked | | |

## Running the tests

```bash
python -m unittest discover -s tests/benchmark -t . -v
```

This needs no network and no Deepgram key, and takes a few minutes, partly because importing
`core` loads torch. `test_live_parity.py` compares replay with a live ONNX run on real dev clips,
including long ones that take the chunked path. It skips when the dataset, the dev cache it
reads or the ONNX model is not available, and fails on any mismatch.

The unit tests for the production code the benchmark depends on live in `tests/`, and the
scoring regression harness is in `tests/regression/`.

## Limitations

These are the things the benchmark does not show, or shows less well than a single number
suggests. `BENCHMARK.md` will repeat them next to the results.

- **The population is different from Word Wiz's users.** speechocean762 speakers are
  Mandarin-L1 English learners reading the right word, and many are adults. Word Wiz's users
  are mostly young children learning to read. The benchmark measures phoneme-level
  mispronunciation detection, not reading mistakes. A skipped, added or guessed word ("sit"
  for "it", "running" for "run") never appears in the labels, so changes that affect those
  cases are invisible here. That mattered for word scoring v2, which ignores one stray
  phoneme at each edge of a word. It scored better here, but it could also hide a child's
  reading miscue, which the benchmark has no way to penalize. It needed a guard that
  withholds the forgiveness when Deepgram heard a different word, and that guard is covered
  by unit tests and not by this benchmark.
- **Production recordings are longer.** The browser recorder only stops after 2 seconds of
  silence (`SILENCE_DELAY_MS` in `frontend/src/hooks/useAudioRecorder.ts`), so a real recording
  ends with about 2 seconds of silence, and speechocean762 clips are trimmed tightly. About 5%
  of dev clips go over the 8 second chunking threshold here, against about 12% once 2 seconds
  of silence are added, so the chunked path is exercised about half as often as in
  production.
- **Thresholds tuned on the dev half are optimistic.** Many comparisons are made on the same
  2,500 clips, so some accepted changes will have looked good by luck, and the acceptance
  rule's interval does not correct for the number of things tried. The sealed test half and
  `test_runs.log` exist to give an honest final number, and it may be worth treating every
  dev-half result as an upper estimate until then.
- **The children slice is small.** It has roughly 180 to 195 real mistakes (depending on
  which clips are scored) from about 60 speakers, so its intervals are wide. That is why the
  children check only fails on a significant drop and not on a lower point estimate.
- **Deepgram returns empty transcripts for some young children.** Some clips of young children
  reading correctly come back from Deepgram with HTTP 200 and no words. They are recorded as
  real results, since production gets the same, and production then asks the child to try
  again. The benchmark counts these clips as rejected, so they are outside every accuracy
  number, and these children are probably the ones the benchmark describes least well. The
  transcripts are frozen at recording time, so a later change in Deepgram's behavior would not
  show up here.
- **The browser (client-phoneme) path is not covered.** Transformers.js extraction is out of
  scope. The server path is the one users get, since a migration turned
  `use_client_phoneme_extraction` off for everyone, and the browser path is only checked for
  agreement with the server path by the regression harness.
- **Phone-level positions use forward alignment only.** Each word's G2P phones are matched to
  the experts' canonical phones by one left-to-right edit-distance alignment, and a phone is
  flagged by the same kind of alignment between expected and recognized phones. There is no
  timing information. When several alignments are equally good the harness takes one of them,
  so an error can land on a neighboring phone. Phone-level numbers are therefore rougher than
  word-level numbers, which is why they are not used to accept a change.
- **Scoring uses production G2P, which sometimes disagrees with the experts.** A wrong
  expected pronunciation turns a correct reading into a false alarm. That is intended, since
  production has the same problem, but it caps precision. The summary reports the
  disagreement rate (`g2p_disagreement_rate`) so the cap is visible.
- **Human labels are noisy.** Annotators only partly agree, which is what `human_reference`
  shows, so no system can be expected to match the labels exactly.
- **Published systems are not a like-for-like comparison.** Published speechocean762 results
  come from models trained on its train half. Word Wiz is not trained on it, so correlations
  against those papers need that caveat.
- **Speed numbers are relative.** `speed` compares two configurations on one local machine
  (16 threads, no GPU) and leaves out Deepgram's network time. The ratio between runs is
  meaningful, and the absolute seconds are not what the production server (about 3.8 GB of
  memory) will see.
