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
let LIVE = false;          // connected to the local API (webserver.py)
let editingId = null;      // task id being edited in the modal, or null for add
let _ctxMenu = null;
let _toastTimer = null;

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

/* ---------- date helpers ---------- */
function startOfToday() { const d = new Date(); d.setHours(0, 0, 0, 0); return d; }
function isoDate(d) { const p = (n) => String(n).padStart(2, "0"); return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`; }
function addDays(d, n) { const x = new Date(d); x.setDate(x.getDate() + n); return x; }
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

/* ---------- filtering (suspended-aware, mirrors the desktop) ---------- */
function activeTasks() { return tasks.filter((t) => !t.done && !t.suspended); }

function viewTasks() {
  let list;
  if (state.view === "done") {
    list = tasks.filter((t) => t.done && !t.suspended);
  } else if (state.view === "suspended") {
    list = tasks.filter((t) => t.suspended && !t.done);
  } else if (state.view === "habits") {
    list = tasks.filter((t) => t.repeat && t.repeat !== "none" && !t.suspended);
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
  { id: "suspended", icon: "⏸", label: "Suspended" },
];

function viewCount(id) {
  if (id === "today") return activeTasks().filter((t) => { const d = parseDue(t.due); return d && dayDiff(d) <= 0; }).length;
  if (id === "upcoming") return activeTasks().filter((t) => { const d = parseDue(t.due); return d && dayDiff(d) > 0; }).length;
  if (id === "habits") return tasks.filter((t) => t.repeat && t.repeat !== "none" && !t.suspended).length;
  if (id === "all") return activeTasks().length;
  if (id === "done") return tasks.filter((t) => t.done && !t.suspended).length;
  if (id === "suspended") return tasks.filter((t) => t.suspended && !t.done).length;
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
    el.innerHTML = `<span class="ico">#</span><span class="label">${escapeHtml(name)}</span><span class="count">${groups[name]}</span>`;
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
  el.className = "task" + (t.done ? " done" : "") + (t.suspended ? " suspended" : "");
  el.style.setProperty("--bar", `var(--p-${t.priority})`);

  const meta = [];
  if (t.group) meta.push(`<span class="chip group">${escapeHtml(t.group)}</span>`);
  if (chip) meta.push(`<span class="chip due${chip.overdue ? " overdue" : ""}">${chip.overdue ? "⚠ " : ""}${chip.text}</span>`);
  if (t.repeat && t.repeat !== "none") meta.push(`<span class="chip repeat">🔁 ${escapeHtml(t.repeat)}</span>`);
  if (t.times) meta.push(`<span class="chip">✓ ${t.times}×</span>`);

  el.innerHTML = `
    <div class="check" title="Toggle done">${t.done ? "✓" : ""}</div>
    <div class="body">
      <div class="title">${escapeHtml(t.title)}</div>
      ${t.notes ? `<div class="notes">${escapeHtml(t.notes)}</div>` : ""}
      <div class="meta">${meta.join("")}</div>
    </div>
    <button class="row-menu" title="Actions">⋯</button>
    <span class="prio-tag" style="background: var(--p-${t.priority})">${p.icon} ${p.label}</span>
  `;
  el.querySelector(".check").onclick = (e) => { e.stopPropagation(); toggleDone(t); };
  el.querySelector(".body").onclick = () => openModal(t);          // click to edit
  el.querySelector(".row-menu").onclick = (e) => { e.stopPropagation(); const r = e.target.getBoundingClientRect(); showContextMenu(r.left, r.bottom + 4, t); };
  el.oncontextmenu = (e) => { e.preventDefault(); showContextMenu(e.clientX, e.clientY, t); };  // right-click, like the desktop
  return el;
}

/* ---------- context menu (right-click / ⋯) ---------- */
function showContextMenu(x, y, t) {
  closeContextMenu();
  const m = document.createElement("div");
  m.className = "context-menu";
  const add = (label, fn, cls) => {
    const it = document.createElement("div");
    it.className = "item" + (cls ? " " + cls : "");
    it.textContent = label;
    it.onclick = () => { closeContextMenu(); fn(); };
    m.appendChild(it);
  };
  const sep = () => { const s = document.createElement("div"); s.className = "sep"; m.appendChild(s); };
  add("✎  Edit", () => openModal(t));
  add(t.done ? "↩  Mark not done" : "✓  Mark done", () => toggleDone(t));
  add(t.suspended ? "▶  Unsuspend" : "⏸  Suspend", () => setSuspended(t, !t.suspended));
  sep();
  add("🗑  Delete", () => deleteTask(t), "danger");
  document.body.appendChild(m);
  const r = m.getBoundingClientRect();
  m.style.left = Math.min(x, window.innerWidth - r.width - 8) + "px";
  m.style.top = Math.min(y, window.innerHeight - r.height - 8) + "px";
  _ctxMenu = m;
}
function closeContextMenu() { if (_ctxMenu) { _ctxMenu.remove(); _ctxMenu = null; } }

/* ---------- mutations ---------- */
async function toggleDone(t) {
  const snap = { ...t };
  if (LIVE) {
    try { Object.assign(t, await api("POST", `/api/tasks/${t.id}/toggle`)); }
    catch (e) { t.done = !t.done; }
  } else { t.done = !t.done; }
  render();
  showToast(snap.done ? "Marked not done" : "Marked done", "Undo", () => undoToggle(snap));
}
async function undoToggle(snap) {
  if (LIVE) {
    try {
      await api("PATCH", `/api/tasks/${snap.id}`, {
        due: snap.due, completed_at: snap.completed_at || "", times: snap.times, history: snap.history || [],
        is_suspended: !!snap.suspended,
      });
      await loadData();
    } catch (e) {}
  } else {
    const t = tasks.find((x) => x.id === snap.id);
    if (t) Object.assign(t, snap);
  }
  render();
}
async function setSuspended(t, val) {
  if (LIVE) {
    try { Object.assign(t, await api("PATCH", `/api/tasks/${t.id}`, { is_suspended: val })); } catch (e) {}
  } else { t.suspended = val; }
  render();
  showToast(val ? "Suspended" : "Unsuspended", "Undo", () => setSuspended(t, !val));
}
async function deleteTask(t) {
  const snap = { ...t };
  if (LIVE) { try { await api("DELETE", `/api/tasks/${t.id}`); } catch (e) {} }
  tasks = tasks.filter((x) => x.id !== t.id);
  render();
  showToast("Deleted", "Undo", async () => {
    if (LIVE) { try { await api("PATCH", `/api/tasks/${snap.id}`, { is_deleted: false }); await loadData(); } catch (e) {} }
    else { tasks.push(snap); }
    render();
  });
}

/* ---------- habit heatmap ---------- */
function heatmapData(days) {
  const cells = [];
  let seed = 7;
  const rand = () => { seed = (seed * 9301 + 49297) % 233280; return seed / 233280; };
  for (let i = days - 1; i >= 0; i--) {
    cells.push(i < 5 ? 3 : (rand() < 0.74 ? (1 + Math.floor(rand() * 3)) : 0));
  }
  let streak = 0;
  for (let i = cells.length - 1; i >= 0 && cells[i] > 0; i--) streak++;
  return { cells, streak };
}
function streakFromSet(set) {
  const today = startOfToday();
  let i = set.has(isoDate(today)) ? 0 : 1;
  let s = 0;
  for (; ; i++) { if (set.has(isoDate(addDays(today, -i)))) s++; else break; }
  return s;
}
function habitInfo() {
  const recurring = tasks.filter((t) => t.repeat && t.repeat !== "none" && Array.isArray(t.history) && t.history.length);
  if (!recurring.length) { const d = heatmapData(91); return { title: "Take vitamins", cells: d.cells, streak: d.streak }; }
  recurring.sort((a, b) => b.history.length - a.history.length);
  const t = recurring[0];
  const set = new Set(t.history.map((s) => String(s).slice(0, 10)));
  const today = startOfToday(), cells = [];
  for (let i = 90; i >= 0; i--) cells.push(set.has(isoDate(addDays(today, -i))) ? 3 : 0);
  return { title: t.title, cells, streak: streakFromSet(set) };
}
function bestStreak() {
  const withHist = tasks.filter((t) => Array.isArray(t.history) && t.history.length);
  if (!withHist.length) return heatmapData(91).streak;
  return Math.max(0, ...withHist.map((t) => streakFromSet(new Set(t.history.map((x) => String(x).slice(0, 10))))));
}

function renderHabits(content) {
  const { title, cells, streak } = habitInfo();
  const card = document.createElement("div");
  card.className = "card";
  card.innerHTML = `
    <h3>${escapeHtml(title)}</h3>
    <div class="muted">Top habit · last 13 weeks</div>
    <div style="display:flex;align-items:center;gap:28px;flex-wrap:wrap;margin-top:14px">
      <div><div class="streak-big">${streak} <span>day streak</span></div></div>
      <div class="heatmap">${cells.map((l) => `<div class="cell${l ? " l" + l : ""}"></div>`).join("")}</div>
    </div>`;
  content.appendChild(card);

  const heading = document.createElement("div");
  heading.className = "section-title";
  heading.textContent = "All recurring tasks";
  content.appendChild(heading);
  sortTasks(viewTasks()).forEach((t) => content.appendChild(taskRow(t)));
}

/* ---------- stats ---------- */
function renderStats(content) {
  const open = activeTasks().length;
  const todayIso = isoDate(startOfToday());
  const doneToday = tasks.filter((t) => (t.completed_at ? String(t.completed_at).slice(0, 10) === todayIso : t.done)).length;
  const week = activeTasks().filter((t) => { const d = parseDue(t.due); return d && dayDiff(d) >= 0 && dayDiff(d) <= 7; }).length;
  const cards = [
    { label: "Open", value: open },
    { label: "Done today", value: doneToday },
    { label: "Due this week", value: week },
    { label: "Best streak", value: `${bestStreak()} <small>days</small>` },
  ];
  const wrap = document.createElement("div");
  wrap.className = "stats";
  wrap.innerHTML = cards.map((c) => `<div class="stat"><div class="label">${c.label}</div><div class="value">${c.value}</div></div>`).join("");
  content.appendChild(wrap);
}

/* ---------- main render ---------- */
function render() {
  renderSidebar();
  const titleMap = { today: "Today", upcoming: "Upcoming", habits: "Habits", all: "All tasks", done: "Completed", suspended: "Suspended" };
  document.getElementById("viewTitle").textContent = state.group || titleMap[state.view];
  const niceDate = new Date().toLocaleDateString(undefined, { weekday: "long", month: "long", day: "numeric" });
  document.getElementById("viewSub").textContent = state.view === "today" && !state.group ? niceDate : "";

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

  // Completed view: most-recently-completed first.
  let list;
  if (state.view === "done") {
    list = viewTasks().sort((a, b) => String(b.completed_at || "").localeCompare(String(a.completed_at || "")));
  } else {
    list = sortTasks(viewTasks());
  }

  if (!list.length) {
    const msg = state.view === "today" ? "Nothing due today. Nice." : "Nothing here.";
    content.insertAdjacentHTML("beforeend", `<div class="empty"><div class="big">🎉</div><div>${msg}</div></div>`);
    return;
  }
  list.forEach((t) => content.appendChild(taskRow(t)));
}

/* ---------- toast ---------- */
function showToast(msg, actionLabel, actionFn) {
  let el = document.getElementById("toast");
  if (!el) { el = document.createElement("div"); el.id = "toast"; el.className = "toast"; document.body.appendChild(el); }
  el.innerHTML = "";
  const span = document.createElement("span"); span.textContent = msg; el.appendChild(span);
  if (actionLabel && actionFn) {
    const b = document.createElement("button"); b.textContent = actionLabel;
    b.onclick = () => { hideToast(); actionFn(); };
    el.appendChild(b);
  }
  el.classList.add("show");
  clearTimeout(_toastTimer);
  _toastTimer = setTimeout(hideToast, 5000);
}
function hideToast() { const el = document.getElementById("toast"); if (el) el.classList.remove("show"); }

/* ---------- modal (add + edit) ---------- */
function val(id) { return document.getElementById(id).value; }
function setVal(id, v) { document.getElementById(id).value = v; }

function openModal(task) {
  editingId = task ? task.id : null;
  document.getElementById("m_modalTitle").textContent = task ? "Edit task" : "Add a task";
  document.getElementById("m_save").textContent = task ? "Save" : "Add task";
  setVal("m_title", task ? task.title : "");
  setVal("m_due", task ? (task.due || "") : "");
  setVal("m_prio", task ? task.priority : "M");
  setVal("m_repeat", task ? (task.repeat || "none") : "none");
  setVal("m_group", task ? (task.group || "") : "");
  setVal("m_notes", task ? (task.notes || "") : "");
  document.getElementById("overlay").classList.add("open");
  document.getElementById("m_title").focus();
}
function closeModal() { document.getElementById("overlay").classList.remove("open"); }

async function saveModal() {
  const title = val("m_title").trim();
  if (!title) return;
  const payload = {
    title, due: val("m_due").trim(), priority: val("m_prio"),
    repeat: val("m_repeat"), group: val("m_group").trim(), notes: val("m_notes"),
  };
  if (editingId != null) {
    if (LIVE) {
      try {
        const u = await api("PATCH", `/api/tasks/${editingId}`, payload);
        const i = tasks.findIndex((t) => t.id === editingId);
        if (i >= 0) tasks[i] = u;
      } catch (e) {}
    } else {
      const t = tasks.find((x) => x.id === editingId);
      if (t) { t.title = title; t.due = parseQuickDue(payload.due); t.priority = payload.priority; t.repeat = payload.repeat; t.group = payload.group; t.notes = payload.notes; }
    }
  } else {
    if (LIVE) {
      try { tasks.push(await api("POST", "/api/tasks", payload)); } catch (e) {}
    } else {
      tasks.push({ id: nextId++, title, due: parseQuickDue(payload.due), priority: payload.priority, repeat: payload.repeat, group: payload.group, notes: payload.notes, done: false, times: 0 });
    }
  }
  closeModal();
  render();
}

/* ---------- misc helpers ---------- */
function escapeHtml(s) { return String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); }
function setTheme(mode, persist) {
  document.documentElement.setAttribute("data-theme", mode);
  document.getElementById("themeBtn").textContent = mode === "dark" ? "☀️" : "🌙";
  if (persist) { try { localStorage.setItem("tt_theme", mode); } catch (e) {} }
}
function currentTheme() { return document.documentElement.getAttribute("data-theme") || "light"; }
function closeSidebar() { document.getElementById("sidebar").classList.remove("open"); }
function parseQuickDue(s) {
  s = (s || "").trim().toLowerCase();
  if (!s) return "";
  if (s === "today") return isoDate(startOfToday());
  if (s === "tomorrow") return isoDate(addDays(startOfToday(), 1));
  const m = s.match(/^\+(\d+)d$/);
  if (m) return isoDate(addDays(startOfToday(), parseInt(m[1], 10)));
  if (/^\d{4}-\d{2}-\d{2}/.test(s)) return s;
  return isoDate(startOfToday());
}

/* ---------- init ---------- */
async function init() {
  setTheme(currentTheme(), false); // inline <head> script already chose saved/system
  document.getElementById("themeBtn").onclick = () => setTheme(currentTheme() === "dark" ? "light" : "dark", true);
  document.getElementById("search").oninput = (e) => { state.search = e.target.value; render(); };
  document.getElementById("menuBtn").onclick = () => document.getElementById("sidebar").classList.toggle("open");
  document.getElementById("addBtn").onclick = () => openModal(null);
  document.getElementById("m_cancel").onclick = closeModal;
  document.getElementById("m_save").onclick = saveModal;
  const overlay = document.getElementById("overlay");
  overlay.onclick = (e) => { if (e.target === overlay) closeModal(); };
  document.addEventListener("click", closeContextMenu);
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") { closeContextMenu(); closeModal(); } });
  await loadData();
  render();
}

document.addEventListener("DOMContentLoaded", init);
