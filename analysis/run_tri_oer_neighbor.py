"""Run the frozen clean TRI OER second-family neighbor-borrowing experiment."""
from __future__ import annotations

import argparse
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
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold
from sklearn.neighbors import NearestNeighbors

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis.common import ELEMENT_INDEX, composition_features, key_to_dict  # noqa: E402
from analysis.prepare_tri_oer_neighbor import (  # noqa: E402
    ACID_TARGET,
    PLATE_ELEMENTS,
    PICKLE,
    SchemaUnpickler,
    load_acid_source,
)
from analysis.run_starrydata_reverse_transport import (  # noqa: E402
    fit_predict,
    make_model,
    naive_pool_prediction,
    source_calibrated,
    stable_seed,
)

RESULTS = HERE / "results"
DESIGN = HERE / "tri_oer_neighbor_design.json"
IMPLEMENTATION = HERE / "tri_oer_implementation.json"
FREEZE = RESULTS / "tri_oer_PREOUTCOME.json"
METADATA = RESULTS / "tri_oer_target_metadata.csv"
PREDICTIONS = RESULTS / "tri_oer_source_predictions.csv"
MATCHED = RESULTS / "tri_oer_matched_source_controls.csv"
POLICY_ORDERS = RESULTS / "tri_oer_policy_orders.csv"
CARDS = RESULTS / "tri_oer_hypothesis_cards.csv"

METHODS = [
    "target_only",
    "acid_same_reaction_frozen_stack",
    "orr_adjacent_frozen_stack",
    "ocx_adjacent_frozen_stack",
    "adjacent_consensus_frozen_stack",
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
REPRESENTATIONS = ["element_fraction", "periodic_summary"]
BUDGETS = [15, 30, 60]
REAL_SOURCES = [
    "acid_oer_same_reaction",
    "orr_adjacent_oxygen_electrocatalysis",
    "ocx_adjacent_electrocatalysis",
]
WRONG_SOURCES = ["borg_wrong_mechanical", "obelix_wrong_ionic"]

PERIODIC = {
    "Ca": (20, 2, 4, 1.00, 176),
    "Ti": (22, 4, 4, 1.54, 160),
    "Mn": (25, 7, 4, 1.55, 139),
    "Fe": (26, 8, 4, 1.83, 132),
    "Co": (27, 9, 4, 1.88, 126),
    "Ni": (28, 10, 4, 1.91, 124),
    "Cu": (29, 11, 4, 1.90, 132),
    "Sn": (50, 14, 5, 1.96, 139),
    "Sb": (51, 15, 5, 2.05, 139),
    "La": (57, 3, 6, 1.10, 207),
    "Ce": (58, 3, 6, 1.12, 204),
    "Ta": (73, 5, 6, 1.50, 146),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_preoutcome() -> dict:
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    if freeze["status"] != "preoutcome-frozen":
        raise AssertionError("TRI outcome access denied: invalid freeze")
    for relative, expected in freeze["artifact_hashes"].items():
        path = ROOT / relative
        if not path.is_file() or sha256(path) != expected:
            raise AssertionError(f"TRI outcome access denied: hash mismatch {relative}")
    if sha256(PICKLE) != freeze["target_sha256"]:
        raise AssertionError("TRI target hash mismatch")
    return freeze


def join_fom(metadata: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    # First target FOM decode occurs only after verify_preoutcome succeeds.
    with PICKLE.open("rb") as handle:
        schema = SchemaUnpickler(handle, encoding="latin1").load()
    values: list[float] = []
    for row in metadata.itertuples(index=False):
        fom = schema[str(row.plate)]["fom"].decode()
        values.append(float(fom[int(row.original_row)]))
    target = metadata.copy()
    target["target_fom"] = values
    before = len(target)
    target = target[np.isfinite(target["target_fom"])].reset_index(drop=True)
    return target, {
        "frozen_entities": before,
        "outcome_entities": len(target),
        "nonfinite_excluded": before - len(target),
        "plate_counts": {
            str(key): int(value) for key, value in target["plate"].value_counts().sort_index().items()
        },
    }


def periodic_summary(keys: list[str]) -> np.ndarray:
    rows: list[list[float]] = []
    for key in keys:
        composition = key_to_dict(key)
        elements = [element for element in composition if element in PERIODIC]
        weights = np.asarray([composition[element] for element in elements], dtype=float)
        weights /= weights.sum()
        props = np.asarray([PERIODIC[element] for element in elements], dtype=float)
        features: list[float] = []
        for column in range(props.shape[1]):
            values = props[:, column]
            mean = float(np.sum(weights * values))
            features.extend(
                [mean, math.sqrt(float(np.sum(weights * (values - mean) ** 2))), float(values.min()), float(values.max())]
            )
        features.extend(
            [float(len(elements)), -float(np.sum(weights * np.log(weights))), float(np.max(weights)), float(np.sum(weights**2))]
        )
        rows.append(features)
    return np.asarray(rows, dtype=np.float32)


def representations(target: pd.DataFrame) -> dict[str, np.ndarray]:
    keys = target["material_key"].tolist()
    return {
        "element_fraction": composition_features(keys).astype(np.float32)[:, : len(ELEMENT_INDEX)],
        "periodic_summary": periodic_summary(keys),
    }


def select_labelled(target: pd.DataFrame, plate: str, repeat: int, budget: int) -> np.ndarray:
    local = target[target["plate"].astype(str).eq(str(plate))]
    groups = {str(group): frame.index.to_numpy(int) for group, frame in local.groupby("composition_cluster")}
    order = sorted(groups, key=lambda group: hashlib.sha256(f"{plate}|{repeat}|{budget}|{group}".encode()).hexdigest())
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
        raise RuntimeError(f"{plate}/{repeat}/{budget}: insufficient selected labels")
    return np.asarray(sorted(selected), dtype=int)


def dynamic_scopes(x_fraction: np.ndarray, labelled: np.ndarray, evaluation: np.ndarray) -> dict[str, np.ndarray]:
    distance = NearestNeighbors(n_neighbors=1).fit(x_fraction[labelled]).kneighbors(
        x_fraction[evaluation], return_distance=True
    )[0][:, 0]
    quartiles = pd.qcut(pd.Series(distance), 4, labels=[1, 2, 3, 4], duplicates="drop").astype(int).to_numpy()
    scopes = {"all_evaluation": evaluation}
    for quartile in [1, 2, 3, 4]:
        scopes[f"dynamic_ood_q{quartile}"] = evaluation[quartiles == quartile]
    return scopes


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
    folds = min(3, len(np.unique(groups[train])))
    if folds < 2:
        return 0.5
    splitter = GroupKFold(n_splits=folds, shuffle=True, random_state=seed)
    target_oof = np.full(len(train), np.nan)
    source_oof = np.full(len(train), np.nan)
    for fold, (local_train, local_test) in enumerate(splitter.split(x[train], y[train], groups[train])):
        train_indices, test_indices = train[local_train], train[local_test]
        target_oof[local_test] = fit_predict(
            learner, stable_seed(f"{seed}|target|{fold}"), trees, x, y, train_indices, test_indices
        )
        source_oof[local_test] = source_calibrated(source_x, y, train_indices, test_indices)
    target_rmse = math.sqrt(mean_squared_error(y[train], target_oof))
    source_rmse = math.sqrt(mean_squared_error(y[train], source_oof))
    return (1 / max(target_rmse, 1e-12)) / (
        1 / max(target_rmse, 1e-12) + 1 / max(source_rmse, 1e-12)
    )


def task(
    plate: str,
    repeat: int,
    budget: int,
    learner: str,
    representation: str,
    trees: int,
    target: pd.DataFrame,
    x: np.ndarray,
    x_fraction: np.ndarray,
    y: np.ndarray,
    source: pd.DataFrame,
    matched: pd.DataFrame,
    acid_x: np.ndarray,
    acid_y: np.ndarray,
) -> tuple[list[dict], list[dict], list[dict]]:
    labelled = select_labelled(target, plate, repeat, budget)
    plate_indices = target.index[target["plate"].astype(str).eq(str(plate))].to_numpy(int)
    evaluation = np.asarray(sorted(set(plate_indices) - set(labelled)), dtype=int)
    scopes = dynamic_scopes(x_fraction, labelled, evaluation)
    seed = stable_seed(f"tri-task|{plate}|{repeat}|{budget}|{learner}|{representation}")
    rank = {
        "acid": source["acid_oer_same_reaction_rank"].to_numpy(float),
        "orr": source["orr_adjacent_oxygen_electrocatalysis_rank"].to_numpy(float),
        "ocx": source["ocx_adjacent_electrocatalysis_rank"].to_numpy(float),
        "borg": source["borg_wrong_mechanical_rank"].to_numpy(float),
        "obelix": source["obelix_wrong_ionic_rank"].to_numpy(float),
        "shuffled_acid": source["shuffled_acid_oer_same_reaction_rank"].to_numpy(float),
        "shuffled_orr": source["shuffled_orr_adjacent_oxygen_electrocatalysis_rank"].to_numpy(float),
        "shuffled_ocx": source["shuffled_ocx_adjacent_electrocatalysis_rank"].to_numpy(float),
    }
    feature_sets = {
        "acid_same_reaction_frozen_stack": np.column_stack([x, rank["acid"]]),
        "orr_adjacent_frozen_stack": np.column_stack([x, rank["orr"]]),
        "ocx_adjacent_frozen_stack": np.column_stack([x, rank["ocx"]]),
        "adjacent_consensus_frozen_stack": np.column_stack([x, rank["orr"], rank["ocx"]]),
        "all_neighbor_frozen_stack": np.column_stack([x, rank["acid"], rank["orr"], rank["ocx"]]),
        "wrong_source_frozen_stack": np.column_stack([x, rank["borg"], rank["obelix"]]),
        "shuffled_source_frozen_stack": np.column_stack(
            [x, rank["shuffled_acid"], rank["shuffled_orr"], rank["shuffled_ocx"]]
        ),
        "equal_capacity_random_feature_stack": np.column_stack(
            [x] + [source[f"random_feature_{index}"].to_numpy(float) for index in range(1, 6)]
        ),
    }
    predictions: dict[str, np.ndarray] = {
        "target_only": fit_predict(learner, seed, trees, x, y, labelled, evaluation)
    }
    for method, augmented in feature_sets.items():
        predictions[method] = fit_predict(
            learner, stable_seed(f"{seed}|{method}"), trees, augmented, y, labelled, evaluation
        )
    source_x = np.column_stack([rank["acid"], rank["orr"], rank["ocx"]])
    source_prediction = source_calibrated(source_x, y, labelled, evaluation)
    predictions["source_only_calibrated"] = source_prediction
    pool_acid_x = acid_x
    predictions["naive_domain_standardized_pooling"] = naive_pool_prediction(
        learner, stable_seed(f"{seed}|pool"), trees, x, y, labelled, evaluation, pool_acid_x, acid_y
    )
    calibrated_train = source_calibrated(source_x, y, labelled, labelled)
    residual_model = make_model(learner, stable_seed(f"{seed}|residual"), trees)
    residual_model.fit(x[labelled], y[labelled] - calibrated_train)
    predictions["cross_fitted_residual_shrinkage"] = source_prediction + residual_model.predict(x[evaluation])
    weight = mixture_weight(
        learner, stable_seed(f"{seed}|mixture"), trees, x, source_x, y, labelled,
        target["composition_cluster"].astype(str).to_numpy(),
    )
    predictions["cross_fitted_mixture_of_experts"] = (
        weight * predictions["target_only"] + (1 - weight) * source_prediction
    )
    if set(predictions) != set(METHODS):
        raise AssertionError("Incomplete TRI method family")

    index_to_local = {index: position for position, index in enumerate(evaluation)}
    metric_rows: list[dict] = []
    group_rows: list[dict] = []
    for method, prediction in predictions.items():
        for scope, indices in scopes.items():
            local = np.asarray([index_to_local[index] for index in indices], dtype=int)
            truth, estimate = y[indices], prediction[local]
            metric_rows.append(
                {
                    "plate": plate,
                    "repeat": repeat,
                    "budget": budget,
                    "labelled_n": len(labelled),
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
            local_frame = pd.DataFrame(
                {
                    "composition_cluster": target.loc[evaluation, "composition_cluster"].to_numpy(),
                    "squared_error": (y[evaluation] - prediction) ** 2,
                    "absolute_error": np.abs(y[evaluation] - prediction),
                }
            )
            grouped = local_frame.groupby("composition_cluster", as_index=False).agg(
                squared_error_sum=("squared_error", "sum"),
                absolute_error_sum=("absolute_error", "sum"),
                n=("squared_error", "size"),
            )
            for item in grouped.itertuples(index=False):
                group_rows.append(
                    {
                        "plate": plate,
                        "repeat": repeat,
                        "learner": learner,
                        "representation": representation,
                        "method": method,
                        "composition_cluster": item.composition_cluster,
                        "squared_error_sum": item.squared_error_sum,
                        "absolute_error_sum": item.absolute_error_sum,
                        "n": item.n,
                    }
                )

    specificity_rows: list[dict] = []
    if budget == 30 and learner == "extra_trees" and representation == "element_fraction":
        q4 = scopes["dynamic_ood_q4"]
        scope_map = {"dynamic_ood_q4": q4}
        base_prediction = predictions["target_only"]
        for real in REAL_SOURCES:
            for wrong in WRONG_SOURCES:
                coverage = matched[f"coverage_matched_{real}_vs_{wrong}"].astype(bool).to_numpy()
                coverage_indices = q4[coverage[q4]]
                if len(coverage_indices) >= 20:
                    scope_map[f"coverage_matched_q4|{real}|{wrong}"] = coverage_indices
                for role, column in [
                    ("real", f"size_matched_{real}_for_{wrong}_rank"),
                    ("wrong", f"size_matched_{wrong}_for_{real}_rank"),
                ]:
                    augmented = np.column_stack([x, matched[column].to_numpy(float)])
                    method = f"size_matched|{real}|{wrong}|{role}"
                    estimate = fit_predict(
                        "extra_trees", stable_seed(f"{seed}|{method}"), trees,
                        augmented, y, labelled, evaluation,
                    )
                    for scope, indices in scope_map.items():
                        local = np.asarray([index_to_local[index] for index in indices], dtype=int)
                        specificity_rows.append(
                            {
                                "plate": plate,
                                "repeat": repeat,
                                "method": method,
                                "scope": scope,
                                "n": len(indices),
                                "rmse": math.sqrt(mean_squared_error(y[indices], estimate[local])),
                            }
                        )
        for real in REAL_SOURCES:
            column = f"skill_matched_{real}_wrong_rank"
            augmented = np.column_stack([x, matched[column].to_numpy(float)])
            method = f"skill_matched_wrong|{real}"
            estimate = fit_predict(
                "extra_trees", stable_seed(f"{seed}|{method}"), trees, augmented, y, labelled, evaluation
            )
            local = np.asarray([index_to_local[index] for index in q4], dtype=int)
            specificity_rows.append(
                {
                    "plate": plate,
                    "repeat": repeat,
                    "method": method,
                    "scope": "dynamic_ood_q4",
                    "n": len(q4),
                    "rmse": math.sqrt(mean_squared_error(y[q4], estimate[local])),
                }
            )
    return metric_rows, group_rows, specificity_rows


def exploration(target: pd.DataFrame, policies: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for plate, local_target in target.groupby("plate"):
        component_max = local_target.groupby("composition_cluster")["target_fom"].max().sort_values(ascending=False)
        top_n = max(1, int(math.ceil(0.05 * len(component_max))))
        top_components = set(component_max.head(top_n).index)
        top_entity_n = max(1, int(math.ceil(0.05 * len(local_target))))
        top_entities = set(local_target.nlargest(top_entity_n, "target_fom")["entity_id"])
        for policy, order in policies[policies["plate"].astype(str).eq(str(plate))].groupby("policy"):
            recovered: set[str] = set()
            cumulative: list[int] = []
            entity_hits = 0
            first = 21
            for position, item in enumerate(order.sort_values("position").head(20).itertuples(index=False), start=1):
                if item.composition_cluster in top_components:
                    recovered.add(item.composition_cluster)
                    first = min(first, position)
                if item.entity_id in top_entities:
                    entity_hits += 1
                cumulative.append(len(recovered))
            rows.append(
                {
                    "plate": plate,
                    "policy": policy,
                    "top_components": top_n,
                    "distinct_component_auc20": sum(cumulative),
                    "component_recall20": len(recovered) / top_n,
                    "first_top_component": first,
                    "entity_recall20": entity_hits / top_entity_n,
                }
            )
    return pd.DataFrame(rows)


def card_tests(target: pd.DataFrame, cards: pd.DataFrame, permutations: int) -> pd.DataFrame:
    values = target.set_index("entity_id")["target_fom"]
    rng = np.random.default_rng(stable_seed("tri-card-tests"))
    rows: list[dict] = []
    for card in cards.itertuples(index=False):
        candidates = [value for value in str(card.candidate_entity_ids).split(";") if value in values.index]
        controls = [value for value in str(card.ood_matched_control_entity_ids).split(";") if value in values.index]
        n = min(len(candidates), len(controls))
        differences = values.loc[candidates[:n]].to_numpy(float) - values.loc[controls[:n]].to_numpy(float)
        null = np.empty(permutations)
        for index in range(permutations):
            null[index] = float(np.mean(differences * rng.choice([-1.0, 1.0], size=n)))
        rows.append(
            {
                "card_id": card.card_id,
                "pairs": n,
                "mean_paired_fom_difference": float(np.mean(differences)),
                "median_paired_fom_difference": float(np.median(differences)),
                "randomization_p_one_sided": float((1 + np.sum(null >= np.mean(differences))) / (permutations + 1)),
            }
        )
    result = pd.DataFrame(rows)
    order = np.argsort(result["randomization_p_one_sided"].to_numpy())
    adjusted = np.empty(len(result))
    running = 0.0
    for rank_index, index in enumerate(order):
        running = max(running, min(1.0, (len(result) - rank_index) * result.at[index, "randomization_p_one_sided"]))
        adjusted[index] = running
    result["holm_p"] = adjusted
    return result


def summary(metrics: pd.DataFrame, outcome_audit: dict, smoke: bool) -> dict:
    local = metrics[
        metrics["budget"].eq(30)
        & metrics["learner"].eq("extra_trees")
        & metrics["representation"].eq("element_fraction")
        & metrics["scope"].eq("dynamic_ood_q4")
    ]
    pivot = local.pivot(index=["plate", "repeat"], columns="method", values="rmse")
    baseline = pivot["target_only"]
    all_gain = (baseline - pivot["all_neighbor_frozen_stack"]) / baseline
    same_gain = (baseline - pivot["acid_same_reaction_frozen_stack"]) / baseline
    adjacent_gain = (baseline - pivot["adjacent_consensus_frozen_stack"]) / baseline
    controls = pivot[["wrong_source_frozen_stack", "shuffled_source_frozen_stack", "equal_capacity_random_feature_stack"]]
    best_control = ((baseline.to_numpy()[:, None] - controls.to_numpy()) / baseline.to_numpy()[:, None]).max(axis=1)
    rows = []
    for plate in sorted(pivot.index.get_level_values("plate").unique()):
        values = all_gain.xs(plate).to_numpy()
        rows.append({"plate": str(plate), "mean_all_neighbor_relative_gain": float(np.mean(values)), "positive_repeats": int(np.sum(values > 0))})
    return {
        "status": "smoke-nonclaim" if smoke else "formal-complete",
        "claim_guard": "One second-family retrospective benchmark; prospective discovery remains separate.",
        "outcome_audit": outcome_audit,
        "primary_cell": "n=30, ExtraTrees, element_fraction, dynamic OOD quartile 4",
        "all_neighbor_relative_gain_mean": float(all_gain.mean()),
        "all_neighbor_minus_same_reaction_mean": float((all_gain - same_gain).mean()),
        "adjacent_consensus_minus_same_reaction_mean": float((adjacent_gain - same_gain).mean()),
        "all_neighbor_minus_best_control_mean": float(np.mean(all_gain.to_numpy() - best_control)),
        "plate_effects": rows,
        "absolute_all_neighbor_r2_mean": float(
            local[local["method"].eq("all_neighbor_frozen_stack")]["r2"].mean()
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--jobs", type=int, default=max(1, min(16, os.cpu_count() or 1)))
    args = parser.parse_args()
    freeze = verify_preoutcome()
    metadata = pd.read_csv(METADATA, dtype={"plate": str})
    target, outcome_audit = join_fom(metadata)
    source = target[["entity_id"]].merge(pd.read_csv(PREDICTIONS, dtype={"plate": str}), on="entity_id", validate="one_to_one")
    matched = target[["entity_id"]].merge(pd.read_csv(MATCHED, dtype={"plate": str}), on="entity_id", validate="one_to_one")
    source.index = target.index
    matched.index = target.index
    y = target["target_fom"].to_numpy(float)
    x_by_rep = representations(target)
    acid = load_acid_source(set(target["material_key"]))
    acid_y = acid["value"].to_numpy(float)
    acid_x_by_rep = {
        "element_fraction": composition_features(acid["material_key"].tolist()).astype(np.float32)[:, : len(ELEMENT_INDEX)],
        "periodic_summary": periodic_summary(acid["material_key"].tolist()),
    }
    repeats = 1 if args.smoke else 100
    trees = 30 if args.smoke else 300
    specs = [
        (plate, repeat, budget, learner, representation)
        for plate in PLATE_ELEMENTS
        for repeat in range(repeats)
        for budget in BUDGETS
        for learner in LEARNERS
        for representation in REPRESENTATIONS
    ]
    outputs = Parallel(n_jobs=args.jobs, verbose=10)(
        delayed(task)(
            plate, repeat, budget, learner, representation, trees,
            target, x_by_rep[representation], x_by_rep["element_fraction"], y,
            source, matched, acid_x_by_rep[representation], acid_y,
        )
        for plate, repeat, budget, learner, representation in specs
    )
    metrics = pd.DataFrame([row for metric_rows, _, _ in outputs for row in metric_rows])
    group_errors = pd.DataFrame([row for _, group_rows, _ in outputs for row in group_rows])
    specificity = pd.DataFrame([row for _, _, specificity_rows in outputs for row in specificity_rows])
    policies = pd.read_csv(POLICY_ORDERS, dtype={"plate": str})
    policy_results = exploration(target, policies)
    card_results = card_tests(target, pd.read_csv(CARDS), 500 if args.smoke else 10000)
    result_summary = summary(metrics, outcome_audit, args.smoke)
    prefix = "tri_oer_smoke" if args.smoke else "tri_oer"
    metrics.to_csv(RESULTS / f"{prefix}_metrics.csv", index=False)
    group_errors.to_csv(RESULTS / f"{prefix}_group_errors.csv", index=False)
    specificity.to_csv(RESULTS / f"{prefix}_matched_specificity.csv", index=False)
    policy_results.to_csv(RESULTS / f"{prefix}_exploration.csv", index=False)
    card_results.to_csv(RESULTS / f"{prefix}_hypothesis_tests.csv", index=False)
    (RESULTS / f"{prefix}_summary.json").write_text(
        json.dumps(result_summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    complete = {
        "status": "smoke-nonclaim" if args.smoke else "complete",
        "design_sha256": sha256(DESIGN),
        "implementation_sha256": sha256(IMPLEMENTATION),
        "preoutcome_sha256": sha256(FREEZE),
        "preoutcome_artifact_hashes": freeze["artifact_hashes"],
        "plates": sorted(PLATE_ELEMENTS),
        "repeats_per_plate": repeats,
        "task_rows": len(specs),
        "metric_rows": len(metrics),
        "group_error_rows": len(group_errors),
        "specificity_rows": len(specificity),
        "exploration_rows": len(policy_results),
        "hypothesis_rows": len(card_results),
    }
    (RESULTS / f"{prefix}_COMPLETE.json").write_text(
        json.dumps(complete, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(result_summary, indent=2))


if __name__ == "__main__":
    main()
