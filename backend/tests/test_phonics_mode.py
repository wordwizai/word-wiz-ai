"""Tests for the phonics pattern mode and its end of the audio stream.

Run from backend/:  python -m unittest tests.test_phonics_mode

The stream test stubs audio loading, the model and the audio cache, so it
needs no recording, model or API keys.
"""

import asyncio
import json
import types
import unittest
from unittest import mock

from tests.phonics_helpers import make_db, make_user

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from fastapi import HTTPException  # noqa: E402

from core.modes.phonics_pattern import PhonicsPatternPractice, phonics_mode_for  # noqa: E402
from core.phonics_data import get_pattern  # noqa: E402
from crud.phonics_sessions import start_pattern_session  # noqa: E402
from routers.handlers import audio_processing_handler as handler  # noqa: E402

AT = get_pattern("at-family")


def next_for(sentence, readings_so_far=0):
    session = types.SimpleNamespace(feedback_entries=[object()] * readings_so_far)
    mode = PhonicsPatternPractice(AT)
    return asyncio.run(mode.get_next_sentence(sentence, None, None, session))


class ModeTest(unittest.TestCase):
    def test_gives_the_next_line(self):
        self.assertEqual(
            next_for(AT["lines"][0]),
            {"sentence": AT["lines"][1], "line_index": 1, "line_count": 7},
        )

    def test_reading_a_line_again_does_not_skip_ahead(self):
        self.assertEqual(next_for(AT["lines"][0], readings_so_far=3)["sentence"], AT["lines"][1])

    def test_the_last_line_ends_the_session(self):
        self.assertEqual(
            next_for(AT["lines"][-1], readings_so_far=6),
            {"session_complete": True, "line_index": 6, "line_count": 7},
        )

    def test_an_unknown_sentence_falls_back_to_counting(self):
        self.assertEqual(next_for("Something else.", readings_so_far=2)["sentence"], AT["lines"][3])

    def test_a_missing_pattern_is_a_404(self):
        with self.assertRaises(HTTPException) as caught:
            phonics_mode_for(types.SimpleNamespace(pattern_slug="gone-family"))
        self.assertEqual(caught.exception.status_code, 404)


class FakeAssistant:
    """Scores every word of the sentence at `per`, with no model."""

    def __init__(self, per=0.0):
        self.per = per

    async def process_audio(self, sentence, audio, verbose=False):
        words = [word.strip(".,!?").lower() for word in sentence.split()]
        df = pd.DataFrame([
            {"ground_truth_word": word, "predicted_word": word, "per": self.per,
             "ground_truth_phonemes": ["k"], "predicted_phonemes": ["k"],
             "missed": [], "added": [], "substituted": []}
            for word in words
        ])
        return df, {"word": words[0], "per": self.per}, {"most_common_errors": []}, {"sentence_per": self.per}

    def feedback_to_audio(self, text, ssml=None):
        return {"data": "UklGRg==", "filename": "feedback.wav", "mimetype": "audio/wav"}


class StreamTest(unittest.TestCase):
    def setUp(self):
        async def fake_load(*args, **kwargs):
            return np.ones(16000, dtype="float32"), "cache-id"

        for target, value in [
            ("load_and_preprocess_audio_bytes", fake_load),
            ("check_speech_activity", lambda audio, quality: None),
            ("audio_cache", mock.Mock()),
        ]:
            patcher = mock.patch.object(handler, target, value)
            patcher.start()
            self.addCleanup(patcher.stop)

        self.db = make_db()()
        self.addCleanup(self.db.close)
        self.child = make_user(self.db, "Maya")
        self.session = start_pattern_session(self.db, self.child.id, "at-family")

    def read(self, line):
        async def go():
            return [chunk async for chunk in handler.analyze_audio_file_event_stream(
                phoneme_assistant=FakeAssistant(),
                activity_object=PhonicsPatternPractice(AT),
                audio_bytes=b"x",
                audio_filename="r.wav",
                audio_content_type="audio/wav",
                attempted_sentence=line,
                db=self.db,
                current_user=self.child,
                session=self.session,
            )]
        chunks = asyncio.run(go())
        events = [json.loads(l[6:]) for c in chunks for l in c.splitlines() if l.startswith("data: ")]
        return {event["type"]: event for event in events}

    def test_reads_through_to_the_finish(self):
        for i, line in enumerate(AT["lines"][:-1]):
            events = self.read(line)
            self.assertNotIn("error", events)
            self.assertNotIn("session_complete", events)
            self.assertEqual(
                events["next_sentence"]["data"],
                {"sentence": AT["lines"][i + 1], "line_index": i + 1, "line_count": 7},
            )

        events = self.read(AT["lines"][-1])
        self.assertNotIn("next_sentence", events)
        result = events["session_complete"]["data"]
        self.assertTrue(result["mastered"])
        self.assertEqual(result["words_correct"], result["words_total"])
        self.assertGreater(result["words_total"], len(AT["words"]))
        self.db.refresh(self.session)
        self.assertEqual(self.session.is_completed, 1)


if __name__ == "__main__":
    unittest.main()
