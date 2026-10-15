"""Tests for the audio-analysis WebSocket (/ai/ws/audio-analysis in routers/ai.py).

Run from backend/:  PYTHONUTF8=1 python -m unittest tests.test_ws_audio_analysis

These never load the phoneme model or call OpenAI/Google: the module-level
PhonemeAssistant is swapped for a fake before routers.ai is imported, the
activity is a fake, and the database is a throwaway in-memory SQLite one.
"""

import base64
import contextlib
import io
import json
import os
import unittest
from unittest import mock

from tests.phonics_helpers import make_db, make_user

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from jose import jwt  # noqa: E402

import core.phoneme_assistant  # noqa: E402
from models import Activity, FeedbackEntry, Session  # noqa: E402
from routers.handlers import audio_processing_handler as handler  # noqa: E402

SECRET = "ws-test-secret"
SENTENCE = "The cat sat."
# "the cat sat" read as "the tat sat", as the browser's phoneme model would send it.
CLIENT_PHONEMES = [["ð", "ə"], ["t", "æ", "t"], ["s", "æ", "t"]]
CLIENT_WORDS = ["the", "cat", "sat"]


class FakeAssistant:
    word_extractor = None

    def feedback_to_audio(self, text, ssml=None):
        return {"data": base64.b64encode(b"mp3").decode(), "filename": "f.mp3", "mimetype": "audio/mpeg"}


class FakeActivity:
    async def get_next_sentence(self, **_kwargs):
        return {"sentence": "The dog ran."}


# routers.ai builds a PhonemeAssistant at import, which loads the ONNX model.
with mock.patch.object(core.phoneme_assistant, "PhonemeAssistant", FakeAssistant):
    from routers import ai  # noqa: E402


class WebSocketAudioAnalysisTest(unittest.TestCase):
    def setUp(self):
        self.SessionLocal = make_db()
        with self.SessionLocal() as db:
            user = make_user(db, "Pat Reader")
            activity = Activity(title="Free", description="d", activity_type="unlimited", activity_settings={})
            db.add(activity)
            db.commit()
            session = Session(user_id=user.id, activity_id=activity.id)
            db.add(session)
            db.commit()
            self.username, self.session_id = user.username, session.id

        def fresh_db():
            yield self.SessionLocal()

        stack = contextlib.ExitStack()
        self.addCleanup(stack.close)
        # The socket opens its own database session instead of using Depends(get_db).
        stack.enter_context(mock.patch.object(ai, "get_db", fresh_db))
        stack.enter_context(mock.patch.object(ai, "phoneme_assistant", FakeAssistant()))
        stack.enter_context(mock.patch.object(ai, "get_activity_object", lambda _session: FakeActivity()))
        stack.enter_context(mock.patch.object(handler.audio_cache, "save_feedback_audio"))
        stack.enter_context(mock.patch.dict(os.environ, {"SECRET_KEY": SECRET}))
        stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
        os.environ.pop("WWAI_GT_ANCHORED_ALIGNMENT", None)

        app = FastAPI()
        app.include_router(ai.router, prefix="/ai")
        self.client = TestClient(app)

    def message(self, **fields):
        message = {
            "type": "analyze_audio",
            "audio_base64": "",
            "attempted_sentence": SENTENCE,
            "session_id": self.session_id,
            "filename": "empty.wav",
            "content_type": "audio/wav",
            "client_phonemes": CLIENT_PHONEMES,
            "client_words": CLIENT_WORDS,
        }
        message.update(fields)
        return message

    def read(self, message):
        """Send one message, then a ping, and return every event before the pong.

        The socket answers messages in order, so the pong comes after the last
        event of the reading, and a broken reading fails instead of hanging.
        """
        token = jwt.encode({"sub": self.username}, SECRET, algorithm="HS256")
        with self.client.websocket_connect(f"/ai/ws/audio-analysis?token={token}") as ws:
            ws.send_text(json.dumps(message))
            ws.send_text(json.dumps({"type": "ping"}))
            events = []
            while (event := ws.receive_json())["type"] != "pong":
                events.append(event)
        return events

    def stored_readings(self):
        with self.SessionLocal() as db:
            return db.query(FeedbackEntry).filter_by(session_id=self.session_id).count()

    def test_a_reading_extracted_in_the_browser_is_scored_without_audio(self):
        # useHybridAudioAnalysis.ts sends an empty file when the browser extracted
        # both phonemes and words. FileReader turns it into "" (Chrome and Firefox
        # today), and a browser that gives no base64 part leaves the key out.
        missing = self.message()
        del missing["audio_base64"]
        for label, message in (("empty", self.message()), ("missing", missing)):
            with self.subTest(audio=label):
                before = self.stored_readings()
                events = self.read(message)
                types = [e["type"] for e in events]
                self.assertNotIn("error", types, events)
                for expected in ("analysis", "feedback", "next_sentence", "audio_feedback_file"):
                    self.assertIn(expected, types)
                mode = next(e for e in events if e["type"] == "processing_mode")["data"]["mode"]
                self.assertEqual(mode, "client")
                df = next(e for e in events if e["type"] == "analysis")["data"]["pronunciation_dataframe"]
                words = [df["ground_truth_word"][k] for k in sorted(df["ground_truth_word"], key=int)]
                self.assertEqual(words, ["the", "cat", "sat"])
                self.assertEqual(self.stored_readings(), before + 1)

    def test_no_audio_and_no_browser_extraction_is_an_error(self):
        events = self.read(self.message(client_phonemes=None, client_words=None))
        types = [e["type"] for e in events]
        self.assertEqual(types[-1], "error")
        self.assertNotIn("analysis", types)
        self.assertEqual(self.stored_readings(), 0)

    def test_missing_sentence_or_session_is_refused_before_any_work(self):
        for field in ("attempted_sentence", "session_id"):
            with self.subTest(missing=field):
                message = self.message()
                del message[field]
                events = self.read(message)
                self.assertEqual([e["type"] for e in events], ["error"])
                self.assertIn("Missing required fields", events[0]["data"]["message"])


if __name__ == "__main__":
    unittest.main()
