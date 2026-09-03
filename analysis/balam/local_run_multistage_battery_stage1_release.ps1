param(
    [int]$Workers = 8
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python)) {
    throw "Project virtual-environment Python was not found: $Python"
}

Write-Host "Releasing and extracting only the 141 frozen Stage 1 archives."
Write-Host "Stage 2 remains sealed. Completed archives are deleted after extraction."
& $Python (Join-Path $Root "analysis\run_multistage_battery_stage1_release.py") --workers $Workers
if ($LASTEXITCODE -ne 0) {
    throw "Stage 1 release is incomplete. Rerun this command to resume checkpoints."
}
