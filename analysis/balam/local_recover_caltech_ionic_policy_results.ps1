$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$RemoteHostName = "yangbai@balam.scinet.utoronto.ca"
$RemoteRoot = "/scratch/yangbai/collective-exp-ood"
$ArchiveName = "caltech_ionic_external_policy_recovery.tar.gz"
$RemoteArchive = "$RemoteRoot/analysis/results/$ArchiveName"
$LocalArchive = Join-Path $env:TEMP $ArchiveName

Push-Location $RepoRoot
try {
    Write-Host "Balam will request Duo login for archive creation and download."
    $RemoteCommand = "cd '$RemoteRoot' && tar -czf 'analysis/results/$ArchiveName' " +
        "analysis/results/caltech_ionic_external_audit.json " +
        "analysis/results/caltech_ionic_external_policy_trajectories.csv " +
        "analysis/results/caltech_ionic_external_policy_gates.csv " +
        "analysis/results/caltech_ionic_external_policy_utility.csv " +
        "analysis/results/caltech_ionic_external_policy_gate_summary.csv " +
        "analysis/results/caltech_ionic_external_policy_source_quality.csv " +
        "analysis/results/caltech_ionic_external_policy_contrasts.csv " +
        "analysis/results/caltech_ionic_external_policy_summary.json " +
        "analysis/results/caltech_ionic_external_policy_balam_environment.txt " +
        "analysis/results/caltech_ionic_external_policy_balam_checksums.sha256 " +
        "analysis/results/caltech_ionic_external_policy_COMPLETE.json"
    & ssh $RemoteHostName $RemoteCommand
    if ($LASTEXITCODE -ne 0) { throw "Remote recovery archive creation failed." }

    & scp "${RemoteHostName}:$RemoteArchive" $LocalArchive
    if ($LASTEXITCODE -ne 0) { throw "Recovery archive download failed." }
    & tar.exe -xzf $LocalArchive -C $RepoRoot
    if ($LASTEXITCODE -ne 0) { throw "Recovery archive extraction failed." }

    & ".\.venv\Scripts\python.exe" "analysis\run_caltech_ionic_external_policy.py" "--validate-only"
    if ($LASTEXITCODE -ne 0) { throw "Local frozen-protocol validation failed." }
    & ".\.venv\Scripts\python.exe" "analysis\verify_caltech_ionic_external_policy_results.py"
    if ($LASTEXITCODE -ne 0) { throw "Recovered formal result verification failed." }
    Write-Host "Recovered formal results passed the corrected independent verifier."
}
finally {
    Pop-Location
}
