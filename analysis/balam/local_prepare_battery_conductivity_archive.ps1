param(
    [string]$RepositoryRoot = (
        Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
    )
)

$ErrorActionPreference = "Stop"
$targetDirectory = Join-Path `
    $RepositoryRoot "data\external\battery_conductivity_borrowing"
$archive = Join-Path $targetDirectory "battery-v2.zip"
$url = "https://ndownloader.figshare.com/files/34496339"
$expectedBytes = 97765422
$expectedMd5 = "c7411b5da52afddef98ef868fba25e0d"

New-Item -ItemType Directory -Force -Path $targetDirectory | Out-Null

if (Test-Path -LiteralPath $archive) {
    $existing = Get-Item -LiteralPath $archive
    if ($existing.Length -ne $expectedBytes) {
        throw "Existing battery-v2.zip has an unexpected byte size."
    }
} else {
    Write-Host "Downloading the frozen BatteryBERT v2 archive (about 98 MB)."
    curl.exe --fail --location --retry 5 --retry-delay 3 `
        --output $archive $url
    if ($LASTEXITCODE -ne 0) {
        throw "BatteryBERT v2 download failed."
    }
}

$item = Get-Item -LiteralPath $archive
if ($item.Length -ne $expectedBytes) {
    throw "Downloaded archive byte size does not match the freeze."
}
$md5 = (Get-FileHash -LiteralPath $archive -Algorithm MD5).Hash.ToLower()
if ($md5 -ne $expectedMd5) {
    throw "Downloaded archive MD5 does not match the freeze."
}

$python = Join-Path `
    $env:USERPROFILE `
    ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    $python = "python"
}

Push-Location $RepositoryRoot
try {
    & $python "analysis\audit_battery_conductivity_archive_schema.py"
    if ($LASTEXITCODE -ne 0) {
        throw "Outcome-blind BatteryBERT archive schema audit failed."
    }
} finally {
    Pop-Location
}

Write-Host "Battery archive downloaded, verified, and schema-audited."

