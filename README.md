# TikTok Daily Curation

Windows-first daily curation of funny, beauty, creative and curiosity short videos.

## Important data-source limitation
TikTok does not offer a general unrestricted global trending API to every developer. Research API access is eligibility/approval-based. This first release uses an importable JSON/CSV provider and a pluggable provider contract; it does not bypass login, anti-bot controls, or download restrictions. It does not claim to scrape global trends.

Only local footage with explicit authorization, a license description, and an authorization reference is eligible for editing. Public metadata discovery and rights to download/reuse video are separate permissions.

## Requirements
- Windows 10/11
- Python 3.11+
- FFmpeg on PATH

## Install
```powershell
git clone https://github.com/yslss123/TikTok-Daily-Curation.git
cd TikTok-Daily-Curation
git checkout feature/initial-implementation
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\install.ps1
```

Copy authorized MP4 files into `media/`, copy `data/candidates.example.json` to `data/candidates.json`, then edit the metadata. Categories: `funny`, `beauty`, `creative`, `curiosity`.

## Run and schedule
```powershell
.\.venv\Scripts\python.exe -m tdc.cli --config config.toml
.\scripts\register-task.ps1 -Time '09:00'
```
Output: `output/YYYY-MM-DD/daily_best.mp4` and `manifest.json`. Selects up to 20 unseen eligible videos and warns when fewer than 10 exist; it never fabricates items.

## Current scope
Implemented: JSON/CSV import provider, engagement scoring, authorization checks, SQLite de-duplication, FFmpeg vertical compilation, manifest, Windows scripts and tests.
Not implemented: automatic TikTok browsing/downloading, AI vision analysis, subtitles or auto-publishing. Add an approved source by implementing `CandidateProvider.fetch()`.
