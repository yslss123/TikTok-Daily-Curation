$ErrorActionPreference='Stop'
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
if (!(Test-Path config.toml)) { Copy-Item config.example.toml config.toml }
New-Item -ItemType Directory -Force data,output,media | Out-Null
Write-Host 'Install complete. Add authorized local clips and data/candidates.json.'
