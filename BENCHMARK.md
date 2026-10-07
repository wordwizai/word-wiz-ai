# Word Wiz AI accuracy benchmark

Word Wiz AI listens to a child read a sentence and tells them which word to practice. This
document reports how often that feedback agrees with expert human judges, before and after a
series of changes to the scoring. Everything was developed on one half of a public dataset and
checked once, at the end, on the other half, which had been sealed until then.

On that sealed half, word-level F0.5 rose from 0.169 to 0.314 (95% confidence interval of the
difference +0.115 to +0.172), and for children from 0.104 to 0.221. The share of readings in
which a child is told to fix a word they read correctly fell from 80% to 41% (for children,
from 86% to 45%), and spoken corrections that name a real mistake doubled, from 12% to 25%.
Speed and memory did not change measurably.

## Results

All numbers in this section come from the sealed test half of speechocean762 (125 speakers,
2,500 recordings, 1,280 of them by children). "Before" is the original scoring, reproduced
with the current code by turning on every kill switch. That reproduction was checked
recording by recording on the dev half (see "How it is measured"). "After" is the final system
with its defaults. Intervals are 95% speaker-bootstrap confidence intervals of the difference.

### What the child hears

| | Before | After | Difference (95% CI) |
|---|---|---|---|
| Readings where the child is told to fix a word they read correctly | 79.7% | 40.5% | -39.2 points (-42.3 to -35.9) |
| ... children only | 86.0% | 45.0% | -41.0 points |
| Spoken corrections whose word was a real mistake | 12.3% | 24.8% | +12.5 points (+9.6 to +15.3) |
| ... children only | 7.8% | 16.9% | +9.1 points |
| Readings with no real mistake that still get a correction | 87.5% | 44.5% | |
| Readings with a real mistake where that mistake is the word named | 38.1% | 45.8% | |
| Readings with a real mistake that get "Great job!" | 0.9% | 8.0% | +7.1 points |
| Recordings refused with "we couldn't hear you" | 4.9% | 0.2% | -4.7 points |

The feedback names one word per reading. A "real mistake" is a word the experts scored 0 to 6
out of 10. The last-but-one row is the main cost of the changes. The system now praises some
readings that had a mistake, in exchange for correcting about half as many readings that had
none.

### Word-level agreement with the experts

A word counts as flagged when the feedback is allowed to correct it.

| | Before | After | Difference (95% CI) |
|---|---|---|---|
| F0.5, all | 0.169 | 0.314 | +0.145 (+0.115 to +0.172) |
| F0.5, children | 0.104 | 0.221 | +0.117 (+0.072 to +0.164) |
| F0.5, adults | 0.227 | 0.394 | +0.166 |
| Precision (flagged words that were real mistakes) | 14.0% | 28.9% | +14.9 points |
| Recall (real mistakes that were flagged) | 90.6% | 47.9% | -42.7 points |
| False-alarm rate (correctly read words that were flagged) | 45.9% | 10.3% | -35.6 points |
| Recordings that could be scored | 95.1% | 99.8% | +4.7 points |

Before, the system flagged almost every real mistake, but it also flagged nearly half of all
correctly read words, so most of its flags were wrong. After, it flags about half of the real
mistakes and one correctly read word in ten.

### Speed and memory

Measured on 200 dev recordings, twice each, with the live ONNX phoneme model and cached speech
recognizer transcripts. The two configurations ran in one process, alternating recording by
recording. A back-to-back comparison turned out to mostly measure heat, since a laptop that has
been busy for ten minutes runs 15 to 30% slower than a cool one.

| | Before | After |
|---|---|---|
| Median latency | 1.51 s | 1.40 s (7% faster) |
| 95th percentile latency | 3.33 s | 3.32 s (1.00x, budget 1.10x) |
| Recordings that finish | 195 of 200 | 200 of 200 |
| Peak memory | 2,118 MB | 2,121 MB (+3 MB, budget +150 MB) |

No second model was added. The median is faster mainly because the audio is now cleaned once
instead of twice, and the new alignment is quicker than the old one. The slowest recordings
are dominated by the phoneme model itself, which did not change.

## What changed

Each change was tried on the dev half first and kept only if it passed the acceptance checks
listed under "How it is measured". Every change has an environment switch that restores the old
behaviour.

| # | Change | Kill switch | Dev-half effect when accepted |
|---|---|---|---|
| 1 | Align the heard sounds to the sentence the child was asked to read, instead of to what the speech recognizer thought it heard | `WWAI_GT_ANCHORED_ALIGNMENT=0` | F0.5 0.196 to 0.204 (CI +0.005 to +0.011), false alarms 46.9% to 44.4% |
| 2 | Score each word against its closest dictionary pronunciation ("to" may be said "tu" or "tuh"), and ignore stray sounds at a word's edges that belong to the next word | `WWAI_LEGACY_WORD_SCORING=1` | F0.5 0.204 to 0.219, false alarms 44.4% to 37.3% |
| 3 | Clean the audio once instead of twice (each pass trimmed about 50 ms), and let quality problems produce a gentle hint instead of a rejection | `WWAI_SINGLE_PREPROCESS=0`, `WWAI_SOFT_QUALITY_GATES=0` | F0.5 +0.004 (CI +0.000 to +0.009), refused recordings 112 to 93 |
| 4 | Forgive at most three stray edge sounds, and stop forgiving them when the recognizer heard a different real word that fits the sounds ("sit" for "it") | part of #2 | F0.5 0.226 to 0.228 (CI +0.000 to +0.004), recall +1.0 point |
| 5 | Name the word the problem sound came from, not the first word in the sentence that shares the sound | `WWAI_LEGACY_FEEDBACK=1` | spoken corrections whose word was a real mistake 14.6% to 19.2% (CI +3.1 to +6.0 points) |
| 6 | Score phonemes sent by the browser exactly like phonemes found on the server | `WWAI_GT_ANCHORED_ALIGNMENT=0` | browser path F0.5 0.157 to 0.228, false alarms 66.6% to 36.7% |
| 7 | Keep apostrophes inside words, so "it's" and "didn't" get real pronunciations instead of being scored against their spelling | `WWAI_LEGACY_SENTENCE_CLEANING=1` | F0.5 +0.001 (CI +0.001 to +0.002), false alarms -0.3 points |
| 8 | Correct a word only when at least three of its sounds were wrong, and say "Keep practicing!" instead of naming a barely-wrong word | `WWAI_LEGACY_FEEDBACK=1` | F0.5 0.229 to 0.346 (CI +0.091 to +0.138), false alarms 36.4% to 10.2%, children 0.077 to 0.130 |
| 9 | Score a reading the speech recognizer heard nothing in, when the phoneme model heard at least 30% of the expected sounds | `WWAI_REQUIRE_ASR_WORDS=1` | refused recordings 3.7% to 0.2% (61 more children's readings scored), false alarms +0.2 points |

Changes 5 and 9 did not pass the first acceptance check, and they deserve an explanation.
Change 5 only changes which word is spoken, so word-level F0.5 cannot see it at all. It was kept
because the spoken-feedback numbers improved with intervals clear of zero. Change 9 adds
readings to the scored set, and F0.5 is computed only over scored readings, so it cannot give
credit for coverage. It was kept because every other check passed and the feedback on the
rescued readings was better than average (36% of its corrections named a real mistake, against
28% overall). Both decisions were made after looking at the dev half, which is looser than the
rule set in advance, so it seems fair to say so plainly.

Smaller fixes made along the way include a kind message instead of "Something went wrong" when
a recording has no speech or is too short, double quotes, colons and dashes no longer being
scored as sounds, and each word in the analysis now carrying a `clear_mistake` flag that matches
the spoken feedback.

### What was tried and not kept

| Attempt | Why it was dropped |
|---|---|
| Weighting substitutions by how similar the sounds are (`WWAI_WEIGHTED_PER`) | No effect at all. The weighting turned out to be used only in an old segmentation step, not in word scoring. |
| Normalizing affricates plus strict G2P tokens | F0.5 -0.003. The model writes "ch" as one symbol and the dictionary as two, so a perfect "church" scored PER 0.5. |
| The single preprocessing pass alone, and soft gates alone | Each raised F0.5 by about 0.003, with intervals touching zero. Together they passed (change 3). |
| Scoring empty transcripts under the old PER cutoff | False alarms +0.64 points, over the 0.5-point limit. Retried after change 8 and kept (change 9). |
| Forgiving only one edge sound, and withdrawing forgiveness whenever the recognizer wrote another word | False alarms +2.9 points. Real word boundaries often spill two or three sounds, and the recognizer often mishears correct readings. Replaced by change 4. |
| Praising whenever no word was clearly wrong | False praise rose to 21% of readings with a real mistake. |
| Length-aware versions of the three-error rule | F0.5 +0.002 to +0.004, within noise, so not worth an extra rule. |
| Goodness-of-pronunciation scores from the model's own confidence (prototype) | Best-threshold F0.5 0.226 against 0.214 for PER at the time. A modest gain that would need forced alignment on every request. |

## How it is measured

**Data.** speechocean762 (OpenSLR 101) has 5,000 English sentences read by 250 non-native
speakers aged 6 to 43, each scored by five expert annotators at the phone, word and sentence
level. Its train half (125 speakers, 1,160 children's recordings) was the development half. Its
test half (125 other speakers, 1,280 children's recordings) was sealed until the final check.

**What counts as a mistake.** A word is a real mistake when the experts scored it 0 to 6 out of
10, the rubric's band for wrong sounds, a wrong word or a missed word. Scores of 7 to 10 mean
correct, or correct with an accent, so flagging such a word is a false alarm.

**What is scored.** The benchmark runs each recording through the same request path the server
uses (quality gates, preprocessing, the phoneme model, the speech recognizer, alignment, scoring
and the spoken-feedback formatter) and scores production's own decisions. The spoken feedback is
scored by checking whether the word it names was a real mistake.

**Primary metric.** Word-level F0.5, which weights precision twice as much as recall, because
telling a child they misread a word they read correctly does more harm than missing a mistake.
Children's recordings are reported on their own as well.

**Acceptance checks.** A change was kept when, on the dev half,

1. the 95% speaker-bootstrap interval of the F0.5 difference was above zero,
2. children's F0.5 was not significantly worse (the interval's upper bound was at least zero),
3. the false-alarm rate rose by at most 0.5 points,
4. the share of recordings that could not be scored rose by at most 1 point, and
5. there were no new unexpected failures.

Speed was checked separately against a budget of +10% on 95th-percentile latency and +150 MB of
memory.

**Cache and replay.** The phoneme model's raw outputs (recorded at the ONNX session boundary and
keyed by a hash of its exact input) and the speech recognizer's transcripts were recorded once.
Every experiment then replays them and runs all of the other code for real, so a full run over
2,500 recordings takes about two minutes and gives the same answer every time. Replay was checked
against live model runs on 12 real recordings, including long ones that are cut into chunks, and
matched exactly. If a change alters what the model would hear, the recorded input hash no longer
matches and the run stops instead of replaying stale outputs.

**Measuring the original.** The original system was run at its own commit (`95633c8`) on the dev
half. The final code with all of its kill switches on was then run on the same half, and all
2,500 recordings came out identical (status, error message, and every word's phonemes and
score). That configuration is what "Before" means on the test half. It lets both sides be scored
by the same harness, including the spoken-feedback measures, which did not exist yet when the
original was built.

**The sealed half.** A run on the test half needs an unlock variable, a written reason and a
clean git tree, and every look is appended to `backend/tests/benchmark/test_runs.log`, which is
committed. Exactly two looks were taken, "Before" and "After", both at commit `a276b21`.

## Comparison with human experts and published results

**Human experts.** Each of the five annotators was scored against the median of the other four
with the same word-level rule. They reach F0.5 0.597 on the test half (precision 0.572, recall
0.770, false alarms 5.1%) and 0.678 on the dev half. The final system's 0.314 is about half of
the experts' agreement with each other, so there is still a lot of room.

**Published systems.** Papers on speechocean762 report Pearson correlation with the experts'
scores rather than a mistake-detection rate. GOPT (Gong et al., ICASSP 2022, Table 1, with a
Librispeech acoustic model) reports these on the test half.

| Pearson correlation with the experts | GOPT | Word Wiz, before | Word Wiz, after |
|---|---|---|---|
| Phone accuracy | 0.612 | 0.298 | 0.304 |
| Word accuracy | 0.533 | 0.220 | 0.301 |
| Sentence accuracy | 0.714 | 0.483 | 0.556 |

This is not a fair contest. GOPT is trained on speechocean762's own train half to predict exactly
these scores, while Word Wiz was never trained on this data and does not try to produce a score
out of 10 at all. Its numbers here correlate the negative phoneme error rate with the experts'
scores. The table only shows roughly where a general-purpose system sits.

## Limitations

- **This is not the population Word Wiz serves.** speechocean762 is read by non-native speakers
  who always attempt the right word, while Word Wiz is for children learning to read, who also
  misread words ("sit" for "it"). The benchmark measures mispronunciation detection, not
  reading-error detection.
- **Short words are now almost never corrected.** Under the three-error rule a one- or two-sound
  word ("it", "the") cannot be corrected, and neither can a single wrong vowel in a three-sound
  word ("cat" read as "cut"). On this data such corrections were mostly wrong (only 9 to 13% of
  short-word flags were real mistakes), but beginning readers make these mistakes far more often
  than these speakers do, so on their recordings more of those flags would be right. Recall and
  false-alarm rate do not depend on how common mistakes are, while precision and F0.5 do, which
  is why the rule was chosen with false-alarm rates in view and not F0.5 alone.
  `WWAI_LEGACY_FEEDBACK=1` restores the old rule.
- **False praise went up**, from 0.9% to 8.0% of readings with a real mistake.
- **The spoken-feedback measures were added partway through.** They exist because the word-level
  number turned out to hide how often a child heard a wrong correction. Changes 5 and 9 were
  accepted on them or on coverage, as explained above.
- **The browser path is simulated.** The browser runs the same pinned phoneme model as the
  server, so the benchmark feeds the server's phonemes through the browser's scoring path. The
  browser's own speech recognizer is not simulated.
- **Speech recognition time is not in the latency numbers**, because transcripts are cached.
- **Production recordings are longer.** The app keeps about two seconds of trailing silence, so
  more real recordings take the chunked path than benchmark recordings do (about 12% against 5%
  of dev recordings).
- **The experts disagree with each other**, as the human reference above shows, so a perfect
  score is not possible.

## Reproduce

Run these from `backend/`, with the dataset downloaded and the caches built. The steps for that,
including Windows setup, are in `backend/tests/benchmark/README.md`.

```bash
python -m tests.benchmark.run --name final --workers 8
```

```bash
python -m tests.benchmark.run --name original --workers 8 --flag WWAI_GT_ANCHORED_ALIGNMENT=0 --flag WWAI_LEGACY_WORD_SCORING=1 --flag WWAI_SINGLE_PREPROCESS=0 --flag WWAI_SOFT_QUALITY_GATES=0 --flag WWAI_LEGACY_FEEDBACK=1 --flag WWAI_LEGACY_SENTENCE_CLEANING=1
```

```bash
python -m tests.benchmark.compare tests/benchmark/results/original_dev.json tests/benchmark/results/final_dev.json
```

The test-half numbers come from the same commands with `--half test`, `WWAI_BENCH_UNLOCK_TEST=1`
and a `--reason`, at commit `a276b21`. Their summaries are committed in
`backend/tests/benchmark/results/`. The speed table comes from
`python tests/benchmark/speed_interleaved.py 2 tests/benchmark/results/interleaved_speed.json`.

## Ideas for next steps

- It might be worth colouring the words on the practice screen with the same rule the spoken
  feedback uses. Each word now carries a `clear_mistake` flag for that. Today the screen colours a
  word red at a PER of 0.5 or more, so a child can see a red word and hear "Great job!".
- The soft quality gates produce a gentle hint ("try somewhere quieter") that the app does not
  show yet. Showing it may help children whose recordings are noisy.
- Catching a single wrong sound in a short word probably needs a better acoustic signal than the
  current phoneme recognizer, which marks almost half of correctly read words with at least one
  error. A model fine-tuned on children's speech, or confidence scores from forced alignment, may
  deserve a look.
- A small set of real children's recordings, labelled for reading mistakes, would test what this
  dataset cannot, namely whether the feedback helps beginning readers.
- The browser loads the phoneme model without pinning its revision, while the server pins it.
  Pinning both would keep the two paths from drifting apart.
