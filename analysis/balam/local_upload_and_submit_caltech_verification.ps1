$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$RemoteHostName = "yangbai@balam.scinet.utoronto.ca"
$RemoteRoot = "/scratch/yangbai/collective-exp-ood"
$PackageName = "caltech_ionic_verifier_patch.tar.gz"
$PackagePath = Join-Path $env:TEMP $PackageName

Push-Location $RepoRoot
try {
    if (Test-Path $PackagePath) { Remove-Item -LiteralPath $PackagePath -Force }
    & tar.exe -czf $PackagePath `
        "analysis/verify_caltech_ionic_external_policy_results.py" `
        "analysis/CALTECH_IONIC_VERIFIER_AMENDMENT_4.md" `
        "analysis/CALTECH_IONIC_REMOTE_VERIFICATION_AMENDMENT_5.md" `
        "analysis/balam/run_caltech_ionic_external_policy_verify_balam.sh"
    if ($LASTEXITCODE -ne 0) { throw "Failed to create verifier patch." }

    Write-Host "Balam will request Duo login for upload and submission."
    & scp $PackagePath "${RemoteHostName}:~/$PackageName"
    if ($LASTEXITCODE -ne 0) { throw "Verifier patch upload failed." }
    $RemoteCommand = "cd '$RemoteRoot' && tar -xzf ~/$PackageName && sbatch --parsable analysis/balam/run_caltech_ionic_external_policy_verify_balam.sh"
    & ssh $RemoteHostName $RemoteCommand
    if ($LASTEXITCODE -ne 0) { throw "Verification job submission failed." }
}
finally {
    Pop-Location
}
