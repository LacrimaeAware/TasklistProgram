# Tiny Tasklist — Design Document

This is the "north star" doc: what the app is, who it's for, the design principles,
and — most importantly — the strategic decisions about **the UI direction** and
**where the app should go next** (a better-looking UI, and access from a phone /
the owner's website). It's a living document; nothing here is committed in stone.

> Privacy note: this doc is committed to a public repo, so it describes usage
> *patterns* abstractly and contains no personal task content.

---

## 1. What it is today

A local-first, single-user desktop app (Python + Tkinter, zero third-party deps)
that is equal parts **to-do list** and **habit/recurring-task tracker**, with
per-task notes, a daily journal, mantras, and lightweight reminders. All data is
plain JSON + Markdown on disk; nothing leaves the machine.

## 2. Who it's for (usage profile)

Derived from the owner's real data (aggregate only):

- **Heavy, sustained daily use** — hundreds of tasks over many months, ~1,000+
  completions, single habits completed 60+ times.
- **Recurring-first.** A large share of tasks repeat (daily / weekly / **bi-weekly,
  the single most-used cadence** / monthly). This is as much a routine tracker as a
  task list.
- **Two big domains:** coursework (assignments, classes, deadlines) and
  self-care/fitness (training, diet, supplements, medication, maintenance routines).
- **Organization-heavy:** ~20 active groups; grouping and filtering matter at scale.
- **Notes-heavy:** most tasks carry notes / a Markdown document.
- **Reminders are used; hazard-escalation is not** (it has never actually fired).

**Implications for design:** the default experience should center on *today's
routine + what's due*, make *recurring/streaks* first-class, scale gracefully to
hundreds of tasks across many groups, treat *notes* as first-class, and stay
fast to capture. Mood tracking and real notifications fit the self-care theme
naturally. A simpler escalation/priority model may serve better than the current
hazard feature.

## 3. Design principles

1. **Local-first & private by default.** The owner's data (incl. health/medication
   and, soon, mood) is sensitive. It must never land in the public repo, and any
   networked version must be access-controlled and owner-hosted.
2. **Routine over reminders.** Optimize for the daily ritual: open → see today →
   check things off → journal → done.
3. **Fast capture, low friction.** Keyboard-first, quick-add, sensible defaults.
4. **Scales to hundreds of items** across many groups without becoming noisy.
5. **Notes are first-class**, not an afterthought.
6. **One source of truth for logic.** UI is a thin shell over a tested core (already
   true: `core/` is pure and unit-tested). This is what makes a future UI/platform
   change cheap.

## 4. Current architecture (recap)

See [ARCHITECTURE.md](ARCHITECTURE.md). The important property for everything below:
**business logic lives in `core/` with no UI dependency** (model, dates, filters,
scheduler, reminders, documents, io_import). The Tkinter UI in `ui/` + `app.py` is
a shell. That separation is the foundation for any UI redesign or platform move.

## 5. UI / UX direction (acting as designer)

### Diagnosis of the current UI
- The Tkinter look is functional but dated, and theming is genuinely painful (the
  v1 dark mode had to switch ttk themes and hand-color classic widgets — a smell
  that the toolkit is fighting us).
- **Full-row flood colors** for every priority make a dense list loud, and caused
  the reported Misc-vs-group-header confusion.
- No dedicated **Today/Focus** view despite that being the core daily use.
- No **calendar/upcoming** view despite heavy deadline use.
- No **streak/habit** visualization despite 1,000+ completions.

### Proposed visual language
- **Quieter priority encoding:** replace full-row flood with a **colored left bar +
  subtle tint** per row. Keeps at-a-glance priority, far less visual noise, scales
  better, and removes color clashes. (Group headers stay a clearly different,
  neutral bar — already fixed.)
- **A typographic scale** (one base font, a couple of sizes/weights) and consistent
  spacing tokens, all defined in one place (already started: `ui/theme.py`).
- **Light/Dark themes** from one palette module (done, v1).

### Proposed layout (target)
```
┌───────────┬──────────────────────────────┬──────────────┐
│ Sidebar   │  Main list / view            │ Detail pane  │
│ • Today   │  (filtered, grouped, sorted) │ selected task│
│ • Upcoming│                              │  + notes/doc │
│ • Habits  │                              │  preview     │
│ • Groups… │                              │              │
│ • Search  │                              │              │
└───────────┴──────────────────────────────┴──────────────┘  + status bar
```
- **Today/Focus** as the default view (due today + overdue + daily habits).
- **Upcoming/Calendar** for coursework deadlines.
- **Habits** view with a streak heatmap.
- **Groups** as a sidebar (replaces the Category combobox for navigation).
- **Detail pane** showing the selected task's notes/document inline (instead of
  shelling out to an external editor).

### Incremental UI wins (regardless of platform) — see [ROADMAP.md](ROADMAP.md)
Tooltips, empty-state hints, remember window geometry, keyboard shortcuts, a
"Today" filter preset, and the priority-bar restyle can all land in the current
Tkinter app cheaply.

## 6. The strategic question: stay on Tkinter, or move?

The owner wants (a) a much nicer UI and (b) access from a phone, ideally woven into
their personal website, plus (c) mood tracking and notifications. These goals point
in different directions, so let's separate them.

### Options

| Option | Nicer UI? | Phone / web? | Effort | Notes |
|--------|-----------|--------------|--------|-------|
| **Polish Tkinter** | somewhat | ❌ | low | Dead end for phone; theming is painful. |
| **CustomTkinter** | yes (modern Tk skin) | ❌ | low–med | Quick visual upgrade, still desktop-only. |
| **PySide6 / Qt rewrite** | yes (excellent) | ❌ (mobile is painful) | high | Great desktop UI, but doesn't reach the phone. |
| **Flet (Flutter+Python)** | yes | ✅ desktop + web + mobile | med | One Python codebase to all targets; younger ecosystem; needs a server for web/mobile. |
| **Web app (API + PWA)** | yes (full control) | ✅ from any browser/phone | med–high | The standard answer for "on my phone + my website"; needs hosting + auth. |

### Recommendation

**Don't do a desktop-only rewrite (Qt/CustomTkinter).** It buys a nicer window but
not the phone — which is the bigger goal. Instead, invest in the **client/server
split** that unlocks the phone, the website, and notifications:

> **Target architecture: a small backend API over the existing `core/` logic, with
> a responsive web front-end (PWA) you can open on your phone.** Keep the desktop
> app working in the meantime.

If you want the *fastest* path to "it's on my phone" with the least new
technology, **Flet** is the pragmatic alternative — you keep writing Python, reuse
`core/`, and get desktop + web + mobile from one codebase, at the cost of a younger
framework. Both are good; the API+PWA path gives the most long-term control and the
cleanest fit with your own website.

## 7. Web + mobile + website integration (how the phone goal actually works)

To use this on your phone "while out and about," something has to be reachable over
the internet and access-controlled. The clean shape:

```
  Phone / laptop browser  ──HTTPS──>  Your server (your website's host)
        (PWA front-end)                 ├─ FastAPI/Flask app  ── core/ logic
                                        ├─ database (SQLite → Postgres)
                                        └─ auth + web-push
```

- **Backend:** wrap the existing `core/` functions in a small **FastAPI** service.
  It already has the hard parts (recurrence, filters, reminders) as pure functions.
- **Storage:** migrate the JSON file to **SQLite** (still a single file, easy
  backups) — or Postgres if it lives on the website host. The `model.py` schema
  maps directly to a `tasks` table.
- **Front-end:** a responsive **PWA** (installable, offline-capable, supports web
  push). Plain HTML/Svelte/React — your call; the API makes the choice independent.
- **Website integration:** host the app behind auth on a subdomain or path
  (e.g. `tasks.yoursite.com`) with its **own database**, isolated from the public
  site. The public GitHub repo stays code-only (data never committed — already
  enforced).

### Privacy & security (this is the gating concern, and you're right to flag it)
Your data includes health/medication and (soon) mood — treat it as sensitive:
- **Auth on everything.** Single-user is fine: a strong password + session tokens,
  or OAuth via an identity you already use. Never expose the API unauthenticated.
- **HTTPS only**, secrets in env vars (never in the repo), rate-limiting, and
  least-privilege DB access.
- **You host it.** A small VPS or your existing web host keeps the data under your
  control rather than a third-party task service.
- **Encrypt at rest** (disk/db encryption) and keep **off-site encrypted backups**.
- **Web push** needs a service worker + VAPID keys — keep the private key secret.

## 8. New features: mood tracking & notifications

These fit the self-care theme and the platform plan:

- **Mood tracking.** Add a `mood_entries` concept: timestamp, a small scale
  (1–5 or emoji), optional note, optional tags (sleep, energy, stress). Store
  alongside the journal/structured log. The payoff is **correlation** — mood vs.
  habit completion / training / sleep over time, surfaced as a simple chart. Same
  sensitivity/privacy as tasks.
- **Notifications.**
  - *Desktop (now):* the reminder system is currently passive (a ⏰ chip + a
    Reminders list). A real local toast on due/checkpoint would be a small add.
  - *Web/mobile (later):* web push from the PWA for due/checkpoint reminders, the
    daily mantra, and a daily **mood check-in** prompt.

## 9. Naming

"Tiny Tasklist" is clear but generic, and given it's really a *routine + task +
journal + mood* companion, a more evocative name may fit — e.g. something around
*routine / cadence / keystone / daily*. This is purely cosmetic: the window title is
already just "Tiny Tasklist" (the stray "(Modular)" dev label is gone); renaming the
Python package/repo later is a mechanical change. Worth deciding before the web
version gets a public URL.

## 10. Phased roadmap (preserving local-first)

1. **Phase 0 — Polish & harden (now).** Dark mode ✅, color fix ✅, tests ✅. Land the
   cheap UI wins; restyle priority to a left-bar; add a Today preset.
2. **Phase 1 — Solidify the core & schema.** Optionally migrate JSON → SQLite behind
   `model.py` (keep the desktop app working). Freeze a clean data schema.
3. **Phase 2 — Backend API.** FastAPI over `core/`, run locally first. Desktop app
   can keep using the local file; the API is additive.
4. **Phase 3 — Web/PWA front-end + hosting + auth.** The phone milestone. Web push
   notifications. Host behind auth on your domain.
5. **Phase 4 — Mood + insights.** Mood entries, correlation charts, mood check-in
   notifications.
6. **Phase 5 — Decide the desktop's fate.** Keep it as an offline client against the
   API, or retire it in favor of the PWA.

Each phase is independently useful and reversible; you never have to "big-bang"
rewrite.

## 11. Open decisions (for whenever you want to weigh in — no rush)
- **Platform:** API + PWA (recommended) vs. Flet (fastest to multi-platform).
- **Storage:** stay on JSON vs. move to SQLite (recommended before networking).
- **Hosting:** which host for the eventual web version (your existing website host?).
- **Name:** keep "Tiny Tasklist" or rebrand before it gets a public URL.
- **Priority model:** keep hazard escalation (currently unused) or replace with a
  simpler "snooze/overdue" emphasis.
