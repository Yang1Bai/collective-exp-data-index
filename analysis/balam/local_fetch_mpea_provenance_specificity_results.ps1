$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$RemoteHostName = "yangbai@balam.scinet.utoronto.ca"
$RemoteArchive = "/scratch/yangbai/collective-exp-ood/analysis/results/mpea_provenance_specificity_balam_results.tar.gz"
$LocalArchive = Join-Path $env:TEMP "mpea_provenance_specificity_balam_results.tar.gz"
$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"

Push-Location $RepoRoot
try {
    Write-Host "Balam may request Duo login. Approve the push on your phone."
    & scp "${RemoteHostName}:$RemoteArchive" $LocalArchive
    if ($LASTEXITCODE -ne 0) {
        throw "Result download failed; the job may still be running."
    }
    & tar.exe -xzf $LocalArchive -C $RepoRoot
    if ($LASTEXITCODE -ne 0) { throw "Result extraction failed." }
    & $Python "analysis\verify_mpea_provenance_specificity.py" `
        "--design-path" "analysis\mpea_provenance_specificity_design.json" `
        "--output-prefix" "mpea_provenance_specificity" `
        "--require-inference"
    if ($LASTEXITCODE -ne 0) {
        throw "Downloaded MPEA provenance-specificity verification failed."
    }
    & $Python "analysis\verify_caltech_static_ranking_inference.py"
    if ($LASTEXITCODE -ne 0) {
        throw "Downloaded Caltech corrective verification failed."
    }
    Write-Host "MPEA strengthening results downloaded and independently verified."
}
finally {
    Pop-Location
}
