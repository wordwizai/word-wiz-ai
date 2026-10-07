"""One clip through the production request path, with pluggable acoustic models.

Mirrors a server-path analysis request:
  load_and_preprocess_audio_bytes  -> core.request_audio.gate_and_preprocess, mark_preprocessed,
                                      then the speech-activity check on the preprocessed audio
  PhonemeAssistant.process_audio   -> clean_sentence -> grapheme_to_phoneme -> process_audio_array
  the router                       -> analyze_results, then generate_feedback on its outputs, called
                                      exactly as the router calls it. That text is what TTS speaks to
                                      the child, so the outcome keeps what it is about (see
                                      describe_feedback) for scoring. Running both also means a record
                                      change that would break production breaks the benchmark too, and
                                      speed.py times the same work.
Only the two model objects differ between stage_cache (recording the real models),
run (replaying cached outputs) and speed (live ONNX, cached transcripts).

stage_cache passes apply_gates=False. It records model outputs for every clip, and the gates
(quality and speech activity) are applied later, at scoring time.

analyze_clip is not thread-safe. quiet() swaps the process-wide stdout and stderr, and each call
starts its own event loop, so call it from synchronous code, one clip at a time per process.
"""

from __future__ import annotations

import asyncio
import traceback
from dataclasses import dataclass, field

import numpy as np

from . import common

SAMPLE_RATE = 16000
#: The per-word fields scoring needs. Everything else in a record is display data.
RECORD_FIELDS = (
    "type", "ground_truth_word", "expected_phonemes", "actual_phonemes",
    "per", "total_errors", "total_phonemes",
)


def compact_record(record: dict) -> dict:
    out = {}
    for key in RECORD_FIELDS:
        value = record[key]  # not .get(), so a renamed field fails loudly instead of scoring as None
        out[key] = list(value) if isinstance(value, (list, tuple)) else value
    return out


#: What generate_feedback returns when nothing needs correcting.
PRAISE_TEXT = "Great job!"


def describe_feedback(result) -> dict:
    """The part of a FeedbackResult that scoring needs.

    kind is "correction" when the feedback names words, "praise" for "Great job!", and
    "generic" for anything else (today that is "Keep practicing!").
    """
    words = list(result.focus_words or [])
    if words:
        kind = "correction"
    elif result.text == PRAISE_TEXT:
        kind = "praise"
    else:
        kind = "generic"
    return {"kind": kind, "focus_phoneme": result.focus_phoneme, "focus_words": words}


@dataclass
class ClipOutcome:
    status: str  # "ok" or "rejected"
    words: list = field(default_factory=list)
    error_type: str | None = None
    error: str | None = None
    feedback: dict | None = None  # describe_feedback() of the spoken feedback. None when rejected.

    def to_dict(self) -> dict:
        feedback = None
        if self.feedback is not None:
            feedback = {
                "kind": self.feedback["kind"],
                "focus_phoneme": self.feedback["focus_phoneme"],
                "focus_words": list(self.feedback["focus_words"]),
            }
        return {
            "status": self.status,
            "words": [compact_record(w) for w in self.words],
            "error_type": self.error_type,
            "error": self.error,
            "feedback": feedback,
        }


def load_audio(path: str) -> np.ndarray:
    import soundfile as sf

    audio, sr = sf.read(path, dtype="float32")
    if audio.ndim == 2:
        audio = audio.mean(axis=1)
    if sr != SAMPLE_RATE:
        import librosa

        audio = librosa.resample(audio, orig_sr=sr, target_sr=SAMPLE_RATE)
    return np.ascontiguousarray(audio, dtype=np.float32)


async def _analyze(audio, text, phoneme_model, word_model, apply_gates):
    from core.audio_preprocessing import mark_preprocessed, reset_preprocessing_state
    from core.grapheme_to_phoneme import clean_sentence, grapheme_to_phoneme
    from core.phoneme_feedback_formatter import generate_feedback
    from core.process_audio import analyze_results, process_audio_array
    from core.request_audio import check_speech_activity, gate_and_preprocess

    reset_preprocessing_state()
    audio = gate_and_preprocess(audio, SAMPLE_RATE, len(audio) / SAMPLE_RATE, apply_gates=apply_gates)
    mark_preprocessed(audio)
    if apply_gates:
        check_speech_activity(audio)  # on the preprocessed audio and before g2p, as in production
    ground_truth = grapheme_to_phoneme(clean_sentence(text))
    words = await process_audio_array(
        ground_truth_phonemes=ground_truth,
        audio_array=audio,
        sampling_rate=SAMPLE_RATE,
        phoneme_extraction_model=phoneme_model,
        word_extraction_model=word_model,
    )
    # The router's next two steps. The feedback text is what TTS speaks to the child.
    df, _highest, problem_summary, per_summary = analyze_results(words)
    feedback = generate_feedback(
        problem_summary=problem_summary,
        per_summary=per_summary,
        pronunciation_data=df.to_dict("records"),
    )
    return words, feedback


def _expected_failure(exc) -> bool:
    """Rejections production shows a child: gates (AudioRejected is a ValueError), no speech,
    one-word texts, and upstream or replayed model errors."""
    from core.errors import WordWizError

    return isinstance(exc, (ValueError, WordWizError, common.ReplayedError))


def analyze_clip(audio, text, phoneme_model, word_model, apply_gates=True) -> ClipOutcome:
    """Run one clip. Pipeline failures become a 'rejected' outcome; a stale cache is re-raised.

    Anything that is not an expected rejection (see _expected_failure) is still reported as
    'rejected', so the rejection rate counts it, but its error_type starts with 'unexpected:'
    and its error holds the end of the traceback, so a harness bug cannot pass for a child's
    rejected recording.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        pass
    else:
        raise RuntimeError("analyze_clip() starts its own event loop; call it from synchronous code")
    try:
        with common.quiet():
            words, feedback = asyncio.run(_analyze(audio, text, phoneme_model, word_model, apply_gates))
    except common.StaleCacheError:
        raise
    except Exception as exc:  # noqa: BLE001 - every pipeline failure is reported, see the docstring
        if _expected_failure(exc):
            error_type = getattr(exc, "error_type", None) or type(exc).__name__
            return ClipOutcome("rejected", [], error_type, str(exc)[:300])
        return ClipOutcome("rejected", [], f"unexpected:{type(exc).__name__}", traceback.format_exc()[-1000:])
    return ClipOutcome("ok", list(words or []), feedback=describe_feedback(feedback))
