"""Local job preferences and application tracking for Luclid-ii."""
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = Path.home() / '.luclid-ii' / 'job_agent.sqlite3'

class JobStore:
    def __init__(self, path=DB_PATH):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(path))
        self.db.execute('CREATE TABLE IF NOT EXISTS preferences (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
        self.db.execute('''CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'Saved',
            notes TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL)''')
        self.db.commit()

    def preferences(self):
        return {k: json.loads(v) for k, v in self.db.execute('SELECT key,value FROM preferences')}

    def save_preferences(self, values):
        with self.db:
            for key, value in values.items():
                self.db.execute('INSERT OR REPLACE INTO preferences(key,value) VALUES(?,?)', (key,json.dumps(value)))

    def add_job(self, url, title='', status='Saved'):
        if not url.startswith('https://'):
            raise ValueError('Only HTTPS job links are supported')
        with self.db:
            self.db.execute('''INSERT INTO jobs(url,title,status,updated_at) VALUES(?,?,?,?)
                ON CONFLICT(url) DO UPDATE SET title=CASE WHEN excluded.title != '' THEN excluded.title ELSE jobs.title END,
                updated_at=excluded.updated_at''', (url,title,status,datetime.now(timezone.utc).isoformat()))

    def jobs(self):
        return list(self.db.execute('SELECT id,title,url,status,notes FROM jobs ORDER BY updated_at DESC'))

    def set_status(self, job_id, status):
        if status not in ('Saved','Prepared','Applied','Interviewing','Rejected','Offered'):
            raise ValueError('Unsupported status')
        with self.db:
            self.db.execute('UPDATE jobs SET status=?, updated_at=? WHERE id=?',
                            (status,datetime.now(timezone.utc).isoformat(),job_id))

    def close(self):
        self.db.close()
