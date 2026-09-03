"""Independently verify the post hoc continuous-adjacency diagnostic."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "analysis" / "results" / "multistage_battery_stage2_coverage_sensitivity"
BASE = DIR / "analysis"
DIAGNOSTIC = DIR / "postrelease_adjacency_diagnostic"
SPECIFICATION = DIR / "POSTRELEASE_ADJACENCY_DIAGNOSTIC_SPECIFICATION.json"
SUMMARY = DIAGNOSTIC / "POSTRELEASE_ADJACENCY_DIAGNOSTIC_SUMMARY.json"
GROUP_ERRORS = BASE / "condition_group_errors.csv"
PREDICTIONS = BASE / "stage2_outer_predictions.csv"
APPLICABILITY = DIR / "postrelease_applicability_plan.csv"
GROUP_MAP = DIAGNOSTIC / "condition_borrowing_map.csv"
BOOTSTRAP_TABLE = DIAGNOSTIC / "adjacency_condition_cluster_bootstrap.csv"
OUTPUT = DIAGNOSTIC / "INDEPENDENT_VERIFICATION.json"
SEED = 20260721
BOOTSTRAPS = 10_000
SIGN_FLIPS = 9_999
COMPARATORS = ["target_only", "wrong_property", "shuffled_source", "random_features"]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def holm(values: dict[str, float]) -> dict[str, float]:
    ordered = sorted(values, key=values.get)
    result: dict[str, float] = {}
    running = 0.0
    for rank, label in enumerate(ordered):
        running = max(running, (len(ordered) - rank) * values[label])
        result[label] = min(1.0, running)
    return result


def main() -> None:
    specification = json.loads(SPECIFICATION.read_text(encoding="utf-8"))
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    if not summary["method_selection_was_outcome_guided"] or summary["confirmatory_success"]:
        raise AssertionError("Post hoc timing or confirmatory boundary was lost")
    if summary["condition_map_sha256"] != sha256(GROUP_MAP):
        raise AssertionError("Condition borrowing map hash mismatch")
    if summary["bootstrap_sha256"] != sha256(BOOTSTRAP_TABLE):
        raise AssertionError("Adjacency bootstrap hash mismatch")
    if summary["specification_sha256"] != sha256(SPECIFICATION):
        raise AssertionError("Adjacency specification hash mismatch")

    errors = pd.read_csv(GROUP_ERRORS)
    applicability = pd.read_csv(APPLICABILITY, dtype={"file_id": str, "borrow_allowed": bool})
    outer_app = applicability.loc[applicability["scope"].eq("outer_test")].groupby(
        ["type", "outer_heldout_group"], as_index=False
    ).agg(
        applicability=("applicability", "mean"),
        source_distance=("source_distance", "mean"),
        target_distance=("target_distance", "mean"),
        source_uncertainty_normalized=("source_uncertainty_normalized", "mean"),
        borrow_allowed=("borrow_allowed", "all"),
    ).rename(columns={"outer_heldout_group": "condition_group"})
    reconstructed = errors.pivot(
        index=["type", "condition_group"], columns="policy", values="condition_rmse"
    ).reset_index().merge(outer_app, on=["type", "condition_group"], validate="one_to_one")
    reconstructed["adjacency_relative_rmse_gain_vs_target_only"] = (
        1.0 - reconstructed["adjacency_only"] / reconstructed["target_only"]
    )
    reconstructed["adjacency_absolute_rmse_change_vs_target_only"] = (
        reconstructed["target_only"] - reconstructed["adjacency_only"]
    )
    reconstructed["adjacency_wins_target"] = reconstructed["adjacency_only"] < reconstructed["target_only"]
    stored_map = pd.read_csv(GROUP_MAP).sort_values(["type", "condition_group"]).reset_index(drop=True)
    reconstructed = reconstructed.sort_values(["type", "condition_group"]).reset_index(drop=True)
    for column in reconstructed.columns:
        if column in {"type", "condition_group"}:
            if not stored_map[column].equals(reconstructed[column]):
                raise AssertionError(f"Group map key mismatch: {column}")
        elif pd.api.types.is_bool_dtype(reconstructed[column]):
            if not stored_map[column].astype(bool).equals(reconstructed[column].astype(bool)):
                raise AssertionError(f"Group map boolean mismatch: {column}")
        elif not np.allclose(stored_map[column], reconstructed[column], rtol=1e-12, atol=1e-12):
            raise AssertionError(f"Group map numeric mismatch: {column}")

    stored_bootstrap = pd.read_csv(BOOTSTRAP_TABLE)
    if len(stored_bootstrap) != 40_000:
        raise AssertionError("Expected 40,000 diagnostic bootstrap rows")
    rng = np.random.default_rng(SEED)
    rebuilt: dict[str, dict] = {}
    raw_p: dict[str, float] = {}
    for comparator in COMPARATORS:
        label = f"adjacency_only minus {comparator}"
        parts = {aging_type: reconstructed.loc[reconstructed["type"].eq(aging_type)].reset_index(drop=True) for aging_type in ("k", "z")}
        stratum = {
            aging_type: 1.0 - part["adjacency_only"].mean() / part[comparator].mean()
            for aging_type, part in parts.items()
        }
        observed = 0.5 * (stratum["k"] + stratum["z"])
        boot = np.empty(BOOTSTRAPS)
        boot_k = np.empty(BOOTSTRAPS)
        boot_z = np.empty(BOOTSTRAPS)
        for index in range(BOOTSTRAPS):
            effects = {}
            for aging_type, part in parts.items():
                sampled = part.iloc[rng.integers(0, len(part), len(part))]
                effects[aging_type] = 1.0 - sampled["adjacency_only"].mean() / sampled[comparator].mean()
            boot_k[index], boot_z[index] = effects["k"], effects["z"]
            boot[index] = 0.5 * (effects["k"] + effects["z"])
        stored = stored_bootstrap.loc[stored_bootstrap["comparison"].eq(label)].sort_values("bootstrap")
        for column, values in (("effect", boot), ("calendar_effect", boot_k), ("cycle_effect", boot_z)):
            if not np.allclose(stored[column], values, rtol=1e-12, atol=1e-12):
                raise AssertionError(f"Diagnostic bootstrap mismatch: {label}, {column}")
        null = np.empty(SIGN_FLIPS)
        for index in range(SIGN_FLIPS):
            permuted = {}
            for aging_type, part in parts.items():
                midpoint = 0.5 * (part["adjacency_only"].to_numpy() + part[comparator].to_numpy())
                half_difference = 0.5 * (part["adjacency_only"].to_numpy() - part[comparator].to_numpy())
                signs = rng.choice(np.array([-1.0, 1.0]), size=len(part))
                permuted[aging_type] = 1.0 - (midpoint + signs * half_difference).mean() / (
                    midpoint - signs * half_difference
                ).mean()
            null[index] = 0.5 * (permuted["k"] + permuted["z"])
        p_value = float((1 + np.sum(null >= observed)) / (SIGN_FLIPS + 1))
        raw_p[label] = p_value
        rebuilt[label] = {
            "effect": float(observed),
            "calendar_effect": float(stratum["k"]),
            "cycle_effect": float(stratum["z"]),
            "ci95": [float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))],
            "calendar_ci95": [float(np.quantile(boot_k, 0.025)), float(np.quantile(boot_k, 0.975))],
            "cycle_ci95": [float(np.quantile(boot_z, 0.025)), float(np.quantile(boot_z, 0.975))],
            "one_sided_sign_flip_p": p_value,
        }
    adjusted = holm(raw_p)
    for label, values in rebuilt.items():
        values["holm_adjusted_p"] = adjusted[label]
        reported = summary["inference"][label]
        for key, value in values.items():
            if isinstance(value, list):
                if not np.allclose(value, reported[key], rtol=1e-12, atol=1e-12):
                    raise AssertionError(f"Diagnostic inference mismatch: {label}, {key}")
            elif not np.isclose(value, reported[key], rtol=1e-12, atol=1e-12):
                raise AssertionError(f"Diagnostic inference mismatch: {label}, {key}")

    predictions = pd.read_csv(PREDICTIONS, dtype={"file_id": str})
    adjacency = predictions.loc[predictions["policy"].eq("adjacency_only")].sort_values("file_id")
    global_source = predictions.loc[predictions["policy"].eq("global_credibility")].sort_values("file_id")
    maximum_difference = float(np.max(np.abs(adjacency["prediction"].to_numpy() - global_source["prediction"].to_numpy())))
    if maximum_difference > 1e-12:
        raise AssertionError("Global rescaling is not numerically equivalent to adjacency")

    verification = {
        "status": "independently-verified-postrelease-adjacency-diagnostic",
        "method_selection_was_outcome_guided": True,
        "frozen_primary_status": "non-evaluable-stage2-release",
        "condition_groups": len(reconstructed),
        "bootstrap_rows": len(stored_bootstrap),
        "reconstructed_inference": rebuilt,
        "maximum_adjacency_global_prediction_difference": maximum_difference,
        "summary_sha256": sha256(SUMMARY),
        "claim_guard": "The diagnostic is numerically reproducible but remains post hoc and cannot establish confirmation.",
        "errors": [],
    }
    OUTPUT.write_text(json.dumps(verification, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(verification, indent=2))


if __name__ == "__main__":
    main()
