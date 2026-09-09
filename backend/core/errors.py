"""
Typed error taxonomy for the Word Wiz AI audio pipeline.

Why this module exists
----------------------
Every failure in the audio pipeline used to collapse into one of two strings:

  * ``ValueError("The audio provided has no speech inside")`` -- raised in
    ``process_audio.py`` whenever the word list came back short, *including*
    when the upstream ASR provider timed out or returned 401.
  * ``"AI processing failed: {e}"`` -- the catch-all in the websocket/SSE
    handler.

Both conflate two completely different audiences:

  * the **child**, who needs a short, kind, actionable sentence and must never
    be blamed for a server-side outage, and
  * the **operator**, who needs the provider, the HTTP status, the timing and
    the retry count in order to answer "why did that one recording go wrong?".

Every exception here therefore carries BOTH, separately, plus a stable machine
``code``, a ``retryable`` flag, and an ``alert_operator`` flag.

Nothing in this module has side effects or imports anything heavy; it is safe
to import from anywhere in the backend.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional


# --------------------------------------------------------------------------- #
# Category constants (stable strings -- safe to key dashboards/alerts off)
# --------------------------------------------------------------------------- #

CATEGORY_UPSTREAM_TRANSIENT = "upstream_transient"
CATEGORY_UPSTREAM_AUTH = "upstream_auth"
CATEGORY_UPSTREAM_QUOTA = "upstream_quota"
CATEGORY_EMPTY_AUDIO = "empty_audio"
CATEGORY_INTERNAL = "internal"


# Child-facing copy lives in one place so the tone can be reviewed as a set.
# Rule: if the fault is ours, say so plainly and tell the child it is not their
# fault. Never ask a child to debug our infrastructure.
_USER_MSG_TRANSIENT = (
    "We had trouble listening to your recording just now. "
    "That was our fault, not yours - please try reading it again."
)
_USER_MSG_AUTH = (
    "Our listening helper is having a problem right now. "
    "It is not your fault, and we are already looking at it. "
    "Please try again in a little while."
)
_USER_MSG_QUOTA = (
    "Our listening helper is very busy right now. "
    "It is not your fault - please try again in a few minutes."
)
_USER_MSG_EMPTY = (
    "We could not hear any words in that recording. "
    "Try again a little louder, and hold the microphone closer."
)
_USER_MSG_INTERNAL = (
    "Something went wrong on our side while checking your reading. "
    "That was not your fault - please try again."
)


class WordWizError(Exception):
    """
    Base class for every typed pipeline error.

    Attributes
    ----------
    code:
        Stable dotted machine code, e.g. ``asr.upstream.timeout``. Safe to
        alert/group on; never shown to a child.
    user_message:
        Child-appropriate, one or two short sentences. Must never blame the
        child for a server-side problem.
    operator_detail:
        Precise, high-cardinality technical description: provider, endpoint,
        HTTP status, timings, attempt counts.
    category:
        One of the ``CATEGORY_*`` constants above.
    retryable:
        True when retrying the *same* request has a reasonable chance of
        succeeding without human intervention.
    alert_operator:
        True when a human needs to look at this (auth, quota, internal bugs).
    user_actionable:
        True when the child can actually do something about it (speak louder).
    context:
        Free-form structured detail merged into log records.
    """

    code: str = "internal.unknown"
    category: str = CATEGORY_INTERNAL
    retryable: bool = False
    alert_operator: bool = True
    user_actionable: bool = False
    default_user_message: str = _USER_MSG_INTERNAL

    def __init__(
        self,
        operator_detail: str,
        *,
        user_message: Optional[str] = None,
        code: Optional[str] = None,
        retryable: Optional[bool] = None,
        alert_operator: Optional[bool] = None,
        context: Optional[Dict[str, Any]] = None,
        cause: Optional[BaseException] = None,
    ) -> None:
        # The Exception's own str() is the OPERATOR message on purpose: any
        # existing `str(e)` in logs keeps getting the technical text, and the
        # child-facing text is only ever reachable through .user_message.
        super().__init__(operator_detail)
        self.operator_detail = operator_detail
        self.user_message = user_message or self.default_user_message
        if code is not None:
            self.code = code
        if retryable is not None:
            self.retryable = retryable
        if alert_operator is not None:
            self.alert_operator = alert_operator
        self.context: Dict[str, Any] = dict(context or {})
        self.cause = cause
        if cause is not None and self.__cause__ is None:
            self.__cause__ = cause

    # -- serialisation ----------------------------------------------------- #

    def to_user_payload(self) -> Dict[str, Any]:
        """
        The dict that is safe to send over the wire to the browser.

        Deliberately contains NO operator detail -- no provider names, no HTTP
        bodies, no stack context. ``code`` is included so the frontend can
        branch (e.g. offer a "try again" button only when ``retryable``).
        """
        return {
            "message": self.user_message,
            "code": self.code,
            "category": self.category,
            "retryable": self.retryable,
            "user_actionable": self.user_actionable,
        }

    def to_log_record(self) -> Dict[str, Any]:
        """The dict an operator wants in the log line."""
        record: Dict[str, Any] = {
            "code": self.code,
            "category": self.category,
            "error_class": type(self).__name__,
            "retryable": self.retryable,
            "alert_operator": self.alert_operator,
            "operator_detail": self.operator_detail,
        }
        if self.cause is not None:
            record["cause_class"] = type(self.cause).__name__
            record["cause"] = str(self.cause)
        if self.context:
            record["context"] = self.context
        return record

    def __repr__(self) -> str:  # pragma: no cover - debugging convenience
        return f"<{type(self).__name__} {self.code}: {self.operator_detail}>"


# --------------------------------------------------------------------------- #
# Upstream (third-party service) failures
# --------------------------------------------------------------------------- #


class UpstreamServiceError(WordWizError):
    """A third-party dependency (Deepgram, OpenAI, Google TTS) failed us."""

    code = "upstream.error"
    service: str = "unknown"

    def __init__(
        self,
        operator_detail: str,
        *,
        service: str = "unknown",
        status_code: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        context = dict(kwargs.pop("context", None) or {})
        context.setdefault("service", service)
        if status_code is not None:
            context.setdefault("http_status", status_code)
        super().__init__(operator_detail, context=context, **kwargs)
        self.service = service
        self.status_code = status_code


class UpstreamTransientError(UpstreamServiceError):
    """
    Timeout, connection reset, 5xx. Expected to clear on its own.

    Retryable, and NOT worth waking anyone up for a single occurrence (a rate
    of these is what should alert, not one).
    """

    code = "upstream.transient"
    category = CATEGORY_UPSTREAM_TRANSIENT
    retryable = True
    alert_operator = False
    default_user_message = _USER_MSG_TRANSIENT


class UpstreamAuthError(UpstreamServiceError):
    """
    401/403, or a missing/blank API key.

    NOT retryable: every subsequent request will fail identically until a human
    rotates the key. This is the failure mode that used to be reported to a
    seven-year-old as "the audio provided has no speech inside".
    """

    code = "upstream.auth"
    category = CATEGORY_UPSTREAM_AUTH
    retryable = False
    alert_operator = True
    default_user_message = _USER_MSG_AUTH


class UpstreamQuotaError(UpstreamServiceError):
    """
    429 / 402: rate limited or out of credit.

    Not retryable on the timescale of a single child's attempt, and always
    worth alerting -- unlike a timeout, this does not fix itself.
    """

    code = "upstream.quota"
    category = CATEGORY_UPSTREAM_QUOTA
    retryable = False
    alert_operator = True
    default_user_message = _USER_MSG_QUOTA


# --------------------------------------------------------------------------- #
# Genuinely bad input (the one case where the child can act)
# --------------------------------------------------------------------------- #


class EmptyAudioError(WordWizError, ValueError):
    """
    The recording really did contain no recognisable speech.

    This is the ONLY error whose message may point at the recording, and it
    must only be raised when an ASR call actually *succeeded* and came back
    with nothing (or when we were handed a zero-length buffer).

    It deliberately also subclasses ``ValueError``: ``process_audio.py``'s
    chunked path does ``except ValueError`` around each chunk to skip silent
    chunks, and that behaviour should be preserved. Upstream/internal errors do
    NOT subclass ValueError, so a Deepgram outage mid-chunk now aborts loudly
    instead of being silently recorded as "this chunk was quiet".
    """

    code = "audio.empty"
    category = CATEGORY_EMPTY_AUDIO
    retryable = False
    alert_operator = False
    user_actionable = True
    default_user_message = _USER_MSG_EMPTY


# --------------------------------------------------------------------------- #
# Our own bugs
# --------------------------------------------------------------------------- #


class InternalPipelineError(WordWizError):
    """
    A bug in our code: bad request we constructed, alignment blew up, an
    unexpected exception type. Always alerts; never blames the child.
    """

    code = "internal.pipeline"
    category = CATEGORY_INTERNAL
    retryable = False
    alert_operator = True
    default_user_message = _USER_MSG_INTERNAL


class ConfigurationError(InternalPipelineError):
    """Misconfiguration found at startup/first use (missing env var, etc.)."""

    code = "internal.configuration"


# --------------------------------------------------------------------------- #
# Classification helpers
# --------------------------------------------------------------------------- #


def classify_http_status(
    status_code: Optional[int],
    *,
    service: str,
    operator_detail: str,
    context: Optional[Dict[str, Any]] = None,
    cause: Optional[BaseException] = None,
) -> WordWizError:
    """
    Map an HTTP status from a third-party ASR/LLM/TTS call onto the taxonomy.

    The interesting decision here is that a generic 4xx is classified as an
    *internal* error, not an upstream one: a 400 from Deepgram means we built a
    bad request, which is our bug, and should page us rather than being retried
    or blamed on the network.
    """
    kwargs: Dict[str, Any] = {
        "service": service,
        "status_code": status_code,
        "context": context,
        "cause": cause,
    }

    if status_code in (401, 403):
        return UpstreamAuthError(operator_detail, **kwargs)
    if status_code in (402, 429):
        return UpstreamQuotaError(operator_detail, **kwargs)
    if status_code is not None and 500 <= status_code < 600:
        return UpstreamTransientError(operator_detail, **kwargs)
    if status_code in (408, 425):
        return UpstreamTransientError(operator_detail, **kwargs)
    if status_code is not None and 400 <= status_code < 500:
        # We sent something the provider refused: our bug.
        return InternalPipelineError(
            operator_detail,
            context=dict(context or {}, service=service, http_status=status_code),
            cause=cause,
        )
    # No status at all (connection error, DNS, reset) -> transient.
    return UpstreamTransientError(operator_detail, **kwargs)


def wrap_unexpected(
    exc: BaseException,
    *,
    where: str,
    context: Optional[Dict[str, Any]] = None,
) -> WordWizError:
    """
    Turn an arbitrary exception into a typed one without losing information.

    Already-typed errors pass straight through so classification made deeper in
    the stack is never downgraded by an outer ``except Exception``.
    """
    if isinstance(exc, WordWizError):
        return exc
    return InternalPipelineError(
        f"Unexpected {type(exc).__name__} in {where}: {exc}",
        context=dict(context or {}, where=where),
        cause=exc,
    )


def to_error_frame(exc: BaseException) -> Dict[str, Any]:
    """
    Build the websocket/SSE ``{"type": "error", ...}`` frame for any exception.

    Untyped exceptions degrade to the internal-bug message rather than leaking
    ``str(e)`` (which is how stack detail ended up in front of children).
    """
    typed = exc if isinstance(exc, WordWizError) else wrap_unexpected(exc, where="pipeline")
    return {"type": "error", "data": typed.to_user_payload()}


def format_log_line(event: str, record: Dict[str, Any]) -> str:
    """One-line JSON rendering used by the structured logs in this package."""
    try:
        return f"{event} {json.dumps(record, default=str, sort_keys=True)}"
    except Exception:  # pragma: no cover - logging must never raise
        return f"{event} {record!r}"


__all__ = [
    "CATEGORY_EMPTY_AUDIO",
    "CATEGORY_INTERNAL",
    "CATEGORY_UPSTREAM_AUTH",
    "CATEGORY_UPSTREAM_QUOTA",
    "CATEGORY_UPSTREAM_TRANSIENT",
    "ConfigurationError",
    "EmptyAudioError",
    "InternalPipelineError",
    "UpstreamAuthError",
    "UpstreamQuotaError",
    "UpstreamServiceError",
    "UpstreamTransientError",
    "WordWizError",
    "classify_http_status",
    "format_log_line",
    "to_error_frame",
    "wrap_unexpected",
]
