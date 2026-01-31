# Task Document Folders

This document explains how task-related document folders should be organized.

## Folder Structure

The application now uses a clean folder structure:

```
TasklistProgram/
├── data/                          # User data folder (gitignored)
│   ├── tasks_gui.json            # Task database
│   ├── tasks_gui.json.bak        # Backup
│   └── task_documents/           # Optional: documents related to tasks
│       ├── Project Name/         # Example: folder for a project
│       ├── Daily Maintenance/    # Example: folder for recurring tasks
│       └── ...
├── tasklistprogram/              # Application code
│   └── core/
│       └── filesystem.py         # Utilities for creating properly named folders
└── ...
```

## Creating Task Document Folders

If you need to create folders for organizing documents related to your tasks or groups, you can use the provided filesystem utilities:

```python
from pathlib import Path
from tasklistprogram.core.filesystem import create_task_document_folder

# Create the base task documents directory
base_path = Path("data/task_documents")

# Create a folder for a specific task or group
# The name will be automatically sanitized for filesystem safety
folder = create_task_document_folder(base_path, "Daily Maintenance")
# Creates: data/task_documents/Daily Maintenance/

# Example with special characters
folder = create_task_document_folder(base_path, "Project: Important Tasks")
# Creates: data/task_documents/Project  Important Tasks/
```

## Important: Folder Naming

The `sanitize_folder_name()` function ensures folder names are safe for all operating systems:

### What it does:
- ✅ Preserves all normal characters (including 'n', 't', and all other letters)
- ✅ Replaces only unsafe filesystem characters: `< > : " / \ | ? *`
- ✅ Handles leading/trailing spaces and dots
- ✅ Limits folder name length for compatibility

### What it does NOT do:
- ❌ Does NOT replace normal letters like 'n' or 't'
- ❌ Does NOT mangle words like "Supplements", "Maintenance", or "Internet"

## Example Usage

```python
from tasklistprogram.core.filesystem import sanitize_folder_name

# These work correctly:
sanitize_folder_name("Supplements")         # → "Supplements"
sanitize_folder_name("Daily Maintenance")   # → "Daily Maintenance"  
sanitize_folder_name("Diet Food")           # → "Diet Food"
sanitize_folder_name("Internet Connection") # → "Internet Connection"

# Unsafe characters are handled:
sanitize_folder_name("Task: Important")     # → "Task  Important"
sanitize_folder_name("File<Name>")          # → "File Name "
```

## Git Ignore

The `data/` folder is automatically ignored by git, so your personal task data and documents won't be committed to version control.
