$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$RemoteHostName = "yangbai@balam.scinet.utoronto.ca"
$RemoteArchive = "/scratch/yangbai/collective-exp-ood/analysis/results/starrydata_reverse_balam_results.tar.gz"
$LocalArchive = Join-Path $env:TEMP "starrydata_reverse_balam_results.tar.gz"

Push-Location $RepoRoot
try {
    Write-Host "Balam may request Duo login. Do not paste a passcode into chat."
    & scp "${RemoteHostName}:$RemoteArchive" $LocalArchive
    if ($LASTEXITCODE -ne 0) { throw "Result download failed; the job may still be running." }
    & tar.exe -xzf $LocalArchive -C $RepoRoot
    if ($LASTEXITCODE -ne 0) { throw "Result extraction failed." }
    & ".\.venv\Scripts\python.exe" "analysis\verify_starrydata_reverse_transport_results.py" "--portable"
    if ($LASTEXITCODE -ne 0) { throw "Downloaded Starrydata result verification failed." }
    Write-Host "Starrydata reverse-transport results downloaded and independently verified."
}
finally {
    Pop-Location
}
