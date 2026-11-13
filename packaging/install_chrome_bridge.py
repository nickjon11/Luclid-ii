"""Register pairing-only native messaging host for a user-loaded Chrome extension.

Run from the Luclid-ii repository root after loading browser_extension in Chrome.
"""
import argparse
import json
import os
import re
import stat
import sys
from pathlib import Path

HOST = 'com.luclid_ii.bridge'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--extension-id', required=True, help='32-character Chrome extension ID from chrome://extensions')
    args = parser.parse_args()
    if not re.fullmatch(r'[a-p]{32}', args.extension_id):
        parser.error('Invalid Chrome extension ID')
    root = Path(__file__).resolve().parents[1]
    host_script = root / 'packaging' / 'luclid_native_host.py'
    if not host_script.is_file():
        parser.error('Missing packaging/luclid_native_host.py')
    if sys.platform == 'win32':
        import winreg
        wrapper = root / 'packaging' / 'luclid_native_host.cmd'
        wrapper.write_text('@echo off\r\n"' + sys.executable + '" "' + str(host_script) + '"\r\n', encoding='utf-8')
        host_path = wrapper
        manifest_path = Path(os.environ['LOCALAPPDATA']) / 'Luclid-ii' / 'chrome_native_host.json'
    else:
        wrapper = root / 'packaging' / 'luclid_native_host.sh'
        wrapper.write_text('#!/bin/sh\nexec "' + sys.executable + '" "' + str(host_script) + '"\n', encoding='utf-8')
        wrapper.chmod(wrapper.stat().st_mode | stat.S_IXUSR)
        host_path = wrapper
        if sys.platform == 'darwin':
            manifest_path = Path.home() / 'Library/Application Support/Google/Chrome/NativeMessagingHosts' / (HOST + '.json')
        else:
            manifest_path = Path.home() / '.config/google-chrome/NativeMessagingHosts' / (HOST + '.json')
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = {'name': HOST, 'description': 'Luclid-ii pairing bridge', 'path': str(host_path.resolve()), 'type': 'stdio', 'allowed_origins': [f'chrome-extension://{args.extension_id}/']}
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    if sys.platform == 'win32':
        import winreg
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, 'Software\\Google\\Chrome\\NativeMessagingHosts\\' + HOST) as key:
            winreg.SetValueEx(key, '', 0, winreg.REG_SZ, str(manifest_path.resolve()))
    from luclid_native_host import ensure_token
    print('Native host registered:', manifest_path)
    print('Pairing code (keep private):', ensure_token())
    print('Restart Chrome, then paste the pairing code into the extension.')


if __name__ == '__main__':
    main()
