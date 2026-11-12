#!/usr/bin/env python3
"""Package a Linux-built PyInstaller onedir into a Debian .deb."""
import os
import shutil
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[2]
version = (root / 'VERSION').read_text().strip()
source = root / 'dist/Luclid-ii'
if not (source / 'Luclid-ii').is_file():
    raise SystemExit('Build the Linux executable first: python packaging/build_native.py')
arch = subprocess.check_output(['dpkg', '--print-architecture'], text=True).strip()
stage = root / 'build/deb-stage'
if stage.exists():
    shutil.rmtree(stage)
app = stage / 'opt/luclid-ii'
shutil.copytree(source, app)
for f in app.rglob('*'):
    if f.is_file():
        f.chmod(0o755 if os.access(f, os.X_OK) else 0o644)
launcher = stage / 'usr/bin/luclid-ii'
launcher.parent.mkdir(parents=True)
launcher.write_text('#!/bin/sh\nexec /opt/luclid-ii/Luclid-ii "$@"\n')
launcher.chmod(0o755)
desktop = stage / 'usr/share/applications/luclid-ii.desktop'
desktop.parent.mkdir(parents=True)
desktop.write_text('[Desktop Entry]\nType=Application\nName=Luclid-ii\nComment=Local AI desktop assistant\nExec=/usr/bin/luclid-ii\nIcon=luclid-ii\nTerminal=false\nCategories=Utility;\n')
icon = stage / 'usr/share/icons/hicolor/256x256/apps/luclid-ii.png'
icon.parent.mkdir(parents=True)
shutil.copy2(root / 'src/local_muse/assets/lii_icon.png', icon)
control = stage / 'DEBIAN/control'
control.parent.mkdir()
control.write_text(f'Package: luclid-ii\nVersion: {version}\nSection: utils\nPriority: optional\nArchitecture: {arch}\nMaintainer: Luclid-ii maintainers <maintainer@example.invalid>\nDepends: libc6, libglib2.0-0, libx11-6, libxcb1, libxkbcommon0, libdbus-1-3\nDescription: Local AI desktop assistant\n Retro-inspired PySide6 application using a locally configured Ollama server.\n')
output = root / f'luclid-ii_{version}_{arch}.deb'
subprocess.check_call(['dpkg-deb', '--build', '--root-owner-group', str(stage), str(output)])
print(output)
