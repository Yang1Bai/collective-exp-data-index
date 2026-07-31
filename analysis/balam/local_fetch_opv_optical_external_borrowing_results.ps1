$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$RemoteHostName = "yangbai@balam.scinet.utoronto.ca"
$RemoteArchive = "/scratch/yangbai/collective-exp-ood/analysis/results/opv_optical_external_balam_results.tar.gz"
$LocalArchive = Join-Path $env:TEMP "opv_optical_external_balam_results.tar.gz"

Push-Location $RepoRoot
try {
    Write-Host "Balam may request Duo login. Do not paste a passcode into chat."
    & scp "${RemoteHostName}:$RemoteArchive" $LocalArchive
    if ($LASTEXITCODE -ne 0) { throw "Result download failed." }
    & tar.exe -xzf $LocalArchive
    if ($LASTEXITCODE -ne 0) { throw "Result extraction failed." }

    $ChecksumPath = "analysis\results\opv_optical_external_checksums.sha256"
    foreach ($Line in Get-Content -LiteralPath $ChecksumPath) {
        if ($Line -notmatch '^([0-9a-f]{64})\s+(.+)$') {
            throw "Invalid checksum line: $Line"
        }
        $Expected = $Matches[1]
        $Path = $Matches[2].Trim()
        $Actual = (
            Get-FileHash -Algorithm SHA256 -LiteralPath $Path
        ).Hash.ToLowerInvariant()
        if ($Actual -ne $Expected) {
            throw "Checksum mismatch for $Path"
        }
    }

    $SourceSummary = Get-Content -Raw -LiteralPath `
        "analysis\results\opv_optical_source_summary.json" |
        ConvertFrom-Json
    if ($SourceSummary.status -ne "strict-source-features-ready") {
        throw "Strict target-excluded optical source feature gate failed."
    }
    & ".\.venv\Scripts\python.exe" `
        "analysis\verify_opv_optical_external_borrowing.py" `
        "--mode" "formal"
    if ($LASTEXITCODE -ne 0) {
        throw "Formal optical-to-OPV semantic verification failed."
    }
    Get-Content -LiteralPath `
        "analysis\results\opv_optical_external_formal_summary.json"
    Write-Host "Optical-to-OPV results downloaded and independently verified."
}
finally {
    Pop-Location
}
