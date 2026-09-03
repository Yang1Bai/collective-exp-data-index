$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$RemoteHostName = "yangbai@balam.scinet.utoronto.ca"
$RemoteArchive = "/scratch/yangbai/collective-exp-ood/analysis/results/multi_target_ood_balam_results.tar.gz"
$LocalArchive = Join-Path $env:TEMP "multi_target_ood_balam_results.tar.gz"

Push-Location $RepoRoot
try {
    Write-Host "Balam may request Duo login. Do not paste a passcode into chat."
    & scp "${RemoteHostName}:$RemoteArchive" $LocalArchive
    if ($LASTEXITCODE -ne 0) {
        throw "Result download failed; the job may still be running."
    }
    & tar.exe -xzf $LocalArchive -C $RepoRoot
    if ($LASTEXITCODE -ne 0) { throw "Result extraction failed." }
    & ".\.venv\Scripts\python.exe" "analysis\verify_multi_target_ood_borrowing.py"
    if ($LASTEXITCODE -ne 0) {
        throw "Downloaded multi-target OOD result verification failed."
    }
    Write-Host "Multi-target OOD results downloaded and independently verified."
}
finally {
    Pop-Location
}
