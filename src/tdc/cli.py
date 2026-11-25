import argparse
import logging
import os
import tomllib
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from .classifiers import CATEGORIES, build_classifier
from .database import Store
from .editor import build
from .providers import FileProvider, TikTokResearchApiProvider
from .reports import write_daily_reports
from .scoring import rank_candidates, select_editable


def load_env_file(path: Path):
    """Load simple KEY=VALUE entries without overriding existing process variables."""
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _make_providers(config):
    paths = config["paths"]
    providers = [FileProvider(paths["candidates"])]
    research = config.get("research_api", {})
    if research.get("enabled", False):
        client_key = os.getenv("TIKTOK_RESEARCH_CLIENT_KEY", "").strip()
        client_secret = os.getenv("TIKTOK_RESEARCH_CLIENT_SECRET", "").strip()
        end = datetime.now(timezone.utc).date()
        start = end - timedelta(days=int(research.get("start_days_ago", 7)))
        providers.append(TikTokResearchApiProvider(
            client_key=client_key,
            client_secret=client_secret,
            keywords=research.get("keywords", []),
            regions=research.get("regions", []),
            start_date=research.get("start_date") or start.strftime("%Y%m%d"),
            end_date=research.get("end_date") or end.strftime("%Y%m%d"),
            max_count=research.get("max_count", 100),
            max_pages=research.get("max_pages", 2),
        ))
    return providers


def run(config_path="config.toml", compile_videos=False):
    config_file = Path(config_path).resolve()
    load_env_file(config_file.parent / ".env")
    config = tomllib.loads(config_file.read_text(encoding="utf-8"))
    paths = config["paths"]
    log_path = Path(paths.get("log_file", "logs/tdc.log"))
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_path, encoding="utf-8"),
        ],
        force=True,
    )
    app = config.get("app", {})
    min_items = int(app.get("min_items", 10))
    max_items = int(app.get("max_items", 20))
    if min_items < 1 or max_items < min_items or max_items > 20:
        raise ValueError("Configure 1 <= min_items <= max_items <= 20.")

    store = Store(paths["database"])
    candidates = []
    for provider in _make_providers(config):
        fetched = provider.fetch()
        logging.info("%s: fetched %d candidate records", provider.__class__.__name__, len(fetched))
        candidates.extend(fetched)

    # Deduplicate merged providers by stable video ID; keep the first source record.
    merged = {}
    for candidate in candidates:
        if candidate.id:
            merged.setdefault(candidate.id, candidate)

    classifier = build_classifier()
    for candidate in merged.values():
        if candidate.category not in CATEGORIES:
            category, confidence = classifier.classify(candidate)
            candidate.category = category
            candidate.classification_confidence = confidence
            candidate.classification_source = classifier.name
        elif candidate.classification_confidence <= 0:
            candidate.classification_confidence = 0.65
            candidate.classification_source = candidate.classification_source or "provided"

    all_candidates = list(merged.values())
    for candidate in all_candidates:
        store.save_candidate(candidate)

    fresh = [item for item in all_candidates if not store.is_curated(item.id)]
    selected = rank_candidates(fresh, max_items=max_items)
    report_folder = write_daily_reports(selected, paths.get("report_dir", "reports"))
    for candidate in selected:
        store.mark_curated(candidate.id, date.today().isoformat())

    logging.info("Daily report created: %s (%d selected)", report_folder, len(selected))
    if len(selected) < min_items:
        logging.warning(
            "Only %d eligible candidates; target minimum is %d. No entries were fabricated.",
            len(selected), min_items,
        )

    if compile_videos:
        editable = select_editable(selected, max_items=max_items)
        if not editable:
            logging.warning(
                "No selected candidate has a local file plus explicit reuse authorization; "
                "skipping MP4 compilation. Metadata discovery does not grant media reuse rights."
            )
        else:
            result = build(editable, paths["output_dir"], config["video"])
            logging.info("Authorized compilation created: %s", result)
    return selected


def main():
    parser = argparse.ArgumentParser(description="Discover, classify and rank permitted short-video metadata.")
    parser.add_argument("--config", default="config.toml")
    parser.add_argument("--compile", action="store_true", help="Compile only selected local files with documented reuse authorization.")
    args = parser.parse_args()
    run(args.config, compile_videos=args.compile)


if __name__ == "__main__":
    main()
