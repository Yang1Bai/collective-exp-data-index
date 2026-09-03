$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$RemoteHostName = "yangbai@balam.scinet.utoronto.ca"
$RemoteArchive = "/scratch/yangbai/collective-exp-ood/analysis/results/state_matched_mpea_balam_v2_results.tar.gz"
$LocalArchive = Join-Path $env:TEMP "state_matched_mpea_balam_v2_results.tar.gz"

Push-Location $RepoRoot
try {
    Write-Host "Balam may request Duo login. Do not paste a passcode into chat."
    & scp "${RemoteHostName}:$RemoteArchive" $LocalArchive
    if ($LASTEXITCODE -ne 0) {
        throw "V2 result download failed; the job may still be running."
    }
    & tar.exe -xzf $LocalArchive -C $RepoRoot
    if ($LASTEXITCODE -ne 0) { throw "V2 result extraction failed." }
    & ".\.venv\Scripts\python.exe" "analysis\verify_state_matched_mpea_balam.py" `
        "--design-path" "analysis\state_matched_mpea_balam_design_v2.json" `
        "--input-prefix" "state_matched_mpea_balam_v2" `
        "--output-prefix" "state_matched_mpea_balam_v2"
    if ($LASTEXITCODE -ne 0) {
        throw "Downloaded state-matched MPEA V2 verification failed."
    }
    Write-Host "State-matched MPEA V2 results downloaded and independently verified."
}
finally {
    Pop-Location
}
