param([int]$Workers = 8)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python)) { throw "Project Python was not found: $Python" }

Write-Host "Executing the fully frozen Stage 2 release. This is the first target-outcome access."
& $Python (Join-Path $Root "analysis\run_multistage_battery_stage2_release.py") --workers $Workers
if ($LASTEXITCODE -ne 0) { throw "Stage 2 release is incomplete or non-evaluable; analysis was not run." }

& $Python (Join-Path $Root "analysis\run_multistage_battery_stage2_analysis.py")
if ($LASTEXITCODE -ne 0) { throw "Frozen Stage 2 analysis failed." }
