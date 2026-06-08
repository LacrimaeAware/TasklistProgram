import unittest
from datetime import date, timedelta

from tasklistprogram import webserver as ws


def fresh_db():
    return {"version": 1, "tasks": [], "next_id": 1}


class AdapterTests(unittest.TestCase):
    def test_to_client_maps_done_and_times(self):
        c = ws.to_client({"id": 1, "title": "x", "completed_at": "2026-01-01T00:00:00",
                          "times_completed": 5, "priority": "H"})
        self.assertTrue(c["done"])
        self.assertEqual(c["times"], 5)
        self.assertEqual(c["priority"], "H")

    def test_visible_excludes_deleted(self):
        db = {"tasks": [{"id": 1, "is_deleted": True}, {"id": 2}]}
        self.assertEqual([t["id"] for t in ws.visible_tasks(db)], [2])


class OpAddTests(unittest.TestCase):
    def test_add_basic(self):
        db = fresh_db()
        t = ws.op_add(db, {"title": "Write report", "priority": "H"})
        self.assertEqual(t["title"], "Write report")
        self.assertEqual(t["priority"], "H")
        self.assertEqual(db["next_id"], 2)

    def test_add_requires_title(self):
        with self.assertRaises(ValueError):
            ws.op_add(fresh_db(), {"title": "   "})

    def test_add_misc_maps_to_x_and_daily_for_d(self):
        db = fresh_db()
        self.assertEqual(ws.op_add(db, {"title": "a", "priority": "Misc"})["priority"], "X")
        d = ws.op_add(db, {"title": "b", "priority": "D"})
        self.assertEqual(d["repeat"], "daily")

    def test_add_parses_due(self):
        t = ws.op_add(fresh_db(), {"title": "a", "due": "tomorrow"})
        self.assertEqual(t["due"], (date.today() + timedelta(days=1)).strftime("%Y-%m-%d"))


class OpDoneTests(unittest.TestCase):
    def test_mark_done_oneoff(self):
        t = {"id": 1, "title": "a", "repeat": "none", "due": "", "completed_at": "", "times_completed": 0}
        ws.op_mark_done(t)
        self.assertTrue(t["completed_at"])
        self.assertEqual(t["times_completed"], 1)
        self.assertEqual(len(t["history"]), 1)

    def test_mark_done_recurring_advances_and_stays_active(self):
        today = date.today().strftime("%Y-%m-%d")
        t = {"id": 1, "title": "a", "repeat": "daily", "due": today, "completed_at": "", "times_completed": 0}
        ws.op_mark_done(t)
        self.assertEqual(t["completed_at"], "")  # resets for next cycle
        self.assertEqual(t["due"], (date.today() + timedelta(days=1)).strftime("%Y-%m-%d"))
        self.assertEqual(t["times_completed"], 1)

    def test_toggle_undo(self):
        t = {"id": 1, "repeat": "none", "due": "", "completed_at": "x"}
        ws.op_toggle(t)
        self.assertEqual(t["completed_at"], "")

    def test_toggle_marks_done_when_open(self):
        t = {"id": 1, "repeat": "none", "due": "", "completed_at": "", "times_completed": 0}
        ws.op_toggle(t)
        self.assertTrue(t["completed_at"])


if __name__ == "__main__":
    unittest.main()
