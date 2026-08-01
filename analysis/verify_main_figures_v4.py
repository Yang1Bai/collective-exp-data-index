"""Semantic verification for the five-figure canonical manuscript set."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "analysis" / "results"
FIGURES = ROOT / "analysis" / "figures"
SOURCE = FIGURES / "source_data"
REPORT = RESULTS / "main_figures_v4_verification.json"


def close(actual: float, expected: float, tolerance: float = 5e-6) -> None:
    if not np.isclose(actual, expected, atol=tolerance, rtol=0):
        raise AssertionError(f"numeric mismatch: {actual} != {expected}")


def source_value(frame: pd.DataFrame, route: str, metric: str) -> float:
    row = frame[(frame.route == route) & (frame.metric == metric)]
    if len(row) != 1:
        raise AssertionError(f"expected one Figure 1 source row for {route}:{metric}")
    return float(row.iloc[0].value)


def main() -> None:
    expected_files: list[str] = []
    for stem in [
        "knowledge_borrowing_overview_ai_v4",
        "figure2_failure_benchmark_nmi_v3",
        "figure3_relation_transfer_nmi_v3",
        "figure4_routing_nmi_v4",
        "figure5_ordinal_screening_nmi_v4",
    ]:
        for suffix in ["pdf", "svg", "png", "tiff"]:
            path = FIGURES / f"{stem}.{suffix}"
            if not path.exists() or path.stat().st_size == 0:
                raise AssertionError(f"missing or empty figure export: {path}")
            expected_files.append(str(path.relative_to(ROOT)))

    fig1 = pd.read_csv(SOURCE / "knowledge_borrowing_overview_ai_v4.csv")
    close(source_value(fig1, "predict", "relative_log_rmse_gain"), 27.41, .005)
    close(source_value(fig1, "predict", "raw_r2"), .607, .0005)
    close(source_value(fig1, "predict", "spearman"), .864, .0005)
    close(source_value(fig1, "screen", "recipient_spearman"), .537, .0005)
    close(source_value(fig1, "screen", "borrowed_spearman"), .910, .0005)
    close(source_value(fig1, "screen", "recipient_precision_top_quartile"), .490, .0005)
    close(source_value(fig1, "screen", "borrowed_precision_top_quartile"), .933, .0005)
    close(source_value(fig1, "abstain", "frozen_donor_score"), .694, .0005)
    close(source_value(fig1, "abstain", "frozen_recipient_score"), .783, .0005)

    fig2 = pd.read_csv(SOURCE / "figure2_failure_benchmark_nmi_v3.csv")
    edges = pd.read_csv(RESULTS / "multi_target_ood_edge_summary.csv")
    real_edges = int((~edges["is_shuffled_control"].astype(bool)).sum())
    if real_edges != 40:
        raise AssertionError("Figure 2 benchmark must contain 40 real edges")
    close(float(fig2.loc[fig2.measure.eq("source_internal_r2"), "estimate"].iloc[0]), .790, .001)
    close(float(fig2.loc[fig2.measure.eq("transported_r2"), "estimate"].iloc[0]), -3.006, .001)

    catalyst = pd.read_csv(RESULTS / "specgen_derivative_oer_figure_source_data.csv")
    expected_catalyst = {"A": .0319129679, "B": .1634878300, "C": -.1037707991, "D": .2607354444}
    for target, expected in expected_catalyst.items():
        value = catalyst[(catalyst.target.eq(target)) &
                         (catalyst.measure.eq("relative_rmse_gain"))].estimate.iloc[0]
        close(float(value), expected)

    external = pd.read_csv(RESULTS / "bamboomixer_LiAsF6_only_external_metrics.csv").set_index("scope")
    close(float(external.loc["all_source_salts", "raw_r2"]), .6070800827)
    close(float(external.loc["all_source_salts", "spearman"]), .8639511089)
    external_predictions = pd.read_csv(RESULTS / "bamboomixer_LiAsF6_only_external_predictions.csv")
    external_primary = external_predictions[external_predictions["scope"].eq("all_source_salts")]
    if len(external_primary) != 1660 or external_primary["formula_group"].nunique() != 156:
        raise AssertionError("Figure 3 must use 1,660 strict LiAsF6 rows and 156 formulations")

    stress = pd.read_csv(RESULTS / "bamboomixer_recipient_baseline_stress_test_metrics.csv")
    five = stress[stress.anchor_budget.eq(5)]
    source_rows = five[five.model.eq("programme_balanced_source_portfolio")]
    source_rho = float(source_rows.spearman.mean())
    source_precision = float(source_rows.top_quartile_precision.mean())
    recipient = five[five.model.eq("rbf_kernel_ridge_alpha_10")]
    recipient_rho = float(recipient.spearman.mean())
    recipient_precision = float(recipient.top_quartile_precision.mean())
    close(source_rho, .9102998261)
    close(source_precision, .9325)
    close(recipient_rho, .5366383641)
    close(recipient_precision, .49)

    finales = json.loads((RESULTS / "finales_rank_replication_summary.json").read_text(encoding="utf-8"))
    donor_concordance = float(finales["primary"]["donor_concordance"])
    recipient_concordance = float(finales["primary"]["strongest_baseline_concordance"])
    close(donor_concordance, .6938775510)
    close(recipient_concordance, .7826086957)

    report = {
        "status": "verified-complete",
        "canonical_exports": expected_files,
        "figure1_routes": ["predict", "screen", "abstain"],
        "figure2_real_edges": real_edges,
        "figure2_complete_passes": 0,
        "figure3_strict_LiAsF6_rows": len(external_primary),
        "figure3_strict_LiAsF6_formulations": int(external_primary["formula_group"].nunique()),
        "figure3_external_raw_r2": float(external.loc["all_source_salts", "raw_r2"]),
        "figure3_external_spearman": float(external.loc["all_source_salts", "spearman"]),
        "figure4_controlled_targets": 4,
        "figure5_five_anchor_source_spearman": source_rho,
        "figure5_five_anchor_recipient_spearman": recipient_rho,
        "figure5_five_anchor_source_precision": source_precision,
        "figure5_five_anchor_recipient_precision": recipient_precision,
        "figure5_frozen_decision": finales["decision"],
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
