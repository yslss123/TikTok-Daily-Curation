import json
import sqlite3
from pathlib import Path


class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS processed "
                "(id TEXT PRIMARY KEY, source_url TEXT NOT NULL, processed_at TEXT DEFAULT CURRENT_TIMESTAMP)"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS candidates "
                "(id TEXT PRIMARY KEY, source_url TEXT NOT NULL, category TEXT NOT NULL, "
                "score REAL NOT NULL, payload_json TEXT NOT NULL, last_seen TEXT DEFAULT CURRENT_TIMESTAMP)"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS curated "
                "(id TEXT PRIMARY KEY, curated_date TEXT NOT NULL)"
            )

    def connect(self):
        return sqlite3.connect(self.path)

    def seen(self, key):
        with self.connect() as db:
            return db.execute("SELECT 1 FROM processed WHERE id=?", (key,)).fetchone() is not None

    def mark(self, key, url):
        with self.connect() as db:
            db.execute(
                "INSERT OR IGNORE INTO processed(id,source_url) VALUES (?,?)", (key, url)
            )

    def is_curated(self, key):
        with self.connect() as db:
            return db.execute("SELECT 1 FROM curated WHERE id=?", (key,)).fetchone() is not None

    def mark_curated(self, key, curated_date):
        with self.connect() as db:
            db.execute(
                "INSERT OR IGNORE INTO curated(id,curated_date) VALUES (?,?)",
                (key, curated_date),
            )

    def save_candidate(self, candidate):
        payload = json.dumps(candidate.to_record(), ensure_ascii=False)
        with self.connect() as db:
            db.execute(
                "INSERT INTO candidates(id,source_url,category,score,payload_json,last_seen) "
                "VALUES(?,?,?,?,?,CURRENT_TIMESTAMP) "
                "ON CONFLICT(id) DO UPDATE SET source_url=excluded.source_url, "
                "category=excluded.category, score=excluded.score, "
                "payload_json=excluded.payload_json, last_seen=CURRENT_TIMESTAMP",
                (candidate.id, candidate.source_url, candidate.category, candidate.score, payload),
            )
