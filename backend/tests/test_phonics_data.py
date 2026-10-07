"""Tests for the phonics data export (scripts/export_phonics_data.py) and loader.

Run from backend/:  python -m unittest tests.test_phonics_data
"""

import importlib.util
import sys
import unittest
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from core import phonics_data  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "export_phonics_data", BACKEND / "scripts" / "export_phonics_data.py"
)
export = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(export)


def sizes(lines):
    return [len(line.split()) for line in lines]


class WordLinesTest(unittest.TestCase):
    def test_deals_words_evenly_into_lines_of_five_or_fewer(self):
        self.assertEqual(sizes(export.word_lines([f"w{i}" for i in range(14)])), [5, 5, 4])
        self.assertEqual(sizes(export.word_lines([f"w{i}" for i in range(11)])), [4, 4, 3])
        self.assertEqual(sizes(export.word_lines([f"w{i}" for i in range(16)])), [4, 4, 4, 4])

    def test_short_list_is_one_line_in_order(self):
        self.assertEqual(export.word_lines(["cat", "hat", "bat"]), ["cat hat bat"])
        self.assertEqual(export.word_lines(list("abcdef")), ["a b c", "d e f"])


class UnitsTest(unittest.TestCase):
    PATTERNS = {"at-family": {}, "an-family": {}}

    def curriculum(self, *unit_patterns):
        return {
            "units": [
                {"id": f"u{i}", "title": f"Unit {i}", "grade": "K", "patterns": list(p)}
                for i, p in enumerate(unit_patterns)
            ]
        }

    def test_unknown_pattern_is_refused(self):
        with self.assertRaisesRegex(ValueError, "unknown pattern nope"):
            export.build_units(self.curriculum(["at-family", "an-family", "nope"]), self.PATTERNS)

    def test_pattern_in_two_units_is_refused(self):
        with self.assertRaisesRegex(ValueError, "at-family is in both u0 and u1"):
            export.build_units(self.curriculum(["at-family", "an-family"], ["at-family"]), self.PATTERNS)

    def test_pattern_in_no_unit_is_refused(self):
        with self.assertRaisesRegex(ValueError, "in no unit: an-family"):
            export.build_units(self.curriculum(["at-family"]), self.PATTERNS)


class BuildTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = export.build()

    def test_every_pattern_is_placed_in_curriculum_order(self):
        self.assertEqual(len(self.data["units"]), 18)
        self.assertEqual(len(self.data["patterns"]), 113)
        positions = [p["position"] for p in self.data["patterns"].values()]
        self.assertEqual(positions, list(range(113)))

    def test_at_family_reads_word_lines_then_sentences(self):
        at = self.data["patterns"]["at-family"]
        self.assertEqual(at["display_name"], "-at Word Family")
        self.assertEqual(at["unit"], "short-a")
        self.assertEqual(at["word_line_count"], 3)
        self.assertEqual(at["lines"][0], "cat hat bat mat rat")
        self.assertEqual(at["lines"][3:], at["sentences"])


class LoaderTest(unittest.TestCase):
    def test_reads_patterns_and_units(self):
        self.assertEqual(phonics_data.get_pattern("sh-digraph")["unit"], "digraphs")
        self.assertIsNone(phonics_data.get_pattern("nope"))
        self.assertEqual(phonics_data.units()[0]["id"], "short-a")
        self.assertEqual(next(iter(phonics_data.all_patterns())), "at-family")


if __name__ == "__main__":
    unittest.main()
