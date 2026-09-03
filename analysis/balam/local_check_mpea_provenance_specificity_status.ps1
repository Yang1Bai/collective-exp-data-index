$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$RemoteHostName = "yangbai@balam.scinet.utoronto.ca"
$StatusPath = Join-Path $RepoRoot "analysis\results\mpea_provenance_specificity_balam_status.txt"
$RemoteRoot = "/scratch/yangbai/collective-exp-ood"
$RemoteCommand = @"
cd '$RemoteRoot'
squeue -j 71811 2>&1 || true
sacct -j 71811 --format=JobID,JobName,State,ExitCode,Elapsed,Start,End
scontrol show job 71811 2>&1 || true
test -f analysis/results/mpea_provenance_specificity_balam_results.tar.gz && ls -lh analysis/results/mpea_provenance_specificity_balam_results.tar.gz || true
test -f logs/mpea-prov2-71811.out && tail -n 50 logs/mpea-prov2-71811.out || true
test -f logs/mpea-prov2-71811.err && tail -n 50 logs/mpea-prov2-71811.err || true
"@

Push-Location $RepoRoot
try {
    Write-Host "Approve the Balam Duo push when prompted."
    $PreviousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & ssh $RemoteHostName $RemoteCommand 2>&1 |
        ForEach-Object { "$_" } |
        Tee-Object -FilePath $StatusPath
    $SshExitCode = $LASTEXITCODE
    $ErrorActionPreference = $PreviousErrorActionPreference
    if ($SshExitCode -ne 0) {
        throw "Balam status query failed."
    }
    Write-Host "Status saved to $StatusPath"
}
finally {
    Pop-Location
}
