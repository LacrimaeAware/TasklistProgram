import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import re
from typing import Optional, Tuple, List
from datetime import datetime, date, timedelta

from .core.dates import parse_due_flexible, fmt_due_for_store, parse_stored_due, next_due
from .core.model import load_db, save_db, get_task, delete_task, stats_summary, normalize_settings
from .ui.dialogs import (
    EditDialog,
    StatsDialog,
    SettingsDialog,
    RemindersDialog,
    PasteImportDialog,
    HelpDialog,
    MantraDialog,
    JournalDialog,
)
from .core.io_import import import_from_string
from .core.documents import (
    sync_task_notes,
    move_task_document_if_needed,
    open_document,
    append_journal_task,
    append_journal_manual,
    ensure_journal_path,
    open_directory,
    get_mantras_file_path,
    read_task_notes_from_file,
    task_doc_path,
    load_mantras_from_file,
    DATA_DIR,
)

from .core.actions import ActionsMixin

from .ui.listview import TaskListView
from .ui.controls import AutoCompleteEntry
from .core.constants import PRIORITY_ORDER, PRIO_ICON

class TaskApp(ActionsMixin, tk.Tk):
    REPEAT_OPTIONS = ["none", "daily", "weekdays", "weekly", "bi-weekly", "monthly", "custom"]

    def __init__(self):
        super().__init__()
        self.title("Tiny Tasklist (Modular)")
        self.geometry("1120x660")
        self.db = load_db()
        
        # Track last shown mantra to avoid consecutive duplicates
        self.last_shown_mantra = None

        # Keeps expanded/collapsed state by group name (harmless to keep)
        self.group_state = {}  # {group_name: True/False}

        # Menu bar
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Settings...", command=self.open_settings)
        file_menu.add_command(label="Reminders…", command=self.open_reminders)
        file_menu.add_command(label="Import Tasks…", command=self.import_tasks)
        file_menu.add_command(label="Import (paste text)…", command=self.import_tasks_paste)
        file_menu.add_separator()
        file_menu.add_command(label="Open Repository Folder", command=self.open_repository_folder)
        menubar.add_cascade(label="File", menu=file_menu)

        mantra_menu = tk.Menu(menubar, tearoff=0)
        mantra_menu.add_command(label="Show Mantra…", command=self.open_mantras)
        mantra_menu.add_command(label="Open Mantra File", command=self.open_mantra_file)
        menubar.add_cascade(label="Mantras", menu=mantra_menu)

        journal_menu = tk.Menu(menubar, tearoff=0)
        journal_menu.add_command(label="Journal…", command=self.open_journal)
        journal_menu.add_command(label="Open Today's Journal", command=self.open_today_journal)
        menubar.add_cascade(label="Journal", menu=journal_menu)

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
                                    values=self.REPEAT_OPTIONS, state="readonly")
        repeat_combo.pack(side=tk.LEFT, padx=4)
        repeat_combo.bind("<<ComboboxSelected>>", self._on_repeat_selected)
        self.repeat_combo = repeat_combo

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
        settings = normalize_settings(self.db.get("settings", {}))
        self.db["settings"] = settings
        default_filter = settings.get("ui_filter_scope", "all")
        if default_filter == "habits":
            default_filter = "repeating"
        if default_filter not in ["today", "week", "overdue", "repeating", "all", "done", "deleted", "suspended"]:
            default_filter = "all"
        self.filter_var = tk.StringVar(value=default_filter)
        fcombo = ttk.Combobox(filt, textvariable=self.filter_var, width=10,
                              values=["today","week","overdue","repeating","all","done","deleted","suspended"],
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

        self.mark_done_btn = ttk.Button(filt, text="Mark Done", command=self.mark_done)
        self.delete_btn = ttk.Button(filt, text="Delete", command=self.soft_delete)
        self.suspend_btn = ttk.Button(filt, text="Suspend", command=self.suspend_tasks)
        self.mark_done_btn.pack(side=tk.LEFT, padx=(16, 4))
        self.delete_btn.pack(side=tk.LEFT, padx=4)
        self.suspend_btn.pack(side=tk.LEFT, padx=4)

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
        self.menu.add_command(label="Suspend", command=self.suspend_tasks)
        self.menu.add_command(label="Unsuspend", command=self.unsuspend_tasks)
        self.menu.add_command(label="Open Document…", command=self.open_task_document)

        setp = tk.Menu(self.menu, tearoff=0)
        setp.add_command(label="High",   command=lambda: self.set_priority_bulk("H"))
        setp.add_command(label="Medium", command=lambda: self.set_priority_bulk("M"))
        setp.add_command(label="Low",    command=lambda: self.set_priority_bulk("L"))
        setp.add_command(label="Daily",  command=lambda: self.set_priority_bulk("D"))
        setp.add_command(label="Misc",   command=lambda: self.set_priority_bulk("X"))
        self.menu.add_cascade(label="Set Priority", menu=setp)

        setr = tk.Menu(self.menu, tearoff=0)
        for rlab, rval in [("none","none"),("daily","daily"),("weekdays","weekdays"),("weekly","weekly"),("bi-weekly","bi-weekly"),("monthly","monthly"),("custom…","custom")]:
            setr.add_command(label=rlab, command=lambda v=rval: self.set_repeat_bulk(v))
        self.menu.add_cascade(label="Set Repeat", menu=setr)

        self.menu.add_command(label="Set Due…", command=self.set_due_bulk)

        # NEW: bulk set/clear group (assumes you have set_group_bulk implemented)
        self.menu.add_command(label="Set Group…", command=self.set_group_bulk)
        self.menu.add_command(label="Clear Group", command=lambda: self.set_group_bulk(clear=True))

        # Attach context menu to the new tree
        self.list.tree.bind("<Button-3>", self.popup_menu)
        self.list.tree.bind("<<TreeviewSelect>>", lambda e: self._update_action_buttons())

        # Initial refresh & schedule resets
        self.refresh()
        self.after(300, self.check_reminders)
        self.reset_repeating_tasks(catchup=True)
        self.schedule_midnight_reset()
        self.after(600, self._maybe_show_mantra_on_launch)

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
                self._apply_skip_escalation(t)
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

    def _on_repeat_selected(self, event=None):
        selected = (self.repeat_var.get() or "none").strip().lower()
        if selected != "custom":
            return
        custom_value = self._prompt_custom_repeat_days()
        if custom_value is None:
            self.repeat_var.set("none")
            return
        self.repeat_var.set(f"custom:{custom_value}")

    def _prompt_custom_repeat_days(self):
        return simpledialog.askinteger(
            "Custom Repeat",
            "Repeat every how many days?\n\nExample: 6 means repeats every 6 days.",
            parent=self,
            minvalue=1,
        )

    def _priority_visible(self, p: str) -> bool:
        s = self.db.get('settings', {})
        minv = s.get('min_priority_visible', 'L')
        minv_code = 'X' if isinstance(minv, str) and minv.lower() == 'misc' else (minv or 'L').upper()
        return PRIORITY_ORDER.get((p or 'M').upper(), 0) >= PRIORITY_ORDER.get(minv_code, 2)

    def _hazard_enabled(self) -> bool:
        return bool(self.db.get("settings", {}).get("hazard_escalation_enabled", False))

    def _apply_skip_escalation(self, task: dict) -> None:
        if not self._hazard_enabled():
            return
        if (task.get("repeat") or "none").lower() in ("", "none"):
            return
        task["skip_count"] = int(task.get("skip_count", 0)) + 1
        if task["skip_count"] >= 2 and "base_priority" not in task:
            task["base_priority"] = task.get("priority", "M")
        if task["skip_count"] >= 3:
            task["priority"] = "U"
        elif task["skip_count"] >= 2:
            task["priority"] = "H"

    def reset_hazard_escalation(self):
        changed = False
        for t in self.db.get("tasks", []):
            if int(t.get("skip_count", 0)) != 0:
                t["skip_count"] = 0
                changed = True
            if "base_priority" in t:
                t["priority"] = t.get("base_priority", t.get("priority", "M"))
                t.pop("base_priority", None)
                changed = True
        if changed:
            save_db(self.db)
            self.refresh()
        messagebox.showinfo("Hazard Escalation", "Hazard escalation has been reset for all tasks.")

    def _display_title(self, task: dict) -> str:
        title = task.get("title", "")
        if self._hazard_enabled() and int(task.get("skip_count", 0)) >= 1:
            return f"⚠ {title}"
        return title

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

        self._configure_context_menu()
        self.menu.tk_popup(event.x_root, event.y_root)

    def _configure_context_menu(self):
        self.menu.delete(0, tk.END)
        
        # Create Edit cascade submenu
        edit_menu = tk.Menu(self.menu, tearoff=0)
        edit_menu.add_command(label="Manual Edit", command=self.edit_task)
        
        # Set Priority cascade
        priority_menu = tk.Menu(edit_menu, tearoff=0)
        priority_menu.add_command(label="High", command=lambda: self.set_priority_bulk("H"))
        priority_menu.add_command(label="Medium", command=lambda: self.set_priority_bulk("M"))
        priority_menu.add_command(label="Low", command=lambda: self.set_priority_bulk("L"))
        priority_menu.add_command(label="Daily", command=lambda: self.set_priority_bulk("D"))
        priority_menu.add_command(label="Misc", command=lambda: self.set_priority_bulk("X"))
        edit_menu.add_cascade(label="Set Priority", menu=priority_menu)
        
        # Set Repeat cascade
        repeat_menu = tk.Menu(edit_menu, tearoff=0)
        repeat_menu.add_command(label="none", command=lambda: self.set_repeat_bulk("none"))
        repeat_menu.add_command(label="daily", command=lambda: self.set_repeat_bulk("daily"))
        repeat_menu.add_command(label="weekdays", command=lambda: self.set_repeat_bulk("weekdays"))
        repeat_menu.add_command(label="weekly", command=lambda: self.set_repeat_bulk("weekly"))
        repeat_menu.add_command(label="bi-weekly", command=lambda: self.set_repeat_bulk("bi-weekly"))
        repeat_menu.add_command(label="monthly", command=lambda: self.set_repeat_bulk("monthly"))
        repeat_menu.add_command(label="custom…", command=lambda: self.set_repeat_bulk("custom"))
        edit_menu.add_cascade(label="Set Repeat", menu=repeat_menu)
        
        edit_menu.add_command(label="Set Due…", command=self.set_due_bulk)
        edit_menu.add_command(label="Set Group…", command=self.set_group_bulk)
        
        # Bump cascade
        bump_menu = tk.Menu(edit_menu, tearoff=0)
        bump_menu.add_command(label="+1 day", command=lambda: self.bump_days(1))
        bump_menu.add_command(label="-1 day", command=lambda: self.bump_days(-1))
        bump_menu.add_command(label="+1 week", command=lambda: self.bump_weeks(1))
        bump_menu.add_command(label="-1 week", command=lambda: self.bump_weeks(-1))
        edit_menu.add_cascade(label="Bump", menu=bump_menu)
        
        self.menu.add_cascade(label="Edit", menu=edit_menu)
        
        # State-aware Delete/Restore and Suspend/Unsuspend
        selection = self.selected_tasks()
        show_restore = any(t.get("is_deleted") for t in selection)
        show_delete = any(not t.get("is_deleted") for t in selection)
        show_unsuspend = any(t.get("is_suspended") for t in selection)
        show_suspend = any(not t.get("is_suspended") for t in selection)
        delete_label = "Restore" if show_restore and not show_delete else "Delete (soft)"
        delete_cmd = self.restore if delete_label == "Restore" else self.soft_delete
        suspend_label = "Unsuspend" if show_unsuspend and not show_suspend else "Suspend"
        suspend_cmd = self.unsuspend_tasks if suspend_label == "Unsuspend" else self.suspend_tasks
        self.menu.add_command(label=delete_label, command=delete_cmd)
        self.menu.add_command(label="Hard Delete…", command=self.hard_delete)
        self.menu.add_command(label=suspend_label, command=suspend_cmd)
        self.menu.add_command(label="Open Document…", command=self.open_task_document)

    def _update_action_buttons(self):
        if not hasattr(self, "list"):
            return
        selection = self.selected_tasks()
        has_deleted = any(t.get("is_deleted") for t in selection)
        has_active = any(not t.get("is_deleted") for t in selection)
        has_suspended = any(t.get("is_suspended") for t in selection)
        has_unsuspended = any(not t.get("is_suspended") for t in selection)
        if has_deleted and not has_active:
            self.delete_btn.config(text="Restore", command=self.restore, state="normal")
        else:
            self.delete_btn.config(text="Delete", command=self.soft_delete, state="normal" if selection else "disabled")
        if has_suspended and not has_unsuspended:
            self.suspend_btn.config(text="Unsuspend", command=self.unsuspend_tasks, state="normal")
        else:
            self.suspend_btn.config(text="Suspend", command=self.suspend_tasks, state="normal" if selection else "disabled")

    def open_task_document(self):
        sels = self.selected_tasks()
        if not sels:
            return
        task = sels[0]
        move_task_document_if_needed(task)
        # Read external changes before opening
        if read_task_notes_from_file(task):
            # Save DB only if external changes were detected and applied
            save_db(self.db)
        else:
            # No external changes, ensure file is synced with current notes
            # (save_db not needed here as sync_task_notes doesn't modify task)
            sync_task_notes(task)
        open_document(task_doc_path(task))

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
            "is_suspended": False,
            "skip_count": 0,
            "group": ""  # group set via Edit or bulk action
        }
        self.db["tasks"].append(t)
        self.db["next_id"] += 1
        save_db(self.db)
        sync_task_notes(t)
        save_db(self.db)
        self.title_var.set("")
        self.due_var.set("")
        self.notes_txt.delete("1.0", "end")
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
            "is_suspended": False,
            "skip_count": 0,
            "group": ""
        }
        self.db["tasks"].append(t); self.db["next_id"] += 1
        save_db(self.db)
        sync_task_notes(t)
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
            move_task_document_if_needed(t)
            sync_task_notes(t)
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
            move_task_document_if_needed(t)
            sync_task_notes(t)
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
        if scope == "suspended":
            return t.get("is_suspended", False) and not t.get("is_deleted", False)
        if t.get("is_deleted", False):
            return False
        if t.get("is_suspended", False):
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
        if scope in ("habits", "repeating"):
            return (t.get("repeat") or "").lower() not in ("", "none")
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
        if scope == "habits":
            scope = "repeating"
        query = self.search_var.get().strip()
        col, asc = self.sort_state

        tasks = [t for t in self.db["tasks"] if self.passes_filter(t, scope) and self.search_match(t, query)]
        tasks.sort(key=lambda x: self.sort_key_for(x, col), reverse=not asc)
        for t in tasks:
            t["_display_title"] = self._display_title(t)

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
        self._update_action_buttons()

    # ===== Stats / Settings / Reminders =====
    def open_help(self, initial_tab: str = "tutorial"):
        HelpDialog(self, initial_tab=initial_tab)

    def open_mantras(self):
        def _next():
            # Reload mantras from file each time
            mantra = self._pick_random_mantra()
            self.last_shown_mantra = mantra
            return mantra

        def _add():
            text = simpledialog.askstring("Add Mantra", "Enter a new mantra:", parent=self)
            if text:
                # Append to the mantra file
                path = get_mantras_file_path()
                current_content = path.read_text(encoding="utf-8")
                if not current_content.endswith('\n'):
                    current_content += '\n'
                path.write_text(current_content + text.strip() + '\n', encoding="utf-8")
                return text.strip()
            return None

        # Load mantras from file and pick initial one
        initial = self._pick_mantra_of_day()
        self.last_shown_mantra = initial
        # MantraDialog no longer needs mantras parameter - loads from file via callbacks
        MantraDialog(self, on_add=_add, on_next=_next, initial=initial)

    def _pick_mantra_of_day(self) -> str:
        """Pick mantra based on day of year from file."""
        mantras = load_mantras_from_file()
        if not mantras:
            return ""
        idx = date.today().toordinal() % len(mantras)
        return mantras[idx]

    def _pick_random_mantra(self) -> str:
        """Pick a random mantra from file, avoiding the last shown one if possible."""
        mantras = load_mantras_from_file()
        if not mantras:
            return ""
        
        # If only one mantra, return it
        if len(mantras) == 1:
            return mantras[0]
        
        # Filter out the last shown mantra to avoid consecutive duplicates
        available = [m for m in mantras if m != self.last_shown_mantra]
        
        # If all mantras were filtered out (shouldn't happen), use all mantras
        if not available:
            available = mantras
        
        import random
        return random.choice(available)

    def _maybe_show_mantra_on_launch(self):
        settings = self.db.get("settings", {})
        if not settings.get("mantras_autoshow", True):
            return
        today_key = date.today().isoformat()
        if settings.get("last_mantra_date") == today_key:
            return
        settings["last_mantra_date"] = today_key
        save_db(self.db)
        self.open_mantras()

    def open_journal(self):
        def _add_entry(text: str):
            append_journal_manual(text)

        def _open_file():
            path = ensure_journal_path()
            open_document(path)

        JournalDialog(self, on_add_entry=_add_entry, on_open_file=_open_file)

    def open_today_journal(self):
        path = ensure_journal_path()
        open_document(path)
    
    def open_repository_folder(self):
        """Open the data directory in the system file explorer."""
        open_directory(DATA_DIR)
    
    def open_mantra_file(self):
        """Open the mantras file for manual editing."""
        path = get_mantras_file_path()
        open_document(path)

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
            merged = normalize_settings(self.db.get("settings", {}))
            reset_requested = bool(s.pop("reset_hazard_escalation", False))
            merged.update(s)
            self.db["settings"] = merged
            save_db(self.db)
            if reset_requested:
                self.reset_hazard_escalation()
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
