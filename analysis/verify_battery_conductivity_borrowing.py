"""Independent semantic verifier for the formal battery borrowing results."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
DESIGN = HERE / "battery_conductivity_borrowing_design.json"
IMPLEMENTATION = HERE / "battery_conductivity_implementation.json"
CARDS = HERE / "results" / "battery_conductivity_source_cards.csv"
SOURCE_SUMMARY = (
    HERE / "results" / "battery_conductivity_source_summary.json"
)
METRICS = HERE / "results" / "battery_conductivity_metrics.csv"
PREDICTIONS = (
    HERE / "results" / "battery_conductivity_primary_predictions.csv.gz"
)
CONTRASTS = HERE / "results" / "battery_conductivity_contrasts.csv"
SUMMARY = HERE / "results" / "battery_conductivity_formal_summary.json"
COMPLETE = HERE / "results" / "battery_conductivity_complete.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    design = json.loads(DESIGN.read_text(encoding="utf-8"))
    implementation = json.loads(IMPLEMENTATION.read_text(encoding="utf-8"))
    source_summary = json.loads(SOURCE_SUMMARY.read_text(encoding="utf-8"))
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    complete = json.loads(COMPLETE.read_text(encoding="utf-8"))
    metrics = pd.read_csv(METRICS)
    predictions = pd.read_csv(PREDICTIONS, low_memory=False)
    contrasts = pd.read_csv(CONTRASTS)

    expected_hashes = {
        "design_sha256": sha256(DESIGN),
        "implementation_sha256": sha256(IMPLEMENTATION),
        "cards_sha256": sha256(CARDS),
        "source_summary_sha256": sha256(SOURCE_SUMMARY),
        "metrics_sha256": sha256(METRICS),
        "predictions_sha256": sha256(PREDICTIONS),
        "contrasts_sha256": sha256(CONTRASTS),
        "summary_sha256": sha256(SUMMARY),
    }
    for key, expected in expected_hashes.items():
        observed = complete.get(key, summary.get(key))
        if observed != expected:
            raise AssertionError(f"Hash mismatch: {key}")
    if source_summary["status"] != "source-card-gate-passed":
        raise AssertionError("Formal benchmark ran without source skill")
    if len(metrics) != complete["metric_rows"]:
        raise AssertionError("Metric row count mismatch")
    if len(predictions) != complete["prediction_rows"]:
        raise AssertionError("Prediction row count mismatch")
    if len(contrasts) != complete["contrasts"]:
        raise AssertionError("Contrast row count mismatch")
    if not np.isfinite(
        metrics[["rmse", "mae", "r2"]].to_numpy(float)
    ).all():
        raise AssertionError("Nonfinite primary metrics")

    benchmark = implementation["recipient_benchmark"]
    expected_metric_rows = (
        complete["repeats"]
        * len(complete["budgets"])
        * len(complete["learners"])
        * len(benchmark["methods"])
        * len(benchmark["scopes"])
    )
    if len(metrics) != expected_metric_rows:
        raise AssertionError("Formal metric grid is incomplete")
    if set(metrics["method"]) != set(benchmark["methods"]):
        raise AssertionError("Formal method set changed")
    if set(metrics["scope"]) != set(benchmark["scopes"]):
        raise AssertionError("Formal scope set changed")
    if predictions["budget"].nunique() != 1:
        raise AssertionError("Prediction release is not primary-budget only")
    if predictions["budget"].iloc[0] != benchmark["primary_label_budget"]:
        raise AssertionError("Prediction release uses wrong label budget")
    if predictions.duplicated(
        ["repeat", "learner", "method", "target_id"]
    ).any():
        raise AssertionError("Duplicate formal predictions")

    gate = complete["formal_success_gate"]
    if gate["passed"] != all(gate["checks"].values()):
        raise AssertionError("Formal success decision mismatch")
    if complete["claim_guard"] != implementation["claim_guard"]:
        raise AssertionError("Claim guard changed")
    if design["inference"]["success_gate"][
        "minimum_mean_relative_rmse_gain"
    ] != 0.05:
        raise AssertionError("Frozen practical threshold changed")

    output = {
        "status": "verified-complete",
        "design_sha256": complete["design_sha256"],
        "implementation_sha256": complete["implementation_sha256"],
        "metric_rows": len(metrics),
        "prediction_rows": len(predictions),
        "contrasts": len(contrasts),
        "formal_success_gate": gate,
        "claim_guard": complete["claim_guard"],
    }
    print(json.dumps(output, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()

