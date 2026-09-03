$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$RemoteHostName = "yangbai@balam.scinet.utoronto.ca"
$RemoteArchive = "/scratch/yangbai/collective-exp-ood/analysis/results/multistage_battery_file_map_results.tar.gz"
$LocalArchive = Join-Path $env:TEMP "multistage_battery_file_map_results.tar.gz"

Push-Location $RepoRoot
try {
    Write-Host "Balam may request Duo login. Do not paste a passcode into chat."
    & scp "${RemoteHostName}:$RemoteArchive" $LocalArchive
    if ($LASTEXITCODE -ne 0) { throw "Result download failed." }
    & tar.exe -xzf $LocalArchive
    if ($LASTEXITCODE -ne 0) { throw "Result extraction failed." }
    & "D:\Program\anaconda3\python.exe" "analysis\verify_multistage_battery_file_map.py" "analysis\results\multistage_battery_file_map"
    if ($LASTEXITCODE -ne 0) { throw "Downloaded metadata-only map verification failed." }
    Write-Host "Battery archive mapping results downloaded and independently verified."
}
finally {
    Pop-Location
}
