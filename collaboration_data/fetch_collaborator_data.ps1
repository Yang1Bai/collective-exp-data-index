param(
    [string]$Destination = "collaborator_workspace",
    [string]$Repository = "Yang1Bai/collective-exp-data-index",
    [string]$Tag = "collaborator-data-v2026.08.04"
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw "GitHub CLI (gh) is required. Install it and authenticate with access to the private repository."
}

gh auth status | Out-Null
New-Item -ItemType Directory -Force -Path $Destination | Out-Null

gh release download $Tag --repo $Repository --dir $Destination --clobber
if ($LASTEXITCODE -ne 0) {
    throw "Release download failed. Confirm repository access and the release tag."
}

$checksumFile = Join-Path $PSScriptRoot "RELEASE_ASSET_CHECKSUMS.sha256"
if (-not (Test-Path $checksumFile)) {
    throw "Missing committed release checksum file: $checksumFile"
}

Get-Content $checksumFile | ForEach-Object {
    if ($_ -match '^([0-9a-fA-F]{64})\s+\*?(.+)$') {
        $expected = $Matches[1].ToLowerInvariant()
        $name = $Matches[2].Trim()
        $path = Join-Path $Destination $name
        if (-not (Test-Path $path)) { throw "Missing downloaded asset: $name" }
        $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLowerInvariant()
        if ($actual -ne $expected) { throw "SHA-256 mismatch for $name" }
    }
}

Get-ChildItem -LiteralPath $Destination -Filter '*.zip' | ForEach-Object {
    $out = Join-Path $Destination $_.BaseName
    if (Test-Path $out) { Remove-Item -LiteralPath $out -Recurse -Force }
    Expand-Archive -LiteralPath $_.FullName -DestinationPath $out -Force
}

Write-Host "Collaborator datasets downloaded, verified, and extracted to $Destination"
