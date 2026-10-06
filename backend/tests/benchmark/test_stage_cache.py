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


class TestModelInputSha(unittest.TestCase):
    def test_deterministic_and_sensitive_to_values_dtype_and_shape(self):
        a = np.arange(12, dtype=np.float32).reshape(1, 12)
        self.assertEqual(SC.model_input_sha(a), SC.model_input_sha(a.copy()))
        self.assertNotEqual(SC.model_input_sha(a), SC.model_input_sha(a * 2))
        self.assertNotEqual(SC.model_input_sha(a), SC.model_input_sha(a.reshape(12, 1)))  # same bytes
        self.assertNotEqual(SC.model_input_sha(a), SC.model_input_sha(a.astype(np.float64)))


class TestRecordingSession(unittest.TestCase):
    def test_records_the_input_hash_and_the_logits(self):
        inner = mock.Mock()
        inner.run.return_value = [np.ones((1, 3, 4), dtype=np.float64)]
        session = SC.RecordingSession(inner)
        values = np.zeros((1, 50), dtype=np.float32)
        outputs = session.run(None, {"input_values": values})
        self.assertIs(outputs, inner.run.return_value)
        inner.run.assert_called_once_with(None, {"input_values": values})
        self.assertEqual(session.calls, [{"input_sha": SC.model_input_sha(values), "logits_key": "logits_0"}])
        self.assertEqual(session.logits[0].dtype, np.float32)

    def test_records_and_reraises_a_session_error(self):
        inner = mock.Mock()
        inner.run.side_effect = MemoryError("out of memory")
        session = SC.RecordingSession(inner)
        with self.assertRaises(MemoryError):
            session.run(None, {"input_values": np.zeros((1, 50), dtype=np.float32)})
        call = session.calls[0]
        self.assertEqual((call["error_type"], call["error"], call["is_value_error"]),
                         ("MemoryError", "out of memory", False))
        self.assertNotIn("logits_key", call)
        self.assertEqual(session.logits, [])

    def test_get_inputs_comes_from_the_real_session(self):
        inner = mock.Mock()
        self.assertIs(SC.RecordingSession(inner).get_inputs(), inner.get_inputs.return_value)


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


_WORDS_OK = [{"input_sha": "x", "words": ["a", "b"]}]
_OUTAGE = [{"input_sha": "x", "words": [],
            "asr_failure": {"code": "upstream.timeout", "category": "upstream_transient", "retryable": True}}]


def _outcome(status="ok", error_type=None):
    return {"status": status, "error_type": error_type, "error": None if status == "ok" else "e"}


class TestEntryNeedsRetry(unittest.TestCase):
    def test_a_session_error_that_is_not_a_value_error_is_retried(self):
        # Memory and runtime failures in the ONNX session are usually transient.
        meta = {
            "phoneme_calls": [{"input_sha": "x", "error_type": "Fail", "error": "oom", "is_value_error": False}],
            "word_calls": _WORDS_OK,
            "outcome": _outcome("rejected", "ReplayedError"),
        }
        self.assertTrue(SC.entry_needs_retry(meta))

    def test_an_unexpected_outcome_is_retried(self):
        meta = {"phoneme_calls": [], "word_calls": _WORDS_OK, "outcome": _outcome("rejected", "unexpected:KeyError")}
        self.assertTrue(SC.entry_needs_retry(meta))

    def test_a_word_error_is_retried(self):
        self.assertTrue(SC.entry_needs_retry({"phoneme_calls": [], "word_calls": _OUTAGE, "outcome": _outcome()}))

    def test_a_session_value_error_is_kept(self):
        meta = {
            "phoneme_calls": [{"input_sha": "x", "error_type": "ValueError", "error": "bad", "is_value_error": True}],
            "word_calls": _WORDS_OK,
            "outcome": _outcome("rejected", "ValueError"),
        }
        self.assertFalse(SC.entry_needs_retry(meta))

    def test_a_genuine_empty_transcript_is_kept(self):
        meta = {
            "phoneme_calls": [{"input_sha": "x", "logits_key": "logits_0"}],
            "word_calls": [{"input_sha": "x", "words": [],
                            "asr_failure": {"code": "audio.empty", "category": "empty_audio", "retryable": False}}],
            "outcome": _outcome("rejected", "ValueError"),
        }
        self.assertFalse(SC.entry_needs_retry(meta))

    def test_an_ok_entry_is_kept(self):
        meta = {"phoneme_calls": [{"input_sha": "x", "logits_key": "logits_0"}], "word_calls": _WORDS_OK,
                "outcome": _outcome()}
        self.assertFalse(SC.entry_needs_retry(meta))
        self.assertFalse(SC.entry_needs_retry({}))


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

    def test_a_later_successful_load_clears_an_earlier_failure(self):
        SC._init_error = "ValueError: no key"
        with (
            mock.patch.object(SC, "_load_deepgram_key"),
            mock.patch("core.phoneme_extractor_onnx.PhonemeExtractorONNX", mock.MagicMock()),
            mock.patch("core.word_extractor.WordExtractorOnline", mock.MagicMock()),
        ):
            SC._init_worker()
        self.assertIsNone(SC._init_error)

    def test_failed_model_load_is_reported_by_the_task_instead_of_hanging_the_pool(self):
        with (
            mock.patch.object(SC, "_load_deepgram_key"),
            mock.patch("core.phoneme_extractor_onnx.PhonemeExtractorONNX", mock.MagicMock()),
            mock.patch("core.word_extractor.WordExtractorOnline", side_effect=ValueError("no key")),
        ):
            SC._init_worker()  # must not raise: the error is reported by the task, with its cause
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
        with mock.patch.object(SC, "record_clip", return_value={"utt_id": "u"}) as record:
            self.assertEqual(SC._record_task(("u", "w", "t", "d")), {"utt_id": "u"})
        record.assert_called_once_with("u", "w", "t", "d", phoneme, words)


class TestBuildFailsFast(unittest.TestCase):
    def test_missing_deepgram_key_stops_before_the_pool_starts(self):
        clip = types.SimpleNamespace(utt_id="u1", wav_path="u1.wav", text="hi")
        with (
            tempfile.TemporaryDirectory() as tmp,
            mock.patch.dict(os.environ, {"WWAI_BENCH_CACHE_DIR": tmp}),
            mock.patch.object(SC, "_load_deepgram_key"),
            mock.patch.object(SC, "write_meta"),
            mock.patch.object(SC, "ProcessPoolExecutor") as pool,
            mock.patch("tests.benchmark.dataset.load_clips", return_value=[clip]),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            os.environ.pop("DEEPGRAM_KEY", None)
            with self.assertRaises(SystemExit) as ctx:
                SC.build("dev", "baseline", {}, workers=1)
        self.assertIn("DEEPGRAM_KEY", str(ctx.exception))
        pool.assert_not_called()


class TestRecordAll(unittest.TestCase):
    """The pool is a spawn ProcessPoolExecutor: a worker that dies hard breaks it instead of hanging."""

    def _run(self, record_task, todo):
        with (
            mock.patch.object(SC, "ProcessPoolExecutor", U.InlineExecutor),
            mock.patch.object(SC, "_init_worker") as init_worker,
            mock.patch.object(SC, "_record_task", side_effect=record_task),
            mock.patch.dict(os.environ),
        ):
            os.environ.pop("PYTHONIOENCODING", None)
            self.init_worker = init_worker
            try:
                return list(SC._record_all(todo, 3))
            finally:
                self.assertEqual(init_worker.call_count, 1)

    def test_uses_a_spawn_process_pool_with_the_worker_initializer(self):
        todo = [("u1", "w", "t", "d"), ("u2", "w", "t", "d")]
        entries = self._run(lambda task: {"utt_id": task[0]}, todo)
        self.assertEqual(sorted(e["utt_id"] for e in entries), ["u1", "u2"])
        pool = U.InlineExecutor.last
        self.assertEqual(pool.max_workers, 3)
        self.assertEqual(pool.mp_context.get_start_method(), "spawn")
        self.assertIs(pool.initializer, self.init_worker)  # looked up at call time, so the patched one
        # Under WWAI_BENCH_VERBOSE with redirected output, an emoji print in a worker would raise
        # UnicodeEncodeError, a ValueError that would be scored as a rejection.
        self.assertEqual(pool.pythonioencoding, "utf-8")

    def test_a_failed_task_stops_the_run_and_cancels_what_is_left(self):
        def record_task(task):
            if task[0] == "u2":
                raise RuntimeError("benchmark worker could not load its models: OSError: x")
            return {"utt_id": task[0]}

        with self.assertRaises(RuntimeError):
            self._run(record_task, [("u1", "w", "t", "d"), ("u2", "w", "t", "d"), ("u3", "w", "t", "d")])
        self.assertIn(True, U.InlineExecutor.last.shutdowns)


class TestWorkerDiesHard(unittest.TestCase):
    def test_a_broken_pool_stops_the_build_with_a_clear_message(self):
        from concurrent.futures.process import BrokenProcessPool

        def entries():
            yield _entry("u0")
            raise BrokenProcessPool("A process in the process pool was terminated abruptly")

        with (
            tempfile.TemporaryDirectory() as tmp,
            mock.patch.dict(os.environ, {"WWAI_BENCH_CACHE_DIR": tmp, "DEEPGRAM_KEY": "test-key"}),
            mock.patch.object(SC, "_load_deepgram_key"),
            mock.patch.object(SC, "write_meta"),
            mock.patch("tests.benchmark.dataset.load_clips", return_value=[_clip("u0"), _clip("u1")]),
            mock.patch.object(SC, "_record_all", return_value=entries()),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            with self.assertRaises(SystemExit) as ctx:
                SC.build("dev", "baseline", {}, workers=2)
        self.assertIn("worker process died", str(ctx.exception))
        self.assertIn("run the same command again", str(ctx.exception))


def _clip(utt_id):
    return types.SimpleNamespace(utt_id=utt_id, wav_path=f"{utt_id}.wav", text="hi there")


def _entry(utt_id, status="ok", error_type=None, word_calls=None, phoneme_calls=None):
    return {
        "utt_id": utt_id,
        "phoneme_calls": phoneme_calls or [],
        "word_calls": _WORDS_OK if word_calls is None else word_calls,
        "outcome": _outcome(status, error_type),
    }


class TestBuild(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        for patcher in (
            mock.patch.dict(os.environ, {"WWAI_BENCH_CACHE_DIR": self.tmp.name, "DEEPGRAM_KEY": "test-key"}),
            mock.patch.object(SC, "_load_deepgram_key"),
            mock.patch.object(SC, "write_meta"),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            patcher.__enter__()
            self.addCleanup(patcher.__exit__, None, None, None)
        self.directory = SC.cache_dir("dev", "baseline")
        os.makedirs(self.directory)

    def _cache(self, meta):
        with open(os.path.join(self.directory, f"{meta['utt_id']}.json"), "w", encoding="utf-8") as fh:
            json.dump(meta, fh)

    def _build(self, clips, entries, **kwargs):
        with (
            mock.patch("tests.benchmark.dataset.load_clips", return_value=clips),
            mock.patch.object(SC, "_record_all", return_value=(e for e in entries)) as record_all,
        ):
            summary = SC.build("dev", "baseline", {}, workers=2, **kwargs)
        return summary, record_all

    def test_summary_counts_error_types_and_lists_the_clips_to_retry(self):
        entries = [
            _entry("u0"),
            _entry("u1", "rejected", "EmptyAudioError"),
            _entry("u2", "rejected", "unexpected:Fail"),
            _entry("u3", "rejected", "EmptyAudioError", word_calls=_OUTAGE),
        ]
        summary, _ = self._build([_clip(e["utt_id"]) for e in entries], entries)
        self.assertEqual(summary["recorded"], 4)
        self.assertEqual(summary["statuses"], {"ok": 1, "rejected": 3})
        self.assertEqual(summary["error_types"], {"EmptyAudioError": 2, "unexpected:Fail": 1})
        self.assertEqual(summary["needs_retry"], ["u2", "u3"])
        self.assertEqual(summary["word_errors"], ["u3"])

    def test_stops_when_deepgram_fails_for_each_of_the_first_20_clips(self):
        consumed, closed = [], []

        def entries():
            try:
                for i in range(25):
                    consumed.append(i)
                    yield _entry(f"u{i:02d}", "rejected", "ValueError", word_calls=_OUTAGE)
            finally:
                closed.append(True)

        with (
            mock.patch("tests.benchmark.dataset.load_clips", return_value=[_clip(f"u{i:02d}") for i in range(25)]),
            mock.patch.object(SC, "_record_all", return_value=entries()),
        ):
            with self.assertRaises(SystemExit) as ctx:
                SC.build("dev", "baseline", {}, workers=2)
        self.assertEqual(str(ctx.exception),
                         "Deepgram failed for every one of the first 20 clips; check the key and balance")
        self.assertEqual(len(consumed), 20)
        self.assertEqual(closed, [True])  # the pool is shut down, not left running

    def test_keeps_going_when_one_of_the_first_20_clips_has_words(self):
        entries = [_entry(f"u{i:02d}", word_calls=_WORDS_OK if i == 7 else _OUTAGE) for i in range(25)]
        summary, _ = self._build([_clip(e["utt_id"]) for e in entries], entries)
        self.assertEqual(summary["recorded"], 25)
        self.assertEqual(len(summary["needs_retry"]), 24)

    def test_cached_entries_that_need_a_retry_are_reported_without_retry_errors(self):
        self._cache(_entry("u0", word_calls=_OUTAGE))
        self._cache(_entry("u1"))
        summary, record_all = self._build([_clip("u0"), _clip("u1"), _clip("u2")], [_entry("u2")])
        todo = record_all.call_args.args[0]
        self.assertEqual([task[0] for task in todo], ["u2"])
        self.assertEqual(summary["needs_retry"], ["u0"])

    def test_retry_errors_records_again_only_what_is_worth_retrying(self):
        session_error = [{"input_sha": "x", "error_type": "Fail", "error": "oom", "is_value_error": False}]
        session_value_error = [{"input_sha": "x", "error_type": "ValueError", "error": "bad", "is_value_error": True}]
        self._cache(_entry("u0", "rejected", "unexpected:Fail", phoneme_calls=session_error))
        self._cache(_entry("u1", "rejected", "ValueError", phoneme_calls=session_value_error))
        self._cache(_entry("u2"))
        summary, record_all = self._build([_clip("u0"), _clip("u1"), _clip("u2")], [_entry("u0")],
                                          retry_errors=True)
        todo = record_all.call_args.args[0]
        self.assertEqual([task[0] for task in todo], ["u0"])
        self.assertEqual(summary["needs_retry"], [])


class TestMainExitCode(unittest.TestCase):
    def _main(self, summary):
        with (
            mock.patch.object(SC.common, "dotenv_wwai_keys", return_value=[]),
            mock.patch.object(SC, "build", return_value=summary),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            return SC.main(["--half", "dev"])

    def test_returns_1_while_clips_need_a_retry(self):
        self.assertEqual(self._main({"needs_retry": ["u1"], "word_errors": []}), 1)

    def test_returns_0_when_nothing_needs_a_retry(self):
        self.assertEqual(self._main({"needs_retry": [], "word_errors": []}), 0)


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
        entry = SC.record_clip(
            "000020022", self.wav, U.SAMPLE_TEXT, self.cache, U.fake_onnx_extractor(self.processor), U.FakeWords()
        )
        with open(os.path.join(self.cache, "000020022.json"), encoding="utf-8") as fh:
            meta = json.load(fh)
        self.assertEqual(meta, entry)  # record_clip returns what it wrote
        self.assertEqual(meta["utt_id"], "000020022")
        self.assertEqual(meta["outcome"], {"status": "ok", "error_type": None, "error": None})
        self.assertRegex(meta["git_sha"], r"^([0-9a-f]{40}(-dirty)?|unknown)$")
        self.assertFalse(SC.entry_needs_retry(meta))
        self.assertEqual(len(meta["phoneme_calls"]), 1)
        self.assertEqual(meta["phoneme_calls"][0]["logits_key"], "logits_0")
        self.assertEqual(meta["word_calls"][0]["words"], U.SAMPLE_TEXT.split())
        with np.load(os.path.join(self.cache, "000020022.npz")) as data:
            self.assertEqual(data["logits_0"].dtype, np.float32)

    def test_the_shared_extractor_is_not_modified(self):
        extractor = U.fake_onnx_extractor(self.processor)
        session = extractor.session
        SC.record_clip("000020022", self.wav, U.SAMPLE_TEXT, self.cache, extractor, U.FakeWords())
        self.assertIs(extractor.session, session)
        self.assertEqual(session.calls, 1)  # the recording session passed the call through

    def test_word_errors_are_recorded(self):
        SC.record_clip(
            "000020022", self.wav, U.SAMPLE_TEXT, self.cache, U.fake_onnx_extractor(self.processor), _FailingWords()
        )
        with open(os.path.join(self.cache, "000020022.json"), encoding="utf-8") as fh:
            meta = json.load(fh)
        self.assertEqual(meta["outcome"]["status"], "rejected")
        self.assertEqual(meta["outcome"]["error_type"], "unexpected:TimeoutError")
        self.assertEqual(meta["word_calls"][0]["error_type"], "TimeoutError")
        self.assertIs(meta["word_calls"][0]["is_value_error"], False)
        self.assertTrue(SC.entry_has_word_error(meta))

    def test_value_error_is_flagged_so_replay_can_rebuild_it(self):
        SC.record_clip(
            "000020022", self.wav, U.SAMPLE_TEXT, self.cache, U.fake_onnx_extractor(self.processor), _ValueErrorWords()
        )
        with open(os.path.join(self.cache, "000020022.json"), encoding="utf-8") as fh:
            meta = json.load(fh)
        self.assertEqual(meta["word_calls"][0]["error_type"], "ValueError")
        self.assertIs(meta["word_calls"][0]["is_value_error"], True)

    def _record(self, words):
        SC.record_clip(
            "000020022", self.wav, U.SAMPLE_TEXT, self.cache, U.fake_onnx_extractor(self.processor), words
        )
        with open(os.path.join(self.cache, "000020022.json"), encoding="utf-8") as fh:
            return json.load(fh)

    def test_retryable_failure_is_recorded_and_the_entry_is_retried(self):
        meta = self._record(_OutageWords())
        call = meta["word_calls"][0]
        self.assertEqual(call["words"], [])
        self.assertEqual(call["asr_failure"], {"code": "upstream.timeout", "category": "upstream", "retryable": True})
        self.assertTrue(SC.entry_has_word_error(meta))
        self.assertTrue(SC.entry_needs_retry(meta))

    def test_non_retryable_empty_transcript_is_kept(self):
        meta = self._record(_EmptyTranscriptWords())
        call = meta["word_calls"][0]
        self.assertEqual(call["words"], [])
        self.assertIs(call["asr_failure"]["retryable"], False)
        self.assertFalse(SC.entry_has_word_error(meta))
        self.assertFalse(SC.entry_needs_retry(meta))

    def test_a_clean_call_records_no_asr_failure(self):
        meta = self._record(U.FakeWords())
        self.assertNotIn("asr_failure", meta["word_calls"][0])

    def test_the_last_final_failure_wins(self):
        meta = self._record(_TwoFailuresWords())
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
        meta = self._record(_LoggingThenRaisingWords())
        self.assertEqual(logger.handlers, before)
        self.assertEqual(meta["word_calls"][0]["error_type"], "TimeoutError")
        self.assertTrue(SC.entry_has_word_error(meta))

    def test_gates_are_not_applied_when_recording(self):
        from core import request_audio

        with mock.patch.object(request_audio, "gate_audio", side_effect=request_audio.AudioRejected("no")):
            entry = SC.record_clip(
                "000020022", self.wav, U.SAMPLE_TEXT, self.cache, U.fake_onnx_extractor(self.processor), U.FakeWords()
            )
        self.assertEqual(entry["outcome"]["status"], "ok")  # a gate that would reject was never consulted


if __name__ == "__main__":
    unittest.main()
