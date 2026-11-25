import csv
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .models import Candidate


class CandidateProvider:
    """Interface for permitted metadata sources. Implementations must respect source terms."""

    def fetch(self) -> list[Candidate]:
        raise NotImplementedError


class FileProvider(CandidateProvider):
    """Import candidate metadata from a JSON array or CSV file."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def fetch(self) -> list[Candidate]:
        if not self.path.exists():
            return []
        if self.path.suffix.lower() == ".csv":
            with self.path.open(encoding="utf-8-sig", newline="") as stream:
                rows = list(csv.DictReader(stream))
        else:
            with self.path.open(encoding="utf-8") as stream:
                rows = json.load(stream)
        if not isinstance(rows, list):
            raise ValueError("Candidate file must contain a JSON array or CSV rows")
        return [Candidate.from_dict(row) for row in rows]


class TikTokResearchApiProvider(CandidateProvider):
    """Approved TikTok Research API adapter; never downloads video media."""

    TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
    QUERY_URL = "https://open.tiktokapis.com/v2/research/video/query/"
    FIELDS = ",".join((
        "id", "video_description", "create_time", "region_code", "share_count",
        "view_count", "like_count", "comment_count", "hashtag_names", "username",
        "video_duration", "voice_to_text",
    ))

    def __init__(
        self,
        client_key: str,
        client_secret: str,
        keywords: list[str],
        regions: list[str] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        max_count: int = 100,
        max_pages: int = 2,
        timeout: int = 30,
    ):
        if not client_key or not client_secret:
            raise RuntimeError(
                "TikTok Research API is enabled but TIKTOK_RESEARCH_CLIENT_KEY / "
                "TIKTOK_RESEARCH_CLIENT_SECRET are missing."
            )
        self.client_key = client_key
        self.client_secret = client_secret
        self.keywords = [word.strip() for word in keywords if word.strip()]
        self.regions = [region.strip().upper() for region in (regions or []) if region.strip()]
        today = datetime.now(timezone.utc).date()
        self.end_date = end_date or today.strftime("%Y%m%d")
        self.start_date = start_date or (today - timedelta(days=7)).strftime("%Y%m%d")
        start = datetime.strptime(self.start_date, "%Y%m%d").date()
        end = datetime.strptime(self.end_date, "%Y%m%d").date()
        if start > end or (end - start).days > 30:
            raise ValueError("TikTok Research API date range must be ordered and no longer than 30 days.")
        self.max_count = max(1, min(int(max_count), 100))
        self.max_pages = max(1, min(int(max_pages), 10))
        self.timeout = timeout
        self._token: str | None = None

    def _json_request(self, request: Request) -> dict:
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"TikTok Research API HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise RuntimeError(f"Cannot reach TikTok Research API: {exc.reason}") from exc

    def _access_token(self) -> str:
        if self._token:
            return self._token
        body = urlencode({
            "client_key": self.client_key,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
        }).encode("utf-8")
        request = Request(
            self.TOKEN_URL,
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        payload = self._json_request(request)
        token = payload.get("access_token")
        if not token:
            raise RuntimeError(f"TikTok token request failed: {payload.get('error_description') or payload}")
        self._token = str(token)
        return self._token

    def _query_body(self, cursor: int | None = None, search_id: str | None = None) -> dict:
        conditions = [
            {"operation": "EQ", "field_name": "keyword", "field_values": [word]}
            for word in self.keywords
        ]
        query: dict = {"or": conditions} if conditions else {"and": [
            {"operation": "GTE", "field_name": "view_count", "field_values": ["1"]}
        ]}
        if self.regions:
            query.setdefault("and", []).append({
                "operation": "IN", "field_name": "region_code", "field_values": self.regions
            })
        body = {
            "query": query,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "max_count": self.max_count,
            "is_random": True,
        }
        if cursor is not None:
            body["cursor"] = cursor
        if search_id:
            body["search_id"] = search_id
        return body

    def fetch(self) -> list[Candidate]:
        token = self._access_token()
        results: list[Candidate] = []
        cursor = None
        search_id = None
        for _ in range(self.max_pages):
            url = f"{self.QUERY_URL}?{urlencode({'fields': self.FIELDS})}"
            request = Request(
                url,
                data=json.dumps(self._query_body(cursor, search_id)).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            payload = self._json_request(request)
            error = payload.get("error") or {}
            if error and error.get("code") not in ("ok", 0, None):
                raise RuntimeError(
                    f"TikTok Research API query failed: {error.get('code')} "
                    f"{error.get('message', '')} (log_id={error.get('log_id', '')})"
                )
            data = payload.get("data") or {}
            for video in data.get("videos", []):
                row = dict(video)
                row["discovery_source"] = "tiktok_research_api"
                # Research API returns metadata, not a downloadable video file or reuse licence.
                row["authorized"] = False
                row["local_path"] = ""
                row["license"] = ""
                row["authorization_reference"] = ""
                results.append(Candidate.from_dict(row))
            if not data.get("has_more"):
                break
            cursor = data.get("cursor")
            search_id = data.get("search_id")
            if cursor is None or not search_id:
                break
        return results
