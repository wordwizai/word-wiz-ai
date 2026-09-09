"""
Tests for pause-preserving audio chunking (WWAI_CHUNK_PRESERVE_PAUSES).

The legacy chunker concatenates ONLY the non-silent intervals returned by
librosa.effects.split, so every inter-word pause is thrown away before the audio
ever reaches wav2vec2 / Deepgram. These tests pin down both behaviors:

  * flag OFF -> byte-identical to the legacy implementation (pauses dropped)
  * flag ON  -> contiguous slices, pauses retained, overlapping seams deduplicated

Run with (from the repo root):

    PYTHONIOENCODING=utf-8 \
      C:/Users/bruce/Coding/word-wiz-ai/backend/venv/Scripts/python.exe \
      -m unittest tests.test_audio_chunking_pauses -v

(from inside backend/)

No network, no models, no audio files: the signal is synthesized in-process.
"""

import contextlib
import io
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import librosa

from core import audio_chunking
from core.audio_chunking import (
    chunk_audio_at_silence,
    merge_chunk_results,
    should_use_chunking,
    plan_chunk_boundaries,
)


SR = 16000
FLAG = "WWAI_CHUNK_PRESERVE_PAUSES"
ENV_KEYS = [
    FLAG,
    "WWAI_CHUNK_MAX_DURATION",
    "WWAI_CHUNK_MIN_DURATION",
    "WWAI_CHUNK_OVERLAP_SECONDS",
    "WWAI_CHUNK_THRESHOLD_SECONDS",
    "WWAI_CHUNK_DEDUPE_MAX_WORDS",
]


def quiet(fn, *args, **kwargs):
    """Call fn, swallowing the module's progress prints."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        result = fn(*args, **kwargs)
    return result


def make_speech_like_audio(sr=SR, seed=1234):
    """
    Synthesize a ~12s 'sentence': 16 tone bursts ('words') separated by silence,
    with a longer pause after every 4th word ('phrase breaks').

    Returns (audio, word_spans, pause_spans) where the spans are (start_s, end_s).
    """
    rng = np.random.default_rng(seed)

    word_duration = 0.40
    short_pause = 0.30
    long_pause = 0.65
    lead = 0.10
    n_words = 16

    pieces = []
    word_spans = []
    pause_spans = []
    t = 0.0

    def add_silence(duration, record=False):
        nonlocal t
        n = int(round(duration * sr))
        # Tiny noise floor so "silence" is not literally zeros - makes the
        # array-equality assertions below meaningful.
        pieces.append(rng.normal(0.0, 1e-4, n).astype(np.float32))
        if record:
            pause_spans.append((t, t + n / sr))
        t += n / sr

    def add_word(index):
        nonlocal t
        n = int(round(word_duration * sr))
        tt = np.arange(n) / sr
        f0 = 140.0 + 8.0 * index
        sig = (
            np.sin(2 * np.pi * f0 * tt)
            + 0.5 * np.sin(2 * np.pi * 2 * f0 * tt)
            + 0.25 * np.sin(2 * np.pi * 3 * f0 * tt)
        )
        # Simple attack/decay envelope so bursts look speech-ish to librosa.
        env = np.hanning(n) ** 0.5
        pieces.append((0.3 * sig * env).astype(np.float32))
        word_spans.append((t, t + n / sr))
        t += n / sr

    add_silence(lead)
    for i in range(n_words):
        add_word(i)
        if i == n_words - 1:
            add_silence(lead, record=False)
        elif (i + 1) % 4 == 0:
            add_silence(long_pause, record=True)
        else:
            add_silence(short_pause, record=True)

    audio = np.concatenate(pieces).astype(np.float32)
    return audio, word_spans, pause_spans


def legacy_reference_chunks(audio, sr=SR, max_chunk_duration=7, top_db=30):
    """Independent re-implementation of the pre-flag behavior, for comparison."""
    intervals = librosa.effects.split(audio, top_db=top_db)
    chunks, metadata = [], []
    current_start, current_samples, current_duration = 0, [], 0

    for start, end in intervals:
        segment = audio[start:end]
        segment_duration = len(segment) / sr
        if current_duration + segment_duration > max_chunk_duration:
            if current_samples:
                chunk_audio = np.concatenate(current_samples)
                chunks.append(chunk_audio)
                metadata.append({
                    "start_time": current_start,
                    "end_time": current_start + current_duration,
                    "duration": current_duration,
                    "num_samples": len(chunk_audio),
                })
            current_start = start / sr
            current_samples = [segment]
            current_duration = segment_duration
        else:
            current_samples.append(segment)
            current_duration += segment_duration

    if current_samples:
        chunk_audio = np.concatenate(current_samples)
        chunks.append(chunk_audio)
        metadata.append({
            "start_time": current_start,
            "end_time": current_start + current_duration,
            "duration": current_duration,
            "num_samples": len(chunk_audio),
        })
    return chunks, metadata


class ChunkingTestBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audio, cls.word_spans, cls.pause_spans = make_speech_like_audio()
        cls.duration = len(cls.audio) / SR

    def setUp(self):
        self._saved_env = {k: os.environ.get(k) for k in ENV_KEYS}
        for k in ENV_KEYS:
            os.environ.pop(k, None)

    def tearDown(self):
        for k, v in self._saved_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def enable_flag(self, **overrides):
        os.environ[FLAG] = "true"
        for k, v in overrides.items():
            os.environ[k] = str(v)


class TestLegacyBehaviorUnchanged(ChunkingTestBase):
    """With the flag unset, nothing at all may change."""

    def test_flag_off_matches_legacy_reference_exactly(self):
        chunks, metadata = quiet(chunk_audio_at_silence, self.audio, SR)
        ref_chunks, ref_metadata = legacy_reference_chunks(self.audio, SR)

        self.assertEqual(len(chunks), len(ref_chunks))
        self.assertEqual(metadata, ref_metadata)
        for got, expected in zip(chunks, ref_chunks):
            np.testing.assert_array_equal(got, expected)

    def test_flag_off_drops_the_pauses(self):
        chunks, metadata = quiet(chunk_audio_at_silence, self.audio, SR)
        total = sum(len(c) for c in chunks) / SR
        lost = self.duration - total

        print(
            f"\n[legacy, flag OFF] input {self.duration:.3f}s -> "
            f"{len(chunks)} chunks totalling {total:.3f}s "
            f"({lost:.3f}s of pause discarded, {100 * lost / self.duration:.1f}%)"
        )

        # The whole point: the legacy path loses real time (all of it silence).
        self.assertGreater(lost, 1.0)

    def test_flag_off_merge_does_not_deduplicate(self):
        # Legacy merge is a plain concatenation, duplicates included.
        merged_ph, merged_w = merge_chunk_results(
            [[["k", "æ", "t"]], [["k", "æ", "t"], ["s", "æ", "t"]]],
            [["cat"], ["cat", "sat"]],
            [{"overlap_start_seconds": 0.0}, {"overlap_start_seconds": 0.5}],
        )
        self.assertEqual(merged_w, ["cat", "cat", "sat"])
        self.assertEqual(len(merged_ph), 3)

    def test_flag_off_threshold_is_eight_seconds(self):
        self.assertTrue(should_use_chunking(np.zeros(int(8.5 * SR)), SR, threshold_seconds=8))
        self.assertFalse(should_use_chunking(np.zeros(int(7.5 * SR)), SR, threshold_seconds=8))


class TestPausesArePreserved(ChunkingTestBase):
    def test_total_duration_matches_original(self):
        # Forced to 5s so the ~12s fixture actually splits; at the shipped
        # default (12s max / 15s threshold) this input is a single pass.
        self.enable_flag(WWAI_CHUNK_MAX_DURATION=5)
        chunks, metadata = quiet(chunk_audio_at_silence, self.audio, SR)
        self.assertGreater(len(chunks), 1, "12s input at a 5s max should be split")

        overlap = sum(m["overlap_start_seconds"] for m in metadata)
        total = sum(len(c) for c in chunks) / SR

        # Every sample is covered exactly once, apart from the deliberate overlap.
        self.assertAlmostEqual(total - overlap, self.duration, places=6)
        print(
            f"\n[pause-preserving, flag ON] input {self.duration:.3f}s -> "
            f"{len(chunks)} chunks totalling {total:.3f}s "
            f"({overlap:.3f}s of that is intentional overlap; "
            f"{self.duration - (total - overlap):.6f}s lost)"
        )

    def test_chunks_reassemble_into_the_original_signal(self):
        self.enable_flag(WWAI_CHUNK_MAX_DURATION=5)
        chunks, metadata = quiet(chunk_audio_at_silence, self.audio, SR)

        rebuilt = []
        for chunk, meta in zip(chunks, metadata):
            lead = int(round(meta["overlap_start_seconds"] * SR))
            rebuilt.append(chunk[lead:])
        rebuilt = np.concatenate(rebuilt)

        self.assertEqual(len(rebuilt), len(self.audio))
        np.testing.assert_array_equal(rebuilt, self.audio)

    def test_pauses_survive_at_expected_timestamps(self):
        self.enable_flag(WWAI_CHUNK_MAX_DURATION=5)
        chunks, metadata = quiet(chunk_audio_at_silence, self.audio, SR)

        half_window = 0.08  # seconds either side of the pause midpoint
        for pause_start, pause_end in self.pause_spans:
            mid = (pause_start + pause_end) / 2.0
            found = False
            for chunk, meta in zip(chunks, metadata):
                if meta["start_time"] <= mid - half_window and meta["end_time"] >= mid + half_window:
                    local = int(round((mid - meta["start_time"]) * SR))
                    window = chunk[local - int(half_window * SR): local + int(half_window * SR)]
                    self.assertGreater(len(window), 0)
                    self.assertLess(
                        float(np.max(np.abs(window))), 0.01,
                        f"expected silence at {mid:.3f}s, chunk starting {meta['start_time']:.3f}s",
                    )
                    found = True
                    break
            self.assertTrue(found, f"pause at {mid:.3f}s is not inside any chunk")

    def test_legacy_path_destroys_those_same_pauses(self):
        # Control: the same probe run against the legacy output finds no silence,
        # because the pauses were removed before the chunk was assembled.
        chunks, _ = quiet(chunk_audio_at_silence, self.audio, SR)
        silent_windows = 0
        probe = int(0.16 * SR)
        for chunk in chunks:
            for i in range(0, len(chunk) - probe, probe):
                if float(np.max(np.abs(chunk[i:i + probe]))) < 0.01:
                    silent_windows += 1
        self.assertEqual(
            silent_windows, 0,
            "legacy chunks unexpectedly contain silence - test signal may be wrong",
        )


class TestOverlapAndSeams(ChunkingTestBase):
    def test_phoneme_sized_window_on_a_boundary_is_never_split(self):
        """A 60ms event straddling a cut must survive whole inside one chunk."""
        self.enable_flag(WWAI_CHUNK_OVERLAP_SECONDS=0.5, WWAI_CHUNK_MAX_DURATION=5)
        chunks, metadata = quiet(chunk_audio_at_silence, self.audio, SR)
        boundaries = plan_chunk_boundaries(self.audio, SR)

        self.assertGreater(len(boundaries), 2, "need at least one interior cut")

        half = int(0.03 * SR)  # 60ms total - roughly one phoneme
        for idx, cut in enumerate(boundaries[1:-1], start=1):
            straddling = self.audio[cut - half: cut + half]
            chunk = chunks[idx]
            lead = int(round(metadata[idx]["overlap_start_seconds"] * SR))
            self.assertGreaterEqual(lead, half, "overlap must cover a phoneme")
            recovered = chunk[lead - half: lead + half]
            np.testing.assert_array_equal(
                recovered, straddling,
                err_msg=f"event straddling cut at sample {cut} was not intact in chunk {idx + 1}",
            )

    def test_seam_words_are_deduplicated_once(self):
        self.enable_flag()
        chunk_phonemes = [
            [["ð", "ə"], ["k", "æ", "t"], ["s", "æ", "t"]],
            [["s", "æ", "t"], ["d", "aʊ", "n"]],
        ]
        chunk_words = [["the", "cat", "sat"], ["Sat", "down"]]
        chunk_metadata = [
            {"start_time": 0.0, "end_time": 6.0, "duration": 6.0,
             "num_samples": 96000, "overlap_start_seconds": 0.0},
            {"start_time": 5.5, "end_time": 9.0, "duration": 3.5,
             "num_samples": 56000, "overlap_start_seconds": 0.5},
        ]

        merged_ph, merged_w = quiet(
            merge_chunk_results, chunk_phonemes, chunk_words, chunk_metadata
        )

        self.assertEqual(merged_w, ["the", "cat", "sat", "down"])
        self.assertEqual(len(merged_ph), len(merged_w))
        self.assertEqual(merged_ph[2], ["s", "æ", "t"])
        self.assertEqual(merged_ph[3], ["d", "aʊ", "n"])

    def test_seam_word_is_not_lost_when_there_is_no_duplicate(self):
        self.enable_flag()
        merged_ph, merged_w = quiet(
            merge_chunk_results,
            [[["k", "æ", "t"]], [["d", "ɔ", "g"]]],
            [["cat"], ["dog"]],
            [{"overlap_start_seconds": 0.0}, {"overlap_start_seconds": 0.5}],
        )
        self.assertEqual(merged_w, ["cat", "dog"])
        self.assertEqual(merged_ph, [["k", "æ", "t"], ["d", "ɔ", "g"]])

    def test_no_dedupe_when_phonemes_and_words_are_misaligned(self):
        """Dropping entries in lockstep is only safe when the lists line up."""
        self.enable_flag()
        merged_ph, merged_w = quiet(
            merge_chunk_results,
            [[["k", "æ", "t"]], [["s"], ["æ"], ["t"]]],
            [["cat"], ["cat", "sat"]],
            [{"overlap_start_seconds": 0.0}, {"overlap_start_seconds": 0.5}],
        )
        self.assertEqual(merged_w, ["cat", "cat", "sat"])

    def test_empty_input_still_returns_empty_pair(self):
        self.enable_flag()
        self.assertEqual(merge_chunk_results([], [], []), ([], []))


class TestMetadataContract(ChunkingTestBase):
    REQUIRED = ("start_time", "end_time", "duration", "num_samples")

    def _assert_contract(self, chunks, metadata):
        self.assertEqual(len(chunks), len(metadata))
        for chunk, meta in zip(chunks, metadata):
            for key in self.REQUIRED:
                self.assertIn(key, meta)
            self.assertIsInstance(meta["start_time"], (int, float))
            self.assertIsInstance(meta["end_time"], (int, float))
            self.assertIsInstance(meta["duration"], (int, float))
            self.assertIsInstance(meta["num_samples"], int)
            self.assertNotIsInstance(meta["num_samples"], bool)
            self.assertEqual(meta["num_samples"], len(chunk))
            self.assertAlmostEqual(meta["duration"], len(chunk) / SR, places=6)
            self.assertGreater(meta["end_time"], meta["start_time"])
            # process_audio.py does `metadata['duration'] += ...` etc.
            meta["duration"] += 0.1
            meta["end_time"] += 0.1
            meta["num_samples"] += 1

    def test_metadata_contract_flag_off(self):
        chunks, metadata = quiet(chunk_audio_at_silence, self.audio, SR)
        self._assert_contract(chunks, metadata)

    def test_metadata_contract_flag_on(self):
        self.enable_flag()
        chunks, metadata = quiet(chunk_audio_at_silence, self.audio, SR)
        self._assert_contract(chunks, metadata)


class TestThreshold(ChunkingTestBase):
    def test_flag_on_raises_threshold_to_fifteen_seconds(self):
        self.enable_flag()
        # The caller passes threshold_seconds=8 positionally; the flag overrides it.
        self.assertFalse(should_use_chunking(np.zeros(int(12.0 * SR)), SR, threshold_seconds=8))
        self.assertTrue(should_use_chunking(np.zeros(int(15.5 * SR)), SR, threshold_seconds=8))

    def test_threshold_is_configurable(self):
        self.enable_flag(WWAI_CHUNK_THRESHOLD_SECONDS=20)
        self.assertFalse(should_use_chunking(np.zeros(int(19.0 * SR)), SR, threshold_seconds=8))
        self.assertTrue(should_use_chunking(np.zeros(int(21.0 * SR)), SR, threshold_seconds=8))

    def test_bad_env_value_falls_back_to_default(self):
        self.enable_flag(WWAI_CHUNK_THRESHOLD_SECONDS="not-a-number")
        self.assertTrue(quiet(should_use_chunking, np.zeros(int(16.0 * SR)), SR, 8))
        self.assertFalse(quiet(should_use_chunking, np.zeros(int(14.0 * SR)), SR, 8))

    def test_max_chunk_duration_is_configurable(self):
        self.enable_flag(WWAI_CHUNK_MAX_DURATION=4)
        chunks, metadata = quiet(chunk_audio_at_silence, self.audio, SR)
        for meta in metadata:
            # max + min slack for the tail chunk
            self.assertLessEqual(meta["duration"], 4 + 1.0 + 0.5 + 1e-6)
        self.assertGreaterEqual(len(chunks), 3)

    def test_short_audio_is_a_single_chunk(self):
        self.enable_flag()
        short = self.audio[: int(3.0 * SR)]
        chunks, metadata = quiet(chunk_audio_at_silence, short, SR)
        self.assertEqual(len(chunks), 1)
        np.testing.assert_array_equal(chunks[0], short)

    def test_no_chunk_is_short_enough_to_trigger_the_caller_merge(self):
        """
        process_audio.py merges any chunk under 0.3s into the previous one, which
        would concatenate two overlapping slices and lose the seam metadata. The
        min-chunk guard must make that branch unreachable.
        """
        for max_duration in (3, 5, 7, 12):
            with self.subTest(max_duration=max_duration):
                self.enable_flag(WWAI_CHUNK_MAX_DURATION=max_duration)
                chunks, metadata = quiet(chunk_audio_at_silence, self.audio, SR)
                for meta in metadata:
                    self.assertGreaterEqual(meta["duration"], 0.3)

    def test_empty_audio_is_handled(self):
        self.enable_flag()
        chunks, metadata = quiet(chunk_audio_at_silence, np.zeros(0, dtype=np.float32), SR)
        self.assertEqual(chunks, [])
        self.assertEqual(metadata, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
