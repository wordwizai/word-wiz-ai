"""Tests for the public "try it" route (routers/guest.py).

Run from backend/:  python -m unittest tests.test_guest_router

These never load the ONNX model, call Deepgram/Google, or touch the real
database: the router is mounted on a bare FastAPI app, the assistant is a fake,
the heavy stream is patched where a test only cares about the router's checks,
and the guest-user tests get a throwaway in-memory database.
"""

import asyncio
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd
from fastapi import FastAPI
from fastapi.testclient import TestClient

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

# The handler module imports the SQLAlchemy models, and database.py builds an
# engine at import. These tests never use it, but point it at an in-memory
# SQLite database so they can never reach the shared RDS instance in .env.
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from core.guest_limits import SlidingWindowLimiter, client_ip, normalize_sentence  # noqa: E402
from database import get_db  # noqa: E402
from models import User  # noqa: E402
from tests.phonics_helpers import make_db  # noqa: E402
from routers import guest  # noqa: E402
from routers.handlers import audio_processing_handler as handler  # noqa: E402

ALLOWED = "Jake made a cake for the game."


def sse_events(body: str) -> list[dict]:
    return [json.loads(line[6:]) for line in body.splitlines() if line.startswith("data: ")]


class FakeAssistant:
    def __init__(self):
        self.process_calls = []

    async def process_audio(self, sentence, audio, verbose=False):
        self.process_calls.append(sentence)
        df = pd.DataFrame(
            [{"ground_truth_word": "cake", "predicted_word": "cak", "per": 0.33,
              "ground_truth_phonemes": ["k", "eɪ", "k"], "predicted_phonemes": ["k", "æ", "k"],
              "missed": ["eɪ"], "added": ["æ"], "substituted": [("eɪ", "æ")]}]
        )
        return df, {"word": "cake", "per": 0.33}, {"most_common_errors": []}, {"sentence_per": 0.1}

    def feedback_to_audio(self, text, ssml=None):
        return {"data": "UklGRg==", "filename": "feedback.wav", "mimetype": "audio/wav"}


def make_client(assistant=None, SessionLocal=None):
    app = FastAPI()
    app.include_router(guest.router, prefix="/guest")
    app.dependency_overrides[guest.get_phoneme_assistant] = lambda: assistant or FakeAssistant()
    if SessionLocal is not None:
        def override_db():
            db = SessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_db
    return TestClient(app)


def post(client, sentence=ALLOWED, audio=b"RIFF0000WAVE", headers=None, guest_id=None):
    data = {"attempted_sentence": sentence}
    if guest_id is not None:
        data["guest_id"] = guest_id
    return client.post(
        "/guest/analyze-audio",
        data=data,
        files={"audio_file": ("r.wav", audio, "audio/wav")},
        headers=headers or {},
    )


async def fake_stream(**kwargs):
    yield 'data: {"type": "complete", "data": {}}\n\n'


class FreshLimits(unittest.TestCase):
    """Give every test its own limiters and slots so tests don't leak counts."""

    def setUp(self):
        patches = [
            mock.patch.object(guest, "PER_IP_BURST", SlidingWindowLimiter(15, 600)),
            mock.patch.object(guest, "PER_IP_DAILY", SlidingWindowLimiter(60, 86400)),
            mock.patch.object(guest, "SITE_HOURLY", SlidingWindowLimiter(400, 3600)),
            mock.patch.object(guest, "_guest_slots", asyncio.Semaphore(guest.GUEST_CONCURRENCY)),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)


class RouterChecksTest(FreshLimits):
    def setUp(self):
        super().setUp()
        p = mock.patch.object(guest, "analyze_audio_guest_event_stream", side_effect=fake_stream)
        self.stream = p.start()
        self.addCleanup(p.stop)
        self.client = make_client()

    def test_allowed_sentence_streams(self):
        r = post(self.client)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(sse_events(r.text)[-1]["type"], "complete")

    def test_sentence_match_ignores_case_quotes_and_spacing(self):
        r = post(self.client, sentence="  jake MADE a cake   for the game. ")
        self.assertEqual(r.status_code, 200)

    def test_unknown_sentence_is_refused_before_any_work(self):
        r = post(self.client, sentence="Please transcribe this arbitrary sentence for me.")
        self.assertEqual(r.status_code, 400)
        self.stream.assert_not_called()

    def test_oversized_audio_is_refused(self):
        r = post(self.client, audio=b"0" * (guest.MAX_AUDIO_BYTES + 1))
        self.assertEqual(r.status_code, 413)
        self.stream.assert_not_called()

    def test_per_ip_burst_limit(self):
        for _ in range(15):
            self.assertEqual(post(self.client).status_code, 200)
        r = post(self.client)
        self.assertEqual(r.status_code, 429)
        self.assertIn("free account", r.json()["detail"])

    def test_refused_requests_do_not_use_up_quota(self):
        for _ in range(20):
            post(self.client, sentence="not on the list")
        self.assertEqual(post(self.client).status_code, 200)

    def test_slots_are_released_after_each_stream(self):
        for _ in range(guest.GUEST_CONCURRENCY + 3):
            self.assertEqual(post(self.client).status_code, 200)
        self.assertEqual(guest._guest_slots._value, guest.GUEST_CONCURRENCY)


class GuestUserTest(FreshLimits):
    """Each browser that reads a sentence is counted once as a guest user."""

    GUEST_ID = "6f1c2b9e-3d4a-4f5b-8c7d-9e0a1b2c3d4e"

    def setUp(self):
        super().setUp()
        p = mock.patch.object(guest, "analyze_audio_guest_event_stream", side_effect=fake_stream)
        p.start()
        self.addCleanup(p.stop)
        self.SessionLocal = make_db()
        self.client = make_client(SessionLocal=self.SessionLocal)

    def guests(self):
        db = self.SessionLocal()
        try:
            return [(u.username, u.is_guest) for u in db.query(User).all()]
        finally:
            db.close()

    def test_readings_from_one_browser_add_one_guest(self):
        for _ in range(3):
            self.assertEqual(post(self.client, guest_id=self.GUEST_ID).status_code, 200)
        self.assertEqual(self.guests(), [(f"guest-{self.GUEST_ID}", True)])

    def test_each_browser_is_its_own_guest(self):
        post(self.client, guest_id=self.GUEST_ID)
        post(self.client, guest_id="0b4e7d1a-2c3f-4a5b-9c8d-7e6f5a4b3c2d")
        self.assertEqual(len(self.guests()), 2)

    def test_no_or_invalid_guest_id_adds_nothing(self):
        self.assertEqual(post(self.client).status_code, 200)
        self.assertEqual(post(self.client, guest_id="nope").status_code, 200)
        self.assertEqual(self.guests(), [])

    def test_refused_readings_add_nothing(self):
        post(self.client, sentence="not on the list", guest_id=self.GUEST_ID)
        post(self.client, audio=b"0" * (guest.MAX_AUDIO_BYTES + 1), guest_id=self.GUEST_ID)
        self.assertEqual(self.guests(), [])

    def test_rate_limited_readings_add_nothing(self):
        for _ in range(15):
            post(self.client)
        self.assertEqual(post(self.client, guest_id=self.GUEST_ID).status_code, 429)
        self.assertEqual(self.guests(), [])

    def test_a_database_error_still_gives_feedback(self):
        with mock.patch.object(guest, "record_guest_user", side_effect=RuntimeError("db down")):
            r = post(self.client, guest_id=self.GUEST_ID)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(sse_events(r.text)[-1]["type"], "complete")


class ClientIpTest(unittest.TestCase):
    def test_trusts_real_ip_from_private_peer(self):
        self.assertEqual(client_ip("172.18.0.3", {"x-real-ip": "203.0.113.9"}), "203.0.113.9")

    def test_ignores_header_from_public_peer(self):
        # A real public address: Python counts the RFC 5737 documentation
        # ranges (198.51.100.0/24 etc.) as private, so they can't stand in here.
        self.assertEqual(client_ip("8.8.8.8", {"x-real-ip": "1.2.3.4"}), "8.8.8.8")

    def test_ignores_garbage_header(self):
        self.assertEqual(client_ip("127.0.0.1", {"x-real-ip": "not-an-ip"}), "127.0.0.1")


class SlidingWindowTest(unittest.TestCase):
    def test_window_expires(self):
        now = [0.0]
        lim = SlidingWindowLimiter(2, 10, clock=lambda: now[0])
        self.assertTrue(lim.hit("a"))
        self.assertTrue(lim.hit("a"))
        self.assertFalse(lim.hit("a"))
        self.assertTrue(lim.hit("b"))
        now[0] = 10.0
        self.assertTrue(lim.hit("a"))
        lim.prune()
        now[0] = 100.0
        lim.prune()
        self.assertEqual(dict(lim._events), {})


class GuestStreamTest(unittest.TestCase):
    """The stream itself, with preprocessing stubbed (no real audio needed)."""

    def run_stream(self, assistant):
        async def go():
            return [c async for c in handler.analyze_audio_guest_event_stream(
                phoneme_assistant=assistant,
                audio_bytes=b"x",
                audio_filename="r.wav",
                audio_content_type="audio/wav",
                attempted_sentence=ALLOWED,
            )]
        return [e for c in asyncio.run(go()) for e in sse_events(c)]

    def setUp(self):
        async def fake_load(*args, **kwargs):
            self.load_kwargs = kwargs
            return np.ones(16000, dtype="float32"), "cache-id"

        for target, value in [
            ("load_and_preprocess_audio_bytes", fake_load),
            ("check_speech_activity", lambda audio, q: None),
        ]:
            p = mock.patch.object(handler, target, value)
            p.start()
            self.addCleanup(p.stop)

    def test_event_order_and_no_caching(self):
        assistant = FakeAssistant()
        events = self.run_stream(assistant)
        self.assertEqual(
            [e["type"] for e in events],
            ["processing_started", "analysis", "feedback", "audio_feedback_file", "complete"],
        )
        self.assertEqual(assistant.process_calls, [ALLOWED])
        self.assertIs(self.load_kwargs["cache_audio"], False)
        self.assertEqual(self.load_kwargs["max_duration_seconds"], handler.GUEST_MAX_AUDIO_SECONDS)

    def test_tts_failure_still_completes(self):
        assistant = FakeAssistant()
        assistant.feedback_to_audio = mock.Mock(side_effect=RuntimeError("tts down"))
        types = [e["type"] for e in self.run_stream(assistant)]
        self.assertEqual(types, ["processing_started", "analysis", "feedback", "complete"])

    def test_scoring_failure_is_a_friendly_error(self):
        assistant = FakeAssistant()

        async def boom(*a, **k):
            raise RuntimeError("model exploded")

        assistant.process_audio = boom
        events = self.run_stream(assistant)
        self.assertEqual(events[-1]["type"], "error")
        self.assertNotIn("exploded", events[-1]["data"]["message"])


class AllowlistTest(unittest.TestCase):
    def test_allowlist_matches_frontend_data(self):
        result = subprocess.run(
            [sys.executable, str(BACKEND / "scripts" / "export_phonics_data.py"), "--check"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_normalize(self):
        self.assertEqual(normalize_sentence(" Don’t  RUN "), "don't run")


if __name__ == "__main__":
    unittest.main()
