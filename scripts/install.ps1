$ErrorActionPreference = 'Stop'
if (-not (Get-Command python -ErrorAction SilentlyContinue)) { throw 'Python 3.11+ is required. Install from https://www.python.org/downloads/windows/' }
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
if (-not (Test-Path config.toml)) { Copy-Item config.example.toml config.toml }
New-Item -ItemType Directory -Force data, output, logs | Out-Null
Write-Host 'Install complete. Put authorized local MP4 files in media/ and edit data/candidates.json.'
