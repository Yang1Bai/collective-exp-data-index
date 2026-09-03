"""Independently reconstruct the released 22-group sensitivity statistics."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "analysis" / "results" / "multistage_battery_stage2_coverage_sensitivity"
ANALYSIS = DIR / "analysis"
SUMMARY = ANALYSIS / "POSTRELEASE_SENSITIVITY_SUMMARY.json"
PREDICTIONS = ANALYSIS / "stage2_outer_predictions.csv"
GATES = ANALYSIS / "training_only_gate.csv"
GROUP_ERRORS = ANALYSIS / "condition_group_errors.csv"
BOOTSTRAPS = ANALYSIS / "condition_cluster_bootstrap.csv"
SPECIFICATION = DIR / "POSTRELEASE_SENSITIVITY_SPECIFICATION.json"
OUTPUT = DIR / "INDEPENDENT_VERIFICATION.json"
SEED = 20260720
N_BOOTSTRAPS = 10_000
N_SIGN_FLIPS = 9_999


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def assert_close(left: float, right: float, label: str, tolerance: float = 1e-12) -> None:
    if not np.isclose(left, right, rtol=tolerance, atol=tolerance):
        raise AssertionError(f"{label}: {left} != {right}")


def holm(values: dict[str, float]) -> dict[str, float]:
    ordered = sorted(values, key=values.get)
    return {
        ordered[0]: min(1.0, 2.0 * values[ordered[0]]),
        ordered[1]: min(1.0, max(2.0 * values[ordered[0]], values[ordered[1]])),
    }


def main() -> None:
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    specification = json.loads(SPECIFICATION.read_text(encoding="utf-8"))
    if summary["status"] != "verified-complete-postrelease-coverage-sensitivity":
        raise AssertionError("Sensitivity summary is incomplete")
    if summary["confirmatory_success"] or summary["frozen_primary_status"] != "non-evaluable-stage2-release":
        raise AssertionError("The non-evaluable frozen primary was overwritten")
    hash_map = {
        "prediction_table_sha256": PREDICTIONS,
        "gate_table_sha256": GATES,
        "group_error_table_sha256": GROUP_ERRORS,
        "bootstrap_table_sha256": BOOTSTRAPS,
    }
    for key, path in hash_map.items():
        if summary[key] != sha256(path):
            raise AssertionError(f"Hash mismatch for {path.name}")

    predictions = pd.read_csv(PREDICTIONS, dtype={"file_id": str})
    gates = pd.read_csv(GATES)
    observed_policies = sorted(predictions["policy"].unique())
    if len(predictions) != 945 or len(observed_policies) != 7:
        raise AssertionError("Expected 135 cells under each of seven policies")
    if not (predictions.groupby("policy")["file_id"].nunique() == 135).all():
        raise AssertionError("A policy does not cover every retained cell")
    if predictions["condition_group"].nunique() != 22 or len(gates) != 22:
        raise AssertionError("Expected exactly 22 independent condition groups")
    if not np.allclose(
        predictions["residual"].to_numpy(),
        predictions["observed"].to_numpy() - predictions["prediction"].to_numpy(),
        rtol=0,
        atol=1e-12,
    ):
        raise AssertionError("Residuals do not equal observed minus predicted")

    reconstructed = predictions.groupby(["type", "condition_group", "policy"], as_index=False).agg(
        condition_rmse=("residual", lambda values: float(np.sqrt(np.mean(np.square(values))))),
        n_cells=("residual", "size"),
        source_distance=("source_distance", "mean"),
    )
    stored = pd.read_csv(GROUP_ERRORS).sort_values(["type", "condition_group", "policy"]).reset_index(drop=True)
    reconstructed = reconstructed.sort_values(["type", "condition_group", "policy"]).reset_index(drop=True)
    if list(stored[["type", "condition_group", "policy"]].itertuples(index=False, name=None)) != list(
        reconstructed[["type", "condition_group", "policy"]].itertuples(index=False, name=None)
    ):
        raise AssertionError("Condition-error keys differ")
    for column in ("condition_rmse", "source_distance"):
        if not np.allclose(stored[column], reconstructed[column], rtol=1e-12, atol=1e-12):
            raise AssertionError(f"Condition-error reconstruction failed for {column}")

    wide = reconstructed.pivot(index=["type", "condition_group"], columns="policy", values="condition_rmse").reset_index()
    comparison_order = [
        ("adjacency_only", "CCA-v2 minus adjacency-only"),
        ("target_only", "CCA-v2 minus endpoint-matched target-only"),
    ]
    rng = np.random.default_rng(SEED)
    reconstructed_inference: dict[str, dict] = {}
    p_values: dict[str, float] = {}
    stored_bootstraps = pd.read_csv(BOOTSTRAPS)
    if len(stored_bootstraps) != 20_000:
        raise AssertionError("Expected exactly 20,000 cluster-bootstrap records")
    for comparator, label in comparison_order:
        parts = {aging_type: wide.loc[wide["type"].eq(aging_type)].reset_index(drop=True) for aging_type in ("k", "z")}
        effects = {
            aging_type: 1.0 - part["cca_v2"].mean() / part[comparator].mean()
            for aging_type, part in parts.items()
        }
        observed = 0.5 * (effects["k"] + effects["z"])
        boot = np.empty(N_BOOTSTRAPS)
        boot_k = np.empty(N_BOOTSTRAPS)
        boot_z = np.empty(N_BOOTSTRAPS)
        for index in range(N_BOOTSTRAPS):
            sampled_effects = {}
            for aging_type, part in parts.items():
                sampled = part.iloc[rng.integers(0, len(part), len(part))]
                sampled_effects[aging_type] = 1.0 - sampled["cca_v2"].mean() / sampled[comparator].mean()
            boot_k[index], boot_z[index] = sampled_effects["k"], sampled_effects["z"]
            boot[index] = 0.5 * (sampled_effects["k"] + sampled_effects["z"])
        stored_part = stored_bootstraps.loc[stored_bootstraps["comparison"].eq(label)].sort_values("bootstrap")
        for column, values in (("effect", boot), ("calendar_effect", boot_k), ("cycle_effect", boot_z)):
            if not np.allclose(stored_part[column], values, rtol=1e-12, atol=1e-12):
                raise AssertionError(f"Bootstrap reconstruction failed for {label}: {column}")

        null = np.empty(N_SIGN_FLIPS)
        for index in range(N_SIGN_FLIPS):
            permuted = {}
            for aging_type, part in parts.items():
                midpoint = 0.5 * (part["cca_v2"].to_numpy() + part[comparator].to_numpy())
                half_difference = 0.5 * (part["cca_v2"].to_numpy() - part[comparator].to_numpy())
                signs = rng.choice(np.array([-1.0, 1.0]), size=len(part))
                permuted[aging_type] = 1.0 - (midpoint + signs * half_difference).mean() / (
                    midpoint - signs * half_difference
                ).mean()
            null[index] = 0.5 * (permuted["k"] + permuted["z"])
        p_value = float((1 + np.sum(null >= observed)) / (N_SIGN_FLIPS + 1))
        p_values[label] = p_value
        reconstructed_inference[label] = {
            "effect": observed,
            "calendar_effect": effects["k"],
            "cycle_effect": effects["z"],
            "ci95": [float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))],
            "calendar_ci95": [float(np.quantile(boot_k, 0.025)), float(np.quantile(boot_k, 0.975))],
            "cycle_ci95": [float(np.quantile(boot_z, 0.025)), float(np.quantile(boot_z, 0.975))],
            "one_sided_sign_flip_p": p_value,
        }
    adjusted = holm(p_values)
    for label, values in reconstructed_inference.items():
        values["holm_adjusted_p"] = adjusted[label]
        reported = summary["primary_named_comparisons_reported_as_exploratory"][label]
        for key in ("effect", "calendar_effect", "cycle_effect", "one_sided_sign_flip_p", "holm_adjusted_p"):
            assert_close(float(values[key]), float(reported[key]), f"{label}: {key}")
        for key in ("ci95", "calendar_ci95", "cycle_ci95"):
            if not np.allclose(values[key], reported[key], rtol=1e-12, atol=1e-12):
                raise AssertionError(f"{label}: {key} differs")

    verification = {
        "status": "independently-verified-postrelease-coverage-sensitivity",
        "frozen_primary_status": "non-evaluable-stage2-release",
        "retained_cells": 135,
        "independent_condition_groups": 22,
        "policies": observed_policies,
        "prediction_rows": len(predictions),
        "bootstrap_rows": len(stored_bootstraps),
        "reconstructed_inference": reconstructed_inference,
        "summary_sha256": sha256(SUMMARY),
        "specification_sha256": sha256(SPECIFICATION),
        "claim_guard": "Verification establishes numerical reproducibility only; it does not upgrade this post-release sensitivity to confirmatory evidence.",
        "errors": [],
    }
    OUTPUT.write_text(json.dumps(verification, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(verification, indent=2))


if __name__ == "__main__":
    main()
