import json
from datetime import date

from tdc.cli import run


def test_cli_writes_daily_report_without_ffmpeg(tmp_path, monkeypatch):
    monkeypatch.delenv("AI_API_KEY", raising=False)
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    candidates = [{
        "id": "cli-1",
        "title": "Funny comedy sketch",
        "category": "",
        "source_url": "https://www.tiktok.com/video/cli-1",
        "creator": "sample",
        "views": 50000,
        "likes": 4000,
        "comments": 100,
        "shares": 200,
        "local_path": "",
        "authorized": False,
        "description": "funny comedy",
        "hashtags": ["sketch"],
    }]
    (data_dir / "candidates.json").write_text(json.dumps(candidates), encoding="utf-8")
    config = tmp_path / "config.toml"
    config.write_text(
        '[app]\nmin_items=1\nmax_items=10\n'
        '[paths]\ncandidates="data/candidates.json"\n'
        'database="data/state.sqlite3"\nreport_dir="reports"\n'
        'output_dir="output"\nlog_file="logs/tdc.log"\n'
        '[research_api]\nenabled=false\n'
        '[video]\nffmpeg="ffmpeg"\nwidth=1080\nheight=1920\nfps=30\nclip_seconds=12\n',
        encoding="utf-8",
    )
    selected = run(config)
    assert len(selected) == 1
    assert selected[0].category == "funny"
    report = tmp_path / "reports" / date.today().isoformat() / "selected.json"
    assert json.loads(report.read_text(encoding="utf-8"))[0]["id"] == "cli-1"
    assert (tmp_path / "logs" / "tdc.log").exists()
