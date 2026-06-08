# Ideas Backlog

A parking lot for ideas — not commitments. When one is picked up, move it to
[ROADMAP.md](ROADMAP.md) (active plan) and, once shipped, note it in
[CHANGELOG.md](CHANGELOG.md). The big strategic vision (web/mobile, hosting, mood,
notifications) lives in [DESIGN.md](DESIGN.md).

## Organization & workflow
- **Smart / fewer groups.** ~20 groups is noisy. Options: sections (group-of-groups),
  collapse rarely-used groups by default, or **auto-group related tasks** by context
  (supplements taken together, a "morning routine"). Maybe ship a few **designed
  templates** (Supplements, Meals, Morning) instead of only free-form groups.
- **Clearer recurring instances.** A task that recurs as just "meal" is ambiguous —
  per-occurrence labels (Breakfast/Lunch/Dinner) or a title pattern so the day's
  instance is self-explanatory.
- **Export** (the inverse of import) — round-trip the pipe format for backups/sharing.
- **Bulk edit on web** (multi-select → set priority/repeat/due/group, bump).

## Tracking & insight
- **Mood tracking** + correlation with habit completion / sleep / training (see DESIGN).
- Richer **stats**: completion trends, per-group throughput, "best day," calendar view.
- **Streak heatmaps per habit** on the desktop too (web has one).

## Notifications & reminders
- Real **desktop notifications** (toast) on due/checkpoint, not just the passive chip.
- **Web push** from the PWA (due reminders, daily mantra, mood check-in) — needs the
  hosting/auth phase.

## UI / UX
- Quieter priority encoding everywhere (left-bar instead of full-row flood — done on web).
- Tooltips, friendlier empty states, remember window size/position (desktop).
- Keyboard-first flow on web (e=edit, d=done, / = focus search).
- Inline date picker (custom widget; avoid a 3rd-party dep), accessibility (ARIA).
- Reduce per-row chip clutter on dense lists.

## Platform & data
- **SQLite** single source of truth (also unblocks safe concurrency) — see ROADMAP.
- **Configurable data dir** — done (`TINYTASKLIST_DATA_DIR`); could add a settings UI.
- **Auth + hosting** for private phone access (DESIGN, Phases 3–4).
- **Naming/branding** before a public URL (it's really a routine/task/journal/mood
  companion, not just "Tiny Tasklist").

## Quality
- Add `pytest`-style coverage reporting (optional; keep stdlib-runnable).
- A tiny CI (GitHub Actions) running `unittest` + `node --check`.
