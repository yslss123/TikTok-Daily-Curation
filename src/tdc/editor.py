import json, shutil, subprocess
from datetime import date
from pathlib import Path

def build(items, output_dir, cfg):
    if not items: raise ValueError("No authorized local videos available")
    ffmpeg=cfg["ffmpeg"]
    if not shutil.which(ffmpeg) and not Path(ffmpeg).exists(): raise RuntimeError("FFmpeg not found on PATH")
    folder=Path(output_dir)/date.today().isoformat(); work=folder/"segments"; work.mkdir(parents=True,exist_ok=True)
    parts=[]
    for i,c in enumerate(items,1):
        dst=work/f"{i:02d}.mp4"
        vf=f"scale={cfg['width']}:{cfg['height']}:force_original_aspect_ratio=decrease,pad={cfg['width']}:{cfg['height']}:(ow-iw)/2:(oh-ih)/2,fps={cfg['fps']},format=yuv420p"
        subprocess.run([ffmpeg,"-y","-i",str(c.local_path),"-t",str(cfg["clip_seconds"]),"-vf",vf,"-an","-c:v","libx264","-preset","veryfast","-crf","23",str(dst)],check=True,capture_output=True)
        parts.append(dst)
    listing=work/"concat.txt"
    listing.write_text("".join(f"file '{x.resolve().as_posix()}'\n" for x in parts),encoding="utf-8")
    final=folder/"daily_best.mp4"
    subprocess.run([ffmpeg,"-y","-f","concat","-safe","0","-i",str(listing),"-c","copy",str(final)],check=True,capture_output=True)
    manifest=[{"id":c.id,"title":c.title,"category":c.category,"source_url":c.source_url,"creator":c.creator,"license":c.license,"authorization_reference":c.authorization_reference,"score":c.score} for c in items]
    (folder/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    return final
