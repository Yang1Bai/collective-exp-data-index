$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$RemoteHostName = "yangbai@balam.scinet.utoronto.ca"
$RemoteArchive = (
    "/scratch/yangbai/collective-exp-ood/analysis/results/" +
    "strength_fatigue_ood_balam_results.tar.gz"
)
$LocalArchive = Join-Path `
    $env:TEMP "strength_fatigue_ood_balam_results.tar.gz"

Push-Location $RepoRoot
try {
    Write-Host "Balam may request Duo login. Approve the push on your phone."
    & scp "${RemoteHostName}:$RemoteArchive" $LocalArchive
    if ($LASTEXITCODE -ne 0) {
        throw "Strength/fatigue result download failed."
    }
    & tar.exe -xzf $LocalArchive
    if ($LASTEXITCODE -ne 0) {
        throw "Strength/fatigue result extraction failed."
    }

    $ChecksumPath = `
        "analysis\results\strength_fatigue_ood_checksums.sha256"
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
        "analysis\verify_strength_to_fatigue_results.py"
    if ($LASTEXITCODE -ne 0) {
        throw "Strength/fatigue semantic verification failed."
    }
    Get-Content -LiteralPath `
        "analysis\results\strength_fatigue_summary.json"
    Get-Content -LiteralPath `
        "analysis\results\strength_fatigue_VERIFIED.json"
    Write-Host (
        "Strength-to-fatigue OOD results downloaded and independently verified."
    )
}
finally {
    Pop-Location
}
