import json
from datetime import date
from pathlib import Path

from tdc.classifiers import KeywordClassifier
from tdc.database import Store
from tdc.models import Candidate
from tdc.providers import FileProvider, TikTokResearchApiProvider
from tdc.reports import write_daily_reports
from tdc.scoring import rank_candidates, select_editable


def candidate(tmp_path, **changes):
    data = {
        "id": "video-1",
        "title": "A hilarious comedy prank",
        "category": "",
        "source_url": "https://www.tiktok.com/video/1",
        "creator": "creator",
        "views": 120000,
        "likes": 10000,
        "comments": 500,
        "shares": 700,
        "local_path": "",
        "authorized": False,
        "license": "",
        "authorization_reference": "",
        "description": "funny prank",
        "hashtags": ["comedy"],
        "create_time": 0,
        "region": "US",
        "duration_seconds": 15,
        "discovery_source": "test",
    }
    data.update(changes)
    return Candidate.from_dict(data)


def test_keyword_classifier_categories(tmp_path):
    item = candidate(tmp_path, title="DIY creative craft tutorial", description="", hashtags=[])
    category, confidence = KeywordClassifier().classify(item)
    assert category == "creative"
    assert confidence > 0


def test_metadata_candidates_can_be_ranked_without_video_download(tmp_path):
    item = candidate(tmp_path)
    chosen = rank_candidates([item], max_items=20)
    assert [x.id for x in chosen] == ["video-1"]
    assert select_editable(chosen) == []


def test_authorized_local_asset_is_editable(tmp_path):
    local = tmp_path / "clip.mp4"
    local.write_bytes(b"test")
    item = candidate(
        tmp_path, local_path=str(local), authorized=True,
        license="Creator permission", authorization_reference="permission-123",
    )
    assert [x.id for x in select_editable([item])] == ["video-1"]


def test_csv_boolean_is_parsed(tmp_path):
    source = tmp_path / "candidates.csv"
    source.write_text(
        "id,title,category,source_url,authorized,license,authorization_reference,local_path\n"
        "a,funny,funny,https://example.com,true,permission,ref,clip.mp4\n",
        encoding="utf-8",
    )
    result = FileProvider(source).fetch()
    assert result[0].authorized is True


def test_store_curated_deduplication(tmp_path):
    store = Store(tmp_path / "state.sqlite3")
    assert not store.is_curated("video-1")
    store.mark_curated("video-1", date.today().isoformat())
    assert store.is_curated("video-1")


def test_daily_reports_write_json_csv_html(tmp_path):
    item = candidate(tmp_path)
    folder = write_daily_reports([item], tmp_path / "reports", date(2026, 1, 2))
    assert json.loads((folder / "selected.json").read_text(encoding="utf-8"))[0]["id"] == "video-1"
    assert (folder / "selected.csv").exists()
    page = (folder / "report.html").read_text(encoding="utf-8")
    assert "video-1" not in page
    assert "hilarious" in page


def test_research_api_requires_credentials():
    try:
        TikTokResearchApiProvider("", "", ["funny"])
    except RuntimeError as exc:
        assert "CLIENT_KEY" in str(exc)
    else:
        raise AssertionError("Expected missing credentials to fail")


def test_research_query_builds_keyword_and_region_filters():
    provider = TikTokResearchApiProvider(
        "client-key", "client-secret", ["funny", "beauty"], ["US", "GB"],
        start_date="20260101", end_date="20260110",
    )
    body = provider._query_body()
    assert len(body["query"]["or"]) == 2
    assert body["query"]["and"][0]["field_name"] == "region_code"
    assert body["max_count"] == 100
