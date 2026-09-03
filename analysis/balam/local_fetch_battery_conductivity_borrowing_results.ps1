$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$RemoteHostName = "yangbai@balam.scinet.utoronto.ca"
$RemoteArchive = (
    "/scratch/yangbai/collective-exp-ood/analysis/results/" +
    "battery_conductivity_balam_results.tar.gz"
)
$LocalArchive = Join-Path `
    $env:TEMP "battery_conductivity_balam_results.tar.gz"

Push-Location $RepoRoot
try {
    Write-Host "Balam may request Duo login. Do not paste a passcode into chat."
    & scp "${RemoteHostName}:$RemoteArchive" $LocalArchive
    if ($LASTEXITCODE -ne 0) {
        throw "Battery borrowing result download failed."
    }
    & tar.exe -xzf $LocalArchive
    if ($LASTEXITCODE -ne 0) {
        throw "Battery borrowing result extraction failed."
    }

    $ChecksumPath = (
        "analysis\results\battery_conductivity_checksums.sha256"
    )
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
        "analysis\verify_battery_conductivity_source_cards.py"
    if ($LASTEXITCODE -ne 0) {
        throw "Battery source-card verification failed."
    }
    & ".\.venv\Scripts\python.exe" `
        "analysis\verify_battery_conductivity_borrowing.py"
    if ($LASTEXITCODE -ne 0) {
        throw "Battery borrowing semantic verification failed."
    }
    Get-Content -LiteralPath `
        "analysis\results\battery_conductivity_formal_summary.json"
    Write-Host (
        "Battery conductivity borrowing results downloaded and " +
        "independently verified."
    )
}
finally {
    Pop-Location
}

