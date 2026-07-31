param(
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$RemoteHostName = "yangbai@balam.scinet.utoronto.ca"
$RemoteRoot = "/scratch/yangbai/collective-exp-ood"
$PackageName = "multi_target_ood_borrowing_balam_package.tar.gz"
$PackagePath = Join-Path $env:TEMP $PackageName

Push-Location $RepoRoot
try {
    $env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
    & ".\.venv\Scripts\python.exe" "-m" "pytest" `
        "tests\test_multi_target_ood_borrowing.py" "-q"
    if ($LASTEXITCODE -ne 0) { throw "Multi-target OOD tests failed." }

    if (Test-Path $PackagePath) {
        Remove-Item -LiteralPath $PackagePath -Force
    }
    & tar.exe -czf $PackagePath `
        "analysis\common.py" `
        "analysis\run_knowledge_map.py" `
        "analysis\knowledge_map_design.json" `
        "analysis\MULTI_TARGET_OOD_BORROWING_PROTOCOL.md" `
        "analysis\multi_target_ood_borrowing_design.json" `
        "analysis\run_multi_target_ood_borrowing.py" `
        "analysis\verify_multi_target_ood_borrowing.py" `
        "analysis\balam\requirements.txt" `
        "analysis\balam\run_multi_target_ood_borrowing_balam.sh" `
        "analysis\balam\prepare_and_submit_multi_target_ood_borrowing.sh" `
        "tests\test_multi_target_ood_borrowing.py" `
        "data\collective.sqlite"
    if ($LASTEXITCODE -ne 0) { throw "Failed to create multi-target OOD package." }

    $PackageHash = (
        Get-FileHash -Algorithm SHA256 -LiteralPath $PackagePath
    ).Hash.ToLowerInvariant()
    $PackageSizeMB = [math]::Round((Get-Item $PackagePath).Length / 1MB, 2)
    Write-Host "Package SHA256: $PackageHash"
    Write-Host "Package size: $PackageSizeMB MB"
    if ($DryRun) {
        Write-Host "Dry run complete. Package was verified locally and was not uploaded."
        return
    }

    Write-Host "Balam will request Duo login. Do not paste a passcode into chat."
    & scp $PackagePath "${RemoteHostName}:~/$PackageName"
    if ($LASTEXITCODE -ne 0) { throw "Upload to Balam failed." }
    $RemoteCommand = "mkdir -p '$RemoteRoot' && mv ~/$PackageName '$RemoteRoot/$PackageName' && cd '$RemoteRoot' && tar -xzf '$PackageName' && bash analysis/balam/prepare_and_submit_multi_target_ood_borrowing.sh"
    & ssh $RemoteHostName $RemoteCommand
    if ($LASTEXITCODE -ne 0) { throw "Remote setup or submission failed." }
}
finally {
    Pop-Location
}
