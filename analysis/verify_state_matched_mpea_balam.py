"""Portable integrity and completeness verifier for the Balam robustness run."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
DESIGN = HERE / "state_matched_mpea_balam_design.json"
METRICS = RESULTS / "state_matched_mpea_balam_screen.csv"
PREDICTIONS = RESULTS / "state_matched_mpea_balam_predictions.csv"
SUMMARY = RESULTS / "state_matched_mpea_balam_summary.json"
BOOTSTRAP = RESULTS / "state_matched_mpea_balam_bootstrap.csv.gz"
BOOTSTRAP_SUMMARY = RESULTS / "state_matched_mpea_balam_bootstrap_summary.json"
VERIFIED = RESULTS / "state_matched_mpea_balam_VERIFIED.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--design-path", type=Path, default=DESIGN)
    parser.add_argument("--input-prefix", default="state_matched_mpea_balam")
    parser.add_argument("--output-prefix", default="state_matched_mpea_balam")
    return parser.parse_args()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    args = parse_args()
    design_path = args.design_path.resolve()
    metrics_path = RESULTS / f"{args.input_prefix}_screen.csv"
    predictions_path = RESULTS / f"{args.input_prefix}_predictions.csv"
    summary_path = RESULTS / f"{args.input_prefix}_summary.json"
    bootstrap_path = RESULTS / f"{args.input_prefix}_bootstrap.csv.gz"
    bootstrap_summary_path = RESULTS / f"{args.input_prefix}_bootstrap_summary.json"
    verified_path = RESULTS / f"{args.output_prefix}_VERIFIED.json"
    design = json.loads(design_path.read_text(encoding="utf-8"))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    bootstrap_summary = json.loads(bootstrap_summary_path.read_text(encoding="utf-8"))
    metrics = pd.read_csv(metrics_path)
    predictions = pd.read_csv(predictions_path)

    expected_hash = sha256(design_path)
    if summary["design_sha256"] != expected_hash:
        raise AssertionError("Design hash mismatch")
    if bootstrap_summary["design_sha256"] != expected_hash:
        raise AssertionError("Bootstrap design hash mismatch")
    screen = design["screen"]
    expected_runs = (
        int(screen["repeats"])
        * len(screen["learners"])
        * len(screen["target_label_budgets"])
        * len(design["deployment_contracts"])
    )
    primary = metrics[
        (metrics["contract"] == screen["primary_contract"])
        & (metrics["budget"] == screen["primary_budget"])
        & (metrics["method"] == screen["primary_method"])
    ]
    for scope in ("all", "q1", "q2", "q3", "q4"):
        found = len(primary[primary["scope"] == scope])
        if found != expected_runs:
            raise AssertionError(f"Primary {scope} has {found} rows; expected {expected_runs}")
    if set(primary["learner"]) != set(screen["learners"]):
        raise AssertionError("Learner set changed")
    if primary[["relative_rmse_gain", "base_r2", "aug_r2"]].isna().any().any():
        raise AssertionError("Primary metrics contain missing values")

    expected_prediction_rows = (
        int(screen["repeats"])
        * len(screen["learners"])
        * int(summary["data"]["evaluation_rows"])
    )
    if len(predictions) != expected_prediction_rows:
        raise AssertionError(
            f"Prediction rows {len(predictions)} != {expected_prediction_rows}"
        )
    required_prediction_columns = {
        "group",
        "scope",
        "observed_log10_ys",
        "state_only",
        "state_plus_predicted_uts",
        "shuffled_uts_residual_anchor",
        "predicted_log10_uts",
    }
    if (
        design["screen"].get("shuffled_control_method")
        == "state_plus_crossfitted_shuffled_uts"
    ):
        required_prediction_columns.add("state_plus_shuffled_uts")
    missing = required_prediction_columns - set(predictions)
    if missing:
        raise AssertionError(f"Missing prediction columns: {sorted(missing)}")
    if predictions[list(required_prediction_columns)].isna().any().any():
        raise AssertionError("Saved prediction evidence contains missing values")
    group_scopes = predictions.groupby(
        ["contract", "budget", "repeat", "learner", "group"]
    )["scope"].nunique()
    if int(group_scopes.max()) != 1:
        raise AssertionError("An elemental system crosses an OOD quartile")

    payload = {
        "status": "verified-complete",
        "verified_utc": datetime.now(timezone.utc).isoformat(),
        "design_sha256": expected_hash,
        "metrics_sha256": sha256(metrics_path),
        "predictions_sha256": sha256(predictions_path),
        "summary_sha256": sha256(summary_path),
        "bootstrap_sha256": sha256(bootstrap_path),
        "bootstrap_summary_sha256": sha256(bootstrap_summary_path),
        "primary_runs_per_scope": expected_runs,
        "prediction_rows": int(len(predictions)),
        "evaluation_groups": int(summary["data"]["evaluation_groups"]),
        "descriptive_gate": summary["balam_escalation_gate"],
        "primary_bootstrap_gate": bootstrap_summary["gate"],
        "claim_guard": design["claim_guard"],
    }
    verified_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
