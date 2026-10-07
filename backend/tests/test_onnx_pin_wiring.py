"""PhonemeExtractorONNX loads the revision pinned in core/model_registry.py.

No network and no model: the loaders are mocked.
Run from backend/:  PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.test_onnx_pin_wiring -v
"""

import os
import sys
import unittest
from unittest import mock

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from core import phoneme_extractor_onnx as onnx_mod  # noqa: E402
from core.model_registry import get  # noqa: E402

CONFIG = {"model_cache_enabled": False, "warmup_runs": 0, "enable_performance_logging": False}
REPO = "Bobcat9/wav2vec2-timit-ipa-onnx"


class TestPinWiring(unittest.TestCase):
    def setUp(self):
        self._saved = {k: os.environ.pop(k, None) for k in ("WWAI_IGNORE_MODEL_PINS", "WWAI_PIN_PHONEME_IPA_ONNX")}

    def tearDown(self):
        for key, value in self._saved.items():
            os.environ.pop(key, None)
            if value is not None:
                os.environ[key] = value

    def _load(self):
        with mock.patch.object(onnx_mod, "Wav2Vec2Processor") as proc, \
             mock.patch("huggingface_hub.hf_hub_download", return_value="model.onnx") as hub, \
             mock.patch.object(onnx_mod.ort, "InferenceSession"):
            onnx_mod.PhonemeExtractorONNX(optimization_config=CONFIG)
        return proc, hub

    def test_revision_is_pinned(self):
        self.assertIsNotNone(get("PHONEME_IPA_ONNX").revision)

    def test_loader_passes_the_pin(self):
        pin = get("PHONEME_IPA_ONNX").revision
        proc, hub = self._load()
        proc.from_pretrained.assert_called_once_with(REPO, revision=pin)
        hub.assert_called_once_with(repo_id=REPO, filename="model.onnx", revision=pin)

    def test_global_escape_hatch(self):
        os.environ["WWAI_IGNORE_MODEL_PINS"] = "true"
        proc, hub = self._load()
        proc.from_pretrained.assert_called_once_with(REPO)
        hub.assert_called_once_with(repo_id=REPO, filename="model.onnx")


if __name__ == "__main__":
    unittest.main()
