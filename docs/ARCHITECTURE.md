# Architecture

Tiny Tasklist is a single-process Tkinter desktop app. It deliberately uses only
the Python standard library, stores everything in local files, and never touches
the network.

## High-level shape

```
┌─────────────────────────────────────────────────────────────┐
│ tasklistprogram/app.py — TaskApp(tk.Tk, ActionsMixin)        │
│  • builds the window: menus, input row, filter row, table    │
│  • owns the in-memory db dict and the refresh()/filter logic │
│  • schedules midnight resets and launch-time mantra          │
└───────────────┬───────────────────────────┬─────────────────┘
                │                            │
        core/ (no Tkinter)            ui/ (Tkinter widgets)
   model, actions, dates,          listview, dialogs, controls
   filters, scheduler,
   documents, io_import,
   reminders, constants
```

The package is split into a **`core/`** layer (pure logic, no UI imports — the one
exception is `actions.py`, which is a mixin that also drives small dialogs) and a
**`ui/`** layer (Tkinter views). `app.py` wires them together.

## Module reference

### Entry points
- **`__main__.py`** — `python -m tasklistprogram` → calls `app.main()`.
- **`app.py`** — `TaskApp` is the whole window. Responsibilities:
  - Build menus (File / Mantras / Journal / Help), the add-task input row, the
    filter row (Category, Time, custom date, Search, Min prio, Group view), and
    the action buttons.
  - Hold `self.db` (loaded via `core.model.load_db`) and the current sort/filter
    state.
  - `refresh()` is the central redraw: it filters (`passes_filter`), searches,
    sorts (`sort_key_for`), then hands rows to `TaskListView.render`.
  - Scheduling: `schedule_midnight_reset()` and `reset_repeating_tasks()` advance
    recurring tasks at midnight; `_maybe_show_mantra_on_launch()` shows the daily
    mantra once.
  - It inherits task operations from `ActionsMixin`.

### core/ (business logic)
- **`model.py`** — persistence and aggregates.
  - `load_db()` / `save_db()` — JSON load and **atomic write** (`tmp` file +
    `os.replace`) with a `.bak` backup of the prior version. Falls back to the
    backup if the main file is corrupt. Migrates a legacy root-level data file
    into `data/`.
  - `default_settings()` / `normalize_settings()` — settings schema and migration
    of the old single `ui_filter_scope` into split `ui_category_scope` /
    `ui_time_scope`.
  - `get_task`, `delete_task`, `stats_summary` (open/done counts + streaks).
- **`dates.py`** — all date handling.
  - `parse_due_flexible()` — the flexible input parser (absolute, MM/DD, weekday,
    daypart, `midnight`, relative tokens). Returns `None`, a `datetime`, or a
    `('dateonly', datetime)` tuple.
  - `parse_due_entry()` — the canonical entry-point parser used by every text
    field (adds bare-time `HH:MM`/`HHMM` support on top of `parse_due_flexible`).
  - `fmt_due_for_store()` / `parse_stored_due()` — convert to/from the stored
    string form (`YYYY-MM-DD` or `YYYY-MM-DD HH:MM`).
  - `next_due()`, `repeat_interval_days()`, `month_add()` (`add_months_dateonly`
    is a thin alias) — recurrence math.
- **`filters.py`** — pure predicates for the task list: `passes_filter`,
  `passes_category_filter`, `passes_time_filter`, `priority_visible`,
  `search_match`, `sort_key_for`. `app.refresh()` calls these; they have no Tk
  dependency so they're unit-tested directly.
- **`scheduler.py`** — recurrence advancement: `advance_repeating_tasks(db, today,
  hazard_enabled)` rolls repeating tasks forward to their next occurrence and
  applies `apply_skip_escalation`. `app.py` owns the Tk timer that calls it.
- **`actions.py`** — `ActionsMixin` (mixed into `TaskApp`): `mark_done`,
  `soft_delete`, `restore`, `suspend`/`unsuspend`, `hard_delete`, bulk setters
  (priority/repeat/group/due), and `bump_*`. These mutate `self.db`, call
  `save_db`, and `refresh`.
- **`documents.py`** — file-backed content:
  - Task documents at `data/task_documents/<Group>/<Title>-<id>.md`, split by a
    divider into a synced "displayed notes" top section and a private bottom
    section.
  - Daily journals at `data/journals/YYYY/MM/YYYY-MM-DD.md` (manual entries on
    top, an auto "## Completed Tasks" log below the `---` divider).
  - Mantras in `data/mantras.md`, with `pick_mantra_of_day()` /
    `pick_random_mantra()` selectors.
  - `open_document` / `open_directory` (OS file-explorer helpers).
- **`io_import.py`** — parse pipe-delimited task lines from a file or pasted text;
  returns `(added, failed[, error_details])`.
- **`reminders.py`** — compute evenly spaced "checkpoints" between a task's
  creation and its due date; `reminder_chip()` returns ⏰ when one is due and
  unacknowledged; `pending_reminders()` builds rows for the Reminders dialog.
- **`constants.py`** — `PRIORITY_ORDER` and `PRIO_ICON`.

### ui/ (Tkinter)
- **`listview.py`** — `TaskListView` wraps a `ttk.Treeview`: column layout,
  priority row colors, group headers with expand/collapse, auto-sizing, and
  double-click handling (edit a task / toggle a group).
- **`dialogs.py`** — all Toplevel dialogs: `EditDialog`, `StatsDialog`,
  `SettingsDialog`, `HelpDialog`, `MantraDialog`, `JournalDialog`,
  `PasteImportDialog`, `RemindersDialog`.
- **`controls.py`** — `AutoCompleteEntry`, a `ttk.Entry` with a dropdown of
  candidate completions (used for titles and group names).

## Data flow

1. **Startup** — `TaskApp.__init__` → `load_db()` → build widgets → `refresh()` →
   `reset_repeating_tasks(catchup=True)` → `schedule_midnight_reset()` → maybe
   show mantra.
2. **Mutation** — a user action (add/edit/done/bulk) mutates the `db` dict in
   memory, calls `save_db(db)` (atomic write + backup), then `refresh()`.
3. **Render** — `refresh()` filters → searches → sorts → `TaskListView.render`.
4. **Documents** — adding/editing a task also calls `sync_task_notes()` /
   `move_task_document_if_needed()` so the Markdown file tracks the task.

## Storage format

`data/tasks_gui.json`:

```json
{
  "version": 1,
  "next_id": 42,
  "settings": { "...": "see default_settings()" },
  "tasks": [
    {
      "id": 1,
      "title": "Example",
      "notes": "",
      "priority": "M",
      "due": "2026-06-07 14:00",
      "repeat": "weekly",
      "created_at": "2026-06-01T09:00:00",
      "completed_at": "",
      "times_completed": 3,
      "history": ["2026-05-24", "2026-05-31"],
      "is_deleted": false,
      "is_suspended": false,
      "skip_count": 0,
      "group": "Work",
      "doc_path": "…/task_documents/Work/Example-1.md"
    }
  ]
}
```

Optional fields that appear once used: `base_priority` (saved original priority
during hazard escalation), `bumped_count`, `deleted_at`, `updated_at`,
`acknowledged_checkpoints`. `_display_title` is a transient UI-only field.

## Key behaviors worth knowing

- **Recurring tasks reset, not archive.** `mark_done` on a repeating task records
  the completion (history, times_completed, journal) but then clears
  `completed_at` and advances `due` to the next occurrence, so the row reappears
  as a fresh checklist item. Therefore completed repeating tasks do **not** show
  under the `done` category.
- **Midnight rollover.** `reset_repeating_tasks` advances any repeating task whose
  next occurrence is already ≤ today, catching up multiple missed occurrences in a
  loop, and (if hazard escalation is on) bumping priority per missed occurrence.
- **Hazard escalation.** When enabled, missed recurrences raise `skip_count`;
  ≥2 → High (original saved to `base_priority`), ≥3 → Ultra, with a ⚠ title
  prefix. `mark_done` and the Settings "reset" clear it.
