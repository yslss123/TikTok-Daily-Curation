import csv, json
from pathlib import Path
from .models import Candidate

class CandidateProvider:
    """Pluggable provider contract. Implementations must use permitted data sources."""
    def fetch(self) -> list[Candidate]:
        raise NotImplementedError

class FileProvider(CandidateProvider):
    def __init__(self, path: str | Path): self.path = Path(path)
    def fetch(self) -> list[Candidate]:
        if not self.path.exists(): return []
        if self.path.suffix.lower() == ".csv":
            with self.path.open(encoding="utf-8-sig", newline="") as f: rows = list(csv.DictReader(f))
        else:
            with self.path.open(encoding="utf-8") as f: rows = json.load(f)
        if not isinstance(rows, list): raise ValueError("Candidate file must contain a JSON array or CSV rows")
        return [Candidate.from_dict(row) for row in rows]
