"""Interleaved latency: original behaviour (all kill switches) vs final defaults, same process.

Each clip runs once per configuration per repeat, and the order within the pair alternates
clip by clip, so heat and turbo drift land on both sides equally. speed.py measures one
configuration per process, and two of those runs back to back mostly measured how much the
machine had warmed up (the second run was 15 to 30% slower whichever went second). This is
what BENCHMARK.md's speed table comes from. "original" is every kill switch on, which the
benchmark verified gives the original scoring exactly. Live ONNX, cached Deepgram transcripts
(the baseline cache for original, the single-preprocess plus soft-gates cache for final). Run
it from backend/ with nothing else heavy running.

    python tests/benchmark/speed_interleaved.py [repeats] [out.json]
"""
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.getcwd())
repeats = int(sys.argv[1]) if len(sys.argv) > 1 else 2
out_path = sys.argv[2] if len(sys.argv) > 2 else None

ORIGINAL = {
    "WWAI_GT_ANCHORED_ALIGNMENT": "0", "WWAI_LEGACY_WORD_SCORING": "1",
    "WWAI_SINGLE_PREPROCESS": "0", "WWAI_SOFT_QUALITY_GATES": "0",
    "WWAI_LEGACY_FEEDBACK": "1", "WWAI_LEGACY_SENTENCE_CLEANING": "1",
}
CONFIGS = {"original": (ORIGINAL, "baseline"),
           "final": ({}, "WWAI_SINGLE_PREPROCESS=1+WWAI_SOFT_QUALITY_GATES=1")}

from tests.benchmark import common  # noqa: E402
from tests.benchmark.dataset import load_clips  # noqa: E402
from tests.benchmark.pipeline import analyze_clip, load_audio  # noqa: E402
from tests.benchmark.replay import CacheEntry, ReplayWordExtractor  # noqa: E402
from core.phoneme_extractor_onnx import PhonemeExtractorONNX  # noqa: E402

for k in ORIGINAL:
    os.environ.pop(k, None)


def set_config(name):
    flags, _ = CONFIGS[name]
    for k in ORIGINAL:
        os.environ.pop(k, None)
    os.environ.update(flags)


subset = set(open("tests/benchmark/subsets/speed_dev.txt").read().split())
clips = [c for c in load_clips("dev") if c.utt_id in subset]
with common.quiet():
    ex = PhonemeExtractorONNX()
audios = {c.utt_id: load_audio(c.wav_path) for c in clips}
dirs = {name: os.path.join(common.cache_root(), "dev", cache) for name, (_, cache) in CONFIGS.items()}

for name in CONFIGS:  # warm up both
    set_config(name)
    analyze_clip(audios[clips[0].utt_id], clips[0].text, ex,
                 ReplayWordExtractor(CacheEntry(dirs[name], clips[0].utt_id), check_inputs=False))

times = {name: [[] for _ in range(repeats)] for name in CONFIGS}
oks = {name: [set() for _ in range(repeats)] for name in CONFIGS}
t0 = time.perf_counter()
for rep in range(repeats):
    for i, clip in enumerate(clips):
        order = ["original", "final"] if (i + rep) % 2 == 0 else ["final", "original"]
        for name in order:
            set_config(name)
            words = ReplayWordExtractor(CacheEntry(dirs[name], clip.utt_id), check_inputs=False)
            s = time.perf_counter()
            outcome = analyze_clip(audios[clip.utt_id], clip.text, ex, words)
            dt = time.perf_counter() - s
            if outcome.status == "ok":
                times[name][rep].append((clip.utt_id, dt))
                oks[name][rep].add(clip.utt_id)

result = {"clips": len(clips), "repeats": repeats, "wall_s": time.perf_counter() - t0}
for name in CONFIGS:
    p50 = np.mean([np.percentile([t for _, t in r], 50) for r in times[name]])
    p95 = np.mean([np.percentile([t for _, t in r], 95) for r in times[name]])
    result[name] = {"p50_s": float(p50), "p95_s": float(p95), "clips_ok": min(len(o) for o in oks[name])}
# Same-clip comparison: only clips that succeeded under both, every repeat.
both = set.intersection(*oks["original"], *oks["final"])
for name in CONFIGS:
    sel = [[t for u, t in r if u in both] for r in times[name]]
    result[name]["p50_common_s"] = float(np.mean([np.percentile(r, 50) for r in sel]))
    result[name]["p95_common_s"] = float(np.mean([np.percentile(r, 95) for r in sel]))
result["common_clips"] = len(both)
result["p95_ratio"] = result["final"]["p95_s"] / result["original"]["p95_s"]
result["p95_ratio_common"] = result["final"]["p95_common_s"] / result["original"]["p95_common_s"]
result["p50_ratio_common"] = result["final"]["p50_common_s"] / result["original"]["p50_common_s"]
print(json.dumps(result, indent=1))
if out_path:
    json.dump(result, open(out_path, "w"), indent=1)
