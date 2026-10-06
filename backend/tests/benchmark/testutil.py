"""Shared helpers and fakes for the benchmark tests. Imports are lazy on purpose."""

from __future__ import annotations

import functools
import os
import shutil
import types
import unittest

import numpy as np

from tests.benchmark import common

SAMPLE_WAV = os.path.join(common.BACKEND_ROOT, "tests", "system", "test_case_02", "audio.wav")
SAMPLE_TEXT = "the quick brown fox jumped over the lazy dog"
SAMPLE_IPA = "ðə kwɪk braʊn fɑks ʤəmpt oʊvər ðə leɪzi dɔg"
MINI_DATASET = os.path.join(common.FIXTURES_DIR, "mini_speechocean")


def make_temp_dataset(tmpdir: str) -> str:
    """Copy the mini fixture into tmpdir and give every clip the sample WAV as audio."""
    root = os.path.join(tmpdir, "speechocean762")
    shutil.copytree(MINI_DATASET, root)
    for half in ("train", "test"):
        with open(os.path.join(root, half, "wav.scp"), encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                _utt, rel = line.split()
                dst = os.path.join(root, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy(SAMPLE_WAV, dst)
    return root


@functools.lru_cache(maxsize=1)
def _load_processor():
    from transformers import Wav2Vec2Processor
    from core.model_registry import from_pretrained_kwargs, repo_id

    with common.quiet():
        return Wav2Vec2Processor.from_pretrained(
            repo_id("PHONEME_IPA_ONNX"), local_files_only=True, **from_pretrained_kwargs("PHONEME_IPA_ONNX")
        )


def real_processor_or_skip():
    """The real wav2vec2 tokenizer from the local HF cache, or SkipTest when it is not cached."""
    try:
        return _load_processor()
    except OSError as exc:
        raise unittest.SkipTest(f"wav2vec2 processor not in the local HF cache: {exc}")


class FakeSession:
    """Stands in for an ONNX session: one-hot logits that decode to `transcription`, whatever the input.

    With ``fail_on_call`` set, the run() call with that index (0-based) raises ``exc`` instead.
    """

    def __init__(self, processor, transcription: str = SAMPLE_IPA, fail_on_call=None, exc=None):
        self.processor = processor
        self.transcription = transcription
        self.fail_on_call = fail_on_call
        self.exc = exc
        self.calls = 0

    def get_inputs(self):
        return [types.SimpleNamespace(name="input_values")]

    def run(self, output_names, feeds):
        index = self.calls
        self.calls += 1
        if self.fail_on_call is not None and index == self.fail_on_call:
            raise self.exc if self.exc is not None else RuntimeError("fake session failure")
        return [self._logits()]

    def _logits(self) -> np.ndarray:
        vocab = self.processor.tokenizer.get_vocab()
        pad = vocab[self.processor.tokenizer.pad_token]
        ids = []
        for ch in self.transcription:
            token_id = vocab["|"] if ch == " " else vocab[ch]
            if ids and ids[-1] == token_id:
                ids.append(pad)
            ids.append(token_id)
        # Same width as the real model output (vocab_size, 44), not len(get_vocab()) (46).
        logits = np.full((1, len(ids), self.processor.tokenizer.vocab_size), -10.0, dtype=np.float32)
        logits[0, np.arange(len(ids)), ids] = 10.0
        return logits


def fake_onnx_extractor(processor, transcription: str = SAMPLE_IPA, **session_kwargs):
    """A PhonemeExtractorONNX that runs all real extractor code except the model."""
    from core.audio_optimization import OptimizedAudioPreprocessor
    from core.phoneme_extractor_onnx import PhonemeExtractorONNX, default_model_output_processing

    ext = PhonemeExtractorONNX.__new__(PhonemeExtractorONNX)
    ext.processor = processor
    ext.audio_preprocessor = OptimizedAudioPreprocessor(target_sr=16000, enable_logging=False)
    ext.model_output_processing = default_model_output_processing
    ext._performance_logging = False
    ext.session = FakeSession(processor, transcription, **session_kwargs)
    return ext


class FakeWords:
    def __init__(self, words=None):
        self.words = list(words if words is not None else SAMPLE_TEXT.split())

    def extract_words(self, audio, sampling_rate=16000, **_kwargs):
        return list(self.words)


def synthetic_clip(utt_id, speaker, age, words, sentence_accuracy=8.0, half="dev"):
    """words: list of (text, accuracy, "ARPA PHONES", [phone accuracies])."""
    from tests.benchmark.dataset import Clip, Word

    return Clip(
        utt_id=utt_id, speaker=speaker, age=age, half=half,
        text=" ".join(w[0] for w in words), wav_path="",
        sentence_accuracy=float(sentence_accuracy),
        words=[Word(t, float(a), p.split(), [float(x) for x in pa]) for t, a, p, pa in words],
    )


def record(word, expected, actual, per, rtype=None):
    expected, actual = list(expected), list(actual)
    return {
        "type": rtype or ("match" if per == 0 else "substitution"),
        "ground_truth_word": word,
        "expected_phonemes": expected,
        "actual_phonemes": actual,
        "per": per,
        "total_errors": int(round(per * len(expected))),
        "total_phonemes": len(expected),
    }


def ok(*records):
    return {"status": "ok", "words": list(records), "error_type": None, "error": None}


def rejected(error_type="AudioRejected"):
    return {"status": "rejected", "words": [], "error_type": error_type, "error": "rejected"}


def results_dict(name, outcomes, half="dev", subset=None, threshold=0.4):
    return {"name": name, "half": half, "subset": subset, "threshold": threshold, "outcomes": outcomes}
