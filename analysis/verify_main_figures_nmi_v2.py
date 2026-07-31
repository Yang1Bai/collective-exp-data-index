"""Semantic verification for the four canonical main figures."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "analysis" / "results"
FIGURES = ROOT / "analysis" / "figures"
SOURCE = FIGURES / "source_data"
REPORT = RESULTS / "main_figures_nmi_v2_verification.json"


def close(actual: float, expected: float, tolerance: float = 5e-6) -> None:
    if not np.isclose(actual, expected, atol=tolerance, rtol=0):
        raise AssertionError(f"numeric mismatch: {actual} != {expected}")


def main() -> None:
    expected_files = []
    for stem in [
        "knowledge_borrowing_overview_nmi_v2",
        "figure2_failure_benchmark_nmi_v2",
        "figure3_relation_transfer_nmi_v2",
        "figure4_ordinal_screening_nmi_v2",
    ]:
        for suffix in ["pdf", "svg", "png", "tiff"]:
            path = FIGURES / f"{stem}.{suffix}"
            if not path.exists() or path.stat().st_size == 0:
                raise AssertionError(f"missing or empty figure export: {path}")
            expected_files.append(str(path.relative_to(ROOT)))

    fig2 = pd.read_csv(SOURCE / "figure2_failure_benchmark_nmi_v2.csv")
    edges = pd.read_csv(RESULTS / "multi_target_ood_edge_summary.csv")
    if int((~edges["is_shuffled_control"].astype(bool)).sum()) != 40:
        raise AssertionError("Figure 2 benchmark must contain 40 real edges")
    close(float(fig2.loc[fig2["measure"].eq("source_internal_r2"), "estimate"].iloc[0]), 0.790, .001)
    close(float(fig2.loc[fig2["measure"].eq("transported_r2"), "estimate"].iloc[0]), -3.006, .001)

    catalyst = pd.read_csv(RESULTS / "specgen_derivative_oer_figure_source_data.csv")
    expected_catalyst = {"A": .0319129679, "B": .1634878300, "C": -.1037707991, "D": .2607354444}
    for target, expected in expected_catalyst.items():
        value = catalyst[(catalyst["target"].eq(target)) &
                         (catalyst["measure"].eq("relative_rmse_gain"))]["estimate"].iloc[0]
        close(float(value), expected)
    external = pd.read_csv(RESULTS / "bamboomixer_response_transfer_external_metrics.csv").set_index("scope")
    close(float(external.loc["all_source_salts", "raw_r2"]), .6294395422)
    close(float(external.loc["all_source_salts", "spearman"]), .8708256451)

    stress = pd.read_csv(RESULTS / "bamboomixer_recipient_baseline_stress_test_metrics.csv")
    five = stress[stress["anchor_budget"].eq(5)]
    source_mean = float(five.loc[five["model"].eq("programme_balanced_source_portfolio"), "spearman"].mean())
    recipient_means = (five.loc[~five["model"].eq("programme_balanced_source_portfolio")]
                       .groupby("model")["spearman"].mean())
    best_recipient = float(recipient_means.max())
    close(source_mean, .9102998261)
    close(best_recipient, .5366377618)
    close(source_mean - best_recipient, .3736620643)
    finales = json.loads((RESULTS / "finales_rank_replication_summary.json").read_text(encoding="utf-8"))
    close(float(finales["primary"]["donor_concordance"]), .6938775510)
    close(float(finales["primary"]["strongest_baseline_concordance"]), .7826086957)
    close(float(finales["primary"]["concordance_advantage"]), -.0887311446)

    report = {
        "status": "verified-complete",
        "canonical_exports": expected_files,
        "figure2_real_edges": 40,
        "figure2_complete_passes": 0,
        "figure3_external_raw_r2": float(external.loc["all_source_salts", "raw_r2"]),
        "figure3_external_spearman": float(external.loc["all_source_salts", "spearman"]),
        "figure4_five_anchor_source_spearman": source_mean,
        "figure4_best_fixed_recipient_spearman": best_recipient,
        "figure4_delta_spearman": source_mean - best_recipient,
        "figure4_frozen_decision": finales["decision"],
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
