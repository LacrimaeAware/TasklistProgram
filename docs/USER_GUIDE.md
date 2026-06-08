# User Guide

A complete walkthrough of Tiny Tasklist. For installation see the
[README](../README.md); for the code layout see [ARCHITECTURE.md](ARCHITECTURE.md).

## The main window

- **Top input row** — Title, Due, Priority, Repeat, Notes, and the **Add** and
  **Stats** buttons.
- **Filter row** — Category, Time, Search, Min prio, Group view, an expand/collapse
  caret, and the **Mark Done / Delete / Suspend** action buttons.
- **Task table** — one row per task, color-coded by priority, optionally grouped.
  Click any column header to sort by it; click again to reverse. The active sort
  column shows a ▲/▼ arrow.
- **Status bar** (bottom) — a quick summary: how many tasks are showing, how many
  are open, and how many you've completed today.

### Row colors

Each priority has its own row color — 🚨 Ultra (red), 🔴 High, 🟠 Medium,
🟡 Low, 🟢 Daily, 🔵 Misc (blue). Group headers use a neutral gray bar so they're
always distinguishable from task rows. Deleted/suspended tasks are grayed out.

### Light / Dark mode

**View → Toggle Dark Mode** switches the theme; your choice is remembered between
runs. (Dark mode is v1 — the main window is fully themed; a few popup dialogs may
still appear light for now.)

## Adding tasks

1. Type a **Title** (required). The Title field autocompletes from past tasks.
2. Optionally set **Due**, **Priority**, **Repeat**, and **Notes**.
3. Click **Add**, or press **Enter** in the Notes box.

Shortcut: **Shift+Enter** in the Title field quick-adds a task due *tomorrow* with
Medium priority.

> If you add a task with **no due date** while the **Time** filter is set to
> anything other than `any`, the new row won't appear (date-less tasks are hidden
> by time filters). Switch Time to `any` to see it.

## Editing tasks

- **Double-click** a row, or right-click → **Edit → Manual Edit**.
- The Edit dialog covers Title, Due, Priority, Repeat, Group, and Notes.
- Selecting **custom** repeat asks how many days between repeats.

For several tasks at once, select multiple rows and use the right-click **Edit**
submenu: **Set Priority**, **Set Repeat**, **Set Due**, **Set Group**, or **Bump**
(±1 day / ±1 week).

## Priorities

| Code | Name | Color | Notes |
|------|------|-------|-------|
| `U` | Ultra | red | Set automatically by hazard escalation; not chosen directly. |
| `H` | High | pink-red | |
| `M` | Medium | orange | Default. |
| `L` | Low | yellow | |
| `D` | Daily | green | Choosing Daily forces the repeat to `daily`. |
| `Misc` (`X`) | Misc | blue | "Someday / uncategorized" bucket. |

## Repeat options

| Repeat | Meaning |
|--------|---------|
| none | one-off task |
| daily | every day |
| weekdays | Mon–Fri |
| weekly | every 7 days |
| bi-weekly | every 14 days |
| monthly | same day next calendar month (clamped to month length) |
| custom:N | every N days (you pick N) |

When you **Mark Done** a repeating task, it logs the completion and then advances
to its next due date, reappearing as a fresh checklist item.

## Due dates and times

See the table in the [README](../README.md#due-date-formats). Highlights:

- Absolute: `2026-10-05`, `2026-10-05 14:00`, `10/05`, `10/05 14:00`.
- Bare time: `14:00` or `1400` → today at that time.
- Day words: `today`, `tomorrow`, `yesterday` (optionally with a time, e.g.
  `tomorrow 14:00`).
- Weekdays: `fri`, `monday` → the next such day.
- Month names: `Sept 29`, `September 29 2027` (optionally with a time).
- Dayparts: `morning`/`noon`/`afternoon`/`evening`.
- `midnight` → today 23:59.
- Relative: `+2d +3h` (`d` days, `h` hours, `m` minutes, `w` weeks).

Don't mix words and relative tokens (`+1w friday` is rejected). All of these work
everywhere a due value is typed — the Add box, the Edit dialog, Set Due, and import.

## Filtering, search, and grouping

- **Category**: `active`, `repeating`, `overdue`, `done`, `deleted`, `suspended`,
  `all`. `active` hides done/deleted/suspended tasks.
- **Time**: `any`, `today`, `week`, `month`, or `custom` (pick a cutoff date). For
  `today`, overdue items roll forward and stay visible.
- **Search**: matches titles and notes as you type.
- **Min prio**: hides anything below the chosen priority.
- **Group view**: collapses tasks under their group headers; double-click a header
  or use the caret button to expand/collapse everything.

Your Category, Time, Min prio, and Group view choices are saved between runs.

## Task documents (notes files)

Each task has a Markdown file at
`data/task_documents/<Group>/<Title>-<id>.md`. Right-click → **Open Document…**
(or the menu) opens it. The file has two sections separated by a divider:

```
<your displayed notes — synced with the task's Notes field>
--- Displayed notes ↑ | Private notes ↓ ---
<private notes — kept in the file, never shown in the app>
```

Editing the **top** section in the file and reopening it through the app pulls your
changes back into the task's Notes. The **bottom** section is yours alone.

## Journal

- **Journal → Journal…** opens a box to add a timestamped entry to today's file.
- **Journal → Open Today's Journal** opens the Markdown file directly.
- Completing any task auto-appends a line under "## Completed Tasks" in that day's
  journal.

Journals live at `data/journals/YYYY/MM/YYYY-MM-DD.md`.

## Mantras

- **Mantras → Show Mantra…** shows a mantra; "Show another" rotates, "Add mantra"
  appends a new one.
- **Mantras → Open Mantra File** edits `data/mantras.md` directly (one mantra per
  line; lines starting with `#` and `<!-- -->` blocks are ignored).
- A "mantra of the day" can auto-show once at the first launch each day (toggle in
  Settings).

## Reminders

Reminders nudge you toward a due date with "checkpoints" spread between when a task
was created and when it's due.

- A **⏰ chip** appears in the REM column when a checkpoint is due and not yet
  acknowledged.
- **File → Reminders…** lists pending checkpoints; select rows and **Acknowledge**
  to dismiss them.

Configure in **Settings**: enable/disable, checkpoints per task, and the minimum
priority that gets reminders. *(There is currently no automatic pop-up — check the
Reminders list or watch the ⏰ chip.)*

## Hazard escalation

Opt-in nudging for recurring tasks you keep skipping. When enabled (Settings →
"Enable hazard escalation"):

- Each missed occurrence at midnight raises the task's `skip_count`.
- After 2 skips the priority jumps to **High** (your original is remembered); after
  3 it jumps to **Ultra**. A **⚠** appears before the title.
- **Mark Done** clears the escalation and restores the original priority.
- Settings → "Reset all hazard escalation to baseline on Save" clears it for every
  task.

## Importing tasks

**File → Import Tasks…** (from a `.txt` file) or **Import (paste text)…**. One task
per line:

```
Title | due: <date/time/+rel> | prio: H/M/L/D/Misc | repeat: none/daily/weekdays/weekly/bi-weekly/monthly/custom:<days> | group: <name> | notes: <text>
```

- Text before the first `|` becomes the title; every field is optional.
- `prio: D` forces `repeat: daily`; `custom` repeats need a positive day count
  (e.g. `custom:6`).
- Lines that fail to parse are reported with the reason; the rest still import.

**Got a messy list?** See [IMPORTING.md](IMPORTING.md) for the full format and a
**copy-paste AI prompt** — hand an AI your raw tasks and it returns clean importable
lines. In the web import dialog, the **“Copy AI prompt”** button copies it for you.

Examples:

```
Buy groceries
Midterm Exam | due: 10/13 14:00 | prio: H | group: School | notes: bring calculator
Daily standup | repeat: daily | prio: D | group: Work
Water plants | repeat: custom:6 | prio: L | group: Home
Pay rent | due: +5d | prio: H | group: Life Admin
```

## Settings summary

| Setting | Default | Effect |
|---------|---------|--------|
| Enable reminders | off | Master switch for checkpoints and the ⏰ chip. |
| Reminder count | 4 | Checkpoints per task. |
| Min priority for reminders | M | Lowest priority that gets reminders. |
| Min priority to show | L | Hides lower-priority tasks from the list. |
| Enable hazard escalation | on | Auto-bump skipped recurring tasks. |
| Show mantra at first launch each day | on | Daily mantra pop-up. |
| Reset all hazard escalation | — | One-shot reset on Save. |

## Keyboard shortcuts

| Keys | Action |
|------|--------|
| Enter (in Notes) | Add task |
| Shift+Enter (in Title) | Quick-add due tomorrow |
| Double-click row | Edit task |
| Delete | Soft-delete selected |
| Ctrl+Enter | Mark done |
