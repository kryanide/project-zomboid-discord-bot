@echo off
REM Starts the PZ Discord bot using the project's virtual environment.
REM Run this from anywhere - it cd's to its own folder first.

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Virtual environment not found at .venv\Scripts\python.exe
    echo Create it with:  py -m venv .venv
    pause
    exit /b 1
)

".venv\Scripts\python.exe" bot.py

echo.
echo Bot exited with code %errorlevel%.
pause
