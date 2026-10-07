# SpeechOcean762 Accuracy Benchmark and Agent Improvement Rounds

**Date:** 2026-10-05
**Status:** Approved
**Target:** final held-out result and BENCHMARK.md by 2026-11-01

## Goal

Build a benchmark inside the repo that measures how well Word Wiz AI's pronunciation scoring
agrees with expert human judgments on speechocean762. Then use it to run rounds of parallel
agents that each propose one kind of accuracy improvement, and merge only the proposals that
measurably help without slowing the system down.

The finished result is a number that holds up to scrutiny. It is measured once on held-out
data, compared against how well human experts agree with each other, and documented in
`BENCHMARK.md` with a single command to reproduce it.

## Context

What exists today, and why it is not enough.

- `backend/tests/regression/` checks determinism, client/server path agreement and drift
  against pinned baselines on 7 cases, 5 of them hand-written. Its README says it proves
  stability, not quality. Nothing in the repo compares scores against human labels.
- Several accuracy features from the audio robustness round sit behind flags that default to
  OFF and were never measured on real speech. These are `WWAI_GT_ANCHORED_ALIGNMENT`,
  `WWAI_PHONEME_NORMALIZATION`, `WWAI_G2P_STRICT`, `WWAI_WEIGHTED_PER`,
  `WWAI_SINGLE_PREPROCESS`, `WWAI_SOFT_QUALITY_GATES` and `WWAI_CHUNK_PRESERVE_PAUSES`.
- `PhonemeExtractorONNX.extract_phoneme` takes the argmax of the logits and discards them, so
  any idea that needs per-frame model confidence currently has nothing to work with.
- The server path sends every clip to Deepgram nova-2 for word extraction, which needs a
  network connection and costs money per call.
- A migration (`a1b2c3d4e5f6`) set `use_client_phoneme_extraction` to false for every user, so
  the server path is the one real users hit.
- Production flags a word in feedback when its PER is at least `HIGH_PER_THRESHOLD = 0.4`
  (`core/phoneme_feedback_formatter.py`).
- The production box has about 3.8 GB of memory and already idles near 83% used. It cannot
  hold a second acoustic model.
- The local machine has 16 threads, 31 GB of memory and no GPU.

## Decisions

| Topic | Decision |
|---|---|
| What "more accurate" means | Precision-first. Rarely tell a child they misread a word they read correctly. Primary metric is word-level F0.5. |
| Speed and memory budget | p95 local-pipeline latency at most 10% above baseline, peak memory at most +150 MB, no second model. |
| Which path | Server path only. The browser path stays covered by the existing path-agreement regression test. |
| Benchmark architecture | Cache-and-replay. Slow deterministic stages run once per clip, and the real production scoring code runs against the cached outputs. |
| Deliverable | `BENCHMARK.md` in the repo, with method, before/after table with confidence intervals, comparison to published results, limitations, and a reproduce command. |
| Deadline | 2026-11-01. One flag sweep, one agent round, and an optional small second round. |

## Data and labels

### Source

`dataset.py` downloads the official speechocean762 release (the Kaldi-format files plus
`resource/scores.json` and `resource/scores-detail.json`) into
`backend/tests/benchmark/data/`, which is gitignored. No new Python dependency is needed. The
parser writes one manifest per half with, for each clip, the utterance id, speaker id, speaker
age, text, sentence scores, and for each word its text, human accuracy score (0 to 10),
canonical ARPAbet phones and per-phone human accuracy scores (0 to 2).

### Dev half and test half

- The dataset's **train** half (2,500 clips) is the **dev half**. Agents use it freely.
- The dataset's **test** half (2,500 clips) is held out. `run.py` refuses to read it unless
  `WWAI_BENCH_UNLOCK_TEST=1` is set. Every unlocked run appends a line (timestamp, git SHA,
  config name, reason) to the committed file `backend/tests/benchmark/test_runs.log`, so the
  number of looks at the test half is public. The intended count is two, once for the
  baseline and once for the final system.
- `dataset.py` asserts that no speaker appears in both halves and fails loudly if one does.
- A fixed **smoke subset** of 250 dev clips (stratified by child/adult, fixed seed, list
  committed) exists for fast iteration. Acceptance decisions always use the full dev half.

### What counts as a real mistake

Thresholds come straight from the speechocean762 rubric, chosen so that accent alone is
never treated as a mistake.

| Level | Real mistake | Not a mistake (flagging it is a false alarm) |
|---|---|---|
| Word | human accuracy 0 to 6 (phones wrong, wrong word, or missed) | 7 to 10 (correct, or correct with an accent) |
| Phone | human accuracy 0 (incorrect or missed) | 1 to 2 (correct, or heavy accent) |

A stricter phone-level variant, where a phone score of 1 also counts as a mistake, is
reported as a secondary number. Human scores are the released per-item scores in
`scores.json`.

### Slices

Every metric is reported overall, for children, and for adults. A child is a speaker whose
age in `spk2age` is under 18.

### Ground-truth phonemes

Scoring uses the production G2P (`core/grapheme_to_phoneme.py`), exactly as the app does.
The expert canonical phones are used only for a diagnostic, which is the rate at which G2P
disagrees with them after ARPAbet-to-IPA conversion. A G2P error turns a correct reading into
a false alarm, so this rate matters for precision.

## Benchmark components

Everything lives in `backend/tests/benchmark/` and runs as `python -m tests.benchmark.<cmd>`
from `backend/`, matching `tests/regression/`. `PYTHONIOENCODING=utf-8` is required on
Windows, as with the regression harness.

| Unit | Responsibility | Depends on |
|---|---|---|
| `dataset.py` | Download, parse, write manifests, speaker-disjointness check, smoke subset list | nothing in `core/` |
| `stage_cache.py` | Run the slow stages once per clip and save the outputs | production preprocessing, ONNX extractor, Deepgram |
| `replay.py` | Stand-in phoneme and word extractors that return cached outputs | production decode function |
| `run.py` | Run the real pipeline over a half with replay stand-ins and write a results file | the three above |
| `metrics.py` | Pure metric functions | nothing |
| `compare.py` | Paired comparison of two results files with confidence intervals and the acceptance check | `metrics.py` |
| `speed.py` | Serial live latency and memory measurement on a fixed 200-clip subset | live pipeline |
| `sweep.py` | Round 0 flag sweep | `run.py`, `compare.py` |

### `stage_cache.py`

For each clip it runs the real request path (preprocessing, chunking, then both models)
with recording wrappers around the ONNX extractor and the Deepgram extractor. For every
model call it saves a hash of the exact audio the model received plus the model's output,
which is the raw logits (float32, so replayed argmax is exact) for ONNX and the word list
for Deepgram. Entries live in `cache/<half>/<name>/<utt_id>.npz` and `.json`. Gates are not
applied while recording, so every clip has model outputs, and gates run at scoring time.

Replay checks each call's audio hash, so any change in what the models would receive
(preprocessing code, chunking, a front-end flag) stops the run and asks for a new cache.
This replaces fingerprinting source files and catches changes no file list would. The
cache also records the ONNX model revision, and `run.py` refuses a cache built on a
different revision. The cache name defaults to `baseline` or to the front-end flags that
are set. Caching is resumable (existing entries are skipped) and parallel across
processes. Clips whose Deepgram call failed are recorded with the error and re-run with
`--retry-errors`.

An agent that changes preprocessing builds its own cache. While exploring it may reuse the
baseline Deepgram transcripts, and the proposal must say so. Before such a proposal is
accepted, Deepgram is re-run on the new preprocessing so the final measurement is faithful.
The cache directory is gitignored.

### Production changes (all behavior-preserving)

- `PhonemeExtractorONNX` gains `extract_logits(audio, sampling_rate)` returning the raw
  logits, and a module-level `decode_logits(logits, processor)` that does what the end of
  `extract_phoneme` does today. `extract_phoneme` becomes `decode_logits(extract_logits(...))`,
  and a golden test proves identical output on sample audio. `replay.py` decodes cached
  logits through `decode_logits`, so a decoding change made in `core/` is what the
  benchmark measures.
- The quality gates move from the router into `core/request_audio.py` (`gate_audio`,
  `gate_and_preprocess`, `AudioRejected`). The handler converts `AudioRejected` into the
  same 400 responses as before. Without this the benchmark could not run the real gates,
  and the soft-gates flag could not be measured.
- `clean_sentence()` is extracted from `PhonemeAssistant.process_audio` so both score the
  same ground truth.
- `HIGH_PER_THRESHOLD` moves to module level in `core/phoneme_feedback_formatter.py` so
  the benchmark reads production's cutoff.
- The ONNX model revision is pinned in `core/model_registry.py` and passed to the loader.

### `run.py`

For each clip in the chosen half (or smoke subset), it runs production G2P on the text, calls
the real `process_audio_array` with the replay stand-ins, and records the per-word analysis
output the app would receive. Output is a results JSON with the config name, git SHA, cache
name and model revision, active `WWAI_*` flags, operating threshold, per-clip per-word
predictions and a metrics summary. Clips run in parallel across processes. The pipeline's `print()` output is
suppressed unless `WWAI_BENCH_VERBOSE=1`.

Messy cases are counted rather than dropped.

- **Rejected clips.** When the pipeline raises (no speech detected, quality gate, alignment
  failure), the clip is recorded as rejected with the error type. Its words are left out of
  word and phone scoring, since the child would be asked to try again rather than corrected.
  Rejection rate is reported and guarded (see acceptance rule) so that refusing hard clips
  cannot pass as an improvement.
- **Word-count mismatches.** System output entries for ground-truth words are matched to
  speechocean words by position after text normalization. Insertion records are skipped.
  When the counts still differ, the clip's words are left out of word and phone scoring,
  logged, and counted in the summary.
- **Phone mapping.** For phone-level scoring, each word's G2P phones are aligned to its
  canonical phones (converted to IPA) by edit distance. Only aligned positions are scored. A
  phone is flagged when the pipeline's per-phoneme error output marks it as a substitution or
  deletion.

### Operating point

The headline numbers use production's own decision rule. `run.py` reads
`HIGH_PER_THRESHOLD` from `core/phoneme_feedback_formatter.py` rather than hardcoding 0.4,
so a proposal that changes the constant is measured at its new value. Each results file also
reports the F0.5-maximizing threshold on that half and a precision/recall curve. A proposal
may change the production threshold, but the value must be chosen on the dev half and is
frozen before any test-half run. A proposal may also define a different per-word score, as
long as production feedback uses that same score.

### `speed.py`

Runs the live local pipeline (preprocessing, ONNX, decode, alignment, scoring, with Deepgram
replaced by cached transcripts) serially over a fixed, committed list of 200 dev clips after a
warmup. The subset is run twice and the mean of the two p95 latencies is reported, along with
p50 and peak process memory. Only the orchestrator runs it, with no agents or other heavy
processes running, so every measurement happens under the same conditions.

## Metrics and acceptance rule

### Primary

Word-level F0.5 on the full dev half at the proposal's operating threshold, all speakers
pooled.

### Acceptance

A proposal is accepted only when every condition holds against the current baseline.

1. **Real improvement.** The 95% confidence interval of the F0.5 difference lies entirely
   above zero. The interval comes from a paired bootstrap over speakers (resample the dev
   speakers with replacement, 2,000 resamples, fixed seed, recompute both systems on the same
   resample).
2. **Children are not worse.** The children-only F0.5 difference is at least zero.
3. **No more wrong corrections.** The false-alarm rate on words humans scored 7 to 10 rises
   by at most 0.5 percentage points.
4. **No hiding.** The rejection rate rises by at most 1 percentage point.
5. **Speed and memory.** `speed.py` p95 latency at most 10% above baseline, peak memory at
   most +150 MB, and no additional model loaded.
6. **Nothing breaks.** The backend unit tests and the regression harness pass. If a change
   intentionally moves regression scores, the proposal includes the re-pinned baseline and a
   written reason.

`compare.py` checks conditions 1 to 4, prints a table, and exits nonzero when any of them
fails. Conditions 5 and 6 are checked by the orchestrator at review time.

### Reported but not used for acceptance

- Phone-level precision, recall and F0.5 under the lenient and strict definitions.
- Pearson correlation with human scores at phone, word and sentence level, for comparison
  with published speechocean762 results such as GOPT (Gong et al., 2022). Published figures
  are copied from the papers at write-up time, not from memory. The write-up states that those
  systems are trained on the speechocean762 train half and Word Wiz is not trained on it.
- G2P disagreement rate against the canonical phones.
- **Human agreement reference.** Using `scores-detail.json`, each annotator's labels are
  scored against the median of the other four on the same metrics, and the mean over
  annotators is reported. This shows how close the system is to expert-level agreement.

### Determinism precondition

Running the baseline twice must produce identical results files apart from timestamps. If it
does not, the source of nondeterminism is fixed before Round 0 starts.

## Agent rounds

### Round 0: flag sweep (script, no agents)

`sweep.py` runs each OFF flag alone on the dev half, with `WWAI_PHONEME_NORMALIZATION` and
`WWAI_G2P_STRICT` also tested as a pair since they were built to be coupled.
`WWAI_SINGLE_PREPROCESS` needs its own cache. It then does greedy forward selection, adding
the best accepted flag, re-measuring, and repeating until nothing else passes. The same
acceptance rule applies. The selected flags become defaults in code, and that system becomes
the baseline for Round 1.

### Round 1: six parallel agents

Each agent works in its own git worktree branched from the Round 0 baseline and owns one
area.

| # | Area | Scope |
|---|---|---|
| 1 | Decoding | Better use of cached logits, such as blank penalty, beam search, and decoding informed by the expected phonemes |
| 2 | Confidence scoring | Goodness-of-pronunciation style scores for each expected phoneme from the logits, alone or combined with PER, with no extra model |
| 3 | Alignment | Assigning recognized phonemes to words, including legacy versus GT-anchored alignment, Deepgram hint use and word-edge handling |
| 4 | Accent tolerance and threshold | Which substitutions are accent-level versus real errors, the phonetic distance table, weighted PER and the flag threshold |
| 5 | Ground-truth quality | Accepting any valid dictionary pronunciation variant, stress handling and out-of-vocabulary words, guided by the canonical-phone diagnostic |
| 6 | Audio front end and child speech | Trimming that clips word edges, noise reduction, normalization, and whether child clips fail differently (builds its own cache) |

Each agent receives the dev half, the benchmark commands, the baseline results, its area with
starting points, the acceptance rule, and these constraints. It must not unlock or read the
test half, must not load a second model, must stay on the server path, and should keep its
edits inside its area. It returns a branch with a `PROPOSAL.md` containing the hypothesis,
the change, `compare.py` output against the baseline, any threshold change, tests run,
risks, and what was tried and did not work.

### Review gate (orchestrator)

For each proposal the orchestrator re-runs `compare.py` itself rather than trusting the
agent's numbers, runs `speed.py`, runs the unit tests and regression harness, and reviews
the code. Accepted proposals are merged one at a time in order of F0.5 gain, and the
benchmark is re-run after each merge. A proposal whose gain does not survive on top of
earlier merges is dropped and recorded as such.

### Round 2 (optional)

If time allows in week 3, two or three agents push further on the most promising direction
from Round 1 under the same rules.

### Housekeeping

The 11 leftover worktrees in `.claude/worktrees/` from the audio robustness round are removed
before Round 1, after confirming each has no unmerged commits or uncommitted changes.

## Testing the benchmark itself

- `metrics.py` is tested against small hand-computed cases (precision, recall, F0.5,
  false-alarm rate, Pearson, threshold sweep, speaker bootstrap on a toy dataset with a known
  answer).
- `dataset.py` parsing is tested on a tiny committed fixture shaped like `scores.json`,
  including the speaker-overlap check firing.
- `decode_logits(extract_logits(x))` is tested to equal today's `extract_phoneme(x)` on
  sample audio.
- Replay is tested to match a live run on a handful of clips.
- `compare.py` exit codes are tested for pass, each failing condition, and inputs that
  cannot be compared. `run.py` is tested to stop with its own exit code on a missing or
  stale cache.
- The test-half lock is tested to refuse without the variable and to append to
  `test_runs.log` with it.

## Results and files committed

- Committed. Code, tests, fixtures, smoke and speed subset lists, `test_runs.log`, results
  summaries for every accepted step, and full per-clip results for the original baseline and
  the final system.
- Gitignored. Downloaded audio, caches, and per-clip results for exploratory runs.

## Timeline

| Week | Dates | Work |
|---|---|---|
| 1 | Oct 5 to 11 | Build and test the benchmark, cache both halves, record the dev baseline, determinism check |
| 2 | Oct 12 to 18 | Round 0 flag sweep and merge, clean up old worktrees, launch Round 1 |
| 3 | Oct 19 to 25 | Review gate and merges, optional Round 2 |
| 4 | Oct 26 to Nov 1 | Freeze, one test-half run of the original baseline and the final system, write `BENCHMARK.md`, deploy when Bruce approves |

## Out of scope

- The browser (Transformers.js) path, beyond keeping the existing regression test green.
- GPT feedback, TTS and the WebSocket layer.
- Training or fine-tuning any model. This would also break the dev-half discipline, since
  speechocean762's train half is the dev half here.
- Reading-miscue detection (skipped, inserted or guessed words). speechocean762 does not
  label these.
- Deploying to production. That is a separate step after the final result, following the
  deploy and memory checks in `CLAUDE.md`.

## Risks and limitations

- **Overfitting to the dev half.** Many proposals tuned on the same 2,500 clips will include
  some that look good by luck. The sealed test half and the public `test_runs.log` keep
  the reported number honest.
- **Population mismatch.** speechocean762 speakers are Mandarin-L1 English learners, while
  Word Wiz users are mostly children learning to read. The benchmark measures phoneme-level
  mispronunciation detection, not reading mistakes, and `BENCHMARK.md` will say so plainly.
- **Human label noise.** Annotators only partly agree with each other. The human agreement
  reference shows how much of the remaining error any system could realistically remove.
- **CPU contention.** Six agents on one machine make their own timings meaningless, which is
  why only the orchestrator measures speed.
- **Stale caches.** Per-call audio hashes stop a results file from being built on a cache
  that no longer matches what the code feeds the models.
- **Unpinned models.** Every model in `core/model_registry.py` is unpinned, so a push upstream
  could shift results between the baseline and the final run. Resolving and pinning the ONNX
  model revision is part of week 1.
