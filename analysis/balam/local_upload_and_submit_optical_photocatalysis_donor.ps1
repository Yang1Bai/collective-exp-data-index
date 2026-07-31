param(
    [switch]$DryRun,
    [string]$CancelJobId = ""
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$RemoteHostName = "yangbai@balam.scinet.utoronto.ca"
$RemoteRoot = "/scratch/yangbai/collective-exp-ood"
$PackageName = "optical_photocatalysis_donor_balam_package.tar.gz"
$PackagePath = Join-Path $env:TEMP $PackageName

Push-Location $RepoRoot
try {
    $RequiredFiles = @(
        "analysis\optical_photocatalysis_borrowing_design.json",
        "analysis\OPTICAL_PHOTOCATALYSIS_FROZEN_PROTOCOL.md",
        "analysis\prepare_optical_photocatalysis_donor_features.py",
        "analysis\results\optical_photocatalysis_pair_audit.json",
        "analysis\results\optical_photocatalysis_target_metadata.csv",
        "analysis\balam\requirements.txt",
        "analysis\balam\run_optical_photocatalysis_donor_balam.sh",
        "analysis\balam\prepare_and_submit_optical_photocatalysis_donor.sh",
        "data\external\optical_photocatalysis\DB for chromophore_Sci_Data_rev02.csv"
    )
    foreach ($Path in $RequiredFiles) {
        if (-not (Test-Path -LiteralPath $Path)) {
            throw "Required frozen input is missing: $Path"
        }
    }

    if (Test-Path -LiteralPath $PackagePath) {
        Remove-Item -LiteralPath $PackagePath -Force
    }
    & tar.exe -czf $PackagePath @RequiredFiles
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create the optical donor package."
    }

    $PackageHash = (
        Get-FileHash -Algorithm SHA256 -LiteralPath $PackagePath
    ).Hash.ToLowerInvariant()
    $PackageSizeMB = [math]::Round((Get-Item $PackagePath).Length / 1MB, 2)
    Write-Host "Package SHA256: $PackageHash"
    Write-Host "Package size: $PackageSizeMB MB"
    if ($DryRun) {
        Write-Host "Dry run complete. Package was not uploaded."
        return
    }

    Write-Host "Balam will request Duo login. Do not paste a passcode into chat."
    & scp $PackagePath "${RemoteHostName}:~/$PackageName"
    if ($LASTEXITCODE -ne 0) { throw "Upload to Balam failed." }
    $CancelCommand = ""
    if ($CancelJobId) {
        if ($CancelJobId -notmatch '^\d+$') {
            throw "CancelJobId must contain digits only."
        }
        $CancelCommand = "scancel '$CancelJobId' && "
    }
    $RemoteCommand = "${CancelCommand}mkdir -p '$RemoteRoot' && mv ~/$PackageName '$RemoteRoot/$PackageName' && cd '$RemoteRoot' && tar -xzf '$PackageName' && bash analysis/balam/prepare_and_submit_optical_photocatalysis_donor.sh"
    & ssh $RemoteHostName $RemoteCommand
    if ($LASTEXITCODE -ne 0) { throw "Remote setup or submission failed." }
}
finally {
    Pop-Location
}
