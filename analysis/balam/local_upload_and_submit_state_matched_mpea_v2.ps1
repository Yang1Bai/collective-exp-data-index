param(
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$RemoteHostName = "yangbai@balam.scinet.utoronto.ca"
$RemoteRoot = "/scratch/yangbai/collective-exp-ood"
$PackageName = "state_matched_mpea_balam_v2_package.tar.gz"
$PackagePath = Join-Path $env:TEMP $PackageName

Push-Location $RepoRoot
try {
    & ".\.venv\Scripts\python.exe" "-m" "py_compile" `
        "analysis\run_state_matched_mpea_borrowing_screen.py" `
        "analysis\analyze_state_matched_mpea_balam_bootstrap.py" `
        "analysis\verify_state_matched_mpea_balam.py"
    if ($LASTEXITCODE -ne 0) { throw "Python validation failed." }
    & ".\.venv\Scripts\python.exe" "-m" "json.tool" `
        "analysis\state_matched_mpea_balam_design_v2.json" | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Frozen V2 design is invalid." }

    if (Test-Path $PackagePath) {
        Remove-Item -LiteralPath $PackagePath -Force
    }
    & tar.exe -czf $PackagePath `
        "analysis\common.py" `
        "analysis\run_knowledge_map.py" `
        "analysis\run_state_matched_mpea_borrowing_screen.py" `
        "analysis\analyze_state_matched_mpea_balam_bootstrap.py" `
        "analysis\verify_state_matched_mpea_balam.py" `
        "analysis\STATE_MATCHED_MPEA_BORROWING_PROTOCOL.md" `
        "analysis\STATE_MATCHED_MPEA_CONTROL_AMENDMENT_V2.md" `
        "analysis\state_matched_mpea_balam_design_v2.json" `
        "analysis\balam\requirements.txt" `
        "analysis\balam\run_state_matched_mpea_balam_v2.sh" `
        "analysis\balam\prepare_and_submit_state_matched_mpea_v2.sh" `
        "scripts\localdb\build_localdb.py" `
        "data\collective.sqlite"
    if ($LASTEXITCODE -ne 0) { throw "Failed to create V2 Balam package." }

    $PackageHash = (
        Get-FileHash -Algorithm SHA256 -LiteralPath $PackagePath
    ).Hash.ToLowerInvariant()
    $PackageSizeMB = [math]::Round((Get-Item $PackagePath).Length / 1MB, 2)
    Write-Host "Package SHA256: $PackageHash"
    Write-Host "Package size: $PackageSizeMB MB"
    if ($DryRun) {
        Write-Host "Dry run complete. V2 package was validated and not uploaded."
        return
    }

    Write-Host "Balam will request Duo login. Do not paste a passcode into chat."
    & scp $PackagePath "${RemoteHostName}:~/$PackageName"
    if ($LASTEXITCODE -ne 0) { throw "Upload to Balam failed." }
    $RemoteCommand = "mkdir -p '$RemoteRoot' && mv ~/$PackageName '$RemoteRoot/$PackageName' && cd '$RemoteRoot' && tar -xzf '$PackageName' && bash analysis/balam/prepare_and_submit_state_matched_mpea_v2.sh"
    & ssh $RemoteHostName $RemoteCommand
    if ($LASTEXITCODE -ne 0) { throw "Remote setup or submission failed." }
}
finally {
    Pop-Location
}
