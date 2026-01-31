import tkinter as tk
from tkinter import ttk, messagebox
from ..core.dates import parse_due_flexible, fmt_due_for_store

class EditDialog(tk.Toplevel):
    def __init__(self, master, task, on_save):
        super().__init__(master)
        self.title(f"Edit Task #{task['id']}")
        self.resizable(False, False)
        self.on_save = on_save
        self.task = task

        frm = ttk.Frame(self, padding=10)
        frm.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frm, text="Title").grid(row=0, column=0, sticky="w")
        self.title_var = tk.StringVar(value=task.get("title",""))
        ttk.Entry(frm, textvariable=self.title_var, width=40).grid(row=0, column=1, sticky="we", padx=6, pady=4)

        ttk.Label(frm, text="Due").grid(row=1, column=0, sticky="w")
        self.due_var = tk.StringVar(value=task.get("due",""))
        ttk.Entry(frm, textvariable=self.due_var, width=24).grid(row=1, column=1, sticky="w", padx=6, pady=4)

        ttk.Label(frm, text="Priority").grid(row=2, column=0, sticky="w")
        self.prio_var = tk.StringVar(value=task.get("priority","M"))
        prio_values = ["H", "M", "L", "D"]
        if str(task.get("priority", "")).upper() == "U":
            prio_values = ["U"] + prio_values
        ttk.Combobox(frm, textvariable=self.prio_var, state="readonly", values=prio_values, width=6)\
            .grid(row=2, column=1, sticky="w", padx=6, pady=4)

        ttk.Label(frm, text="Repeat").grid(row=3, column=0, sticky="w")
        self.rep_var = tk.StringVar(value=task.get("repeat","none"))
        ttk.Combobox(frm, textvariable=self.rep_var, state="readonly",
                     values=["none","daily","weekdays","weekly","monthly"], width=12)\
            .grid(row=3, column=1, sticky="w", padx=6, pady=4)

        ttk.Label(frm, text="Group").grid(row=4, column=0, sticky="w")
        self.group_var = tk.StringVar(value=task.get("group",""))
        ttk.Entry(frm, textvariable=self.group_var, width=24).grid(row=4, column=1, sticky="w", padx=6, pady=4)

        ttk.Label(frm, text="Notes").grid(row=5, column=0, sticky="nw")
        self.notes_txt = tk.Text(frm, width=40, height=4)
        self.notes_txt.grid(row=5, column=1, sticky="we", padx=6, pady=4)
        self.notes_txt.insert("1.0", task.get("notes",""))

        btns = ttk.Frame(frm)
        btns.grid(row=6, column=0, columnspan=2, pady=(8,0))
        ttk.Button(btns, text="Save", command=self.save).pack(side=tk.LEFT, padx=6)
        ttk.Button(btns, text="Cancel", command=self.destroy).pack(side=tk.LEFT, padx=6)

        self.bind("<Return>", lambda e: self.save())
        self.bind("<Escape>", lambda e: self.destroy())

    def save(self):
        title = self.title_var.get().strip()
        if not title:
            messagebox.showerror("Error", "Title required.")
            return
        due_s = self.due_var.get().strip()
        parsed = None
        if due_s:
            parsed = parse_due_flexible(due_s)
            if parsed is None:
                messagebox.showerror("Error", "Invalid due format.")
                return
        prio = self.prio_var.get().upper()
        if prio == "U" and str(self.task.get("priority", "")).upper() != "U":
            prio = "H"
        rep = self.rep_var.get()
        if prio == "D":
            rep = "daily"
        data = {
            "title": title,
            "due": fmt_due_for_store(parsed) if due_s else "",
            "priority": prio,
            "repeat": rep,
            "notes": self.notes_txt.get("1.0", "end").strip(),
            "group": self.group_var.get().strip(),
        }
        self.on_save(data)
        self.destroy()

class StatsDialog(tk.Toplevel):
    def __init__(self, master, summary):
        super().__init__(master)
        self.title("Stats")
        self.resizable(False, False)
        frm = ttk.Frame(self, padding=12)
        frm.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frm, text=f"Open tasks: {summary['open']}").pack(anchor="w")
        ttk.Label(frm, text=f"Done today: {summary['done_today']}").pack(anchor="w")
        ttk.Label(frm, text=f"Done last 7 days: {summary['done_7']}").pack(anchor="w")
        ttk.Label(frm, text=f"Done last 30 days: {summary['done_30']}").pack(anchor="w")

        ttk.Label(frm, text="Top streaks (daily/recurring):", padding=(0,8,0,0)).pack(anchor="w")
        if not summary["top_streaks"]:
            ttk.Label(frm, text="(none)").pack(anchor="w")
        else:
            for title, streak in summary["top_streaks"]:
                ttk.Label(frm, text=f"  {title} — {streak} days").pack(anchor="w")


class SettingsDialog(tk.Toplevel):
    def __init__(self, master, settings, on_save):
        super().__init__(master)
        self.title("Settings")
        self.resizable(False, False)
        self.on_save = on_save

        s = settings or {
            "reminders_enabled": True,
            "reminder_count": 4,
            "reminder_min_priority": "M",
            "min_priority_visible": "L",
            "hazard_escalation_enabled": False,
            "mantras_autoshow": True,
        }

        frm = ttk.Frame(self, padding=12)
        frm.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.enabled_var = tk.BooleanVar(value=s.get("reminders_enabled", True))
        chk = ttk.Checkbutton(frm, text="Enable reminders", variable=self.enabled_var)
        chk.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0,8))

        ttk.Label(frm, text="Reminder count (per task):").grid(row=1, column=0, sticky="w")
        self.count_var = tk.IntVar(value=int(s.get("reminder_count", 4)))
        ttk.Spinbox(frm, from_=1, to=12, textvariable=self.count_var, width=6)\
            .grid(row=1, column=1, sticky="w", padx=6, pady=4)

        ttk.Label(frm, text="Min priority for reminders:").grid(row=2, column=0, sticky="w")
        self.minp_var = tk.StringVar(value=s.get("reminder_min_priority","M"))
        ttk.Combobox(frm, textvariable=self.minp_var, values=["H","M","L","D","Misc"], state="readonly", width=8)\
            .grid(row=2, column=1, sticky="w", padx=6, pady=4)

        ttk.Label(frm, text="Min priority to show:").grid(row=3, column=0, sticky="w")
        self.minvis_var = tk.StringVar(value=s.get("min_priority_visible","L"))
        ttk.Combobox(frm, textvariable=self.minvis_var, values=["H","M","L","D","Misc"], state="readonly", width=8)\
            .grid(row=3, column=1, sticky="w", padx=6, pady=4)

        self.hazard_var = tk.BooleanVar(value=s.get("hazard_escalation_enabled", False))
        ttk.Checkbutton(frm, text="Enable hazard escalation (skip warnings)", variable=self.hazard_var)\
            .grid(row=4, column=0, columnspan=2, sticky="w", pady=(8, 0))

        self.mantra_autoshow_var = tk.BooleanVar(value=s.get("mantras_autoshow", True))
        ttk.Checkbutton(frm, text="Show mantra at first launch each day", variable=self.mantra_autoshow_var)\
            .grid(row=5, column=0, columnspan=2, sticky="w", pady=(4, 0))

        btns = ttk.Frame(frm)
        btns.grid(row=6, column=0, columnspan=2, sticky="e", pady=(12,0))
        ttk.Button(btns, text="Save", command=self.save).pack(side=tk.LEFT, padx=6)
        ttk.Button(btns, text="Cancel", command=self.destroy).pack(side=tk.LEFT, padx=6)


    def save(self):
        data = {
            "reminders_enabled": self.enabled_var.get(),
            "reminder_count": max(1, int(self.count_var.get())),
            "reminder_min_priority": self.minp_var.get(),
            "min_priority_visible": self.minvis_var.get(),
            "hazard_escalation_enabled": self.hazard_var.get(),
            "mantras_autoshow": self.mantra_autoshow_var.get(),
        }
        self.on_save(data)
        self.destroy()

class HelpDialog(tk.Toplevel):
    def __init__(self, master, initial_tab: str = "tutorial"):
        super().__init__(master)
        self.title("Help & Guide")
        self.geometry("820x560")
        self.resizable(True, True)

        frm = ttk.Frame(self, padding=10)
        frm.pack(fill=tk.BOTH, expand=True)

        notebook = ttk.Notebook(frm)
        notebook.pack(fill=tk.BOTH, expand=True)

        tutorial = self._build_text_tab(
            notebook,
            "Quick Start",
            (
                "Getting started\n"
                "• Add a task: fill Title and (optional) Due/Priority/Repeat, then click Add.\n"
                "• Edit a task: double-click a row.\n"
                "• Mark done: select task(s) and click Mark Done.\n"
                "• Delete or restore: use Delete/Restore or the right-click menu.\n\n"
                "Fields explained\n"
                "• Title: a short label for the task.\n"
                "• Due: accepts date-only or date+time (see examples below).\n"
                "• Priority: H/M/L/D/Misc (D = daily repeat).\n"
                "• Repeat: none, daily, weekdays, weekly, monthly.\n"
                "• Notes: free text, useful for details.\n"
                "• Group: optional label used for grouping in the list.\n\n"
                "Due date formats (examples)\n"
                "• 2024-10-05\n"
                "• 2024-10-05 14:00\n"
                "• 10/05\n"
                "• 10/05 14:00\n"
                "• 14:00 or 1400 (today at 2:00 PM)\n"
                "• midnight (today at 23:59)\n"
                "• +2d +3h (relative)\n\n"
                "Tips\n"
                "• Use Group view to collapse tasks by group.\n"
                "• Search filters titles and notes.\n"
                "• Repeating Tasks filter shows all repeating items.\n"
                "• Group view and filter selections are saved between runs.\n"
            ),
        )

        import_tab = self._build_text_tab(
            notebook,
            "Import Instructions",
            (
                "Paste or generate tasks in this format (one per line):\n"
                "  Title | due: <date or time or +rel> | prio: H/M/L/D/Misc | repeat: none/daily/weekdays/weekly/monthly | group: <name> | notes: <free text>\n\n"
                "Shortcuts:\n"
                "  • Plain text before the first '|' becomes the title.\n"
                "  • due accepts 'YYYY-MM-DD', 'MM/DD', 'HH:MM', 'HHMM', words like 'tomorrow', 'fri', or '+2d +3h'.\n"
                "  • prio: H/M/L/D (D forces repeat=daily), or 'Misc'.\n"
                "  • Any field is optional. Unknown fields are ignored.\n\n"
                "Examples:\n"
                "  Project 1 Due | due: Sept 29 | prio: H | group: CS101 | notes: start early\n"
                "  Program Assignment 3 Due | due: 09/22 | prio: M | group: CS101\n"
                "  Midterm Exam | due: 10/13 14:00 | prio: H | group: CS101\n"
                "  Reflection 2 Due | due: Dec 1 | prio: L | group: CS101\n"
            ),
        )

        notebook.add(tutorial, text="Tutorial")
        notebook.add(import_tab, text="Import")

        tabs = {"tutorial": 0, "import": 1}
        notebook.select(tabs.get(initial_tab, 0))

        btns = ttk.Frame(frm)
        btns.pack(fill=tk.X, pady=(8, 0))
        ttk.Button(
            btns,
            text="Copy Tab",
            command=lambda: self._copy_tab_text(notebook),
        ).pack(side=tk.LEFT)
        ttk.Button(btns, text="Close", command=self.destroy).pack(side=tk.RIGHT)

    def _build_text_tab(self, notebook: ttk.Notebook, title: str, content: str) -> ttk.Frame:
        panel = ttk.Frame(notebook, padding=8)
        txt = tk.Text(panel, width=84, height=24, wrap="word")
        txt.insert("1.0", content)
        txt.config(state="disabled")
        txt.pack(fill=tk.BOTH, expand=True)
        panel._text_widget = txt
        panel._tab_title = title
        return panel

    def _copy_tab_text(self, notebook: ttk.Notebook) -> None:
        panel = notebook.nametowidget(notebook.select())
        txt = getattr(panel, "_text_widget", None)
        if not txt:
            return
        self.clipboard_clear()
        self.clipboard_append(txt.get("1.0", "end-1c"))


class MantraDialog(tk.Toplevel):
    def __init__(self, master, mantras: list[str], on_add, on_next, initial: str | None = None):
        super().__init__(master)
        self.title("Mantras")
        self.resizable(False, False)
        self.mantras = mantras
        self.on_add = on_add
        self.on_next = on_next

        frm = ttk.Frame(self, padding=12)
        frm.pack(fill=tk.BOTH, expand=True)

        self.text_var = tk.StringVar(value=initial or "")
        label = ttk.Label(frm, textvariable=self.text_var, wraplength=420, justify="center")
        label.pack(fill=tk.BOTH, expand=True, pady=(0, 12))

        btns = ttk.Frame(frm)
        btns.pack(fill=tk.X)
        ttk.Button(btns, text="Show another", command=self._show_next).pack(side=tk.LEFT)
        ttk.Button(btns, text="Add mantra", command=self._add_mantra).pack(side=tk.LEFT, padx=8)
        ttk.Button(btns, text="Close", command=self.destroy).pack(side=tk.RIGHT)

    def _show_next(self):
        self.text_var.set(self.on_next())

    def _add_mantra(self):
        text = self.on_add()
        if text:
            self.text_var.set(text)


class JournalDialog(tk.Toplevel):
    def __init__(self, master, on_add_entry, on_open_file):
        super().__init__(master)
        self.title("Journal")
        self.resizable(True, True)
        self.on_add_entry = on_add_entry
        self.on_open_file = on_open_file

        frm = ttk.Frame(self, padding=12)
        frm.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frm, text="Add journal entry (saved to today's file):").pack(anchor="w")
        self.txt = tk.Text(frm, width=70, height=6, wrap="word")
        self.txt.pack(fill=tk.BOTH, expand=True, pady=(6, 10))

        btns = ttk.Frame(frm)
        btns.pack(fill=tk.X)
        ttk.Button(btns, text="Add entry", command=self._submit).pack(side=tk.LEFT)
        ttk.Button(btns, text="Open journal file", command=self.on_open_file).pack(side=tk.LEFT, padx=8)
        ttk.Button(btns, text="Close", command=self.destroy).pack(side=tk.RIGHT)

    def _submit(self):
        text = self.txt.get("1.0", "end-1c").strip()
        if not text:
            messagebox.showinfo("Journal", "Nothing to add.")
            return
        self.on_add_entry(text)
        self.txt.delete("1.0", "end")


class PasteImportDialog(tk.Toplevel):
    def __init__(self, master, on_import_text):
        super().__init__(master)
        self.title("Import Tasks – Paste Text")
        self.resizable(True, True)
        self.on_import_text = on_import_text

        frm = ttk.Frame(self, padding=10)
        frm.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frm, text="Paste lines below and click Import:").pack(anchor="w")
        self.txt = tk.Text(frm, width=84, height=16, wrap="word")
        self.txt.pack(fill=tk.BOTH, expand=True, pady=6)

        btns = ttk.Frame(frm)
        btns.pack(fill=tk.X)
        ttk.Button(btns, text="Import", command=self._do_import).pack(side=tk.LEFT)
        ttk.Button(btns, text="Cancel", command=self.destroy).pack(side=tk.RIGHT)

    def _do_import(self):
        text = self.txt.get("1.0", "end-1c").strip()
        if not text:
            messagebox.showinfo("Import", "Nothing to import.")
            return
        try:
            added, failed = self.on_import_text(text)
            messagebox.showinfo("Import", f"Imported {added} task(s). Failed: {failed}.")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Import failed", str(e))

class RemindersDialog(tk.Toplevel):
    def __init__(self, master, reminders, on_ack):
        super().__init__(master)
        self.title("Reminders")
        self.geometry("720x380")
        self.on_ack = on_ack

        frm = ttk.Frame(self, padding=8)
        frm.pack(fill=tk.BOTH, expand=True)

        cols = ("id","title","due","priority","checkpoint")
        self.tree = ttk.Treeview(frm, columns=cols, show="headings", height=12, selectmode="extended")
        headers = {"id":"ID","title":"TITLE","due":"DUE","priority":"PRIO","checkpoint":"CHECKPOINT"}
        widths = {"id":60,"title":360,"due":160,"priority":80,"checkpoint":180}
        for c in cols:
            self.tree.heading(c, text=headers[c])
            self.tree.column(c, width=widths[c], anchor=tk.W)
        self.tree.pack(fill=tk.BOTH, expand=True)

        for row in reminders:
            self.tree.insert("", tk.END, values=(
                row["id"], row["title"], row.get("_due_str",""), row.get("priority",""), row.get("_cp_key","")
            ))

        btns = ttk.Frame(frm)
        btns.pack(fill=tk.X, pady=(8,0))
        ttk.Button(btns, text="Acknowledge", command=self.ack_selected).pack(side=tk.LEFT)
        ttk.Button(btns, text="Close", command=self.destroy).pack(side=tk.RIGHT)

        self.tree.bind("<Double-1>", lambda e: self.ack_selected())

    def ack_selected(self):
        sels = self.tree.selection()
        pairs = []
        for iid in sels:
            vals = self.tree.item(iid)["values"]
            if vals and len(vals) >= 5:
                pairs.append((int(vals[0]), str(vals[4])))
        if pairs:
            self.on_ack(pairs)
            for iid in list(sels):
                self.tree.delete(iid)
