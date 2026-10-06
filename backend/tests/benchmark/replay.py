"""Feed cached model outputs back into the real pipeline.

Each replayed call checks that its input hashes to what was recorded. For the phoneme
model the replay happens at the ONNX session: ReplayPhonemeExtractor is the production
PhonemeExtractorONNX with a stub session, so its validation, trimming, feature extraction
and decoding all run for real and the session input is what gets checked. Any front-end
change (preprocessing code, chunking, trimming, a front-end flag) therefore stops the run
with StaleCacheError instead of silently scoring outputs for different audio.

This module imports core at load time. run.py imports it lazily, after apply_flags().
"""

from __future__ import annotations

import builtins
import os
import types

import numpy as np

from core import errors as core_errors
from core.audio_optimization import OptimizedAudioPreprocessor
from core.phoneme_extractor_onnx import PhonemeExtractorONNX, default_model_output_processing

from . import common
from .stage_cache import audio_sha, model_input_sha, read_entry


class CacheEntry:
    def __init__(self, directory: str, utt_id: str):
        meta_path = os.path.join(directory, f"{utt_id}.json")
        if not os.path.isfile(meta_path):
            raise common.StaleCacheError(
                f"no cache entry for {utt_id} in {directory}; build it with tests.benchmark.stage_cache"
            )
        try:
            self.meta = read_entry(meta_path)
        except ValueError as exc:
            raise common.StaleCacheError(
                f"cache entry {meta_path} is unreadable ({exc}); rebuild it with tests.benchmark.stage_cache"
            ) from exc
        self.utt_id = utt_id
        self._npz_path = os.path.join(directory, f"{utt_id}.npz")
        self._logits: dict | None = None

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
    """Raise a recorded exception again so that the pipeline treats it as the live run did.

    1. A builtin keeps its type, so `except ValueError` and analyze_clip see the original.
    2. Any other recorded ValueError becomes ReplayedValueError. It was an expected rejection
       live, and process_audio_array's chunk loop swallowed it, so it must still be a ValueError.
    3. A core.errors.WordWizError becomes ReplayedError, an expected rejection as in production.
    4. Anything else (onnxruntime's Fail, a harness or runtime crash) becomes a fresh exception
       class with the recorded name, so analyze_clip reports it as unexpected:<Name>. It must
       never count as a rejection a child would see.
    """
    error_type, message = call["error_type"], call.get("error", "")
    exc_cls = getattr(builtins, error_type, None)
    if isinstance(exc_cls, type) and issubclass(exc_cls, Exception):
        try:
            exc = exc_cls(message)
        except TypeError:
            # Some builtins cannot be built from one message (UnicodeDecodeError takes five
            # arguments). They fall through to the rules below.
            pass
        else:
            raise exc
    if call.get("is_value_error"):
        raise common.ReplayedValueError(error_type, message)
    project_cls = getattr(core_errors, error_type, None)
    if isinstance(project_cls, type) and issubclass(project_cls, core_errors.WordWizError):
        raise common.ReplayedError(error_type, message)
    raise type(error_type, (Exception,), {})(message)


class _Replay:
    kind = ""

    def __init__(self, entry: CacheEntry, calls: list, check_inputs: bool = True):
        self.entry = entry
        self._calls = calls
        self._next = 0
        self.check_inputs = check_inputs

    def _take(self, input_sha) -> dict:
        """The next recorded call. ``input_sha`` is a zero-argument function that hashes what
        the model received now; it is only evaluated when inputs are checked."""
        if self._next >= len(self._calls):
            raise common.StaleCacheError(
                f"{self.entry.utt_id}: the pipeline made more {self.kind} calls than were recorded; rebuild the cache"
            )
        call = self._calls[self._next]
        self._next += 1
        if not isinstance(call, dict) or "input_sha" not in call:
            raise common.StaleCacheError(
                f"{self.entry.utt_id}: recorded {self.kind} call {self._next} has no input hash; rebuild the cache"
            )
        if self.check_inputs and input_sha() != call["input_sha"]:
            raise common.StaleCacheError(
                f"{self.entry.utt_id}: the input to the {self.kind} model differs from the cached run "
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


class ReplaySession(_Replay):
    """Stub ONNX session: returns cached logits and checks the exact model input."""

    kind = "phoneme"

    def __init__(self, entry: CacheEntry, check_inputs: bool = True):
        super().__init__(entry, entry.phoneme_calls, check_inputs)

    def get_inputs(self):
        return [types.SimpleNamespace(name="input_values")]

    def run(self, output_names, feeds):
        values = next(iter(feeds.values()))
        call = self._take(lambda: model_input_sha(values))  # recorded errors are raised here, unwrapped
        try:
            logits = self.entry.logits(call["logits_key"])
        except Exception as exc:
            raise self._broken(exc) from exc
        return [logits]


class ReplayPhonemeExtractor(PhonemeExtractorONNX):
    """The production extractor with its ONNX session replaced by a ReplaySession.

    extract_phoneme, extract_logits and decode_logits are the production methods, so input
    validation, trimming, feature extraction and decoding all run for real.
    """

    def __init__(self, entry: CacheEntry, processor, check_inputs: bool = True):
        # Deliberately not super().__init__(), which loads the model. These are the attributes
        # extract_phoneme and extract_logits read.
        self.entry = entry
        self.processor = processor
        self.audio_preprocessor = OptimizedAudioPreprocessor(target_sr=16000, enable_logging=False)
        self.model_output_processing = default_model_output_processing
        self._performance_logging = False
        self.session = ReplaySession(entry, check_inputs)


class ReplayWordExtractor(_Replay):
    kind = "word"

    def __init__(self, entry: CacheEntry, check_inputs: bool = True):
        super().__init__(entry, entry.word_calls, check_inputs)

    def extract_words(self, audio, sampling_rate=16000, **_kwargs):
        call = self._take(lambda: audio_sha(audio, sampling_rate))  # recorded errors are raised here, unwrapped
        try:
            words = call["words"]
            return None if words is None else list(words)
        except Exception as exc:
            raise self._broken(exc) from exc
