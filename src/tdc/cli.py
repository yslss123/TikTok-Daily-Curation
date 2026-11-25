import argparse, logging, tomllib
from pathlib import Path
from .providers import FileProvider
from .scoring import select
from .database import Store
from .editor import build

def run(config):
    cfg=tomllib.loads(Path(config).read_text(encoding="utf-8"))
    logging.basicConfig(level=logging.INFO,format="%(asctime)s %(levelname)s %(message)s")
    p,v,a=cfg["paths"],cfg["video"],cfg["app"]
    store=Store(p["database"])
    candidates=[c for c in FileProvider(p["candidates"]).fetch() if not store.seen(c.id)]
    chosen=select(candidates,a.get("max_items",20))
    if len(chosen)<a.get("min_items",10): logging.warning("Only %d eligible items; minimum target is %d",len(chosen),a.get("min_items",10))
    result=build(chosen,p["output_dir"],v)
    for c in chosen: store.mark(c.id,c.source_url)
    logging.info("Created %s (%d clips)",result,len(chosen))

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--config",default="config.toml")
    run(parser.parse_args().config)

if __name__=="__main__": main()
