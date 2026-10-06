"""Feed cached model outputs back into the real pipeline.

Each replayed call checks that the audio it receives hashes to what was recorded. Any
front-end change (preprocessing code, chunking, a front-end flag) therefore stops the
run with StaleCacheError instead of silently scoring outputs for different audio.
"""

from __future__ import annotations

import builtins
import json
import os

import numpy as np

from . import common
from .stage_cache import audio_sha


class CacheEntry:
    def __init__(self, directory: str, utt_id: str):
        meta_path = os.path.join(directory, f"{utt_id}.json")
        if not os.path.isfile(meta_path):
            raise common.StaleCacheError(
                f"no cache entry for {utt_id} in {directory}; build it with tests.benchmark.stage_cache"
            )
        with open(meta_path, encoding="utf-8") as fh:
            self.meta = json.load(fh)
        self._npz_path = os.path.join(directory, f"{utt_id}.npz")
        self._logits: dict | None = None

    @property
    def utt_id(self) -> str:
        return self.meta.get("utt_id", "?")

    @property
    def phoneme_calls(self) -> list:
        return self.meta["phoneme_calls"]

    @property
    def word_calls(self) -> list:
        return self.meta["word_calls"]

    def logits(self, key: str) -> np.ndarray:
        if self._logits is None:
            with np.load(self._npz_path) as data:
                self._logits = {k: data[k] for k in data.files}
        return self._logits[key]


def load_processor():
    from transformers import Wav2Vec2Processor
    from core.model_registry import from_pretrained_kwargs, repo_id

    return Wav2Vec2Processor.from_pretrained(
        repo_id("PHONEME_IPA_ONNX"), **from_pretrained_kwargs("PHONEME_IPA_ONNX")
    )


def _raise_recorded(call: dict):
    error_type, message = call["error_type"], call.get("error", "")
    exc_cls = getattr(builtins, error_type, None)
    if isinstance(exc_cls, type) and issubclass(exc_cls, Exception):
        try:
            exc = exc_cls(message)
        except TypeError:
            # Some builtins cannot be built from one message (UnicodeDecodeError takes five
            # arguments). They are replayed through the types below, which respect is_value_error.
            pass
        else:
            raise exc  # builtins keep their type, so `except ValueError` still matches
    if call.get("is_value_error"):
        # process_audio_array's chunk loop swallows ValueError, so a recorded ValueError subclass
        # (for example a project exception type) must still be one when it is replayed.
        raise common.ReplayedValueError(error_type, message)
    raise common.ReplayedError(error_type, message)


class _Replay:
    kind = ""

    def __init__(self, entry: CacheEntry, calls: list, check_inputs: bool = True):
        self.entry = entry
        self._calls = calls
        self._next = 0
        self.check_inputs = check_inputs

    def _take(self, audio, sampling_rate) -> dict:
        if self._next >= len(self._calls):
            raise common.StaleCacheError(
                f"{self.entry.utt_id}: the pipeline made more {self.kind} calls than were recorded; rebuild the cache"
            )
        call = self._calls[self._next]
        self._next += 1
        if self.check_inputs and audio_sha(audio, sampling_rate) != call["input_sha"]:
            raise common.StaleCacheError(
                f"{self.entry.utt_id}: audio sent to the {self.kind} model differs from the cached run "
                "(front-end code or flags changed); build a new cache with tests.benchmark.stage_cache"
            )
        if "error_type" in call:
            _raise_recorded(call)
        return call

    def _broken(self, exc: Exception) -> common.StaleCacheError:
        """A failure in the adapter's own work, never a recorded error.

        It must not look like a recorded ValueError, because process_audio_array's chunk loop
        would swallow that and silently turn the chunk into deletions.
        """
        return common.StaleCacheError(
            f"{self.entry.utt_id}: could not replay {self.kind} call: {type(exc).__name__}: {exc}"
        )


class ReplayPhonemeExtractor(_Replay):
    kind = "phoneme"

    def __init__(self, entry: CacheEntry, processor, check_inputs: bool = True):
        super().__init__(entry, entry.phoneme_calls, check_inputs)
        self.processor = processor

    def extract_phoneme(self, audio, sampling_rate=16000, **_kwargs):
        from core.phoneme_extractor_onnx import decode_logits

        call = self._take(audio, sampling_rate)  # recorded errors are raised here, unwrapped
        try:
            return decode_logits(self.entry.logits(call["logits_key"]), self.processor)
        except Exception as exc:
            raise self._broken(exc) from exc


class ReplayWordExtractor(_Replay):
    kind = "word"

    def __init__(self, entry: CacheEntry, check_inputs: bool = True):
        super().__init__(entry, entry.word_calls, check_inputs)

    def extract_words(self, audio, sampling_rate=16000, **_kwargs):
        call = self._take(audio, sampling_rate)  # recorded errors are raised here, unwrapped
        try:
            words = call["words"]
            return None if words is None else list(words)
        except Exception as exc:
            raise self._broken(exc) from exc
