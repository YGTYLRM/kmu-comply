# Registers a Windows Scheduled Task that runs canary_check.py daily at
# 06:00 local time under the current user (no admin rights required).
#
# Same caveat as register_backup_task.ps1: this schedules the check on
# THIS machine, as a stand-in until a real production host exists. Once a
# deploy target is chosen, wire canary_check.py into that host's own
# scheduler (cron, systemd timer, etc.) instead — this script is not itself
# portable to a Linux deploy target.
#
# Usage (PowerShell):
#   cd backend\scripts
#   .\register_canary_task.ps1
#
# To remove:
#   schtasks /Delete /TN "Complio pgvector Canary" /F
#
# To run once immediately (test):
#   schtasks /Run /TN "Complio pgvector Canary"

$ErrorActionPreference = "Stop"

$backendDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$wrapper    = Join-Path $backendDir "scripts\run_canary_check.bat"

& schtasks.exe /Create /TN "Complio pgvector Canary" /TR "`"$wrapper`"" /SC DAILY /ST 06:00 /F
if ($LASTEXITCODE -ne 0) {
    throw "schtasks /Create failed with exit code $LASTEXITCODE"
}

Write-Host "Registered. Test with: schtasks /Run /TN `"Complio pgvector Canary`""
