# Documentation index

Start with [`../CLAUDE.md`](../CLAUDE.md) for a one-page project profile (humans & AI).

| Doc | What it's for |
|---|---|
| [OVERVIEW → CLAUDE.md](../CLAUDE.md) | Fast map: what it is, how to run, layout, conventions, current state. |
| [USER_GUIDE.md](USER_GUIDE.md) | Every feature explained, for end users. |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Module map, data flow, the JSON schema, web server + concurrency model. |
| [FEATURES.md](FEATURES.md) | Feature inventory + desktop ↔ web parity matrix. |
| [DESIGN.md](DESIGN.md) | Design principles, UI direction, and the web/mobile + privacy plan. |
| [ROADMAP.md](ROADMAP.md) | Active plan and priorities (what's done, what's next). |
| [IDEAS.md](IDEAS.md) | Idea backlog (not commitments). |
| [BUGS.md](BUGS.md) | Open and recently-fixed defects. |
| [CHANGELOG.md](CHANGELOG.md) | Dated history of notable changes. |

## How these stay current (lightweight process)
- **Ship a change →** add a dated line to `CHANGELOG.md`; update `FEATURES.md` if a
  capability changed; if it fixed a defect, move the item to "Fixed" in `BUGS.md`.
- **Find a bug →** log it in `BUGS.md` (Open). **Have an idea →** drop it in `IDEAS.md`.
- **Pick up an idea →** move it to `ROADMAP.md`.
- Keep `CLAUDE.md` accurate when the layout, run commands, or conventions change.
