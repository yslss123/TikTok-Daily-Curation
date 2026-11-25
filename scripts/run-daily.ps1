$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
.\.venv\Scripts\python.exe -m tdc.cli --config config.toml
