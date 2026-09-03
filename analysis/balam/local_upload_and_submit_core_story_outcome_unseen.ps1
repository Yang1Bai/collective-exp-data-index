param(
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$RemoteHostName = "yangbai@balam.scinet.utoronto.ca"
$RemoteRoot = "/scratch/yangbai/collective-exp-ood"
$PackageName = "core_story_outcome_unseen_balam_package.tar.gz"
$PackagePath = Join-Path $env:TEMP $PackageName

Push-Location $RepoRoot
try {
    & ".\.venv\Scripts\python.exe" "analysis\verify_starrydata_reverse_preoutcome.py"
    if ($LASTEXITCODE -ne 0) { throw "Starrydata pre-outcome verification failed." }
    & ".\.venv\Scripts\python.exe" "analysis\verify_tri_oer_preoutcome.py"
    if ($LASTEXITCODE -ne 0) { throw "TRI OER pre-outcome verification failed." }
    & ".\.venv\Scripts\python.exe" "analysis\prepare_starrydata_matched_source_controls.py"
    if ($LASTEXITCODE -ne 0) { throw "Starrydata matched-control preparation failed." }

    if (Test-Path $PackagePath) { Remove-Item -LiteralPath $PackagePath -Force }
    & tar.exe -czf $PackagePath `
        "analysis/common.py" `
        "analysis/audit_caltech_ionic_external_target.py" `
        "analysis/run_caltech_ionic_external_policy.py" `
        "analysis/prepare_starrydata_reverse_transport.py" `
        "analysis/verify_starrydata_reverse_preoutcome.py" `
        "analysis/run_starrydata_reverse_transport.py" `
        "analysis/prepare_starrydata_matched_source_controls.py" `
        "analysis/run_starrydata_matched_specificity.py" `
        "analysis/verify_starrydata_reverse_transport_results.py" `
        "analysis/STARRYDATA_VERIFIER_AMENDMENT.md" `
        "analysis/starrydata_reverse_transport_design.json" `
        "analysis/starrydata_reverse_transport_implementation.json" `
        "analysis/STARRYDATA_REVERSE_TRANSPORT_SCHEMA_AMENDMENT.md" `
        "analysis/STARRYDATA_FORMAL_EXECUTION_AMENDMENT.md" `
        "analysis/results/starrydata_reverse_PREOUTCOME.json" `
        "analysis/results/starrydata_reverse_target_metadata.csv" `
        "analysis/results/starrydata_reverse_source_predictions.csv" `
        "analysis/results/starrydata_reverse_source_quality.csv" `
        "analysis/results/starrydata_reverse_policy_orders.csv" `
        "analysis/results/starrydata_reverse_hypothesis_cards.csv" `
        "analysis/prepare_caltech_acid_oer_neighbor.py" `
        "analysis/prepare_tri_oer_neighbor.py" `
        "analysis/verify_tri_oer_preoutcome.py" `
        "analysis/run_tri_oer_neighbor.py" `
        "analysis/verify_tri_oer_neighbor_results.py" `
        "analysis/verify_tri_oer_neighbor_results_amended.py" `
        "analysis/TRI_OER_VERIFIER_AMENDMENT.md" `
        "analysis/synthesize_outcome_unseen_validation.py" `
        "analysis/tri_oer_neighbor_design.json" `
        "analysis/tri_oer_implementation.json" `
        "analysis/TRI_OER_PICKLE_SCHEMA_AMENDMENT.md" `
        "analysis/TRI_OER_CLEAN_REPLACEMENT_PROTOCOL.md" `
        "analysis/outcome_unseen_neighbor_validation_program.json" `
        "analysis/results/tri_oer_PREOUTCOME.json" `
        "analysis/results/tri_oer_target_metadata.csv" `
        "analysis/results/tri_oer_source_predictions.csv" `
        "analysis/results/tri_oer_source_quality.csv" `
        "analysis/results/tri_oer_matched_source_controls.csv" `
        "analysis/results/tri_oer_policy_orders.csv" `
        "analysis/results/tri_oer_hypothesis_cards.csv" `
        "scripts/localdb/build_localdb.py" `
        "data/collective.sqlite" `
        "data/external/caltech_ionic/ionic_conductivity_database.csv" `
        "data/external/starrydata_2026-07-17/ThermoelectricMaterials_curves.csv.gz" `
        "data/external/starrydata_2026-07-17/ThermoelectricMaterials_samples.csv.gz" `
        "data/external/starrydata_2026-07-17/ThermoelectricMaterials_papers.csv.gz" `
        "data/external/caltech_acid_oer/extracted/data/OER/oer_all_foms.csv" `
        "data/external/caltech_acid_oer/sources/ORR_catalyst_metrics_MnNiMgCaFeLaYIn.csv" `
        "data/external/tri_oer/tri_data_share.pck" `
        "analysis/balam/requirements.txt" `
        "analysis/balam/run_core_story_outcome_unseen_balam.sh" `
        "analysis/balam/prepare_and_submit_core_story_outcome_unseen.sh"
    if ($LASTEXITCODE -ne 0) { throw "Failed to create core-story Balam package." }

    $PackageHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $PackagePath).Hash.ToLowerInvariant()
    $PackageSizeMB = [math]::Round((Get-Item $PackagePath).Length / 1MB, 2)
    Write-Host "Package SHA256: $PackageHash"
    Write-Host "Package size: $PackageSizeMB MB"
    if ($DryRun) {
        Write-Host "Dry run complete. Package was verified locally and was not uploaded."
        return
    }
    Write-Host "Balam will request Duo login. Do not paste a passcode into chat."
    & scp $PackagePath "${RemoteHostName}:~/$PackageName"
    if ($LASTEXITCODE -ne 0) { throw "Upload to Balam failed." }
    $RemoteCommand = "mkdir -p '$RemoteRoot' && mv ~/$PackageName '$RemoteRoot/$PackageName' && cd '$RemoteRoot' && tar -xzf '$PackageName' && bash analysis/balam/prepare_and_submit_core_story_outcome_unseen.sh"
    & ssh $RemoteHostName $RemoteCommand
    if ($LASTEXITCODE -ne 0) { throw "Remote setup or submission failed." }
}
finally {
    Pop-Location
}
