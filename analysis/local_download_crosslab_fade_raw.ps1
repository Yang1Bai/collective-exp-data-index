param(
    [string]$Destination = "E:\collective-exp-battery-raw"
)

$ErrorActionPreference = "Stop"

$files = @(
    @{
        Name = "MATR_batch_20170512.mat"
        Url = "https://data.matr.io/1/api/v1/file/5c86c0b5fa2ede00015ddf66/download"
        Bytes = 3025320241
    },
    @{
        Name = "MATR_batch_20170630.mat"
        Url = "https://data.matr.io/1/api/v1/file/5c86bf13fa2ede00015ddd82/download"
        Bytes = 2007331155
    },
    @{
        Name = "MATR_batch_20180412.mat"
        Url = "https://data.matr.io/1/api/v1/file/5c86bd64fa2ede00015ddbb2/download"
        Bytes = 3236690412
    },
    @{
        Name = "MATR_batch_20190124.mat"
        Url = "https://data.matr.io/1/api/v1/file/5dcef152110002c7215b2c90/download"
        Bytes = 2601295745
    },
    @{
        Name = "hust_data.zip"
        Url = "https://data.mendeley.com/public-files/datasets/nsc7hnsg4s/files/5ca0ac3e-d598-4d07-8dcb-879aa047e98b/file_downloaded"
        Bytes = 1188136932
    }
)

New-Item -ItemType Directory -Path $Destination -Force | Out-Null
$log = Join-Path $Destination "download.log"

foreach ($item in $files) {
    $target = Join-Path $Destination $item.Name
    $existing = if (Test-Path -LiteralPath $target) {
        (Get-Item -LiteralPath $target).Length
    } else {
        0
    }

    if ($existing -eq $item.Bytes) {
        Add-Content -LiteralPath $log -Value "$(Get-Date -Format o) verified-existing $($item.Name) $existing"
        continue
    }
    if ($existing -gt $item.Bytes) {
        throw "Existing file is larger than the frozen source size: $target"
    }

    Add-Content -LiteralPath $log -Value "$(Get-Date -Format o) downloading $($item.Name) resume_bytes=$existing"
    & curl.exe --fail --location --retry 20 --retry-delay 10 --continue-at - `
        --output $target $item.Url
    if ($LASTEXITCODE -ne 0) {
        throw "Download failed: $($item.Name)"
    }

    $actual = (Get-Item -LiteralPath $target).Length
    if ($actual -ne $item.Bytes) {
        throw "Size verification failed for $($item.Name): expected $($item.Bytes), got $actual"
    }
    Add-Content -LiteralPath $log -Value "$(Get-Date -Format o) verified $($item.Name) $actual"
}

$manifest = foreach ($item in $files) {
    $target = Join-Path $Destination $item.Name
    [ordered]@{
        name = $item.Name
        bytes = (Get-Item -LiteralPath $target).Length
        sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $target).Hash.ToLowerInvariant()
        url = $item.Url
    }
}

[ordered]@{
    status = "downloaded-and-size-verified"
    created_utc = (Get-Date).ToUniversalTime().ToString("o")
    destination = $Destination
    files = $manifest
} | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 `
    -LiteralPath (Join-Path $Destination "raw_source_manifest.json")

Write-Host "Raw sources downloaded and verified in $Destination"
