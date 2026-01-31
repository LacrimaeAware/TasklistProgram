import re
from datetime import datetime, date, timedelta
from typing import Optional

WEEKDAY_MAP = {
    "mon": 0,
    "monday": 0,
    "tue": 1,
    "tues": 1,
    "tuesday": 1,
    "wed": 2,
    "weds": 2,
    "wednesday": 2,
    "thu": 3,
    "thur": 3,
    "thurs": 3,
    "thursday": 3,
    "fri": 4,
    "friday": 4,
    "sat": 5,
    "saturday": 5,
    "sun": 6,
    "sunday": 6,
}

DAYPART_MAP = {
    "morning": (8, 0),
    "noon": (12, 0),
    "afternoon": (16, 0),
    "evening": (20, 0),
}

def _end_of_day(dt: datetime) -> datetime:
    return dt.replace(hour=23, minute=59, second=0, microsecond=0)

def _has_time_tokens(tokens):
    for tok in tokens:
        m = re.match(r'^[+-](\d+)([hm])$', tok.lower())
        if m:
            return True
    for tok in tokens:
        if tok.lower() in ('+0m', '+0h'):
            return True
    return False

def parse_due_flexible(s: Optional[str]):
    """Parse flexible due strings.
       Returns:
         - None for empty
         - datetime for precise
         - ('dateonly', datetime) for date-only precision

    Accepts:
      - 'YYYY-MM-DD' [ 'HHMM' | 'HH:MM' | 'midnight' ]
      - 'MM/DD' [ 'HHMM' | 'HH:MM' | 'midnight' ]
      - 'midnight'  (today 23:59)
      - relative tokens: '+2d +5h -3h +1w' (optional 'midnight' to force 23:59)
    """
    if not s or not s.strip():
        return None
    s = s.strip()

    # Plain 'midnight' -> today 23:59
    if s.lower() == "midnight":
        now = datetime.now()
        return now.replace(hour=23, minute=59, second=0, microsecond=0)

    # Plain dayparts -> today at a sensible time
    if s.lower() in DAYPART_MAP:
        now = datetime.now()
        hh, mm = DAYPART_MAP[s.lower()]
        return now.replace(hour=hh, minute=mm, second=0, microsecond=0)

    # Weekday names with optional time or daypart
    tokens = s.split()
    if tokens:
        day_key = tokens[0].lower()
        if day_key in WEEKDAY_MAP:
            today = date.today()
            target = WEEKDAY_MAP[day_key]
            days_ahead = (target - today.weekday()) % 7
            target_date = today + timedelta(days=days_ahead)
            if len(tokens) == 1:
                return ("dateonly", datetime.combine(target_date, datetime.min.time()))
            tail = " ".join(tokens[1:]).strip().lower()
            if tail == "midnight":
                return datetime.combine(target_date, datetime.min.time()).replace(hour=23, minute=59)
            if tail in DAYPART_MAP:
                hh, mm = DAYPART_MAP[tail]
                return datetime.combine(target_date, datetime.min.time()).replace(hour=hh, minute=mm)
            m_time = re.match(r'^(\d{1,2}):(\d{2})$', tail) or re.match(r'^(\d{3,4})$', tail)
            if m_time:
                if ":" in tail:
                    hh, mm = int(m_time.group(1)), int(m_time.group(2))
                else:
                    raw = m_time.group(1)
                    if len(raw) == 3:
                        raw = "0" + raw
                    hh, mm = int(raw[:2]), int(raw[2:])
                return datetime.combine(target_date, datetime.min.time()).replace(hour=hh, minute=mm)

    # Absolute YYYY-MM-DD with optional time or 'midnight'
    m = re.match(r'^(\d{4}-\d{2}-\d{2})(?:\s+(\d{2})(?::?(\d{2}))|\s+midnight)?$', s, re.IGNORECASE)
    if m:
        d = datetime.strptime(m.group(1), "%Y-%m-%d")
        if m.group(2):
            hh = int(m.group(2)); mm = int(m.group(3) or 0)
            return d.replace(hour=hh, minute=mm)
        if s.lower().endswith("midnight"):
            return d.replace(hour=23, minute=59)
        return ('dateonly', d)

    # Absolute MM/DD with optional time or 'midnight'
    m2 = re.match(r'^(\d{1,2})/(\d{1,2})(?:\s+(\d{2})(?::?(\d{2}))?|\s+midnight)?$', s, re.IGNORECASE)
    if m2:
        y = datetime.now().year
        mon, day = int(m2.group(1)), int(m2.group(2))
        try:
            d = datetime(year=y, month=mon, day=day)
        except ValueError:
            return None
        if m2.group(3):
            hh = int(m2.group(3)); mm = int(m2.group(4) or 0)
            return d.replace(hour=hh, minute=mm)
        if s.lower().endswith("midnight"):
            return d.replace(hour=23, minute=59)
        return ('dateonly', d)

    # Relative tokens with optional 'midnight'
    tokens = s.split()
    midnight_flag = any(tok.lower() == 'midnight' for tok in tokens)
    tokens = [t for t in tokens if t.lower() != 'midnight']

    ok = True
    for tok in tokens:
        if re.match(r'^[+-]\d+[dhmw]$', tok.lower()) or tok.lower() in ('+0m', '+0h'):
            continue
        ok = False; break
    if not ok or not tokens:
        return None

    now = datetime.now()
    total = timedelta()
    for tok in tokens:
        tl = tok.lower()
        if tl in ('+0m', '+0h'):
            continue
        m = re.match(r'^([+-])(\d+)([dhmw])$', tl)
        sign = 1 if m.group(1) == '+' else -1
        amt = int(m.group(2)) * sign
        unit = m.group(3)
        if unit == 'm': total += timedelta(minutes=amt)
        elif unit == 'h': total += timedelta(hours=amt)
        elif unit == 'd': total += timedelta(days=amt)
        elif unit == 'w': total += timedelta(weeks=amt)

    result_dt = now + total
    if _has_time_tokens(tokens):
        return result_dt
    else:
        if midnight_flag:
            return result_dt.replace(hour=23, minute=59, second=0, microsecond=0)
        d = result_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        return ('dateonly', d)

def fmt_due_for_store(parsed):
    if parsed is None:
        return ""
    if isinstance(parsed, tuple) and parsed and parsed[0] == 'dateonly':
        dt = parsed[1]
        return dt.strftime("%Y-%m-%d")
    if isinstance(parsed, datetime):
        return parsed.strftime("%Y-%m-%d %H:%M")
    return ""

def parse_stored_due(s: str) -> Optional[datetime]:
    if not s:
        return None
    try:
        if len(s) == 10:
            d = datetime.strptime(s, "%Y-%m-%d")
            return d  # date-only, 00:00
        return datetime.strptime(s, "%Y-%m-%d %H:%M")
    except Exception:
        return None

def month_add(base: date) -> date:
    m = base.month + 1
    y = base.year + (m - 1)//12
    m = ((m - 1)%12) + 1
    days = [31,29 if y%4==0 and (y%100!=0 or y%400==0) else 28,31,30,31,30,31,31,30,31,30,31][m-1]
    day = min(base.day, days)
    return date(y, m, day)

def next_due(d: Optional[date], repeat: str) -> Optional[date]:
    if repeat in ("", "none", None):
        return d
    base = d or date.today()
    if repeat == "daily":
        return base + timedelta(days=1)
    if repeat == "weekdays":
        nd = base + timedelta(days=1)
        while nd.weekday() >= 5:
            nd += timedelta(days=1)
        return nd
    if repeat == "weekly":
        return base + timedelta(days=7)
    if repeat == "monthly":
        return month_add(base)
    return base

def add_months_dateonly(d):
    y = d.year
    m = d.month + 1
    y += (m - 1)//12
    m = ((m - 1)%12) + 1
    days = [31,29 if y%4==0 and (y%100!=0 or y%400==0) else 28,31,30,31,30,31,31,30,31,30,31][m-1]
    day = min(d.day, days)
    return date(y, m, day)
