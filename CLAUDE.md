# Tiny Tasklist — project profile (for humans & AI)

Read this first. It's the fast map of the project; deeper docs live in [`docs/`](docs/).

## What it is
A local-first, single-user **task + habit tracker**. Two front-ends over **one JSON
data file**:
- **Desktop** — Python + Tkinter, zero third-party deps. The full-featured original.
- **Web** — a static HTML/CSS/JS app served by a stdlib HTTP server
  (`tasklistprogram/webserver.py`) that exposes a JSON API over the same `core/`
  logic and the same data file. Local-only (`127.0.0.1`), no auth yet.

Nothing is sent anywhere; all data stays on disk.

## Run it
```bash
python -m tasklistprogram            # desktop app
python -m tasklistprogram.webserver  # web app at http://localhost:8000  (or run_web.bat)
python -m unittest discover -s tests # tests (stdlib, no install)
node --check web/app.js              # lint the web script (if Node present)
```
The desktop app also has **View → Open Web App** to launch the server + browser.

## Layout
```
tasklistprogram/
  app.py            desktop window (menus, filters, scheduling) — mixes in ActionsMixin
  webserver.py      stdlib HTTP server + JSON API (second front-end)
  core/             pure logic, no UI:
    model.py        JSON load/save (atomic + .bak + daily backups), settings, stats
    dates.py        due parsing (parse_due_entry) + recurrence math
    filters.py      filter/search/sort predicates
    scheduler.py    recurrence advancement (midnight reset)
    actions.py      desktop task ops (done/delete/bulk/bump) — Tk mixin
    documents.py    per-task notes files, journals, mantras
    io_import.py    text/file import
    reminders.py    reminder checkpoints
    constants.py    priority order/icons
  ui/               Tkinter widgets: listview, dialogs, controls, theme, assets/icon
web/                index.html, styles.css, app.js, sample-data.js  (the web front-end)
tests/              unittest suite
docs/               all documentation (see docs/README.md)
```

## Data (gitignored — never commit)
`tasklistprogram/data/`: **`tasks.db`** (SQLite, the primary store) + `tasks_gui.json.bak`
(previous state, JSON) + `tasks_gui.json.premigration` (the original pre-SQLite JSON,
kept for safety) + `backups/tasks_gui_YYYY-MM-DD.json` (14-day rotation) +
`task_documents/<Group>/<Title>-<id>.md` + `journals/YYYY/MM/*.md` + `mantras.md`.
Override location with the `TINYTASKLIST_DATA_DIR` env var. **In tests/manual runs,
always point that env var (and/or `model.DB_FILE`) at a temp dir — never the real store.**

## Conventions
- **Zero runtime dependencies.** Tests use stdlib `unittest`. Keep it that way.
- **Logic lives in `core/` (UI-free) and is unit-tested.** UI is a thin shell.
- A task is a dict; see the schema in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
- After web changes, run `node --check web/app.js` (a syntax error silently kills the
  whole front-end — there's a test guard for this).
- Don't touch real data in tests/manual runs — point `TINYTASKLIST_DATA_DIR` at a temp dir.

## Current state & where to look
- **Feature parity** (desktop vs web): [docs/FEATURES.md](docs/FEATURES.md)
- **What changed, when**: [docs/CHANGELOG.md](docs/CHANGELOG.md)
- **Open bugs / known issues**: [docs/BUGS.md](docs/BUGS.md)
- **Plan & priorities**: [docs/ROADMAP.md](docs/ROADMAP.md)  ·  **Ideas**: [docs/IDEAS.md](docs/IDEAS.md)
- **Direction (UI, web/mobile, privacy)**: [docs/DESIGN.md](docs/DESIGN.md)

**Concurrency:** storage is SQLite (atomic transactions); the web reads fresh per
request and the desktop reloads on focus when the store's `rev` changed — so the two
front-ends stay consistent for normal single-user use. (Per-row granular writes are a
future hardening for the simultaneous-same-task edge case.)
