$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$RemoteHostName = "yangbai@balam.scinet.utoronto.ca"
$RemoteRoot = "/scratch/yangbai/collective-exp-ood"
$PackageName = "obelix_ood_balam_package.tar.gz"
$PackagePath = Join-Path $env:TEMP $PackageName

Push-Location $RepoRoot
try {
    & ".\.venv\Scripts\python.exe" "analysis\run_obelix_ood_discovery.py" "--validate-only"
    if ($LASTEXITCODE -ne 0) { throw "Local frozen-input validation failed." }

    if (Test-Path $PackagePath) { Remove-Item -LiteralPath $PackagePath -Force }
    & tar.exe -czf $PackagePath `
        "analysis/run_obelix_ood_discovery.py" `
        "analysis/verify_obelix_ood_discovery_results.py" `
        "analysis/obelix_ood_discovery_design.json" `
        "analysis/results/obelix_ood_discovery_input.npz" `
        "analysis/results/obelix_ood_discovery_input_meta.json" `
        "analysis/balam/requirements.txt" `
        "analysis/balam/run_obelix_ood_discovery_balam.sh" `
        "analysis/balam/prepare_and_submit_balam.sh"
    if ($LASTEXITCODE -ne 0) { throw "Failed to create the Balam package." }

    $PackageHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $PackagePath).Hash.ToLowerInvariant()
    Write-Host "Package SHA256: $PackageHash"
    Write-Host "Balam will request your password or interactive login. Do not paste it into chat."

    & scp $PackagePath "${RemoteHostName}:~/$PackageName"
    if ($LASTEXITCODE -ne 0) { throw "Upload to Balam failed." }

    # Tilde expansion is intentionally outside quotes in the actual command.
    $RemoteCommand = "mkdir -p '$RemoteRoot' && mv ~/$PackageName '$RemoteRoot/$PackageName' && cd '$RemoteRoot' && tar -xzf '$PackageName' && bash analysis/balam/prepare_and_submit_balam.sh"
    & ssh $RemoteHostName $RemoteCommand
    if ($LASTEXITCODE -ne 0) { throw "Remote environment setup or submission failed." }
}
finally {
    Pop-Location
}
