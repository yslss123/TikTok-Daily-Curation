import csv, json
from pathlib import Path
from .models import Candidate

class CandidateProvider:
    def fetch(self):
        raise NotImplementedError

class FileProvider(CandidateProvider):
    def __init__(self, path): self.path = Path(path)
    def fetch(self):
        if not self.path.exists(): return []
        if self.path.suffix.lower() == ".csv":
            with self.path.open(encoding="utf-8-sig", newline="") as f: rows = list(csv.DictReader(f))
        else:
            with self.path.open(encoding="utf-8") as f: rows = json.load(f)
        if not isinstance(rows, list): raise ValueError("Expected JSON array or CSV rows")
        return [Candidate.from_dict(x) for x in rows]
