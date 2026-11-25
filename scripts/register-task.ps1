param([string]$Time = '09:00')
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$root\scripts\run-daily.ps1`""
$trigger = New-ScheduledTaskTrigger -Daily -At $Time
Register-ScheduledTask -TaskName 'TikTokDailyCuration' -Action $action -Trigger $trigger -Description 'Build daily compilation from authorized local videos' -Force
Write-Host "Scheduled daily run at $Time"
