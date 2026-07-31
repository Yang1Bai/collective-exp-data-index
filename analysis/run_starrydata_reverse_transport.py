"""Run the frozen outcome-unseen Starrydata reverse-transport experiment.

The program refuses to read target ZT until every pre-outcome artifact hash has
been verified.  It evaluates prediction, OOD-localized transfer, fixed
family-first exploration, and the prewritten hypothesis cards.  Smoke outputs
are explicitly non-claim-bearing.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from scipy import stats
from sklearn.ensemble import ExtraTreesRegressor, RandomForestRegressor
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis.common import composition_features  # noqa: E402
from analysis.run_caltech_ionic_external_policy import source_entities  # noqa: E402

RESULTS = HERE / "results"
DESIGN = HERE / "starrydata_reverse_transport_design.json"
IMPLEMENTATION = HERE / "starrydata_reverse_transport_implementation.json"
FREEZE = RESULTS / "starrydata_reverse_PREOUTCOME.json"
METADATA = RESULTS / "starrydata_reverse_target_metadata.csv"
PREDICTIONS = RESULTS / "starrydata_reverse_source_predictions.csv"
POLICY_ORDERS = RESULTS / "starrydata_reverse_policy_orders.csv"
CARDS = RESULTS / "starrydata_reverse_hypothesis_cards.csv"
CURVES = ROOT / "data" / "external" / "starrydata_2026-07-17" / "ThermoelectricMaterials_curves.csv.gz"

METHODS = [
    "target_only",
    "same_domain_estm_frozen_stack",
    "obelix_adjacent_frozen_stack",
    "caltech_adjacent_frozen_stack",
    "ionic_consensus_frozen_stack",
    "all_neighbor_frozen_stack",
    "source_only_calibrated",
    "naive_domain_standardized_pooling",
    "cross_fitted_residual_shrinkage",
    "cross_fitted_mixture_of_experts",
    "wrong_source_frozen_stack",
    "shuffled_source_frozen_stack",
    "equal_capacity_random_feature_stack",
]
LEARNERS = ["ridge", "random_forest", "extra_trees"]
REPRESENTATIONS = ["composition", "composition_context"]
BUDGETS = [15, 30, 60]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_seed(label: str) -> int:
    return int.from_bytes(hashlib.sha256(label.encode()).digest()[:4], "little")


def parse_list(value: object) -> list[float]:
    if pd.isna(value):
        return []
    try:
        parsed = ast.literal_eval(str(value))
    except (SyntaxError, ValueError):
        return []
    if not isinstance(parsed, (list, tuple, np.ndarray)):
        return []
    output: list[float] = []
    for item in parsed:
        try:
            output.append(float(item))
        except (TypeError, ValueError):
            output.append(float("nan"))
    return output


def verify_preoutcome() -> dict:
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    if freeze["status"] != "preoutcome-frozen":
        raise AssertionError("Outcome access denied: invalid freeze status")
    for relative, expected in freeze["artifact_hashes"].items():
        path = ROOT / relative
        if not path.is_file() or sha256(path) != expected:
            raise AssertionError(f"Outcome access denied: hash mismatch for {relative}")
    if sha256(CURVES) != freeze["input_hashes"]["curves"]:
        raise AssertionError("Outcome access denied: target curve hash mismatch")
    return freeze


def join_target_outcomes(metadata: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    # This is the first and only function that requests the target ``y`` column.
    raw = pd.read_csv(CURVES, usecols=["x", "y"], low_memory=False)
    outcomes: list[float] = []
    retained_counts: list[int] = []
    unequal = 0
    nonfinite = 0
    out_of_range = 0
    for row in metadata.itertuples(index=False):
        curve_rows = [int(value) for value in str(row.curve_rows).split(";")]
        positions = [int(value) for value in str(row.selected_positions).split(";")]
        values: list[float] = []
        for curve_row, position in zip(curve_rows, positions):
            x_values = parse_list(raw.at[curve_row, "x"])
            y_values = parse_list(raw.at[curve_row, "y"])
            if len(x_values) != len(y_values):
                unequal += 1
                continue
            if position >= len(y_values) or not math.isfinite(y_values[position]):
                nonfinite += 1
                continue
            value = float(y_values[position])
            if not 0 <= value <= 10:
                out_of_range += 1
                continue
            values.append(value)
        outcomes.append(float(np.median(values)) if values else float("nan"))
        retained_counts.append(len(values))
    target = metadata.copy()
    target["target_zt"] = outcomes
    target["outcome_curve_count"] = retained_counts
    before = len(target)
    target = target[np.isfinite(target["target_zt"])].reset_index(drop=True)
    audit = {
        "frozen_entities": before,
        "outcome_entities": len(target),
        "entities_without_outcome": before - len(target),
        "unequal_curve_lists": unequal,
        "nonfinite_selected_values": nonfinite,
        "out_of_range_selected_values": out_of_range,
    }
    return target, audit


def representations(target: pd.DataFrame) -> dict[str, np.ndarray]:
    composition = composition_features(target["material_key"].tolist()).astype(np.float32)
    text = (
        target["sample_name"].fillna("").astype(str)
        + " "
        + target["sample_info"].fillna("").astype(str)
        + " "
        + target["composition_details"].fillna("").astype(str)
    )
    context = HashingVectorizer(
        n_features=64,
        alternate_sign=True,
        norm="l2",
        analyzer="word",
        ngram_range=(1, 2),
        lowercase=True,
    ).transform(text).toarray().astype(np.float32)
    return {
        "composition": composition,
        "composition_context": np.hstack([composition, context]).astype(np.float32),
    }


def make_model(learner: str, seed: int, trees: int):
    if learner == "ridge":
        return make_pipeline(StandardScaler(), Ridge(alpha=10.0))
    common = {
        "n_estimators": trees,
        "min_samples_leaf": 2,
        "max_features": 0.7,
        "random_state": seed,
        "n_jobs": 1,
    }
    if learner == "random_forest":
        return RandomForestRegressor(**common)
    if learner == "extra_trees":
        return ExtraTreesRegressor(**common)
    raise KeyError(learner)


def select_labelled(target: pd.DataFrame, repeat: int, budget: int) -> np.ndarray:
    development = target[target["split"].eq("development")]
    groups = {str(group): local.index.to_numpy(int) for group, local in development.groupby("component_id")}
    order = sorted(groups, key=lambda group: hashlib.sha256(f"{repeat}|{budget}|{group}".encode()).hexdigest())
    selected: list[int] = []
    deferred: list[str] = []
    for group in order:
        members = list(groups[group])
        if len(selected) + len(members) <= budget:
            selected.extend(members)
        else:
            deferred.append(group)
    if deferred:
        best = min(deferred, key=lambda group: (abs(len(selected) + len(groups[group]) - budget), group))
        if abs(len(selected) + len(groups[best]) - budget) < abs(len(selected) - budget):
            selected.extend(groups[best])
    if len(selected) < 10:
        raise RuntimeError(f"repeat={repeat} budget={budget}: insufficient grouped labels")
    return np.asarray(sorted(selected), dtype=int)


def fit_predict(learner: str, seed: int, trees: int, x: np.ndarray, y: np.ndarray, train: np.ndarray, test: np.ndarray) -> np.ndarray:
    model = make_model(learner, seed, trees)
    model.fit(x[train], y[train])
    return model.predict(x[test])


def source_calibrated(source_x: np.ndarray, y: np.ndarray, train: np.ndarray, test: np.ndarray) -> np.ndarray:
    model = make_pipeline(StandardScaler(), Ridge(alpha=10.0))
    model.fit(source_x[train], y[train])
    return model.predict(source_x[test])


def mixture_weight(
    learner: str,
    seed: int,
    trees: int,
    x: np.ndarray,
    source_x: np.ndarray,
    y: np.ndarray,
    train: np.ndarray,
    groups: np.ndarray,
) -> float:
    unique = np.unique(groups[train])
    folds = min(3, len(unique))
    if folds < 2:
        return 0.5
    splitter = GroupKFold(n_splits=folds, shuffle=True, random_state=seed)
    target_oof = np.full(len(train), np.nan)
    source_oof = np.full(len(train), np.nan)
    for fold, (local_train, local_test) in enumerate(splitter.split(x[train], y[train], groups[train])):
        train_indices = train[local_train]
        test_indices = train[local_test]
        target_oof[local_test] = fit_predict(
            learner, stable_seed(f"{seed}|mix|{fold}"), trees, x, y, train_indices, test_indices
        )
        source_oof[local_test] = source_calibrated(source_x, y, train_indices, test_indices)
    target_rmse = math.sqrt(mean_squared_error(y[train], target_oof))
    source_rmse = math.sqrt(mean_squared_error(y[train], source_oof))
    inverse_target = 1.0 / max(target_rmse, 1e-12)
    inverse_source = 1.0 / max(source_rmse, 1e-12)
    return inverse_target / (inverse_target + inverse_source)


def naive_pool_prediction(
    learner: str,
    seed: int,
    trees: int,
    target_x: np.ndarray,
    target_y: np.ndarray,
    train: np.ndarray,
    test: np.ndarray,
    estm_x: np.ndarray,
    estm_y: np.ndarray,
) -> np.ndarray:
    source_mean, source_sd = float(np.mean(estm_y)), float(np.std(estm_y, ddof=1))
    target_mean, target_sd = float(np.mean(target_y[train])), float(np.std(target_y[train], ddof=1))
    source_sd = max(source_sd, 1e-8)
    target_sd = max(target_sd, 1e-8)
    pooled_x = np.vstack([estm_x, target_x[train]])
    pooled_y = np.concatenate([(estm_y - source_mean) / source_sd, (target_y[train] - target_mean) / target_sd])
    model = make_model(learner, seed, trees)
    model.fit(pooled_x, pooled_y)
    return target_mean + target_sd * model.predict(target_x[test])


def metric_rows(
    *, repeat: int, budget: int, learner: str, representation: str,
    target: pd.DataFrame, y: np.ndarray, evaluation: np.ndarray,
    predictions: dict[str, np.ndarray], labelled_n: int,
) -> tuple[list[dict], list[dict]]:
    rows: list[dict] = []
    group_rows: list[dict] = []
    scopes = {"all_evaluation": evaluation}
    for quartile in [1, 2, 3, 4]:
        scopes[f"ood_q{quartile}"] = evaluation[target.loc[evaluation, "ood_quartile"].to_numpy(int) == quartile]
    for method, prediction in predictions.items():
        for scope, indices in scopes.items():
            if len(indices) < 2:
                continue
            local = np.searchsorted(evaluation, indices)
            truth = y[indices]
            estimate = prediction[local]
            rows.append(
                {
                    "repeat": repeat,
                    "budget": budget,
                    "labelled_n": labelled_n,
                    "learner": learner,
                    "representation": representation,
                    "method": method,
                    "scope": scope,
                    "n": len(indices),
                    "rmse": math.sqrt(mean_squared_error(truth, estimate)),
                    "mae": mean_absolute_error(truth, estimate),
                    "r2": r2_score(truth, estimate),
                    "spearman": float(stats.spearmanr(truth, estimate).statistic),
                }
            )
        if budget == 30:
            squared = (y[evaluation] - prediction) ** 2
            absolute = np.abs(y[evaluation] - prediction)
            local_frame = pd.DataFrame(
                {
                    "component_id": target.loc[evaluation, "component_id"].to_numpy(),
                    "provenance_group": target.loc[evaluation, "provenance_group"].to_numpy(),
                    "squared_error": squared,
                    "absolute_error": absolute,
                }
            )
            grouped = local_frame.groupby(["component_id", "provenance_group"], as_index=False).agg(
                squared_error_sum=("squared_error", "sum"),
                absolute_error_sum=("absolute_error", "sum"),
                n=("squared_error", "size"),
            )
            for item in grouped.itertuples(index=False):
                group_rows.append(
                    {
                        "repeat": repeat,
                        "learner": learner,
                        "representation": representation,
                        "method": method,
                        "component_id": item.component_id,
                        "provenance_group": item.provenance_group,
                        "squared_error_sum": item.squared_error_sum,
                        "absolute_error_sum": item.absolute_error_sum,
                        "n": item.n,
                    }
                )
    return rows, group_rows


def run_task(
    repeat: int,
    budget: int,
    learner: str,
    representation: str,
    trees: int,
    target: pd.DataFrame,
    x: np.ndarray,
    y: np.ndarray,
    source: pd.DataFrame,
    estm_x: np.ndarray,
    estm_y: np.ndarray,
) -> tuple[list[dict], list[dict]]:
    train = select_labelled(target, repeat, budget)
    evaluation = np.sort(target.index[target["split"].eq("evaluation")].to_numpy(int))
    seed = stable_seed(f"task|{repeat}|{budget}|{learner}|{representation}")
    columns = {
        "estm": source["estm_same_domain_rank"].to_numpy(float),
        "obelix": source["obelix_adjacent_ionic_rank"].to_numpy(float),
        "caltech": source["caltech_adjacent_ionic_rank"].to_numpy(float),
        "borg": source["borg_wrong_mechanical_rank"].to_numpy(float),
        "ocx": source["ocx_wrong_catalysis_rank"].to_numpy(float),
        "shuffled_obelix": source["shuffled_obelix_adjacent_ionic_rank"].to_numpy(float),
        "shuffled_caltech": source["shuffled_caltech_adjacent_ionic_rank"].to_numpy(float),
    }
    feature_sets = {
        "same_domain_estm_frozen_stack": np.column_stack([x, columns["estm"]]),
        "obelix_adjacent_frozen_stack": np.column_stack([x, columns["obelix"]]),
        "caltech_adjacent_frozen_stack": np.column_stack([x, columns["caltech"]]),
        "ionic_consensus_frozen_stack": np.column_stack([x, columns["obelix"], columns["caltech"]]),
        "all_neighbor_frozen_stack": np.column_stack([x, columns["estm"], columns["obelix"], columns["caltech"]]),
        "wrong_source_frozen_stack": np.column_stack([x, columns["borg"], columns["ocx"]]),
        "shuffled_source_frozen_stack": np.column_stack([x, columns["shuffled_obelix"], columns["shuffled_caltech"]]),
        "equal_capacity_random_feature_stack": np.column_stack(
            [x] + [source[f"random_feature_{index}"].to_numpy(float) for index in range(1, 6)]
        ),
    }
    output: dict[str, np.ndarray] = {
        "target_only": fit_predict(learner, seed, trees, x, y, train, evaluation)
    }
    for method, augmented_x in feature_sets.items():
        output[method] = fit_predict(
            learner, stable_seed(f"{seed}|{method}"), trees, augmented_x, y, train, evaluation
        )
    source_x = np.column_stack([columns["obelix"], columns["caltech"]])
    source_prediction = source_calibrated(source_x, y, train, evaluation)
    output["source_only_calibrated"] = source_prediction
    pool_estm_x = estm_x
    if representation == "composition_context":
        pool_estm_x = np.column_stack([estm_x, np.zeros((len(estm_x), x.shape[1] - estm_x.shape[1]))])
    output["naive_domain_standardized_pooling"] = naive_pool_prediction(
        learner, stable_seed(f"{seed}|pool"), trees, x, y, train, evaluation, pool_estm_x, estm_y
    )
    calibrated_train = source_calibrated(source_x, y, train, train)
    residual = y[train] - calibrated_train
    residual_model = make_model(learner, stable_seed(f"{seed}|residual"), trees)
    residual_model.fit(x[train], residual)
    output["cross_fitted_residual_shrinkage"] = source_prediction + residual_model.predict(x[evaluation])
    weight = mixture_weight(
        learner, stable_seed(f"{seed}|mixture-weight"), trees, x, source_x, y, train,
        target["component_id"].astype(str).to_numpy(),
    )
    output["cross_fitted_mixture_of_experts"] = weight * output["target_only"] + (1 - weight) * source_prediction
    if set(output) != set(METHODS):
        raise AssertionError(f"Incomplete prediction family: {sorted(set(METHODS) - set(output))}")
    return metric_rows(
        repeat=repeat,
        budget=budget,
        learner=learner,
        representation=representation,
        target=target,
        y=y,
        evaluation=evaluation,
        predictions=output,
        labelled_n=len(train),
    )


def exploration_results(target: pd.DataFrame, policies: pd.DataFrame) -> pd.DataFrame:
    evaluation = target[target["split"].eq("evaluation")].copy()
    component_max = evaluation.groupby("component_id")["target_zt"].max().sort_values(ascending=False)
    top_n = max(1, int(math.ceil(0.05 * len(component_max))))
    top_components = set(component_max.head(top_n).index)
    top_entity_n = max(1, int(math.ceil(0.05 * len(evaluation))))
    top_entities = set(evaluation.nlargest(top_entity_n, "target_zt")["entity_id"])
    rows: list[dict] = []
    for policy, order in policies.groupby("policy", sort=True):
        order = order.sort_values("position")
        recovered: set[str] = set()
        entity_hits = 0
        cumulative = []
        first = 21
        for position, item in enumerate(order.head(20).itertuples(index=False), start=1):
            if item.component_id in top_components and item.component_id not in recovered:
                recovered.add(item.component_id)
                first = min(first, position)
            if item.entity_id in top_entities:
                entity_hits += 1
            cumulative.append(len(recovered))
        rows.append(
            {
                "policy": policy,
                "top_components": top_n,
                "distinct_component_auc20": int(sum(cumulative)),
                "component_recall20": len(recovered) / top_n,
                "first_top_component": first,
                "entity_recall20": entity_hits / top_entity_n,
            }
        )
    return pd.DataFrame(rows)


def hypothesis_results(target: pd.DataFrame, cards: pd.DataFrame, permutations: int) -> pd.DataFrame:
    values = target.set_index("entity_id")["target_zt"]
    rng = np.random.default_rng(stable_seed("starry-hypothesis-cards"))
    rows: list[dict] = []
    for card in cards.itertuples(index=False):
        candidate_ids = [value for value in str(card.candidate_entity_ids).split(";") if value in values.index]
        control_ids = [value for value in str(card.matched_target_only_control_entity_ids).split(";") if value in values.index]
        pair_n = min(len(candidate_ids), len(control_ids))
        candidate = values.loc[candidate_ids[:pair_n]].to_numpy(float)
        control = values.loc[control_ids[:pair_n]].to_numpy(float)
        differences = candidate - control
        observed = float(np.median(candidate) - np.median(control)) if pair_n else float("nan")
        if pair_n:
            null = np.empty(permutations)
            for index in range(permutations):
                signs = rng.choice([-1.0, 1.0], size=pair_n)
                null[index] = float(np.mean(differences * signs))
            p_value = float((1 + np.sum(null >= np.mean(differences))) / (permutations + 1))
        else:
            p_value = float("nan")
        rows.append(
            {
                "card_id": card.card_id,
                "pairs": pair_n,
                "candidate_median_zt": float(np.median(candidate)) if pair_n else float("nan"),
                "control_median_zt": float(np.median(control)) if pair_n else float("nan"),
                "median_difference": observed,
                "mean_paired_difference": float(np.mean(differences)) if pair_n else float("nan"),
                "randomization_p_one_sided": p_value,
            }
        )
    result = pd.DataFrame(rows)
    if len(result):
        order = np.argsort(result["randomization_p_one_sided"].to_numpy())
        adjusted = np.empty(len(result))
        running = 0.0
        for rank, index in enumerate(order):
            value = min(1.0, (len(result) - rank) * result.at[index, "randomization_p_one_sided"])
            running = max(running, value)
            adjusted[index] = running
        result["holm_p"] = adjusted
    return result


def summarize(metrics: pd.DataFrame, audit: dict, smoke: bool) -> dict:
    primary = metrics[
        metrics["budget"].eq(30)
        & metrics["learner"].eq("extra_trees")
        & metrics["representation"].eq("composition")
        & metrics["scope"].eq("ood_q4")
    ]
    pivot = primary.pivot(index="repeat", columns="method", values="rmse")
    relative = (pivot["target_only"] - pivot["ionic_consensus_frozen_stack"]) / pivot["target_only"]
    control = pivot[["wrong_source_frozen_stack", "shuffled_source_frozen_stack", "equal_capacity_random_feature_stack"]]
    control_gain = (pivot["target_only"].to_numpy()[:, None] - control.to_numpy()) / pivot["target_only"].to_numpy()[:, None]
    specificity = relative.to_numpy() - np.max(control_gain, axis=1)
    rng = np.random.default_rng(stable_seed("starry-summary-bootstrap"))
    def interval(values: np.ndarray, reps: int = 10000) -> list[float]:
        if smoke:
            reps = 200
        boot = np.mean(rng.choice(values, size=(reps, len(values)), replace=True), axis=1)
        return [float(np.mean(values)), float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))]
    return {
        "status": "smoke-nonclaim" if smoke else "formal-complete",
        "claim_guard": "One independent retrospective target; multi-target inference and prospective discovery remain separate gates.",
        "outcome_audit": audit,
        "metric_rows": len(metrics),
        "primary_cell": "n=30, ExtraTrees, composition, frozen OOD quartile 4",
        "ionic_consensus_relative_rmse_reduction": interval(relative.to_numpy()),
        "ionic_consensus_minus_best_control": interval(specificity),
        "ionic_consensus_absolute_r2_mean": float(
            primary[primary["method"].eq("ionic_consensus_frozen_stack")]["r2"].mean()
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--jobs", type=int, default=max(1, min(16, os.cpu_count() or 1)))
    args = parser.parse_args()
    freeze = verify_preoutcome()
    metadata = pd.read_csv(METADATA)
    target, outcome_audit = join_target_outcomes(metadata)
    if len(target) < 100 or target["component_id"].nunique() < 40:
        raise AssertionError("Post-join target minimum gate failed")
    source = pd.read_csv(PREDICTIONS)
    source = target[["entity_id"]].merge(source, on="entity_id", how="left", validate="one_to_one")
    if source.isna().any().any():
        raise AssertionError("Incomplete frozen source predictions after outcome join")
    source.index = target.index
    x_by_representation = representations(target)
    y = target["target_zt"].to_numpy(float)
    policies = pd.read_csv(POLICY_ORDERS)
    policies = policies[policies["entity_id"].isin(set(target["entity_id"]))].copy()
    cards = pd.read_csv(CARDS)

    target_keys = set(target["material_key"])
    target_dois = {value for value in target["normalized_doi"].dropna().astype(str) if value}
    estm = source_entities("estm_transport_neighbor", target_keys, target_dois)
    estm_x = composition_features(estm["material_key"].tolist()).astype(np.float32)
    estm_y = estm["value"].to_numpy(float)

    repeats = 2 if args.smoke else 100
    trees = 30 if args.smoke else 300
    task_specs = [
        (repeat, budget, learner, representation)
        for repeat in range(repeats)
        for budget in BUDGETS
        for learner in LEARNERS
        for representation in REPRESENTATIONS
    ]
    outputs = Parallel(n_jobs=args.jobs, verbose=10)(
        delayed(run_task)(
            repeat,
            budget,
            learner,
            representation,
            trees,
            target,
            x_by_representation[representation],
            y,
            source,
            estm_x,
            estm_y,
        )
        for repeat, budget, learner, representation in task_specs
    )
    metric_records = [row for metrics, _ in outputs for row in metrics]
    group_records = [row for _, groups in outputs for row in groups]
    metrics = pd.DataFrame(metric_records)
    group_errors = pd.DataFrame(group_records)
    exploration = exploration_results(target, policies)
    card_results = hypothesis_results(target, cards, 500 if args.smoke else 10000)
    summary = summarize(metrics, outcome_audit, args.smoke)
    prefix = "starrydata_reverse_smoke" if args.smoke else "starrydata_reverse"
    metrics.to_csv(RESULTS / f"{prefix}_metrics.csv", index=False)
    group_errors.to_csv(RESULTS / f"{prefix}_group_errors.csv", index=False)
    exploration.to_csv(RESULTS / f"{prefix}_exploration.csv", index=False)
    card_results.to_csv(RESULTS / f"{prefix}_hypothesis_tests.csv", index=False)
    (RESULTS / f"{prefix}_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    complete = {
        "status": "smoke-nonclaim" if args.smoke else "complete",
        "design_sha256": sha256(DESIGN),
        "implementation_sha256": sha256(IMPLEMENTATION),
        "preoutcome_sha256": sha256(FREEZE),
        "preoutcome_artifact_hashes": freeze["artifact_hashes"],
        "repeats": repeats,
        "task_rows": len(task_specs),
        "metric_rows": len(metrics),
        "group_error_rows": len(group_errors),
        "exploration_rows": len(exploration),
        "hypothesis_rows": len(card_results),
    }
    (RESULTS / f"{prefix}_COMPLETE.json").write_text(
        json.dumps(complete, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
