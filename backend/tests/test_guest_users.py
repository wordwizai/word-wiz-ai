"""Tests for try-mode guest users (crud/guest_users.py) and signing up from one.

Run from backend/:  python -m unittest tests.test_guest_users
"""

import os
import unittest
import uuid
from unittest import mock

from tests.phonics_helpers import make_db

from fastapi import FastAPI  # noqa: E402
from fastapi.responses import RedirectResponse  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from starlette.middleware.sessions import SessionMiddleware  # noqa: E402

from auth.auth_handler import authenticate_user  # noqa: E402
from crud.guest_users import parse_guest_id, record_guest_user, upgrade_guest_user  # noqa: E402
from database import get_db  # noqa: E402
from models import User  # noqa: E402
from routers import auth, google_auth  # noqa: E402

GUEST_ID = "6f1c2b9e-3d4a-4f5b-8c7d-9e0a1b2c3d4e"


def app_with(SessionLocal, *routes, sessions=False):
    app = FastAPI()
    if sessions:
        app.add_middleware(SessionMiddleware, secret_key="test")
    for prefix, router in routes:
        app.include_router(router, prefix=prefix)

    def override_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    return TestClient(app)


class GuestUserCrudTest(unittest.TestCase):
    def setUp(self):
        self.db = make_db()()
        self.addCleanup(self.db.close)

    def test_one_row_per_browser(self):
        first = record_guest_user(self.db, GUEST_ID)
        again = record_guest_user(self.db, GUEST_ID)
        self.assertEqual(first.id, again.id)
        self.assertTrue(first.is_guest)
        self.assertIsNone(first.email)
        self.assertIsNone(first.hashed_password)
        self.assertEqual(self.db.query(User).count(), 1)

    def test_id_spellings_are_the_same_browser(self):
        record_guest_user(self.db, GUEST_ID)
        record_guest_user(self.db, GUEST_ID.upper())
        record_guest_user(self.db, GUEST_ID.replace("-", ""))
        self.assertEqual(self.db.query(User).count(), 1)

    def test_invalid_ids_add_nothing(self):
        for raw in (None, "", "not-a-uuid", "x" * 500):
            self.assertIsNone(record_guest_user(self.db, raw))
        self.assertEqual(self.db.query(User).count(), 0)

    def test_guest_rows_cannot_sign_in(self):
        guest = record_guest_user(self.db, GUEST_ID)
        self.assertFalse(authenticate_user(self.db, guest.username, ""))

    def test_upgrade_turns_the_guest_into_an_account_with_settings(self):
        guest = record_guest_user(self.db, GUEST_ID)
        user = upgrade_guest_user(
            self.db, GUEST_ID, username="maya", email="maya@example.test",
            full_name="Maya", hashed_password="hash",
        )
        self.assertEqual(user.id, guest.id)
        self.assertFalse(user.is_guest)
        self.assertIsNotNone(user.settings)
        self.assertEqual(self.db.query(User).count(), 1)

    def test_upgrade_without_a_guest_row_returns_none(self):
        self.assertIsNone(upgrade_guest_user(
            self.db, str(uuid.uuid4()), username="maya", email="maya@example.test",
            full_name="Maya", hashed_password="hash",
        ))

    def test_an_upgraded_row_is_no_longer_a_guest(self):
        record_guest_user(self.db, GUEST_ID)
        upgrade_guest_user(
            self.db, GUEST_ID, username="maya", email="maya@example.test",
            full_name="Maya", hashed_password="hash",
        )
        # Same browser, signed out, trying again: a new guest, not the account.
        guest = record_guest_user(self.db, GUEST_ID)
        self.assertTrue(guest.is_guest)
        self.assertEqual(self.db.query(User).count(), 2)


class RegisterFromGuestTest(unittest.TestCase):
    def setUp(self):
        self.SessionLocal = make_db()
        self.db = self.SessionLocal()
        self.addCleanup(self.db.close)
        self.client = app_with(self.SessionLocal, ("/auth", auth.router))

    def register(self, **extra):
        return self.client.post("/auth/register", json={
            "username": "maya", "email": "maya@example.test",
            "password": "correct horse", "full_name": "Maya", **extra,
        })

    def users(self):
        self.db.expire_all()
        return self.db.query(User).all()

    def test_signup_takes_over_the_guest_row(self):
        guest_row_id = record_guest_user(self.db, GUEST_ID).id
        r = self.register(guest_id=GUEST_ID)
        self.assertEqual(r.status_code, 200, r.text)
        [user] = self.users()
        self.assertEqual(user.id, guest_row_id)
        self.assertFalse(user.is_guest)
        self.assertEqual((user.username, user.email), ("maya", "maya@example.test"))
        self.assertTrue(authenticate_user(self.db, "maya@example.test", "correct horse"))

    def test_signup_without_a_guest_id_adds_a_row(self):
        record_guest_user(self.db, GUEST_ID)
        self.assertEqual(self.register().status_code, 200)
        self.assertEqual(sorted(u.is_guest for u in self.users()), [False, True])

    def test_unknown_guest_id_still_signs_up(self):
        self.assertEqual(self.register(guest_id=str(uuid.uuid4())).status_code, 200)
        [user] = self.users()
        self.assertFalse(user.is_guest)


class GoogleSignupFromGuestTest(unittest.TestCase):
    USERINFO = {"email": "leo@example.test", "name": "Leo", "email_verified": True}

    def setUp(self):
        self.SessionLocal = make_db()
        self.db = self.SessionLocal()
        self.addCleanup(self.db.close)
        self.client = app_with(
            self.SessionLocal, ("/auth/google", google_auth.router), sessions=True
        )
        patches = [
            mock.patch.dict(os.environ, {"FRONTEND_URL": "https://example.test"}),
            mock.patch.object(
                google_auth.oauth.google, "authorize_redirect",
                side_effect=lambda *a, **k: RedirectResponse("https://accounts.example.test"),
            ),
            mock.patch.object(
                google_auth.oauth.google, "authorize_access_token",
                side_effect=lambda *a, **k: {"userinfo": self.USERINFO},
            ),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def sign_in(self, login_url):
        self.client.get(login_url, follow_redirects=False)
        return self.client.get("/auth/google/callback", follow_redirects=False)

    def users(self):
        self.db.expire_all()
        return self.db.query(User).all()

    def test_new_google_account_takes_over_the_guest_row(self):
        guest_row_id = record_guest_user(self.db, GUEST_ID).id
        r = self.sign_in(f"/auth/google/login?guest_id={GUEST_ID}")
        self.assertEqual(r.status_code, 307, r.text)
        [user] = self.users()
        self.assertEqual(user.id, guest_row_id)
        self.assertFalse(user.is_guest)
        self.assertEqual(user.email, "leo@example.test")

    def test_login_without_guest_id_ignores_an_earlier_abandoned_one(self):
        record_guest_user(self.db, GUEST_ID)
        self.client.get(f"/auth/google/login?guest_id={GUEST_ID}", follow_redirects=False)
        self.sign_in("/auth/google/login")
        self.assertEqual(sorted(u.is_guest for u in self.users()), [False, True])


class ParseGuestIdTest(unittest.TestCase):
    def test_canonical_form(self):
        self.assertEqual(parse_guest_id(GUEST_ID.upper()), GUEST_ID)
        self.assertEqual(parse_guest_id(f"  {GUEST_ID}  "), GUEST_ID)


if __name__ == "__main__":
    unittest.main()
