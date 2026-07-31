param(
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$RemoteHostName = "yangbai@balam.scinet.utoronto.ca"
$RemoteRoot = "/scratch/yangbai/collective-exp-ood"
$PackageName = "opv_optical_external_balam_package.tar.gz"
$PackagePath = Join-Path $env:TEMP $PackageName

Push-Location $RepoRoot
try {
    $RequiredFiles = @(
        "analysis\opv_optical_external_borrowing_design.json",
        "analysis\opv_optical_implementation_freeze.json",
        "analysis\OPV_OPTICAL_EXTERNAL_BORROWING_PROTOCOL.md",
        "analysis\OPV_OPTICAL_PORTABLE_ZIP_AMENDMENT.md",
        "analysis\OPV_OPTICAL_PREOUTCOME_IMPLEMENTATION_ALIGNMENT_AMENDMENT.md",
        "analysis\audit_opv_optical_external_pair.py",
        "analysis\prepare_opv_optical_draws.py",
        "analysis\prepare_opv_optical_source_features.py",
        "analysis\preflight_opv_optical_external_borrowing.py",
        "analysis\run_opv_optical_external_borrowing.py",
        "analysis\summarize_opv_optical_external_borrowing.py",
        "analysis\verify_opv_optical_external_borrowing.py",
        "analysis\prepare_optical_photocatalysis_donor_features.py",
        "analysis\pretrain_optical_source_chemprop.py",
        "analysis\optical_supervised_borrowing_config.json",
        "analysis\results\opv_optical_external_pair_audit.json",
        "analysis\results\opv_optical_target_metadata_no_outcomes.csv",
        "analysis\results\opv_optical_label_draws.csv",
        "analysis\results\opv_optical_label_draws_manifest.json",
        "analysis\results\optical_supervised_source_summary.json",
        "analysis\results\optical_supervised_source_VERIFIED.json",
        "analysis\balam\requirements.txt",
        "analysis\balam\requirements_opv_optical.txt",
        "analysis\balam\run_opv_optical_external_borrowing_balam.sh",
        "analysis\balam\prepare_and_submit_opv_optical_external_borrowing.sh",
        "data\external\optical_photocatalysis\DB for chromophore_Sci_Data_rev02.csv",
        "data\external\opv_borrowing\opvdb.zip",
        "tests\test_opv_optical_external_borrowing.py"
    )
    $Freeze = Get-Content -Raw -LiteralPath `
        "analysis\opv_optical_implementation_freeze.json" |
        ConvertFrom-Json
    foreach ($CheckpointName in $Freeze.solid_source_checkpoint_sha256.PSObject.Properties.Name) {
        $RequiredFiles += (
            "analysis\results\optical_supervised_source_checkpoints\" +
            $CheckpointName
        )
    }
    foreach ($Path in $RequiredFiles) {
        if (-not (Test-Path -LiteralPath $Path)) {
            throw "Required OPV borrowing input is missing: $Path"
        }
    }

    $env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
    & ".\.venv\Scripts\python.exe" "-m" "pytest" `
        "tests\test_opv_optical_external_borrowing.py" "-q"
    if ($LASTEXITCODE -ne 0) {
        throw "OPV optical-borrowing tests failed."
    }

    if (Test-Path -LiteralPath $PackagePath) {
        Remove-Item -LiteralPath $PackagePath -Force
    }
    & tar.exe -czf $PackagePath @RequiredFiles
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create OPV optical-borrowing package."
    }
    & ".\.venv\Scripts\python.exe" `
        "analysis\preflight_opv_optical_external_borrowing.py" `
        "--stage" "package" `
        "--archive" $PackagePath
    if ($LASTEXITCODE -ne 0) {
        throw "The packaged OPV borrowing archive failed semantic preflight."
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
    $RemoteCommand = "mkdir -p '$RemoteRoot' && mv -f ~/$PackageName '$RemoteRoot/$PackageName' && cd '$RemoteRoot' && echo '$PackageHash  $PackageName' | sha256sum -c - && tar --overwrite -xzf '$PackageName' && bash analysis/balam/prepare_and_submit_opv_optical_external_borrowing.sh"
    & ssh $RemoteHostName $RemoteCommand
    if ($LASTEXITCODE -ne 0) {
        throw "Remote environment validation or submission failed."
    }
}
finally {
    Pop-Location
}
