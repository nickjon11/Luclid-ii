@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
 echo Missing virtual environment. Follow README.md setup instructions.
 pause
 exit /b 1
)
".venv\Scripts\python.exe" -m local_muse.app
