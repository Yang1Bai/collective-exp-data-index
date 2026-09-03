$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$RemoteHostName = "yangbai@balam.scinet.utoronto.ca"
$RemoteArchive = "/scratch/yangbai/collective-exp-ood/analysis/results/optical_photocatalysis_development_balam_results.tar.gz"
$LocalArchive = Join-Path $env:TEMP "optical_photocatalysis_development_balam_results.tar.gz"

Push-Location $RepoRoot
try {
    Write-Host "Balam may request Duo login. Do not paste a passcode into chat."
    & scp "${RemoteHostName}:$RemoteArchive" $LocalArchive
    if ($LASTEXITCODE -ne 0) { throw "Result download failed." }
    & tar.exe -xzf $LocalArchive
    if ($LASTEXITCODE -ne 0) { throw "Result extraction failed." }

    $ChecksumPath = "analysis\results\optical_photocatalysis_development_checksums.sha256"
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
    & ".\.venv\Scripts\python.exe" `
        "analysis\verify_optical_photocatalysis_development_gate.py"
    if ($LASTEXITCODE -ne 0) {
        throw "Optical development semantic verification failed."
    }
    Write-Host "Optical development results downloaded and independently verified."
}
finally {
    Pop-Location
}
