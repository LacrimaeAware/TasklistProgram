# io_import.py
import re
from datetime import datetime
from .dates import parse_due_flexible, fmt_due_for_store

VALID_REPEATS = {"none", "daily", "weekdays", "weekly", "bi-weekly", "monthly"}
VALID_PRIOS = {"H", "M", "L", "D", "X", "MISC", "Misc", "misc"}


def _parse_lines(lines, db, return_details: bool = False):
    """
    Parse iterable of lines and mutate db in-place.
    Returns:
      - (added_count, failed_count)
      - OR (added_count, failed_count, error_details) when return_details=True
    """
    added = 0
    failed = 0
    error_details = []

    for idx, raw in enumerate(lines, start=1):
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
                if k in ("due", "d"):
                    due_s = v
                elif k in ("prio", "priority", "p"):
                    prio = v.upper()
                elif k in ("repeat", "r"):
                    rep = v.lower()
                elif k in ("notes", "n"):
                    notes = v
                elif k in ("group", "g"):
                    group = v
                elif k in ("title", "t"):
                    title = v
            else:
                if not title and p:
                    title = p

        if not title:
            failed += 1
            error_details.append(f"Line {idx}: missing title.")
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
                    raw_hhmm = m_plain.group(1)
                    if len(raw_hhmm) == 3:
                        raw_hhmm = '0' + raw_hhmm
                    hh, mm = int(raw_hhmm[:2]), int(raw_hhmm[2:])
                if hh > 23 or mm > 59:
                    parsed = None
                else:
                    parsed = datetime.now().replace(hour=hh, minute=mm, second=0, microsecond=0)
            else:
                parsed = parse_due_flexible(due_s)
        if due_s and parsed is None:
            failed += 1
            error_details.append(
                f"Line {idx}: invalid due '{due_s}'. Use YYYY-MM-DD, MM/DD, HH:MM, HHMM, weekday words, or relative tokens like +2d +3h."
            )
            continue

        # normalize priority & repeat
        if prio == "D":
            rep = "daily"
        if prio not in VALID_PRIOS:
            prio = "X" if prio.upper() == "MISC" else "M"
        prio = ("X" if prio.upper() == "MISC" else prio.upper())

        if rep.startswith("custom:"):
            raw_repeat = rep.split(":", 1)[1].strip()
            if raw_repeat.isdigit() and int(raw_repeat) > 0:
                rep = f"custom:{int(raw_repeat)}"
            else:
                failed += 1
                error_details.append(f"Line {idx}: custom repeat must be a positive day count, e.g. custom:6.")
                continue
        elif rep not in VALID_REPEATS:
            failed += 1
            error_details.append(
                f"Line {idx}: invalid repeat '{rep}'. Use none/daily/weekdays/weekly/bi-weekly/monthly/custom:<days>."
            )
            continue

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

    if return_details:
        return added, failed, error_details
    return added, failed


def import_from_txt(path: str, db: dict, return_details: bool = False):
    """
    Returns (added_count, failed_count) or (added_count, failed_count, error_details).
    Side effect: appends to db["tasks"] and increments db["next_id"].
    """
    with open(path, "r", encoding="utf-8") as f:
        return _parse_lines(f, db, return_details=return_details)


def import_from_string(text: str, db: dict, return_details: bool = False):
    """
    Same as file import, but takes raw text (multi-line).
    """
    return _parse_lines(text.splitlines(), db, return_details=return_details)
