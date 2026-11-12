#!/usr/bin/env python3
"""One-command source launcher. Installs into an isolated venv on first use."""
import os
import subprocess
import sys
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENV = ROOT / '.venv'
PYTHON = ENV / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')

def main():
    if sys.version_info < (3, 11):
        raise SystemExit('Luclid-ii requires Python 3.11 or newer.')
    if not PYTHON.exists():
        print('Luclid-ii: preparing a private Python environment (first run only)...', flush=True)
        venv.EnvBuilder(with_pip=True).create(ENV)
    stamp = ENV / '.luclid-installed-version'
    version = (ROOT / 'VERSION').read_text().strip()
    if not stamp.exists() or stamp.read_text().strip() != version:
        print('Luclid-ii: installing dependencies (internet required on first run)...', flush=True)
        subprocess.check_call([str(PYTHON), '-m', 'pip', 'install', '--disable-pip-version-check', '-e', str(ROOT)])
        stamp.write_text(version)
    os.execv(str(PYTHON), [str(PYTHON), '-m', 'local_muse.app', *sys.argv[1:]]) if os.name != 'nt' else subprocess.call([str(PYTHON), '-m', 'local_muse.app', *sys.argv[1:]])

if __name__ == '__main__':
    try:
        main()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f'Luclid-ii could not start: {exc}')
