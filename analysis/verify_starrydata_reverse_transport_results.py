"""Independently verify formal Starrydata prediction, policy, and control results."""
from __future__ import annotations

import argparse
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

from analysis.prepare_starrydata_reverse_transport import family_first_order  # noqa: E402
from analysis.run_starrydata_reverse_transport import (  # noqa: E402
    CARDS,
    METADATA,
    METHODS,
    POLICY_ORDERS,
    PREDICTIONS,
    join_target_outcomes,
    sha256,
    stable_seed,
    verify_preoutcome,
)

RESULTS = HERE / "results"
METRICS = RESULTS / "starrydata_reverse_metrics.csv"
GROUP_ERRORS = RESULTS / "starrydata_reverse_group_errors.csv"
EXPLORATION = RESULTS / "starrydata_reverse_exploration.csv"
CARD_RESULTS = RESULTS / "starrydata_reverse_hypothesis_tests.csv"
SUMMARY = RESULTS / "starrydata_reverse_summary.json"
COMPLETE = RESULTS / "starrydata_reverse_COMPLETE.json"
MATCHED_METRICS = RESULTS / "starrydata_reverse_matched_specificity_metrics.csv"
MATCHED_SUMMARY = RESULTS / "starrydata_reverse_matched_specificity_summary.json"
MATCHED_COMPLETE = RESULTS / "starrydata_reverse_matched_specificity_COMPLETE.json"
OUTPUT = RESULTS / "starrydata_reverse_VALIDATED.json"
VERIFIER_AMENDMENT = HERE / "STARRYDATA_VERIFIER_AMENDMENT.md"

POLICIES = {
    "uniform_family_first",
    "composition_novelty_family_first",
    "estm_best_same_domain",
    "obelix_adjacent_single",
    "caltech_adjacent_single",
    "neighbor_entity_consensus",
    "cca_family_first_consensus",
    "cca_family_first_round_robin",
    "wrong_source_family_first",
    "shuffled_neighbor_family_first",
}
EXPLORATION_COMPARATORS = [
    "uniform_family_first",
    "composition_novelty_family_first",
    "estm_best_same_domain",
    "obelix_adjacent_single",
    "caltech_adjacent_single",
    "wrong_source_family_first",
    "shuffled_neighbor_family_first",
]
FROZEN_RANK_COLUMNS = [
    "estm_same_domain_rank",
    "obelix_adjacent_ionic_rank",
    "caltech_adjacent_ionic_rank",
]


def holm(p_values: list[float]) -> list[float]:
    order = np.argsort(p_values)
    adjusted = np.empty(len(p_values))
    running = 0.0
    for rank, index in enumerate(order):
        value = min(1.0, (len(p_values) - rank) * p_values[index])
        running = max(running, value)
        adjusted[index] = running
    return adjusted.tolist()


def interval(values: np.ndarray) -> list[float]:
    return [float(np.mean(values)), float(np.quantile(values, 0.025)), float(np.quantile(values, 0.975))]


def validate_rows(metrics: pd.DataFrame, group_errors: pd.DataFrame) -> dict:
    expected_metrics = 100 * 3 * 3 * 2 * len(METHODS) * 5
    if len(metrics) != expected_metrics:
        raise AssertionError(f"Metric row mismatch: {len(metrics)} != {expected_metrics}")
    if set(metrics["repeat"]) != set(range(100)):
        raise AssertionError("Formal repeat coverage is incomplete")
    if set(metrics["method"]) != set(METHODS):
        raise AssertionError("Formal prediction method family changed")
    keys = ["repeat", "budget", "learner", "representation", "method", "scope"]
    if metrics.duplicated(keys).any():
        raise AssertionError("Duplicate formal metric cells")
    if not np.isfinite(metrics[["rmse", "mae", "r2", "spearman"]]).all().all():
        raise AssertionError("Nonfinite formal metrics")
    units = group_errors[["component_id", "provenance_group"]].drop_duplicates()
    expected_groups = 100 * 3 * 2 * len(METHODS) * len(units)
    if len(group_errors) != expected_groups:
        raise AssertionError(f"Group-error row mismatch: {len(group_errors)} != {expected_groups}")
    return {"metric_rows": len(metrics), "group_error_rows": len(group_errors), "evaluation_units": len(units)}


def hierarchical_prediction(group_errors: pd.DataFrame, bootstrap_reps: int) -> dict:
    local = group_errors[
        group_errors["learner"].eq("extra_trees")
        & group_errors["representation"].eq("composition")
        & group_errors["method"].isin(
            [
                "target_only",
                "ionic_consensus_frozen_stack",
                "same_domain_estm_frozen_stack",
                "wrong_source_frozen_stack",
                "shuffled_source_frozen_stack",
                "equal_capacity_random_feature_stack",
            ]
        )
    ].copy()
    local["unit"] = local["component_id"].astype(str) + "|" + local["provenance_group"].astype(str)
    repeats = sorted(local["repeat"].unique())
    units = sorted(local["unit"].unique())
    methods = sorted(local["method"].unique())
    method_index = {method: index for index, method in enumerate(methods)}
    pivot = local.pivot(index=["repeat", "unit"], columns="method", values="squared_error_sum")
    counts = local.drop_duplicates(["repeat", "unit"]).set_index(["repeat", "unit"])["n"]
    sse = np.empty((len(repeats), len(units), len(methods)))
    n = np.empty((len(repeats), len(units)))
    for r_index, repeat in enumerate(repeats):
        sse[r_index] = pivot.loc[repeat, methods].reindex(units).to_numpy(float)
        n[r_index] = counts.loc[repeat].reindex(units).to_numpy(float)
    rng = np.random.default_rng(stable_seed("starry-two-level-bootstrap"))
    effects = np.empty((bootstrap_reps, 3))
    for bootstrap in range(bootstrap_reps):
        repeat_indices = rng.integers(0, len(repeats), len(repeats))
        unit_indices = rng.integers(0, len(units), len(units))
        sampled_sse = sse[repeat_indices][:, unit_indices, :].sum(axis=(0, 1))
        sampled_n = n[repeat_indices][:, unit_indices].sum()
        rmse = np.sqrt(sampled_sse / sampled_n)
        baseline = rmse[method_index["target_only"]]
        gain = (baseline - rmse) / baseline
        ionic = gain[method_index["ionic_consensus_frozen_stack"]]
        effects[bootstrap, 0] = ionic
        effects[bootstrap, 1] = ionic - gain[method_index["same_domain_estm_frozen_stack"]]
        controls = [
            gain[method_index["wrong_source_frozen_stack"]],
            gain[method_index["shuffled_source_frozen_stack"]],
            gain[method_index["equal_capacity_random_feature_stack"]],
        ]
        effects[bootstrap, 2] = ionic - max(controls)
    p_values = [float((1 + np.sum(effects[:, index] <= 0)) / (bootstrap_reps + 1)) for index in range(3)]
    labels = ["ionic_vs_target", "ionic_vs_same_domain_estm", "ionic_vs_best_control"]
    adjusted = holm(p_values)
    return {
        label: {
            "mean_ci95": interval(effects[:, index]),
            "bootstrap_p_one_sided": p_values[index],
            "holm_p": adjusted[index],
        }
        for index, label in enumerate(labels)
    }


def robustness(metrics: pd.DataFrame) -> list[dict]:
    local = metrics[
        metrics["budget"].eq(30)
        & metrics["scope"].eq("ood_q4")
        & metrics["method"].isin(["target_only", "ionic_consensus_frozen_stack"])
    ]
    pivot = local.pivot(
        index=["repeat", "learner", "representation"], columns="method", values="rmse"
    ).reset_index()
    pivot["relative_rmse_gain"] = (
        pivot["target_only"] - pivot["ionic_consensus_frozen_stack"]
    ) / pivot["target_only"]
    return (
        pivot.groupby(["learner", "representation"], as_index=False)["relative_rmse_gain"]
        .agg(["mean", "std", "count"])
        .reset_index()
        .to_dict("records")
    )


def component_auc(order: pd.DataFrame, top_components: set[str]) -> int:
    recovered: set[str] = set()
    cumulative: list[int] = []
    for item in order.sort_values("position").head(20).itertuples(index=False):
        if item.component_id in top_components:
            recovered.add(item.component_id)
        cumulative.append(len(recovered))
    return int(sum(cumulative))


def merge_frozen_exploration_ranks(
    evaluation: pd.DataFrame, frozen: pd.DataFrame
) -> pd.DataFrame:
    """Attach frozen ranks without duplicating target component metadata."""
    target_required = {"entity_id", "component_id"}
    frozen_required = target_required | set(FROZEN_RANK_COLUMNS)
    if not target_required.issubset(evaluation.columns):
        raise AssertionError("Evaluation target lacks entity or component metadata")
    if not frozen_required.issubset(frozen.columns):
        raise AssertionError("Frozen source table lacks exploration ranks or component metadata")
    if evaluation["entity_id"].duplicated().any() or frozen["entity_id"].duplicated().any():
        raise AssertionError("Exploration entity identifiers are not one-to-one")

    component_audit = evaluation[["entity_id", "component_id"]].merge(
        frozen[["entity_id", "component_id"]],
        on="entity_id",
        how="left",
        validate="one_to_one",
        suffixes=("_target", "_frozen"),
    )
    if component_audit["component_id_frozen"].isna().any():
        raise AssertionError("Frozen source ranks do not cover every evaluation entity")
    if not component_audit["component_id_target"].astype(str).equals(
        component_audit["component_id_frozen"].astype(str)
    ):
        raise AssertionError("Target and frozen component assignments disagree")

    pool = evaluation.merge(
        frozen[["entity_id", *FROZEN_RANK_COLUMNS]],
        on="entity_id",
        how="left",
        validate="one_to_one",
    ).reset_index(drop=True)
    if pool[FROZEN_RANK_COLUMNS].isna().any().any():
        raise AssertionError("Frozen exploration ranks are incomplete")
    return pool


def exploration_inference(target: pd.DataFrame, permutations: int, bootstrap_reps: int) -> dict:
    policies = pd.read_csv(POLICY_ORDERS)
    policies = policies[policies["entity_id"].isin(set(target["entity_id"]))].copy()
    observed = pd.read_csv(EXPLORATION).set_index("policy")
    if set(observed.index) != POLICIES:
        raise AssertionError("Exploration policy family changed")
    evaluation = target[target["split"].eq("evaluation")].copy()
    component_max = evaluation.groupby("component_id")["target_zt"].max().sort_values(ascending=False)
    top_n = max(1, int(math.ceil(0.05 * len(component_max))))
    top_components = set(component_max.head(top_n).index)

    # Component-block bootstrap of AUC20 contrasts. Each top component's AUC
    # contribution is determined by its first recovery position.
    all_components = sorted(evaluation["component_id"].unique())
    contribution: dict[str, np.ndarray] = {}
    for policy in ["cca_family_first_consensus"] + EXPLORATION_COMPARATORS:
        order = policies[policies["policy"].eq(policy)].sort_values("position")
        first = order.groupby("component_id")["position"].min().to_dict()
        contribution[policy] = np.asarray(
            [max(0, 21 - int(first.get(component, 21))) if component in top_components else 0 for component in all_components],
            dtype=float,
        )
    rng = np.random.default_rng(stable_seed("starry-component-bootstrap"))
    differences = {policy: np.empty(bootstrap_reps) for policy in EXPLORATION_COMPARATORS}
    for bootstrap in range(bootstrap_reps):
        counts = rng.multinomial(len(all_components), np.full(len(all_components), 1 / len(all_components)))
        cca = float(np.sum(counts * contribution["cca_family_first_consensus"]))
        for policy in EXPLORATION_COMPARATORS:
            differences[policy][bootstrap] = cca - float(np.sum(counts * contribution[policy]))
    p_values = [
        float((1 + np.sum(differences[policy] <= 0)) / (bootstrap_reps + 1))
        for policy in EXPLORATION_COMPARATORS
    ]
    adjusted = holm(p_values)
    contrasts = {
        policy: {
            "auc20_difference_ci95": interval(differences[policy]),
            "bootstrap_p_one_sided": p_values[index],
            "holm_p": adjusted[index],
        }
        for index, policy in enumerate(EXPLORATION_COMPARATORS)
    }

    # Conditional source-rank null for the frozen CCA family-first order.
    frozen = pd.read_csv(PREDICTIONS)
    pool = merge_frozen_exploration_ranks(evaluation, frozen)
    estm = pool["estm_same_domain_rank"].to_numpy(float)
    obelix = pool["obelix_adjacent_ionic_rank"].to_numpy(float)
    caltech = pool["caltech_adjacent_ionic_rank"].to_numpy(float)
    observed_auc = int(observed.at["cca_family_first_consensus", "distinct_component_auc20"])
    null = np.empty(permutations)
    for index in range(permutations):
        score = pd.Series((estm + rng.permutation(obelix) + rng.permutation(caltech)) / 3)
        order_indices = family_first_order(pool, score, "component_id")
        order = pool.loc[order_indices, ["entity_id", "component_id"]].copy()
        order["position"] = np.arange(1, len(order) + 1)
        null[index] = component_auc(order, top_components)
    return {
        "observed_cca_auc20": observed_auc,
        "component_bootstrap_contrasts": contrasts,
        "source_rank_permutation_p": float((1 + np.sum(null >= observed_auc)) / (permutations + 1)),
        "source_rank_null_mean": float(np.mean(null)),
        "source_rank_null_ci95": [float(np.quantile(null, 0.025)), float(np.quantile(null, 0.975))],
    }


def validate_matched() -> dict:
    complete = json.loads(MATCHED_COMPLETE.read_text(encoding="utf-8"))
    if complete["status"] != "complete" or complete["repeats"] != 100:
        raise AssertionError("Matched-specificity run incomplete")
    metrics = pd.read_csv(MATCHED_METRICS)
    if set(metrics["repeat"]) != set(range(100)):
        raise AssertionError("Matched-specificity repeat coverage incomplete")
    if metrics.duplicated(["repeat", "method", "scope"]).any():
        raise AssertionError("Duplicate matched-specificity cells")
    return {
        "metric_rows": len(metrics),
        "methods": sorted(metrics["method"].unique()),
        "scopes": sorted(metrics["scope"].unique()),
        "reported_summary_sha256": sha256(MATCHED_SUMMARY),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--portable", action="store_true")
    args = parser.parse_args()
    freeze = verify_preoutcome()
    complete = json.loads(COMPLETE.read_text(encoding="utf-8"))
    if complete["status"] != "complete" or complete["repeats"] != 100:
        raise AssertionError("Formal Starrydata run incomplete")
    metrics = pd.read_csv(METRICS)
    group_errors = pd.read_csv(GROUP_ERRORS)
    row_validation = validate_rows(metrics, group_errors)
    metadata = pd.read_csv(METADATA)
    target, outcome_audit = join_target_outcomes(metadata)
    cards = pd.read_csv(CARD_RESULTS)
    if len(cards) != len(pd.read_csv(CARDS)) or cards["card_id"].duplicated().any():
        raise AssertionError("Hypothesis-card family incomplete")
    prediction = hierarchical_prediction(group_errors, 10000)
    exploration = exploration_inference(target, 5000, 10000)
    matched = validate_matched()
    result = {
        "status": "verified-complete",
        "verification_mode": "portable" if args.portable else "formal-environment",
        "preoutcome_sha256": sha256(RESULTS / "starrydata_reverse_PREOUTCOME.json"),
        "preoutcome_artifact_hashes": freeze["artifact_hashes"],
        "outcome_audit": outcome_audit,
        "row_validation": row_validation,
        "hierarchical_primary_prediction": prediction,
        "learner_representation_robustness": robustness(metrics),
        "exploration_inference": exploration,
        "matched_specificity_validation": matched,
        "hypothesis_cards": len(cards),
        "reported_summary_sha256": sha256(SUMMARY),
        "verifier_amendment_sha256": sha256(VERIFIER_AMENDMENT),
        "claim_guard": "This validates one independent retrospective reverse-edge target. Second-family and multi-target inference remain open; prospective discovery is not established.",
    }
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
