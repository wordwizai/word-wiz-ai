"""One clip through the production request path, with pluggable acoustic models.

Mirrors a server-path analysis request:
  load_and_preprocess_audio_bytes  -> core.request_audio.gate_and_preprocess, mark_preprocessed
  PhonemeAssistant.process_audio   -> clean_sentence -> grapheme_to_phoneme -> process_audio_array
Only the two model objects differ between stage_cache (recording the real models),
run (replaying cached outputs) and speed (live ONNX, cached transcripts).
"""

from __future__ import annotations

import asyncio
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
        value = record.get(key)
        out[key] = list(value) if isinstance(value, (list, tuple)) else value
    return out


@dataclass
class ClipOutcome:
    status: str  # "ok" or "rejected"
    words: list = field(default_factory=list)
    error_type: str | None = None
    error: str | None = None

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "words": [compact_record(w) for w in self.words],
            "error_type": self.error_type,
            "error": self.error,
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
    from core.process_audio import process_audio_array
    from core.request_audio import gate_and_preprocess

    reset_preprocessing_state()
    audio = gate_and_preprocess(audio, SAMPLE_RATE, len(audio) / SAMPLE_RATE, apply_gates=apply_gates)
    mark_preprocessed(audio)
    ground_truth = grapheme_to_phoneme(clean_sentence(text))
    return await process_audio_array(
        ground_truth_phonemes=ground_truth,
        audio_array=audio,
        sampling_rate=SAMPLE_RATE,
        phoneme_extraction_model=phoneme_model,
        word_extraction_model=word_model,
    )


def analyze_clip(audio, text, phoneme_model, word_model, apply_gates=True) -> ClipOutcome:
    """Run one clip. Pipeline failures become a 'rejected' outcome; a stale cache is re-raised."""
    try:
        with common.quiet():
            words = asyncio.run(_analyze(audio, text, phoneme_model, word_model, apply_gates))
    except common.StaleCacheError:
        raise
    except Exception as exc:  # noqa: BLE001 - every pipeline failure is something the child would see
        error_type = getattr(exc, "error_type", None) or type(exc).__name__
        return ClipOutcome("rejected", [], error_type, str(exc)[:300])
    return ClipOutcome("ok", list(words or []))
