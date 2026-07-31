$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$RemoteHostName = "yangbai@balam.scinet.utoronto.ca"
$RemoteRoot = "/scratch/yangbai/collective-exp-ood"
$PackageName = "neighbor_transfer_policy_balam_package.tar.gz"
$PackagePath = Join-Path $env:TEMP $PackageName

Push-Location $RepoRoot
try {
    & ".\.venv\Scripts\python.exe" "analysis\run_neighbor_transfer_policy_benchmark.py" "--validate-only"
    if ($LASTEXITCODE -ne 0) { throw "Local policy/input validation failed." }

    if (Test-Path $PackagePath) { Remove-Item -LiteralPath $PackagePath -Force }
    & tar.exe -czf $PackagePath `
        "analysis/run_neighbor_transfer_policy_benchmark.py" `
        "analysis/run_obelix_ood_discovery.py" `
        "analysis/verify_neighbor_transfer_policy_results.py" `
        "analysis/neighbor_transfer_policy_design.json" `
        "analysis/results/obelix_ood_discovery_input.npz" `
        "analysis/results/obelix_ood_discovery_input_meta.json" `
        "analysis/balam/requirements.txt" `
        "analysis/balam/run_neighbor_transfer_policy_balam.sh" `
        "analysis/balam/prepare_and_submit_neighbor_policy.sh"
    if ($LASTEXITCODE -ne 0) { throw "Failed to create the Balam policy package." }

    $PackageHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $PackagePath).Hash.ToLowerInvariant()
    Write-Host "Package SHA256: $PackageHash"
    Write-Host "Balam will request your password or interactive login. Do not paste it into chat."

    & scp $PackagePath "${RemoteHostName}:~/$PackageName"
    if ($LASTEXITCODE -ne 0) { throw "Upload to Balam failed." }

    $RemoteCommand = "mkdir -p '$RemoteRoot' && mv ~/$PackageName '$RemoteRoot/$PackageName' && cd '$RemoteRoot' && tar -xzf '$PackageName' && bash analysis/balam/prepare_and_submit_neighbor_policy.sh"
    & ssh $RemoteHostName $RemoteCommand
    if ($LASTEXITCODE -ne 0) { throw "Remote environment setup or submission failed." }
}
finally {
    Pop-Location
}
