# Web UI Prototype

A **static, dependency-free preview** of the planned web version of Tiny Tasklist —
the "professional, website-style" direction discussed in
[../docs/DESIGN.md](../docs/DESIGN.md).

## What it is
- Pure HTML/CSS/JS. No build step, no dependencies.
- In **sample mode** uses `sample-data.js`; in **live mode** (served by the local
  server) it reads/writes your real tasks.
- Sidebar navigation (Today / Upcoming / Habits / All / Completed / Suspended +
  groups), stat cards, a calm task list with priority left-bars and chips, a habit
  **streak heatmap**, light/dark themes (follows your OS, remembered), search, and a
  responsive layout that collapses on mobile.

## Interacting with tasks
- **Add:** the "+ Add task" button.
- **Edit:** click a task row, or **right-click** it (or the ⋯ button) for a menu
  with Edit / Mark done / Suspend / Delete.
- **Complete:** click the circle. A toast appears with **Undo** (works even for
  recurring tasks, which advance their date when completed).
- **Suspended** tasks are hidden from the active views and live under the Suspended
  view — matching the desktop app.

## Two ways to run it

**1) Static preview (sample data).** Just open `index.html` in any browser, or:
```bash
cd web && python -m http.server 8000   # http://localhost:8000
```

**2) Live mode — connected to your real tasks.** Run the bundled local server
(standard library only, no install), which serves this UI *and* a JSON API backed
by your actual `data/tasks_gui.json`:
```bash
python -m tasklistprogram.webserver        # http://localhost:8000
```
Or just **double-click `run_web.bat`** in the project root — it starts the server
windowless and opens the browser for you.
When the page loads from this server it auto-detects the API and switches to live
data — you can add tasks and check them off, and changes persist to the same file
the desktop app uses. The banner at the top tells you which mode you're in.

To see it on your **phone** (same Wi-Fi), run either server and visit
`http://<your-computer-ip>:8000`. (The live server currently binds to localhost and
has **no auth** — fine for your own machine; do not expose it to the internet until
the auth/hosting phase in [../docs/DESIGN.md](../docs/DESIGN.md).)

> Tip: point the data anywhere with the `TINYTASKLIST_DATA_DIR` environment
> variable (both the desktop app and the web server honor it).

## What it is NOT (yet)
The live server has **no authentication** and isn't hardened for public exposure.
The hosted version (see DESIGN.md, Phases 3–4) adds a database, auth, HTTPS, and web
push so it's reachable — privately — from anywhere.

## Files
- `index.html` — layout
- `styles.css` — the design system (colors as CSS variables → easy theming)
- `app.js` — rendering + interactions
- `sample-data.js` — generic demo tasks
- `assets/icon.png` — app icon (shared with the desktop app)
