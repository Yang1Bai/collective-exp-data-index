"""Verify the recipient-only baseline stress-test summary and alignment."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from common import RESULTS
from electrolyte_programme_interaction_common import sha256


HERE = Path(__file__).resolve().parent
DESIGN = HERE / "bamboomixer_cross_database_interaction_design.json"
METRICS = (
    RESULTS
    / "bamboomixer_recipient_baseline_stress_test_metrics.csv"
)
SUMMARY = (
    RESULTS
    / "bamboomixer_recipient_baseline_stress_test_summary.json"
)
FORMAL_ANCHORS = (
    RESULTS
    / "bamboomixer_cross_database_interaction_solventseg_anchor_metrics.csv"
)
OUTPUT = (
    RESULTS
    / "bamboomixer_recipient_baseline_stress_test_verification.json"
)


def close(observed: float, expected: float, label: str) -> None:
    if not np.isclose(observed, expected, rtol=1e-10, atol=1e-12):
        raise AssertionError(f"{label}: {observed} != {expected}")


def quantiles(values: pd.Series) -> list[float]:
    return [
        float(values.quantile(0.025)),
        float(values.quantile(0.975)),
    ]


def main() -> None:
    metrics = pd.read_csv(METRICS)
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    if len(metrics) != 4200:
        raise AssertionError("Stress-test metric table is incomplete")
    if set(metrics["anchor_budget"]) != {3, 5, 10}:
        raise AssertionError("Anchor budgets changed")
    counts = metrics.groupby(["anchor_budget", "draw"]).size()
    if len(counts) != 300 or not (counts == 14).all():
        raise AssertionError("Model family is incomplete")
    source = metrics[
        metrics["model"].eq("programme_balanced_source_portfolio")
    ].sort_values(["anchor_budget", "draw"])
    formal = pd.read_csv(FORMAL_ANCHORS)
    formal = formal[
        formal["model"].eq("programme_balanced_portfolio_frozen")
    ].sort_values(["anchor_budget", "draw"])
    for metric in (
        "spearman",
        "top_quartile_precision",
        "normalized_regret",
    ):
        if not np.allclose(
            source[metric],
            formal[metric],
            rtol=1e-10,
            atol=1e-12,
        ):
            raise AssertionError(f"Formal anchor alignment changed: {metric}")
    primary = metrics[metrics["anchor_budget"].eq(5)]
    source = primary[
        primary["model"].eq("programme_balanced_source_portfolio")
    ].set_index("draw")
    recipient = primary[
        ~primary["model"].eq("programme_balanced_source_portfolio")
    ]
    macro = (
        recipient.groupby("model")[
            ["spearman", "top_quartile_precision", "normalized_regret"]
        ]
        .mean()
        .sort_values("spearman", ascending=False)
    )
    strongest = str(macro.index[0])
    if strongest != summary["five_anchor"][
        "strongest_average_recipient_model"
    ]:
        raise AssertionError("Strongest recipient model changed")
    strongest_draw = recipient[
        recipient["model"].eq(strongest)
    ].set_index("draw")
    difference = source["spearman"] - strongest_draw["spearman"]
    oracle = recipient.groupby("draw")["spearman"].max()
    oracle_difference = source["spearman"] - oracle
    stored = summary["five_anchor"]
    close(
        float(difference.mean()),
        stored["source_minus_strongest_spearman"]["mean"],
        "Strongest-recipient mean contrast",
    )
    close(
        float(oracle_difference.mean()),
        stored["source_minus_oracle_spearman"]["mean"],
        "Oracle mean contrast",
    )
    if not np.allclose(
        quantiles(difference),
        stored["source_minus_strongest_spearman"]["ci95"],
        rtol=1e-10,
        atol=1e-12,
    ):
        raise AssertionError("Strongest-recipient interval changed")
    if not np.allclose(
        quantiles(oracle_difference),
        stored["source_minus_oracle_spearman"]["ci95"],
        rtol=1e-10,
        atol=1e-12,
    ):
        raise AssertionError("Oracle interval changed")
    if not stored["passes_adversarial_spearman_gate"]:
        raise AssertionError("Stored gate is not positive")
    verification = {
        "status": "verified-complete",
        "verification_mode": "summary-recalculation-and-formal-anchor-alignment",
        "design_sha256": sha256(DESIGN),
        "metrics_sha256": sha256(METRICS),
        "summary_sha256": sha256(SUMMARY),
        "rows": len(metrics),
        "formal_anchor_rows_aligned": len(source) * 3,
        "strongest_average_recipient_model": strongest,
        "source_minus_strongest_spearman_mean": float(difference.mean()),
        "source_minus_oracle_spearman_mean": float(oracle_difference.mean()),
    }
    OUTPUT.write_text(
        json.dumps(verification, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(json.dumps(verification, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
