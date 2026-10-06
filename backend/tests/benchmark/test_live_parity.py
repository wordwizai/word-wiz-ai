"""Replaying the real dev cache gives exactly what a live ONNX run gives on the same clips.

The clips are 8 from smoke_dev, spread evenly over the sorted subset, plus the longest dev
clips. process_audio_array chunks audio over 8 seconds and then makes several model calls per
clip, so the long clips are what show that replay follows the chunk loop and not only a single
call. The word side of both runs comes from the cache, because a live Deepgram call is not
allowed.

Skips when the dataset, the dev baseline cache or the ONNX model is not available. Anything
else fails, including a stale cache entry and a mismatch between replay and the live run.
"""

import os
import unittest
from unittest import mock

from tests.benchmark import common
from tests.benchmark import pipeline as PL

N_SMOKE = 8
N_LONG = 4
MIN_LONG = 3
#: process_audio_array chunks audio longer than this many seconds.
CHUNK_SECONDS = 8.0


def spread(items, n):
    """n items spread evenly over a list, first and last included (all of them if n is not smaller)."""
    if len(items) <= n:
        return list(items)
    return [items[round(i * (len(items) - 1) / (n - 1))] for i in range(n)]


def audio_seconds(path):
    import soundfile as sf

    info = sf.info(path)
    return info.frames / info.samplerate


def pick_clips(dev, smoke):
    """The clips to compare, sorted by utt id, and the audio length in seconds of every dev clip.

    The long clips are the N_LONG longest dev clips over CHUNK_SECONDS, chosen by audio length
    alone. Whether they really make several model calls is checked against the cache afterwards.
    """
    seconds = {clip.utt_id: audio_seconds(clip.wav_path) for clip in dev}
    smoke_pick = spread(sorted(smoke, key=lambda c: c.utt_id), N_SMOKE)
    long_clips = sorted(
        (c for c in dev if seconds[c.utt_id] > CHUNK_SECONDS),
        key=lambda c: (-seconds[c.utt_id], c.utt_id),
    )[:N_LONG]
    chosen = {c.utt_id: c for c in smoke_pick + long_clips}
    return [chosen[utt_id] for utt_id in sorted(chosen)], {c.utt_id for c in long_clips}, seconds


class CountingSession:
    """Wraps the real ONNX session and counts the run() calls the pipeline makes on it."""

    def __init__(self, inner):
        self.inner = inner
        self.calls = 0

    def get_inputs(self):
        return self.inner.get_inputs()

    def run(self, *args, **kwargs):
        self.calls += 1
        return self.inner.run(*args, **kwargs)


class TestLiveParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from tests.benchmark.dataset import find_dataset_root, load_clips
        from tests.benchmark.replay import load_processor
        from tests.benchmark.stage_cache import cache_dir
        from core.phoneme_extractor_onnx import PhonemeExtractorONNX

        cls.directory = cache_dir("dev", "baseline")
        if not os.path.isdir(cls.directory):
            raise unittest.SkipTest(f"dev baseline cache not found at {cls.directory}")
        try:
            root = find_dataset_root()
        except FileNotFoundError as exc:
            raise unittest.SkipTest(f"speechocean762 not available: {exc}")

        # Outside any try, so a corrupt dataset or a bad subset file fails instead of skipping.
        dev = load_clips("dev", root=root)
        smoke = load_clips("dev", "smoke_dev", root=root)
        cls.clips, cls.long_ids, cls.seconds = pick_clips(dev, smoke)
        if len(cls.long_ids) < MIN_LONG:
            raise AssertionError(f"only {len(cls.long_ids)} dev clips are longer than {CHUNK_SECONDS} s")

        try:
            with common.quiet():
                cls.live = PhonemeExtractorONNX()
                cls.processor = load_processor()
        except OSError as exc:
            raise unittest.SkipTest(f"ONNX model or processor not available: {exc}")

        # The baseline cache was recorded with single preprocessing and soft quality gates off.
        # Both are on by default now, so the live run has to switch them off to be comparable.
        front_end = mock.patch.dict(os.environ, {"WWAI_SINGLE_PREPROCESS": "0", "WWAI_SOFT_QUALITY_GATES": "0"})
        front_end.start()
        cls.addClassCleanup(front_end.stop)

    def test_long_clips_take_the_chunked_path(self):
        from tests.benchmark.replay import CacheEntry

        for utt_id in sorted(self.long_ids):
            with self.subTest(utt=utt_id):
                self.assertGreater(self.seconds[utt_id], CHUNK_SECONDS)
                entry = CacheEntry(self.directory, utt_id)
                self.assertGreater(len(entry.phoneme_calls), 1, f"{utt_id} made one model call, so it was not chunked")

    def test_replay_equals_live(self):
        from tests.benchmark.replay import CacheEntry, ReplayPhonemeExtractor, ReplayWordExtractor

        for clip in self.clips:
            with self.subTest(utt=clip.utt_id, seconds=round(self.seconds[clip.utt_id], 1)):
                audio = PL.load_audio(clip.wav_path)

                counting = CountingSession(self.live.session)
                self.live.session = counting
                try:
                    live = PL.analyze_clip(
                        audio, clip.text, self.live, ReplayWordExtractor(CacheEntry(self.directory, clip.utt_id))
                    )
                finally:
                    self.live.session = counting.inner

                entry = CacheEntry(self.directory, clip.utt_id)
                replay_phonemes = ReplayPhonemeExtractor(entry, self.processor)
                replay = PL.analyze_clip(audio, clip.text, replay_phonemes, ReplayWordExtractor(entry))

                # A harness failure shows up as the same "unexpected:" outcome on both sides.
                self.assertFalse((live.error_type or "").startswith("unexpected:"), live.error)
                self.assertEqual(replay.to_dict(), live.to_dict())

                if clip.utt_id in self.long_ids:
                    self.assertEqual(live.status, "ok")
                    self.assertGreater(counting.calls, 1, "the live run made one model call, so it was not chunked")
                if live.status == "ok":
                    # Replay used every recorded call, and the live run made exactly that many.
                    self.assertEqual(counting.calls, len(entry.phoneme_calls))
                    self.assertEqual(replay_phonemes.session._next, len(entry.phoneme_calls))


if __name__ == "__main__":
    unittest.main()
