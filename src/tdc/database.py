import sqlite3
from pathlib import Path

class Store:
    def __init__(self, path: str | Path):
        self.path = Path(path); self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS processed (id TEXT PRIMARY KEY, processed_at TEXT DEFAULT CURRENT_TIMESTAMP, source_url TEXT NOT NULL)''')
    def connect(self): return sqlite3.connect(self.path)
    def seen(self, item_id: str) -> bool:
        with self.connect() as db: return db.execute("SELECT 1 FROM processed WHERE id=?", (item_id,)).fetchone() is not None
    def mark(self, item_id: str, source_url: str):
        with self.connect() as db: db.execute("INSERT OR IGNORE INTO processed(id, source_url) VALUES (?,?)", (item_id, source_url))
