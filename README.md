# Tiny Tasklist

A lightweight, single-user task manager built with Python and Tkinter (standard
library only — no third-party dependencies). All data lives in plain JSON and
Markdown files on your machine; nothing is sent anywhere.

## Features

- **Priorities** with color coding: High, Medium, Low, Daily, and Misc — plus an
  automatic **Ultra** level used by hazard escalation.
- **Recurring tasks**: daily, weekdays, weekly, bi-weekly, monthly, and
  *custom* (every N days). Recurring tasks behave like a checklist that resets to
  its next due date when you mark it done.
- **Flexible due dates/times** (see formats below).
- **Grouping, filtering, and search**: split Category and Time filters, a minimum
  priority filter, full-text search over titles and notes, and a collapsible
  group view. Filter selections persist between runs.
- **Per-task documents**: every task gets a Markdown file with a public "displayed
  notes" section (synced with the app) and a private notes section the app never
  shows.
- **Daily journal**: jot timestamped entries; completing a task is auto-logged to
  that day's journal.
- **Mantras**: a rotating motivational line, optionally shown once per day at launch.
- **Hazard escalation** (opt-in): repeating tasks you keep skipping automatically
  bump in priority until you deal with them.
- **Reminders**: each task can surface "checkpoint" nudges (a ⏰ chip and a
  Reminders list) on the way to its due date.
- **Stats**: open/done counts and top streaks for recurring tasks.
- **Import** tasks from a `.txt` file or by pasting text.
- **Light / Dark themes** (View → Toggle Dark Mode), remembered between runs.

## Getting Started

Requires **Python 3.13+** with Tkinter (bundled with the standard CPython
installer on Windows and macOS).

```powershell
# Windows
.\run.ps1        # creates a .venv and launches the app
# or
.\run.bat
```

```bash
# Any platform
python -m tasklistprogram
```

## Quick Start

- **Add a task**: fill in Title (and optionally Due / Priority / Repeat / Notes),
  then click **Add**. Pressing **Shift+Enter** in the Title field quick-adds a
  task due tomorrow.
- **Edit a task**: double-click any row.
- **Mark done**: select task(s) and click **Mark Done** (or Ctrl+Enter).
- **Delete / restore / suspend**: use the buttons or the right-click menu.
- **Bulk edits**: select several rows and use the right-click **Edit** submenu to
  set priority, repeat, due, group, or to bump dates.

## Fields

| Field | Meaning |
|-------|---------|
| **Title** | Short label for the task. |
| **Due** | Date and optional time (see formats below). Optional. |
| **Priority** | `H` High, `M` Medium, `L` Low, `D` Daily habit (forces daily repeat), `Misc`. `Ultra` is set automatically by hazard escalation. |
| **Repeat** | none, daily, weekdays, weekly, bi-weekly, monthly, or custom (every N days). |
| **Notes** | Free text. Also written to the task's Markdown document. |
| **Group** | Optional label for organizing related tasks in group view. |

## Due Date Formats

| Input | Result |
|-------|--------|
| `2026-10-05` | date only |
| `2026-10-05 14:00` | date with time |
| `10/05` | MM/DD in the current year |
| `10/05 14:00` | MM/DD with time |
| `14:00` or `1400` | today at that time |
| `today` / `tomorrow` / `yesterday` | that day (optional trailing time, e.g. `tomorrow 14:00`) |
| `fri`, `monday`, … | next occurrence of that weekday |
| `Sept 29`, `September 29 2027` | month-name date (optional trailing time) |
| `morning` / `noon` / `afternoon` / `evening` | today at 08:00 / 12:00 / 16:00 / 20:00 |
| `midnight` | today at 23:59 |
| `+2d +3h` | relative: combine `+/-N` with `d` (days), `h` (hours), `m` (minutes), `w` (weeks) |

> Don't mix natural words and relative tokens in one value (e.g. `+1w friday` is
> invalid). Pick one style. All formats above work everywhere a due value is typed
> (Add box, Edit dialog, Set Due, and import).

## Tips

- Use **Group view** to collapse tasks by group; the caret button expands/collapses all.
- **Search** filters both titles and notes.
- The **Category** + **Time** filters are independent — e.g. Category `active` with
  Time `today`. Note: with a Time filter other than `any`, tasks **without a due
  date are hidden**; switch Time to `any` to see them.
- Filter selections, group view, and settings are saved between sessions.

## Data & Privacy

All user data is stored locally under `tasklistprogram/data/` and is **gitignored**
(never committed):

```
tasklistprogram/data/
├── tasks_gui.json            # the task database (atomic writes)
├── tasks_gui.json.bak        # automatic backup of the previous save
├── task_documents/<Group>/<Title>-<id>.md   # per-task notes (public + private sections)
├── journals/<YYYY>/<MM>/<YYYY-MM-DD>.md      # daily journal + auto-logged completions
└── mantras.md                # your mantras, one per line
```

See [docs/USER_GUIDE.md](docs/USER_GUIDE.md) for a full walkthrough and
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the code layout.

## Project Structure

```
TasklistProgram/                 # repository root
├── tasklistprogram/             # the application package
│   ├── __main__.py              # entry point (python -m tasklistprogram)
│   ├── app.py                   # main window, menus, filtering, scheduling
│   ├── core/                    # business logic (no UI)
│   │   ├── model.py             # JSON load/save, settings, stats
│   │   ├── actions.py           # task operations (done/delete/bulk/bump)
│   │   ├── dates.py             # due-date parsing & recurrence math
│   │   ├── filters.py           # filter/search/sort predicates
│   │   ├── scheduler.py         # recurrence advancement (midnight reset)
│   │   ├── documents.py         # task docs, journals, mantras
│   │   ├── io_import.py         # text/file import
│   │   ├── reminders.py         # reminder checkpoints
│   │   └── constants.py         # priority order & icons
│   ├── ui/                      # Tkinter widgets
│   │   ├── listview.py          # the task table (Treeview)
│   │   ├── dialogs.py           # Edit/Stats/Settings/Help/… dialogs
│   │   └── controls.py          # autocomplete entry
│   └── data/                    # local user data (gitignored)
├── docs/                        # documentation
├── tests/                       # unittest suite (stdlib, no deps)
├── run.ps1 / run.bat           # launchers
└── pyproject.toml
```

## Development

The project uses only the Python standard library, including the test suite, so no
install step is needed to run the tests:

```bash
python -m unittest discover -s tests
```

The tests cover the pure-logic modules (`dates`, `filters`, `scheduler`,
`reminders`, `io_import`, `model`) and run headlessly (no Tkinter window).

## Documentation

See [`CLAUDE.md`](CLAUDE.md) for a one-page project profile, and
[`docs/`](docs/README.md) for everything:

- [User Guide](docs/USER_GUIDE.md) — every feature explained.
- [Importing](docs/IMPORTING.md) — bulk-import format + a copy-paste **AI prompt** to format tasks.
- [Architecture](docs/ARCHITECTURE.md) — module map, data flow, file formats, web server.
- [Features & parity](docs/FEATURES.md) — desktop ↔ web feature matrix.
- [Design](docs/DESIGN.md) — UI direction and the web/mobile + privacy plan.
- [Roadmap](docs/ROADMAP.md) · [Ideas](docs/IDEAS.md) · [Bugs](docs/BUGS.md) · [Changelog](docs/CHANGELOG.md)

## Web prototype

A static preview of the planned **web/mobile** version lives in [`web/`](web/README.md) —
open `web/index.html` in a browser (sample data only). It shows the professional,
website-style direction described in the [design doc](docs/DESIGN.md).

<img width="1455" height="1306" alt="image" src="https://github.com/user-attachments/assets/76faf5af-0487-44cc-815e-f5aaff020378" />
