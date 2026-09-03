param(
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$RemoteHostName = "yangbai@balam.scinet.utoronto.ca"
$RemoteRoot = "/scratch/yangbai/collective-exp-ood"
$PackageName = "bandgap_perovskite_pce_ood_balam_package.tar.gz"
$PackagePath = Join-Path $env:TEMP $PackageName
$ExpectedDesignHash = (
    "8d370d238e5eb2072d0625b12ca2b06d" +
    "7e1d18d2c63e234f87f698d3867294e0"
)

$RequiredFiles = @(
    "analysis\BANDGAP_PEROVSKITE_PCE_OOD_DESIGN.json",
    "analysis\bandgap_borrowing_common.py",
    "analysis\audit_bandgap_perovskite_pair.py",
    "analysis\run_bandgap_external_source_skill.py",
    "analysis\run_bandgap_perovskite_pce_ood.py",
    "analysis\verify_bandgap_perovskite_results.py",
    "analysis\balam\requirements.txt",
    "analysis\balam\run_bandgap_perovskite_pce_ood_balam.sh",
    "analysis\balam\prepare_and_submit_bandgap_perovskite_pce_ood.sh",
    "data\external\bandgap_borrowing\BandgapDatabase1_v2.zip",
    "data\external\bandgap_borrowing\hybrid_bandgap_210413.zip",
    "data\external\bandgap_borrowing\hybrid3_bandgap\hybrid3_bandgap_records.csv",
    "data\external\bandgap_borrowing\hybrid3_bandgap\hybrid3_bandgap_manifest.json",
    "data\external\bandgap_borrowing\nomad_perovskite_v4\perovskite_solar_cell_recipient.csv",
    "data\external\bandgap_borrowing\nomad_perovskite_v4\perovskite_solar_cell_recipient_manifest.json"
)

Push-Location $RepoRoot
try {
    foreach ($Path in $RequiredFiles) {
        if (-not (Test-Path -LiteralPath $Path)) {
            throw "Required band-gap/PCE input is missing: $Path"
        }
    }
    $Python = ".\.venv\Scripts\python.exe"
    & $Python "-m" "py_compile" `
        "analysis\bandgap_borrowing_common.py" `
        "analysis\audit_bandgap_perovskite_pair.py" `
        "analysis\run_bandgap_external_source_skill.py" `
        "analysis\run_bandgap_perovskite_pce_ood.py" `
        "analysis\verify_bandgap_perovskite_results.py"
    if ($LASTEXITCODE -ne 0) {
        throw "Band-gap/PCE Python compilation failed."
    }
    $DesignHash = (
        Get-FileHash -Algorithm SHA256 -LiteralPath `
            "analysis\BANDGAP_PEROVSKITE_PCE_OOD_DESIGN.json"
    ).Hash.ToLowerInvariant()
    if ($DesignHash -ne $ExpectedDesignHash) {
        throw "Frozen PCE design hash changed: $DesignHash"
    }
    & $Python "analysis\audit_bandgap_perovskite_pair.py"
    if ($LASTEXITCODE -ne 0) {
        throw "Band-gap/PCE outcome-free pair audit failed."
    }

    if (Test-Path -LiteralPath $PackagePath) {
        Remove-Item -LiteralPath $PackagePath -Force
    }
    & tar.exe -czf $PackagePath @RequiredFiles
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create the band-gap/PCE Balam package."
    }
    $PackageHash = (
        Get-FileHash -Algorithm SHA256 -LiteralPath $PackagePath
    ).Hash.ToLowerInvariant()
    $PackageSizeMB = [math]::Round(
        (Get-Item -LiteralPath $PackagePath).Length / 1MB,
        2
    )
    Write-Host "Package SHA256: $PackageHash"
    Write-Host "Package size: $PackageSizeMB MB"
    if ($DryRun) {
        Write-Host "Dry run complete. Package was not uploaded."
        return
    }

    Write-Host (
        "Balam will request Duo login. Approve the push on your phone."
    )
    & scp $PackagePath "${RemoteHostName}:~/$PackageName"
    if ($LASTEXITCODE -ne 0) {
        throw "Band-gap/PCE package upload failed."
    }
    $RemoteCommand = (
        "mkdir -p '$RemoteRoot' && " +
        "mv -f ~/$PackageName '$RemoteRoot/$PackageName' && " +
        "cd '$RemoteRoot' && " +
        "echo '$PackageHash  $PackageName' | sha256sum -c - && " +
        "tar --overwrite -xzf '$PackageName' && " +
        "bash analysis/balam/" +
        "prepare_and_submit_bandgap_perovskite_pce_ood.sh"
    )
    & ssh $RemoteHostName $RemoteCommand
    if ($LASTEXITCODE -ne 0) {
        throw "Remote band-gap/PCE validation or submission failed."
    }
}
finally {
    Pop-Location
}
