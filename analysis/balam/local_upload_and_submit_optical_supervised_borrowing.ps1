param(
    [switch]$DryRun,
    [switch]$ResumeFromSource
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$RemoteHostName = "yangbai@balam.scinet.utoronto.ca"
$RemoteRoot = "/scratch/yangbai/collective-exp-ood"
$PackageName = "optical_supervised_borrowing_balam_package.tar.gz"
$PackagePath = Join-Path $env:TEMP $PackageName

Push-Location $RepoRoot
try {
    $RequiredFiles = @(
        "analysis\optical_photocatalysis_borrowing_design.json",
        "analysis\optical_supervised_borrowing_config.json",
        "analysis\OPTICAL_FOCUSED_METHOD_DECISION.md",
        "analysis\OPTICAL_SUPERVISED_BORROWING_PROTOCOL.md",
        "analysis\OPTICAL_SUPERVISED_VERIFIER_AMENDMENT.md",
        "analysis\prepare_optical_photocatalysis_donor_features.py",
        "analysis\prepare_optical_supervised_borrowing_scopes.py",
        "analysis\pretrain_optical_source_chemprop.py",
        "analysis\verify_optical_supervised_source_encoder.py",
        "analysis\run_optical_supervised_borrowing_development.py",
        "analysis\verify_optical_supervised_borrowing_development.py",
        "analysis\results\optical_photocatalysis_pair_audit.json",
        "analysis\results\optical_photocatalysis_target_metadata.csv",
        "analysis\results\optical_photocatalysis_donor_features.csv",
        "analysis\results\optical_transfer_method_discovery_draws.csv",
        "analysis\results\optical_supervised_borrowing_scopes.csv",
        "analysis\results\optical_supervised_borrowing_scopes_manifest.json",
        "analysis\balam\requirements.txt",
        "analysis\balam\requirements_optical_supervised.txt",
        "analysis\balam\run_optical_supervised_borrowing_balam.sh",
        "analysis\balam\prepare_and_submit_optical_supervised_borrowing.sh",
        "data\external\optical_photocatalysis\DB for chromophore_Sci_Data_rev02.csv",
        "data\external\optical_photocatalysis\SC-012-D1SC02150H-s005.csv",
        "tests\test_optical_supervised_borrowing.py"
    )
    foreach ($Path in $RequiredFiles) {
        if (-not (Test-Path -LiteralPath $Path)) {
            throw "Required focused input is missing: $Path"
        }
    }

    & ".\.venv\Scripts\python.exe" `
        "analysis\prepare_optical_supervised_borrowing_scopes.py" `
        "--jobs" "12"
    if ($LASTEXITCODE -ne 0) {
        throw "Outcome-independent OOD scope freeze failed."
    }
    $env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
    & ".\.venv\Scripts\python.exe" "-m" "pytest" `
        "tests\test_optical_supervised_borrowing.py" "-q"
    if ($LASTEXITCODE -ne 0) {
        throw "Focused optical borrowing tests failed."
    }

    if (Test-Path -LiteralPath $PackagePath) {
        Remove-Item -LiteralPath $PackagePath -Force
    }
    & tar.exe -czf $PackagePath @RequiredFiles
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create focused optical borrowing package."
    }
    $PackageHash = (
        Get-FileHash -Algorithm SHA256 -LiteralPath $PackagePath
    ).Hash.ToLowerInvariant()
    $PackageSizeMB = [math]::Round((Get-Item $PackagePath).Length / 1MB, 2)
    Write-Host "Package SHA256: $PackageHash"
    Write-Host "Package size: $PackageSizeMB MB"
    if ($DryRun) {
        Write-Host "Dry run complete. Package was not uploaded."
        return
    }

    Write-Host "Balam will request Duo login. Do not paste a passcode into chat."
    & scp $PackagePath "${RemoteHostName}:~/$PackageName"
    if ($LASTEXITCODE -ne 0) { throw "Upload to Balam failed." }
    $ResumePrefix = if ($ResumeFromSource) {
        "OPTICAL_RESUME_FROM_SOURCE=1 "
    }
    else {
        ""
    }
    $RemoteCommand = "mkdir -p '$RemoteRoot' && mv ~/$PackageName '$RemoteRoot/$PackageName' && cd '$RemoteRoot' && tar -xzf '$PackageName' && ${ResumePrefix}bash analysis/balam/prepare_and_submit_optical_supervised_borrowing.sh"
    & ssh $RemoteHostName $RemoteCommand
    if ($LASTEXITCODE -ne 0) {
        throw "Remote environment validation or submission failed."
    }
}
finally {
    Pop-Location
}
