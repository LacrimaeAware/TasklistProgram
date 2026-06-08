# Features & Desktop ↔ Web Parity

The source-of-truth inventory of every feature, and where each stands on the two
front-ends. Keep this updated when features land. Legend: ✅ full · ⚠️ partial ·
❌ missing · ➕ front-end-only bonus.

## Task lifecycle

| Feature | Desktop | Web | Notes |
|---|:--:|:--:|---|
| Add task (title/due/priority/repeat/notes/group) | ✅ | ✅ | Web add-modal includes notes + group. |
| Quick-add (due tomorrow) | ✅ | ❌ | Desktop: Shift+Enter in title. |
| Edit task | ✅ | ✅ | Web: click a row or right-click → Edit. |
| Mark done (+ recurrence advance, history, journal) | ✅ | ⚠️ | Web advances recurrence + history, but does **not** write the journal completion line. |
| Undo a completion | ❌ | ➕ | Web has an Undo toast (restores snapshot); desktop has no quick undo. |
| Soft delete / Restore | ✅ | ✅ | |
| Hard delete (permanent) | ✅ | ✅ | Both confirm first. |
| Suspend / Unsuspend | ✅ | ✅ | |
| Bulk actions on multi-select | ✅ | ❌ | Desktop: set priority/repeat/due/group, clear group, bump ±day/week. Web: none. |
| Bump due date (±day/week/month) | ✅ | ⚠️ | Web can edit the due field, but no one-click bump. |

## Priorities & recurrence

| Feature | Desktop | Web | Notes |
|---|:--:|:--:|---|
| Priorities U/H/M/L/D/Misc (color + icon) | ✅ | ✅ | |
| "Daily" forces daily repeat | ✅ | ✅ | |
| Repeats none/daily/weekdays/weekly/bi-weekly/monthly | ✅ | ✅ | |
| Custom repeat (every N days) | ✅ | ❌ | Not in the web editor's repeat dropdown yet. |
| Flexible due parsing (dates, MM/DD, bare time, weekday, daypart, today/tomorrow, month names, +rel, midnight) | ✅ | ⚠️ | Web **live** mode uses the same parser; web **static/sample** mode is simplistic. |

## Views, filters, organization

| Feature | Desktop | Web | Notes |
|---|:--:|:--:|---|
| Category filter (active/repeating/overdue/done/deleted/suspended/all) | ✅ | ✅ | Web: left sidebar. |
| Time filter (any/today/week/month) | ✅ | ✅ | |
| Custom date filter | ✅ | ❌ | Desktop has a date picker; web has no custom range. |
| Min-priority filter | ✅ | ✅ | |
| Search (title + notes) | ✅ | ✅ | |
| Group view (collapsible headers) | ✅ | ✅ | Web: ▤ Group toggle + Collapse all; state persists. |
| Focus a single group | ✅ | ✅ | Web: click a group in the sidebar. |
| Column-header sorting (asc/desc) | ✅ | ❌ | Web sorts by due then priority only. |
| Persist filter/view choices | ✅ | ✅ | Desktop: settings; web: localStorage. |

## Reminders, hazard, stats

| Feature | Desktop | Web | Notes |
|---|:--:|:--:|---|
| Reminder checkpoints + ⏰ chip + Reminders dialog | ✅ | ❌ | Not on web yet. |
| Hazard escalation display (⚠) | ✅ | ✅ | |
| Reset hazard escalation | ✅ | ✅ | Web: ⚙ menu. |
| Configure hazard / reminders (Settings) | ✅ | ❌ | No web Settings dialog. |
| Stats (open / done today / streaks) | ✅ | ⚠️ | Web shows stat cards; "done today" counts recurring via history. |
| Habit streak heatmap | ❌ | ➕ | Web-only, under the Repeating view. |
| Midnight recurrence rollover (catch-up) | ✅ | n/a | Server-side advance happens on desktop launch / midnight; web relies on it. |

## Content & extras

| Feature | Desktop | Web | Notes |
|---|:--:|:--:|---|
| Per-task Markdown document (public + private notes) | ✅ | ❌ | Web edits the `notes` field but can't open the doc / private section. |
| Daily journal (add entry, open, auto-log completions) | ✅ | ❌ | Not on web. |
| Mantras (show/add/open, daily auto-show) | ✅ | ❌ | Not on web. |
| Import (.txt file / paste) | ✅ | ❌ | Not on web. |
| Help / Guide dialog | ✅ | ❌ | Web has inline hints only. |
| Open data folder | ✅ | n/a | Desktop: File menu. |

## Platform / chrome

| Feature | Desktop | Web | Notes |
|---|:--:|:--:|---|
| Light / Dark theme | ✅ | ✅ | Web follows OS preference + remembers. |
| App icon (window/taskbar) | ✅ | ✅ | Web uses it as favicon. |
| Status bar (counts) | ✅ | ⚠️ | Web shows stat cards instead. |
| Autocomplete (title/group) | ✅ | ❌ | |
| Keyboard shortcuts | ✅ | ⚠️ | Web: Esc closes menus/modal; fewer than desktop. |
| Responsive / mobile layout | n/a | ➕ | Web collapses to a single column. |
| Open from the other front-end | ✅ | n/a | Desktop: View → Open Web App. |

## Biggest remaining web gaps (priority order)
1. **Reminders** (checkpoints + chip + list)
2. **Per-task document + private notes** access
3. **Journal** and **Mantras**
4. **Import** (paste/file)
5. **Custom repeat** in the editor, **custom date** filter
6. **Bulk actions** + **bump**
7. **Column-header sorting**, **Settings** dialog, **autocomplete**

See [ROADMAP.md](ROADMAP.md) for sequencing.
