@echo off
cd /d "%~dp0"
py -3 "Luclid-ii-Setup.py"
if errorlevel 1 pause
