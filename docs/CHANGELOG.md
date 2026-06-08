# Changelog

Notable changes, newest first. Dates are local. This was a doc-sparse project early
on (pre-AI-assist), so entries before 2026-06 are reconstructed from git history and
are coarser.

## 2026-06-08 — Backups + documentation system

- **Automatic daily backups.** `save_db` now writes a dated snapshot to
  `data/backups/tasks_gui_YYYY-MM-DD.json`, pruned to the last 14 days, in addition
  to the immediate `.bak`. Cheap (one write/day), never breaks a save.
- **Documentation overhaul** (this set): `CLAUDE.md` project profile, `docs/FEATURES.md`
  (desktop↔web parity matrix), this changelog, `docs/IDEAS.md`, `docs/BUGS.md`, and a
  `docs/README.md` index. README/ROADMAP cross-linked.

## 2026-06-07 — Web app reaches desktop parity; quality pass

A large multi-session pass (committed 06-07).

- **Web app full parity push** (driven by a 39-finding multi-agent audit):
  - Collapsible **Group view** in the main list (see/minimize multiple groups).
  - Full **filters**: Category sidebar × Time × Min-priority × Search, persisted.
  - **Deleted** management (view, Restore, Delete-permanently) + **hazard reset**.
  - **CRITICAL fix:** serialized the web server's read-modify-write with a lock so
    concurrent requests can't lose data.
  - Task **editing** (click row / right-click context menu), **undo** toast,
    **suspended** parity, **Completed** ordered by recency.
  - Fixed "Done today" stat (counts recurring via history); habit heatmap excludes
    suspended.
- **Web backend** (`webserver.py`): stdlib HTTP server serving the web UI + a JSON
  API (`/api/tasks`, toggle/done, PATCH, delete, hard-delete, hazard reset, stats)
  over the same `core/` logic and data file; front-end auto-detects live vs sample.
- **Web prototype → app**: `web/` UI (sidebar, stat cards, priority left-bars,
  streak heatmap, light/dark, responsive). App **icon** (`tools/make_icon.py`),
  **Today** preset, status bar, sort arrows, calmer colors, dark-mode follows OS.
- **Robustness:** `_load_json` tolerates a UTF-8 BOM (no more crash on Notepad/
  PowerShell saves); fixed a JS syntax error that had silently broken the whole
  front-end (+ a `node --check` test guard).
- **Desktop quality pass:** fixed an Edit-dialog crash; unified due parsing
  (`parse_due_entry`: bare time, today/tomorrow, month names everywhere); Misc
  selectable in Edit; reminders use the canonical priority order (Ultra/Misc fixed);
  removed dead code; `print` → `logging`.
- **Modularization:** extracted `core/filters.py` and `core/scheduler.py`; mantra
  pickers → `core/documents.py`; slimmed `app.py`.
- **Tests:** introduced a stdlib `unittest` suite (now 111 tests) covering
  dates/filters/scheduler/reminders/io_import/model/webserver + a web syntax guard.
- **Docs:** rewrote README; added ARCHITECTURE, USER_GUIDE, DESIGN, ROADMAP.
- **Theming:** `ui/theme.py` Light/Dark palettes + View → Toggle Dark Mode (desktop).
- Dropped the stray "(Modular)" window title; filled in `pyproject.toml`.

## 2026-02-22 — Repeats & filter UX

- Added **bi-weekly** and **custom (every N days)** repeat options.
- Added a **hazard escalation reset** control.
- Split filtering into **Category** + **Time**; improved import diagnostics; refined
  the custom-date button placement.

## 2026-02-01 — Documents, journal, mantras

- **Per-task Markdown documents** with a displayed/private notes separator.
- **File-based mantras** with a clear format; placeholder text and default settings.
- Task document menu options; display-notes external-change sync.
- Edit cascade submenu; bump escalation fix.

## 2026-01-31 — Early structure

- Reorganized project structure; initial README; `.gitignore` hardening.

---
*Conventions: group entries by date; lead with the user-facing change; note any
data-format or breaking changes explicitly.*
