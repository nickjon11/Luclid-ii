@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" py -3 -m venv .venv
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -e .
".venv\Scripts\python.exe" -m playwright install chromium
if errorlevel 1 (echo Setup failed. & pause & exit /b 1)
echo Setup complete.
pause
