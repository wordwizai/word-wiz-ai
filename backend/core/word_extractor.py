# %%
"""
Word (ASR) extraction.

Two implementations live here:

  * ``WordExtractor``        -- local wav2vec2 (``jonatasgrosman/wav2vec2-large-xlsr-53-english``).
                               No network, ~1.2GB of weights, slow cold start.
  * ``WordExtractorOnline``  -- Deepgram nova-2 over HTTPS. This is the one used
                               in production (``PhonemeAssistant`` instantiates it).

Historically every Deepgram failure mode -- timeout, 401, 429, unexpected
exception -- ended in ``return []``. That empty list reached
``process_audio.process_audio_array`` and was turned into
``ValueError("The audio provided has no speech inside")``: a server-side outage
reported to a child as their own fault, and indistinguishable in the logs from
a genuinely silent recording.

This module now:
  1. classifies each failure into the taxonomy in ``core/errors.py``,
  2. can fall back to the local wav2vec2 extractor, and
  3. emits one structured log record per extraction describing which path ran,
     which extractor produced the words, whether a fallback fired, the timings
     and the failure classification.

Everything that changes runtime behaviour is behind ``WWAI_ASR_FALLBACK``,
which defaults to OFF. With the flag unset this file behaves exactly as before
(including the ``return []`` on every failure and the emoji prints); only the
structured log lines are new.
"""

import asyncio
import inspect
import json
import logging
import os
import re
import threading
import time
import uuid
from contextvars import ContextVar
from typing import Any, Callable, Dict, List, Optional

import numpy as np

try:  # normal package import
    from .errors import (
        EmptyAudioError,
        InternalPipelineError,
        UpstreamAuthError,
        UpstreamServiceError,
        UpstreamTransientError,
        WordWizError,
        classify_http_status,
        format_log_line,
        wrap_unexpected,
    )
except ImportError:  # pragma: no cover - supports `python core/word_extractor.py`
    from errors import (  # type: ignore
        EmptyAudioError,
        InternalPipelineError,
        UpstreamAuthError,
        UpstreamServiceError,
        UpstreamTransientError,
        WordWizError,
        classify_http_status,
        format_log_line,
        wrap_unexpected,
    )


logger = logging.getLogger(__name__)

DEEPGRAM_SERVICE = "deepgram"
LOCAL_ASR_MODEL = "jonatasgrosman/wav2vec2-large-xlsr-53-english"


# --------------------------------------------------------------------------- #
# Feature flags
# --------------------------------------------------------------------------- #

#: Master switch. OFF (default) => byte-identical to the previous behaviour.
#: ON  => typed errors are raised AND the local wav2vec2 fallback is attempted.
FLAG_ASR_FALLBACK = "WWAI_ASR_FALLBACK"

#: Optional override so an operator can get the typed errors (fail fast, no
#: 1.2GB model load) without enabling the local fallback. When unset it simply
#: inherits WWAI_ASR_FALLBACK.
FLAG_ASR_TYPED_ERRORS = "WWAI_ASR_TYPED_ERRORS"

_TRUTHY = {"1", "true", "t", "yes", "y", "on"}
_FALSY = {"0", "false", "f", "no", "n", "off"}


def _env_flag(name: str, default: Optional[bool] = None) -> Optional[bool]:
    """Read a tri-state env flag: True / False / None (unset or unparseable)."""
    raw = os.getenv(name)
    if raw is None:
        return default
    value = raw.strip().lower()
    if value in _TRUTHY:
        return True
    if value in _FALSY:
        return False
    return default


def asr_fallback_enabled() -> bool:
    """True when the Deepgram -> local wav2vec2 fallback chain is armed."""
    return bool(_env_flag(FLAG_ASR_FALLBACK, False))


def asr_typed_errors_enabled() -> bool:
    """
    True when failures raise typed errors instead of returning ``[]``.

    Defaults to whatever ``WWAI_ASR_FALLBACK`` says, so the single documented
    flag turns the whole feature on.
    """
    explicit = _env_flag(FLAG_ASR_TYPED_ERRORS, None)
    if explicit is not None:
        return explicit
    return asr_fallback_enabled()


# --------------------------------------------------------------------------- #
# Per-request correlation context (optional; callers may set it)
# --------------------------------------------------------------------------- #

_request_context: ContextVar[Dict[str, Any]] = ContextVar("wwai_asr_request_context", default={})


def set_asr_request_context(**fields: Any) -> None:
    """
    Attach correlation fields (request_id, session_id, user_id, ...) to every
    structured record emitted from this module on the current task/thread.

    Optional: if nothing sets it, a per-call ``request_id`` is generated so log
    lines are still correlatable with each other.
    """
    merged = dict(_request_context.get() or {})
    merged.update({k: v for k, v in fields.items() if v is not None})
    _request_context.set(merged)


def get_asr_request_context() -> Dict[str, Any]:
    return dict(_request_context.get() or {})


def _log_record(event: str, record: Dict[str, Any], level: int = logging.INFO) -> None:
    """Emit one structured line. Logging must never break extraction."""
    try:
        payload = dict(get_asr_request_context())
        payload.update(record)
        logger.log(level, format_log_line(event, payload), extra={"wwai": payload})
    except Exception:  # pragma: no cover
        pass


#: How loudly each terminal outcome is logged.
_OUTCOME_LOG_LEVEL = {
    "success": logging.INFO,
    "success_degraded": logging.WARNING,
    "empty": logging.WARNING,
    "failed": logging.ERROR,
}


def default_model_output_processing(transcription):
    # Filter out our transcription
    filtered_transcription = transcription[0]

    # Remove punctuation and convert to lowercase
    filtered_transcription = re.sub(r"[\W_]+", " ", filtered_transcription).lower()

    # Split by words
    filtered_transcription = filtered_transcription.split()

    return filtered_transcription


class WordExtractor:
    """
    Local wav2vec2 word extractor. No network, but ~1.2GB of weights and a slow
    cold start, so it is only ever constructed lazily (see
    :func:`get_local_word_extractor`).

    ``torch``/``transformers`` are imported inside the methods rather than at
    module scope so that importing ``core.word_extractor`` -- which the online
    path and the tests do -- does not drag in the ML stack.
    """

    def __init__(
        self,
        model_name=LOCAL_ASR_MODEL,
        model_output_processing=default_model_output_processing,
    ):
        from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor

        # Replace with your pre-trained phoneme model identifier from Hugging Face
        self.model_name = model_name
        # Load the phoneme tokenizer and model
        self.processor = Wav2Vec2Processor.from_pretrained(
            self.model_name,
        )

        self.model = Wav2Vec2ForCTC.from_pretrained(self.model_name)

        self.blank_token_id = self.processor.tokenizer.pad_token_id  # for CTC loss

        self.model_output_processing = model_output_processing

    async def extract_words(self, audio, sampling_rate=16000):
        import torch

        # Load the audio file
        # Tokenize the audio file
        input_values = self.processor(
            audio, sampling_rate=sampling_rate, return_tensors="pt"
        ).input_values
        # Simulating asynchronous work for I/O-bound tasks
        await asyncio.sleep(0)  # Placeholder for real async I/O calls

        # retrieve logits from the model
        with torch.no_grad():
            logits = self.model(input_values).logits

        # take the probs
        probs = torch.softmax(logits, dim=-1)
        top2_probs, top2_ids = torch.topk(probs, k=2, dim=-1)

        # take argmax and decode, greedy decoding
        predicted_ids = torch.argmax(logits, dim=-1)

        # Decode the collapsed token sequences to get phoneme transcription strings
        # (The tokenizer's decode method will convert token ids to phoneme symbols)
        transcription = self.processor.batch_decode(predicted_ids)
        transcription = self.model_output_processing(
            transcription
        )  # convert and filter our output

        return transcription


# --------------------------------------------------------------------------- #
# Lazy, process-wide local extractor
# --------------------------------------------------------------------------- #

_local_extractor: Optional[Any] = None
_local_extractor_lock = threading.Lock()
_local_extractor_failed: Optional[BaseException] = None


def get_local_word_extractor(factory: Optional[Callable[[], Any]] = None) -> Any:
    """
    Return the process-wide local ``WordExtractor``, constructing it on first
    use and caching it.

    Loading is ~1.2GB and tens of seconds cold, so it happens exactly once per
    process, is guarded by a lock (two concurrent fallbacks must not load the
    model twice), and a previous load failure is remembered so we do not retry
    a doomed load on every single request.
    """
    global _local_extractor, _local_extractor_failed

    if _local_extractor is not None:
        return _local_extractor

    with _local_extractor_lock:
        if _local_extractor is not None:
            return _local_extractor
        if _local_extractor_failed is not None:
            raise InternalPipelineError(
                f"Local wav2vec2 word extractor previously failed to load: "
                f"{type(_local_extractor_failed).__name__}: {_local_extractor_failed}",
                context={"model": LOCAL_ASR_MODEL},
                cause=_local_extractor_failed,
            )
        build = factory or WordExtractor
        started = time.time()
        try:
            _local_extractor = build()
        except BaseException as exc:  # noqa: BLE001 - remembered and re-raised typed
            _local_extractor_failed = exc
            _log_record(
                "asr.local_model_load",
                {
                    "model": LOCAL_ASR_MODEL,
                    "outcome": "failed",
                    "load_ms": round((time.time() - started) * 1000, 1),
                    "error_class": type(exc).__name__,
                    "error": str(exc),
                },
                level=logging.ERROR,
            )
            raise InternalPipelineError(
                f"Failed to load local wav2vec2 word extractor '{LOCAL_ASR_MODEL}': "
                f"{type(exc).__name__}: {exc}",
                context={"model": LOCAL_ASR_MODEL},
                cause=exc,
            ) from exc
        _log_record(
            "asr.local_model_load",
            {
                "model": LOCAL_ASR_MODEL,
                "outcome": "loaded",
                "load_ms": round((time.time() - started) * 1000, 1),
            },
        )
        return _local_extractor


def preload_local_word_extractor(factory: Optional[Callable[[], Any]] = None) -> bool:
    """
    Operator hook: warm the local model at startup so that a fallback is a
    ~0.5s inference rather than a ~30s cold load in front of a waiting child.

    Returns True if the model is resident afterwards. Never raises.
    """
    try:
        get_local_word_extractor(factory)
        return True
    except Exception:
        return False


def reset_local_word_extractor() -> None:
    """Drop the cached local extractor (used by tests)."""
    global _local_extractor, _local_extractor_failed
    with _local_extractor_lock:
        _local_extractor = None
        _local_extractor_failed = None


def _call_maybe_async(fn: Callable[..., Any], **kwargs: Any) -> Any:
    """
    Call ``fn`` and, if it returns an awaitable, drive it to completion.

    ``WordExtractor.extract_words`` is ``async def`` while
    ``WordExtractorOnline.extract_words`` is synchronous, and callers in
    ``process_audio.py`` invoke both through ``asyncio.to_thread`` -- i.e. from
    a worker thread with no running loop. Without this, falling back would hand
    the caller an un-awaited coroutine instead of a word list.
    """
    result = fn(**kwargs)
    if inspect.isawaitable(result):
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(result)
        # A loop is already running on this thread: run the coroutine on a
        # private loop in a helper thread rather than deadlocking.
        box: Dict[str, Any] = {}

        def _runner() -> None:
            try:
                box["value"] = asyncio.run(result)
            except BaseException as exc:  # noqa: BLE001
                box["error"] = exc

        thread = threading.Thread(target=_runner, daemon=True)
        thread.start()
        thread.join()
        if "error" in box:
            raise box["error"]
        return box.get("value")
    return result


class WordExtractorOnline:
    def __init__(
        self,
        model_output_processing=default_model_output_processing,
        local_extractor_factory: Optional[Callable[[], Any]] = None,
    ):
        """
        Initialize Deepgram Speech-to-Text client.
        Requires DEEPGRAM_KEY environment variable to be set.

        Args:
            model_output_processing: transcript -> word list post-processor.
            local_extractor_factory: optional callable returning the local
                fallback extractor. Injected by tests so no real model loads.
        """
        # Get Deepgram API key from environment
        self.api_key = os.getenv("DEEPGRAM_KEY")
        if not self.api_key:
            raise ValueError("DEEPGRAM_KEY environment variable is not set")

        self.model_output_processing = model_output_processing
        self.deepgram_url = "https://api.deepgram.com/v1/listen"
        self.local_extractor_factory = local_extractor_factory

    # ------------------------------------------------------------------ #
    # Public entry point
    # ------------------------------------------------------------------ #

    def extract_words(self, audio, sampling_rate=16000, timeout=15, max_retries=2):
        """
        Extract words from audio using Deepgram Speech-to-Text API.

        Args:
            audio: numpy array of audio data or bytes
            sampling_rate: sampling rate of the audio (default: 16000)
            timeout: timeout in seconds for the API call (default: 15)
            max_retries: maximum number of retry attempts (default: 2)

        Returns:
            List of words extracted from the audio.

        Raises:
            Only when ``WWAI_ASR_FALLBACK`` (or ``WWAI_ASR_TYPED_ERRORS``) is
            on: a subclass of :class:`core.errors.WordWizError`. With the flags
            unset every failure still returns ``[]``, exactly as before.
        """
        typed_errors = asr_typed_errors_enabled()
        fallback_enabled = asr_fallback_enabled()

        record: Dict[str, Any] = {
            "request_id": get_asr_request_context().get("request_id") or uuid.uuid4().hex[:12],
            "path": "online",
            "extractor": f"{DEEPGRAM_SERVICE}:nova-2",
            "typed_errors": typed_errors,
            "fallback_enabled": fallback_enabled,
            "fallback_fired": False,
            "attempts": 0,
            "sampling_rate": sampling_rate,
            "timeout_s": timeout,
            "max_retries": max_retries,
        }
        started = time.time()
        words: Optional[List[str]] = None

        # The record is emitted in `finally` so that a raised typed error --
        # the whole point of this module -- still leaves a log line behind.
        try:
            try:
                words = self._extract_words_online(
                    audio, sampling_rate, timeout, max_retries, record
                )
            except WordWizError as primary_error:
                record["primary_failure"] = primary_error.to_log_record()
                words = self._handle_primary_failure(
                    primary_error, audio, sampling_rate, record, typed_errors, fallback_enabled
                )
            except Exception as unexpected:  # pragma: no cover - defensive
                primary_error = wrap_unexpected(
                    unexpected, where="WordExtractorOnline.extract_words"
                )
                record["primary_failure"] = primary_error.to_log_record()
                words = self._handle_primary_failure(
                    primary_error, audio, sampling_rate, record, typed_errors, fallback_enabled
                )
            return words
        finally:
            record["total_ms"] = round((time.time() - started) * 1000, 1)
            record["word_count"] = len(words) if words else 0
            record.setdefault("outcome", "success" if words else "empty")
            _log_record(
                "asr.word_extraction",
                record,
                level=_OUTCOME_LOG_LEVEL.get(record["outcome"], logging.WARNING),
            )

    # ------------------------------------------------------------------ #
    # Failure handling / fallback chain
    # ------------------------------------------------------------------ #

    def _handle_primary_failure(
        self,
        primary_error: WordWizError,
        audio,
        sampling_rate,
        record: Dict[str, Any],
        typed_errors: bool,
        fallback_enabled: bool,
    ) -> List[str]:
        """
        Deepgram -> local wav2vec2 -> typed error.

        The fallback is only attempted for *upstream service* failures. A
        successful API call that returned an empty transcript means the child
        really was silent, and re-running a second acoustic model over the same
        silence would burn 1.2GB and tens of seconds to reach the same answer;
        so ``EmptyAudioError`` (and our own bugs) fail fast.
        """
        should_fallback = fallback_enabled and isinstance(primary_error, UpstreamServiceError)
        record["fallback_considered"] = should_fallback

        if should_fallback:
            fb_started = time.time()
            try:
                words = self._extract_words_local(audio, sampling_rate)
                record["fallback_fired"] = True
                record["fallback_ms"] = round((time.time() - fb_started) * 1000, 1)
                record["path"] = "local_fallback"
                record["extractor"] = f"wav2vec2:{LOCAL_ASR_MODEL}"
                record["degraded"] = True
                if words:
                    record["outcome"] = "success_degraded"
                    print(
                        f"🛟 Deepgram unavailable ({primary_error.code}); "
                        f"used local wav2vec2 fallback -> {words}"
                    )
                    return words
                # The local model heard nothing either. Report it as empty
                # audio, but record that we got there down the degraded path.
                record["outcome"] = "empty"
                empty = EmptyAudioError(
                    "Local wav2vec2 fallback produced no words after Deepgram failure "
                    f"({primary_error.operator_detail})",
                    context={
                        "degraded": True,
                        "primary_failure_code": primary_error.code,
                        "model": LOCAL_ASR_MODEL,
                    },
                    cause=primary_error,
                )
                record["final_failure"] = empty.to_log_record()
                if typed_errors:
                    raise empty
                return []
            except WordWizError as fb_error:
                if isinstance(fb_error, EmptyAudioError):
                    raise
                # Fallback itself broke: keep the ORIGINAL classification so
                # the operator still sees "Deepgram 401", not "torch OOM".
                record["fallback_fired"] = False
                record["fallback_ms"] = round((time.time() - fb_started) * 1000, 1)
                record["fallback_failure"] = fb_error.to_log_record()
                print(f"❌ Local word-extraction fallback failed: {fb_error.operator_detail}")
            except Exception as fb_exc:  # pragma: no cover - defensive
                record["fallback_fired"] = False
                record["fallback_ms"] = round((time.time() - fb_started) * 1000, 1)
                record["fallback_failure"] = wrap_unexpected(
                    fb_exc, where="local word extraction fallback"
                ).to_log_record()
                print(f"❌ Local word-extraction fallback failed: {fb_exc}")

        record["outcome"] = "failed"
        record["final_failure"] = primary_error.to_log_record()
        if typed_errors:
            raise primary_error
        return []

    def _extract_words_local(self, audio, sampling_rate) -> List[str]:
        """Run the local wav2vec2 extractor (lazy-loaded, process-wide)."""
        print("🛟 Falling back to local wav2vec2 word extraction (no network)...")
        extractor = get_local_word_extractor(self.local_extractor_factory)
        words = _call_maybe_async(
            extractor.extract_words, audio=audio, sampling_rate=sampling_rate
        )
        if words is None:
            return []
        return list(words)

    # ------------------------------------------------------------------ #
    # Deepgram call
    # ------------------------------------------------------------------ #

    def _extract_words_online(
        self, audio, sampling_rate, timeout, max_retries, record: Dict[str, Any]
    ) -> List[str]:
        """
        The original Deepgram request/retry loop, with each terminal failure
        raising a typed error instead of returning ``[]``.

        Every ``print`` below is unchanged from the previous implementation so
        that existing log-scraping keeps working; the typed errors are what the
        caller sees differently, and only when the flag is on.
        """
        import requests

        typed_errors = asr_typed_errors_enabled()

        # Convert numpy array to bytes if needed
        if isinstance(audio, np.ndarray):
            # Normalize audio to [-1, 1] range if not already
            if np.max(np.abs(audio)) > 1.0:
                audio = audio / np.max(np.abs(audio))

            # Ensure audio is in the correct format (16-bit PCM)
            audio_int16 = (audio * 32767).astype(np.int16)
            audio_bytes = audio_int16.tobytes()
        else:
            audio_bytes = audio

        record["audio_bytes"] = len(audio_bytes) if audio_bytes is not None else 0

        # Validate audio length
        if len(audio_bytes) == 0:
            print("⚠️  Warning: Empty audio data received")
            raise EmptyAudioError(
                "Zero-length audio buffer handed to WordExtractorOnline.extract_words",
                context={"stage": "pre_request"},
            )

        # Calculate audio duration for logging
        audio_duration = len(audio_bytes) / (sampling_rate * 2)  # 2 bytes per sample (16-bit)
        record["audio_seconds"] = round(audio_duration, 3)
        print(f"📤 Sending {audio_duration:.2f}s audio to Deepgram for transcription...")

        # Prepare headers
        headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "audio/wav"
        }

        # Prepare query parameters
        params = {
            "model": "nova-2",
            "language": "en-US",
            "punctuate": "true",
            "smart_format": "true",
            "encoding": "linear16",
            "sample_rate": sampling_rate
        }

        # Retry loop
        last_error: Optional[WordWizError] = None
        upstream_ms = 0.0
        for attempt in range(max_retries + 1):
            record["attempts"] = attempt + 1
            response = None
            try:
                if attempt > 0:
                    print(f"🔄 Retry attempt {attempt}/{max_retries} for word extraction...")
                    time.sleep(1 * attempt)  # Exponential backoff

                # Perform the transcription with timeout
                start_time = time.time()
                response = requests.post(
                    self.deepgram_url,
                    headers=headers,
                    params=params,
                    data=audio_bytes,
                    timeout=timeout
                )
                elapsed_time = time.time() - start_time
                upstream_ms += elapsed_time * 1000

                # Check if request was successful
                response.raise_for_status()

                # Parse the JSON response
                result = response.json()

                print(f"✓ Deepgram transcription completed in {elapsed_time:.2f}s")

                # Extract transcription from response
                transcriptions = []
                if result.get("results") and result["results"].get("channels"):
                    for channel in result["results"]["channels"]:
                        if channel.get("alternatives"):
                            transcript = channel["alternatives"][0].get("transcript", "")
                            if transcript:
                                transcriptions.append(transcript)

                print(f"📝 Transcription results: {transcriptions}")

                # If no transcription found, the API *succeeded* and heard
                # nothing -- this is the one genuinely user-actionable case.
                if not transcriptions:
                    print("⚠️  Warning: No transcription results found")
                    record["upstream_ms"] = round(upstream_ms, 1)
                    raise EmptyAudioError(
                        f"{DEEPGRAM_SERVICE} nova-2 returned HTTP 200 with an empty transcript "
                        f"for {audio_duration:.2f}s of audio (attempt {attempt + 1})",
                        context={
                            "service": DEEPGRAM_SERVICE,
                            "audio_seconds": round(audio_duration, 3),
                            "stage": "transcript",
                        },
                    )

                # Combine multiple transcription results if present
                combined_transcription = " ".join(transcriptions)

                # Process the transcription to match WordExtractor output format
                transcription = self.model_output_processing([combined_transcription])

                record["upstream_ms"] = round(upstream_ms, 1)

                if not transcription:
                    raise EmptyAudioError(
                        f"{DEEPGRAM_SERVICE} nova-2 transcript contained no word characters: "
                        f"{combined_transcription!r}",
                        context={
                            "service": DEEPGRAM_SERVICE,
                            "audio_seconds": round(audio_duration, 3),
                            "stage": "post_processing",
                        },
                    )

                record["outcome"] = "success"
                return transcription

            except requests.exceptions.Timeout as e:
                upstream_ms += (time.time() - start_time) * 1000
                last_error = UpstreamTransientError(
                    f"{DEEPGRAM_SERVICE} POST {self.deepgram_url} timed out after {timeout}s "
                    f"(attempt {attempt + 1}/{max_retries + 1}, {audio_duration:.2f}s audio)",
                    service=DEEPGRAM_SERVICE,
                    context={
                        "reason": "timeout",
                        "timeout_s": timeout,
                        "attempt": attempt + 1,
                        "audio_seconds": round(audio_duration, 3),
                    },
                    cause=e,
                )
                print(f"⏱️  Timeout after {timeout}s - audio may be too long or network is slow")
                if attempt == max_retries:
                    print(f"❌ All {max_retries + 1} attempts failed due to timeout")
                    record["upstream_ms"] = round(upstream_ms, 1)
                    raise last_error

            except requests.exceptions.HTTPError as e:
                status_code = None
                body = None
                err_response = getattr(e, "response", None) or response
                if err_response is not None:
                    status_code = getattr(err_response, "status_code", None)
                    try:
                        body = err_response.text
                    except Exception:
                        body = None
                record["http_status"] = status_code
                last_error = classify_http_status(
                    status_code,
                    service=DEEPGRAM_SERVICE,
                    operator_detail=(
                        f"{DEEPGRAM_SERVICE} POST {self.deepgram_url} returned HTTP {status_code} "
                        f"(attempt {attempt + 1}/{max_retries + 1}): {e}. "
                        f"Body: {(body or '')[:500]!r}"
                    ),
                    context={
                        "reason": "http_error",
                        "attempt": attempt + 1,
                        "response_body_excerpt": (body or "")[:500],
                    },
                    cause=e,
                )
                print(
                    f"❌ Deepgram API error: {e} - "
                    f"{body if body is not None else 'No response'}"
                )
                # Retrying a 401/403/429 just burns the child's patience -- the
                # answer will not change. Only skip the retries when the typed
                # error path is on, so flag-off behaviour stays identical.
                if typed_errors and not last_error.retryable:
                    print(
                        f"⛔ Not retrying: {last_error.code} "
                        f"(HTTP {status_code}) will not resolve on retry"
                    )
                    record["upstream_ms"] = round(upstream_ms, 1)
                    record["retries_skipped"] = True
                    raise last_error
                if attempt == max_retries:
                    print(f"❌ All {max_retries + 1} attempts failed due to API error")
                    record["upstream_ms"] = round(upstream_ms, 1)
                    raise last_error

            except WordWizError:
                # EmptyAudioError raised from the success branch above: a
                # successful call, nothing to retry.
                raise

            except Exception as e:
                last_error = wrap_unexpected(
                    e,
                    where=f"{DEEPGRAM_SERVICE} word extraction (attempt {attempt + 1})",
                    context={"attempt": attempt + 1},
                )
                if isinstance(e, (json.JSONDecodeError, ValueError)):
                    last_error = UpstreamTransientError(
                        f"{DEEPGRAM_SERVICE} returned an unparseable response on attempt "
                        f"{attempt + 1}: {type(e).__name__}: {e}",
                        service=DEEPGRAM_SERVICE,
                        context={"reason": "bad_response", "attempt": attempt + 1},
                        cause=e,
                    )
                print(f"❌ Unexpected error during Deepgram transcription: {e}")
                if attempt == max_retries:
                    print(f"❌ All {max_retries + 1} attempts failed")
                    record["upstream_ms"] = round(upstream_ms, 1)
                    raise last_error

        # Should not reach here, but just in case
        print(f"❌ Word extraction failed after {max_retries + 1} attempts: {last_error}")
        record["upstream_ms"] = round(upstream_ms, 1)
        raise last_error or InternalPipelineError(
            "Deepgram retry loop exited without a result or an error",
            context={"service": DEEPGRAM_SERVICE},
        )


# if __name__ == '__main__':
#     from grapheme_to_phoneme import grapheme_to_phoneme
#     from audio_recording import record_and_process_pronunciation
#
#     # Load the audio file
#     audio, sampling_rate = librosa.load("./temp_audio/output.wav", sr=16000)
#     # Create the phoneme extractor
#     extractor = WordExtractor()
#
#     # Extract the phonemes
#     phonemes = extractor.extract_words(audio, sampling_rate)
#     ground_truth_phonemes = grapheme_to_phoneme("zero three five one")
#     # phonemes, ground_truth_phonemes = record_and_process_pronunciation("the quick brown fox jumped over the lazy dog", extractor)
#
#     print(phonemes)
#     print(ground_truth_phonemes)
