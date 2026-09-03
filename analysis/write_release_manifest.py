"""Write the final, claim-bearing reproducibility manifest.

Run this after every analysis and figure script. Unlike the legacy manifest
written midway through ``run_confirmatory.py``, this file inventories the
frozen designs, compact scientific outputs, and final figure bundle.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "collective.sqlite"
LOCK = ROOT / "scripts" / "localdb" / "sources.lock.json"
OUTPUT = ROOT / "analysis" / "results" / "manifest.json"

DESIGN_FILES = [
    "analysis/knowledge_map_design.json",
    "analysis/external_confirmation_design.json",
    "analysis/matbench_steels_confirmation_design.json",
    "analysis/kit_temperature_borrowing_design.json",
    "analysis/calisol_external_borrowing_design.json",
    "analysis/calisol_anchored_delta_transfer_design.json",
    "analysis/STRENGTH_LAW_SPEC.md",
    "analysis/ISODB_ISOSTERIC_SPEC.md",
    "analysis/OOD_DECISION_BORROWING_SPEC.md",
    "analysis/ood_decision_borrowing_design.json",
    "analysis/hard_ood_composition_design.json",
    "analysis/obelix_ood_discovery_design.json",
    "analysis/neighbor_transfer_methods_design.json",
    "analysis/neighbor_transfer_policy_design.json",
    "analysis/caltech_ionic_external_policy_design.json",
    "analysis/caltech_ionic_external_policy_implementation.json",
    "analysis/local_gated_neighbor_portfolio_design.json",
    "analysis/family_first_neighbor_portfolio_design.json",
    "analysis/cca_family_first_outcome_unseen_protocol.json",
    "analysis/ood_knowledge_deficit_design.json",
    "analysis/outcome_unseen_neighbor_validation_program.json",
    "analysis/starrydata_reverse_transport_design.json",
    "analysis/starrydata_reverse_transport_implementation.json",
    "analysis/core_story_experiment_registry.json",
    "analysis/target_metadata/starrydata_manifest_2026-07-17.json",
    "analysis/caltech_acid_oer_neighbor_design.json",
    "analysis/tri_oer_neighbor_design.json",
    "analysis/tri_oer_implementation.json",
    "analysis/specgen_derivative_oer_borrowing_design.json",
]

CODE_FILES = [
    ".github/workflows/validate.yml",
    "scripts/localdb/build_localdb.py",
    "scripts/validate_catalog.py",
    "analysis/common.py",
    "analysis/audit_snapshot.py",
    "analysis/run_confirmatory.py",
    "analysis/run_knowledge_map.py",
    "analysis/refine_candidate_permutations.py",
    "analysis/run_external_confirmation.py",
    "analysis/run_external_sensitivities.py",
    "analysis/run_matbench_steels_confirmation.py",
    "analysis/run_kit_temperature_borrowing.py",
    "analysis/run_kit_sample_equivalence_uncertainty.py",
    "analysis/run_calisol_external_borrowing.py",
    "analysis/run_calisol_anchored_delta_transfer.py",
    "analysis/verify_calisol_anchored_delta_transfer.py",
    "analysis/run_strength_law_external.py",
    "analysis/run_isodb_isosteric.py",
    "analysis/run_isodb_universality.py",
    "analysis/run_ood_decision_borrowing.py",
    "analysis/run_hard_ood_composition.py",
    "analysis/write_obelix_ood_discovery_input.py",
    "analysis/run_obelix_ood_discovery.py",
    "analysis/verify_obelix_ood_discovery_results.py",
    "analysis/analyze_obelix_ood_discovery_diagnostics.py",
    "analysis/analyze_neighbor_transfer_signals.py",
    "analysis/run_neighbor_transfer_policy_benchmark.py",
    "analysis/verify_neighbor_transfer_policy_results.py",
    "analysis/audit_neighbor_transfer_policy_results.py",
    "analysis/audit_caltech_ionic_external_target.py",
    "analysis/run_caltech_ionic_external_policy.py",
    "analysis/verify_caltech_ionic_external_policy_results.py",
    "analysis/audit_caltech_ionic_external_policy_results.py",
    "analysis/run_local_gated_neighbor_portfolio.py",
    "analysis/audit_family_first_neighbor_portfolio.py",
    "analysis/run_ood_knowledge_deficit_audit.py",
    "analysis/verify_ood_knowledge_deficit_results.py",
    "analysis/check_core_story_experiments.py",
    "analysis/prepare_starrydata_reverse_transport.py",
    "analysis/verify_starrydata_reverse_preoutcome.py",
    "analysis/run_starrydata_reverse_transport.py",
    "analysis/verify_starrydata_reverse_transport_results.py",
    "analysis/prepare_starrydata_matched_source_controls.py",
    "analysis/run_starrydata_matched_specificity.py",
    "analysis/prepare_caltech_acid_oer_neighbor.py",
    "analysis/prepare_tri_oer_neighbor.py",
    "analysis/verify_tri_oer_preoutcome.py",
    "analysis/run_tri_oer_neighbor.py",
    "analysis/verify_tri_oer_neighbor_results.py",
    "analysis/verify_tri_oer_neighbor_results_amended.py",
    "analysis/synthesize_outcome_unseen_validation.py",
    "analysis/synthesize_knowledge_map.py",
    "analysis/make_data_foundation_figure.py",
    "analysis/make_main_knowledge_map_figure.py",
    "analysis/make_ood_decision_figure.py",
    "analysis/make_caltech_external_policy_figure.py",
    "analysis/make_family_first_neighbor_portfolio_figure.py",
    "analysis/make_outcome_unseen_validation_figure.py",
    "analysis/make_neighbor_map_exploration_figure.py",
    "analysis/make_battery_continuous_borrowing_figure.py",
    "analysis/balam/local_fetch_results.ps1",
    "analysis/balam/local_upload_and_submit.ps1",
    "analysis/balam/prepare_and_submit_balam.sh",
    "analysis/balam/run_obelix_ood_discovery_balam.sh",
    "analysis/balam/local_upload_and_submit_neighbor_policy.ps1",
    "analysis/balam/local_fetch_neighbor_policy_results.ps1",
    "analysis/balam/prepare_and_submit_neighbor_policy.sh",
    "analysis/balam/run_neighbor_transfer_policy_balam.sh",
    "analysis/balam/local_upload_and_submit_caltech_ionic_policy.ps1",
    "analysis/balam/local_upload_and_submit_caltech_verification.ps1",
    "analysis/balam/local_fetch_caltech_ionic_policy_results.ps1",
    "analysis/balam/local_recover_caltech_ionic_policy_results.ps1",
    "analysis/balam/prepare_and_submit_caltech_ionic_policy.sh",
    "analysis/balam/run_caltech_ionic_external_policy_balam.sh",
    "analysis/balam/run_caltech_ionic_external_policy_verify_balam.sh",
    "analysis/balam/local_upload_and_submit_core_story_outcome_unseen.ps1",
    "analysis/balam/local_fetch_core_story_outcome_unseen_results.ps1",
    "analysis/balam/prepare_and_submit_core_story_outcome_unseen.sh",
    "analysis/balam/run_core_story_outcome_unseen_balam.sh",
    "tests/test_analysis_integrity.py",
    "tests/test_caltech_external_protocol.py",
    "tests/test_family_first_neighbor_portfolio.py",
    "tests/test_core_story_registry.py",
    "tests/test_starrydata_verifier.py",
    "tests/test_tri_oer_verifier_amendment.py",
    "tests/test_new_main_figures.py",
    "analysis/run_specgen_derivative_oer_borrowing.py",
    "analysis/run_specgen_composition_secondary.py",
    "analysis/run_specgen_top20_temporal_check.py",
    "analysis/verify_specgen_derivative_results.py",
    "analysis/make_specgen_derivative_oer_figure.py",
    "analysis/write_release_manifest.py",
]

DOCUMENTATION_FILES = [
    "README.md",
    "docs/methodology.md",
    "analysis/README.md",
    "analysis/MANUSCRIPT_DRAFT.md",
    "analysis/MANUSCRIPT_DRAFT_STREAMLINED.md",
    "analysis/SUPPLEMENTARY_INFORMATION.md",
    "analysis/PRESUBMISSION_REVIEW.md",
    "analysis/ADVERSARIAL_REVIEW_RESPONSE.md",
    "analysis/SELECTIVE_NEIGHBOR_BORROWING_STRATEGY.md",
    "analysis/PAPER_PACKAGE.md",
    "analysis/PHASE1_FINDINGS.md",
    "analysis/PHASE2_FINDINGS.md",
    "analysis/PHASE3_FINDINGS.md",
    "analysis/RELATED_WORK.md",
    "analysis/REFERENCES.bib",
    "analysis/CITATION_VERIFICATION.md",
    "analysis/TERMINOLOGY_LEDGER.md",
    "analysis/DATA_FOUNDATION_FIGURE_CONTRACT.md",
    "analysis/DATA_FOUNDATION_FIGURE_QA.md",
    "analysis/FIGURE_CONTRACT.md",
    "analysis/FIGURE_QA.md",
    "analysis/FAMILY_FIRST_FIGURE_CONTRACT.md",
    "analysis/OUTCOME_UNSEEN_FIGURE_CONTRACT.md",
    "analysis/NEIGHBOR_MAP_FIGURE_CONTRACT.md",
    "analysis/NEIGHBOR_MAP_FIGURE_QA.md",
    "analysis/BATTERY_FIGURE_CONTRACT.md",
    "analysis/BATTERY_FIGURE_QA.md",
    "analysis/CCA_FAMILY_FIRST_PROTOCOL.md",
    "analysis/KNOWLEDGE_BORROWING_MAP_SPEC.md",
    "analysis/NEIGHBOR_TRANSFER_METHODS_ROADMAP.md",
    "analysis/NEIGHBOR_TRANSFER_POLICY_VALIDATION.md",
    "analysis/CALTECH_IONIC_EXTERNAL_POLICY_SPEC.md",
    "analysis/CALTECH_IONIC_SCHEMA_AMENDMENT.md",
    "analysis/CALTECH_IONIC_INFERENCE_AMENDMENT.md",
    "analysis/CALTECH_IONIC_IMPLEMENTATION_AMENDMENT_2.md",
    "analysis/CALTECH_IONIC_INFRASTRUCTURE_AMENDMENT_3.md",
    "analysis/CALTECH_IONIC_VERIFIER_AMENDMENT_4.md",
    "analysis/CALTECH_IONIC_REMOTE_VERIFICATION_AMENDMENT_5.md",
    "analysis/CALTECH_IONIC_EXTERNAL_POLICY_VALIDATION.md",
    "analysis/balam/README.md",
    "analysis/balam/requirements.txt",
    "analysis/MATBENCH_STEELS_CONFIRMATION_AMENDMENT.md",
    "analysis/KIT_TEMPERATURE_BORROWING_AMENDMENT.md",
    "analysis/CALISOL_EXTERNAL_BORROWING_AMENDMENT.md",
    "analysis/CALISOL_ANCHORED_DELTA_TRANSFER_PROTOCOL.md",
    "analysis/CALISOL_ANCHORED_DELTA_TRANSFER_FINDINGS.md",
    "analysis/CALISOL_ANCHORED_DELTA_IMPLEMENTATION_AMENDMENT.md",
    "analysis/CALISOL_ANCHORED_DELTA_FIGURE_CONTRACT.md",
    "analysis/CALISOL_ANCHORED_DELTA_FIGURE_QA.md",
    "analysis/CORE_STORY_EXPERIMENT_MATRIX.md",
    "analysis/STARRYDATA_REVERSE_TRANSPORT_SCHEMA_AMENDMENT.md",
    "analysis/STARRYDATA_FORMAL_EXECUTION_AMENDMENT.md",
    "analysis/STARRYDATA_VERIFIER_AMENDMENT.md",
    "analysis/CALTECH_ACID_OER_ACCIDENTAL_ACCESS_AMENDMENT.md",
    "analysis/TRI_OER_CLEAN_REPLACEMENT_PROTOCOL.md",
    "analysis/TRI_OER_PICKLE_SCHEMA_AMENDMENT.md",
    "analysis/TRI_OER_VERIFIER_AMENDMENT.md",
    "analysis/DATASET_CANDIDATE_EDGE_AUDIT_2026-07-30.md",
    "analysis/SPECGEN_DERIVATIVE_OER_BORROWING_PROTOCOL.md",
    "analysis/SPECGEN_COMPOSITION_SECONDARY_AMENDMENT.md",
    "analysis/SPECGEN_TOP20_TEMPORAL_CHECK.md",
    "analysis/SPECGEN_DERIVATIVE_FIGURE_CONTRACT.md",
    "analysis/SPECGEN_DERIVATIVE_FIGURE_QA.md",
]

CLAIM_FILES = [
    "analysis/results/data_lake_profile.csv",
    "analysis/results/data_lake_registered_sources.csv",
    "analysis/results/data_quality_findings.csv",
    "analysis/results/knowledge_map_edges_refined.csv",
    "analysis/results/external_confirmation_edges.csv",
    "analysis/results/external_confirmation_utility_summary.json",
    "analysis/results/matbench_steels_external_summary.json",
    "analysis/results/matbench_steels_external_edges.csv",
    "analysis/results/matbench_steels_external_sensitivity.csv",
    "analysis/results/matbench_steels_external_source_quality.csv",
    "analysis/results/matbench_steels_external_learning_curve.csv",
    "analysis/results/kit_temperature_summary.json",
    "analysis/results/kit_temperature_edges.csv",
    "analysis/results/kit_temperature_sensitivity.csv",
    "analysis/results/kit_temperature_source_quality.csv",
    "analysis/results/kit_temperature_learning_curve.csv",
    "analysis/results/kit_temperature_replicate_structure.csv",
    "analysis/results/kit_temperature_feature_importance.csv",
    "analysis/results/kit_temperature_permutation_null.csv",
    "analysis/results/kit_sample_equivalence_uncertainty.json",
    "analysis/results/kit_sample_equivalence_bootstrap.csv",
    "analysis/results/calisol_external_summary.json",
    "analysis/results/calisol_external_edges.csv",
    "analysis/results/calisol_external_sensitivity.csv",
    "analysis/results/calisol_external_source_quality.csv",
    "analysis/results/calisol_external_source_quality_predictions.csv",
    "analysis/results/calisol_external_learning_curve.csv",
    "analysis/results/calisol_external_temperature_structure.csv",
    "analysis/results/calisol_external_outer_folds.csv",
    "analysis/results/calisol_external_feature_importance.csv",
    "analysis/results/calisol_external_permutation_null.csv",
    "analysis/results/calisol_anchored_delta_summary.json",
    "analysis/results/calisol_anchored_delta_verified.json",
    "analysis/results/calisol_anchored_delta_predictions.csv",
    "analysis/results/calisol_anchored_delta_article_metrics.csv",
    "analysis/results/calisol_anchored_delta_macro_metrics.csv",
    "analysis/results/calisol_anchored_delta_shuffled_null.csv",
    "analysis/results/calisol_anchored_delta_random_anchor_sensitivity.csv",
    "analysis/results/calisol_anchored_delta_leakage_audit.csv",
    "analysis/results/strength_law_summary.json",
    "analysis/results/knowledge_map_synthesis_summary.json",
    "analysis/results/isodb_compensation_summary.json",
    "analysis/results/isodb_universality_summary.json",
    "analysis/results/ood_decision_summary.json",
    "analysis/results/ood_decision_edges.csv",
    "analysis/results/hard_ood_decision_summary.json",
    "analysis/results/hard_ood_decision_edges.csv",
    "analysis/results/obelix_ood_discovery_summary.json",
    "analysis/results/obelix_ood_discovery_edges.csv",
    "analysis/results/obelix_ood_discovery_reach.csv",
    "analysis/results/obelix_ood_discovery_diagnostics.json",
    "analysis/results/obelix_ood_discovery_pairwise_diagnostics.csv",
    "analysis/results/obelix_ood_discovery_survival.csv",
    "analysis/results/obelix_ood_discovery_input_meta.json",
    "analysis/results/obelix_ood_discovery_balam_job.json",
    "analysis/results/obelix_ood_discovery_balam_environment.txt",
    "analysis/results/obelix_ood_discovery_balam_checksums.sha256",
    "analysis/results/obelix_ood_discovery_COMPLETE.json",
    "analysis/results/neighbor_transfer_signal_summary.json",
    "analysis/results/neighbor_transfer_signal_diagnostics.csv",
    "analysis/results/neighbor_transfer_policy_reach.csv",
    "analysis/results/neighbor_transfer_policy_trajectories.csv",
    "analysis/results/neighbor_transfer_policy_contrasts.csv",
    "analysis/results/neighbor_transfer_policy_bootstrap.csv",
    "analysis/results/neighbor_transfer_policy_secondary_utility.csv",
    "analysis/results/neighbor_transfer_policy_summary.json",
    "analysis/results/neighbor_transfer_policy_validation.json",
    "analysis/results/neighbor_transfer_policy_balam_environment.txt",
    "analysis/results/neighbor_transfer_policy_balam_checksums.sha256",
    "analysis/results/neighbor_transfer_policy_COMPLETE.json",
    "analysis/results/caltech_ionic_external_audit.json",
    "analysis/results/caltech_ionic_external_policy_summary.json",
    "analysis/results/caltech_ionic_external_policy_contrasts.csv",
    "analysis/results/caltech_ionic_external_policy_gate_summary.csv",
    "analysis/results/caltech_ionic_external_policy_source_quality.csv",
    "analysis/results/caltech_ionic_external_policy_validation.json",
    "analysis/results/caltech_ionic_external_policy_balam_job.json",
    "analysis/results/caltech_ionic_external_policy_balam_environment.txt",
    "analysis/results/caltech_ionic_external_policy_balam_checksums.sha256",
    "analysis/results/caltech_ionic_external_policy_COMPLETE.json",
    "analysis/results/caltech_ionic_external_policy_VERIFIED.json",
    "analysis/results/caltech_neighbor_portfolio_diagnostic.csv",
    "analysis/results/local_gated_neighbor_portfolio_summary.json",
    "analysis/results/local_gated_neighbor_portfolio_contrasts.csv",
    "analysis/results/family_first_neighbor_portfolio_summary.json",
    "analysis/results/family_first_neighbor_portfolio_metrics.csv",
    "analysis/results/family_first_neighbor_portfolio_orders.csv",
    "analysis/results/family_first_neighbor_portfolio_null.csv",
    "analysis/results/family_first_neighbor_portfolio_figure_source.csv",
    "analysis/results/family_first_neighbor_hypothesis_cards.csv",
    "analysis/results/ood_knowledge_deficit_summary.json",
    "analysis/results/ood_knowledge_deficit_metrics.csv",
    "analysis/results/ood_knowledge_deficit_contrasts.csv",
    "analysis/results/ood_knowledge_deficit_diagnostics.csv",
    "analysis/results/ood_knowledge_deficit_VERIFIED.json",
    "analysis/results/starrydata_reverse_target_metadata.csv",
    "analysis/results/starrydata_reverse_source_predictions.csv",
    "analysis/results/starrydata_reverse_source_quality.csv",
    "analysis/results/starrydata_reverse_policy_orders.csv",
    "analysis/results/starrydata_reverse_hypothesis_cards.csv",
    "analysis/results/starrydata_reverse_PREOUTCOME.json",
    "analysis/results/caltech_acid_oer_PREOUTCOME.json",
    "analysis/results/caltech_acid_oer_target_metadata.csv",
    "analysis/results/caltech_acid_oer_source_predictions.csv",
    "analysis/results/caltech_acid_oer_source_quality.csv",
    "analysis/results/caltech_acid_oer_policy_orders.csv",
    "analysis/results/caltech_acid_oer_hypothesis_cards.csv",
    "analysis/results/tri_oer_PREOUTCOME.json",
    "analysis/results/tri_oer_target_metadata.csv",
    "analysis/results/tri_oer_source_predictions.csv",
    "analysis/results/tri_oer_source_quality.csv",
    "analysis/results/tri_oer_matched_source_controls.csv",
    "analysis/results/tri_oer_policy_orders.csv",
    "analysis/results/tri_oer_hypothesis_cards.csv",
    "analysis/results/starrydata_reverse_summary.json",
    "analysis/results/starrydata_reverse_exploration.csv",
    "analysis/results/starrydata_reverse_hypothesis_tests.csv",
    "analysis/results/starrydata_reverse_matched_specificity_summary.json",
    "analysis/results/starrydata_reverse_COMPLETE.json",
    "analysis/results/starrydata_reverse_VALIDATED.json",
    "analysis/results/tri_oer_summary.json",
    "analysis/results/tri_oer_exploration.csv",
    "analysis/results/tri_oer_hypothesis_tests.csv",
    "analysis/results/tri_oer_COMPLETE.json",
    "analysis/results/tri_oer_VALIDATED.json",
    "analysis/results/outcome_unseen_multi_target_summary.json",
    "analysis/results/core_story_balam_environment.txt",
    "analysis/results/core_story_outcome_unseen_checksums.sha256",
    "analysis/results/figure_data_foundation_inventory.csv",
    "analysis/results/figure_data_foundation_lake.csv",
    "analysis/results/figure_data_foundation_scope.csv",
    "analysis/results/figure_data_foundation_portfolio.csv",
    "analysis/results/specgen_derivative_oer_borrowing_complete.json",
    "analysis/results/specgen_derivative_zero_label_metrics.csv",
    "analysis/results/specgen_composition_secondary_summary.json",
    "analysis/results/specgen_top20_temporal_metrics.csv",
    "analysis/results/specgen_top20_temporal_summary.json",
    "analysis/results/specgen_derivative_verification.json",
    "analysis/results/specgen_derivative_oer_figure_source_data.csv",
    "analysis/results/figure_main_panel_a.csv",
    "analysis/results/figure_main_panel_b.csv",
    "analysis/results/figure_main_panel_c.csv",
    "analysis/results/figure_main_panel_d.csv",
    "analysis/results/figure_ood_decision_panel_a.csv",
    "analysis/results/figure_ood_decision_panel_b.csv",
    "analysis/results/figure_ood_decision_panel_c.csv",
    "analysis/results/figure_caltech_policy_panel_a.csv",
    "analysis/results/figure_caltech_policy_panel_b.csv",
    "analysis/results/figure_caltech_policy_panel_c.csv",
    "analysis/results/figure_outcome_unseen_panel_a.csv",
    "analysis/results/figure_outcome_unseen_panel_b.csv",
    "analysis/results/figure_outcome_unseen_panel_c.csv",
    "analysis/results/figure_outcome_unseen_panel_d.csv",
    "analysis/results/figure_neighbor_map_panel_a.csv",
    "analysis/results/figure_neighbor_map_panel_b.csv",
    "analysis/results/figure_neighbor_map_panel_c.csv",
    "analysis/results/figure_neighbor_map_panel_d.csv",
    "analysis/results/figure_neighbor_map_panel_e.csv",
    "analysis/results/figure_battery_panel_a.csv",
    "analysis/results/figure_battery_panel_b.csv",
    "analysis/results/figure_battery_panel_c.csv",
    "analysis/results/figure_battery_panel_d.csv",
    "analysis/results/figure_battery_panel_e.csv",
    "analysis/results/multistage_battery_stage2/STAGE2_RELEASE_AUDIT.json",
    "analysis/results/multistage_battery_stage2_coverage_sensitivity/analysis/POSTRELEASE_SENSITIVITY_SUMMARY.json",
    "analysis/results/multistage_battery_stage2_coverage_sensitivity/analysis/training_only_gate.csv",
    "analysis/results/multistage_battery_stage2_coverage_sensitivity/postrelease_adjacency_diagnostic/POSTRELEASE_ADJACENCY_DIAGNOSTIC_SUMMARY.json",
    "analysis/results/multistage_battery_stage2_coverage_sensitivity/postrelease_adjacency_diagnostic/condition_borrowing_map.csv",
    "analysis/figures/data_foundation_scope.svg",
    "analysis/figures/data_foundation_scope.pdf",
    "analysis/figures/data_foundation_scope.png",
    "analysis/figures/data_foundation_scope.tiff",
    "analysis/figures/specgen_derivative_oer_transfer.svg",
    "analysis/figures/specgen_derivative_oer_transfer.pdf",
    "analysis/figures/specgen_derivative_oer_transfer.png",
    "analysis/figures/specgen_derivative_oer_transfer.tiff",
    "analysis/figures/main_knowledge_borrowing.svg",
    "analysis/figures/main_knowledge_borrowing.pdf",
    "analysis/figures/main_knowledge_borrowing.png",
    "analysis/figures/main_knowledge_borrowing.tif",
    "analysis/figures/ood_decision_borrowing.svg",
    "analysis/figures/ood_decision_borrowing.pdf",
    "analysis/figures/ood_decision_borrowing.png",
    "analysis/figures/ood_decision_borrowing.tiff",
    "analysis/figures/caltech_external_policy_decomposition.svg",
    "analysis/figures/caltech_external_policy_decomposition.pdf",
    "analysis/figures/caltech_external_policy_decomposition.png",
    "analysis/figures/caltech_external_policy_decomposition.tiff",
    "analysis/figures/family_first_neighbor_portfolio.svg",
    "analysis/figures/family_first_neighbor_portfolio.pdf",
    "analysis/figures/family_first_neighbor_portfolio.png",
    "analysis/figures/family_first_neighbor_portfolio_600dpi.tif",
    "analysis/figures/outcome_unseen_validation.svg",
    "analysis/figures/outcome_unseen_validation.pdf",
    "analysis/figures/outcome_unseen_validation.png",
    "analysis/figures/outcome_unseen_validation.tiff",
    "analysis/figures/neighbor_map_exploration.svg",
    "analysis/figures/neighbor_map_exploration.pdf",
    "analysis/figures/neighbor_map_exploration.png",
    "analysis/figures/neighbor_map_exploration.tiff",
    "analysis/figures/battery_continuous_borrowing.svg",
    "analysis/figures/battery_continuous_borrowing.pdf",
    "analysis/figures/battery_continuous_borrowing.png",
    "analysis/figures/battery_continuous_borrowing.tiff",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_files(paths: list[str]) -> None:
    missing = [path for path in paths if not (ROOT / path).is_file()]
    if missing:
        raise FileNotFoundError("Missing release files: " + ", ".join(missing))


def package_versions() -> dict[str, str]:
    versions: dict[str, str] = {}
    for package in ["numpy", "pandas", "scipy", "scikit-learn", "matplotlib", "rdkit"]:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = "not-installed"
    return versions


def main() -> None:
    require_files(DESIGN_FILES + CODE_FILES + DOCUMENTATION_FILES + CLAIM_FILES)
    if not DB.is_file():
        raise FileNotFoundError("Build data/collective.sqlite before writing the manifest")

    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    with sqlite3.connect(DB) as connection:
        counts = {
            "datasets": connection.execute("SELECT COUNT(*) FROM datasets").fetchone()[0],
            "measurements": connection.execute("SELECT COUNT(*) FROM measurements").fetchone()[0],
            "distinct_properties": connection.execute(
                "SELECT COUNT(DISTINCT property) FROM measurements"
            ).fetchone()[0],
            "distinct_canonical_entities": connection.execute(
                "SELECT COUNT(DISTINCT material_key) FROM measurements"
            ).fetchone()[0],
        }
        metadata = dict(connection.execute("SELECT key,value FROM build_metadata"))
        source_commits = dict(
            connection.execute("SELECT id,source_commit FROM datasets ORDER BY id")
        )

    lock_hash = sha256(LOCK)
    if metadata.get("source_lock_sha256") != lock_hash:
        raise RuntimeError(
            "The database was not built from the current sources.lock.json; rebuild it first"
        )

    artifacts = {
        path: {"sha256": sha256(ROOT / path), "bytes": (ROOT / path).stat().st_size}
        for path in DESIGN_FILES + CODE_FILES + DOCUMENTATION_FILES + CLAIM_FILES
    }
    manifest = {
        "manifest_schema_version": 5,
        "snapshot_date": lock.get("generated_utc"),
        "python": sys.version.split()[0],
        "database": {
            "path": "data/collective.sqlite",
            "schema_version": metadata.get("schema_version"),
            "sha256": sha256(DB),
            **counts,
        },
        "source_lock": {
            "path": "scripts/localdb/sources.lock.json",
            "sha256": lock_hash,
        },
        "source_commits": source_commits,
        "packages": package_versions(),
        "frozen_designs": DESIGN_FILES,
        "analysis_scripts": CODE_FILES,
        "manuscript_documentation": DOCUMENTATION_FILES,
        "claim_artifacts": CLAIM_FILES,
        "artifacts": artifacts,
        "claim_boundary": (
            "Qualified neighboring domains can supply useful and complementary information when "
            "sources are leakage-audited, endpoint-matched, and preserved independently. "
            "A controlled SpecGen OER perturbation series shows the routed mechanism directly: "
            "with five recipient labels, matched composition-relation transfer reduces RMSE by "
            "16.3% and 26.1% in two complete held-out derivative systems, remains ranking-only "
            "in one, and is harmful in another. This within-programme post-primary result is not "
            "four independent replications. KIT "
            "provides a 15% few-shot RMSE reduction with positive absolute utility. On the external "
            "Caltech target, prespecified OBELiX and ESTM rankings recover 2/8 and 3/8 top-5% "
            "entities after formula and DOI exclusions, while mechanical and catalysis controls "
            "recover 0/8; an outcome-informed portfolio covers 5/8, demonstrating complementarity "
            "on the observed target. A subsequent CCA family-first allocation covers 4/4 distinct "
            "top external identity/provenance components and both 2/2 hard-OOD components by "
            "acquisition 20, while deliberately reducing repeated entity hits. All wrong-source "
            "suppression guards pass. CALiSol, Matbench, "
            "OBELiX sequential UCB, and Caltech adaptive residual policies provide the necessary "
            "boundaries: adjacency alone is insufficient, and target-surrogate or acquisition "
            "design can erase source signal. The release therefore supports component-level and "
            "retrospective proof of feasibility for the selective neighborhood-borrowing and "
            "distinct-region exploration strategy, "
            "not a universal distance law. In the protected multi-stage battery programme, the "
            "frozen 23-group primary was non-evaluable because one condition lacked all terminal "
            "endpoints; a disclosed outcome-guided diagnostic nominated continuous upstream "
            "source prediction after a 6.12% condition-RMSE gain over target-only and matched "
            "false-source controls, while the hard gate admitted only 4/22 groups. The integrated "
            "portfolio and continuous policy must be frozen on an outcome-unseen target before "
            "independent prospective acceleration or new science is claimed."
        ),
    }
    OUTPUT.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)} with {len(artifacts)} hashed artifacts")


if __name__ == "__main__":
    main()
