$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$RemoteHostName = "yangbai@balam.scinet.utoronto.ca"
$RemoteArchive = "/scratch/yangbai/collective-exp-ood/analysis/results/optical_photocatalysis_donor_balam_results.tar.gz"
$LocalArchive = Join-Path $env:TEMP "optical_photocatalysis_donor_balam_results.tar.gz"

Push-Location $RepoRoot
try {
    Write-Host "Balam may request Duo login. Do not paste a passcode into chat."
    & scp "${RemoteHostName}:$RemoteArchive" $LocalArchive
    if ($LASTEXITCODE -ne 0) { throw "Result download failed." }
    & tar.exe -xzf $LocalArchive
    if ($LASTEXITCODE -ne 0) { throw "Result extraction failed." }

    $ChecksumPath = "analysis\results\optical_photocatalysis_donor_checksums.sha256"
    if (-not (Test-Path -LiteralPath $ChecksumPath)) {
        throw "Downloaded checksum manifest is missing."
    }
    $Lines = Get-Content -LiteralPath $ChecksumPath
    foreach ($Line in $Lines) {
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
    & ".\.venv\Scripts\python.exe" `
        "analysis\verify_optical_photocatalysis_source_features.py"
    if ($LASTEXITCODE -ne 0) {
        throw "Optical donor semantic verification failed."
    }
    Write-Host "Optical donor results downloaded and independently verified."
}
finally {
    Pop-Location
}
