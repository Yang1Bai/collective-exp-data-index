$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$RemoteHostName = "yangbai@balam.scinet.utoronto.ca"
$RemoteArchive = "/scratch/yangbai/collective-exp-ood/analysis/results/core_story_outcome_unseen_balam_results.tar.gz"
$LocalArchive = Join-Path $env:TEMP "core_story_outcome_unseen_balam_results.tar.gz"

Push-Location $RepoRoot
try {
    Write-Host "Balam may request Duo login. Do not paste a passcode into chat."
    & scp "${RemoteHostName}:$RemoteArchive" $LocalArchive
    if ($LASTEXITCODE -ne 0) { throw "Result download failed; the job may still be running." }
    & tar.exe -xzf $LocalArchive -C $RepoRoot
    if ($LASTEXITCODE -ne 0) { throw "Result extraction failed." }
    & ".\.venv\Scripts\python.exe" "analysis\verify_starrydata_reverse_transport_results.py" "--portable"
    if ($LASTEXITCODE -ne 0) { throw "Starrydata portable verification failed." }
    & ".\.venv\Scripts\python.exe" "analysis\verify_tri_oer_neighbor_results_amended.py" "--portable"
    if ($LASTEXITCODE -ne 0) { throw "TRI OER portable verification failed." }
    & ".\.venv\Scripts\python.exe" "analysis\synthesize_outcome_unseen_validation.py"
    if ($LASTEXITCODE -ne 0) { throw "Multi-target synthesis failed." }
    Write-Host "Core-story outcome-unseen results downloaded and independently verified."
}
finally {
    Pop-Location
}
