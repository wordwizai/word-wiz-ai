"""extract_phoneme == decode_logits(extract_logits(...)), with output unchanged by the refactor.

Needs the ONNX model in the local HuggingFace cache; skips otherwise.
Run from backend/:  PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.test_onnx_logits_split -v
"""

import contextlib
import io
import json
import os
import sys
import unittest

import soundfile as sf

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

SAMPLE_WAV = os.path.join(BACKEND_ROOT, "tests", "system", "test_case_02", "audio.wav")
GOLDEN = os.path.join(BACKEND_ROOT, "tests", "benchmark", "fixtures", "onnx_golden_test_case_02.json")


class TestLogitsSplit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._saved = os.environ.pop("WWAI_PHONEME_NORMALIZATION", None)
        try:
            from core.phoneme_extractor_onnx import PhonemeExtractorONNX, decode_logits

            with contextlib.redirect_stdout(io.StringIO()):
                cls.extractor = PhonemeExtractorONNX()
        except Exception as exc:  # noqa: BLE001
            raise unittest.SkipTest(f"ONNX model unavailable: {exc}")
        cls.decode_logits = staticmethod(decode_logits)
        cls.audio, _ = sf.read(SAMPLE_WAV, dtype="float32")

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "_saved", None) is not None:
            os.environ["WWAI_PHONEME_NORMALIZATION"] = cls._saved

    def test_logits_shape(self):
        logits = self.extractor.extract_logits(self.audio, 16000)
        self.assertEqual(logits.ndim, 3)
        self.assertEqual(logits.shape[0], 1)
        # The model emits tokenizer.vocab_size (44) classes; get_vocab() also lists <s> and </s>.
        self.assertEqual(logits.shape[2], self.extractor.processor.tokenizer.vocab_size)

    def test_extract_phoneme_is_decode_of_logits(self):
        logits = self.extractor.extract_logits(self.audio, 16000)
        decoded = self.decode_logits(logits, self.extractor.processor, self.extractor.model_output_processing)
        self.assertEqual(decoded, self.extractor.extract_phoneme(self.audio, 16000))

    def test_output_unchanged_by_refactor(self):
        with open(GOLDEN, encoding="utf-8") as fh:
            golden = json.load(fh)
        self.assertEqual(self.extractor.extract_phoneme(self.audio, 16000), golden)


if __name__ == "__main__":
    unittest.main()
