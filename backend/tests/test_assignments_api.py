"""Tests for the teacher assignment routes (routers/assignments.py).

Run from backend/:  python -m unittest tests.test_assignments_api
"""

import unittest
from datetime import datetime

from tests.phonics_helpers import (
    join,
    make_class,
    make_client,
    make_db,
    make_pattern_session,
    make_user,
)

from models import Assignment, AssignmentStudent, ClassMembership  # noqa: E402
from routers import assignments  # noqa: E402

DAY = datetime(2026, 10, 1)


class AssignmentsApiTest(unittest.TestCase):
    def setUp(self):
        SessionLocal = make_db()
        self.db = SessionLocal()
        self.addCleanup(self.db.close)
        self.teacher = make_user(self.db, "Ms Rivera")
        self.maya = make_user(self.db, "Maya")
        self.leo = make_user(self.db, "Leo")
        self.cls = make_class(self.db, self.teacher, self.maya, self.leo)
        self.as_user = make_client(SessionLocal, ("/classes", assignments.router))
        self.url = f"/classes/{self.cls.id}/assignments"

    def assign(self, slugs, student_ids=None, user=None):
        return self.as_user(user or self.teacher).post(
            self.url, json={"pattern_slugs": slugs, "student_ids": student_ids}
        )

    def listed(self):
        return self.as_user(self.teacher).get(self.url).json()

    def test_whole_class_assignment_lists_everyone_in_curriculum_order(self):
        r = self.assign(["an-family", "at-family"])
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual([a["pattern_slug"] for a in body], ["at-family", "an-family"])
        self.assertTrue(body[0]["whole_class"])
        self.assertEqual(body[0]["pattern_name"], "-at Word Family")
        self.assertEqual(body[0]["unit_title"], "Short a word families")
        self.assertEqual(body[0]["counts"]["not_started"], 2)
        self.assertEqual({s["full_name"] for s in body[0]["students"]}, {"Maya", "Leo"})

    def test_status_comes_from_sessions(self):
        make_pattern_session(self.db, self.maya, "at-family", 9, 10, DAY)
        body = self.assign(["at-family"]).json()
        maya = next(s for s in body[0]["students"] if s["full_name"] == "Maya")
        self.assertEqual((maya["status"], maya["words_correct"], maya["tries"]), ("mastered", 9, 1))
        self.assertEqual(
            body[0]["counts"],
            {"mastered": 1, "needs_practice": 0, "in_progress": 0, "not_started": 1},
        )

    def test_only_the_teacher_can_assign_or_view(self):
        self.assertEqual(self.assign(["at-family"], user=self.maya).status_code, 403)
        self.assertEqual(self.as_user(self.maya).get(self.url).status_code, 403)
        self.assertEqual(self.as_user(self.teacher).get("/classes/999/assignments").status_code, 404)

    def test_bad_requests_are_refused(self):
        outsider = make_user(self.db, "Sam")
        unknown = self.assign(["at-family", "zz-family"])
        self.assertEqual(unknown.status_code, 400)
        self.assertIn("zz-family", unknown.json()["detail"])
        self.assertEqual(self.assign(["at-family"], [outsider.id]).status_code, 400)
        self.assertEqual(self.assign(["at-family"], []).status_code, 400)
        self.assertEqual(self.assign([]).status_code, 400)
        self.assertEqual(self.listed(), [])

    def test_assigning_again_merges_into_one_assignment(self):
        self.assign(["at-family"], [self.maya.id])
        body = self.assign(["at-family"], [self.leo.id]).json()
        self.assertEqual(len(body), 1)
        self.assertFalse(body[0]["whole_class"])
        self.assertEqual({s["full_name"] for s in body[0]["students"]}, {"Maya", "Leo"})
        self.assertTrue(self.assign(["at-family"]).json()[0]["whole_class"])

    def test_whole_class_work_follows_membership(self):
        self.assign(["at-family"])
        ava = make_user(self.db, "Ava")
        join(self.db, self.cls, ava)
        self.db.query(ClassMembership).filter_by(student_id=self.leo.id).delete()
        self.db.commit()
        names = {s["full_name"] for s in self.listed()[0]["students"]}
        self.assertEqual(names, {"Maya", "Ava"})

    def test_duplicate_student_ids_are_fine(self):
        r = self.assign(["at-family"], [self.maya.id, self.maya.id])
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(len(body), 1)
        self.assertEqual([s["full_name"] for s in body[0]["students"]], ["Maya"])

    def test_chosen_students_who_leave_drop_off(self):
        self.assign(["at-family"], [self.maya.id, self.leo.id])
        self.db.query(ClassMembership).filter_by(student_id=self.leo.id).delete()
        self.db.commit()
        self.assertEqual([s["full_name"] for s in self.listed()[0]["students"]], ["Maya"])

    def test_switching_to_whole_class_clears_the_list(self):
        self.assign(["at-family"], [self.maya.id])
        self.assign(["at-family"])
        self.db.expire_all()
        self.assertEqual(self.db.query(AssignmentStudent).count(), 0)

    def test_another_teacher_is_refused(self):
        other = make_user(self.db, "Mr Lee")
        self.assertEqual(self.assign(["at-family"], user=other).status_code, 403)
        self.assertEqual(self.as_user(other).get(self.url).status_code, 403)

    def test_delete(self):
        assignment_id = self.assign(["at-family"]).json()[0]["id"]
        other = make_class(self.db, self.teacher, name="Room 5")
        client = self.as_user(self.teacher)
        self.assertEqual(client.delete(f"/classes/{other.id}/assignments/{assignment_id}").status_code, 404)
        self.assertEqual(client.delete(f"{self.url}/{assignment_id}").status_code, 204)
        self.assertEqual(self.listed(), [])

    def test_a_removed_pattern_shows_as_unavailable(self):
        self.db.add(Assignment(class_id=self.cls.id, pattern_slug="gone-family", whole_class=True))
        self.db.commit()
        body = self.listed()
        self.assertEqual((body[0]["pattern_slug"], body[0]["pattern_name"]), ("gone-family", None))

    def test_class_grid_and_one_student_path(self):
        make_pattern_session(self.db, self.maya, "at-family", 9, 10, DAY)
        client = self.as_user(self.teacher)
        grid = client.get(f"/classes/{self.cls.id}/phonics-progress").json()
        self.assertEqual(len(grid["units"]), 18)
        self.assertEqual(
            {row["full_name"]: row["statuses"] for row in grid["students"]},
            {"Maya": {"at-family": "mastered"}, "Leo": {}},
        )
        path = client.get(f"/classes/{self.cls.id}/students/{self.maya.id}/phonics-path").json()
        self.assertEqual(path["next_slug"], "an-family")

        outsider = make_user(self.db, "Sam")
        self.assertEqual(
            client.get(f"/classes/{self.cls.id}/students/{outsider.id}/phonics-path").status_code, 404
        )
        self.assertEqual(
            self.as_user(self.maya).get(f"/classes/{self.cls.id}/phonics-progress").status_code, 403
        )


if __name__ == "__main__":
    unittest.main()
