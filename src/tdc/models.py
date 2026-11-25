from dataclasses import dataclass
from pathlib import Path

@dataclass(slots=True)
class Candidate:
    id: str
    title: str
    category: str
    source_url: str
    creator: str
    views: int
    likes: int
    comments: int
    shares: int
    local_path: Path
    authorized: bool
    license: str
    authorization_reference: str
    score: float = 0.0

    @classmethod
    def from_dict(cls, row: dict) -> "Candidate":
        return cls(
            id=str(row.get("id", "")).strip(), title=str(row.get("title", "")).strip(),
            category=str(row.get("category", "")).lower().strip(),
            source_url=str(row.get("source_url", "")).strip(), creator=str(row.get("creator", "")).strip(),
            views=max(0, int(row.get("views", 0))), likes=max(0, int(row.get("likes", 0))),
            comments=max(0, int(row.get("comments", 0))), shares=max(0, int(row.get("shares", 0))),
            local_path=Path(str(row.get("local_path", ""))), authorized=row.get("authorized") is True,
            license=str(row.get("license", "")).strip(),
            authorization_reference=str(row.get("authorization_reference", "")).strip())
