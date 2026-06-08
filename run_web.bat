@echo off
REM Launch the Tiny Tasklist local web server (windowless) and open it in the browser.
cd /d "%~dp0"
start "" pythonw -m tasklistprogram.webserver 8000
timeout /t 1 >nul
start "" http://localhost:8000
