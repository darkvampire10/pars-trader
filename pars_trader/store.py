import json
import sqlite3
from pathlib import Path


class Store:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, timeout=10)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript('''
            CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS signals(id TEXT PRIMARY KEY, payload TEXT NOT NULL, created_at INTEGER NOT NULL);
        ''')
        self.db.commit()

    def get(self, key, default=None):
        row = self.db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else default

    def put(self, key, value):
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO settings VALUES (?,?)", (key,json.dumps(value)))

    def add_signal(self, key, payload, now):
        with self.db:
            cursor = self.db.execute("INSERT OR IGNORE INTO signals VALUES (?,?,?)", (key,json.dumps(payload),now))
            return cursor.rowcount == 1

    def recent(self):
        return [json.loads(r[0]) for r in self.db.execute("SELECT payload FROM signals ORDER BY created_at DESC LIMIT 5")]
