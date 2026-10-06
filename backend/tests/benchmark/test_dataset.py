import json
import os
import tempfile
import unittest

from tests.benchmark import dataset as D
from tests.benchmark import testutil as U


class TestParse(unittest.TestCase):
    def setUp(self):
        self.root = U.MINI_DATASET

    def test_dev_half(self):
        dev = D.load_half(self.root, "dev")
        self.assertEqual([c.utt_id for c in dev], ["000010011", "000020022"])
        child, adult = dev
        self.assertEqual((child.speaker, child.age, child.is_child), ("0001", 6, True))
        self.assertFalse(adult.is_child)
        self.assertEqual(child.text, "WE CALL IT BEAR")
        self.assertTrue(os.path.isabs(child.wav_path))
        self.assertTrue(child.wav_path.endswith(os.path.join("SPEAKER0001", "000010011.WAV")))
        bear = child.words[3]
        self.assertEqual((bear.text, bear.accuracy, bear.phones), ("BEAR", 6.0, ["B", "EH0", "R"]))
        self.assertEqual(bear.phone_accuracy, [2.0, 1.6, 0.4])
        self.assertEqual(child.sentence_accuracy, 8.0)

    def test_test_half(self):
        self.assertEqual([c.utt_id for c in D.load_half(self.root, "test")], ["000030033"])

    def test_unknown_half(self):
        with self.assertRaises(ValueError):
            D.load_half(self.root, "train")

    def test_phones_may_be_a_list(self):
        self.assertEqual(D._phones(["W", "IY0"]), ["W", "IY0"])
        self.assertEqual(D._phones("W IY0"), ["W", "IY0"])


class TestRootAndChecks(unittest.TestCase):
    def test_find_nested_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = U.make_temp_dataset(tmp)
            self.assertEqual(D.find_dataset_root(tmp), root)

    def test_missing_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                D.find_dataset_root(tmp)

    def test_speaker_overlap_is_fatal(self):
        a = U.synthetic_clip("1", "0001", 6, [("A", 10, "AH0", [2])])
        b = U.synthetic_clip("2", "0001", 6, [("A", 10, "AH0", [2])], half="test")
        with self.assertRaises(ValueError):
            D.check_speaker_disjoint([a], [b])

    def test_check_on_complete_dataset(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = D.check(U.make_temp_dataset(tmp))
        self.assertEqual(report["problems"], [])
        self.assertEqual((report["dev_clips"], report["test_clips"]), (2, 1))
        self.assertEqual(report["dev_children"], 1)

    def test_check_reports_missing_audio(self):
        report = D.check(U.MINI_DATASET)  # fixture ships no audio
        self.assertTrue(any("missing audio" in p for p in report["problems"]))

    def test_check_reports_unknown_phone(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = U.make_temp_dataset(tmp)
            path = os.path.join(root, "scores.json")
            with open(path, encoding="utf-8") as fh:
                scores = json.load(fh)
            scores["000010011"]["words"][0]["phones"] = "QQ1 IY0"
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(scores, fh)
            report = D.check(root)
        self.assertTrue(any("unknown phone" in p for p in report["problems"]))


class TestSubsets(unittest.TestCase):
    def setUp(self):
        self.clips = [U.synthetic_clip(f"c{i:02d}", f"s{i}", 8 if i < 10 else 30, [("A", 10, "AH0", [2])]) for i in range(20)]

    def test_stratified(self):
        picked = D.make_subset(self.clips, 10, seed=1)
        by_id = {c.utt_id: c for c in self.clips}
        self.assertEqual(len(picked), 10)
        self.assertEqual(sum(by_id[u].is_child for u in picked), 5)

    def test_seeded(self):
        self.assertEqual(D.make_subset(self.clips, 7, seed=3), D.make_subset(self.clips, 7, seed=3))

    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            D.write_subset("smoke", ["b", "a"], directory=tmp)
            self.assertEqual(D.read_subset("smoke", directory=tmp), ["a", "b"])

    def test_load_clips_with_subset(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = U.make_temp_dataset(tmp)
            D.write_subset("one", ["000020022"], directory=tmp)
            clips = D.load_clips("dev", "one", root=root, subsets_dir=tmp)
            self.assertEqual([c.utt_id for c in clips], ["000020022"])
            D.write_subset("bad", ["999"], directory=tmp)
            with self.assertRaises(ValueError):
                D.load_clips("dev", "bad", root=root, subsets_dir=tmp)


if __name__ == "__main__":
    unittest.main()
