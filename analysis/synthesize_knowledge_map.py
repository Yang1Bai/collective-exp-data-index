"""Synthesize internal and external knowledge-map evidence without threshold drift."""
from __future__ import annotations

import itertools
import json

import numpy as np
import pandas as pd
from scipy import stats

from common import RESULTS, ensure_output_dirs


def target_contrasts(edges: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (evidence_set, target), group in edges.groupby(["evidence_set", "target"]):
        near = group[group["neighborhood"] >= 2]["relative_rmse_improvement_mean"]
        distant = group[group["neighborhood"] == 0]["relative_rmse_improvement_mean"]
        if len(near) and len(distant):
            rows.append({
                "evidence_set": evidence_set,
                "target": target,
                "near_edges_n": len(near),
                "distant_edges_n": len(distant),
                "near_mean_effect": near.mean(),
                "distant_mean_effect": distant.mean(),
                "near_minus_distant": near.mean() - distant.mean(),
            })
    return pd.DataFrame(rows)


def exact_signflip_mean_p(values: np.ndarray) -> float:
    observed = float(values.mean())
    null = [
        float(np.mean(values * np.asarray(signs)))
        for signs in itertools.product((-1.0, 1.0), repeat=len(values))
    ]
    return float((1 + sum(value >= observed for value in null)) / (len(null) + 1))


def main() -> None:
    ensure_output_dirs()
    internal = pd.read_csv(RESULTS / "knowledge_map_edges_refined.csv")
    internal = internal[~internal["relation"].str.contains("calibration")].copy()
    internal["evidence_set"] = "internal-confirmation"
    internal["synthesis_status"] = internal["edge_status_refined"]
    external = pd.read_csv(RESULTS / "external_confirmation_edges.csv")
    external["evidence_set"] = "independent-birdshot"
    external["synthesis_status"] = external["edge_status"]
    map_columns = sorted(set(internal.columns) | set(external.columns))
    map_edges = pd.concat(
        [internal.reindex(columns=map_columns), external.reindex(columns=map_columns)],
        ignore_index=True,
    )
    matbench = pd.read_csv(RESULTS / "matbench_steels_external_edges.csv")
    matbench["evidence_set"] = "independent-matbench"
    matbench["synthesis_status"] = matbench["edge_status"]
    kit = pd.read_csv(RESULTS / "kit_temperature_edges.csv")
    kit["evidence_set"] = "within-campaign-kit-temperature"
    kit["synthesis_status"] = kit["edge_status"]
    calisol = pd.read_csv(RESULTS / "calisol_external_edges.csv")
    calisol["evidence_set"] = "independent-multi-article-calisol"
    calisol["synthesis_status"] = calisol["edge_status"]
    shared_columns = sorted(
        set(map_edges.columns)
        | set(matbench.columns)
        | set(kit.columns)
        | set(calisol.columns)
    )
    edges = pd.concat(
        [
            map_edges.reindex(columns=shared_columns),
            matbench.reindex(columns=shared_columns),
            kit.reindex(columns=shared_columns),
            calisol.reindex(columns=shared_columns),
        ],
        ignore_index=True,
    )
    edges.to_csv(RESULTS / "knowledge_map_synthesis_edges.csv", index=False)

    spearman = stats.spearmanr(
        map_edges["neighborhood"], map_edges["relative_rmse_improvement_mean"]
    )
    contrasts = target_contrasts(map_edges)
    contrasts.to_csv(RESULTS / "knowledge_map_target_contrasts.csv", index=False)
    contrast_values = contrasts["near_minus_distant"].to_numpy(float)
    wilcoxon = stats.wilcoxon(contrast_values, alternative="greater")
    signflip_p = exact_signflip_mean_p(contrast_values)
    leave_one_out_p = []
    for index in range(len(contrast_values)):
        subset = np.delete(contrast_values, index)
        leave_one_out_p.append(float(stats.wilcoxon(subset, alternative="greater").pvalue))

    internal_heterogeneity = pd.read_csv(RESULTS / "knowledge_map_neighborhood_tests.csv")
    heterogeneity = internal_heterogeneity[
        internal_heterogeneity["test"] == "cochran_q_edge_heterogeneity"
    ].iloc[0]
    primary_internal = internal[
        (internal["target"] == "alloy_ys") & (internal["source"] == "alloy_uts")
    ].iloc[0]
    primary_external = external[
        (external["target"] == "birdshot_ys") & (external["source"] == "alloy_uts")
    ].iloc[0]
    utility = json.loads(
        (RESULTS / "external_confirmation_utility_summary.json").read_text(encoding="utf-8")
    )
    matbench_summary = json.loads(
        (RESULTS / "matbench_steels_external_summary.json").read_text(encoding="utf-8")
    )
    kit_summary = json.loads(
        (RESULTS / "kit_temperature_summary.json").read_text(encoding="utf-8")
    )
    kit_equivalence = json.loads(
        (RESULTS / "kit_sample_equivalence_uncertainty.json").read_text(
            encoding="utf-8"
        )
    )
    calisol_summary = json.loads(
        (RESULTS / "calisol_external_summary.json").read_text(encoding="utf-8")
    )
    ood_screening = json.loads(
        (RESULTS / "ood_decision_summary.json").read_text(encoding="utf-8")
    )
    hard_ood_screening = json.loads(
        (RESULTS / "hard_ood_decision_summary.json").read_text(encoding="utf-8")
    )
    ood_discovery = json.loads(
        (RESULTS / "obelix_ood_discovery_summary.json").read_text(encoding="utf-8")
    )
    ood_diagnostics = json.loads(
        (RESULTS / "obelix_ood_discovery_diagnostics.json").read_text(
            encoding="utf-8"
        )
    )
    obelix_screen = next(
        row
        for row in ood_screening["primary_edges"]
        if row["edge_id"]
        == "obelix_official_thermoelectric_zt_to_ionic_conductivity"
    )
    obelix_hard_screen = next(
        row
        for row in hard_ood_screening["primary_edges"]
        if row["edge_id"]
        == "hard_ood_obelix_thermoelectric_zt_to_ionic_conductivity"
    )

    summary = {
        "analysis_status": "post-audit synthesis; adjacency contrast was not the original ordinal primary test",
        "edge_inventory_size": {
            "internal_noncalibration_edges": len(internal),
            "independent_birdshot_edges": len(external),
            "independent_matbench_edges": len(matbench),
            "within_campaign_temperature_edges_including_placebo": len(kit),
            "independent_multi_article_calisol_edges_including_placebo": len(calisol),
            "targets_with_near_and_distant_edges": len(contrasts),
        },
        "map_size": {
            "internal_noncalibration_edges": len(internal),
            "independent_birdshot_edges": len(external),
            "independent_matbench_edges": len(matbench),
            "within_campaign_temperature_edges_including_placebo": len(kit),
            "independent_multi_article_calisol_edges_including_placebo": len(calisol),
            "targets_with_near_and_distant_edges": len(contrasts),
        },
        "core_edge": {
            "internal": {
                "effect_relative_rmse": float(primary_internal["relative_rmse_improvement_mean"]),
                "ci": [float(primary_internal["relative_rmse_ci_lo"]), float(primary_internal["relative_rmse_ci_hi"])],
                "holm_p_999_permutations": float(primary_internal["permutation_p_holm_refined"]),
                "target_sample_fraction_saved": float(primary_internal["target_sample_fraction_saved"]),
                "base_r2": float(primary_internal["base_r2_mean"]),
                "augmented_r2": float(primary_internal["aug_r2_mean"]),
                "screen_status": primary_internal["edge_status_refined"],
                "interpretive_status": "internally-selected-candidate-not-externally-replicated-with-positive-utility",
            },
            "independent_rolling_time": {
                "effect_relative_rmse": float(primary_external["relative_rmse_improvement_mean"]),
                "ci": [float(primary_external["relative_rmse_ci_lo"]), float(primary_external["relative_rmse_ci_hi"])],
                "permutation_p": float(primary_external["primary_permutation_p"]),
                "year1_to_year2_effect": float(primary_external["effect_year1_to_year2"]),
                "years1_2_to_year3_effect": float(primary_external["effect_years1_2_to_year3"]),
                "status": primary_external["edge_status"],
            },
            "independent_matbench": {
                "effect_relative_rmse": matbench_summary["relative_rmse_improvement"],
                "ci": matbench_summary["relative_rmse_ci"],
                "permutation_p": matbench_summary["primary_permutation_p"],
                "pooled_base_r2": matbench_summary["pooled_base_r2"],
                "pooled_augmented_r2": matbench_summary["pooled_augmented_r2"],
                "rescue_claim_supported": matbench_summary["rescue_claim_supported"],
                "status": matbench_summary["decision"],
            },
            "within_campaign_local_rescue": {
                "target": "electrolyte conductivity at -30 C",
                "source": "electrolyte conductivity at -20 C",
                "effect_relative_rmse": kit_summary["relative_rmse_improvement"],
                "ci": kit_summary["relative_rmse_ci"],
                "permutation_p": kit_summary["primary_permutation_p"],
                "pooled_base_r2": kit_summary["pooled_base_r2"],
                "pooled_augmented_r2": kit_summary["pooled_augmented_r2"],
                "target_equivalent_n": kit_summary["target_equivalent_n"],
                "target_sample_fraction_saved": kit_summary["target_sample_fraction_saved"],
                "target_equivalent_n_diagnostic_95": kit_equivalence[
                    "bootstrap_target_equivalent_n_95"
                ],
                "target_sample_fraction_saved_diagnostic_95": kit_equivalence[
                    "bootstrap_target_sample_fraction_saved_95"
                ],
                "probability_fraction_saved_at_least_30pct": kit_equivalence[
                    "bootstrap_probability_fraction_saved_at_least_30pct"
                ],
                "positive_learners_of_three": kit_summary["positive_learners_of_three"],
                "source_feature_importance_mean": kit_summary["source_feature_importance_mean"],
                "source_feature_rank_median": kit_summary["source_feature_rank_median"],
                "temperature_distance_spearman_rho": kit_summary["temperature_distance_spearman_rho"],
                "shuffled_source_effect": kit_summary["shuffled_source_effect"],
                "rescue_claim_supported": kit_summary["rescue_claim_supported"],
                "status": kit_summary["decision"],
                "scope": kit_summary["interpretation_scope"],
            },
            "independent_multi_article_local_boundary": {
                "target": "CALiSol liquid-electrolyte conductivity at -40 C",
                "source": "CALiSol liquid-electrolyte conductivity at -30 C",
                "effect_relative_rmse": calisol_summary["relative_rmse_improvement"],
                "ci": calisol_summary["relative_rmse_ci"],
                "permutation_p_fixed_subset": calisol_summary["primary_permutation_p"],
                "pooled_base_r2": calisol_summary["pooled_base_r2"],
                "pooled_augmented_r2": calisol_summary["pooled_augmented_r2"],
                "target_equivalent_n": calisol_summary["target_equivalent_n"],
                "target_sample_fraction_saved": calisol_summary[
                    "target_sample_fraction_saved"
                ],
                "positive_target_learners_of_three": calisol_summary[
                    "positive_target_learners_of_three"
                ],
                "source_article_oof_r2": calisol_summary[
                    "source_article_oof_r2"
                ],
                "test_articles_seen_by_source_model": calisol_summary[
                    "test_articles_seen_by_source_model"
                ],
                "exact_test_chemistries_seen_by_source_model": calisol_summary[
                    "exact_test_chemistries_seen_by_source_model"
                ],
                "rescue_claim_supported": calisol_summary[
                    "rescue_claim_supported"
                ],
                "status": calisol_summary["decision"],
                "scope": calisol_summary["interpretation_scope"],
            },
        },
        "selectivity": {
            "internal_cochran_q": float(heterogeneity["estimate"]),
            "internal_cochran_q_p": float(heterogeneity["p_value"]),
            "harmful_external_edges": int((external["edge_status"] == "harmful").sum()),
            "practically_equivalent_external_edges": int(
                (external["edge_status"] == "practically-equivalent").sum()
            ),
            "matbench_primary_effect_relative_rmse": matbench_summary[
                "relative_rmse_improvement"
            ],
            "matbench_rescue_claim_supported": matbench_summary[
                "rescue_claim_supported"
            ],
            "kit_distance_control_effects_relative_rmse": {
                str(int(row.source_temperature_C)): float(row.relative_rmse_improvement_mean)
                for row in kit[kit["relation"] == "temperature-distance-control"].itertuples()
            },
            "kit_shuffled_source_effect_relative_rmse": kit_summary[
                "shuffled_source_effect"
            ],
            "calisol_primary_effect_relative_rmse": calisol_summary[
                "relative_rmse_improvement"
            ],
            "calisol_article_hierarchical_ci": calisol_summary[
                "relative_rmse_ci"
            ],
            "calisol_rescue_claim_supported": calisol_summary[
                "rescue_claim_supported"
            ],
            "calisol_distance_control_effects_relative_rmse": {
                str(int(row.source_temperature_C)): float(
                    row.relative_rmse_improvement_mean
                )
                for row in calisol[
                    calisol["relation"] == "temperature-distance-control"
                ].itertuples()
            },
        },
        "absolute_utility": {
            "composition_only_pooled_augmented_r2": utility[
                "rolling_time_composition_only"
            ]["pooled_augmented_r2"],
            "process_aware_effect_relative_rmse": utility[
                "rolling_time_process_aware"
            ]["relative_rmse_improvement"],
            "process_aware_ci": utility["rolling_time_process_aware"][
                "relative_rmse_ci"
            ],
            "process_aware_pooled_augmented_r2": utility[
                "rolling_time_process_aware"
            ]["pooled_augmented_r2"],
            "rescue_claim_supported": utility["rescue_claim_supported"],
            "within_campaign_local_rescue_claim_supported": kit_summary[
                "rescue_claim_supported"
            ],
            "within_campaign_target_sample_fraction_saved": kit_summary[
                "target_sample_fraction_saved"
            ],
            "within_campaign_target_sample_fraction_saved_diagnostic_95": kit_equivalence[
                "bootstrap_target_sample_fraction_saved_95"
            ],
            "independent_multi_article_local_rescue_claim_supported": calisol_summary[
                "rescue_claim_supported"
            ],
            "independent_multi_article_pooled_augmented_r2": calisol_summary[
                "pooled_augmented_r2"
            ],
        },
        "physical_ordering": {
            "ordinal_spearman_rho": float(spearman.statistic),
            "ordinal_spearman_p": float(spearman.pvalue),
            "target_level_near_minus_distant_mean": float(contrast_values.mean()),
            "target_level_near_minus_distant_median": float(np.median(contrast_values)),
            "targets_positive_of_total": [int((contrast_values > 0).sum()), len(contrast_values)],
            "wilcoxon_one_sided_p": float(wilcoxon.pvalue),
            "exact_signflip_mean_p": signflip_p,
            "leave_one_target_out_wilcoxon_p_range": [min(leave_one_out_p), max(leave_one_out_p)],
            "decision": (
                "Binary direct-neighbor versus distant-control ordering is exploratory-positive, "
                "but the pre-existing 0-3 ordinal score is not statistically established and the "
                "target-level result is leave-one-target-out fragile."
            ),
            "kit_temperature_distance_spearman_rho": kit_summary[
                "temperature_distance_spearman_rho"
            ],
            "kit_distance_ordering_scope": (
                "Frozen within-target controls support monotonic local distance decay; "
                "this is not a universal cross-domain distance calibration."
            ),
            "calisol_temperature_distance_spearman_rho": calisol_summary[
                "temperature_distance_spearman_rho"
            ],
            "calisol_distance_ordering_scope": (
                "Paper-disjoint CALiSol controls do not preserve monotonic temperature-distance "
                "ordering, so the KIT decay cannot be exported across experimental articles."
            ),
        },
        "decision_endpoints": {
            "obelix_fixed_ood_screening": {
                "baseline_fraction_to_first_hit": obelix_screen[
                    "baseline_fraction_to_first_hit_mean"
                ],
                "augmented_fraction_to_first_hit": obelix_screen[
                    "augmented_fraction_to_first_hit_mean"
                ],
                "effect": obelix_screen["effect_fraction_to_first_hit_mean"],
                "effect_95": obelix_screen[
                    "effect_fraction_to_first_hit_bootstrap_95"
                ],
                "holm_p": obelix_screen["holm_p_primary_family"],
                "status": obelix_screen["decision_status"],
                "passes_improvement_gates": obelix_screen[
                    "passes_improvement_gates"
                ],
            },
            "obelix_hard_ood_screening": {
                "baseline_fraction_to_first_hit": obelix_hard_screen[
                    "baseline_fraction_to_first_hit_mean"
                ],
                "augmented_fraction_to_first_hit": obelix_hard_screen[
                    "augmented_fraction_to_first_hit_mean"
                ],
                "effect": obelix_hard_screen[
                    "effect_fraction_to_first_hit_mean"
                ],
                "effect_95": obelix_hard_screen[
                    "effect_fraction_to_first_hit_bootstrap_95"
                ],
                "status": obelix_hard_screen["decision_status"],
                "claim_guard": hard_ood_screening["selection_history"],
            },
            "obelix_sequential_discovery": ood_discovery[
                "primary_official_test_result"
            ],
            "obelix_sequential_random_reference": {
                "prespecified_target_only_comparison": ood_discovery[
                    "official_test_controls"
                ]["random_control"],
                "exact_random_reference": ood_diagnostics["random_reference"][
                    "official_test"
                ],
                "claim_guard": ood_diagnostics["claim_guard"],
            },
        },
        "claim_boundary": (
            "Qualified neighboring domains can supply useful and complementary information when "
            "the source is leakage-audited, matched to the endpoint, and preserved independently. "
            "In KIT, an adjacent-temperature prior improves few-shot error by about 15% with "
            "positive absolute utility. In the external Caltech target, prespecified OBELiX and "
            "ESTM rankings recover 2/8 and 3/8 top-5% entities after formula and DOI exclusions, "
            "while mechanical and catalysis controls recover 0/8; an outcome-informed portfolio "
            "covers 5/8, demonstrating complementarity on the observed target. Wrong-source guards "
            "also pass. CALiSol, Matbench, OBELiX sequential UCB, and Caltech adaptive residual "
            "policies define the boundaries: adjacency alone is insufficient, and weak target "
            "surrogates or acquisition rules can erase useful source signal. Together, these results "
            "provide component-level and retrospective proof of feasibility for a selective "
            "neighborhood-borrowing strategy and instantiate an artifact-gated decision map over "
            "tested directed edges. Outcome-unseen Starrydata and TRI tests do not pass their complete "
            "prediction, policy, or hypothesis gates; their pooled effect is null and heterogeneous. "
            "The integrated portfolio therefore requires a genuinely temporal or prospective test "
            "before it can establish independent acceleration or new science."
        ),
    }
    (RESULTS / "knowledge_map_synthesis_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
