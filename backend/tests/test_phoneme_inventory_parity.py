# -*- coding: utf-8 -*-
"""Python <-> TypeScript parity test for the canonical phoneme inventory.

The whole point of ``core/phoneme_inventory.py`` is that the client-side path
(``frontend/src/services/phonemeExtractor.ts``) and the server-side path score
the same audio the same way. That only holds if the two implementations
tokenize and normalize IDENTICALLY, so this test proves it rather than assuming
it: it lifts the mirrored block straight out of the .ts source (between the
``WWAI_IPA_MIRROR_BEGIN``/``END`` markers), runs it under Node, and compares the
output token-for-token against the Python implementation over a shared corpus.

If Node is unavailable the test skips loudly rather than passing silently.

Run from ``backend/``:

    PYTHONIOENCODING=utf-8 <venv>/python.exe -m unittest tests.test_phoneme_inventory_parity -v

No network. No model. Node only executes the extracted pure-function block.
"""

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.phoneme_inventory import normalize_phonemes, tokenize_ipa  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TS_PATH = os.path.join(
    REPO_ROOT, "frontend", "src", "services", "phonemeExtractor.ts"
)
BEGIN = "// ---- WWAI_IPA_MIRROR_BEGIN ----"
END = "// ---- WWAI_IPA_MIRROR_END ----"

NODE = shutil.which("node")


def build_corpus():
    """Inputs that exercise every branch of the tokenizer and normalizer."""
    corpus = [
        # eng_to_ipa ground truth (verified real outputs)
        "ðə", "kæt", "sæt",
        "ðə", "ʧərʧ", "ʤəʤd",
        "maɪ", "deɪ", "goʊz",
        # affricates spelled out
        "tʃərtʃ", "dʒədʒd",
        # every canonical symbol in context
        "pbtdkg", "fvθðszʃʒh", "mnŋ", "lrwj",
        "iɪɛæəuʊɔɑ",
        "aɪeɪɔɪaʊoʊ",
        # stress / length / syllable marks
        "ˈhɛloʊ", "ˌhɛˈloʊ", "huːd", "hɛ.loʊ", "kæt*", "wɜːld",
        # rhotics
        "ɹɛd", "bɝd", "bɚd", "fɑðɚ", "ʀɑʁ",
        # unicode edge cases
        "ẽ", "ɑ̃", "ɡoʊz", "ʧʤ",
        "ːæ", "ʰtæ", "l̩", "t͡ʃ",
        # inventory folding
        "ʌv", "ɒn", "ɾæ", "ʔʌʔ", "yɛs", "ɨʉɯ", "øœɤ", "ɲɳʎçɣβɸ",
        # non-IPA / OOV spelling fallthrough
        "wordwiz", "zyzzyva", "blorp", "qxc",
        # degenerate inputs
        "", " ", "ˈ", "ˈˌ.", "|", "aɪ",
        # model-style raw output fragments
        "ðəkwɪkbraʊn", "ɛkstrəɔrdɪnɛri", "sʌpərkælɪfrædʒɪlɪstɪk",
    ]
    # Also feed every 2-char combination of the model's own vocab symbols, which
    # is where longest-match decisions actually get made.
    vocab = list("aæbcdefghijklmnopqrstuvwxyzðŋɑɔəɛɪʃʊʒʤʧθ")
    for a in vocab:
        for b in vocab:
            corpus.append(a + b)
    return corpus


NODE_DRIVER = """
const input = JSON.parse(process.argv[2]);
const out = input.map((s) => ({
  tokens: tokenizeIpa(s),
  normalized: normalizeIpaPhonemes(s),
}));
process.stdout.write(JSON.stringify(out));
"""


def extract_mirror_block():
    with io.open(TS_PATH, encoding="utf-8") as fh:
        src = fh.read()
    if BEGIN not in src or END not in src:
        raise AssertionError(
            "Mirror markers missing from %s -- the TypeScript twin of "
            "phoneme_inventory.py can no longer be parity-tested." % TS_PATH
        )
    return src.split(BEGIN, 1)[1].split(END, 1)[0]


@unittest.skipUnless(NODE, "node executable not found on PATH")
class TestPythonTypeScriptParity(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        cls.corpus = build_corpus()
        block = extract_mirror_block()
        cls.tmpdir = tempfile.mkdtemp(prefix="wwai_ipa_parity_")
        # .mts forces ESM; Node >= 23 strips the TypeScript annotations natively.
        script = os.path.join(cls.tmpdir, "mirror.mts")
        with io.open(script, "w", encoding="utf-8") as fh:
            fh.write(block)
            fh.write(NODE_DRIVER)
        proc = subprocess.run(
            [NODE, script, json.dumps(cls.corpus, ensure_ascii=False)],
            capture_output=True,
        )
        if proc.returncode != 0:
            raise unittest.SkipTest(
                "node could not run the extracted mirror block: %s"
                % proc.stderr.decode("utf-8", "replace")[-2000:]
            )
        cls.js = json.loads(proc.stdout.decode("utf-8"))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(getattr(cls, "tmpdir", ""), ignore_errors=True)

    def test_corpus_is_substantial(self):
        self.assertGreater(len(self.corpus), 1500)
        self.assertEqual(len(self.js), len(self.corpus))

    def test_tokenize_parity(self):
        mismatches = []
        for text, js in zip(self.corpus, self.js):
            py = tokenize_ipa(text)
            if py != js["tokens"]:
                mismatches.append((text, py, js["tokens"]))
        self.assertEqual(mismatches, [], "tokenize_ipa != tokenizeIpa")

    def test_normalize_parity(self):
        mismatches = []
        for text, js in zip(self.corpus, self.js):
            py = normalize_phonemes(text)
            if py != js["normalized"]:
                mismatches.append((text, py, js["normalized"]))
        self.assertEqual(
            mismatches, [], "normalize_phonemes != normalizeIpaPhonemes"
        )


class TestMirrorBlockIsPresent(unittest.TestCase):
    """Runs even without Node -- catches the markers being deleted."""

    def test_markers_present(self):
        block = extract_mirror_block()
        for needle in (
            "IPA_MULTI_CHAR_TOKENS",
            "IPA_DIACRITICS",
            "IPA_IGNORED_CHARS",
            "IPA_ALIAS_MAP",
            "IPA_INVENTORY_FOLD_MAP",
            "export function tokenizeIpa",
            "export function normalizeIpaPhonemes",
        ):
            self.assertIn(needle, block)

    def test_tables_have_the_same_entries_as_python(self):
        """Cheap structural check that does not need Node at all."""
        import re

        from core.phoneme_inventory import (
            ALIAS_MAP,
            DIACRITICS,
            IGNORED_CHARS,
            INVENTORY_FOLD_MAP,
            MULTI_CHAR_TOKENS,
        )

        block = extract_mirror_block()

        def js_set(name):
            body = block.split("const %s" % name, 1)[1]
            body = body.split("new Set([", 1)[1].split("]);", 1)[0]
            return set(re.findall(r'"((?:[^"\\]|\\.)*)"', body))

        def js_map(name):
            body = block.split("const %s" % name, 1)[1]
            body = body.split("new Map([", 1)[1].split("]);", 1)[0]
            pairs = {}
            for key, values in re.findall(
                r'\["((?:[^"\\]|\\.)*)",\s*\[([^\]]*)\]\]', body
            ):
                pairs[key] = tuple(
                    re.findall(r'"((?:[^"\\]|\\.)*)"', values)
                )
            return pairs

        def unescape(s):
            return s.replace("\\t", "\t").replace("\\n", "\n").replace("\\r", "\r")

        self.assertEqual(js_set("IPA_MULTI_CHAR_TOKENS"), set(MULTI_CHAR_TOKENS))
        self.assertEqual(js_set("IPA_DIACRITICS"), set(DIACRITICS))
        self.assertEqual(
            {unescape(c) for c in js_set("IPA_IGNORED_CHARS")}, set(IGNORED_CHARS)
        )
        self.assertEqual(js_map("IPA_ALIAS_MAP"), ALIAS_MAP)
        self.assertEqual(js_map("IPA_INVENTORY_FOLD_MAP"), INVENTORY_FOLD_MAP)


if __name__ == "__main__":
    unittest.main(verbosity=2)
