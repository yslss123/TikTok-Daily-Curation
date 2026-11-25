import csv
import html
import json
from datetime import date
from pathlib import Path


def write_daily_reports(candidates, output_dir, report_date: date | None = None):
    day = report_date or date.today()
    folder = Path(output_dir) / day.isoformat()
    folder.mkdir(parents=True, exist_ok=True)
    records = [candidate.to_record() for candidate in candidates]
    (folder / "selected.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    csv_path = folder / "selected.csv"
    fields = [
        "id", "title", "category", "score", "views", "likes", "comments", "shares",
        "creator", "region", "create_time", "source_url", "discovery_source",
        "classification_source", "classification_confidence", "local_path",
        "authorized", "license", "authorization_reference",
    ]
    with csv_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            writer.writerow(record)
    rows = []
    for item in candidates:
        title = html.escape(item.title or "(untitled)")
        category = html.escape(item.category)
        creator = html.escape(item.creator)
        url = html.escape(item.source_url, quote=True)
        rows.append(
            f'<tr><td>{category}</td><td><a href="{url}" target="_blank" rel="noopener">{title}</a></td>'
            f'<td>{creator}</td><td>{item.views:,}</td><td>{item.score:.3f}</td></tr>'
        )
    page = (
        "<!doctype html><html lang='zh-CN'><meta charset='utf-8'>"
        f"<title>Daily Curation {day.isoformat()}</title><body>"
        f"<h1>每日精选候选 · {day.isoformat()}</h1><p>共 {len(candidates)} 条；此报告包含元数据候选，不代表已获得视频下载或二次使用许可。</p>"
        "<table border='1' cellpadding='6'><thead><tr><th>分类</th><th>视频</th><th>作者</th><th>播放量</th><th>评分</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table></body></html>"
    )
    (folder / "report.html").write_text(page, encoding="utf-8")
    return folder
