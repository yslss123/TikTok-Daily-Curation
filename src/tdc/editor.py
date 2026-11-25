import json, shutil, subprocess
from pathlib import Path
from datetime import date
from .models import Candidate

def build_compilation(items: list[Candidate], output_dir: Path, ffmpeg: str="ffmpeg", width: int=1080, height: int=1920, fps: int=30, clip_seconds: int=12) -> Path:
    if not items: raise ValueError("No authorized local videos available for compilation")
    if not shutil.which(ffmpeg) and not Path(ffmpeg).exists(): raise RuntimeError("FFmpeg not found. Install FFmpeg and add it to PATH.")
    day_dir = output_dir / date.today().isoformat(); work = day_dir / "_segments"
    work.mkdir(parents=True, exist_ok=True)
    segment_files = []
    for i, item in enumerate(items, 1):
        target = work / f"{i:02d}.mp4"
        cmd = [ffmpeg, "-y", "-i", str(item.local_path), "-t", str(clip_seconds), "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,fps={fps},format=yuv420p", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", str(target)]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        segment_files.append(target)
    concat = work / "concat.txt"
    concat.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in segment_files), encoding="utf-8")
    final = day_dir / "daily_best.mp4"
    subprocess.run([ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", str(final)], check=True, capture_output=True, text=True)
    manifest = [{"id":x.id,"title":x.title,"category":x.category,"source_url":x.source_url,"creator":x.creator,"license":x.license,"authorization_reference":x.authorization_reference,"score":x.score} for x in items]
    (day_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return final
