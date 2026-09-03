$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$RemoteHostName = "yangbai@balam.scinet.utoronto.ca"
$RemoteRoot = "/scratch/yangbai/collective-exp-ood"
$PackageName = "caltech_ionic_external_policy_balam_package.tar.gz"
$PackagePath = Join-Path $env:TEMP $PackageName

Push-Location $RepoRoot
try {
    & ".\.venv\Scripts\python.exe" "analysis\audit_caltech_ionic_external_target.py"
    if ($LASTEXITCODE -ne 0) { throw "Local target/source audit failed." }
    & ".\.venv\Scripts\python.exe" "analysis\run_caltech_ionic_external_policy.py" "--validate-only"
    if ($LASTEXITCODE -ne 0) { throw "Local frozen-protocol validation failed." }

    if (Test-Path $PackagePath) { Remove-Item -LiteralPath $PackagePath -Force }
    & tar.exe -czf $PackagePath `
        "analysis/audit_caltech_ionic_external_target.py" `
        "analysis/run_caltech_ionic_external_policy.py" `
        "analysis/verify_caltech_ionic_external_policy_results.py" `
        "analysis/common.py" `
        "analysis/caltech_ionic_external_policy_design.json" `
        "analysis/caltech_ionic_external_policy_implementation.json" `
        "analysis/CALTECH_IONIC_SCHEMA_AMENDMENT.md" `
        "analysis/CALTECH_IONIC_INFERENCE_AMENDMENT.md" `
        "analysis/CALTECH_IONIC_IMPLEMENTATION_AMENDMENT_2.md" `
        "analysis/CALTECH_IONIC_INFRASTRUCTURE_AMENDMENT_3.md" `
        "analysis/CALTECH_IONIC_VERIFIER_AMENDMENT_4.md" `
        "analysis/results/caltech_ionic_external_audit.json" `
        "scripts/localdb/build_localdb.py" `
        "data/external/caltech_ionic/ionic_conductivity_database.csv" `
        "data/collective.sqlite" `
        "analysis/balam/requirements.txt" `
        "analysis/balam/run_caltech_ionic_external_policy_balam.sh" `
        "analysis/balam/prepare_and_submit_caltech_ionic_policy.sh"
    if ($LASTEXITCODE -ne 0) { throw "Failed to create the Balam package." }

    $PackageHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $PackagePath).Hash.ToLowerInvariant()
    $PackageSizeMB = [math]::Round((Get-Item $PackagePath).Length / 1MB, 2)
    Write-Host "Package SHA256: $PackageHash"
    Write-Host "Package size: $PackageSizeMB MB"
    Write-Host "Balam will request Duo login. Do not paste a passcode into chat."

    & scp $PackagePath "${RemoteHostName}:~/$PackageName"
    if ($LASTEXITCODE -ne 0) { throw "Upload to Balam failed." }

    $RemoteCommand = "mkdir -p '$RemoteRoot' && mv ~/$PackageName '$RemoteRoot/$PackageName' && cd '$RemoteRoot' && tar -xzf '$PackageName' && bash analysis/balam/prepare_and_submit_caltech_ionic_policy.sh"
    & ssh $RemoteHostName $RemoteCommand
    if ($LASTEXITCODE -ne 0) { throw "Remote environment setup or submission failed." }
}
finally {
    Pop-Location
}
