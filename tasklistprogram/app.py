import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import re
from typing import Optional, Tuple, List
from datetime import datetime, date, timedelta

from .core.dates import parse_due_flexible, fmt_due_for_store, parse_stored_due, next_due
from .core.model import load_db, save_db, get_task, delete_task, stats_summary
from .ui.dialogs import (
    EditDialog,
    StatsDialog,
    SettingsDialog,
    RemindersDialog,
    PasteImportDialog,
    HelpDialog,
)
from .core.io_import import import_from_string

from .core.actions import ActionsMixin

from .ui.listview import TaskListView
from .ui.controls import AutoCompleteEntry
from .core.constants import PRIORITY_ORDER, PRIO_ICON

class TaskApp(ActionsMixin, tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Tiny Tasklist (Modular)")
        self.geometry("1120x660")
        self.db = load_db()

        # Keeps expanded/collapsed state by group name (harmless to keep)
        self.group_state = {}  # {group_name: True/False}

        # Menu bar
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Settings...", command=self.open_settings)
        file_menu.add_command(label="Reminders…", command=self.open_reminders)
        file_menu.add_command(label="Import Tasks…", command=self.import_tasks)
        file_menu.add_command(label="Import (paste text)…", command=self.import_tasks_paste)
        menubar.add_cascade(label="File", menu=file_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Help / Guide…", command=self.open_help)
        menubar.add_cascade(label="Help", menu=help_menu)
        self.config(menu=menubar)

        self.sort_state: Tuple[str, bool] = ("due", True)  # (column, ascending)

        # Top controls
        top = ttk.Frame(self, padding=8)
        top.pack(fill=tk.X)

        ttk.Label(top, text="Title:").pack(side=tk.LEFT)
        self.title_var = tk.StringVar()
        title_entry = AutoCompleteEntry(top, self._title_candidates, textvariable=self.title_var, width=34)
        title_entry.pack(side=tk.LEFT, padx=4)

        ttk.Label(top, text="Due:").pack(side=tk.LEFT, padx=(8,0))
        self.due_var = tk.StringVar()
        due_entry = ttk.Entry(top, textvariable=self.due_var, width=22)
        due_entry.pack(side=tk.LEFT, padx=4)

        ttk.Label(top, text="Priority:").pack(side=tk.LEFT, padx=(8,0))
        self.priority_var = tk.StringVar(value="M")
        prio_combo = ttk.Combobox(top, textvariable=self.priority_var, width=6,
                                  values=["H","M","L","D","Misc"], state="readonly")
        prio_combo.pack(side=tk.LEFT, padx=4)
        prio_combo.bind("<<ComboboxSelected>>", self._maybe_autoset_repeat)

        ttk.Label(top, text="Repeat:").pack(side=tk.LEFT, padx=(8,0))
        self.repeat_var = tk.StringVar(value="none")
        repeat_combo = ttk.Combobox(top, textvariable=self.repeat_var, width=10,
                                    values=["none","daily","weekdays","weekly","monthly"], state="readonly")
        repeat_combo.pack(side=tk.LEFT, padx=4)

        self.notes_txt = tk.Text(top, width=32, height=2, wrap="word")
        self.notes_txt.pack(side=tk.LEFT, padx=(8, 4))
        self.notes_txt.bind("<Return>", lambda e: (self.add_task(), "break"))
        self.notes_txt.bind("<Shift-Return>", lambda e: None)

        ttk.Button(top, text="Add", command=self.add_task).pack(side=tk.LEFT)
        ttk.Button(top, text="Stats", command=self.open_stats).pack(side=tk.LEFT, padx=(8,0))

        # Keyboard flow
        title_entry.bind("<Shift-Return>", self.quick_add_default)

        # Filter/Search row
        filt = ttk.Frame(self, padding=(8,0,8,8))
        filt.pack(fill=tk.X)
        ttk.Label(filt, text="Filter:").pack(side=tk.LEFT)
        settings = self.db.get("settings", {})
        default_filter = settings.get("ui_filter_scope", "all")
        if default_filter not in ["today", "week", "overdue", "habits", "all", "done", "deleted"]:
            default_filter = "all"
        self.filter_var = tk.StringVar(value=default_filter)
        fcombo = ttk.Combobox(filt, textvariable=self.filter_var, width=10,
                              values=["today","week","overdue","habits","all","done","deleted"],
                              state="readonly")
        fcombo.pack(side=tk.LEFT, padx=6)

        def _apply_filter(*_):
            s = self.db.setdefault("settings", {})
            s["ui_filter_scope"] = self.filter_var.get()
            save_db(self.db)
            self.refresh()

        fcombo.bind("<<ComboboxSelected>>", _apply_filter)

        ttk.Label(filt, text="Search:").pack(side=tk.LEFT, padx=(16,0))
        self.search_var = tk.StringVar()
        s_entry = ttk.Entry(filt, textvariable=self.search_var, width=34)
        s_entry.pack(side=tk.LEFT, padx=6)
        self.search_var.trace_add("write", lambda *args: self.refresh())

        ttk.Label(filt, text="Min prio:").pack(side=tk.LEFT, padx=(16, 0))
        self.minprio_ui = tk.StringVar(value=self.db.get("settings", {}).get("min_priority_visible", "L"))
        mincombo = ttk.Combobox(filt, textvariable=self.minprio_ui, width=8,
                                values=["H", "M", "L", "D", "Misc"], state="readonly")
        mincombo.pack(side=tk.LEFT, padx=6)
        def _apply_minprio(*_):
            s = self.db.setdefault("settings", {})
            s["min_priority_visible"] = self.minprio_ui.get()
            save_db(self.db)
            self.refresh()
        mincombo.bind("<<ComboboxSelected>>", _apply_minprio)

        # Grouping toggle
        self.group_view = tk.BooleanVar(value=bool(settings.get("ui_group_view", False)))

        def _apply_group_view():
            s = self.db.setdefault("settings", {})
            s["ui_group_view"] = bool(self.group_view.get())
            save_db(self.db)
            self.refresh()

        ttk.Checkbutton(filt, text="Group view", variable=self.group_view, command=_apply_group_view) \
            .pack(side=tk.LEFT, padx=(16, 0))

        # --- style: make the caret button flat and remove focus ring
        style = ttk.Style(self)
        style.configure("Caret.TButton", padding=(4, 1), relief="flat")
        style.map("Caret.TButton",
                  relief=[("pressed", "sunken"), ("!pressed", "flat")],
                  focuscolor=[("!disabled", self.cget("background"))],
                  highlightthickness=[("!disabled", 0)],
                  borderwidth=[("!disabled", 0)])

        # Single caret toggle: ▼ = default expanded, ▶ = default collapsed
        self.group_toggle_var = tk.StringVar(value="▼")
        ttk.Button(
            filt,
            textvariable=self.group_toggle_var,
            width=2,
            command=self._toggle_all_groups,
            style="Caret.TButton"  # <— add this
        ).pack(side=tk.LEFT, padx=(6, 10))

        ttk.Button(filt, text="Mark Done", command=self.mark_done).pack(side=tk.LEFT, padx=(16, 4))
        ttk.Button(filt, text="Delete", command=self.soft_delete).pack(side=tk.LEFT, padx=4)
        ttk.Button(filt, text="Restore", command=self.restore).pack(side=tk.LEFT, padx=4)

        # === Treeview moved to TaskListView ===
        self.list = TaskListView(self, on_request_edit=self.edit_task, request_refresh=self.refresh)

        # Keep header sort behavior in app.py so sort state stays consistent
        def _header_sort(col):
            self.sort_by(col)
        for c in ("id","due","rem","prio","rep","title","notes","times"):
            header_text = self.list.tree.heading(c, "text")
            self.list.tree.heading(c, text=header_text, command=lambda col=c: _header_sort(col))

        # Right-click context menu
        self.menu = tk.Menu(self, tearoff=0)
        self.menu.add_command(label="Edit", command=self.edit_task)
        self.menu.add_command(label="Delete (soft)", command=self.soft_delete)
        self.menu.add_command(label="Restore", command=self.restore)
        self.menu.add_command(label="Hard Delete…", command=self.hard_delete)

        setp = tk.Menu(self.menu, tearoff=0)
        setp.add_command(label="High",   command=lambda: self.set_priority_bulk("H"))
        setp.add_command(label="Medium", command=lambda: self.set_priority_bulk("M"))
        setp.add_command(label="Low",    command=lambda: self.set_priority_bulk("L"))
        setp.add_command(label="Daily",  command=lambda: self.set_priority_bulk("D"))
        setp.add_command(label="Misc",   command=lambda: self.set_priority_bulk("X"))
        self.menu.add_cascade(label="Set Priority", menu=setp)

        setr = tk.Menu(self.menu, tearoff=0)
        for rlab, rval in [("none","none"),("daily","daily"),("weekdays","weekdays"),("weekly","weekly"),("monthly","monthly")]:
            setr.add_command(label=rlab, command=lambda v=rval: self.set_repeat_bulk(v))
        self.menu.add_cascade(label="Set Repeat", menu=setr)

        self.menu.add_command(label="Set Due…", command=self.set_due_bulk)

        # NEW: bulk set/clear group (assumes you have set_group_bulk implemented)
        self.menu.add_command(label="Set Group…", command=self.set_group_bulk)
        self.menu.add_command(label="Clear Group", command=lambda: self.set_group_bulk(clear=True))

        # Attach context menu to the new tree
        self.list.tree.bind("<Button-3>", self.popup_menu)

        # Initial refresh & schedule resets
        self.refresh()
        self.after(300, self.check_reminders)
        self.reset_repeating_tasks(catchup=True)
        self.schedule_midnight_reset()

        # Keyboard shortcuts
        self.bind("<Delete>", lambda e: self.soft_delete())
        self.bind("<Control-Return>", lambda e: self.mark_done())
    # ===== Repeat resets =====
    def schedule_midnight_reset(self):
        now = datetime.now()
        tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=5, microsecond=0)
        delay_ms = max(1000, int((tomorrow - now).total_seconds() * 1000))
        self.after(delay_ms, lambda: self.reset_repeating_tasks(catchup=False))

    def reset_repeating_tasks(self, catchup: bool):
        """
        Midnight-only reset: advance repeating tasks when the *next theoretical occurrence date*
        is <= today (i.e. at midnight of the next occurrence). No user setting; always midnight behavior.
        """
        today = date.today()
        changed = False

        for t in self.db["tasks"]:
            rep = t.get("repeat", "none")
            if rep in ("", "none", None):
                continue

            stored = t.get("due", "")
            due_dt = parse_stored_due(stored)
            # If no stored due, assume today at midnight (safe default)
            if not due_dt:
                due_dt = datetime.combine(today, datetime.min.time())
                stored = due_dt.strftime("%Y-%m-%d")

            had_time = isinstance(stored, str) and len(stored) > 10
            original_time = due_dt.time()

            # Advance along the schedule while the *next* occurrence date is already <= today
            while True:
                next_day = next_due(due_dt.date(), rep)  # date of next theoretical occurrence
                if next_day > today:
                    break
                # advance stored due to the next occurrence (preserve time/no-time)
                if had_time:
                    due_dt = datetime.combine(next_day, original_time)
                else:
                    due_dt = datetime.combine(next_day, datetime.min.time())
                changed = True
                # loop to catch up multiple missed occurrences

            # If task was completed previously and the (possibly-updated) due is today,
            # clear completed_at so it reappears as active on its due day.
            if t.get("completed_at") and due_dt.date() == today:
                t["completed_at"] = ""
                changed = True

            # write back preserving the original had_time vs date-only
            if had_time:
                t["due"] = due_dt.strftime("%Y-%m-%d %H:%M")
            else:
                t["due"] = due_dt.strftime("%Y-%m-%d")

        if changed:
            save_db(self.db)
            self.refresh()

        # schedule next midnight-run (unchanged semantics)
        if not catchup:
            self.schedule_midnight_reset()

    # ===== Helpers =====
    def _toggle_all_groups(self):
        # Toggle global default expansion in the list view and refresh.
        if self.list.is_default_expanded():
            self.list.collapse_all()
            self.group_toggle_var.set("▶")
        else:
            self.list.expand_all()
            self.group_toggle_var.set("▼")
        self.refresh()

    def _maybe_autoset_repeat(self, event=None):
        raw = self.priority_var.get()
        if raw.lower() == 'misc':
            return
        if str(raw).upper() == "D":
            self.repeat_var.set("daily")

    def _priority_visible(self, p: str) -> bool:
        s = self.db.get('settings', {})
        minv = s.get('min_priority_visible', 'L')
        minv_code = 'X' if isinstance(minv, str) and minv.lower() == 'misc' else (minv or 'L').upper()
        return PRIORITY_ORDER.get((p or 'M').upper(), 0) >= PRIORITY_ORDER.get(minv_code, 2)

    def _title_candidates(self):
        items = [(t.get("title",""), t.get("times_completed",0)) for t in self.db["tasks"] if t.get("title")]
        items.sort(key=lambda x: (-x[1], x[0].lower()))
        seen, out = set(), []
        for title, _ in items:
            if title not in seen:
                seen.add(title); out.append(title)
        return out

    def selected_tasks(self) -> List[dict]:
        ids = self.list.selected_task_ids()
        return [get_task(self.db, tid) for tid in ids if get_task(self.db, tid)]

    def popup_menu(self, event):
        tree = self.list.tree
        iid = tree.identify_row(event.y)
        kind = self.list.identify_row_kind(iid)

        if not iid or kind != "task":
            return  # only allow popup on real task rows

        # If the clicked row isn't already in the selection, select JUST that row.
        # If it IS already selected, keep the existing multi-selection intact.
        current = set(tree.selection())
        if iid not in current:
            tree.selection_set(iid)

        self.menu.tk_popup(event.x_root, event.y_root)

    # ===== Add & Quick Add =====
    def add_task(self):
        title = self.title_var.get().strip()
        if not title: return
        due_s = self.due_var.get().strip()
        parsed = None
        if due_s:
            ts = due_s.strip()
            m_colon = re.match(r'^(\d{1,2}):(\d{2})$', ts)
            m_plain = re.match(r'^(\d{3,4})$', ts)
            if m_colon or m_plain:
                if m_colon:
                    hh, mm = int(m_colon.group(1)), int(m_colon.group(2))
                else:
                    raw = m_plain.group(1)
                    if len(raw) == 3: raw = '0' + raw
                    hh, mm = int(raw[:2]), int(raw[2:])
                parsed = datetime.now().replace(hour=hh, minute=mm, second=0, microsecond=0)
            else:
                parsed = parse_due_flexible(due_s)
        if due_s and parsed is None:
            messagebox.showerror("Date error",
                "Due must be 'YYYY-MM-DD [HH:MM]', 'MM/DD [HH:MM]', 'HH:MM', 'HHMM', or relative like '+2d +5h' (use 'midnight' for 23:59).")
            return
        rawp = self.priority_var.get()
        prio = ("X" if str(rawp).lower()=="misc" else str(rawp).upper())
        rep = self.repeat_var.get()
        notes = self.notes_txt.get("1.0", "end-1c").strip()
        if prio == "D": rep = "daily"
        t = {
            "id": self.db["next_id"],
            "title": title,
            "notes": notes,
            "priority": prio if prio in ("H","M","L","D","X") else "M",
            "due": fmt_due_for_store(parsed) if due_s else "",
            "repeat": rep,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "completed_at": "",
            "times_completed": 0,
            "history": [],
            "is_deleted": False,
            "group": ""  # group set via Edit or bulk action
        }
        self.db["tasks"].append(t)
        self.db["next_id"] += 1
        save_db(self.db)
        self.title_var.set(""); self.due_var.set(""); self.notes_txt.delete("1.0", "end")
        self.refresh(select_id=t["id"])

    def quick_add_default(self, event=None):
        title = self.title_var.get().strip()
        if not title: return "break"
        tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        t = {
            "id": self.db["next_id"],
            "title": title,
            "notes": "",
            "priority": "M",
            "due": tomorrow,
            "repeat": "none",
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "completed_at": "",
            "times_completed": 0,
            "history": [],
            "is_deleted": False,
            "group": ""
        }
        self.db["tasks"].append(t); self.db["next_id"] += 1
        save_db(self.db)
        self.title_var.set("")
        self.refresh(select_id=t["id"])
        return "break"

    # ===== Edit / Done / Delete / Restore =====
    def edit_task(self):
        sels = self.selected_tasks()
        if not sels: return
        if len(sels) > 1:
            messagebox.showinfo("Edit", "Please select a single task to edit.")
            return
        t = sels[0]
        def on_save(data):
            t["title"] = data["title"]
            t["due"] = data["due"]
            t["priority"] = ("X" if str(data["priority"]).lower()=="misc" else data["priority"])
            t["repeat"] = data["repeat"]
            t["notes"] = data["notes"]
            t["group"] = data.get("group","").strip()
            t["updated_at"] = datetime.now().isoformat(timespec="seconds")
            save_db(self.db)
            self.refresh(select_id=t["id"])
        EditDialog(self, t, on_save)

    def edit_task_for_iid(self, iid: str):
        vals = self.tree.item(iid)["values"]
        if not vals: return
        try:
            tid = int(vals[0])
        except Exception:
            return
        t = get_task(self.db, tid)
        if not t: return
        def on_save(data):
            t["title"] = data["title"]
            t["due"] = data["due"]
            t["priority"] = ("X" if str(data["priority"]).lower()=="misc" else data["priority"])
            t["repeat"] = data["repeat"]
            t["notes"] = data["notes"]
            t["group"] = data.get("group","").strip()
            t["updated_at"] = datetime.now().isoformat(timespec="seconds")
            save_db(self.db)
            self.refresh(select_id=t["id"])
        EditDialog(self, t, on_save)

    def on_tree_double_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region not in ("cell", "tree"):
            return
        iid = self.tree.identify_row(event.y)
        if not iid:
            return
        tags = self.tree.item(iid, "tags")
        if "group_header" in tags:
            vals = self.tree.item(iid)["values"]
            # group name is stored in TITLE column (index 5)
            if len(vals) >= 6:
                gname = str(vals[5])
                self.group_state[gname] = not self.group_state.get(gname, True)
                self.refresh()
            return
        self.edit_task_for_iid(iid)

    # ===== Filter/Search/Sort/Refresh =====
    def passes_filter(self, t, scope):
        if scope == "deleted":
            return t.get("is_deleted", False)
        if t.get("is_deleted", False):
            return False

        done = bool(t.get("completed_at"))
        if done and scope != "done":
            return False
        if not self._priority_visible(t.get("priority", "M")):
            return False

        d = parse_stored_due(t.get("due", "")) if t.get("due") else None
        now = datetime.now()

        if scope == "done":
            return done
        if scope == "all":
            return True
        if scope == "habits":
            return t.get("repeat") in ("daily", "weekdays", "weekly", "monthly")
        if scope == "overdue":
            return (d and d < now) and not done
        if scope == "week":
            if d is None:
                return False
            return d <= (now + timedelta(days=7))
        if scope == "today":
            if not d:
                return False
            if d.date() == date.today():
                return True
            if d < now and not done:
                return True
            return False
        return True

    def search_match(self, t, q: str) -> bool:
        if not q: return True
        ql = q.lower()
        return (ql in t.get("title","").lower()) or (ql in t.get("notes","").lower())

    def sort_by(self, col: str):
        current_col, ascending = self.sort_state
        ascending = not ascending if current_col == col else True
        self.sort_state = (col, ascending)
        self.refresh()

    def sort_key_for(self, t, col: str):
        if col == "id": return t["id"]
        if col == "due":
            d = parse_stored_due(t.get("due","")) if t.get("due") else datetime.max
            return d
        if col == "prio": return PRIORITY_ORDER.get(t.get("priority","M").upper(), 99)
        if col == "rep": return t.get("repeat","")
        if col == "title": return t.get("title","").lower()
        if col == "notes": return t.get("notes","").lower()
        if col == "times": return t.get("times_completed",0)
        return 0

    def refresh(self, select_id: Optional[int] = None):
        scope = self.filter_var.get()
        query = self.search_var.get().strip()
        col, asc = self.sort_state

        tasks = [t for t in self.db["tasks"] if self.passes_filter(t, scope) and self.search_match(t, query)]
        tasks.sort(key=lambda x: self.sort_key_for(x, col), reverse=not asc)

        grouped = bool(self.group_view.get())

        self.list.render(
            tasks,
            scope=scope,
            prio_icon=PRIO_ICON,
            reminder_chip_fn=self._reminder_chip,
            grouped=grouped,
        )

        if select_id is not None:
            id_idx = self.list.COLS.index("id")
            for iid in self.list.tree.get_children():
                vals = self.list.tree.item(iid)["values"]
                if not vals or len(vals) <= id_idx:
                    continue
                try:
                    row_id = int(vals[id_idx])
                except Exception:
                    continue
                if str(row_id) == str(select_id):
                    self.list.tree.selection_set(iid)
                    self.list.tree.see(iid)
                    break

    # ===== Stats / Settings / Reminders =====
    def open_help(self, initial_tab: str = "tutorial"):
        HelpDialog(self, initial_tab=initial_tab)

    def import_tasks_paste(self):
        def _do(text):
            added, failed = import_from_string(text, self.db)
            if added:
                save_db(self.db)
                self.refresh()
            return added, failed

        PasteImportDialog(self, on_import_text=_do)

    def open_stats(self):
        summary = stats_summary(self.db)
        StatsDialog(self, summary)

    def import_tasks(self):
        from .core.io_import import import_from_txt
        path = filedialog.askopenfilename(title="Import tasks",
                                          filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if not path: return
        try:
            added, failed = import_from_txt(path, self.db)
            save_db(self.db)
            self.refresh()
            if failed:
                messagebox.showwarning("Import",
                                       f"Imported {added} task(s). Skipped {failed} line(s) with invalid format.")
            else:
                messagebox.showinfo("Import", f"Imported {added} task(s).")
        except Exception as e:
            messagebox.showerror("Import failed", str(e))

    def open_settings(self):
        def on_save(s):
            merged = dict(self.db.get("settings", {}))
            merged.update(s)
            self.db["settings"] = merged
            save_db(self.db)
        SettingsDialog(self, self.db.get("settings", None), on_save)

    def open_reminders(self):
        from .core.reminders import pending_reminders
        pending = pending_reminders(self.db)
        if not pending:
            messagebox.showinfo("Reminders", "No pending reminders right now.")
            return

        def on_ack(pairs):
            for tid, key in pairs:
                task = next((x for x in self.db["tasks"] if x["id"] == tid), None)
                if task:
                    acks = set(task.get("acknowledged_checkpoints", []))
                    acks.add(key)
                    task["acknowledged_checkpoints"] = sorted(acks)
            save_db(self.db)

        RemindersDialog(self, pending, on_ack)

    def _reminder_chip(self, t) -> str:
        from .core.reminders import reminder_chip
        return reminder_chip(t, self.db.get("settings", {}))

    def check_reminders(self):
        return

def main():
    app = TaskApp()
    app.mainloop()

if __name__ == "__main__":
    main()
