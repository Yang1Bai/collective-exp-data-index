param(
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$RemoteHostName = "yangbai@balam.scinet.utoronto.ca"
$RemoteRoot = "/scratch/yangbai/collective-exp-ood"
$PackageName = "strength_fatigue_ood_balam_package.tar.gz"
$PackagePath = Join-Path $env:TEMP $PackageName
$Transcript = Join-Path `
    $RepoRoot "analysis\results\strength_fatigue_ood_submit.log"
$ExpectedDesignHash = (
    "e26d74d1955e6deab26ba91d235fd0d" +
    "48c7e3bdb55753677d02331977ffabf6f"
)
$ExpectedImplementationHash = (
    "543c794aca34fb324165803b32723296" +
    "d8ff75c76f7df2b56fced5b98a484b1a"
)

$RequiredFiles = @(
    "analysis\strength_to_fatigue_ood_design.json",
    "analysis\strength_fatigue_implementation.json",
    "analysis\STRENGTH_TO_FATIGUE_OOD_PROTOCOL.md",
    "analysis\STRENGTH_TO_FATIGUE_PREOUTCOME_HASH_AMENDMENT.md",
    "analysis\STRENGTH_TO_FATIGUE_PREOUTCOME_STRUCTURE_AMENDMENT.md",
    "analysis\STRENGTH_TO_FATIGUE_SYNTHETIC_SMOKE_AMENDMENT.md",
    "analysis\run_strength_to_fatigue_ood.py",
    "analysis\verify_strength_to_fatigue_results.py",
    "analysis\common.py",
    "analysis\results\strength_fatigue_preoutcome_audit.json",
    "analysis\results\strength_fatigue_preoutcome_VERIFIED.json",
    "analysis\results\strength_fatigue_target_metadata_no_outcomes.csv",
    "analysis\results\strength_fatigue_formal_release_manifest.json",
    "analysis\results\strength_fatigue_formal_target_release.csv",
    "analysis\results\strength_fatigue_formal_donor_release.csv",
    "analysis\balam\requirements.txt",
    "analysis\balam\run_strength_fatigue_ood_balam.sh",
    "analysis\balam\prepare_and_submit_strength_fatigue_ood.sh"
)

Push-Location $RepoRoot
Start-Transcript -LiteralPath $Transcript -Force | Out-Null
try {
    foreach ($Path in $RequiredFiles) {
        if (-not (Test-Path -LiteralPath $Path)) {
            throw "Required strength/fatigue input is missing: $Path"
        }
    }
    $Python = ".\.venv\Scripts\python.exe"
    & $Python "-m" "py_compile" `
        "analysis\run_strength_to_fatigue_ood.py" `
        "analysis\verify_strength_to_fatigue_results.py" `
        "analysis\common.py"
    if ($LASTEXITCODE -ne 0) {
        throw "Strength/fatigue Python compilation failed."
    }
    $DesignHash = (
        Get-FileHash -Algorithm SHA256 -LiteralPath `
            "analysis\strength_to_fatigue_ood_design.json"
    ).Hash.ToLowerInvariant()
    if ($DesignHash -ne $ExpectedDesignHash) {
        throw "Frozen strength/fatigue design hash changed: $DesignHash"
    }
    $ImplementationHash = (
        Get-FileHash -Algorithm SHA256 -LiteralPath `
            "analysis\strength_fatigue_implementation.json"
    ).Hash.ToLowerInvariant()
    if ($ImplementationHash -ne $ExpectedImplementationHash) {
        throw (
            "Frozen strength/fatigue implementation hash changed: " +
            $ImplementationHash
        )
    }
    & $Python "analysis\run_strength_to_fatigue_ood.py" "--validate-only"
    if ($LASTEXITCODE -ne 0) {
        throw "Strength/fatigue frozen-input validation failed."
    }

    if (Test-Path -LiteralPath $PackagePath) {
        Remove-Item -LiteralPath $PackagePath -Force
    }
    & tar.exe -czf $PackagePath @RequiredFiles
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create the strength/fatigue Balam package."
    }
    $PackageHash = (
        Get-FileHash -Algorithm SHA256 -LiteralPath $PackagePath
    ).Hash.ToLowerInvariant()
    $PackageSizeMB = [math]::Round(
        (Get-Item -LiteralPath $PackagePath).Length / 1MB,
        2
    )
    Write-Host "Package SHA256: $PackageHash"
    Write-Host "Package size: $PackageSizeMB MB"
    if ($DryRun) {
        Write-Host "Dry run complete. Package was not uploaded."
        return
    }

    Write-Host "Balam will request Duo login. Approve the push on your phone."
    $PreviousPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $ScpOutput = & scp $PackagePath "${RemoteHostName}:~/$PackageName" 2>&1
    $ScpExitCode = $LASTEXITCODE
    $ErrorActionPreference = $PreviousPreference
    $ScpOutput | ForEach-Object { Write-Host $_ }
    if ($ScpExitCode -ne 0) {
        throw "Strength/fatigue package upload failed."
    }
    $RemoteCommand = (
        "mkdir -p '$RemoteRoot' && " +
        "mv -f ~/$PackageName '$RemoteRoot/$PackageName' && " +
        "cd '$RemoteRoot' && " +
        "echo '$PackageHash  $PackageName' | sha256sum -c - && " +
        "tar --overwrite -xzf '$PackageName' && " +
        "bash analysis/balam/prepare_and_submit_strength_fatigue_ood.sh"
    )
    $PreviousPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $SshOutput = & ssh $RemoteHostName $RemoteCommand 2>&1
    $SshExitCode = $LASTEXITCODE
    $ErrorActionPreference = $PreviousPreference
    $SshOutput | ForEach-Object { Write-Host $_ }
    if ($SshExitCode -ne 0) {
        throw "Remote strength/fatigue validation or submission failed."
    }
}
finally {
    Stop-Transcript | Out-Null
    Pop-Location
}
