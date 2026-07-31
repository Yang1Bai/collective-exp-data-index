param([switch]$DryRun)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$RemoteHostName = "yangbai@balam.scinet.utoronto.ca"
$RemoteRoot = "/scratch/yangbai/collective-exp-ood"
$PackageName = "multistage_battery_file_map_package.tar.gz"
$PackagePath = Join-Path $env:TEMP $PackageName

Push-Location $RepoRoot
try {
    $Python = "D:\Program\anaconda3\python.exe"
    & $Python "analysis\verify_multistage_battery_cca_v2_preoutcome.py"
    if ($LASTEXITCODE -ne 0) { throw "Pre-outcome battery freeze verification failed." }

    if (Test-Path $PackagePath) { Remove-Item -LiteralPath $PackagePath -Force }
    & tar.exe -czf $PackagePath `
        "analysis/map_multistage_battery_archives.py" `
        "analysis/verify_multistage_battery_file_map.py" `
        "analysis/verify_multistage_battery_cca_v2_preoutcome.py" `
        "analysis/multistage_battery_cca_v2_design.json" `
        "analysis/MULTISTAGE_BATTERY_CCA_V2_PROTOCOL.md" `
        "analysis/cca_gate_v2_architecture.json" `
        "analysis/core_story_experiment_registry.json" `
        "analysis/target_metadata/multistage_battery_preoutcome_metadata.json" `
        "analysis/target_metadata/multistage_battery_preoutcome_freeze.json" `
        "catalog/catalog.json" `
        "analysis/balam/run_multistage_battery_file_map_balam.sh" `
        "analysis/balam/prepare_and_submit_multistage_battery_file_map.sh"
    if ($LASTEXITCODE -ne 0) { throw "Failed to create Balam mapping package." }
    Write-Host "Package SHA256: $((Get-FileHash -Algorithm SHA256 -LiteralPath $PackagePath).Hash.ToLowerInvariant())"
    Write-Host "Package size: $([math]::Round((Get-Item $PackagePath).Length / 1KB, 1)) KB"
    if ($DryRun) {
        Write-Host "Dry run complete; package was not uploaded."
        return
    }

    Write-Host "Balam will request Duo login. Do not paste a passcode into chat."
    & scp $PackagePath "${RemoteHostName}:~/$PackageName"
    if ($LASTEXITCODE -ne 0) { throw "Upload to Balam failed." }
    $RemoteCommand = "mkdir -p '$RemoteRoot' && mv ~/$PackageName '$RemoteRoot/$PackageName' && cd '$RemoteRoot' && tar -xzf '$PackageName' && bash analysis/balam/prepare_and_submit_multistage_battery_file_map.sh"
    & ssh $RemoteHostName $RemoteCommand
    if ($LASTEXITCODE -ne 0) { throw "Remote setup or submission failed." }
}
finally {
    Pop-Location
}
