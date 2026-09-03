$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$RemoteHostName = "yangbai@balam.scinet.utoronto.ca"
$RemoteArchive = "/scratch/yangbai/collective-exp-ood/analysis/results/caltech_ionic_external_policy_balam_results.tar.gz"
$LocalArchive = Join-Path $env:TEMP "caltech_ionic_external_policy_balam_results.tar.gz"

Push-Location $RepoRoot
try {
    Write-Host "Balam may request Duo login. Do not paste a passcode into chat."
    & scp "${RemoteHostName}:$RemoteArchive" $LocalArchive
    if ($LASTEXITCODE -ne 0) { throw "Result download failed; the job may still be running." }

    & tar.exe -xzf $LocalArchive -C $RepoRoot
    if ($LASTEXITCODE -ne 0) { throw "Result extraction failed." }

    & ".\.venv\Scripts\python.exe" "analysis\run_caltech_ionic_external_policy.py" "--validate-only"
    if ($LASTEXITCODE -ne 0) { throw "Local frozen-protocol validation failed after download." }
    & ".\.venv\Scripts\python.exe" "analysis\verify_caltech_ionic_external_policy_results.py" "--portable"
    if ($LASTEXITCODE -ne 0) { throw "Downloaded result verification failed." }
    Write-Host "Caltech external policy results downloaded and independently verified."
}
finally {
    Pop-Location
}
