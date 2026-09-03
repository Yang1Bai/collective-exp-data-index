"""Quantify the post hoc continuous-adjacency policy and matched controls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "analysis" / "results" / "multistage_battery_stage2_coverage_sensitivity"
ANALYSIS = DIR / "analysis"
SPECIFICATION = DIR / "POSTRELEASE_ADJACENCY_DIAGNOSTIC_SPECIFICATION.json"
PREDICTIONS = ANALYSIS / "stage2_outer_predictions.csv"
GROUP_ERRORS = ANALYSIS / "condition_group_errors.csv"
APPLICABILITY = DIR / "postrelease_applicability_plan.csv"
OUTPUT_DIR = DIR / "postrelease_adjacency_diagnostic"
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
    adjusted: dict[str, float] = {}
    running = 0.0
    total = len(ordered)
    for rank, label in enumerate(ordered):
        running = max(running, (total - rank) * values[label])
        adjusted[label] = min(1.0, running)
    return adjusted


def r2(observed: np.ndarray, predicted: np.ndarray) -> float:
    denominator = float(np.sum((observed - observed.mean()) ** 2))
    return 1.0 - float(np.sum((observed - predicted) ** 2)) / denominator


def main() -> None:
    specification = json.loads(SPECIFICATION.read_text(encoding="utf-8"))
    if specification["status"] != "specified-outcome-guided-postrelease-diagnostic":
        raise AssertionError("Adjacency diagnostic was not explicitly specified")
    if specification["method_selection_was_outcome_guided"] is not True:
        raise AssertionError("Outcome-guided timing must be disclosed")
    checks = {
        "predictions_sha256": PREDICTIONS,
        "group_errors_sha256": GROUP_ERRORS,
        "applicability_sha256": APPLICABILITY,
        "analysis_runner_sha256": Path(__file__).resolve(),
    }
    for key, path in checks.items():
        if specification[key] != sha256(path):
            raise AssertionError(f"Input changed after adjacency diagnostic specification: {path.name}")

    predictions = pd.read_csv(PREDICTIONS, dtype={"file_id": str})
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

    wide = errors.pivot(index=["type", "condition_group"], columns="policy", values="condition_rmse").reset_index()
    group_map = wide.merge(outer_app, on=["type", "condition_group"], validate="one_to_one")
    group_map["adjacency_relative_rmse_gain_vs_target_only"] = (
        1.0 - group_map["adjacency_only"] / group_map["target_only"]
    )
    group_map["adjacency_absolute_rmse_change_vs_target_only"] = (
        group_map["target_only"] - group_map["adjacency_only"]
    )
    group_map["adjacency_wins_target"] = group_map["adjacency_only"] < group_map["target_only"]
    group_map_path = OUTPUT_DIR / "condition_borrowing_map.csv"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    group_map.sort_values(["type", "condition_group"]).to_csv(group_map_path, index=False, lineterminator="\n")

    rng = np.random.default_rng(SEED)
    inference: dict[str, dict] = {}
    raw_p: dict[str, float] = {}
    bootstrap_records: list[dict] = []
    for comparator in COMPARATORS:
        label = f"adjacency_only minus {comparator}"
        parts = {aging_type: group_map.loc[group_map["type"].eq(aging_type)].reset_index(drop=True) for aging_type in ("k", "z")}
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
            bootstrap_records.append({
                "comparison": label,
                "bootstrap": index,
                "effect": boot[index],
                "calendar_effect": boot_k[index],
                "cycle_effect": boot_z[index],
            })
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
        inference[label] = {
            "effect": float(observed),
            "calendar_effect": float(stratum["k"]),
            "cycle_effect": float(stratum["z"]),
            "ci95": [float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))],
            "calendar_ci95": [float(np.quantile(boot_k, 0.025)), float(np.quantile(boot_k, 0.975))],
            "cycle_ci95": [float(np.quantile(boot_z, 0.025)), float(np.quantile(boot_z, 0.975))],
            "one_sided_sign_flip_p": p_value,
            "inferential_status": "post-hoc-outcome-guided",
        }
    adjusted = holm(raw_p)
    for label, value in adjusted.items():
        inference[label]["holm_adjusted_p"] = value

    bootstrap_path = OUTPUT_DIR / "adjacency_condition_cluster_bootstrap.csv"
    pd.DataFrame(bootstrap_records).to_csv(bootstrap_path, index=False, lineterminator="\n")
    win_summary = {
        aging_type: {
            "groups_improved": int(part["adjacency_wins_target"].sum()),
            "groups_total": len(part),
            "median_group_relative_gain": float(part["adjacency_relative_rmse_gain_vs_target_only"].median()),
        }
        for aging_type, part in group_map.groupby("type")
    }
    hard_ood: dict[str, dict] = {}
    for aging_type, part in group_map.groupby("type"):
        threshold = float(part["source_distance"].quantile(0.75))
        selected = part.loc[part["source_distance"] >= threshold]
        hard_ood[aging_type] = {
            "source_distance_q75": threshold,
            "groups": sorted(selected["condition_group"]),
            "relative_rmse_gain_vs_target_only": float(
                1.0 - selected["adjacency_only"].mean() / selected["target_only"].mean()
            ),
            "groups_improved": int(selected["adjacency_wins_target"].sum()),
            "groups_total": len(selected),
        }

    absolute_r2 = {}
    for aging_type in ("k", "z"):
        part = predictions.loc[
            predictions["type"].eq(aging_type) & predictions["policy"].eq("adjacency_only")
        ]
        absolute_r2[aging_type] = r2(part["observed"].to_numpy(), part["prediction"].to_numpy())
    adjacency_predictions = predictions.loc[predictions["policy"].eq("adjacency_only")].sort_values("file_id")
    global_predictions = predictions.loc[predictions["policy"].eq("global_credibility")].sort_values("file_id")
    if list(adjacency_predictions["file_id"]) != list(global_predictions["file_id"]):
        raise AssertionError("Adjacency and global-credibility predictions do not align")
    max_global_difference = float(
        np.max(np.abs(adjacency_predictions["prediction"].to_numpy() - global_predictions["prediction"].to_numpy()))
    )

    summary = {
        "status": "verified-complete-postrelease-adjacency-diagnostic",
        "frozen_primary_status": "non-evaluable-stage2-release",
        "confirmatory_success": False,
        "method_selection_was_outcome_guided": True,
        "inference": inference,
        "absolute_heldout_r2_by_type": absolute_r2,
        "condition_group_wins": win_summary,
        "hard_ood_diagnostic": hard_ood,
        "global_credibility_equivalence": {
            "maximum_absolute_prediction_difference": max_global_difference,
            "interpretation": "The global scalar rescaling is split-order equivalent for this tree learner and is not an independent source-specificity control.",
        },
        "condition_map_sha256": sha256(group_map_path),
        "bootstrap_sha256": sha256(bootstrap_path),
        "specification_sha256": sha256(SPECIFICATION),
        "candidate_for_independent_test": "Use a credible continuous neighboring-source prediction as one target feature; compare against target-only and matched wrong, shuffled, and random controls without a hard cross-stratum abstention gate.",
        "claim_guard": "This result is an outcome-guided diagnostic on a target whose frozen primary was non-evaluable. It nominates a policy; it does not confirm it.",
        "errors": [],
    }
    summary_path = OUTPUT_DIR / "POSTRELEASE_ADJACENCY_DIAGNOSTIC_SUMMARY.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
