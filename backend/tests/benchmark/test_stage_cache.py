import contextlib
import io
import json
import logging
import os
import tempfile
import types
import unittest
from unittest import mock

import numpy as np

from tests.benchmark import stage_cache as SC
from tests.benchmark import testutil as U


class TestAudioSha(unittest.TestCase):
    def test_deterministic_and_rate_sensitive(self):
        a = np.arange(10, dtype=np.float32)
        self.assertEqual(SC.audio_sha(a, 16000), SC.audio_sha(a.copy(), 16000))
        self.assertNotEqual(SC.audio_sha(a, 16000), SC.audio_sha(a, 8000))
        self.assertNotEqual(SC.audio_sha(a, 16000), SC.audio_sha(a * 2, 16000))


class TestEntryHasWordError(unittest.TestCase):
    def test_error_type_counts(self):
        self.assertTrue(SC.entry_has_word_error({"word_calls": [{"input_sha": "x", "error_type": "TimeoutError"}]}))

    def test_empty_or_missing_words_without_a_failure_are_kept(self):
        # Deepgram genuinely returns an empty transcript for some young children's speech.
        self.assertFalse(SC.entry_has_word_error({"word_calls": [{"input_sha": "x", "words": []}]}))
        self.assertFalse(SC.entry_has_word_error({"word_calls": [{"input_sha": "x", "words": None}]}))
        self.assertFalse(SC.entry_has_word_error({"word_calls": [{"input_sha": "x"}]}))

    def test_empty_words_after_a_retryable_failure_count(self):
        failure = {"code": "upstream.timeout", "category": "upstream", "retryable": True}
        self.assertTrue(SC.entry_has_word_error(
            {"word_calls": [{"input_sha": "x", "words": [], "asr_failure": failure}]}))
        self.assertTrue(SC.entry_has_word_error(
            {"word_calls": [{"input_sha": "x", "words": None, "asr_failure": failure}]}))

    def test_empty_words_after_a_non_retryable_failure_are_kept(self):
        failure = {"code": "audio.empty", "category": "empty_audio", "retryable": False}
        self.assertFalse(SC.entry_has_word_error(
            {"word_calls": [{"input_sha": "x", "words": [], "asr_failure": failure}]}))

    def test_words_present_is_not_an_error(self):
        self.assertFalse(SC.entry_has_word_error({"word_calls": [{"input_sha": "x", "words": ["a", "b"]}]}))
        failure = {"code": "upstream.timeout", "category": "upstream", "retryable": True}
        self.assertFalse(SC.entry_has_word_error(
            {"word_calls": [{"input_sha": "x", "words": ["a"], "asr_failure": failure}]}))

    def test_no_word_calls_is_not_an_error(self):
        self.assertFalse(SC.entry_has_word_error({"word_calls": []}))
        self.assertFalse(SC.entry_has_word_error({}))


class _FailingWords:
    def extract_words(self, audio, sampling_rate=16000, **_kwargs):
        raise TimeoutError("deepgram slow")


class _ValueErrorWords:
    def extract_words(self, audio, sampling_rate=16000, **_kwargs):
        raise ValueError("nope")


def _log_final_failure(code, category, retryable):
    """Log the way core.word_extractor does when Deepgram fails (ERROR, structured payload)."""
    logging.getLogger("core.word_extractor").error(
        "asr.word_extraction failed",
        extra={"wwai": {"final_failure": {"code": code, "category": category, "retryable": retryable}}},
    )


class _OutageWords:
    """Returns [] after a retryable failure, like WordExtractorOnline with default flags."""

    def extract_words(self, audio, sampling_rate=16000, **_kwargs):
        _log_final_failure("upstream.timeout", "upstream", True)
        return []


class _EmptyTranscriptWords:
    """Returns [] after a failure that is not worth retrying."""

    def extract_words(self, audio, sampling_rate=16000, **_kwargs):
        _log_final_failure("audio.empty", "empty_audio", False)
        return []


class _TwoFailuresWords:
    def extract_words(self, audio, sampling_rate=16000, **_kwargs):
        _log_final_failure("upstream.timeout", "upstream", True)
        _log_final_failure("audio.empty", "empty_audio", False)
        return []


class _LoggingThenRaisingWords:
    def extract_words(self, audio, sampling_rate=16000, **_kwargs):
        _log_final_failure("upstream.timeout", "upstream", True)
        raise TimeoutError("deepgram slow")


class TestWorkerStartup(unittest.TestCase):
    def tearDown(self):
        SC._init_error = None
        SC._models.clear()

    def test_failed_model_load_is_reported_by_the_task_instead_of_hanging_the_pool(self):
        with (
            mock.patch.object(SC, "_load_deepgram_key"),
            mock.patch("core.phoneme_extractor_onnx.PhonemeExtractorONNX", mock.MagicMock()),
            mock.patch("core.word_extractor.WordExtractorOnline", side_effect=ValueError("no key")),
        ):
            SC._init_worker()  # must not raise, or Pool respawns the worker forever
        with self.assertRaises(RuntimeError) as ctx:
            SC._record_task(("u", "w", "t", "d"))
        self.assertIn("no key", str(ctx.exception))
        self.assertIn("ValueError", str(ctx.exception))

    def test_successful_load_leaves_no_error_and_runs_the_clip(self):
        phoneme, words = mock.MagicMock(), mock.MagicMock()
        with (
            mock.patch.object(SC, "_load_deepgram_key"),
            mock.patch("core.phoneme_extractor_onnx.PhonemeExtractorONNX", return_value=phoneme),
            mock.patch("core.word_extractor.WordExtractorOnline", return_value=words),
        ):
            SC._init_worker()
        self.assertIsNone(SC._init_error)
        with mock.patch.object(SC, "record_clip", return_value=("u", "ok", False)) as record:
            self.assertEqual(SC._record_task(("u", "w", "t", "d")), ("u", "ok", False))
        record.assert_called_once_with("u", "w", "t", "d", phoneme, words)


class TestBuildFailsFast(unittest.TestCase):
    def test_missing_deepgram_key_stops_before_the_pool_starts(self):
        clip = types.SimpleNamespace(utt_id="u1", wav_path="u1.wav", text="hi")
        with (
            tempfile.TemporaryDirectory() as tmp,
            mock.patch.dict(os.environ, {"WWAI_BENCH_CACHE_DIR": tmp}),
            mock.patch.object(SC, "_load_deepgram_key"),
            mock.patch.object(SC, "write_meta"),
            mock.patch.object(SC, "get_context") as get_context,
            mock.patch("tests.benchmark.dataset.load_clips", return_value=[clip]),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            os.environ.pop("DEEPGRAM_KEY", None)
            with self.assertRaises(SystemExit) as ctx:
                SC.build("dev", "baseline", {}, workers=1)
        self.assertIn("DEEPGRAM_KEY", str(ctx.exception))
        get_context.assert_not_called()


class TestMainRefusesDotenvFlags(unittest.TestCase):
    def test_returns_2_and_names_the_keys(self):
        err = io.StringIO()
        with (
            mock.patch.object(SC.common, "dotenv_wwai_keys", return_value=["WWAI_X"]),
            mock.patch.object(SC, "build") as build,
            contextlib.redirect_stderr(err),
        ):
            self.assertEqual(SC.main(["--half", "dev"]), 2)
        build.assert_not_called()
        self.assertIn("WWAI_X", err.getvalue())
        self.assertIn("--flag", err.getvalue())


class TestRecordClip(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.processor = U.real_processor_or_skip()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = U.make_temp_dataset(self.tmp.name)
        self.wav = os.path.join(self.root, "WAVE", "SPEAKER0002", "000020022.WAV")
        self.cache = os.path.join(self.tmp.name, "cache")

    def tearDown(self):
        self.tmp.cleanup()

    def test_writes_entry(self):
        utt, status, word_error = SC.record_clip(
            "000020022", self.wav, U.SAMPLE_TEXT, self.cache, U.FakeOnnx(self.processor), U.FakeWords()
        )
        self.assertEqual((utt, status, word_error), ("000020022", "ok", False))
        with open(os.path.join(self.cache, "000020022.json"), encoding="utf-8") as fh:
            meta = json.load(fh)
        self.assertEqual(len(meta["phoneme_calls"]), 1)
        self.assertEqual(meta["phoneme_calls"][0]["logits_key"], "logits_0")
        self.assertEqual(meta["word_calls"][0]["words"], U.SAMPLE_TEXT.split())
        with np.load(os.path.join(self.cache, "000020022.npz")) as data:
            self.assertEqual(data["logits_0"].dtype, np.float32)

    def test_word_errors_are_recorded(self):
        _utt, status, word_error = SC.record_clip(
            "000020022", self.wav, U.SAMPLE_TEXT, self.cache, U.FakeOnnx(self.processor), _FailingWords()
        )
        self.assertEqual((status, word_error), ("rejected", True))
        with open(os.path.join(self.cache, "000020022.json"), encoding="utf-8") as fh:
            meta = json.load(fh)
        self.assertEqual(meta["word_calls"][0]["error_type"], "TimeoutError")
        self.assertIs(meta["word_calls"][0]["is_value_error"], False)
        self.assertTrue(SC.entry_has_word_error(meta))

    def test_value_error_is_flagged_so_replay_can_rebuild_it(self):
        SC.record_clip(
            "000020022", self.wav, U.SAMPLE_TEXT, self.cache, U.FakeOnnx(self.processor), _ValueErrorWords()
        )
        with open(os.path.join(self.cache, "000020022.json"), encoding="utf-8") as fh:
            meta = json.load(fh)
        self.assertEqual(meta["word_calls"][0]["error_type"], "ValueError")
        self.assertIs(meta["word_calls"][0]["is_value_error"], True)

    def _record(self, words):
        result = SC.record_clip(
            "000020022", self.wav, U.SAMPLE_TEXT, self.cache, U.FakeOnnx(self.processor), words
        )
        with open(os.path.join(self.cache, "000020022.json"), encoding="utf-8") as fh:
            return result, json.load(fh)

    def test_retryable_failure_is_recorded_and_the_entry_is_retried(self):
        (_utt, _status, word_error), meta = self._record(_OutageWords())
        call = meta["word_calls"][0]
        self.assertEqual(call["words"], [])
        self.assertEqual(call["asr_failure"], {"code": "upstream.timeout", "category": "upstream", "retryable": True})
        self.assertTrue(SC.entry_has_word_error(meta))
        self.assertTrue(word_error)

    def test_non_retryable_empty_transcript_is_kept(self):
        (_utt, _status, word_error), meta = self._record(_EmptyTranscriptWords())
        call = meta["word_calls"][0]
        self.assertEqual(call["words"], [])
        self.assertIs(call["asr_failure"]["retryable"], False)
        self.assertFalse(SC.entry_has_word_error(meta))
        self.assertFalse(word_error)

    def test_a_clean_call_records_no_asr_failure(self):
        _result, meta = self._record(U.FakeWords())
        self.assertNotIn("asr_failure", meta["word_calls"][0])

    def test_the_last_final_failure_wins(self):
        _result, meta = self._record(_TwoFailuresWords())
        self.assertEqual(meta["word_calls"][0]["asr_failure"]["code"], "audio.empty")
        self.assertFalse(SC.entry_has_word_error(meta))

    def test_the_log_handler_is_removed_afterwards(self):
        logger = logging.getLogger("core.word_extractor")
        before = list(logger.handlers)
        self._record(_OutageWords())
        self.assertEqual(logger.handlers, before)

    def test_the_log_handler_is_removed_when_the_extractor_raises(self):
        logger = logging.getLogger("core.word_extractor")
        before = list(logger.handlers)
        _result, meta = self._record(_LoggingThenRaisingWords())
        self.assertEqual(logger.handlers, before)
        self.assertEqual(meta["word_calls"][0]["error_type"], "TimeoutError")
        self.assertTrue(SC.entry_has_word_error(meta))

    def test_gates_are_not_applied_when_recording(self):
        from core import request_audio

        with mock.patch.object(request_audio, "gate_audio", side_effect=request_audio.AudioRejected("no")):
            _utt, status, _ = SC.record_clip(
                "000020022", self.wav, U.SAMPLE_TEXT, self.cache, U.FakeOnnx(self.processor), U.FakeWords()
            )
        self.assertEqual(status, "ok")  # a gate that would reject was never consulted


if __name__ == "__main__":
    unittest.main()
