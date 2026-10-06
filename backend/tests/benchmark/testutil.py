"""Shared helpers and fakes for the benchmark tests. Imports are lazy on purpose."""

from __future__ import annotations

import functools
import os
import shutil
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


class FakeOnnx:
    """Stands in for PhonemeExtractorONNX. One-hot logits that decode to `transcription`."""

    def __init__(self, processor, transcription: str = SAMPLE_IPA):
        from core.phoneme_extractor_onnx import default_model_output_processing

        self.processor = processor
        self.model_output_processing = default_model_output_processing
        self._transcription = transcription

    def extract_logits(self, audio, sampling_rate=16000, **_kwargs):
        vocab = self.processor.tokenizer.get_vocab()
        pad = vocab[self.processor.tokenizer.pad_token]
        ids = []
        for ch in self._transcription:
            token_id = vocab["|"] if ch == " " else vocab[ch]
            if ids and ids[-1] == token_id:
                ids.append(pad)
            ids.append(token_id)
        logits = np.full((1, len(ids), len(vocab)), -10.0, dtype=np.float32)
        logits[0, np.arange(len(ids)), ids] = 10.0
        return logits


class FakeOnnxExtractor:
    """Has extract_phoneme like the real extractor, built on FakeOnnx logits."""

    def __init__(self, processor, transcription: str = SAMPLE_IPA):
        self.inner = FakeOnnx(processor, transcription)

    def extract_phoneme(self, audio, sampling_rate=16000, **_kwargs):
        from core.phoneme_extractor_onnx import decode_logits

        logits = self.inner.extract_logits(audio, sampling_rate)
        return decode_logits(logits, self.inner.processor, self.inner.model_output_processing)


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
