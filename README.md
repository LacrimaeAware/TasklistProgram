# Tiny Tasklist

A lightweight task management application built with Python and Tkinter.

## Features

- Task management with priorities (High, Medium, Low, Daily, Misc)
- Recurring tasks (daily, weekdays, weekly, monthly)
- Due dates and times
- Task grouping and filtering
- Search functionality
- Statistics and streaks tracking
- Import/export capabilities

## Getting Started

### Quick Start

• **Add a task**: Fill in Title and optional Due/Priority/Repeat fields, then click Add
• **Edit a task**: Double-click any row
• **Mark done**: Select task(s) and click Mark Done
• **Delete or restore**: Use Delete/Restore buttons or right-click menu

## Fields Explained

- **Title**: Short label for the task
- **Due**: Date and optionally time (see formats below)
- **Priority**: H (High), M (Medium), L (Low), D (Daily habit), or Misc
- **Repeat**: none, daily, weekdays, weekly, or monthly
- **Notes**: Free text for additional details
- **Group**: Optional label for organizing related tasks

## Due Date Formats

The app supports flexible date/time input:

- `2024-10-05` (date only)
- `2024-10-05 14:00` (date with time)
- `10/05` (MM/DD, current year)
- `10/05 14:00` (MM/DD with time)
- `14:00` or `1400` (today at 2:00 PM)
- `midnight` (today at 23:59)
- `+2d +3h` (relative, 2 days and 3 hours from now)

## Tips

- Use **Group view** to collapse tasks by group
- **Search** filters both titles and notes
- Group view and filter selections are saved between sessions
- Task data is stored in `data/tasks_gui.json` (automatically backed up)

## Folder Structure

```
TasklistProgram/
├── data/                     # User data (gitignored)
│   ├── tasks_gui.json       # Task database
│   └── tasks_gui.json.bak   # Automatic backup
├── tasklistprogram/         # Application code
│   ├── core/                # Core logic
│   │   ├── filesystem.py    # Folder name utilities
│   │   ├── model.py         # Data management
│   │   ├── actions.py       # Task operations
│   │   └── ...
│   └── ui/                  # User interface
│       ├── dialogs.py       # Dialog windows
│       ├── listview.py      # Task list display
│       └── ...
└── test_filesystem.py       # Tests
```
### Code Structure

- `tasklistprogram/app.py` - Main application window
- `tasklistprogram/core/` - Core business logic
- `tasklistprogram/ui/` - User interface components
- `tasklistprogram/data/` - Personal Data
- 

<img width="1455" height="1306" alt="image" src="https://github.com/user-attachments/assets/76faf5af-0487-44cc-815e-f5aaff020378" />

