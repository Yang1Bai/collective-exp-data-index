param(
    [ValidateRange(1, 16)]
    [int]$Workers = 8
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$BundledPython = "C:\Users\yangb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$AnacondaPython = "D:\Program\anaconda3\python.exe"
$Python = if (Test-Path $BundledPython) { $BundledPython } else { $AnacondaPython }
$Output = Join-Path $RepoRoot "analysis\results\multistage_battery_file_map"

Push-Location $RepoRoot
try {
    Write-Host "Verifying the frozen pre-outcome protocol..."
    & $Python "analysis\verify_multistage_battery_cca_v2_preoutcome.py"
    if ($LASTEXITCODE -ne 0) { throw "Pre-outcome battery freeze verification failed." }

    Write-Host "Mapping 279 Figshare archives with $Workers workers."
    Write-Host "Numeric CSV members will not be opened; completed ZIPs are deleted after metadata extraction."
    Write-Host "Checkpoint directory: $Output"
    & $Python -u "analysis\map_multistage_battery_archives.py" `
        --output-dir $Output `
        --workers $Workers
    if ($LASTEXITCODE -ne 0) { throw "Metadata-only archive mapping failed; rerun this command to resume." }

    & $Python "analysis\verify_multistage_battery_file_map.py" $Output `
        --output (Join-Path $Output "INDEPENDENT_VERIFICATION.json")
    if ($LASTEXITCODE -ne 0) { throw "Completed archive map failed independent verification." }
    Write-Host "Battery archive mapping completed and independently verified."
}
finally {
    Pop-Location
}
