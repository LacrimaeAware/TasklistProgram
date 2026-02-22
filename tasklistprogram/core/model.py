import json
import os
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, List
from .dates import parse_stored_due

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
DATA_FILE = DATA_DIR / "tasks_gui.json"
BACKUP_FILE = DATA_DIR / "tasks_gui.json.bak"
LEGACY_DATA_FILE = ROOT_DIR / "tasks_gui.json"
LEGACY_BACKUP_FILE = ROOT_DIR / "tasks_gui.json.bak"

def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def _atomic_write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(f"{path.suffix}.tmp")
    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, path)

def default_settings():
    return {
        "reminders_enabled": False,
        "reminder_count": 4,
        "reminder_min_priority": "M",
        "hazard_escalation_enabled": True,
        "mantras_autoshow": True,
        "min_priority_visible": "L",
        "ui_category_scope": "active",
        "ui_time_scope": "today",
        "ui_time_custom_date": "",
    }

def normalize_settings(settings: dict) -> dict:
    merged = default_settings()
    incoming = dict(settings or {})

    legacy_scope = incoming.pop("ui_filter_scope", None)
    if legacy_scope:
        if legacy_scope in ("today", "week"):
            incoming.setdefault("ui_time_scope", legacy_scope)
            incoming.setdefault("ui_category_scope", "active")
        elif legacy_scope == "overdue":
            incoming.setdefault("ui_time_scope", "any")
            incoming.setdefault("ui_category_scope", "overdue")
        elif legacy_scope in ("all", "repeating"):
            incoming.setdefault("ui_time_scope", "any")
            incoming.setdefault("ui_category_scope", "active" if legacy_scope == "all" else "repeating")
        elif legacy_scope in ("done", "deleted", "suspended"):
            incoming.setdefault("ui_time_scope", "any")
            incoming.setdefault("ui_category_scope", legacy_scope)

    merged.update(incoming)
    return merged

def load_db():
    if not DATA_FILE.exists() and LEGACY_DATA_FILE.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        LEGACY_DATA_FILE.replace(DATA_FILE)
        if LEGACY_BACKUP_FILE.exists():
            LEGACY_BACKUP_FILE.replace(BACKUP_FILE)
    if not DATA_FILE.exists():
        return {"version": 1, "tasks": [], "next_id": 1}
    try:
        db = _load_json(DATA_FILE)
    except json.JSONDecodeError:
        if BACKUP_FILE.exists():
            db = _load_json(BACKUP_FILE)
        else:
            raise
    if "version" not in db:
        db["version"] = 1
    db["settings"] = normalize_settings(db.get("settings", {}))
    return db

def save_db(db):
    if DATA_FILE.exists():
        try:
            _atomic_write_json(BACKUP_FILE, _load_json(DATA_FILE))
        except json.JSONDecodeError:
            pass
    _atomic_write_json(DATA_FILE, db)

def get_task(db, tid: int):
    for t in db["tasks"]:
        if t["id"] == tid:
            return t
    return None

def delete_task(db, tid: int):
    db["tasks"] = [t for t in db["tasks"] if t["id"] != tid]

def stats_summary(db):
    now = datetime.now()
    today = date.today()
    seven = now - timedelta(days=7)
    thirty = now - timedelta(days=30)

    done_today = 0
    done_7 = 0
    done_30 = 0
    open_count = 0

    for t in db["tasks"]:
        if t.get("completed_at"):
            try:
                ct = datetime.fromisoformat(t["completed_at"])
            except Exception:
                continue
            if ct.date() == today:
                done_today += 1
            if ct >= seven:
                done_7 += 1
            if ct >= thirty:
                done_30 += 1
        else:
            open_count += 1

    def streak_for(t):
        hist = set(t.get("history", []))
        if not hist:
            return 0
        streak = 0
        d = today - timedelta(days=1)
        while d.isoformat() in hist:
            streak += 1
            d -= timedelta(days=1)
        return streak

    streaks = []
    for t in db["tasks"]:
        if (t.get("repeat") or "").lower() not in ("", "none"):
            streaks.append((t["title"], streak_for(t)))

    streaks.sort(key=lambda x: x[1], reverse=True)
    top5 = streaks[:5]

    return {
        "open": open_count,
        "done_today": done_today,
        "done_7": done_7,
        "done_30": done_30,
        "top_streaks": top5
    }
