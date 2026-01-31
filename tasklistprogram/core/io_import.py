# io_import.py
import re
from datetime import datetime
from .dates import parse_due_flexible, fmt_due_for_store

VALID_REPEATS = {"none","daily","weekdays","weekly","monthly"}
VALID_PRIOS = {"H","M","L","D","X","MISC","Misc","misc"}

def _parse_lines(lines, db):
    """
    Parse iterable of lines and mutate db in-place.
    Returns (added_count, failed_count).
    """
    added = 0
    failed = 0

    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("- "):
            line = line[2:].strip()

        parts = [p.strip() for p in line.split("|")]

        title = ""
        due_s = ""
        prio = "M"
        rep = "none"
        notes = ""
        group = ""

        for p in parts:
            if ":" in p:
                k, v = p.split(":", 1)
                k = k.strip().lower()
                v = v.strip()
                if k in ("due","d"):
                    due_s = v
                elif k in ("prio","priority","p"):
                    prio = v.upper()
                elif k in ("repeat","r"):
                    rep = v.lower()
                elif k in ("notes","n"):
                    notes = v
                elif k in ("group","g"):
                    group = v
                elif k in ("title","t"):
                    title = v
            else:
                if not title and p:
                    title = p

        if not title:
            failed += 1
            continue

        # parse due (supports HH:MM / HHMM shortcuts)
        parsed = None
        if due_s:
            ts = due_s.strip()
            m_colon = re.match(r'^(\d{1,2}):(\d{2})$', ts)
            m_plain = re.match(r'^(\d{3,4})$', ts)
            if m_colon or m_plain:
                if m_colon:
                    hh, mm = int(m_colon.group(1)), int(m_colon.group(2))
                else:
                    raw = m_plain.group(1)
                    if len(raw) == 3:
                        raw = '0' + raw
                    hh, mm = int(raw[:2]), int(raw[2:])
                parsed = datetime.now().replace(hour=hh, minute=mm, second=0, microsecond=0)
            else:
                parsed = parse_due_flexible(due_s)
        if due_s and parsed is None:
            failed += 1
            continue

        # normalize priority & repeat
        if prio == "D":
            rep = "daily"
        if prio not in VALID_PRIOS:
            prio = "X" if prio.upper() == "MISC" else "M"
        prio = ("X" if prio.upper()=="MISC" else prio.upper())
        if rep not in VALID_REPEATS:
            rep = "none"

        t = {
            "id": db["next_id"],
            "title": title,
            "notes": notes,
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
            "group": group.strip(),
        }
        db["tasks"].append(t)
        db["next_id"] += 1
        added += 1

    return added, failed


def import_from_txt(path: str, db: dict) -> tuple[int, int]:
    """
    Returns (added_count, failed_count).
    Side effect: appends to db["tasks"] and increments db["next_id"].
    """
    with open(path, "r", encoding="utf-8") as f:
        return _parse_lines(f, db)


def import_from_string(text: str, db: dict) -> tuple[int, int]:
    """
    Same as file import, but takes raw text (multi-line).
    """
    return _parse_lines(text.splitlines(), db)
