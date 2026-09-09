"""
Tests for the ASR error taxonomy and the Deepgram -> local wav2vec2 fallback
chain (``core/errors.py`` + ``core/word_extractor.py``).

Every network call is mocked -- no request ever reaches Deepgram -- and the
local ``WordExtractor`` class is patched out in ``setUp`` so no 1.2GB model is
ever downloaded or loaded. ``time.sleep`` is patched too so the retry backoff
does not slow the suite down.

Run from the ``backend/`` directory:

    PYTHONIOENCODING=utf-8 <python> -m unittest tests.test_word_extractor_fallback -v
"""

import json
import logging
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import requests

from core import word_extractor as we
from core.errors import (
    CATEGORY_EMPTY_AUDIO,
    CATEGORY_UPSTREAM_AUTH,
    CATEGORY_UPSTREAM_QUOTA,
    CATEGORY_UPSTREAM_TRANSIENT,
    EmptyAudioError,
    InternalPipelineError,
    UpstreamAuthError,
    UpstreamQuotaError,
    UpstreamTransientError,
    to_error_frame,
)


def _audio(seconds=1.0, sr=16000):
    return np.full(int(seconds * sr), 0.1, dtype=np.float32)


def _http_response(status_code=200, payload=None, text=""):
    resp = mock.MagicMock()
    resp.status_code = status_code
    resp.text = text
    resp.json.return_value = payload or {}
    if status_code >= 400:
        resp.raise_for_status.side_effect = requests.exceptions.HTTPError(
            f"{status_code} Client Error", response=resp
        )
    else:
        resp.raise_for_status.return_value = None
    return resp


def _transcript_payload(transcript):
    return {"results": {"channels": [{"alternatives": [{"transcript": transcript}]}]}}


class _FakeLocalExtractor:
    """Stand-in for the local wav2vec2 model. Async, like the real one."""

    def __init__(self, words=("the", "cat", "sat")):
        self.words = list(words)
        self.calls = 0

    async def extract_words(self, audio, sampling_rate=16000):
        self.calls += 1
        return list(self.words)


class WordExtractorTestBase(unittest.TestCase):
    def setUp(self):
        # Deepgram key must exist for the constructor; it is never used because
        # requests.post is always mocked.
        self.env_patch = mock.patch.dict(
            os.environ,
            {"DEEPGRAM_KEY": "test-key-not-real"},
            clear=False,
        )
        self.env_patch.start()
        self.addCleanup(self.env_patch.stop)

        for flag in (we.FLAG_ASR_FALLBACK, we.FLAG_ASR_TYPED_ERRORS):
            os.environ.pop(flag, None)

        # Hard guarantee: nothing in this suite may construct the real model.
        model_guard = mock.patch.object(
            we,
            "WordExtractor",
            side_effect=AssertionError("real WordExtractor must never be constructed in tests"),
        )
        model_guard.start()
        self.addCleanup(model_guard.stop)

        sleep_patch = mock.patch.object(we.time, "sleep", return_value=None)
        sleep_patch.start()
        self.addCleanup(sleep_patch.stop)

        we.reset_local_word_extractor()
        self.addCleanup(we.reset_local_word_extractor)

        we._request_context.set({})
        self.addCleanup(we._request_context.set, {})

    def enable_fallback(self):
        os.environ[we.FLAG_ASR_FALLBACK] = "true"

    def enable_typed_errors_only(self):
        os.environ[we.FLAG_ASR_TYPED_ERRORS] = "true"

    def make_extractor(self, local_extractor=None):
        factory = (lambda: local_extractor) if local_extractor is not None else None
        return we.WordExtractorOnline(local_extractor_factory=factory)


# --------------------------------------------------------------------------- #
# Failure classification (flag ON)
# --------------------------------------------------------------------------- #


class TestFailureClassification(WordExtractorTestBase):
    def setUp(self):
        super().setUp()
        self.enable_typed_errors_only()
        self.extractor = self.make_extractor()

    def test_timeout_raises_retryable_transient_error(self):
        with mock.patch("requests.post", side_effect=requests.exceptions.Timeout("boom")):
            with self.assertRaises(UpstreamTransientError) as ctx:
                self.extractor.extract_words(_audio(), max_retries=1)

        err = ctx.exception
        self.assertTrue(err.retryable)
        self.assertFalse(err.alert_operator)
        self.assertEqual(err.category, CATEGORY_UPSTREAM_TRANSIENT)
        self.assertNotIsInstance(err, EmptyAudioError)
        # The child must not be told the recording was silent.
        self.assertNotIn("no speech", err.user_message.lower())
        self.assertIn("not yours", err.user_message.lower())
        # The operator gets the precise detail.
        self.assertIn("timed out", err.operator_detail)
        self.assertIn("deepgram", err.operator_detail.lower())

    def test_http_401_is_auth_error_and_not_a_timeout(self):
        with mock.patch("requests.post", return_value=_http_response(401, text="bad key")):
            with self.assertRaises(UpstreamAuthError) as ctx:
                self.extractor.extract_words(_audio(), max_retries=2)

        err = ctx.exception
        self.assertFalse(err.retryable)
        self.assertTrue(err.alert_operator)
        self.assertEqual(err.category, CATEGORY_UPSTREAM_AUTH)
        self.assertNotIsInstance(err, UpstreamTransientError)
        self.assertNotIsInstance(err, EmptyAudioError)
        self.assertIn("401", err.operator_detail)

    def test_http_403_is_auth_error(self):
        with mock.patch("requests.post", return_value=_http_response(403)):
            with self.assertRaises(UpstreamAuthError):
                self.extractor.extract_words(_audio(), max_retries=1)

    def test_http_429_is_quota_error(self):
        with mock.patch("requests.post", return_value=_http_response(429, text="rate limited")):
            with self.assertRaises(UpstreamQuotaError) as ctx:
                self.extractor.extract_words(_audio(), max_retries=1)

        err = ctx.exception
        self.assertEqual(err.category, CATEGORY_UPSTREAM_QUOTA)
        self.assertFalse(err.retryable)
        self.assertTrue(err.alert_operator)
        self.assertNotIsInstance(err, UpstreamAuthError)

    def test_http_500_is_transient(self):
        with mock.patch("requests.post", return_value=_http_response(503)):
            with self.assertRaises(UpstreamTransientError) as ctx:
                self.extractor.extract_words(_audio(), max_retries=1)
        self.assertTrue(ctx.exception.retryable)

    def test_http_400_is_our_bug_not_theirs(self):
        with mock.patch("requests.post", return_value=_http_response(400, text="bad audio")):
            with self.assertRaises(InternalPipelineError) as ctx:
                self.extractor.extract_words(_audio(), max_retries=1)
        self.assertTrue(ctx.exception.alert_operator)

    def test_non_retryable_status_skips_the_retry_loop(self):
        post = mock.MagicMock(return_value=_http_response(401))
        with mock.patch("requests.post", post):
            with self.assertRaises(UpstreamAuthError):
                self.extractor.extract_words(_audio(), max_retries=2)
        self.assertEqual(post.call_count, 1, "401 must not be retried")

    def test_transient_status_still_retries(self):
        post = mock.MagicMock(return_value=_http_response(500))
        with mock.patch("requests.post", post):
            with self.assertRaises(UpstreamTransientError):
                self.extractor.extract_words(_audio(), max_retries=2)
        self.assertEqual(post.call_count, 3)

    def test_successful_call_with_empty_transcript_is_empty_audio(self):
        with mock.patch(
            "requests.post", return_value=_http_response(200, _transcript_payload(""))
        ):
            with self.assertRaises(EmptyAudioError) as ctx:
                self.extractor.extract_words(_audio(), max_retries=1)

        err = ctx.exception
        self.assertEqual(err.category, CATEGORY_EMPTY_AUDIO)
        self.assertTrue(err.user_actionable)
        self.assertFalse(err.alert_operator)
        self.assertNotIsInstance(err, UpstreamTransientError)
        self.assertIn("could not hear", err.user_message.lower())

    def test_zero_length_audio_is_empty_audio(self):
        with mock.patch("requests.post") as post:
            with self.assertRaises(EmptyAudioError):
                self.extractor.extract_words(b"", max_retries=0)
        post.assert_not_called()

    def test_success_contract_is_unchanged(self):
        with mock.patch(
            "requests.post",
            return_value=_http_response(200, _transcript_payload("The cat, sat!")),
        ):
            words = self.extractor.extract_words(_audio(), max_retries=0)
        self.assertEqual(words, ["the", "cat", "sat"])

    def test_only_empty_audio_is_a_valueerror(self):
        """
        process_audio.py's chunk loop does `except ValueError` to skip silent
        chunks. Silence must keep being skippable; an outage must not be.
        """
        with mock.patch(
            "requests.post", return_value=_http_response(200, _transcript_payload(""))
        ):
            with self.assertRaises(ValueError):
                self.extractor.extract_words(_audio(), max_retries=0)

        with mock.patch("requests.post", return_value=_http_response(401)):
            with self.assertRaises(UpstreamAuthError) as ctx:
                self.extractor.extract_words(_audio(), max_retries=0)
        self.assertNotIsInstance(ctx.exception, ValueError)

    def test_user_payload_does_not_leak_operator_detail(self):
        with mock.patch("requests.post", return_value=_http_response(401, text="secret body")):
            with self.assertRaises(UpstreamAuthError) as ctx:
                self.extractor.extract_words(_audio(), max_retries=0)

        frame = to_error_frame(ctx.exception)
        blob = json.dumps(frame)
        self.assertEqual(frame["type"], "error")
        self.assertNotIn("secret body", blob)
        self.assertNotIn("deepgram", blob.lower())
        self.assertNotIn("401", blob)
        self.assertEqual(frame["data"]["code"], "upstream.auth")
        self.assertFalse(frame["data"]["retryable"])


# --------------------------------------------------------------------------- #
# Fallback chain
# --------------------------------------------------------------------------- #


class TestFallbackChain(WordExtractorTestBase):
    def test_fallback_fires_on_timeout_when_flag_on(self):
        self.enable_fallback()
        local = _FakeLocalExtractor(["the", "cat", "sat"])
        extractor = self.make_extractor(local)

        with mock.patch("requests.post", side_effect=requests.exceptions.Timeout("boom")):
            words = extractor.extract_words(_audio(), max_retries=1)

        self.assertEqual(words, ["the", "cat", "sat"])
        self.assertEqual(local.calls, 1)

    def test_fallback_fires_on_auth_error(self):
        self.enable_fallback()
        local = _FakeLocalExtractor(["hello", "world"])
        extractor = self.make_extractor(local)

        with mock.patch("requests.post", return_value=_http_response(401)):
            words = extractor.extract_words(_audio(), max_retries=1)

        self.assertEqual(words, ["hello", "world"])
        self.assertEqual(local.calls, 1)

    def test_local_model_is_loaded_once_and_only_when_needed(self):
        self.enable_fallback()
        local = _FakeLocalExtractor()
        factory = mock.MagicMock(return_value=local)
        extractor = we.WordExtractorOnline(local_extractor_factory=factory)

        with mock.patch("requests.post", side_effect=requests.exceptions.Timeout("boom")):
            extractor.extract_words(_audio(), max_retries=0)
            extractor.extract_words(_audio(), max_retries=0)

        self.assertEqual(factory.call_count, 1, "model must be lazily loaded exactly once")
        self.assertEqual(local.calls, 2)

    def test_no_fallback_for_genuinely_empty_transcript(self):
        self.enable_fallback()
        factory = mock.MagicMock(
            side_effect=AssertionError("must not load the local model for silent audio")
        )
        extractor = we.WordExtractorOnline(local_extractor_factory=factory)

        with mock.patch(
            "requests.post", return_value=_http_response(200, _transcript_payload(""))
        ):
            with self.assertRaises(EmptyAudioError):
                extractor.extract_words(_audio(), max_retries=0)

        factory.assert_not_called()

    def test_fallback_failure_preserves_original_classification(self):
        self.enable_fallback()
        factory = mock.MagicMock(side_effect=RuntimeError("out of memory"))
        extractor = we.WordExtractorOnline(local_extractor_factory=factory)

        with mock.patch("requests.post", return_value=_http_response(401)):
            with self.assertRaises(UpstreamAuthError) as ctx:
                extractor.extract_words(_audio(), max_retries=0)

        self.assertIn("401", ctx.exception.operator_detail)

    def test_fallback_returning_nothing_is_reported_as_empty_audio(self):
        self.enable_fallback()
        local = _FakeLocalExtractor([])
        extractor = self.make_extractor(local)

        with mock.patch("requests.post", side_effect=requests.exceptions.Timeout("boom")):
            with self.assertRaises(EmptyAudioError) as ctx:
                extractor.extract_words(_audio(), max_retries=0)

        self.assertTrue(ctx.exception.context.get("degraded"))

    def test_typed_errors_without_fallback_fails_fast(self):
        self.enable_typed_errors_only()  # WWAI_ASR_FALLBACK stays unset
        factory = mock.MagicMock(side_effect=AssertionError("fallback must not run"))
        extractor = we.WordExtractorOnline(local_extractor_factory=factory)

        with mock.patch("requests.post", side_effect=requests.exceptions.Timeout("boom")):
            with self.assertRaises(UpstreamTransientError):
                extractor.extract_words(_audio(), max_retries=0)

        factory.assert_not_called()


# --------------------------------------------------------------------------- #
# Flag OFF must reproduce today's behaviour exactly
# --------------------------------------------------------------------------- #


class TestFlagOffLegacyBehaviour(WordExtractorTestBase):
    def setUp(self):
        super().setUp()
        self.factory = mock.MagicMock(
            side_effect=AssertionError("fallback must not run with the flag off")
        )
        self.extractor = we.WordExtractorOnline(local_extractor_factory=self.factory)

    def test_flags_default_off(self):
        self.assertFalse(we.asr_fallback_enabled())
        self.assertFalse(we.asr_typed_errors_enabled())

    def test_timeout_returns_empty_list(self):
        with mock.patch("requests.post", side_effect=requests.exceptions.Timeout("boom")):
            self.assertEqual(self.extractor.extract_words(_audio(), max_retries=2), [])
        self.factory.assert_not_called()

    def test_auth_error_returns_empty_list_and_still_retries(self):
        post = mock.MagicMock(return_value=_http_response(401))
        with mock.patch("requests.post", post):
            self.assertEqual(self.extractor.extract_words(_audio(), max_retries=2), [])
        self.assertEqual(post.call_count, 3, "legacy behaviour retried every status")
        self.factory.assert_not_called()

    def test_quota_error_returns_empty_list(self):
        with mock.patch("requests.post", return_value=_http_response(429)):
            self.assertEqual(self.extractor.extract_words(_audio(), max_retries=1), [])

    def test_empty_transcript_returns_empty_list(self):
        with mock.patch(
            "requests.post", return_value=_http_response(200, _transcript_payload(""))
        ):
            self.assertEqual(self.extractor.extract_words(_audio(), max_retries=1), [])

    def test_zero_length_audio_returns_empty_list(self):
        with mock.patch("requests.post") as post:
            self.assertEqual(self.extractor.extract_words(b"", max_retries=0), [])
        post.assert_not_called()

    def test_unexpected_exception_returns_empty_list(self):
        with mock.patch("requests.post", side_effect=RuntimeError("kaboom")):
            self.assertEqual(self.extractor.extract_words(_audio(), max_retries=1), [])

    def test_success_path_identical(self):
        with mock.patch(
            "requests.post",
            return_value=_http_response(200, _transcript_payload("The cat, sat!")),
        ):
            self.assertEqual(
                self.extractor.extract_words(_audio(), max_retries=0), ["the", "cat", "sat"]
            )


# --------------------------------------------------------------------------- #
# Structured logging
# --------------------------------------------------------------------------- #


class TestStructuredLogging(WordExtractorTestBase):
    def _records(self, cm):
        out = []
        for line in cm.output:
            _, _, tail = line.partition("asr.word_extraction ")
            if tail:
                out.append(json.loads(tail))
        return out

    def test_success_record_names_the_extractor_and_path(self):
        extractor = self.make_extractor()
        we.set_asr_request_context(request_id="req-abc", session_id=42)
        with mock.patch(
            "requests.post",
            return_value=_http_response(200, _transcript_payload("the cat sat")),
        ):
            with self.assertLogs("core.word_extractor", level=logging.INFO) as cm:
                extractor.extract_words(_audio(), max_retries=0)

        rec = self._records(cm)[0]
        self.assertEqual(rec["request_id"], "req-abc")
        self.assertEqual(rec["session_id"], 42)
        self.assertEqual(rec["path"], "online")
        self.assertEqual(rec["extractor"], "deepgram:nova-2")
        self.assertEqual(rec["outcome"], "success")
        self.assertFalse(rec["fallback_fired"])
        self.assertEqual(rec["word_count"], 3)
        self.assertIn("total_ms", rec)
        self.assertIn("upstream_ms", rec)

    def test_failure_record_carries_the_classification(self):
        extractor = self.make_extractor()
        self.enable_typed_errors_only()
        with mock.patch("requests.post", return_value=_http_response(429)):
            with self.assertLogs("core.word_extractor", level=logging.INFO) as cm:
                with self.assertRaises(UpstreamQuotaError):
                    extractor.extract_words(_audio(), max_retries=0)

        rec = self._records(cm)[0]
        self.assertEqual(rec["outcome"], "failed")
        self.assertEqual(rec["final_failure"]["code"], "upstream.quota")
        self.assertEqual(rec["final_failure"]["category"], CATEGORY_UPSTREAM_QUOTA)
        self.assertTrue(rec["final_failure"]["alert_operator"])
        self.assertEqual(rec["http_status"], 429)
        self.assertIn("attempts", rec)

    def test_fallback_record_says_a_fallback_fired(self):
        self.enable_fallback()
        local = _FakeLocalExtractor(["a", "b"])
        extractor = self.make_extractor(local)

        with mock.patch("requests.post", side_effect=requests.exceptions.Timeout("boom")):
            with self.assertLogs("core.word_extractor", level=logging.INFO) as cm:
                extractor.extract_words(_audio(), max_retries=0)

        rec = self._records(cm)[0]
        self.assertTrue(rec["fallback_fired"])
        self.assertTrue(rec["degraded"])
        self.assertEqual(rec["path"], "local_fallback")
        self.assertTrue(rec["extractor"].startswith("wav2vec2:"))
        self.assertEqual(rec["outcome"], "success_degraded")
        self.assertEqual(rec["primary_failure"]["category"], CATEGORY_UPSTREAM_TRANSIENT)
        self.assertIn("fallback_ms", rec)


if __name__ == "__main__":
    unittest.main(verbosity=2)
