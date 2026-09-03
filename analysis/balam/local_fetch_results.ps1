$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$RemoteHostName = "yangbai@balam.scinet.utoronto.ca"
$RemoteArchive = "/scratch/yangbai/collective-exp-ood/analysis/results/obelix_ood_discovery_balam_results.tar.gz"
$LocalArchive = Join-Path $env:TEMP "obelix_ood_discovery_balam_results.tar.gz"

Push-Location $RepoRoot
try {
    Write-Host "Balam may request your password or interactive login. Do not paste it into chat."
    & scp "${RemoteHostName}:$RemoteArchive" $LocalArchive
    if ($LASTEXITCODE -ne 0) { throw "Result download failed; the job may still be running." }

    & tar.exe -xzf $LocalArchive -C $RepoRoot
    if ($LASTEXITCODE -ne 0) { throw "Result extraction failed." }

    & ".\.venv\Scripts\python.exe" "analysis\run_obelix_ood_discovery.py" "--validate-only"
    if ($LASTEXITCODE -ne 0) { throw "Local frozen-input validation failed after download." }
    & ".\.venv\Scripts\python.exe" "analysis\verify_obelix_ood_discovery_results.py"
    if ($LASTEXITCODE -ne 0) { throw "Downloaded campaign result verification failed." }
    Write-Host "Balam results downloaded to analysis/results."
}
finally {
    Pop-Location
}
