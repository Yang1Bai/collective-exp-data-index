#!/usr/bin/env python3
"""Build quantitative transferability evidence cards from frozen results.

This module is deliberately outside the model and training paths.  It does not
fit, calibrate, or replace a learner.  It only turns already archived recipient
evaluations into endpoint-specific, machine-readable evidence cards.

The cards avoid a synthetic 0--100 "transferability score".  Instead they keep
data support, absolute-value utility, ranking utility, falsifier specificity,
and uncertainty separate so that the reported route remains auditable.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "analysis" / "results"
MIN_ENDPOINT_GAIN = 0.10
MAX_ADJUSTED_P = 0.05


def _read_json(name: str) -> dict[str, Any]:
    with (RESULTS / name).open(encoding="utf-8") as handle:
        return json.load(handle)


def _read_analysis_json(name: str) -> dict[str, Any]:
    with (ROOT / "analysis" / name).open(encoding="utf-8") as handle:
        return json.load(handle)


def _interval(values: list[float]) -> dict[str, float]:
    return {"low": float(values[0]), "high": float(values[1])}


def choose_evidence_decision(
    *, absolute_prediction_supported: bool, candidate_ranking_supported: bool
) -> str:
    """Select the highest-resolution endpoint whose frozen gates pass."""

    if absolute_prediction_supported:
        return "predict"
    if candidate_ranking_supported:
        return "rank"
    return "withhold"


def build_cards() -> list[dict[str, Any]]:
    """Return evidence cards for the three frozen electrolyte recipients."""

    applicability = _read_json("bamboomixer_applicability_domain_summary.json")
    liasf6 = _read_json("bamboomixer_LiAsF6_only_summary.json")
    cross_programme = _read_json(
        "bamboomixer_cross_database_interaction_summary.json"
    )
    cross_input_audit = _read_json(
        "bamboomixer_cross_database_interaction_input_audit.json"
    )
    cross_design = _read_analysis_json(
        "bamboomixer_cross_database_interaction_design.json"
    )
    recipient_stress = _read_json(
        "bamboomixer_recipient_baseline_stress_test_summary.json"
    )
    finales = _read_json("finales_rank_replication_summary.json")

    li_metrics = liasf6["corrected_external_metrics"]
    li_contrasts = liasf6["corrected_contrasts"]
    li_state = li_contrasts["state_only"]
    li_shuffle = li_contrasts["chemistry_permuted"]
    li_support = applicability["explicit_state_support"]

    solvent = cross_programme["solventseg"]
    solvent_prediction = solvent["routing"]["prediction_gate"]
    solvent_fixed = solvent["fixed_25_C"]["programme_balanced_portfolio"]
    solvent_rank = recipient_stress["five_anchor"]["source_portfolio"]
    solvent_baseline = recipient_stress["five_anchor"]["recipient_macro"][0]
    solvent_advantage = recipient_stress["five_anchor"][
        "source_minus_strongest_spearman"
    ]
    solvent_p = solvent["rank_permutation_p"]["programme_balanced_portfolio"]

    finales_primary = finales["primary"]

    li_absolute_supported = all(
        (
            li_support["temperature_C"]["target_fraction_inside_source_range"]
            == 1.0,
            li_support["salt_molar_ratio"]["target_fraction_inside_source_range"]
            == 1.0,
            applicability["full_representation"][
                "target_fraction_within_reference_q95"
            ]
            > 0.0,
            li_state["relative_log_rmse_gain_ci95"][0] > 0.0,
            li_shuffle["relative_log_rmse_gain_ci95"][0] > 0.0,
        )
    )
    solvent_absolute_supported = all(
        (
            solvent_prediction["portfolio_vs_state_relative_log_rmse_gain"]
            >= MIN_ENDPOINT_GAIN,
            solvent_prediction[
                "portfolio_vs_state_relative_log_rmse_gain_ci95"
            ][0]
            > 0.0,
            solvent_prediction[
                "five_anchor_vs_target_only_relative_log_rmse_gain"
            ]
            >= MIN_ENDPOINT_GAIN,
            solvent_prediction[
                "five_anchor_vs_target_only_relative_log_rmse_gain_ci95"
            ][0]
            > 0.0,
            solvent_prediction["portfolio_log_r2"] > 0.0,
            solvent_prediction[
                "portfolio_vs_permuted_relative_log_rmse_gain"
            ]
            > 0.0,
            solvent_prediction[
                "portfolio_vs_permuted_relative_log_rmse_gain_ci95"
            ][0]
            > 0.0,
        )
    )
    solvent_ranking_supported = all(
        (
            not solvent_absolute_supported,
            solvent_advantage["mean"] >= MIN_ENDPOINT_GAIN,
            solvent_advantage["ci95"][0] > 0.0,
            solvent_p["holm_p"] <= MAX_ADJUSTED_P,
            solvent_rank["top_quartile_precision"]
            > solvent_baseline["top_quartile_precision"],
            solvent_rank["normalized_regret"]
            < solvent_baseline["normalized_regret"],
        )
    )
    solvent_decision = choose_evidence_decision(
        absolute_prediction_supported=solvent_absolute_supported,
        candidate_ranking_supported=solvent_ranking_supported,
    )
    stored_solvent_decision = {
        "prediction": "predict",
        "ranking": "rank",
        "abstain": "withhold",
    }.get(solvent["routing"]["decision"])
    if stored_solvent_decision != solvent_decision:
        raise ValueError(
            "recomputed SolventSeg gate disagrees with the frozen routing decision"
        )

    finales_ranking_supported = finales["success_gate_passed"]
    if not isinstance(finales_ranking_supported, bool):
        raise TypeError("FINALES success_gate_passed must be boolean")
    if finales_ranking_supported != all(finales["gates"].values()):
        raise ValueError("FINALES success gate disagrees with its stored gate booleans")

    return [
        {
            "recipient": "LiAsF6",
            "transferred_object": "chemistry-state-conductivity relation",
            "evidence_status": "retrospective external benchmark",
            "source_artifacts": [
                "analysis/results/bamboomixer_applicability_domain_summary.json",
                "analysis/results/bamboomixer_LiAsF6_only_summary.json",
            ],
            "data_support": {
                "source_rows": applicability["source_rows"],
                "source_salts": applicability["source_salts"],
                "recipient_rows": applicability["target_rows"],
                "recipient_formulations": applicability[
                    "target_exact_formulations"
                ],
                "exact_salt_identity_overlap_fraction": 0.0,
                "solvent_identity_overlap_fraction": li_support[
                    "target_solvent_identity_fraction_seen_in_source"
                ],
                "temperature_inside_source_range_fraction": li_support[
                    "temperature_C"
                ]["target_fraction_inside_source_range"],
                "concentration_inside_source_range_fraction": li_support[
                    "salt_molar_ratio"
                ]["target_fraction_inside_source_range"],
                "full_representation_inside_donor_q95_fraction": applicability[
                    "full_representation"
                ]["target_fraction_within_reference_q95"],
                "salt_descriptor_reference_percentile": applicability[
                    "salt_descriptor"
                ]["target_distance_reference_percentile"],
            },
            "absolute_endpoint": {
                "raw_r2": li_metrics["raw_r2"],
                "spearman": li_metrics["spearman"],
                "relative_log_rmse_gain_vs_state_only": li_state[
                    "relative_log_rmse_gain_mean"
                ],
                "relative_log_rmse_gain_vs_state_only_ci95": _interval(
                    li_state["relative_log_rmse_gain_ci95"]
                ),
                "relative_log_rmse_gain_vs_chemistry_permuted": li_shuffle[
                    "relative_log_rmse_gain_mean"
                ],
                "relative_log_rmse_gain_vs_chemistry_permuted_ci95": _interval(
                    li_shuffle["relative_log_rmse_gain_ci95"]
                ),
            },
            "rank_endpoint": {
                "spearman": li_metrics["spearman"],
                "spearman_gain_vs_state_only": li_state["spearman_gain_mean"],
                "spearman_gain_vs_state_only_ci95": _interval(
                    li_state["spearman_gain_ci95"]
                ),
            },
            "gate_evaluation": {
                "absolute_prediction_supported": li_absolute_supported,
                "candidate_ranking_supported": False,
            },
            "decision": choose_evidence_decision(
                absolute_prediction_supported=li_absolute_supported,
                candidate_ranking_supported=False,
            ),
            "reason_codes": [
                "STATE_FULLY_SUPPORTED",
                "REPRESENTATION_PARTIALLY_SUPPORTED",
                "ABSOLUTE_GAIN_CI_ABOVE_ZERO",
                "CHEMISTRY_SPECIFICITY_CI_ABOVE_ZERO",
                "UNSEEN_IDENTITY_BUT_DESCRIPTOR_SUPPORTED",
            ],
            "plain_language_reason": (
                "The salt identity is unseen, but temperature and concentration are "
                "fully covered, "
                f"{100 * applicability['full_representation']['target_fraction_within_reference_q95']:.1f}% "
                "of recipient rows lie inside the donor's relation-distance boundary, "
                "and the lower confidence bounds for both state-only and "
                "chemistry-shuffled comparisons remain positive."
            ),
        },
        {
            "recipient": "SolventSeg",
            "transferred_object": "programme-balanced candidate order",
            "evidence_status": "post-outcome cross-programme method development",
            "source_artifacts": [
                "analysis/bamboomixer_cross_database_interaction_design.json",
                "analysis/results/bamboomixer_cross_database_interaction_input_audit.json",
                "analysis/results/bamboomixer_cross_database_interaction_summary.json",
                "analysis/results/bamboomixer_recipient_baseline_stress_test_summary.json",
            ],
            "data_support": {
                "source_programmes": 3,
                "recipient_rows": cross_input_audit["solventseg_rows"],
                "recipient_formulations": cross_input_audit[
                    "solventseg_formulations"
                ],
                "recipient_temperatures": len(
                    cross_design["inputs"]["solventseg"]["temperatures_C"]
                ),
                "strict_record_overlap_count": sum(
                    cross_input_audit["strict_record_overlap_counts"][key]
                    for key in (
                        "bamboo_to_solventseg",
                        "calisol_to_solventseg",
                        "kit_to_solventseg",
                    )
                ),
                "recipient_labels_used_by_source_rank": 0,
                "recipient_anchor_budget_for_baseline": 5,
            },
            "absolute_endpoint": {
                "relative_log_rmse_gain_vs_state_only": solvent_prediction[
                    "portfolio_vs_state_relative_log_rmse_gain"
                ],
                "relative_log_rmse_gain_vs_state_only_ci95": _interval(
                    solvent_prediction[
                        "portfolio_vs_state_relative_log_rmse_gain_ci95"
                    ]
                ),
                "relative_log_rmse_gain_vs_chemistry_permuted": solvent_prediction[
                    "portfolio_vs_permuted_relative_log_rmse_gain"
                ],
                "relative_log_rmse_gain_vs_chemistry_permuted_ci95": _interval(
                    solvent_prediction[
                        "portfolio_vs_permuted_relative_log_rmse_gain_ci95"
                    ]
                ),
            },
            "rank_endpoint": {
                "all_formulations_25C_spearman": solvent_fixed["spearman"],
                "all_formulations_25C_top_quartile_precision": solvent_fixed[
                    "top_quartile_precision"
                ],
                "five_anchor_source_spearman": solvent_rank["spearman"],
                "five_anchor_recipient_baseline_spearman": solvent_baseline[
                    "spearman"
                ],
                "source_minus_recipient_spearman": solvent_advantage["mean"],
                "source_minus_recipient_spearman_ci95": _interval(
                    solvent_advantage["ci95"]
                ),
                "source_top_quartile_precision": solvent_rank[
                    "top_quartile_precision"
                ],
                "recipient_top_quartile_precision": solvent_baseline[
                    "top_quartile_precision"
                ],
                "source_normalized_regret": solvent_rank["normalized_regret"],
                "recipient_normalized_regret": solvent_baseline[
                    "normalized_regret"
                ],
                "holm_adjusted_permutation_p": solvent_p["holm_p"],
            },
            "gate_evaluation": {
                "absolute_prediction_supported": solvent_absolute_supported,
                "candidate_ranking_supported": solvent_ranking_supported,
            },
            "decision": solvent_decision,
            "reason_codes": [
                "NO_EXACT_FORMULATION_OVERLAP",
                "ABSOLUTE_SCALE_NOT_SUPPORTED",
                "RANK_ADVANTAGE_CI_ABOVE_ZERO",
                "RANK_PERMUTATION_SIGNIFICANT",
                "SHORTLIST_UTILITY_IMPROVED",
            ],
            "plain_language_reason": (
                "Programme shift breaks absolute calibration: the source portfolio is "
                f"{abs(100 * solvent_prediction['portfolio_vs_state_relative_log_rmse_gain']):.1f}% "
                "worse than state-only on log-RMSE. Candidate order survives: "
                "with zero recipient labels the source rank exceeds the strongest "
                "five-label recipient model by "
                f"{solvent_advantage['mean']:.3f} Spearman units, and the full 95% "
                "interval remains above zero."
            ),
        },
        {
            "recipient": "FINALES",
            "transferred_object": "unchanged candidate order replication",
            "evidence_status": "frozen retrospective replication",
            "source_artifacts": [
                "analysis/results/finales_rank_replication_summary.json"
            ],
            "data_support": {
                "recipient_formulations": finales_primary[
                    "evaluation_formulations"
                ],
                "eligible_temperature_matched_pairs": finales_primary[
                    "eligible_pairs"
                ],
                "recipient_anchor_budget": finales_primary["anchors"],
                "temperature_tolerance_C": finales_primary[
                    "temperature_tolerance_C"
                ],
                "recipient_doi_absent_from_donor": finales["gates"][
                    "recipient_doi_absent_from_donor"
                ],
            },
            "absolute_endpoint": {"evaluated": False},
            "rank_endpoint": {
                "donor_concordance": finales_primary["donor_concordance"],
                "recipient_baseline_concordance": finales_primary[
                    "strongest_baseline_concordance"
                ],
                "donor_minus_recipient_concordance": finales_primary[
                    "concordance_advantage"
                ],
                "donor_minus_recipient_concordance_ci95": _interval(
                    finales_primary["bootstrap_ci95"]
                ),
                "donor_top_quartile_precision": finales_primary[
                    "donor_top_quartile_precision"
                ],
                "recipient_top_quartile_precision": finales_primary[
                    "baseline_top_quartile_precision"
                ],
                "donor_normalized_regret": finales_primary[
                    "donor_normalized_regret"
                ],
                "recipient_normalized_regret": finales_primary[
                    "baseline_normalized_regret"
                ],
                "permutation_p": finales_primary["permutation_p"],
            },
            "gate_evaluation": {
                "absolute_prediction_supported": False,
                "candidate_ranking_supported": finales_ranking_supported,
            },
            "decision": choose_evidence_decision(
                absolute_prediction_supported=False,
                candidate_ranking_supported=finales_ranking_supported,
            ),
            "reason_codes": [
                "RANK_ADVANTAGE_NOT_POSITIVE",
                "RANK_ADVANTAGE_CI_CROSSES_ZERO",
                "PERMUTATION_NOT_SIGNIFICANT",
                "SHORTLIST_PRECISION_NOT_IMPROVED",
                "REGRET_WORSE_THAN_RECIPIENT_BASELINE",
            ],
            "plain_language_reason": (
                "The donor order is weaker than the three-anchor recipient baseline; "
                f"its advantage is {finales_primary['concordance_advantage']:.3f}, its "
                "95% interval crosses zero, the permutation test is not significant "
                f"(P={finales_primary['permutation_p']:.3f}), and regret is "
                f"{finales_primary['donor_normalized_regret']:.3f} versus "
                f"{finales_primary['baseline_normalized_regret']:.3f}. This recipient "
                "therefore supplies quantitative evidence to withhold transfer."
            ),
        },
    ]


def _flatten(prefix: str, value: Any, output: dict[str, Any]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else key
            _flatten(child_prefix, child, output)
    elif isinstance(value, list):
        output[prefix] = ";".join(str(item) for item in value)
    else:
        output[prefix] = value


def write_outputs(cards: list[dict[str, Any]]) -> tuple[Path, Path, Path]:
    json_path = RESULTS / "transferability_evidence_cards.json"
    csv_path = RESULTS / "transferability_evidence_cards.csv"
    report_path = ROOT / "analysis" / "TRANSFERABILITY_EVIDENCE_CARDS.md"

    payload = {
        "schema_version": 1,
        "model_or_training_changes": False,
        "aggregation_policy": (
            "No universal score. Support, endpoint utility, specificity, and "
            "uncertainty remain separate."
        ),
        "cards": cards,
    }
    json_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    flat_cards: list[dict[str, Any]] = []
    fieldnames: list[str] = []
    for card in cards:
        flat: dict[str, Any] = {}
        _flatten("", card, flat)
        flat_cards.append(flat)
        for key in flat:
            if key not in fieldnames:
                fieldnames.append(key)
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(flat_cards)

    report_path.write_text(_render_report(cards), encoding="utf-8")
    return json_path, csv_path, report_path


def _pct(value: float) -> str:
    return f"{100.0 * value:.1f}%"


def _render_report(cards: list[dict[str, Any]]) -> str:
    li, solvent, finales = cards
    li_support = li["data_support"]
    li_abs = li["absolute_endpoint"]
    sol_abs = solvent["absolute_endpoint"]
    sol_rank = solvent["rank_endpoint"]
    fin_rank = finales["rank_endpoint"]

    return f"""# Quantitative transferability evidence cards

These cards are a reporting layer over the frozen analyses. They do not alter
the original code, models, training, hyperparameters, or default routing. They
also do not claim that transferability can be reduced to a universal 0--100
score. Each card reports the observed support and effect for a particular
donor--recipient relation and decision endpoint.

| Recipient | Quantitative data support | Observed endpoint evidence | Route |
|---|---|---|---|
| LiAsF6 | Salt overlap 0%; solvent overlap {_pct(li_support['solvent_identity_overlap_fraction'])}; temperature and concentration coverage 100%; {_pct(li_support['full_representation_inside_donor_q95_fraction'])} within donor q95 relation boundary | log-RMSE gain vs state-only {_pct(li_abs['relative_log_rmse_gain_vs_state_only'])} (95% CI {_pct(li_abs['relative_log_rmse_gain_vs_state_only_ci95']['low'])} to {_pct(li_abs['relative_log_rmse_gain_vs_state_only_ci95']['high'])}); raw R2 {li_abs['raw_r2']:.3f}; rho {li_abs['spearman']:.3f}; gain vs chemistry-shuffled {_pct(li_abs['relative_log_rmse_gain_vs_chemistry_permuted'])} | **predict** |
| SolventSeg | 3 separate source programmes; 36 recipient formulations at 5 temperatures; exact formulation overlap 0%; source ranking uses 0 recipient labels | absolute log-RMSE gain vs state-only {_pct(sol_abs['relative_log_rmse_gain_vs_state_only'])}; five-anchor rank rho {sol_rank['five_anchor_source_spearman']:.3f} vs {sol_rank['five_anchor_recipient_baseline_spearman']:.3f}; delta {sol_rank['source_minus_recipient_spearman']:.3f} (95% CI {sol_rank['source_minus_recipient_spearman_ci95']['low']:.3f} to {sol_rank['source_minus_recipient_spearman_ci95']['high']:.3f}); top-quartile precision {sol_rank['source_top_quartile_precision']:.3f} vs {sol_rank['recipient_top_quartile_precision']:.3f} | **rank** |
| FINALES | 16 evaluation formulations; 98 temperature-matched pairs; 3 recipient anchors; donor and recipient DOI do not overlap | donor concordance {fin_rank['donor_concordance']:.3f} vs recipient {fin_rank['recipient_baseline_concordance']:.3f}; delta {fin_rank['donor_minus_recipient_concordance']:.3f} (95% CI {fin_rank['donor_minus_recipient_concordance_ci95']['low']:.3f} to {fin_rank['donor_minus_recipient_concordance_ci95']['high']:.3f}); p={fin_rank['permutation_p']:.3f}; regret {fin_rank['donor_normalized_regret']:.3f} vs {fin_rank['recipient_normalized_regret']:.3f} | **withhold** |

## Interpretation

- **LiAsF6:** Transfer is not justified by exact identity overlap. It is
  justified by complete experimental-state coverage, partial relation-space
  support, and positive lower confidence bounds against both a state-only
  baseline and a chemistry-destroyed control. The supported object is an
  absolute chemistry--state relation.
- **SolventSeg:** Cross-programme scale shift defeats absolute prediction, but
  the zero-label candidate order remains stronger than the best fixed
  five-label recipient baseline. The supported object is ordinal ranking only.
- **FINALES:** Having enough evaluable pairs does not imply transferability.
  The frozen donor order loses to the recipient baseline and fails uncertainty,
  significance, precision, and regret checks. The supported action is to
  withhold.

## Recommended manuscript use

Use the support columns to explain *why the source data are relevant*, and the
endpoint columns to establish *what level of reuse is empirically allowed*.
Keep the route recipient-specific. These values describe evaluated relations;
they are not a prospective selector for an unseen programme until the same
fields and thresholds are frozen and validated prospectively.
"""


def main() -> None:
    paths = write_outputs(build_cards())
    for path in paths:
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
