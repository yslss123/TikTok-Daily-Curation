# TikTok Daily Curation

Windows-first daily discovery and curation of funny, beauty, creative and curiosity short-video metadata, with optional compilation of separately authorized local footage.

## Requirements
- Windows 10/11
- Python 3.11+ (tested by the project CI on Python 3.11; Python 3.13 is supported by the code)
- FFmpeg on PATH only when compiling local video files

## Install
```powershell
git clone https://github.com/yslss123/TikTok-Daily-Curation.git
cd TikTok-Daily-Curation
git checkout feature/discovery-ai-engine
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\install.ps1
Copy-Item .env.example .env
```

Edit `config.toml` and `.env` as needed. Keep real API credentials in `.env`; never commit it. The project loads simple `KEY=VALUE` entries from `.env` without overriding environment variables already set in PowerShell.

## Stage 2: discovery and ranking

The default source is `data/candidates.json` (JSON array) or CSV. The provider interface supports additional permitted sources. The pipeline classifies metadata into `funny`, `beauty`, `creative`, and `curiosity`, ranks candidates using reach, engagement, recency and classification confidence, deduplicates by video ID in SQLite, and writes:

- `reports/YYYY-MM-DD/selected.json`
- `reports/YYYY-MM-DD/selected.csv`
- `reports/YYYY-MM-DD/report.html`

Run:
```powershell
.\.venv\Scripts\python.exe -m tdc.cli --config config.toml
```

### Optional AI text classification

Set `AI_API_KEY` in `.env`. The classifier uses an OpenAI-compatible Chat Completions endpoint; customize `AI_BASE_URL` and `AI_MODEL` for a compatible provider. If no key is configured or the request fails, the deterministic keyword classifier is used.

**Important:** this AI step classifies title, description and hashtags only. It does not inspect the actual video frames. Visual classification requires a later stage with authorized local video assets and a vision model.

## Optional TikTok Research API source

TikTok Research API is not a general public trending feed available to every developer. Access requires an approved Research API project and the `research.data.basic` scope. Eligibility is limited to qualifying research organizations and approved non-commercial public-interest research proposals. See the [Research API eligibility page](https://developers.tiktok.com/products/research-api/) and [Query Videos API](https://developers.tiktok.com/docs/en/research-api-specs-query-videos).

After approval, put your Research API Client Key and Client Secret in `.env`:
```dotenv
TIKTOK_RESEARCH_CLIENT_KEY=your-approved-client-key
TIKTOK_RESEARCH_CLIENT_SECRET=your-approved-client-secret
```
Then set `research_api.enabled = true` in `config.toml`. The adapter obtains a short-lived client token, queries metadata, and supports pagination. TikTok's API returns metadata; it does **not** grant permission to download, edit, or republish the videos. The adapter never downloads video media.

The configured date range must be no longer than 30 days. The API returns up to 100 videos per page; use `max_pages` to limit requests.

## Optional compilation of authorized local files

Metadata discovery and media reuse rights are separate. Only candidates with a local file, `authorized = true`, a non-empty `license`, and an `authorization_reference` can be compiled.

```powershell
.\.venv\Scripts\python.exe -m tdc.cli --config config.toml --compile
```
FFmpeg must be installed and on PATH. The output MP4 is written to `output/YYYY-MM-DD/daily_best.mp4`. If no selected candidate has a properly authorized local file, compilation is skipped with a warning.

## Daily schedule
```powershell
.\scripts\register-task.ps1 -Time '09:00'
```
The scheduled task runs discovery and reports. To enable compilation in the scheduled task, edit `scripts/run-daily.ps1` and append `--compile`.

## Tests
```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

## Current limitations
- Without an approved Research API project or another permitted source, the app cannot automatically discover global TikTok trends; it works from imported metadata.
- The AI classifier analyzes text metadata, not video imagery.
- No automatic downloading of third-party TikTok videos, login automation, anti-bot bypass, or auto-publishing is implemented.
- The daily target is 10–20 candidates; if fewer eligible candidates are available, the report contains fewer entries rather than fabricating data.
