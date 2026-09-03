param(
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$RemoteHostName = "yangbai@balam.scinet.utoronto.ca"
$RemoteRoot = "/scratch/yangbai/collective-exp-ood"
$PackageName = "optical_photocatalysis_development_balam_package.tar.gz"
$PackagePath = Join-Path $env:TEMP $PackageName

Push-Location $RepoRoot
try {
    $RequiredFiles = @(
        "analysis\optical_photocatalysis_borrowing_design.json",
        "analysis\optical_photocatalysis_development_gate_config.json",
        "analysis\OPTICAL_PHOTOCATALYSIS_SOURCE_VERIFIER_AMENDMENT.md",
        "analysis\run_optical_photocatalysis_development_gate.py",
        "analysis\verify_optical_photocatalysis_development_gate.py",
        "analysis\verify_optical_photocatalysis_source_features.py",
        "analysis\results\optical_photocatalysis_pair_audit.json",
        "analysis\results\optical_photocatalysis_target_metadata.csv",
        "analysis\results\optical_photocatalysis_source_skill.json",
        "analysis\results\optical_photocatalysis_donor_features.csv",
        "analysis\results\optical_photocatalysis_donor_oof_predictions.csv",
        "analysis\results\optical_photocatalysis_development_draws.csv",
        "analysis\results\optical_photocatalysis_development_draws_manifest.json",
        "analysis\balam\requirements.txt",
        "analysis\balam\run_optical_photocatalysis_development_gate_balam.sh",
        "analysis\balam\prepare_and_submit_optical_photocatalysis_development_gate.sh",
        "data\external\optical_photocatalysis\SC-012-D1SC02150H-s005.csv"
    )
    foreach ($Path in $RequiredFiles) {
        if (-not (Test-Path -LiteralPath $Path)) {
            throw "Required frozen input is missing: $Path"
        }
    }

    if (Test-Path -LiteralPath $PackagePath) {
        Remove-Item -LiteralPath $PackagePath -Force
    }
    & tar.exe -czf $PackagePath @RequiredFiles
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create the optical development package."
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
    $RemoteCommand = "mkdir -p '$RemoteRoot' && mv ~/$PackageName '$RemoteRoot/$PackageName' && cd '$RemoteRoot' && tar -xzf '$PackageName' && bash analysis/balam/prepare_and_submit_optical_photocatalysis_development_gate.sh"
    & ssh $RemoteHostName $RemoteCommand
    if ($LASTEXITCODE -ne 0) { throw "Remote setup or submission failed." }
}
finally {
    Pop-Location
}
