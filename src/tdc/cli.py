import argparse, json, logging, tomllib
from pathlib import Path
from datetime import date
from .providers import FileProvider
from .scoring import select
from .database import Store
from .editor import build_compilation

def run(config_path: str):
    cfg = tomllib.loads(Path(config_path).read_text(encoding="utf-8"))
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", handlers=[logging.StreamHandler(), logging.FileHandler("tdc.log", encoding="utf-8")])
    p = cfg["paths"]; v = cfg["video"]; a = cfg["app"]
    store = Store(p["database"])
    candidates = FileProvider(p["candidates"]).fetch()
    fresh = [x for x in candidates if not store.seen(x.id)]
    chosen = select(fresh, a.get("min_items", 10), a.get("max_items", 20))
    if len(chosen) < a.get("min_items", 10): logging.warning("Only %d eligible videos; target minimum is %d. No fake entries will be added.", len(chosen), a.get("min_items", 10))
    result = build_compilation(chosen, Path(p["output_dir"]), v["ffmpeg"], v["width"], v["height"], v["fps"], v["clip_seconds"])
    for x in chosen: store.mark(x.id, x.source_url)
    logging.info("Created %s from %d videos", result, len(chosen))

def main():
    parser=argparse.ArgumentParser(description="Daily authorized short-video curation")
    parser.add_argument("--config", default="config.toml")
    args=parser.parse_args(); run(args.config)
if __name__ == "__main__": main()
