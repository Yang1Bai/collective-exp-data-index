"""Verify formal TRI OER second-family results and independent plate inference."""
from __future__ import annotations

import argparse
import itertools
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis.prepare_tri_oer_neighbor import PLATE_ELEMENTS  # noqa: E402
from analysis.run_tri_oer_neighbor import (  # noqa: E402
    CARDS,
    FREEZE,
    IMPLEMENTATION,
    METADATA,
    METHODS,
    POLICY_ORDERS,
    join_fom,
    sha256,
    verify_preoutcome,
)

RESULTS = HERE / "results"
METRICS = RESULTS / "tri_oer_metrics.csv"
GROUP_ERRORS = RESULTS / "tri_oer_group_errors.csv"
SPECIFICITY = RESULTS / "tri_oer_matched_specificity.csv"
EXPLORATION = RESULTS / "tri_oer_exploration.csv"
HYPOTHESES = RESULTS / "tri_oer_hypothesis_tests.csv"
SUMMARY = RESULTS / "tri_oer_summary.json"
COMPLETE = RESULTS / "tri_oer_COMPLETE.json"
OUTPUT = RESULTS / "tri_oer_VALIDATED.json"

POLICIES = {
    "uniform_family_first",
    "composition_novelty_family_first",
    "acid_oer_same_reaction_single",
    "orr_adjacent_single",
    "ocx_adjacent_single",
    "neighbor_entity_consensus",
    "cca_family_first_consensus",
    "cca_family_first_round_robin",
    "wrong_source_family_first",
    "shuffled_neighbor_family_first",
}
COMPARATORS = [
    "uniform_family_first",
    "composition_novelty_family_first",
    "acid_oer_same_reaction_single",
    "orr_adjacent_single",
    "ocx_adjacent_single",
    "wrong_source_family_first",
    "shuffled_neighbor_family_first",
]


def holm(values: list[float]) -> list[float]:
    order = np.argsort(values)
    adjusted = np.empty(len(values))
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, min(1.0, (len(values) - rank) * values[index]))
        adjusted[index] = running
    return adjusted.tolist()


def bootstrap_interval(values: np.ndarray, rng: np.random.Generator, reps: int = 10000) -> list[float]:
    boot = np.mean(rng.choice(values, size=(reps, len(values)), replace=True), axis=1)
    return [float(np.mean(values)), float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))]


def random_effects(effects: np.ndarray, variances: np.ndarray) -> dict:
    fixed_weights = 1 / np.maximum(variances, 1e-12)
    fixed_mean = float(np.sum(fixed_weights * effects) / np.sum(fixed_weights))
    q = float(np.sum(fixed_weights * (effects - fixed_mean) ** 2))
    df = len(effects) - 1
    c = float(np.sum(fixed_weights) - np.sum(fixed_weights**2) / np.sum(fixed_weights))
    tau2 = max(0.0, (q - df) / max(c, 1e-12))
    weights = 1 / (variances + tau2)
    mean = float(np.sum(weights * effects) / np.sum(weights))
    se = math.sqrt(1 / np.sum(weights))
    return {
        "mean": mean,
        "ci95": [mean - 1.96 * se, mean + 1.96 * se],
        "tau_squared": tau2,
        "q": q,
        "i_squared_percent": max(0.0, (q - df) / max(q, 1e-12)) * 100,
    }


def validate_rows(metrics: pd.DataFrame, group_errors: pd.DataFrame) -> dict:
    expected = 4 * 100 * 3 * 3 * 2 * len(METHODS) * 5
    if len(metrics) != expected:
        raise AssertionError(f"TRI metric rows {len(metrics)} != {expected}")
    if set(metrics["plate"].astype(str)) != set(PLATE_ELEMENTS):
        raise AssertionError("TRI plate family incomplete")
    if set(metrics["repeat"]) != set(range(100)) or set(metrics["method"]) != set(METHODS):
        raise AssertionError("TRI repeat or method coverage incomplete")
    keys = ["plate", "repeat", "budget", "learner", "representation", "method", "scope"]
    if metrics.duplicated(keys).any():
        raise AssertionError("Duplicate TRI metric cells")
    if not np.isfinite(metrics[["rmse", "mae", "r2", "spearman"]]).all().all():
        raise AssertionError("Nonfinite TRI metrics")
    if group_errors.empty or set(group_errors["method"]) != set(METHODS):
        raise AssertionError("TRI component-error family incomplete")
    return {"metric_rows": len(metrics), "group_error_rows": len(group_errors)}


def prediction_inference(metrics: pd.DataFrame) -> dict:
    local = metrics[
        metrics["budget"].eq(30)
        & metrics["learner"].eq("extra_trees")
        & metrics["representation"].eq("element_fraction")
        & metrics["scope"].eq("dynamic_ood_q4")
    ]
    pivot = local.pivot(index=["plate", "repeat"], columns="method", values="rmse")
    baseline = pivot["target_only"]
    gains = pd.DataFrame(index=pivot.index)
    for method in [
        "all_neighbor_frozen_stack",
        "acid_same_reaction_frozen_stack",
        "adjacent_consensus_frozen_stack",
        "wrong_source_frozen_stack",
        "shuffled_source_frozen_stack",
        "equal_capacity_random_feature_stack",
    ]:
        gains[method] = (baseline - pivot[method]) / baseline
    effects_by_plate: dict[str, list[dict]] = {}
    contrast_names = ["all_vs_target", "all_vs_same", "adjacent_vs_same", "all_vs_best_control"]
    plate_effect_matrix = np.empty((len(PLATE_ELEMENTS), 4))
    plate_variance_matrix = np.empty((len(PLATE_ELEMENTS), 4))
    rng = np.random.default_rng(20260718)
    for plate_index, plate in enumerate(PLATE_ELEMENTS):
        frame = gains.xs(plate)
        contrasts = np.column_stack(
            [
                frame["all_neighbor_frozen_stack"],
                frame["all_neighbor_frozen_stack"] - frame["acid_same_reaction_frozen_stack"],
                frame["adjacent_consensus_frozen_stack"] - frame["acid_same_reaction_frozen_stack"],
                frame["all_neighbor_frozen_stack"]
                - frame[
                    [
                        "wrong_source_frozen_stack",
                        "shuffled_source_frozen_stack",
                        "equal_capacity_random_feature_stack",
                    ]
                ].max(axis=1),
            ]
        )
        plate_effect_matrix[plate_index] = contrasts.mean(axis=0)
        plate_variance_matrix[plate_index] = contrasts.var(axis=0, ddof=1) / len(contrasts)
        effects_by_plate[plate] = [
            {"contrast": name, "mean_ci95": bootstrap_interval(contrasts[:, index], rng)}
            for index, name in enumerate(contrast_names)
        ]
    p_values: list[float] = []
    for contrast_index in range(4):
        effects = plate_effect_matrix[:, contrast_index]
        sign_null = [float(np.mean(effects * np.asarray(signs))) for signs in itertools.product([-1, 1], repeat=4)]
        p_values.append(float((1 + np.sum(np.asarray(sign_null) >= np.mean(effects))) / (len(sign_null) + 1)))
    adjusted = holm(p_values)
    across = {
        name: {
            "random_effects": random_effects(
                plate_effect_matrix[:, index], plate_variance_matrix[:, index]
            ),
            "plate_effects": {
                plate: float(plate_effect_matrix[p_index, index])
                for p_index, plate in enumerate(PLATE_ELEMENTS)
            },
            "positive_plates": int(np.sum(plate_effect_matrix[:, index] > 0)),
            "exact_sign_randomization_p": p_values[index],
            "holm_p": adjusted[index],
        }
        for index, name in enumerate(contrast_names)
    }
    absolute = local[local["method"].eq("all_neighbor_frozen_stack")].groupby("plate")["r2"].mean().to_dict()
    return {"by_plate": effects_by_plate, "across_plates": across, "absolute_r2_by_plate": absolute}


def robustness(metrics: pd.DataFrame) -> list[dict]:
    local = metrics[
        metrics["budget"].eq(30)
        & metrics["scope"].eq("dynamic_ood_q4")
        & metrics["method"].isin(["target_only", "all_neighbor_frozen_stack"])
    ]
    pivot = local.pivot(
        index=["plate", "repeat", "learner", "representation"], columns="method", values="rmse"
    ).reset_index()
    pivot["relative_gain"] = (pivot["target_only"] - pivot["all_neighbor_frozen_stack"]) / pivot["target_only"]
    return (
        pivot.groupby(["learner", "representation"], as_index=False)["relative_gain"]
        .agg(mean="mean", std="std", positive_fraction=lambda values: float(np.mean(values > 0)))
        .to_dict("records")
    )


def exploration_inference(exploration: pd.DataFrame) -> dict:
    if set(exploration["policy"]) != POLICIES or set(exploration["plate"].astype(str)) != set(PLATE_ELEMENTS):
        raise AssertionError("TRI exploration family incomplete")
    pivot = exploration.pivot(index="plate", columns="policy", values="distinct_component_auc20")
    contrasts = {
        comparator: (pivot["cca_family_first_consensus"] - pivot[comparator]).to_numpy(float)
        for comparator in COMPARATORS
    }
    p_values = []
    for comparator in COMPARATORS:
        values = contrasts[comparator]
        null = [float(np.mean(values * np.asarray(signs))) for signs in itertools.product([-1, 1], repeat=4)]
        p_values.append(float((1 + np.sum(np.asarray(null) >= np.mean(values))) / (len(null) + 1)))
    adjusted = holm(p_values)
    return {
        comparator: {
            "plate_differences": contrasts[comparator].tolist(),
            "mean_difference": float(np.mean(contrasts[comparator])),
            "positive_plates": int(np.sum(contrasts[comparator] > 0)),
            "exact_sign_randomization_p": p_values[index],
            "holm_p": adjusted[index],
        }
        for index, comparator in enumerate(COMPARATORS)
    }


def specificity_validation(frame: pd.DataFrame) -> dict:
    if frame.empty or set(frame["plate"].astype(str)) != set(PLATE_ELEMENTS):
        raise AssertionError("Matched specificity results incomplete")
    if set(frame["repeat"]) != set(range(100)):
        raise AssertionError("Matched specificity repeat coverage incomplete")
    return {
        "rows": len(frame),
        "methods": sorted(frame["method"].unique()),
        "scopes": sorted(frame["scope"].unique()),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--portable", action="store_true")
    args = parser.parse_args()
    freeze = verify_preoutcome()
    complete = json.loads(COMPLETE.read_text(encoding="utf-8"))
    if complete["status"] != "complete" or complete["repeats_per_plate"] != 100:
        raise AssertionError("TRI formal run incomplete")
    metrics = pd.read_csv(METRICS, dtype={"plate": str})
    group_errors = pd.read_csv(GROUP_ERRORS, dtype={"plate": str})
    row_validation = validate_rows(metrics, group_errors)
    specificity = pd.read_csv(SPECIFICITY, dtype={"plate": str})
    exploration = pd.read_csv(EXPLORATION, dtype={"plate": str})
    hypotheses = pd.read_csv(HYPOTHESES)
    if len(hypotheses) != len(pd.read_csv(CARDS)) or hypotheses["card_id"].duplicated().any():
        raise AssertionError("TRI hypothesis-card family incomplete")
    metadata = pd.read_csv(METADATA, dtype={"plate": str})
    target, outcome_audit = join_fom(metadata)
    result = {
        "status": "verified-complete",
        "verification_mode": "portable" if args.portable else "formal-environment",
        "design_sha256": sha256(HERE / "tri_oer_neighbor_design.json"),
        "implementation_sha256": sha256(IMPLEMENTATION),
        "preoutcome_sha256": sha256(FREEZE),
        "preoutcome_artifact_hashes": freeze["artifact_hashes"],
        "outcome_audit": outcome_audit,
        "row_validation": row_validation,
        "prediction_inference": prediction_inference(metrics),
        "learner_representation_robustness": robustness(metrics),
        "exploration_inference": exploration_inference(exploration),
        "specificity_validation": specificity_validation(specificity),
        "hypothesis_cards": len(hypotheses),
        "summary_sha256": sha256(SUMMARY),
        "claim_guard": "This is a four-plate retrospective second-family test. Cross-target synthesis with Starrydata remains required; prospective discovery is not established.",
    }
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
