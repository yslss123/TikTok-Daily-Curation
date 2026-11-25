from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path


def _as_int(value):
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def _as_bool(value):
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _as_list(value):
    if isinstance(value, list):
        return [str(item).strip().lstrip("#") for item in value if str(item).strip()]
    if isinstance(value, str):
        return [part.strip().lstrip("#") for part in value.replace(",", "|").split("|") if part.strip()]
    return []


def _as_epoch(value):
    if value in (None, ""):
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return int(datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp())
        except ValueError:
            return 0


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
    description: str = ""
    hashtags: list[str] = field(default_factory=list)
    create_time: int = 0
    region: str = ""
    duration_seconds: int = 0
    classification_confidence: float = 0.0
    classification_source: str = "import"
    discovery_source: str = "file"
    score: float = 0.0

    @classmethod
    def from_dict(cls, row: dict) -> "Candidate":
        video_id = str(row.get("id") or row.get("video_id") or "").strip()
        creator = str(row.get("creator") or row.get("username") or "").strip()
        source_url = str(row.get("source_url") or "").strip()
        if not source_url and video_id:
            source_url = f"https://www.tiktok.com/@{creator}/video/{video_id}" if creator else f"https://www.tiktok.com/video/{video_id}"
        description = str(row.get("description") or row.get("video_description") or row.get("title") or "")
        try:
            confidence = float(row.get("classification_confidence", 0.0) or 0.0)
        except (TypeError, ValueError):
            confidence = 0.0
        return cls(
            id=video_id,
            title=str(row.get("title") or row.get("video_description") or "").strip(),
            category=str(row.get("category") or "").lower().strip(),
            source_url=source_url,
            creator=creator,
            views=_as_int(row.get("views", row.get("view_count", 0))),
            likes=_as_int(row.get("likes", row.get("like_count", 0))),
            comments=_as_int(row.get("comments", row.get("comment_count", 0))),
            shares=_as_int(row.get("shares", row.get("share_count", 0))),
            local_path=Path(str(row.get("local_path") or "")),
            authorized=_as_bool(row.get("authorized", False)),
            license=str(row.get("license") or "").strip(),
            authorization_reference=str(row.get("authorization_reference") or "").strip(),
            description=description,
            hashtags=_as_list(row.get("hashtags", row.get("hashtag_names", []))),
            create_time=_as_epoch(row.get("create_time", row.get("created_at", 0))),
            region=str(row.get("region") or row.get("region_code") or "").upper(),
            duration_seconds=_as_int(row.get("duration_seconds", row.get("video_duration", 0))),
            classification_confidence=max(0.0, min(1.0, confidence)),
            classification_source=str(row.get("classification_source") or "import"),
            discovery_source=str(row.get("discovery_source") or "file"),
            score=float(row.get("score", 0.0) or 0.0),
        )

    def to_record(self) -> dict:
        record = asdict(self)
        record["local_path"] = str(self.local_path)
        return record
