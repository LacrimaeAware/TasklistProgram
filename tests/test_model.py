import unittest
from datetime import datetime, date, timedelta

from tasklistprogram.core import model


class SettingsTests(unittest.TestCase):
    def test_defaults_present(self):
        s = model.default_settings()
        for key in ("reminders_enabled", "reminder_count", "min_priority_visible",
                    "ui_category_scope", "ui_time_scope"):
            self.assertIn(key, s)

    def test_normalize_fills_defaults(self):
        s = model.normalize_settings({})
        self.assertEqual(s["ui_category_scope"], "active")
        self.assertEqual(s["ui_time_scope"], "today")

    def test_normalize_keeps_incoming(self):
        s = model.normalize_settings({"reminder_count": 9})
        self.assertEqual(s["reminder_count"], 9)

    def test_migrate_legacy_overdue_scope(self):
        s = model.normalize_settings({"ui_filter_scope": "overdue"})
        self.assertEqual(s["ui_category_scope"], "overdue")
        self.assertEqual(s["ui_time_scope"], "any")

    def test_migrate_legacy_today_scope(self):
        s = model.normalize_settings({"ui_filter_scope": "today"})
        self.assertEqual(s["ui_time_scope"], "today")
        self.assertEqual(s["ui_category_scope"], "active")

    def test_migrate_legacy_done_scope(self):
        s = model.normalize_settings({"ui_filter_scope": "done"})
        self.assertEqual(s["ui_category_scope"], "done")


class LoadDbTests(unittest.TestCase):
    def test_load_db_tolerates_utf8_bom(self):
        import json, tempfile
        from pathlib import Path
        tmp = Path(tempfile.mkdtemp())
        f = tmp / "tasks_gui.json"
        # Write WITH a UTF-8 BOM, as Notepad / PowerShell Out-File would.
        f.write_text(json.dumps({"version": 1, "tasks": [], "next_id": 1}), encoding="utf-8-sig")
        orig = (model.DATA_FILE, model.BACKUP_FILE, model.LEGACY_DATA_FILE)
        try:
            model.DATA_FILE = f
            model.BACKUP_FILE = tmp / "tasks_gui.json.bak"
            model.LEGACY_DATA_FILE = tmp / "nope.json"
            db = model.load_db()
            self.assertEqual(db["next_id"], 1)
        finally:
            model.DATA_FILE, model.BACKUP_FILE, model.LEGACY_DATA_FILE = orig


class TaskHelperTests(unittest.TestCase):
    def test_get_task(self):
        db = {"tasks": [{"id": 1}, {"id": 2}]}
        self.assertEqual(model.get_task(db, 2)["id"], 2)
        self.assertIsNone(model.get_task(db, 99))

    def test_delete_task(self):
        db = {"tasks": [{"id": 1}, {"id": 2}]}
        model.delete_task(db, 1)
        self.assertEqual([t["id"] for t in db["tasks"]], [2])


class StatsTests(unittest.TestCase):
    def test_stats_summary_counts(self):
        now = datetime.now()
        db = {"tasks": [
            {"id": 1, "title": "a", "completed_at": now.isoformat(timespec="seconds"), "repeat": "none"},
            {"id": 2, "title": "b", "completed_at": "", "repeat": "none"},
        ]}
        summary = model.stats_summary(db)
        self.assertEqual(summary["done_today"], 1)
        self.assertEqual(summary["open"], 1)

    def test_stats_streak(self):
        today = date.today()
        hist = [(today - timedelta(days=i)).isoformat() for i in range(1, 4)]
        db = {"tasks": [{"id": 1, "title": "habit", "repeat": "daily", "history": hist, "completed_at": ""}]}
        summary = model.stats_summary(db)
        self.assertTrue(summary["top_streaks"])
        self.assertEqual(summary["top_streaks"][0][1], 3)


if __name__ == "__main__":
    unittest.main()
