param(
    [string]$Destination = "E:\collective-exp-battery-raw\CALCE"
)

$ErrorActionPreference = "Stop"
$cells = @(
    "CS2_33", "CS2_34", "CS2_35", "CS2_36", "CS2_37", "CS2_38",
    "CX2_16", "CX2_33", "CX2_35", "CX2_34", "CX2_36", "CX2_37", "CX2_38"
)
New-Item -ItemType Directory -Path $Destination -Force | Out-Null
$log = Join-Path $Destination "download.log"

foreach ($cell in $cells) {
    $target = Join-Path $Destination "$cell.zip"
    $url = "https://web.calce.umd.edu/batteries/data/$cell.zip"
    $existing = if (Test-Path -LiteralPath $target) {
        (Get-Item -LiteralPath $target).Length
    } else {
        0
    }
    Add-Content -LiteralPath $log -Value "$(Get-Date -Format o) downloading $cell resume_bytes=$existing"
    & curl.exe --fail --location --retry 20 --retry-delay 10 --continue-at - `
        --output $target $url
    if ($LASTEXITCODE -ne 0) {
        throw "Download failed: $cell"
    }
    if ((Get-Item -LiteralPath $target).Length -le 0) {
        throw "Empty download: $cell"
    }
    Add-Content -LiteralPath $log -Value "$(Get-Date -Format o) downloaded $cell"
}

$manifest = foreach ($cell in $cells) {
    $target = Join-Path $Destination "$cell.zip"
    [ordered]@{
        name = "$cell.zip"
        bytes = (Get-Item -LiteralPath $target).Length
        sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $target).Hash.ToLowerInvariant()
        url = "https://web.calce.umd.edu/batteries/data/$cell.zip"
    }
}
[ordered]@{
    status = "downloaded-and-hashed"
    created_utc = (Get-Date).ToUniversalTime().ToString("o")
    files = $manifest
} | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 `
    -LiteralPath (Join-Path $Destination "raw_source_manifest.json")

Write-Host "CALCE wrong-chemistry source downloaded and hashed in $Destination"
