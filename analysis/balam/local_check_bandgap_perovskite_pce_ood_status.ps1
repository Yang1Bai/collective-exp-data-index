param(
    [string]$JobId = ""
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$RemoteHostName = "yangbai@balam.scinet.utoronto.ca"
$RemoteRoot = "/scratch/yangbai/collective-exp-ood"
$Transcript = Join-Path `
    $RepoRoot "analysis\results\bandgap_perovskite_pce_ood_status.log"
$JobSelector = if ($JobId) { "-j '$JobId'" } else { "-u yangbai -n bandgap-pce" }
$AccountingSelector = if ($JobId) {
    "-j '$JobId'"
}
else {
    "-S 2026-07-28 -u yangbai --name=bandgap-pce"
}
$RemoteCommand = @"
squeue $JobSelector || true
sacct $AccountingSelector --format=JobID,JobName,State,ExitCode,Elapsed,Start,End
echo '--- RESULT FILES ---'
ls -lh '$RemoteRoot/analysis/results/'bandgap_perovskite_pce_ood* 2>/dev/null || true
echo '--- STDOUT TAIL ---'
tail -n 40 '$RemoteRoot/logs/'bandgap-pce-*.out 2>/dev/null || true
echo '--- STDERR TAIL ---'
tail -n 40 '$RemoteRoot/logs/'bandgap-pce-*.err 2>/dev/null || true
"@

Start-Transcript -LiteralPath $Transcript -Force | Out-Null
Write-Host "Balam may request Duo login. Approve the push on your phone."
try {
    $PreviousPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $Output = & ssh $RemoteHostName $RemoteCommand 2>&1
    $SshExitCode = $LASTEXITCODE
    $ErrorActionPreference = $PreviousPreference
    $Output | ForEach-Object { Write-Host $_ }
    if ($SshExitCode -ne 0) {
        throw "Balam status check failed."
    }
}
finally {
    Stop-Transcript | Out-Null
}
