import os
import sqlite3
from pathlib import Path


def db_path():
    base = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local" / "share")) / "LocalMuseAgent"
    base.mkdir(parents=True, exist_ok=True)
    return base / "history.sqlite3"


class History:
    """SQLite-backed independent conversations; upgrades the v0.4.0 database in place."""
    def __init__(self, path=None):
        self.path = str(path or db_path())
        with self._connect() as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY, role TEXT NOT NULL, content TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
            conn.execute("CREATE TABLE IF NOT EXISTS conversations (id INTEGER PRIMARY KEY, title TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
            cols = [row[1] for row in conn.execute("PRAGMA table_info(messages)")]
            if 'conversation_id' not in cols:
                conn.execute("ALTER TABLE messages ADD COLUMN conversation_id INTEGER NOT NULL DEFAULT 1")
            conn.execute("INSERT OR IGNORE INTO conversations(id,title) VALUES (1,'Chat 1')")
        self.current_id = 1

    def _connect(self):
        return sqlite3.connect(self.path, timeout=10)

    def conversations(self):
        with self._connect() as conn:
            return conn.execute('SELECT id,title FROM conversations ORDER BY id').fetchall()

    def create(self, title=None):
        with self._connect() as conn:
            cur=conn.execute('INSERT INTO conversations(title) VALUES (?)',(title or 'New Chat',))
            return cur.lastrowid

    def rename(self, cid, title):
        with self._connect() as conn:
            conn.execute('UPDATE conversations SET title=? WHERE id=?',(title,cid))

    def delete(self, cid):
        with self._connect() as conn:
            conn.execute('DELETE FROM messages WHERE conversation_id=?',(cid,))
            conn.execute('DELETE FROM conversations WHERE id=?',(cid,))

    def add(self, role, content, conversation_id=None):
        with self._connect() as conn:
            conn.execute('INSERT INTO messages(role,content,conversation_id) VALUES (?,?,?)',(role,content,conversation_id or self.current_id))

    def recent(self, limit=16, conversation_id=None):
        with self._connect() as conn:
            rows=conn.execute('SELECT role,content FROM messages WHERE conversation_id=? ORDER BY id DESC LIMIT ?', (conversation_id or self.current_id,limit)).fetchall()
        return [{'role':r,'content':c} for r,c in reversed(rows)]

    def all_with_dates(self, conversation_id=None):
        with self._connect() as conn:
            return conn.execute('SELECT role,content,created_at FROM messages WHERE conversation_id=? ORDER BY id',(conversation_id or self.current_id,)).fetchall()

    def all(self, conversation_id=None):
        with self._connect() as conn:
            return conn.execute('SELECT role,content FROM messages WHERE conversation_id=? ORDER BY id',(conversation_id or self.current_id,)).fetchall()

    def clear(self):
        with self._connect() as conn:
            conn.execute('DELETE FROM messages WHERE conversation_id=?',(self.current_id,))

    def close(self):
        pass
