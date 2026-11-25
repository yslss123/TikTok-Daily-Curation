from dataclasses import dataclass
from pathlib import Path

@dataclass
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
    def from_dict(cls, r):
        return cls(str(r.get("id","")).strip(), str(r.get("title","")), str(r.get("category","")).lower(),
                   str(r.get("source_url","")), str(r.get("creator","")), int(r.get("views",0)),
                   int(r.get("likes",0)), int(r.get("comments",0)), int(r.get("shares",0)),
                   Path(str(r.get("local_path",""))), r.get("authorized") is True,
                   str(r.get("license","")).strip(), str(r.get("authorization_reference","")).strip())
