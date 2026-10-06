"""speechocean762: download, parse, check, and fixed clip subsets.

The dataset's own ``train`` half is this benchmark's dev half. Its ``test`` half is the
sealed test half (run.py enforces the unlock rule).

    python -m tests.benchmark.dataset download      # ~520 MB from OpenSLR
    python -m tests.benchmark.dataset check
    python -m tests.benchmark.dataset make-subsets
"""

from __future__ import annotations

import argparse
import contextlib
import http.client
import json
import os
import random
import tarfile
import urllib.request
import wave
import zlib
from dataclasses import dataclass, field

from . import common
from .phones import arpabet_to_ipa

MIRRORS = (
    "https://openslr.trmal.net/resources/101/speechocean762.tar.gz",
    "https://openslr.elda.org/resources/101/speechocean762.tar.gz",
    "https://openslr.magicdatatech.com/resources/101/speechocean762.tar.gz",
)
USER_AGENT = "word-wiz-ai-benchmark/1.0"
EXTRACTED_MARKER = ".extracted"
HALF_DIRS = {"dev": "train", "test": "test"}
CHILD_MAX_AGE = 17  # a child is a speaker under 18
SMOKE_SUBSET = ("smoke_dev", 250, 1234)
SPEED_SUBSET = ("speed_dev", 200, 5678)


@dataclass
class Word:
    text: str
    accuracy: float
    phones: list[str]
    phone_accuracy: list[float]


@dataclass
class Clip:
    utt_id: str
    speaker: str
    age: int
    half: str
    text: str
    wav_path: str
    sentence_accuracy: float
    words: list[Word] = field(default_factory=list)

    @property
    def is_child(self) -> bool:
        return self.age <= CHILD_MAX_AGE


def find_dataset_root(base: str | None = None) -> str:
    base = base or common.data_dir()
    candidates = [base, os.path.join(base, "speechocean762")]
    if os.path.isdir(base):
        candidates += [os.path.join(base, d) for d in sorted(os.listdir(base))
                       if os.path.isdir(os.path.join(base, d))]
    for candidate in candidates:
        if all(os.path.isdir(os.path.join(candidate, d)) for d in HALF_DIRS.values()):
            return candidate
    raise FileNotFoundError(
        f"speechocean762 not found under {base}. Run: python -m tests.benchmark.dataset download"
    )


def find_resource(root: str, name: str) -> str:
    for path in (os.path.join(root, name), os.path.join(root, "resource", name)):
        if os.path.isfile(path):
            return path
    raise FileNotFoundError(f"{name} not found in {root} or {root}/resource")


def _read_kaldi_map(path: str) -> dict[str, str]:
    out: dict[str, str] = {}
    with open(path, encoding="utf-8-sig") as fh:
        for line in fh:
            parts = line.strip().split(None, 1)
            if parts:
                out[parts[0]] = parts[1].strip() if len(parts) > 1 else ""
    return out


def load_scores(root: str) -> dict:
    with open(find_resource(root, "scores.json"), encoding="utf-8") as fh:
        return json.load(fh)


def _phones(value) -> list[str]:
    return value.split() if isinstance(value, str) else list(value)


def load_half(root: str, half: str, scores: dict | None = None) -> list[Clip]:
    if half not in HALF_DIRS:
        raise ValueError(f"half must be one of {sorted(HALF_DIRS)}, got {half!r}")
    directory = os.path.join(root, HALF_DIRS[half])
    wav = _read_kaldi_map(os.path.join(directory, "wav.scp"))
    utt2spk = _read_kaldi_map(os.path.join(directory, "utt2spk"))
    spk2age = _read_kaldi_map(os.path.join(directory, "spk2age"))
    scores = scores if scores is not None else load_scores(root)
    clips = []
    for utt_id in sorted(wav):
        if utt_id not in scores:
            raise ValueError(f"scores.json has no entry for {utt_id} ({half} half)")
        entry = scores[utt_id]
        if utt_id not in utt2spk:
            raise ValueError(f"{HALF_DIRS[half]}/utt2spk has no speaker for utt {utt_id}")
        speaker = utt2spk[utt_id]
        if speaker not in spk2age:
            raise ValueError(f"{HALF_DIRS[half]}/spk2age has no age for speaker {speaker!r} (utt {utt_id})")
        path = wav[utt_id]
        if not os.path.isabs(path):
            path = os.path.normpath(os.path.join(root, path))
        words = [
            Word(
                text=w["text"],
                accuracy=float(w["accuracy"]),
                phones=_phones(w["phones"]),
                phone_accuracy=[float(a) for a in w["phones-accuracy"]],
            )
            for w in entry["words"]
        ]
        clips.append(Clip(
            utt_id=utt_id, speaker=speaker, age=int(spk2age[speaker]), half=half,
            text=entry["text"], wav_path=path, sentence_accuracy=float(entry["accuracy"]),
            words=words,
        ))
    return clips


def check_speaker_disjoint(dev, test) -> None:
    overlap = sorted({c.speaker for c in dev} & {c.speaker for c in test})
    if overlap:
        more = "..." if len(overlap) > 10 else ""
        raise ValueError(f"speakers appear in both halves: {overlap[:10]}{more}")


def subset_path(name: str, directory: str | None = None) -> str:
    return os.path.join(directory or common.SUBSETS_DIR, f"{name}.txt")


def read_subset(name: str, directory: str | None = None) -> list[str]:
    with open(subset_path(name, directory), encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip()]


def write_subset(name: str, utt_ids, directory: str | None = None) -> str:
    path = subset_path(name, directory)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(sorted(utt_ids)) + "\n")
    return path


def make_subset(clips, n: int, seed: int) -> list[str]:
    """n clip ids, stratified so children and adults keep their proportions."""
    if not clips:
        return []
    rng = random.Random(seed)
    children = sorted(c.utt_id for c in clips if c.is_child)
    adults = sorted(c.utt_id for c in clips if not c.is_child)
    n = min(n, len(clips))
    n_child = min(round(n * len(children) / len(clips)), len(children))
    picked = rng.sample(children, n_child) + rng.sample(adults, min(n - n_child, len(adults)))
    return sorted(picked)


def load_clips(half: str, subset: str | None = None, root: str | None = None,
               subsets_dir: str | None = None) -> list[Clip]:
    clips = load_half(root or find_dataset_root(), half)
    if subset:
        wanted = set(read_subset(subset, subsets_dir))
        if not wanted:
            raise ValueError(f"subset {subset!r} is empty")
        clips = [c for c in clips if c.utt_id in wanted]
        missing = wanted - {c.utt_id for c in clips}
        if missing:
            raise ValueError(f"subset {subset!r} names {len(missing)} clip(s) not in the {half} half")
    return clips


def _audio_problem(path: str):
    """None if the WAV looks complete, else a short description of what is wrong."""
    try:
        with wave.open(path, "rb") as w:
            nframes, width, channels, rate = w.getnframes(), w.getsampwidth(), w.getnchannels(), w.getframerate()
    except (wave.Error, EOFError, OSError) as exc:
        return f"unreadable audio {path}: {exc}"
    if nframes == 0:
        return f"empty audio {path}"
    if rate != 16000:
        return f"audio {path} is {rate} Hz, expected 16000"
    if os.path.getsize(path) < nframes * width * channels:
        return f"truncated audio {path}"
    return None


def _key_set_problems(root: str) -> list[str]:
    problems = []
    for half, directory in HALF_DIRS.items():
        base = os.path.join(root, directory)
        keys = {name: set(_read_kaldi_map(os.path.join(base, name))) for name in ("wav.scp", "utt2spk", "text")}
        for name, ids in keys.items():
            for other, other_ids in keys.items():
                if other == name:
                    continue
                extra = sorted(ids - other_ids)
                if extra:
                    problems.append(f"{directory}: {len(extra)} utt id(s) in {name} but not {other}: {extra[:10]}")
    return problems


def check(root: str) -> dict:
    scores = load_scores(root)
    dev, test = load_half(root, "dev", scores), load_half(root, "test", scores)
    check_speaker_disjoint(dev, test)
    problems = _key_set_problems(root)
    for clip in dev + test:
        if not os.path.isfile(clip.wav_path):
            problems.append(f"{clip.utt_id}: missing audio {clip.wav_path}")
        else:
            problem = _audio_problem(clip.wav_path)
            if problem:
                problems.append(f"{clip.utt_id}: {problem}")
        if len(clip.text.split()) != len(clip.words):
            problems.append(f"{clip.utt_id}: {len(clip.text.split())} text tokens but {len(clip.words)} scored words")
        for w in clip.words:
            if len(w.phones) != len(w.phone_accuracy):
                problems.append(f"{clip.utt_id}/{w.text}: {len(w.phones)} phones but {len(w.phone_accuracy)} scores")
            for phone in w.phones:
                try:
                    arpabet_to_ipa(phone)
                except ValueError:
                    problems.append(f"{clip.utt_id}/{w.text}: unknown phone {phone!r}")
    return {
        "dev_clips": len(dev),
        "test_clips": len(test),
        "dev_speakers": len({c.speaker for c in dev}),
        "test_speakers": len({c.speaker for c in test}),
        "dev_children": sum(c.is_child for c in dev),
        "test_children": sum(c.is_child for c in test),
        "problems": problems,
    }


def _fetch(url: str, archive: str) -> None:
    tmp = archive + ".part"
    try:
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=60) as resp, open(tmp, "wb") as out:
            total = int(resp.headers.get("Content-Length") or 0)
            done = 0
            while True:
                chunk = resp.read(1 << 20)
                if not chunk:
                    break
                out.write(chunk)
                done += len(chunk)
                if total:
                    print(f"\r  {done * 100 // total}%", end="", flush=True)
        print()
        if total and done != total:
            raise OSError(f"short download: {done} of {total} bytes")
        os.replace(tmp, archive)
    except BaseException:
        with contextlib.suppress(OSError):
            os.remove(tmp)
        raise


def download(dest: str | None = None, mirrors=MIRRORS) -> str:
    dest = dest or common.data_dir()
    os.makedirs(dest, exist_ok=True)
    marker = os.path.join(dest, EXTRACTED_MARKER)
    if os.path.isfile(marker):
        return find_dataset_root(dest)
    archive = os.path.join(dest, "speechocean762.tar.gz")
    if not os.path.isfile(archive):
        last_error = None
        for url in mirrors:
            try:
                print(f"Downloading {url} (~520 MB)...")
                _fetch(url, archive)
                break
            except (OSError, http.client.HTTPException) as exc:
                print(f"  failed: {exc}")
                last_error = exc
        else:
            raise RuntimeError(f"all mirrors failed: {last_error}")
    print("Extracting...")
    try:
        with tarfile.open(archive, "r:gz") as tar:
            tar.extractall(dest, filter="data")
    except (tarfile.TarError, EOFError, zlib.error) as exc:
        with contextlib.suppress(OSError):
            os.remove(archive)
        raise RuntimeError(
            f"archive was corrupt ({exc}) and has been deleted. Run download again."
        ) from exc
    root = find_dataset_root(dest)
    with open(marker, "w", encoding="utf-8") as fh:
        fh.write(root)
    return root


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m tests.benchmark.dataset")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("download")
    sub.add_parser("check")
    sub.add_parser("make-subsets")
    args = parser.parse_args(argv)

    if args.cmd == "download":
        print(f"Dataset ready at {download()}")
        return 0
    root = find_dataset_root()
    if args.cmd == "check":
        try:
            report = check(root)
        except ValueError as exc:
            print(f"PROBLEM {exc}")
            return 1
        for key, value in report.items():
            if key != "problems":
                print(f"{key:16s} {value}")
        for line in report["problems"][:50]:
            print("PROBLEM", line)
        print(f"{len(report['problems'])} problem(s)")
        return 1 if report["problems"] else 0
    dev = load_half(root, "dev")
    for name, n, seed in (SMOKE_SUBSET, SPEED_SUBSET):
        print(f"wrote {write_subset(name, make_subset(dev, n, seed))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
