"""Independent structural and numerical verification of MPEA strengthening outputs."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, r2_score

from common import RESULTS


HERE = Path(__file__).resolve().parent
DESIGN_PATH = HERE / "mpea_provenance_specificity_design.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--design-path", type=Path, default=DESIGN_PATH)
    parser.add_argument("--output-prefix", default="mpea_provenance_specificity")
    parser.add_argument("--require-inference", action="store_true")
    return parser.parse_args()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def metric_values(frame: pd.DataFrame) -> dict[str, float | int]:
    y = frame["observed"].to_numpy(float)
    baseline = frame["baseline"].to_numpy(float)
    augmented = frame["real_augmented"].to_numpy(float)
    base_rmse = math.sqrt(mean_squared_error(y, baseline))
    aug_rmse = math.sqrt(mean_squared_error(y, augmented))
    return {
        "n": int(len(frame)),
        "base_rmse": base_rmse,
        "aug_rmse": aug_rmse,
        "relative_rmse_gain": (base_rmse - aug_rmse) / base_rmse,
        "base_r2": r2_score(y, baseline),
        "aug_r2": r2_score(y, augmented),
        "delta_r2": r2_score(y, augmented) - r2_score(y, baseline),
    }


def main() -> None:
    args = parse_args()
    design_text = args.design_path.resolve().read_text(encoding="utf-8")
    design = json.loads(design_text)
    design_hash = hashlib.sha256(design_text.encode("utf-8")).hexdigest()
    prefix = args.output_prefix
    metrics_path = RESULTS / f"{prefix}_metrics.csv"
    predictions_path = RESULTS / f"{prefix}_predictions.csv.gz"
    audit_path = RESULTS / f"{prefix}_audit.json"
    complete_path = RESULTS / f"{prefix}_complete.json"
    inference_path = RESULTS / f"{prefix}_inference_summary.json"
    metrics = pd.read_csv(metrics_path)
    predictions = pd.read_csv(predictions_path)
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    complete = json.loads(complete_path.read_text(encoding="utf-8"))
    if audit["design_sha256"] != design_hash or complete["design_sha256"] != design_hash:
        raise AssertionError("Design hash mismatch")
    for path in (metrics_path, predictions_path, audit_path):
        if complete["outputs"][path.name] != sha256(path):
            raise AssertionError(f"Checksum mismatch: {path.name}")

    repeats = int(audit["parameters"]["repeats"])
    learners = len(design["model"]["target_learners"])
    evaluation_rows = int(audit["target"]["evaluation_rows"])
    transfer_conditions = int(complete["transfer_conditions"])
    target_budgets = int(complete["target_only_budgets"])
    expected_predictions = (
        (transfer_conditions + target_budgets)
        * repeats
        * learners
        * evaluation_rows
    )
    expected_metrics = (
        (transfer_conditions + target_budgets) * repeats * learners * 5
    )
    if len(predictions) != expected_predictions:
        raise AssertionError(
            f"Prediction rows {len(predictions)} != {expected_predictions}"
        )
    if len(metrics) != expected_metrics:
        raise AssertionError(f"Metric rows {len(metrics)} != {expected_metrics}")
    if complete["prediction_rows"] != len(predictions):
        raise AssertionError("Complete prediction count mismatch")
    if complete["metrics_rows"] != len(metrics):
        raise AssertionError("Complete metric count mismatch")

    required_numeric = [
        "observed",
        "baseline",
        "real_augmented",
        "shuffled_augmented",
    ]
    if not np.isfinite(predictions[required_numeric].to_numpy(float)).all():
        raise AssertionError("Non-finite model prediction")
    transfer = predictions[~predictions["donor"].eq("none")]
    if not np.isfinite(
        transfer[["real_donor_feature", "shuffled_donor_feature"]].to_numpy(float)
    ).all():
        raise AssertionError("Non-finite donor feature")
    learning = predictions[predictions["donor"].eq("none")]
    if not learning[["real_donor_feature", "shuffled_donor_feature"]].isna().all().all():
        raise AssertionError("Target-only rows unexpectedly contain donor features")

    if predictions.groupby(
        ["condition", "repeat", "learner"]
    ).size().nunique() != 1:
        raise AssertionError("Model-draw prediction row counts differ")
    q4_counts = (
        predictions[predictions["scope"].eq("q4")]
        .groupby(["condition", "repeat", "learner"])["group"]
        .nunique()
    )
    if q4_counts.min() != 14 or q4_counts.max() != 14:
        raise AssertionError(f"Unexpected Q4 group counts: {q4_counts.describe()}")

    condition_audits = {row["condition"]: row for row in audit["conditions"]}
    strict_conditions = [
        name
        for name, row in condition_audits.items()
        if row["provenance_mode"] == "full_doi_disjoint"
    ]
    for name in strict_conditions:
        row = condition_audits[name]
        if row["target_eval_doi_overlap"] != 0:
            raise AssertionError(f"Strict target DOI overlap: {name}")
        if row["source_eval_group_overlap"] != 0:
            raise AssertionError(f"Strict source system overlap: {name}")
        if row["source_eval_doi_overlap"] != 0:
            raise AssertionError(f"Strict source DOI overlap: {name}")
    if condition_audits["provenance__system_disjoint"][
        "source_eval_doi_overlap"
    ] <= 0:
        raise AssertionError(
            "System-only provenance level does not retain the shared-DOI exposure"
        )
    if condition_audits["provenance__donor_doi_disjoint"][
        "source_eval_doi_overlap"
    ] != 0:
        raise AssertionError("Donor DOI-disjoint level retains an evaluation DOI")
    for row in audit["donor_fit_audits"]:
        if row["provenance_mode"] != "system_disjoint":
            if row["real"]["max_forbidden_doi_overlap"] != 0:
                raise AssertionError("Real fold DOI leakage")
            if row["shuffled"]["max_forbidden_doi_overlap"] != 0:
                raise AssertionError("Shuffled fold DOI leakage")
            if row["real"]["source_final_evaluation_doi_overlap"] != 0:
                raise AssertionError("Real final donor DOI leakage")
            if row["shuffled"]["source_final_evaluation_doi_overlap"] != 0:
                raise AssertionError("Shuffled final donor DOI leakage")
        elif row["real"]["source_final_evaluation_doi_overlap"] <= 0:
            raise AssertionError(
                "System-only final donor unexpectedly lost all shared-DOI exposure"
            )

    size_match_n = int(audit["strict_source_size_match_n"])
    for name in (
        "provenance__full_doi_disjoint",
        "specificity__hardness",
        "specificity__elongation",
    ):
        if int(condition_audits[name]["source_rows"]) != size_match_n:
            raise AssertionError(f"Source size mismatch: {name}")

    keys = ["repeat", "learner", "raw_row_id"]
    reference = predictions[
        predictions["condition"].eq("provenance__full_doi_disjoint")
    ][[*keys, "baseline", "scope"]]
    for condition in ("specificity__hardness", "specificity__elongation"):
        candidate = predictions[predictions["condition"].eq(condition)][
            [*keys, "baseline", "scope"]
        ]
        merged = reference.merge(
            candidate,
            on=keys,
            suffixes=("_reference", "_candidate"),
            validate="one_to_one",
        )
        if not np.allclose(
            merged["baseline_reference"], merged["baseline_candidate"], atol=1e-12
        ):
            raise AssertionError(f"Specificity baselines differ: {condition}")
        if not merged["scope_reference"].equals(merged["scope_candidate"]):
            raise AssertionError(f"Specificity OOD scopes differ: {condition}")

    standard = predictions[
        predictions["condition"].eq("provenance__system_disjoint")
    ][[*keys, "baseline", "scope"]]
    donor_doi = predictions[
        predictions["condition"].eq("provenance__donor_doi_disjoint")
    ][[*keys, "baseline", "scope"]]
    merged = standard.merge(
        donor_doi,
        on=keys,
        suffixes=("_standard", "_donor_doi"),
        validate="one_to_one",
    )
    if not np.allclose(
        merged["baseline_standard"], merged["baseline_donor_doi"], atol=1e-12
    ):
        raise AssertionError("Nested provenance target baselines differ unexpectedly")

    # Recompute every saved real metric from row-level predictions.
    metric_index = metrics.set_index(
        ["condition", "repeat", "learner", "scope"]
    )
    for values, local in predictions.groupby(
        ["condition", "repeat", "learner", "scope"], sort=False
    ):
        saved = metric_index.loc[values]
        computed = metric_values(local)
        for key, value in computed.items():
            saved_value = float(saved[f"real_{key}"])
            if not np.isclose(saved_value, value, rtol=1e-10, atol=1e-12):
                raise AssertionError(f"Metric mismatch {values}|{key}")

    inference_status = "not-requested"
    if args.require_inference:
        if not inference_path.exists():
            raise FileNotFoundError(inference_path)
        inference = json.loads(inference_path.read_text(encoding="utf-8"))
        if inference["design_sha256"] != design_hash:
            raise AssertionError("Inference design hash mismatch")
        declared = [row["contrast"] for row in inference["primary_contrasts"]]
        if declared != design["inference"]["primary_contrasts"]:
            raise AssertionError("Primary contrast family changed")
        for row in inference["primary_contrasts"]:
            if not 0 < float(row["one_sided_signflip_p"]) <= 1:
                raise AssertionError("Invalid primary p value")
            if not 0 < float(row["holm_adjusted_p"]) <= 1:
                raise AssertionError("Invalid Holm p value")
        survivors = [
            row["contrast"]
            for row in inference["primary_contrasts"]
            if float(row["holm_adjusted_p"]) < 0.05
        ]
        if survivors != inference["primary_family_holm_survivors"]:
            raise AssertionError("Holm survivor list mismatch")
        inference_status = "verified"

    print(
        json.dumps(
            {
                "status": "verified-complete",
                "design_sha256": design_hash,
                "metrics_rows": len(metrics),
                "prediction_rows": len(predictions),
                "q4_systems_per_model_draw": 14,
                "strict_source_size_match_n": size_match_n,
                "inference": inference_status,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
