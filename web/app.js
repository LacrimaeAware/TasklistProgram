/* Tiny Tasklist — web prototype logic (vanilla JS, no dependencies). */

const MS_DAY = 86400000;
const PRIO = {
  U: { label: "Ultra", icon: "🚨" },
  H: { label: "High", icon: "🔴" },
  M: { label: "Med", icon: "🟠" },
  L: { label: "Low", icon: "🟡" },
  D: { label: "Daily", icon: "🟢" },
  X: { label: "Misc", icon: "🔵" },
};
const PRIO_RANK = { U: 5, H: 4, M: 3, L: 2, D: 1, X: 0 };

let tasks = SAMPLE_TASKS.slice();
let state = { view: "today", group: null, search: "" };
let nextId = Math.max(...tasks.map((t) => t.id)) + 1;
let LIVE = false; // true when connected to the local API (webserver.py)

/* ---------- API ---------- */
async function api(method, url, body) {
  const opts = { method, headers: { "Content-Type": "application/json" } };
  if (body) opts.body = JSON.stringify(body);
  const r = await fetch(url, opts);
  if (!r.ok) throw new Error("api " + r.status);
  return r.json();
}
async function loadData() {
  try {
    const d = await api("GET", "/api/tasks");
    tasks = d.tasks;
    LIVE = true;
  } catch (e) {
    tasks = SAMPLE_TASKS.slice();
    LIVE = false;
  }
}
async function toggleDone(t) {
  if (LIVE) {
    try {
      const updated = await api("POST", `/api/tasks/${t.id}/toggle`);
      Object.assign(t, updated);
    } catch (e) { /* fall back to local */ t.done = !t.done; }
  } else {
    t.done = !t.done;
  }
  render();
}

/* ---------- date helpers ---------- */
function startOfToday() { const d = new Date(); d.setHours(0, 0, 0, 0); return d; }
function parseDue(s) {
  if (!s) return null;
  const [y, m, d] = s.slice(0, 10).split("-").map(Number);
  return new Date(y, m - 1, d);
}
function dayDiff(due) { return Math.round((due - startOfToday()) / MS_DAY); }
function dueChip(due) {
  if (!due) return null;
  const diff = dayDiff(due);
  if (diff < 0) return { text: "Overdue", overdue: true };
  if (diff === 0) return { text: "Today" };
  if (diff === 1) return { text: "Tomorrow" };
  if (diff < 7) return { text: due.toLocaleDateString(undefined, { weekday: "short" }) };
  return { text: due.toLocaleDateString(undefined, { month: "short", day: "numeric" }) };
}

/* ---------- filtering ---------- */
function activeTasks() { return tasks.filter((t) => !t.done); }

function viewTasks() {
  const today = startOfToday();
  let list;
  if (state.view === "done") {
    list = tasks.filter((t) => t.done);
  } else if (state.view === "habits") {
    list = tasks.filter((t) => t.repeat && t.repeat !== "none");
  } else if (state.view === "upcoming") {
    list = activeTasks().filter((t) => { const d = parseDue(t.due); return d && dayDiff(d) > 0; });
  } else if (state.view === "today") {
    list = activeTasks().filter((t) => { const d = parseDue(t.due); return d && dayDiff(d) <= 0; });
  } else {
    list = activeTasks(); // "all"
  }
  if (state.group) list = list.filter((t) => (t.group || "Ungrouped") === state.group);
  if (state.search) {
    const q = state.search.toLowerCase();
    list = list.filter((t) => t.title.toLowerCase().includes(q) || (t.notes || "").toLowerCase().includes(q));
  }
  return list;
}

function sortTasks(list) {
  return list.slice().sort((a, b) => {
    const da = parseDue(a.due), db = parseDue(b.due);
    const ta = da ? da.getTime() : Infinity, tb = db ? db.getTime() : Infinity;
    if (ta !== tb) return ta - tb;
    return (PRIO_RANK[b.priority] || 0) - (PRIO_RANK[a.priority] || 0);
  });
}

/* ---------- sidebar ---------- */
const VIEWS = [
  { id: "today", icon: "★", label: "Today" },
  { id: "upcoming", icon: "📅", label: "Upcoming" },
  { id: "habits", icon: "🔁", label: "Habits" },
  { id: "all", icon: "📋", label: "All tasks" },
  { id: "done", icon: "✓", label: "Completed" },
];

function viewCount(id) {
  const today = startOfToday();
  if (id === "today") return activeTasks().filter((t) => { const d = parseDue(t.due); return d && dayDiff(d) <= 0; }).length;
  if (id === "upcoming") return activeTasks().filter((t) => { const d = parseDue(t.due); return d && dayDiff(d) > 0; }).length;
  if (id === "habits") return tasks.filter((t) => t.repeat && t.repeat !== "none").length;
  if (id === "all") return activeTasks().length;
  if (id === "done") return tasks.filter((t) => t.done).length;
  return 0;
}

function renderSidebar() {
  const v = document.getElementById("views");
  v.innerHTML = "";
  VIEWS.forEach((view) => {
    const el = document.createElement("div");
    el.className = "nav-item" + (state.view === view.id && !state.group ? " active" : "");
    el.innerHTML = `<span class="ico">${view.icon}</span><span class="label">${view.label}</span><span class="count">${viewCount(view.id)}</span>`;
    el.onclick = () => { state.view = view.id; state.group = null; render(); closeSidebar(); };
    v.appendChild(el);
  });

  const groups = {};
  activeTasks().forEach((t) => { const g = t.group || "Ungrouped"; groups[g] = (groups[g] || 0) + 1; });
  const g = document.getElementById("groups");
  g.innerHTML = "";
  Object.keys(groups).sort().forEach((name) => {
    const el = document.createElement("div");
    el.className = "nav-item" + (state.group === name ? " active" : "");
    el.innerHTML = `<span class="ico">#</span><span class="label">${name}</span><span class="count">${groups[name]}</span>`;
    el.onclick = () => { state.group = name; state.view = "all"; render(); closeSidebar(); };
    g.appendChild(el);
  });
}

/* ---------- task rows ---------- */
function taskRow(t) {
  const due = parseDue(t.due);
  const chip = dueChip(due);
  const p = PRIO[t.priority] || PRIO.M;
  const el = document.createElement("div");
  el.className = "task" + (t.done ? " done" : "");
  el.style.setProperty("--bar", `var(--p-${t.priority})`);

  const meta = [];
  if (t.group) meta.push(`<span class="chip group">${t.group}</span>`);
  if (chip) meta.push(`<span class="chip due${chip.overdue ? " overdue" : ""}">${chip.overdue ? "⚠ " : ""}${chip.text}</span>`);
  if (t.repeat && t.repeat !== "none") meta.push(`<span class="chip repeat">🔁 ${t.repeat}</span>`);
  if (t.times) meta.push(`<span class="chip">✓ ${t.times}×</span>`);

  el.innerHTML = `
    <div class="check" title="Toggle done">${t.done ? "✓" : ""}</div>
    <div class="body">
      <div class="title">${escapeHtml(t.title)}</div>
      ${t.notes ? `<div class="notes">${escapeHtml(t.notes)}</div>` : ""}
      <div class="meta">${meta.join("")}</div>
    </div>
    <span class="prio-tag" style="background: var(--p-${t.priority})">${p.icon} ${p.label}</span>
  `;
  el.querySelector(".check").onclick = () => toggleDone(t);
  return el;
}

/* ---------- habit heatmap ---------- */
function heatmapData(days) {
  // Deterministic-ish pattern with a current streak, just for the demo.
  const cells = [];
  let seed = 7;
  const rand = () => { seed = (seed * 9301 + 49297) % 233280; return seed / 233280; };
  for (let i = days - 1; i >= 0; i--) {
    let level;
    if (i < 5) level = 3;                    // a clean current streak
    else level = rand() < 0.74 ? (1 + Math.floor(rand() * 3)) : 0;
    cells.push(level);
  }
  let streak = 0;
  for (let i = cells.length - 1; i >= 0 && cells[i] > 0; i--) streak++;
  return { cells, streak };
}

function renderHabits(content) {
  const { cells, streak } = heatmapData(91);
  const card = document.createElement("div");
  card.className = "card";
  card.innerHTML = `
    <h3>Take vitamins</h3>
    <div class="muted">Daily habit · last 13 weeks</div>
    <div style="display:flex;align-items:center;gap:28px;flex-wrap:wrap;margin-top:14px">
      <div><div class="streak-big">${streak} <span>day streak</span></div></div>
      <div class="heatmap">${cells.map((l) => `<div class="cell${l ? " l" + l : ""}"></div>`).join("")}</div>
    </div>`;
  content.appendChild(card);

  const title = document.createElement("div");
  title.className = "section-title";
  title.textContent = "All recurring tasks";
  content.appendChild(title);
  sortTasks(viewTasks()).forEach((t) => content.appendChild(taskRow(t)));
}

/* ---------- stats ---------- */
function renderStats(content) {
  const open = activeTasks().length;
  const doneToday = tasks.filter((t) => t.done).length;
  const week = activeTasks().filter((t) => { const d = parseDue(t.due); return d && dayDiff(d) >= 0 && dayDiff(d) <= 7; }).length;
  const { streak } = heatmapData(91);
  const cards = [
    { label: "Open", value: open },
    { label: "Done today", value: doneToday },
    { label: "Due this week", value: week },
    { label: "Best streak", value: `${streak} <small>days</small>` },
  ];
  const wrap = document.createElement("div");
  wrap.className = "stats";
  wrap.innerHTML = cards.map((c) => `<div class="stat"><div class="label">${c.label}</div><div class="value">${c.value}</div></div>`).join("");
  content.appendChild(wrap);
}

/* ---------- main render ---------- */
function render() {
  renderSidebar();
  const titleMap = { today: "Today", upcoming: "Upcoming", habits: "Habits", all: "All tasks", done: "Completed" };
  document.getElementById("viewTitle").textContent = state.group || titleMap[state.view];
  const niceDate = new Date().toLocaleDateString(undefined, { weekday: "long", month: "long", day: "numeric" });
  document.getElementById("viewSub").textContent = state.view === "today" ? niceDate : "";

  const content = document.getElementById("content");
  content.innerHTML = "";

  if (state.view === "today" && !state.group) {
    const banner = LIVE
      ? `<div class="banner">🟢 Connected to your local data (via the Tiny Tasklist web server).</div>`
      : `<div class="banner">✨ Static prototype with sample data — run <code>python -m tasklistprogram.webserver</code> to connect your real tasks.</div>`;
    content.insertAdjacentHTML("beforeend", banner);
    renderStats(content);
  }

  if (state.view === "habits" && !state.group) { renderHabits(content); return; }

  const list = sortTasks(viewTasks());
  if (!list.length) {
    content.insertAdjacentHTML("beforeend",
      `<div class="empty"><div class="big">🎉</div><div>Nothing here. Enjoy the moment.</div></div>`);
    return;
  }
  list.forEach((t) => content.appendChild(taskRow(t)));
}

/* ---------- interactions ---------- */
function escapeHtml(s) { return s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); }

function setTheme(mode) {
  document.documentElement.setAttribute("data-theme", mode);
  document.getElementById("themeBtn").textContent = mode === "dark" ? "☀️" : "🌙";
  try { localStorage.setItem("tt_theme", mode); } catch (e) {}
}
function closeSidebar() { document.getElementById("sidebar").classList.remove("open"); }

function parseQuickDue(s) {
  s = (s || "").trim().toLowerCase();
  if (!s) return "";
  if (s === "today") return _due(0);
  if (s === "tomorrow") return _due(1);
  const m = s.match(/^\+(\d+)d$/);
  if (m) return _due(parseInt(m[1], 10));
  if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return s;
  return _due(0);
}

function setupModal() {
  const overlay = document.getElementById("overlay");
  const open = () => { overlay.classList.add("open"); document.getElementById("m_title").focus(); };
  const close = () => overlay.classList.remove("open");
  document.getElementById("addBtn").onclick = open;
  document.getElementById("m_cancel").onclick = close;
  overlay.onclick = (e) => { if (e.target === overlay) close(); };
  document.getElementById("m_save").onclick = async () => {
    const title = document.getElementById("m_title").value.trim();
    if (!title) return;
    const payload = {
      title,
      due: document.getElementById("m_due").value.trim(),
      priority: document.getElementById("m_prio").value,
      repeat: document.getElementById("m_repeat").value,
      group: document.getElementById("m_group").value.trim(),
    };
    if (LIVE) {
      try {
        const created = await api("POST", "/api/tasks", payload);
        tasks.push(created);
      } catch (e) { /* ignore */ }
    } else {
      tasks.push({
        id: nextId++, title,
        due: parseQuickDue(payload.due),
        priority: payload.priority, repeat: payload.repeat, group: payload.group,
        notes: "", done: false, times: 0,
      });
    }
    document.getElementById("m_title").value = "";
    document.getElementById("m_due").value = "";
    document.getElementById("m_group").value = "";
    close();
    render();
  };
}

async function init() {
  let saved = "light";
  try { saved = localStorage.getItem("tt_theme") || "light"; } catch (e) {}
  setTheme(saved);
  document.getElementById("themeBtn").onclick = () =>
    setTheme(document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark");
  document.getElementById("search").oninput = (e) => { state.search = e.target.value; render(); };
  document.getElementById("menuBtn").onclick = () => document.getElementById("sidebar").classList.toggle("open");
  setupModal();
  await loadData();
  render();
}

document.addEventListener("DOMContentLoaded", init);
