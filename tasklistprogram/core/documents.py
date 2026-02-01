import os
from pathlib import Path
from datetime import datetime, date
import re
import subprocess
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
TASKS_DIR = DATA_DIR / "task_documents"
JOURNALS_DIR = DATA_DIR / "journals"

TASK_DIVIDER = "\n--- Display notes (shown in app) ↑ | Personal notes (not shown) ↓ ---\n"
JOURNAL_DIVIDER = "\n---\n"

def _safe_name(value: str, fallback: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\n\r\t]+', "_", value or "").strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned or fallback

def task_doc_path(task: dict) -> Path:
    group = _safe_name(task.get("group", "").strip(), "Ungrouped")
    title = _safe_name(task.get("title", "").strip(), f"task-{task.get('id', 'unknown')}")
    filename = f"{title}-{task.get('id', 'unknown')}.md"
    return TASKS_DIR / group / filename

def _split_sections(content: str, divider: str) -> tuple[str, str]:
    if divider in content:
        top, bottom = content.split(divider, 1)
        return top.strip(), bottom.strip()
    return content.strip(), ""

def _write_sections(path: Path, top: str, bottom: str, divider: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = f"{top.strip()}{divider}{bottom.strip()}\n"
    path.write_text(body, encoding="utf-8")

def sync_task_notes(task: dict) -> Path:
    path = task_doc_path(task)
    existing = ""
    if path.exists():
        existing = path.read_text(encoding="utf-8")
    top, bottom = _split_sections(existing, TASK_DIVIDER)
    
    # If the file exists and has top section content, update task notes from file
    # (user may have edited the display notes section directly)
    if path.exists() and top:
        task["notes"] = top
    else:
        # Otherwise, write task notes to file
        top = task.get("notes", "").strip()
    
    _write_sections(path, top, bottom, TASK_DIVIDER)
    task["doc_path"] = str(path)
    return path

def move_task_document_if_needed(task: dict) -> Path:
    desired = task_doc_path(task)
    current = Path(task.get("doc_path")) if task.get("doc_path") else None
    if current and current.exists() and current != desired:
        desired.parent.mkdir(parents=True, exist_ok=True)
        current.replace(desired)
    task["doc_path"] = str(desired)
    return desired

def open_document(path: Path) -> None:
    if sys.platform.startswith("win"):
        os.startfile(path)  # type: ignore[attr-defined]
        return
    if sys.platform == "darwin":
        subprocess.run(["open", str(path)], check=False)
        return
    subprocess.run(["xdg-open", str(path)], check=False)

def open_directory(path: Path) -> None:
    """Open a directory in the system file explorer."""
    if sys.platform.startswith("win"):
        os.startfile(path)  # type: ignore[attr-defined]
        return
    if sys.platform == "darwin":
        subprocess.run(["open", str(path)], check=False)
        return
    subprocess.run(["xdg-open", str(path)], check=False)

def _journal_path(entry_date: date) -> Path:
    return JOURNALS_DIR / f"{entry_date.year:04d}" / f"{entry_date.month:02d}" / f"{entry_date:%Y-%m-%d}.md"

def _ensure_journal(entry_date: date) -> Path:
    path = _journal_path(entry_date)
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    _write_sections(path, "", "", JOURNAL_DIVIDER)
    return path

def ensure_journal_path(entry_date: date | None = None) -> Path:
    entry_date = entry_date or date.today()
    return _ensure_journal(entry_date)

def append_journal_manual(entry: str, entry_time: datetime | None = None) -> Path:
    entry_time = entry_time or datetime.now()
    path = _ensure_journal(entry_time.date())
    content = path.read_text(encoding="utf-8")
    top, bottom = _split_sections(content, JOURNAL_DIVIDER)
    timestamp = entry_time.strftime("%H:%M")
    entry_text = entry.strip()
    if entry_text:
        line = f"- {timestamp} {entry_text}"
        top = f"{top}\n{line}".strip()
    _write_sections(path, top, bottom, JOURNAL_DIVIDER)
    return path

def append_journal_task(title: str, entry_time: datetime | None = None) -> Path:
    entry_time = entry_time or datetime.now()
    path = _ensure_journal(entry_time.date())
    content = path.read_text(encoding="utf-8")
    top, bottom = _split_sections(content, JOURNAL_DIVIDER)
    timestamp = entry_time.strftime("%H:%M")
    safe_title = title.strip() or "Task completed"
    header = "## Completed Tasks"
    line = f"- {timestamp} Completed: {safe_title}"
    if not bottom:
        bottom = header
    elif not bottom.lstrip().startswith(header):
        bottom = f"{header}\n{bottom}".strip()
    bottom = f"{bottom}\n{line}".strip()
    _write_sections(path, top, bottom, JOURNAL_DIVIDER)
    return path

def get_mantras_file_path() -> Path:
    """Get the path to the mantras file, creating it if it doesn't exist."""
    mantras_file = DATA_DIR / "mantras.txt"
    if not mantras_file.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        mantras_file.write_text("# Mantras\n# Add your personal mantras here, one per line\n\n", encoding="utf-8")
    return mantras_file
