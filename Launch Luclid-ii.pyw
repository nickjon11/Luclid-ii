"""Windowless Windows launcher for an already-installed Luclid-ii environment."""
import subprocess
from pathlib import Path
root=Path(__file__).resolve().parent
pythonw=root/'.venv'/'Scripts'/'pythonw.exe'
if not pythonw.exists():
    from tkinter import Tk, messagebox
    window=Tk();window.withdraw()
    messagebox.showerror('Luclid-ii','Install Luclid-ii using Luclid-ii-Setup.py first.')
else:
    subprocess.Popen([str(pythonw),'-m','local_muse.app'],cwd=str(root),creationflags=subprocess.CREATE_NO_WINDOW)
