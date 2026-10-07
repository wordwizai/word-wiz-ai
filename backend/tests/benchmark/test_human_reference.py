import contextlib
import io
import json
import os
import tempfile
import unittest
from unittest import mock

from tests.benchmark import common
from tests.benchmark import human_reference as H
from tests.benchmark import testutil as U

DETAIL = {
    "a": {"accuracy": [8.0, 8.0, 7.0, 9.0, 8.0], "words": [
        {"text": "CAT", "accuracy": [10.0, 10.0, 10.0, 10.0, 10.0]},
        {"text": "DOG", "accuracy": [3.0, 3.0, 3.0, 3.0, 9.0]},
    ]},
    "b": {"accuracy": [5.0, 6.0, 5.0, 4.0, 6.0], "words": [
        {"text": "SUN", "accuracy": [10.0, 9.0, 10.0, 10.0, 10.0]},
        {"text": "HAT", "accuracy": [2.0, 3.0, 2.0, 2.0, 8.0]},
    ]},
}


class TestAgreement(unittest.TestCase):
    def test_leave_one_out(self):
        result = H.annotator_agreement(DETAIL, ["a", "b"])
        f05 = [p["word_f05"] for p in result["per_annotator"]]
        # Annotators 0-3 agree with the others' median; annotator 4 misses both mistakes.
        self.assertEqual(f05, [1.0, 1.0, 1.0, 1.0, 0.0])
        self.assertAlmostEqual(result["mean"]["word_f05"], 0.8)
        self.assertEqual(result["per_annotator"][4]["recall"], 0.0)
        self.assertIsNotNone(result["per_annotator"][0]["word_pearson"])

    def test_loads_fixture(self):
        detail = H.load_detail(U.MINI_DATASET)
        self.assertEqual(sorted(detail), ["000010011", "000020022", "000030033"])


class TestMain(unittest.TestCase):
    def test_dev_half_runs_on_the_fixture_and_writes_results(self):
        stdout = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(H, "find_dataset_root", return_value=U.MINI_DATASET), \
                    mock.patch.object(common, "results_dir", return_value=tmp), \
                    contextlib.redirect_stdout(stdout):
                code = H.main(["--half", "dev"])
            with open(os.path.join(tmp, "human_reference_dev.json"), encoding="utf-8") as fh:
                written = json.load(fh)
        self.assertEqual(code, 0)
        self.assertEqual(written["half"], "dev")
        self.assertEqual(len(written["per_annotator"]), H.N_ANNOTATORS)
        # The fixture's dev half is two clips with 4 + 9 words.
        self.assertEqual(written["per_annotator"][0]["words"], 13)
        self.assertIn("mean", stdout.getvalue())

    def test_test_half_needs_the_unlock_variable(self):
        # Refused before any dataset or label file is read.
        stderr = io.StringIO()
        with mock.patch.dict("os.environ", {}, clear=False) as env:
            env.pop(common.UNLOCK_ENV, None)
            with mock.patch.object(H, "find_dataset_root") as find, contextlib.redirect_stderr(stderr):
                code = H.main(["--half", "test"])
        self.assertEqual(code, 2)
        self.assertIn(common.UNLOCK_ENV, stderr.getvalue())
        find.assert_not_called()


if __name__ == "__main__":
    unittest.main()
