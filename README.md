# TasklistProgram

A task management application built with Python and tkinter.

## System Requirements

- Python 3.13 or higher
- tkinter (Python's standard GUI library)

## Installation

### 1. Install System Dependencies

tkinter is not installed by default on all systems. Install it using your system's package manager:

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install python3-tk
```

**Fedora:**
```bash
sudo dnf install python3-tkinter
```

**macOS:**
tkinter is usually included with Python installations from python.org. If needed:
```bash
brew install python-tk
```

**Windows:**
tkinter is included with the standard Python installer from python.org.

### 2. Verify tkinter Installation

```bash
python3 -c "import tkinter; print('tkinter is installed')"
```

If this command runs without errors, tkinter is properly installed.

### 3. Install the Application

Using Poetry (recommended):
```bash
poetry install
poetry run python -m tasklistprogram
```

Using pip:
```bash
pip install -e .
python -m tasklistprogram
```

Using the provided scripts:
- **Windows PowerShell:** `.\run.ps1`
- **Windows Command Prompt:** `.\run.bat`

## Running the Application

After installation, run the application using:
```bash
python -m tasklistprogram
```

Or use the provided convenience scripts for Windows.

## Troubleshooting

### ModuleNotFoundError: No module named 'tkinter'

This error means tkinter is not installed on your system. Follow the system dependencies installation instructions above for your operating system.

## License

See LICENSE file for details.
