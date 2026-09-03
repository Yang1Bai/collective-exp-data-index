param(
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$RemoteHostName = "yangbai@balam.scinet.utoronto.ca"
$RemoteRoot = "/scratch/yangbai/collective-exp-ood"
$PackageName = "battery_conductivity_balam_package.tar.gz"
$PackagePath = Join-Path $env:TEMP $PackageName

$RequiredFiles = @(
    "analysis\BATTERY_CONDUCTIVITY_BORROWING_PROTOCOL.md",
    "analysis\BATTERY_CONDUCTIVITY_SCHEMA_AMENDMENT.md",
    "analysis\BATTERY_CONDUCTIVITY_VALUE_SEMANTICS_AMENDMENT.md",
    "analysis\BATTERY_CONDUCTIVITY_SOURCE_AGGREGATION_AMENDMENT.md",
    "analysis\battery_conductivity_borrowing_design.json",
    "analysis\battery_conductivity_implementation.json",
    "analysis\battery_conductivity_release_freeze.json",
    "analysis\battery_conductivity_source_freeze.json",
    "analysis\battery_conductivity_benchmark_freeze.json",
    "analysis\prepare_battery_conductivity_source_cards.py",
    "analysis\verify_battery_conductivity_source_cards.py",
    "analysis\run_battery_conductivity_borrowing.py",
    "analysis\verify_battery_conductivity_borrowing.py",
    "analysis\verify_battery_conductivity_formal_release.py",
    "analysis\results\battery_conductivity_formal_release.csv",
    "analysis\results\battery_conductivity_formal_release_manifest.json",
    "analysis\results\battery_conductivity_preoutcome_audit.json",
    "analysis\balam\requirements.txt",
    "analysis\balam\run_battery_conductivity_borrowing_balam.sh",
    "analysis\balam\prepare_and_submit_battery_conductivity_borrowing.sh"
)

Push-Location $RepoRoot
try {
    foreach ($Path in $RequiredFiles) {
        if (-not (Test-Path -LiteralPath $Path)) {
            throw "Required battery borrowing input is missing: $Path"
        }
    }
    & ".\.venv\Scripts\python.exe" "-m" "py_compile" `
        "analysis\prepare_battery_conductivity_source_cards.py" `
        "analysis\verify_battery_conductivity_source_cards.py" `
        "analysis\run_battery_conductivity_borrowing.py" `
        "analysis\verify_battery_conductivity_borrowing.py"
    if ($LASTEXITCODE -ne 0) {
        throw "Battery borrowing Python compilation failed."
    }
    & ".\.venv\Scripts\python.exe" `
        "analysis\verify_battery_conductivity_formal_release.py"
    if ($LASTEXITCODE -ne 0) {
        throw "Battery formal release verification failed."
    }

    if (Test-Path -LiteralPath $PackagePath) {
        Remove-Item -LiteralPath $PackagePath -Force
    }
    & tar.exe -czf $PackagePath @RequiredFiles
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create the battery borrowing package."
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

    Write-Host "Balam will request Duo login. Do not paste a passcode into chat."
    & scp $PackagePath "${RemoteHostName}:~/$PackageName"
    if ($LASTEXITCODE -ne 0) {
        throw "Upload to Balam failed."
    }
    $RemoteCommand = (
        "mkdir -p '$RemoteRoot' && " +
        "mv -f ~/$PackageName '$RemoteRoot/$PackageName' && " +
        "cd '$RemoteRoot' && " +
        "echo '$PackageHash  $PackageName' | sha256sum -c - && " +
        "tar --overwrite -xzf '$PackageName' && " +
        "bash analysis/balam/" +
        "prepare_and_submit_battery_conductivity_borrowing.sh"
    )
    & ssh $RemoteHostName $RemoteCommand
    if ($LASTEXITCODE -ne 0) {
        throw "Remote environment validation or submission failed."
    }
}
finally {
    Pop-Location
}

