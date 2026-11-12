"""Windowless setup entry point for Windows."""
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).with_name('Luclid-ii-Setup.py')),run_name='__main__')
