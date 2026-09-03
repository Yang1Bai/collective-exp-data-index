param(
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$RemoteHostName = "yangbai@balam.scinet.utoronto.ca"
$RemoteRoot = "/scratch/yangbai/collective-exp-ood"
$PackageName = "mpea_provenance_specificity_package.tar.gz"
$PackagePath = Join-Path $env:TEMP $PackageName
$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"

Push-Location $RepoRoot
try {
    & $Python "-m" "py_compile" `
        "analysis\run_mpea_provenance_specificity.py" `
        "analysis\analyze_mpea_provenance_specificity.py" `
        "analysis\verify_mpea_provenance_specificity.py" `
        "analysis\recompute_caltech_static_ranking_inference.py" `
        "analysis\verify_caltech_static_ranking_inference.py"
    if ($LASTEXITCODE -ne 0) { throw "Python validation failed." }
    & $Python "-m" "json.tool" `
        "analysis\mpea_provenance_specificity_design.json" | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Frozen design is invalid." }
    foreach ($Line in Get-Content "analysis\mpea_provenance_specificity_implementation.sha256") {
        if ($Line -notmatch '^([0-9a-f]{64})  (.+)$') {
            throw "Invalid implementation checksum line: $Line"
        }
        $ExpectedHash = $Matches[1]
        $FrozenPath = $Matches[2]
        $ActualHash = (
            Get-FileHash -Algorithm SHA256 -LiteralPath $FrozenPath
        ).Hash.ToLowerInvariant()
        if ($ActualHash -ne $ExpectedHash) {
            throw "Frozen implementation changed: $FrozenPath"
        }
    }

    & $Python "analysis\verify_mpea_provenance_specificity.py" `
        "--output-prefix" "mpea_provenance_specificity_smoke" `
        "--require-inference"
    if ($LASTEXITCODE -ne 0) { throw "Local end-to-end smoke verification failed." }
    & $Python "analysis\verify_caltech_static_ranking_inference.py"
    if ($LASTEXITCODE -ne 0) { throw "Local Caltech correction verification failed." }

    if (Test-Path -LiteralPath $PackagePath) {
        Remove-Item -LiteralPath $PackagePath -Force
    }
    & tar.exe -czf $PackagePath `
        "analysis\common.py" `
        "analysis\run_knowledge_map.py" `
        "analysis\run_state_matched_mpea_borrowing_screen.py" `
        "analysis\MPEA_PROVENANCE_SPECIFICITY_PROTOCOL.md" `
        "analysis\mpea_provenance_specificity_design.json" `
        "analysis\mpea_provenance_specificity_implementation.sha256" `
        "analysis\run_mpea_provenance_specificity.py" `
        "analysis\analyze_mpea_provenance_specificity.py" `
        "analysis\verify_mpea_provenance_specificity.py" `
        "analysis\recompute_caltech_static_ranking_inference.py" `
        "analysis\verify_caltech_static_ranking_inference.py" `
        "analysis\results\caltech_ionic_external_policy_utility.csv" `
        "analysis\results\family_first_neighbor_portfolio_summary.json" `
        "analysis\balam\requirements.txt" `
        "analysis\balam\run_mpea_provenance_specificity_balam.sh" `
        "analysis\balam\prepare_and_submit_mpea_provenance_specificity.sh" `
        "scripts\localdb\build_localdb.py" `
        "data\collective.sqlite"
    if ($LASTEXITCODE -ne 0) { throw "Failed to create Balam package." }

    $PackageHash = (
        Get-FileHash -Algorithm SHA256 -LiteralPath $PackagePath
    ).Hash.ToLowerInvariant()
    $PackageSizeMB = [math]::Round((Get-Item $PackagePath).Length / 1MB, 2)
    Write-Host "Package SHA256: $PackageHash"
    Write-Host "Package size: $PackageSizeMB MB"
    if ($DryRun) {
        Write-Host "Dry run complete. Package was validated and not uploaded."
        return
    }

    Write-Host "Balam will request Duo login. Approve the push on your phone."
    & scp $PackagePath "${RemoteHostName}:~/$PackageName"
    if ($LASTEXITCODE -ne 0) { throw "Upload to Balam failed." }
    $RemoteCommand = "mkdir -p '$RemoteRoot' && mv ~/$PackageName '$RemoteRoot/$PackageName' && cd '$RemoteRoot' && tar --overwrite -xzf '$PackageName' && bash analysis/balam/prepare_and_submit_mpea_provenance_specificity.sh"
    & ssh $RemoteHostName $RemoteCommand
    if ($LASTEXITCODE -ne 0) { throw "Remote setup or submission failed." }
}
finally {
    Pop-Location
}
