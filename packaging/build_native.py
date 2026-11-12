#!/usr/bin/env python3
"""Build native GUI executable using PyInstaller on the target OS."""
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sep = ';' if sys.platform == 'win32' else ':'
cmd = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean',
       '--windowed', '--onedir', '--name', 'Luclid-ii',
       '--collect-all', 'keyring', '--collect-all', 'playwright',
       '--collect-all', 'local_muse',
       '--add-data', f'{root / "wallpapers"}{sep}wallpapers',
       '--paths', str(root / 'src'),
       str(root / 'packaging/entry.py')]
if sys.platform == 'win32':
    cmd[cmd.index(str(root / 'packaging/entry.py')):cmd.index(str(root / 'packaging/entry.py'))] = ['--icon', str(root / 'src/local_muse/assets/lii_icon.ico')]
subprocess.check_call(cmd, cwd=root)
