"""Tests for routers/phonics.py and the phonics parts of the session routes.

Run from backend/:  python -m unittest tests.test_phonics_api
"""

import unittest
from datetime import datetime

from tests.phonics_helpers import (
    add_reading,
    join,
    make_class,
    make_client,
    make_db,
    make_pattern_session,
    make_user,
)

from core.phonics_data import get_pattern  # noqa: E402
from crud.phonics_sessions import get_phonics_activity  # noqa: E402
from models import Activity, Assignment, AssignmentStudent, Session  # noqa: E402
from routers import activities, phonics  # noqa: E402
from routers import session as session_router  # noqa: E402

AT = get_pattern("at-family")


class PhonicsApiTest(unittest.TestCase):
    def setUp(self):
        SessionLocal = make_db()
        self.db = SessionLocal()
        self.addCleanup(self.db.close)
        self.maya = make_user(self.db, "Maya")
        self.as_user = make_client(
            SessionLocal,
            ("/phonics", phonics.router),
            ("/session", session_router.router),
            ("/activities", activities.router),
        )
        self.client = self.as_user(self.maya)

    def start(self, slug="at-family"):
        return self.client.post("/phonics/sessions", json={"pattern_slug": slug})

    def test_start_creates_then_resumes(self):
        r = self.start()
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual((body["pattern_slug"], body["pattern_name"]), ("at-family", "-at Word Family"))
        self.assertEqual(self.start().json()["id"], body["id"])
        self.assertEqual(self.start("zz-family").status_code, 404)

    def test_path_points_at_the_first_pattern_not_mastered(self):
        self.assertEqual(self.client.get("/phonics/path").json()["next_slug"], "at-family")
        make_pattern_session(self.db, self.maya, "at-family", 10, 10, datetime(2026, 10, 1))
        path = self.client.get("/phonics/path").json()
        self.assertEqual(path["next_slug"], "an-family")
        self.assertEqual(path["units"][0]["patterns"][0]["status"], "mastered")

    def test_curriculum(self):
        units = self.client.get("/phonics/curriculum").json()["units"]
        self.assertEqual(len(units), 18)
        self.assertEqual(units[0]["patterns"][0], {"slug": "at-family", "name": "-at Word Family"})

    def test_assignments_reach_the_right_children(self):
        teacher = make_user(self.db, "Ms Rivera")
        leo = make_user(self.db, "Leo")
        cls = make_class(self.db, teacher, self.maya, leo)
        self.db.add(Assignment(class_id=cls.id, pattern_slug="sh-digraph", whole_class=True))
        group = Assignment(class_id=cls.id, pattern_slug="at-family", whole_class=False)
        group.students.append(AssignmentStudent(student_id=leo.id))
        self.db.add(group)
        self.db.add(Assignment(class_id=cls.id, pattern_slug="gone-family", whole_class=True))
        self.db.commit()

        mine = self.client.get("/phonics/assignments").json()
        self.assertEqual([a["pattern_slug"] for a in mine], ["sh-digraph"])
        self.assertEqual((mine[0]["class_name"], mine[0]["status"]), ("Room 4", "not_started"))
        self.assertEqual(mine[0]["unit_title"], "Digraphs")

        leos = self.as_user(leo).get("/phonics/assignments").json()
        self.assertEqual([a["pattern_slug"] for a in leos], ["at-family", "sh-digraph"])

        ava = make_user(self.db, "Ava")
        join(self.db, cls, ava)
        avas = self.as_user(ava).get("/phonics/assignments").json()
        self.assertEqual([a["pattern_slug"] for a in avas], ["sh-digraph"])

    def test_the_phonics_activity_is_hidden_and_needs_a_pattern(self):
        hidden = get_phonics_activity(self.db)
        self.db.add(Activity(title="Free", description="d", activity_type="unlimited", activity_settings={}))
        self.db.commit()
        listed = [a["activity_type"] for a in self.client.get("/activities/").json()]
        self.assertEqual(listed, ["unlimited"])
        self.assertEqual(self.client.post("/session/", json={"activity_id": hidden.id}).status_code, 400)

    def test_current_data_gives_the_line_to_read(self):
        session_id = self.start().json()["id"]
        state = self.client.get(f"/session/{session_id}/current-data").json()
        self.assertEqual(state["type"], "activity-settings")
        self.assertEqual(state["data"]["first_sentence"], AT["lines"][0])
        self.assertEqual((state["line_index"], state["line_count"]), (0, 7))

        session = self.db.get(Session, session_id)
        add_reading(self.db, session, AT["lines"][0], next_sentence=AT["lines"][1])
        state = self.client.get(f"/session/{session_id}/current-data").json()
        self.assertEqual(state["type"], "full-feedback-state")
        self.assertEqual(state["data"]["gpt_response"]["sentence"], AT["lines"][1])
        self.assertEqual((state["line_index"], state["line_count"]), (1, 7))

        add_reading(self.db, session, AT["lines"][1], next_sentence=AT["lines"][2])
        state = self.client.get(f"/session/{session_id}/current-data").json()
        self.assertEqual(state["line_index"], 2)
        self.assertEqual(state["data"]["gpt_response"]["sentence"], AT["lines"][2])

    def test_current_data_counts_readings_for_a_stale_line(self):
        session_id = self.start().json()["id"]
        session = self.db.get(Session, session_id)
        add_reading(self.db, session, AT["lines"][0], next_sentence="A line that was removed.")
        state = self.client.get(f"/session/{session_id}/current-data").json()
        self.assertEqual(state["line_index"], 1)

    def test_deactivating_a_pattern_session_scores_it(self):
        session_id = self.start().json()["id"]
        session = self.db.get(Session, session_id)
        add_reading(self.db, session, AT["lines"][0], next_sentence=AT["lines"][1])
        r = self.client.post(f"/session/{session_id}/deactivate")
        self.assertEqual(r.status_code, 200, r.text)
        self.assertTrue(r.json()["is_completed"])
        path = self.client.get("/phonics/path").json()
        self.assertEqual(path["units"][0]["patterns"][0]["status"], "mastered")


if __name__ == "__main__":
    unittest.main()
