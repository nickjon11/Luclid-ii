"""Luclid-ii Chrome native messaging host (pairing-only preview).

The token is checked on every authenticated request. This host does not
communicate with the Luclid-ii desktop application or exchange resume data.
"""
import json
import os
import secrets
import struct
import sys
from pathlib import Path

HOST_NAME = 'com.luclid_ii.bridge'
STATE_DIR = Path.home() / '.config' / 'luclid-ii'
TOKEN_FILE = STATE_DIR / 'chrome_pairing_token'
MAX_BYTES = 65536


def read_message():
    header = sys.stdin.buffer.read(4)
    if not header:
        return None
    if len(header) != 4:
        raise ValueError('Incomplete native message header')
    length = struct.unpack('=I', header)[0]
    if length > MAX_BYTES:
        raise ValueError('Message exceeds allowed size')
    payload = sys.stdin.buffer.read(length)
    if len(payload) != length:
        raise ValueError('Incomplete native message')
    return json.loads(payload)


def reply(data):
    payload = json.dumps(data, separators=(',', ':')).encode('utf-8')
    sys.stdout.buffer.write(struct.pack('=I', len(payload)))
    sys.stdout.buffer.write(payload)
    sys.stdout.buffer.flush()


def ensure_token():
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    if not TOKEN_FILE.exists():
        token = secrets.token_urlsafe(32)
        try:
            fd = os.open(TOKEN_FILE, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            pass
        else:
            with os.fdopen(fd, 'w', encoding='utf-8') as stream:
                stream.write(token)
    return TOKEN_FILE.read_text(encoding='utf-8').strip()


def authenticated(message):
    token = message.get('token')
    return isinstance(token, str) and bool(token) and secrets.compare_digest(token, ensure_token())


def handle(message):
    if not isinstance(message, dict):
        return {'ok': False, 'error': 'Invalid request'}
    kind = message.get('type')
    if kind == 'ping':
        return {'ok': True, 'paired': authenticated(message), 'host': HOST_NAME,
                'desktop_connected': False}
    if kind == 'pair':
        valid = authenticated(message)
        return {'ok': valid, 'paired': valid, 'desktop_connected': False,
                'error': None if valid else 'Invalid pairing code'}
    return {'ok': False, 'error': 'Unsupported operation'}


def main():
    while True:
        try:
            message = read_message()
            if message is None:
                return
            reply(handle(message))
        except (ValueError, json.JSONDecodeError) as exc:
            reply({'ok': False, 'error': str(exc)})
            return


if __name__ == '__main__':
    main()
