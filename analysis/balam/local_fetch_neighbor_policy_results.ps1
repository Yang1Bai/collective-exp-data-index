$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$RemoteHostName = "yangbai@balam.scinet.utoronto.ca"
$RemoteArchive = "/scratch/yangbai/collective-exp-ood/analysis/results/neighbor_transfer_policy_balam_results.tar.gz"
$LocalArchive = Join-Path $env:TEMP "neighbor_transfer_policy_balam_results.tar.gz"

Push-Location $RepoRoot
try {
    Write-Host "Balam may request your password or interactive login. Do not paste it into chat."
    & scp "${RemoteHostName}:$RemoteArchive" $LocalArchive
    if ($LASTEXITCODE -ne 0) { throw "Result download failed; the job may still be running." }

    & tar.exe -xzf $LocalArchive -C $RepoRoot
    if ($LASTEXITCODE -ne 0) { throw "Result extraction failed." }

    & ".\.venv\Scripts\python.exe" "analysis\run_neighbor_transfer_policy_benchmark.py" "--validate-only"
    if ($LASTEXITCODE -ne 0) { throw "Local policy/input validation failed after download." }
    & ".\.venv\Scripts\python.exe" "analysis\verify_neighbor_transfer_policy_results.py"
    if ($LASTEXITCODE -ne 0) { throw "Downloaded policy result verification failed." }
    Write-Host "Neighborhood-transfer policy results downloaded to analysis/results."
}
finally {
    Pop-Location
}
