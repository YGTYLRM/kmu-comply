# Registers a nightly Windows Scheduled Task that runs backup_nightly.py
# at 02:00 local time under the current user (no admin rights required).
#
# Usage (PowerShell):
#   cd backend\scripts
#   .\register_backup_task.ps1
#
# To remove:
#   schtasks /Delete /TN "Complio Nightly Backup" /F
#
# To run once immediately (test):
#   schtasks /Run /TN "Complio Nightly Backup"

$ErrorActionPreference = "Stop"

$backendDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$wrapper    = Join-Path $backendDir "scripts\run_nightly_backup.bat"

& schtasks.exe /Create /TN "Complio Nightly Backup" /TR "`"$wrapper`"" /SC DAILY /ST 02:00 /F
if ($LASTEXITCODE -ne 0) {
    throw "schtasks /Create failed with exit code $LASTEXITCODE"
}

Write-Host "Registered. Test with: schtasks /Run /TN `"Complio Nightly Backup`""
