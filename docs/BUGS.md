# Bugs & Known Issues

Tracks defects: **Open** (to fix) and **Fixed** (recent, for history). For feature
*gaps* (not bugs) see [FEATURES.md](FEATURES.md); for plans see [ROADMAP.md](ROADMAP.md).

Severity: 🔴 high · 🟠 medium · 🟡 low.

## Open

- 🟠 **Desktop stats undercount recurring "done today".** `model.stats_summary`
  counts only `completed_at`, which is cleared when a recurring task advances, so
  recurring completions today aren't counted. The web stat was fixed (uses history);
  apply the same to `stats_summary`. `core/model.py`.
- 🟠 **Web static/sample mode due parsing is simplistic.** `parseQuickDue` in
  `web/app.js` only handles today/tomorrow/+Nd/ISO; live mode uses the full server
  parser. Acceptable for the sample demo, but inconsistent. `web/app.js`.
- 🟡 **Streak off-by-one.** `stats_summary` streak counts from *yesterday*, so a task
  done every day including today reads one fewer. Decide if "today counts."
- 🟡 **Reminder chip vs. dialog acknowledgement.** The ⏰ chip lights for *any*
  elapsed unacknowledged checkpoint, but the Reminders dialog surfaces only the
  latest, so clearing the chip can take several acks. `core/reminders.py`.
- 🟡 **Time filter hides date-less tasks** (both front-ends, by design). A new no-due
  task "disappears" unless Time = Any. Consider surfacing no-due active tasks or a hint.

## Fixed (recent)

- ✅ **Desktop ↔ web concurrent-edit clobber** (was 🔴). Storage moved to SQLite with
  atomic transactions; the desktop reloads on focus when the store `rev` changed, and
  the web reads fresh per request — so for normal single-user use the last-writer-wins
  window is closed. Residual: simultaneous same-task edits in both visible windows →
  future per-row granular writes. `core/model.py`, `app.py`. (2026-06-08)
- ✅ **Web front-end fully dead from a JS syntax error** (duplicate `title` in
  `renderHabits`) — nothing rendered, dark mode/edits did nothing. Fixed + added a
  `node --check` test guard. (2026-06-07)
- ✅ **Crash loading a `tasks_gui.json` with a UTF-8 BOM** (Notepad/PowerShell saves)
  — `_load_json` now uses `utf-8-sig`. Regression test added. (2026-06-07)
- ✅ **CRITICAL: web concurrent writes could lose data** — read-modify-write now
  serialized with a lock. (2026-06-07)
- ✅ **Web showed suspended tasks** the desktop hides (active/today views) — now
  excluded; added a Suspended view. (2026-06-07)
- ✅ **Edit dialog crash** picking "custom" repeat (`simpledialog` not imported). (2026-06-07)
- ✅ **Reminders ignored Ultra/Misc** priorities (ad-hoc maps omitted `U`) — now use
  the canonical `PRIORITY_ORDER`. (2026-06-07)
- ✅ **Misc rows looked like group headers** (both pale blue) — group header is now
  neutral gray; web uses a blue priority bar. (2026-06-07)
- ✅ **Latent infinite loop** advancing a malformed repeat — added a no-progress guard
  in `core/scheduler.py`. (2026-06-07)
- ✅ **In-app Help advertised unsupported date formats** (`tomorrow`, `Sept 29`) —
  implemented them in `core/dates.py`. (2026-06-07)

---
*When fixing an Open item, move it to Fixed with a date and the commit/file, and add
a regression test where practical.*
