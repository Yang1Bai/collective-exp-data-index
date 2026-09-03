"""Independent semantic verifier for the optical-to-OPV benchmark."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error


HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
DESIGN_PATH = HERE / "opv_optical_external_borrowing_design.json"
FREEZE_PATH = HERE / "opv_optical_implementation_freeze.json"
METADATA_PATH = (
    HERE / "results" / "opv_optical_target_metadata_no_outcomes.csv"
)
DRAW_PATH = HERE / "results" / "opv_optical_label_draws.csv"
SOURCE_FEATURE_PATH = HERE / "results" / "opv_optical_source_features.csv"
SOURCE_SUMMARY_PATH = HERE / "results" / "opv_optical_source_summary.json"
METHODS = {
    "structure_only",
    "state_aware_target_only",
    "state_aware_plus_real_solid_optical_card",
    "state_aware_plus_shuffled_source_card",
    "state_aware_plus_state_blind_optical_card",
    "state_aware_plus_permuted_real_card",
    "state_aware_plus_gaussian_card",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode", choices=["formal", "synthetic_smoke"], required=True
    )
    arguments = parser.parse_args()
    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    source_summary = json.loads(
        SOURCE_SUMMARY_PATH.read_text(encoding="utf-8")
    )
    run_path = RESULTS / f"opv_optical_external_{arguments.mode}_run.json"
    metrics_path = (
        RESULTS / f"opv_optical_external_{arguments.mode}_metrics.csv"
    )
    predictions_path = (
        RESULTS
        / f"opv_optical_external_{arguments.mode}_primary_predictions.csv"
    )
    summary_path = (
        RESULTS / f"opv_optical_external_{arguments.mode}_summary.json"
    )
    run = json.loads(run_path.read_text(encoding="utf-8"))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    metrics = pd.read_csv(metrics_path)
    predictions = pd.read_csv(predictions_path)
    metadata = pd.read_csv(METADATA_PATH, low_memory=False)
    draws = pd.read_csv(DRAW_PATH, dtype={"id": "string"})
    source = pd.read_csv(SOURCE_FEATURE_PATH)

    if run["design_sha256"] != sha256(DESIGN_PATH):
        raise AssertionError("Run design hash mismatch")
    if run["metadata_sha256"] != sha256(METADATA_PATH):
        raise AssertionError("Run metadata hash mismatch")
    if run["draw_sha256"] != sha256(DRAW_PATH):
        raise AssertionError("Run draw hash mismatch")
    if run["source_feature_sha256"] != sha256(SOURCE_FEATURE_PATH):
        raise AssertionError("Run source feature hash mismatch")
    if run["metrics_sha256"] != sha256(metrics_path):
        raise AssertionError("Run metrics hash mismatch")
    if run["primary_predictions_sha256"] != sha256(predictions_path):
        raise AssertionError("Run prediction hash mismatch")
    if summary["run_sha256"] != sha256(run_path):
        raise AssertionError("Inference run hash mismatch")
    if summary["metrics_sha256"] != sha256(metrics_path):
        raise AssertionError("Inference metrics hash mismatch")
    if summary["predictions_sha256"] != sha256(predictions_path):
        raise AssertionError("Inference prediction hash mismatch")
    if source_summary["feature_sha256"] != sha256(SOURCE_FEATURE_PATH):
        raise AssertionError("Source feature summary mismatch")
    if arguments.mode == "formal":
        freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
        if freeze["design_sha256"] != sha256(DESIGN_PATH):
            raise AssertionError("Formal implementation design drift")
        if freeze["run_sha256"] != run["run_sha256"]:
            raise AssertionError("Formal run implementation drift")
        if freeze["summarizer_sha256"] != summary[
            "implementation_sha256"
        ]:
            raise AssertionError("Formal inference implementation drift")
        if freeze["verifier_sha256"] != sha256(Path(__file__)):
            raise AssertionError("Formal verifier implementation drift")
        if source_summary["status"] != "strict-source-features-ready":
            raise AssertionError("Formal source features are not strict")
    if len(metadata) != int(design["target"]["expected_rows"]):
        raise AssertionError("Target metadata row count drift")
    if source["canonical_smiles"].duplicated().any():
        raise AssertionError("Source feature molecule keys are not unique")
    if set(predictions["method"].astype(str)) != METHODS:
        raise AssertionError("Primary method set drift")
    prediction_columns = [
        "truth_pce",
        "predicted_pce",
        "truth_voc",
        "truth_jsc",
        "truth_ff",
        "predicted_voc",
        "predicted_jsc",
        "predicted_ff",
        "predicted_pce_physics_recombined",
    ]
    if not np.isfinite(predictions[prediction_columns].to_numpy(float)).all():
        raise AssertionError("Nonfinite primary prediction")
    recombined = (
        predictions["predicted_voc"].to_numpy(float)
        * predictions["predicted_jsc"].to_numpy(float)
        * predictions["predicted_ff"].to_numpy(float)
        / 100.0
    )
    if not np.allclose(
        recombined,
        predictions["predicted_pce_physics_recombined"].to_numpy(float),
        rtol=1e-10,
        atol=1e-10,
    ):
        raise AssertionError("Physics-recombined PCE identity mismatch")

    group = predictions.groupby(["repeat", "id"], sort=False)
    method_counts = group["method"].nunique()
    if not (method_counts == len(METHODS)).all():
        raise AssertionError("Primary predictions are not method-paired")
    for column in ["truth_pce", "truth_voc", "truth_jsc", "truth_ff"]:
        truth_counts = group[column].nunique()
        if not (truth_counts == 1).all():
            raise AssertionError(f"Paired target truths differ: {column}")
    doi_counts = group["doi_normalized_audit"].nunique()
    if not (doi_counts == 1).all():
        raise AssertionError("Paired DOI labels differ")

    selected_metrics = metrics[
        (metrics["budget"] == 120)
        & (metrics["learner"] == "extra_trees")
        & (metrics["scope"] == "qualified_hard_ood_40pct")
        & (metrics["outcome"] == "pce")
    ]
    reconstructed = (
        predictions.groupby(["repeat", "method"], as_index=False)
        .apply(
            lambda frame: pd.Series(
                {
                    "rmse_check": float(
                        mean_squared_error(
                            frame["truth_pce"],
                            frame["predicted_pce"],
                        )
                        ** 0.5
                    ),
                    "physics_rmse_check": float(
                        mean_squared_error(
                            frame["truth_pce"],
                            frame["predicted_pce_physics_recombined"],
                        )
                        ** 0.5
                    ),
                    "rows_check": int(len(frame)),
                }
            ),
            include_groups=False,
        )
        .reset_index(drop=True)
    )
    merged = selected_metrics.merge(
        reconstructed, on=["repeat", "method"], validate="one_to_one"
    )
    if not np.allclose(
        merged["rmse"], merged["rmse_check"], rtol=1e-8, atol=1e-8
    ):
        raise AssertionError("Primary RMSE reconstruction mismatch")
    if not (merged["rows"] == merged["rows_check"]).all():
        raise AssertionError("Primary scope row count mismatch")
    physics_metrics = metrics[
        (metrics["budget"] == 120)
        & (metrics["learner"] == "extra_trees")
        & (metrics["scope"] == "qualified_hard_ood_40pct")
        & (metrics["outcome"] == "pce_physics_recombined")
    ]
    physics_merged = physics_metrics.merge(
        reconstructed, on=["repeat", "method"], validate="one_to_one"
    )
    if not np.allclose(
        physics_merged["rmse"],
        physics_merged["physics_rmse_check"],
        rtol=1e-8,
        atol=1e-8,
    ):
        raise AssertionError("Physics-recombined PCE RMSE mismatch")

    external_ids = set(
        metadata.loc[
            metadata["external_doi_holdout"], "id"
        ].astype(str)
    )
    if not set(predictions["id"].astype(str)).issubset(external_ids):
        raise AssertionError("A non-external target entered primary evaluation")
    label_ids = set(
        draws.loc[draws["budget"] == 120, "id"].astype(str)
    )
    if set(predictions["id"].astype(str)).intersection(label_ids):
        raise AssertionError("A labelled target entered external evaluation")

    verification = {
        "status": "verified-complete",
        "mode": arguments.mode,
        "verified_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "design_sha256": sha256(DESIGN_PATH),
        "run_sha256": sha256(run_path),
        "summary_sha256": sha256(summary_path),
        "metrics_sha256": sha256(metrics_path),
        "predictions_sha256": sha256(predictions_path),
        "implementation_sha256": sha256(Path(__file__)),
        "metric_rows": int(len(metrics)),
        "primary_prediction_rows": int(len(predictions)),
        "reconstructed_primary_cells": int(len(merged)),
        "passes_complete_gate": bool(summary["passes_complete_gate"]),
        "decision": summary["decision"],
        "claim_guard": design["claim_guard"],
    }
    verification_path = (
        RESULTS / f"opv_optical_external_{arguments.mode}_VERIFIED.json"
    )
    verification_path.write_text(
        json.dumps(verification, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(json.dumps(verification, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
