import contextlib
import io
import json
import os
import shutil
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.benchmark import common
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
        self.assertEqual(child.raw_text, "WE CALL IT BEAR")
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
        self.assertEqual(report["notes"], [])
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


def _set_raw_text(root, utt_id, text):
    """Change only the sentence in scores.json, leaving the scored words alone."""
    path = os.path.join(root, "scores.json")
    with open(path, encoding="utf-8") as fh:
        scores = json.load(fh)
    scores[utt_id]["text"] = text
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(scores, fh)


class TestSentenceFromScoredWords(unittest.TestCase):
    """A few clips have typos in scores.json text (a missing space after a period, a stray
    quote mark). The sentence the speaker read is the scored words, so the clip's text is
    built from them and the raw text is kept for reference."""

    def test_text_is_built_from_the_scored_words(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = U.make_temp_dataset(tmp)
            _set_raw_text(root, "000010011", "WE CALL IT.BEAR")
            child = D.load_half(root, "dev")[0]
        self.assertEqual(child.utt_id, "000010011")
        self.assertEqual(child.text, "WE CALL IT BEAR")
        self.assertEqual(child.raw_text, "WE CALL IT.BEAR")

    def test_a_token_count_difference_is_a_note_not_a_problem(self):
        for raw in ("WE CALL IT.BEAR", 'WE " CALL IT BEAR'):
            with self.subTest(raw=raw), tempfile.TemporaryDirectory() as tmp:
                root = U.make_temp_dataset(tmp)
                _set_raw_text(root, "000010011", raw)
                report = D.check(root)
                tokens = len(raw.split())
                self.assertEqual(report["problems"], [])
                self.assertEqual(
                    report["notes"],
                    [f"000010011: raw text has {tokens} tokens but 4 scored words (sentence built from scored words)"],
                )

    def test_cli_prints_notes_and_still_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = U.make_temp_dataset(tmp)
            _set_raw_text(root, "000010011", "WE CALL IT.BEAR")
            out = io.StringIO()
            with mock.patch.dict(os.environ, {common.DATA_DIR_ENV: root}), contextlib.redirect_stdout(out):
                code = D.main(["check"])
        self.assertEqual(code, 0)
        self.assertIn("NOTE 000010011: raw text has 3 tokens but 4 scored words", out.getvalue())
        self.assertNotIn("PROBLEM", out.getvalue())
        self.assertIn("0 problem(s), 1 note(s)", out.getvalue())

    def test_cli_still_fails_on_a_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = U.make_temp_dataset(tmp)
            os.remove(_first_wav(root))
            out = io.StringIO()
            with mock.patch.dict(os.environ, {common.DATA_DIR_ENV: root}), contextlib.redirect_stdout(out):
                code = D.main(["check"])
        self.assertEqual(code, 1)
        self.assertIn("PROBLEM 000010011: missing audio", out.getvalue())


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


def _first_wav(root):
    return os.path.join(root, "WAVE", "SPEAKER0001", "000010011.WAV")


class TestHardening(unittest.TestCase):
    def test_check_reports_truncated_audio(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = U.make_temp_dataset(tmp)
            wav = _first_wav(root)
            size = os.path.getsize(wav)
            with open(wav, "r+b") as fh:
                fh.truncate(size // 2)
            report = D.check(root)
        self.assertTrue(any("truncated audio" in p for p in report["problems"]), report["problems"])

    def test_check_reports_unreadable_audio(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = U.make_temp_dataset(tmp)
            with open(_first_wav(root), "r+b") as fh:
                fh.truncate(10)
            report = D.check(root)
        self.assertTrue(any("unreadable audio" in p for p in report["problems"]), report["problems"])

    def test_missing_age_is_value_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = U.make_temp_dataset(tmp)
            path = os.path.join(root, "train", "spk2age")
            with open(path, encoding="utf-8") as fh:
                lines = [ln for ln in fh if not ln.startswith("0002")]
            with open(path, "w", encoding="utf-8") as fh:
                fh.writelines(lines)
            with self.assertRaises(ValueError) as ctx:
                D.load_half(root, "dev")
        self.assertIn("spk2age", str(ctx.exception))

    def test_missing_scores_entry_is_value_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = U.make_temp_dataset(tmp)
            path = os.path.join(root, "scores.json")
            with open(path, encoding="utf-8") as fh:
                scores = json.load(fh)
            del scores["000020022"]
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(scores, fh)
            with self.assertRaises(ValueError) as ctx:
                D.load_half(root, "dev")
        self.assertIn("scores.json", str(ctx.exception))

    def test_bom_in_wav_scp(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = U.make_temp_dataset(tmp)
            path = os.path.join(root, "train", "wav.scp")
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
            with open(path, "w", encoding="utf-8-sig") as fh:
                fh.write(text)
            self.assertEqual(len(D.load_half(root, "dev")), 2)

    def test_check_reports_id_missing_from_wav_scp(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = U.make_temp_dataset(tmp)
            with open(os.path.join(root, "train", "text"), "a", encoding="utf-8") as fh:
                fh.write("999999999 EXTRA WORDS\n")
            report = D.check(root)
        self.assertTrue(any("in text but not wav.scp" in p for p in report["problems"]), report["problems"])

    def test_find_root_in_oddly_named_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            shutil.copytree(U.MINI_DATASET, os.path.join(tmp, "some_other_name"))
            self.assertEqual(D.find_dataset_root(tmp), os.path.join(tmp, "some_other_name"))

    def test_empty_subset_is_value_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = U.make_temp_dataset(tmp)
            with open(D.subset_path("empty", tmp), "w", encoding="utf-8") as fh:
                fh.write("\n")
            with self.assertRaises(ValueError):
                D.load_clips("dev", "empty", root=root, subsets_dir=tmp)


class TestDownload(unittest.TestCase):
    def test_download_end_to_end_offline(self):
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as dest:
            root = U.make_temp_dataset(src)
            archive = os.path.join(src, "pack.tar.gz")
            with tarfile.open(archive, "w:gz") as tar:
                tar.add(root, arcname="speechocean762")
            got = D.download(dest=dest, mirrors=(Path(archive).as_uri(),))
            self.assertTrue(os.path.isdir(os.path.join(got, "train")))
            self.assertTrue(os.path.isfile(os.path.join(dest, D.EXTRACTED_MARKER)))
            self.assertFalse(os.path.exists(os.path.join(dest, "speechocean762.tar.gz.part")))
            os.remove(os.path.join(dest, "speechocean762.tar.gz"))
            self.assertEqual(D.download(dest=dest, mirrors=()), got)

    def test_corrupt_archive_is_deleted(self):
        with tempfile.TemporaryDirectory() as dest:
            archive = os.path.join(dest, "speechocean762.tar.gz")
            with open(archive, "wb") as fh:
                fh.write(os.urandom(100))
            with self.assertRaises(RuntimeError):
                D.download(dest=dest, mirrors=())
            self.assertFalse(os.path.exists(archive))


if __name__ == "__main__":
    unittest.main()
