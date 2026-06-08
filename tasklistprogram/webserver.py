"""Local web server: serves the `web/` prototype AND a small JSON API backed by the
real task data, reusing the existing `core/` logic. Standard library only.

Run:
    python -m tasklistprogram.webserver         # http://localhost:8000
    python -m tasklistprogram.webserver 8765    # custom port

This is local-first: it binds to 127.0.0.1 by default and reads/writes the same
`data/tasks_gui.json` the desktop app uses. It is NOT hardened for public exposure
(no auth yet) — see docs/DESIGN.md for the planned auth/hosting phase.
"""
import json
import sys
import threading
import mimetypes
from datetime import datetime, date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .core import model
from .core.dates import parse_due_entry, fmt_due_for_store, parse_stored_due, next_due
from .core.io_import import import_from_string

ROOT = Path(__file__).resolve().parent.parent
WEB_DIR = ROOT / "web"

# Serializes the read-modify-write cycle so concurrent requests (the server is
# threaded) can't clobber each other's changes.
_DB_LOCK = threading.Lock()


# ---------- task <-> client adapters ----------
def to_client(t: dict) -> dict:
    return {
        "id": t["id"],
        "title": t.get("title", ""),
        "due": t.get("due", ""),
        "priority": t.get("priority", "M"),
        "repeat": t.get("repeat", "none"),
        "group": t.get("group", ""),
        "notes": t.get("notes", ""),
        "done": bool(t.get("completed_at")),
        "completed_at": t.get("completed_at", ""),
        "times": t.get("times_completed", 0),
        "suspended": bool(t.get("is_suspended")),
        "skip_count": int(t.get("skip_count", 0) or 0),
        "is_deleted": bool(t.get("is_deleted")),
        "history": t.get("history", []),
    }


def op_reset_hazard(db: dict) -> int:
    """Clear hazard escalation for all tasks (mirror the desktop reset). Returns count."""
    changed = 0
    for t in db.get("tasks", []):
        if int(t.get("skip_count", 0) or 0) != 0:
            t["skip_count"] = 0
            changed += 1
        if "base_priority" in t:
            t["priority"] = t.get("base_priority", t.get("priority", "M"))
            t.pop("base_priority", None)
            changed += 1
    return changed


def client_tasks(db: dict) -> list:
    # Return ALL tasks (including deleted) so the client can filter by category
    # exactly like the desktop, including a Deleted view with restore.
    return [to_client(t) for t in db["tasks"]]


# ---------- operations (mirror the desktop, minus Tk) ----------
def op_mark_done(t: dict) -> None:
    t["completed_at"] = datetime.now().isoformat(timespec="seconds")
    t["times_completed"] = t.get("times_completed", 0) + 1
    t.setdefault("history", []).append(date.today().isoformat())
    t["skip_count"] = 0
    if "base_priority" in t:
        t["priority"] = t.get("base_priority", t.get("priority", "M"))
        t.pop("base_priority", None)

    rep = (t.get("repeat") or "none").lower()
    if rep != "none":
        cur = t.get("due", "")
        due_dt = parse_stored_due(cur) or datetime.now()
        had_time = isinstance(cur, str) and len(cur) > 10
        nd = next_due(due_dt.date(), rep)
        t["due"] = datetime.combine(nd, due_dt.time()).strftime("%Y-%m-%d %H:%M") if had_time else nd.strftime("%Y-%m-%d")
        t["completed_at"] = ""  # recurring tasks reset for the next cycle


def op_toggle(t: dict) -> None:
    if t.get("completed_at"):
        t["completed_at"] = ""  # undo a one-off completion
    else:
        op_mark_done(t)


def op_update(t: dict, payload: dict) -> None:
    """Apply an edit to a task (used by PATCH). Only updates provided fields.

    Also accepts completed_at / times / history so the client can implement a
    clean Undo by restoring a pre-toggle snapshot.
    """
    if "title" in payload:
        title = (payload.get("title") or "").strip()
        if title:
            t["title"] = title
    if "notes" in payload:
        t["notes"] = payload.get("notes") or ""
    if "group" in payload:
        t["group"] = (payload.get("group") or "").strip()
    if "repeat" in payload:
        t["repeat"] = payload.get("repeat") or "none"
    if "priority" in payload:
        p = payload.get("priority") or "M"
        p = "X" if str(p).lower() == "misc" else str(p).upper()
        if p in ("U", "H", "M", "L", "D", "X"):
            t["priority"] = p
            if p == "D":
                t["repeat"] = "daily"  # mirror the desktop Edit dialog
    if "due" in payload:
        due_s = (payload.get("due") or "").strip()
        if due_s:
            parsed = parse_due_entry(due_s)
            if parsed is not None:
                t["due"] = fmt_due_for_store(parsed)
        else:
            t["due"] = ""
    if "is_suspended" in payload:
        t["is_suspended"] = bool(payload["is_suspended"])
    if "is_deleted" in payload:
        t["is_deleted"] = bool(payload["is_deleted"])  # lets the client undo a delete
    # Fields below let the client restore a snapshot for Undo.
    if "completed_at" in payload:
        t["completed_at"] = payload.get("completed_at") or ""
    if "times" in payload:
        try:
            t["times_completed"] = int(payload["times"])
        except (TypeError, ValueError):
            pass
    if "history" in payload and isinstance(payload["history"], list):
        t["history"] = payload["history"]
    t["updated_at"] = datetime.now().isoformat(timespec="seconds")


def op_add(db: dict, payload: dict) -> dict:
    title = (payload.get("title") or "").strip()
    if not title:
        raise ValueError("title required")
    due_s = (payload.get("due") or "").strip()
    parsed = parse_due_entry(due_s) if due_s else None
    prio = (payload.get("priority") or "M")
    prio = "X" if str(prio).lower() == "misc" else str(prio).upper()
    if prio not in ("U", "H", "M", "L", "D", "X"):
        prio = "M"
    rep = (payload.get("repeat") or "none")
    if prio == "D":
        rep = "daily"
    t = {
        "id": db["next_id"],
        "title": title,
        "notes": (payload.get("notes") or "").strip(),
        "priority": prio,
        "due": fmt_due_for_store(parsed) if due_s else "",
        "repeat": rep,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "completed_at": "",
        "times_completed": 0,
        "history": [],
        "is_deleted": False,
        "is_suspended": False,
        "skip_count": 0,
        "group": (payload.get("group") or "").strip(),
    }
    db["tasks"].append(t)
    db["next_id"] += 1
    return t


# ---------- HTTP handler ----------
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # quiet

    # -- helpers --
    def _send_json(self, obj, status=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception:
            return {}

    def _find(self, db, tid):
        return next((t for t in db["tasks"] if t["id"] == tid), None)

    # -- routing --
    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/tasks":
            with _DB_LOCK:
                db = model.load_db()
                payload = {"tasks": client_tasks(db), "settings": db.get("settings", {})}
            return self._send_json(payload)
        if path == "/api/stats":
            with _DB_LOCK:
                stats = model.stats_summary(model.load_db())
            return self._send_json(stats)
        return self._serve_static(path)

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/api/tasks":
            payload = self._read_json()
            with _DB_LOCK:
                db = model.load_db()
                try:
                    t = op_add(db, payload)
                except ValueError as e:
                    return self._send_json({"error": str(e)}, 400)
                model.save_db(db)
                client = to_client(t)
            return self._send_json(client, 201)
        if path == "/api/hazard/reset":
            with _DB_LOCK:
                db = model.load_db()
                count = op_reset_hazard(db)
                model.save_db(db)
            return self._send_json({"ok": True, "reset": count})
        if path == "/api/import":
            text = self._read_json().get("text", "")
            with _DB_LOCK:
                db = model.load_db()
                added, failed, details = import_from_string(text, db, return_details=True)
                if added:
                    model.save_db(db)
            return self._send_json({"added": added, "failed": failed, "details": details})
        if path.startswith("/api/tasks/") and path.endswith("/toggle"):
            return self._mutate_one(path.split("/")[3], op_toggle)
        if path.startswith("/api/tasks/") and path.endswith("/done"):
            return self._mutate_one(path.split("/")[3], op_mark_done)
        if path.startswith("/api/tasks/") and path.endswith("/harddelete"):
            return self._hard_delete(path.split("/")[3])
        return self._send_json({"error": "not found"}, 404)

    def do_PATCH(self):
        path = urlparse(self.path).path
        if path.startswith("/api/tasks/") and path.count("/") == 3:
            payload = self._read_json()
            return self._mutate_one(path.split("/")[3], lambda t: op_update(t, payload))
        return self._send_json({"error": "not found"}, 404)

    def do_DELETE(self):
        path = urlparse(self.path).path
        if path.startswith("/api/tasks/"):
            def _del(t):
                t["is_deleted"] = True
                t["deleted_at"] = datetime.now().isoformat(timespec="seconds")
            return self._mutate_one(path.split("/")[3], _del)
        return self._send_json({"error": "not found"}, 404)

    def _mutate_one(self, raw_id, fn):
        try:
            tid = int(raw_id)
        except ValueError:
            return self._send_json({"error": "bad id"}, 400)
        with _DB_LOCK:
            db = model.load_db()
            t = self._find(db, tid)
            if not t:
                return self._send_json({"error": "not found"}, 404)
            fn(t)
            model.save_db(db)
            client = to_client(t)
        return self._send_json(client)

    def _hard_delete(self, raw_id):
        try:
            tid = int(raw_id)
        except ValueError:
            return self._send_json({"error": "bad id"}, 400)
        with _DB_LOCK:
            db = model.load_db()
            before = len(db["tasks"])
            db["tasks"] = [t for t in db["tasks"] if t["id"] != tid]
            if len(db["tasks"]) == before:
                return self._send_json({"error": "not found"}, 404)
            model.save_db(db)
        return self._send_json({"ok": True})

    def _serve_static(self, path):
        if path in ("/", ""):
            path = "/index.html"
        target = (WEB_DIR / path.lstrip("/")).resolve()
        # prevent path traversal outside web/
        if not str(target).startswith(str(WEB_DIR.resolve())) or not target.is_file():
            self.send_error(404)
            return
        ctype = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        data = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")  # always serve fresh during dev
        self.end_headers()
        self.wfile.write(data)


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    host = "127.0.0.1"
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Tiny Tasklist web server on http://{host}:{port}  (serving {WEB_DIR})")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopping…")
        server.shutdown()


if __name__ == "__main__":
    main()
