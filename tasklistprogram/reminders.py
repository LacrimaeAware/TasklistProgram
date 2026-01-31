# reminders.py
from datetime import datetime, timedelta
from .dates import parse_stored_due

def _checkpoints_between(start: datetime, end: datetime, count: int) -> list[datetime]:
    ONE_DAY = timedelta(days=1)
    checkpoints = []
    total = end - start
    if total <= timedelta(0):
        return []
    step = total / (count + 1)
    if step < ONE_DAY:
        cur = (start + ONE_DAY).replace(hour=0, minute=0, second=0, microsecond=0)
        while cur < end:
            checkpoints.append(cur)
            cur += ONE_DAY
    else:
        for i in range(1, count + 1):
            checkpoints.append((start + timedelta(seconds=step.total_seconds()*i)).replace(second=0, microsecond=0))
    return checkpoints

def pending_reminders(db: dict, now: datetime | None = None) -> list[dict]:
    """Build rows for the RemindersDialog."""
    now = now or datetime.now()
    s = db.get("settings", {"reminders_enabled": True, "reminder_count": 4, "reminder_min_priority": "M"})
    if not s.get("reminders_enabled", True):
        return []

    count = max(1, int(s.get("reminder_count", 4)))
    minp = (s.get("reminder_min_priority","M") or "M").upper()
    order = {"H":3,"M":2,"L":1,"D":0}
    rows = []

    for t in db["tasks"]:
        if t.get("is_deleted") or t.get("completed_at"):
            continue
        p = (t.get("priority","M") or "M").upper()
        if order.get(p,0) < order.get(minp,2):
            continue

        d = parse_stored_due(t.get("due",""))
        if not d or d <= now:
            continue

        try:
            c_at = datetime.fromisoformat(t.get("created_at",""))
        except Exception:
            c_at = now

        start = max(c_at, now.replace(year=now.year-1))
        cps = _checkpoints_between(start, d, count)
        if not cps:
            continue

        seen = set(t.get("acknowledged_checkpoints", []))
        current_cp = None
        for cp in cps:
            key = cp.isoformat(timespec="minutes")
            if cp <= now and key not in seen:
                current_cp = key
        if current_cp:
            rows.append({
                "id": t["id"],
                "title": t.get("title",""),
                "priority": p,
                "_due_str": (d.strftime("%Y-%m-%d %H:%M") if len((t.get("due") or ""))>10 else d.strftime("%Y-%m-%d")),
                "_cp_key": current_cp
            })

    return rows

def reminder_chip(t: dict, settings: dict | None = None, now: datetime | None = None) -> str:
    """Return '⏰' if a checkpoint is pending for this task, else ''."""
    now = now or datetime.now()
    s = settings or {"reminders_enabled": True, "reminder_count": 4, "reminder_min_priority": "M"}
    if not s.get("reminders_enabled", True):
        return ""

    order = {"H":3,"M":2,"L":1,"D":1,"X":0}
    minp = s.get("reminder_min_priority","M")
    minp_code = "X" if isinstance(minp, str) and str(minp).lower()=="misc" else (minp or "M").upper()
    pcode = (t.get("priority","M") or "M").upper()
    if order.get(pcode,0) < order.get(minp_code,2):
        return ""

    d = parse_stored_due(t.get("due","")) if t.get("due") else None
    if not d or d <= now:
        return ""

    try:
        c_at = datetime.fromisoformat(t.get("created_at",""))
    except Exception:
        c_at = now

    start = max(c_at, now.replace(year=now.year-1))
    count = max(1, int(s.get("reminder_count", 4)))
    cps = _checkpoints_between(start, d, count)
    seen = set(t.get("acknowledged_checkpoints", []))
    for cp in cps:
        key = cp.isoformat(timespec="minutes")
        if cp <= now and key not in seen:
            return "⏰"
    return ""
