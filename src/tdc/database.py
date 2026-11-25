import sqlite3
from pathlib import Path

class Store:
    def __init__(self, path):
        self.path=Path(path); self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db: db.execute("CREATE TABLE IF NOT EXISTS processed (id TEXT PRIMARY KEY, source_url TEXT NOT NULL, processed_at TEXT DEFAULT CURRENT_TIMESTAMP)")
    def connect(self): return sqlite3.connect(self.path)
    def seen(self, key):
        with self.connect() as db: return db.execute("SELECT 1 FROM processed WHERE id=?", (key,)).fetchone() is not None
    def mark(self, key, url):
        with self.connect() as db: db.execute("INSERT OR IGNORE INTO processed(id,source_url) VALUES (?,?)",(key,url))
