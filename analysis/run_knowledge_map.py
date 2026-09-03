"""Build the designated multi-target knowledge-borrowing map.

The design is read from ``knowledge_map_design.json``.  It was written before
the first run of this script but was not externally preregistered.  Outcomes
are separated into a discovery partition and a disjoint internal-confirmation
partition.  A source model is never fitted on an entity assigned to any target
evaluation partition of the same representation kind.

This script does not call an internally admitted edge externally replicated.
That final gate requires a separate dataset or prospective population.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import rdFingerprintGenerator
from rdkit.Chem.Scaffolds import MurckoScaffold
from scipy import stats
from sklearn.base import clone
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold, cross_val_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from common import (
    RESULTS,
    composition_features,
    ensure_output_dirs,
    extra_trees,
    holm_adjust,
    key_to_dict,
    load_obelix,
    load_property,
    metrics,
    random_forest,
    ridge_model,
)

# ``fit_target_pair`` lives in run_confirmatory rather than common.  Keeping a
# local version avoids importing the full confirmatory runner and its figures.
from sklearn.base import clone as sklearn_clone


HERE = Path(__file__).resolve().parent
DESIGN_PATH = HERE / "knowledge_map_design.json"
RDLogger.DisableLog("rdApp.*")


@dataclass
class TaskData:
    task_id: str
    spec: dict[str, Any]
    frame: pd.DataFrame
    X: np.ndarray | None = None


def stable_offset(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16)


def chemical_system(key: str) -> str:
    return "-".join(sorted(key_to_dict(key)))


def molecular_scaffold(smiles: str) -> str:
    molecule = Chem.MolFromSmiles(smiles)
    if molecule is None:
        raise ValueError(f"Invalid canonical SMILES: {smiles}")
    scaffold = MurckoScaffold.MurckoScaffoldSmiles(mol=molecule, includeChirality=False)
    return scaffold or f"acyclic:{smiles}"


def apply_transform(values: pd.Series, transform: str) -> pd.Series:
    values = values.astype(float)
    if transform == "identity":
        return values
    if transform == "log10":
        if (values <= 0).any():
            raise ValueError("log10 task contains non-positive values after filtering")
        return np.log10(values)
    if transform == "log1p":
        if (values < 0).any():
            raise ValueError("log1p task contains negative values after filtering")
        return np.log1p(values)
    raise ValueError(f"Unknown transform: {transform}")


def load_task(task_id: str, spec: dict[str, Any]) -> TaskData:
    if task_id == "electrolyte_conductivity":
        frame = load_obelix().copy()
        # load_obelix already applies log10 and preserves official split/group.
        frame["family_group"] = frame["material_key"].map(chemical_system)
        return TaskData(task_id, spec, frame)

    raw = load_property(spec["dataset"], spec["property"])
    lower = float(spec["min"])
    upper = float(spec["max"])
    if spec["transform"] == "log10":
        raw = raw[(raw["value"] > max(0.0, lower)) & (raw["value"] <= upper)].copy()
    else:
        raw = raw[(raw["value"] >= lower) & (raw["value"] <= upper)].copy()
    frame = (
        raw.groupby("material_key", as_index=False)
        .agg(
            value=("value", "median"),
            n_raw=("value", "size"),
            material_raw=("material_raw", "first"),
        )
        .sort_values("material_key")
        .reset_index(drop=True)
    )
    frame["value"] = apply_transform(frame["value"], spec["transform"])
    if spec["kind"] == "formula":
        frame["group"] = frame["material_key"].map(chemical_system)
    elif spec["kind"] == "molecule":
        frame["group"] = frame["material_key"].map(molecular_scaffold)
    else:
        raise ValueError(f"Unsupported task kind: {spec['kind']}")
    return TaskData(task_id, spec, frame)


def build_feature_spaces(tasks: dict[str, TaskData]) -> None:
    formula_keys = sorted({
        key for task in tasks.values() if task.spec["kind"] == "formula"
        for key in task.frame["material_key"]
    })
    molecule_keys = sorted({
        key for task in tasks.values() if task.spec["kind"] == "molecule"
        for key in task.frame["material_key"]
    })
    formula_matrix = composition_features(formula_keys).astype(np.float32)
    formula_index = {key: index for index, key in enumerate(formula_keys)}

    generator = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=1024)
    molecule_matrix = np.zeros((len(molecule_keys), 1024), dtype=np.float32)
    for index, smiles in enumerate(molecule_keys):
        molecule = Chem.MolFromSmiles(smiles)
        if molecule is None:
            raise ValueError(f"Invalid canonical SMILES: {smiles}")
        fingerprint = generator.GetFingerprint(molecule)
        DataStructs.ConvertToNumpyArray(fingerprint, molecule_matrix[index])
    molecule_index = {key: index for index, key in enumerate(molecule_keys)}

    for task in tasks.values():
        keys = task.frame["material_key"].tolist()
        if task.spec["kind"] == "formula":
            task.X = formula_matrix[[formula_index[key] for key in keys]]
        else:
            task.X = molecule_matrix[[molecule_index[key] for key in keys]]


def balanced_group_partition(
    frame: pd.DataFrame,
    proportions: tuple[float, ...],
    seed: int,
    group_column: str = "group",
) -> list[np.ndarray]:
    """Assign intact groups to approximately row-balanced partitions."""
    counts = frame.groupby(group_column).size().to_dict()
    rng = np.random.default_rng(seed)
    groups = list(counts)
    rng.shuffle(groups)
    # Large groups are placed first; shuffled order resolves equal-size ties.
    groups.sort(key=lambda group: counts[group], reverse=True)
    targets = np.asarray(proportions, dtype=float) * len(frame)
    assigned: list[list[str]] = [[] for _ in proportions]
    totals = np.zeros(len(proportions), dtype=float)
    for group in groups:
        ratios = totals / np.maximum(targets, 1.0)
        destination = int(np.argmin(ratios))
        assigned[destination].append(group)
        totals[destination] += counts[group]
    partitions = [
        frame.index[frame[group_column].isin(group_list)].to_numpy(int)
        for group_list in assigned
    ]
    if any(len(partition) == 0 for partition in partitions):
        raise RuntimeError("Group partition produced an empty split")
    return partitions


def cap_group_partition(
    frame: pd.DataFrame, indices: np.ndarray, cap: int, seed: int
) -> tuple[np.ndarray, np.ndarray]:
    """Cap a test partition by whole groups; return selected and remainder."""
    if len(indices) <= cap:
        return np.asarray(indices, dtype=int), np.asarray([], dtype=int)
    subset = frame.loc[indices]
    counts = subset.groupby("group").size().to_dict()
    groups = list(counts)
    np.random.default_rng(seed).shuffle(groups)
    selected_groups = []
    total = 0
    for group in groups:
        if total >= cap:
            break
        selected_groups.append(group)
        total += counts[group]
    selected = subset.index[subset["group"].isin(selected_groups)].to_numpy(int)
    remainder = np.setdiff1d(indices, selected)
    return selected, remainder


def partition_targets(
    design: dict[str, Any], tasks: dict[str, TaskData]
) -> tuple[dict[str, dict[str, Any]], pd.DataFrame]:
    partitions: dict[str, dict[str, Any]] = {}
    rows: list[dict[str, Any]] = []
    base_seed = int(design["seed"])
    for target_id, target_spec in design["targets"].items():
        task = tasks[target_id]
        frame = task.frame
        seed = base_seed + stable_offset(target_id) % 1_000_000
        if target_spec.get("use_obelix_official_split"):
            development = frame.index[frame["split"] == "train"].to_numpy(int)
            official_test = frame.loc[frame["split"] == "test"].copy()
            discovery_local, confirmation_local = balanced_group_partition(
                official_test, (0.5, 0.5), seed, "group"
            )
            discovery = discovery_local
            confirmation = confirmation_local
        else:
            development, discovery, confirmation = balanced_group_partition(
                frame, (0.60, 0.20, 0.20), seed, "group"
            )
        cap = int(design["partition"].get("maximum_evaluation_entities_per_stage", 10**9))
        discovery, discovery_remainder = cap_group_partition(frame, discovery, cap, seed + 1)
        confirmation, confirmation_remainder = cap_group_partition(frame, confirmation, cap, seed + 2)
        development = np.sort(np.r_[development, discovery_remainder, confirmation_remainder])
        requested_budget = int(target_spec["budget"])
        budget = min(requested_budget, max(8, len(development) // 2))
        if len(development) < budget or min(len(discovery), len(confirmation)) < 8:
            raise RuntimeError(
                f"Insufficient partition for {target_id}: "
                f"dev={len(development)}, discovery={len(discovery)}, confirmation={len(confirmation)}"
            )
        partitions[target_id] = {
            "development": np.asarray(development, dtype=int),
            "discovery": np.asarray(discovery, dtype=int),
            "confirmation": np.asarray(confirmation, dtype=int),
            "budget": budget,
        }
        rows.append({
            "target": target_id,
            "label": task.spec["label"],
            "domain": task.spec["domain"],
            "kind": task.spec["kind"],
            "total_n": len(frame),
            "groups": int(frame["group"].nunique()),
            "development_n": len(development),
            "discovery_n": len(discovery),
            "confirmation_n": len(confirmation),
            "requested_budget": requested_budget,
            "analysis_budget": budget,
        })
    return partitions, pd.DataFrame(rows)


def source_model(task: TaskData, seed: int, *, cv: bool = False):
    if task.spec["kind"] == "formula":
        return ExtraTreesRegressor(
            n_estimators=100 if cv else 240,
            min_samples_leaf=2,
            max_features=0.7,
            random_state=seed,
            n_jobs=-1,
        )
    return make_pipeline(
        StandardScaler(with_mean=False),
        Ridge(alpha=10.0, solver="lsqr"),
    )


def fit_source_models(
    design: dict[str, Any],
    tasks: dict[str, TaskData],
    partitions: dict[str, dict[str, Any]],
) -> tuple[dict[tuple[str, str], Any], pd.DataFrame]:
    # Fit per directed edge.  Only the receiving target's evaluation entities
    # are excluded; excluding unrelated targets would unnecessarily destroy
    # legitimate source-task sample size without reducing leakage for this edge.
    models: dict[tuple[str, str], Any] = {}
    cache: dict[tuple[str, tuple[str, ...]], tuple[Any, dict[str, Any]]] = {}
    rows: list[dict[str, Any]] = []
    base_seed = int(design["seed"])
    for target_id, target_spec in design["targets"].items():
        target = tasks[target_id]
        split = partitions[target_id]
        excluded = set(target.frame.loc[
            np.r_[split["discovery"], split["confirmation"]], "material_key"
        ])
        for edge in target_spec["sources"]:
            source_id = edge["task"]
            task = tasks[source_id]
            present_excluded = tuple(sorted(set(task.frame["material_key"]) & excluded))
            cache_key = (source_id, present_excluded)
            if cache_key in cache:
                model, cached = cache[cache_key]
                training_n = cached["training_n"]
                source_groups = cached["source_groups"]
                cv_mean = cached["cv_mean"]
                cv_sd = cached["cv_sd"]
            else:
                keep = ~task.frame["material_key"].isin(present_excluded)
                training = task.frame.loc[keep].copy()
                indices = np.flatnonzero(keep.to_numpy())
                if len(training) < 25:
                    raise RuntimeError(
                        f"Edge {source_id}->{target_id} has only {len(training)} leakage-safe source entities"
                    )
                x = np.asarray(task.X)[indices]
                y = training["value"].to_numpy(float)
                groups = training["group"].astype(str).to_numpy()
                seed = base_seed + stable_offset(f"{source_id}:{len(present_excluded)}") % 1_000_000
                n_splits = min(3, len(np.unique(groups)))
                cv_scores = cross_val_score(
                    source_model(task, seed, cv=True), x, y,
                    cv=GroupKFold(n_splits=n_splits).split(x, y, groups),
                    scoring="r2", n_jobs=1,
                )
                model = source_model(task, seed).fit(x, y)
                training_n = len(training)
                source_groups = int(training["group"].nunique())
                cv_mean = float(np.mean(cv_scores))
                cv_sd = float(np.std(cv_scores, ddof=1))
                cache[cache_key] = (model, {
                    "training_n": training_n,
                    "source_groups": source_groups,
                    "cv_mean": cv_mean,
                    "cv_sd": cv_sd,
                })
            models[(target_id, source_id)] = model
            rows.append({
                "target": target_id,
                "source": source_id,
                "label": task.spec["label"],
                "domain": task.spec["domain"],
                "kind": task.spec["kind"],
                "total_n": len(task.frame),
                "training_n_after_target_evaluation_exclusion": training_n,
                "raw_evaluation_key_overlap": len(present_excluded),
                "post_exclusion_overlap": 0,
                "source_groups": source_groups,
                "group_cv_r2_mean": cv_mean,
                "group_cv_r2_sd": cv_sd,
            })
    return models, pd.DataFrame(rows)


def target_pair(model, x, y, feature, train_index, test_index):
    baseline = sklearn_clone(model).fit(x[train_index], y[train_index])
    augmented = sklearn_clone(model).fit(
        np.column_stack([x[train_index], feature[train_index]]), y[train_index]
    )
    return (
        baseline.predict(x[test_index]),
        augmented.predict(np.column_stack([x[test_index], feature[test_index]])),
    )


def target_ridge():
    return make_pipeline(StandardScaler(), Ridge(alpha=10.0, solver="lsqr"))


def training_samples(indices: np.ndarray, n: int, repeats: int, seed: int) -> list[np.ndarray]:
    samples = []
    for repeat in range(repeats):
        rng = np.random.default_rng(seed + repeat)
        samples.append(np.sort(rng.choice(indices, size=n, replace=False)))
    return samples


def cluster_relative_interval(
    predictions: pd.DataFrame, *, n_boot: int = 2000, seed: int
) -> tuple[float, float]:
    grouped = (
        predictions.assign(
            base_sse=lambda value: (value["y"] - value["baseline"]) ** 2,
            aug_sse=lambda value: (value["y"] - value["augmented"]) ** 2,
        )
        .groupby(["repeat", "test_group"], as_index=False)
        .agg(base_sse=("base_sse", "sum"), aug_sse=("aug_sse", "sum"), n=("y", "size"))
    )
    repeats = sorted(grouped["repeat"].unique())
    groups = sorted(grouped["test_group"].unique())
    shape = (len(repeats), len(groups))
    matrices = {}
    for column in ("base_sse", "aug_sse", "n"):
        matrices[column] = (
            grouped.pivot(index="repeat", columns="test_group", values=column)
            .reindex(index=repeats, columns=groups, fill_value=0)
            .fillna(0)
            .to_numpy(float)
        )
        if matrices[column].shape != shape:
            raise AssertionError("Unexpected cluster matrix shape")
    rng = np.random.default_rng(seed)
    repeat_weights = rng.multinomial(len(repeats), np.full(len(repeats), 1 / len(repeats)), size=n_boot)
    group_weights = rng.multinomial(len(groups), np.full(len(groups), 1 / len(groups)), size=n_boot)
    denominator = np.einsum("br,rg,bg->b", repeat_weights, matrices["n"], group_weights)
    base_sse = np.einsum("br,rg,bg->b", repeat_weights, matrices["base_sse"], group_weights)
    aug_sse = np.einsum("br,rg,bg->b", repeat_weights, matrices["aug_sse"], group_weights)
    base_rmse = np.sqrt(base_sse / denominator)
    aug_rmse = np.sqrt(aug_sse / denominator)
    relative = (base_rmse - aug_rmse) / base_rmse
    return tuple(np.percentile(relative[np.isfinite(relative)], [2.5, 97.5]))


def evaluate_edge(
    target: TaskData,
    source_feature: np.ndarray,
    samples: list[np.ndarray],
    test_index: np.ndarray,
    learner,
    learner_label: str,
    target_id: str,
    source_id: str,
    stage: str,
    seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    x = np.asarray(target.X)
    y = target.frame["value"].to_numpy(float)
    repeat_rows: list[dict[str, Any]] = []
    prediction_rows: list[dict[str, Any]] = []
    for repeat, train_index in enumerate(samples):
        baseline, augmented = target_pair(
            learner, x, y, source_feature, train_index, test_index
        )
        result = metrics(y[test_index], baseline, augmented)
        repeat_rows.append({
            "target": target_id,
            "source": source_id,
            "stage": stage,
            "learner": learner_label,
            "repeat": repeat,
            "train_n": len(train_index),
            "relative_rmse_improvement": result["delta_rmse"] / result["base_rmse"],
            **result,
        })
        for position, index in enumerate(test_index):
            prediction_rows.append({
                "target": target_id,
                "source": source_id,
                "stage": stage,
                "learner": learner_label,
                "repeat": repeat,
                "test_group": target.frame.at[index, "group"],
                "material_key": target.frame.at[index, "material_key"],
                "y": y[index],
                "baseline": baseline[position],
                "augmented": augmented[position],
            })
    repeats = pd.DataFrame(repeat_rows)
    predictions = pd.DataFrame(prediction_rows)
    ci_lo, ci_hi = cluster_relative_interval(predictions, seed=seed)
    summary = {
        "target": target_id,
        "source": source_id,
        "stage": stage,
        "learner": learner_label,
        "repeats": len(samples),
        "train_n": int(repeats["train_n"].median()),
        "test_n": len(test_index),
        "test_groups": int(target.frame.loc[test_index, "group"].nunique()),
        "base_r2_mean": float(repeats["base_r2"].mean()),
        "aug_r2_mean": float(repeats["aug_r2"].mean()),
        "delta_r2_mean": float(repeats["delta_r2"].mean()),
        "base_rmse_mean": float(repeats["base_rmse"].mean()),
        "aug_rmse_mean": float(repeats["aug_rmse"].mean()),
        "relative_rmse_improvement_mean": float(repeats["relative_rmse_improvement"].mean()),
        "relative_rmse_ci_lo": float(ci_lo),
        "relative_rmse_ci_hi": float(ci_hi),
        "fraction_repeats_positive": float((repeats["relative_rmse_improvement"] > 0).mean()),
        "mse_improvement_mean": float(repeats["mse_improvement"].mean()),
    }
    return repeats, predictions, summary


def baseline_learning_curve(
    target: TaskData,
    development: np.ndarray,
    confirmation: np.ndarray,
    budget: int,
    repeats: int,
    seed: int,
) -> pd.DataFrame:
    maximum = len(development)
    curve_maximum = min(maximum, max(4 * budget, 80))
    requested = sorted(set([8, 10, 15, 20, budget, 30, 40, 50, 60, 80, 100, 120, curve_maximum]))
    sizes = [value for value in requested if 8 <= value <= curve_maximum]
    x = np.asarray(target.X)
    y = target.frame["value"].to_numpy(float)
    rows = []
    permutations = [
        np.random.default_rng(seed + repeat).permutation(development)
        for repeat in range(repeats)
    ]
    for size in sizes:
        values = []
        for repeat, order in enumerate(permutations):
            train_index = np.sort(order[:size])
            model = clone(target_ridge()).fit(x[train_index], y[train_index])
            prediction = model.predict(x[confirmation])
            values.append(math.sqrt(mean_squared_error(y[confirmation], prediction)))
        rows.append({
            "target": target.task_id,
            "train_n": size,
            "repeats": repeats,
            "rmse_mean": float(np.mean(values)),
            "rmse_ci_lo": float(np.percentile(values, 2.5)),
            "rmse_ci_hi": float(np.percentile(values, 97.5)),
        })
    curve = pd.DataFrame(rows)
    curve["rmse_monotone"] = IsotonicRegression(increasing=False).fit_transform(
        curve["train_n"], curve["rmse_mean"]
    )
    return curve


def target_equivalent_samples(
    curve: pd.DataFrame, augmented_rmse: float, budget: int
) -> tuple[float, float, str]:
    curve = curve.sort_values("train_n")
    x = curve["train_n"].to_numpy(float)
    y = curve["rmse_monotone"].to_numpy(float)
    if augmented_rmse < y[-1]:
        equivalent = x[-1]
        status = "right-censored-at-largest-learning-curve-budget"
    elif augmented_rmse >= y[0]:
        equivalent = x[0]
        status = "no-savings"
    else:
        # y decreases with x; reverse for increasing interpolation coordinates.
        equivalent = float(np.interp(augmented_rmse, y[::-1], x[::-1]))
        status = "interpolated"
    saved = equivalent - budget
    fraction = saved / equivalent if equivalent > 0 else float("nan")
    return equivalent, fraction, status


def feature_permutation_test(
    target: TaskData,
    feature: np.ndarray,
    samples: list[np.ndarray],
    test_index: np.ndarray,
    observed: float,
    permutations: int,
    seed: int,
) -> tuple[float, pd.DataFrame]:
    x = np.asarray(target.X)
    y = target.frame["value"].to_numpy(float)
    baseline_mse = []
    for train_index in samples:
        model = clone(target_ridge()).fit(x[train_index], y[train_index])
        baseline_mse.append(mean_squared_error(y[test_index], model.predict(x[test_index])))
    observed_improvements = []
    for repeat, train_index in enumerate(samples):
        augmented = clone(target_ridge()).fit(
            np.column_stack([x[train_index], feature[train_index]]), y[train_index]
        )
        prediction = augmented.predict(np.column_stack([x[test_index], feature[test_index]]))
        observed_improvements.append(
            baseline_mse[repeat] - mean_squared_error(y[test_index], prediction)
        )
    observed = float(np.mean(observed_improvements))
    rng = np.random.default_rng(seed)
    rows = []
    for permutation in range(permutations):
        permuted = feature[rng.permutation(len(feature))]
        improvements = []
        for repeat, train_index in enumerate(samples):
            augmented = clone(target_ridge()).fit(
                np.column_stack([x[train_index], permuted[train_index]]), y[train_index]
            )
            prediction = augmented.predict(np.column_stack([x[test_index], permuted[test_index]]))
            improvements.append(baseline_mse[repeat] - mean_squared_error(y[test_index], prediction))
        rows.append({"permutation": permutation, "mean_mse_improvement": float(np.mean(improvements))})
    null = pd.DataFrame(rows)
    pvalue = (1 + int((null["mean_mse_improvement"] >= observed).sum())) / (len(null) + 1)
    return pvalue, null


def neighborhood_tests(edges: pd.DataFrame, seed: int) -> pd.DataFrame:
    primary = edges[~edges["relation"].str.contains("calibration")].copy()
    score = primary["neighborhood"].to_numpy(float)
    effect = primary["relative_rmse_improvement_mean"].to_numpy(float)
    spearman = stats.spearmanr(score, effect)

    comparable = []
    for target, group in primary.groupby("target"):
        records = group.to_dict("records")
        for left in range(len(records)):
            for right in range(left + 1, len(records)):
                score_difference = records[left]["neighborhood"] - records[right]["neighborhood"]
                if score_difference == 0:
                    continue
                effect_difference = (
                    records[left]["relative_rmse_improvement_mean"]
                    - records[right]["relative_rmse_improvement_mean"]
                )
                comparable.append((target, float(score_difference * effect_difference > 0)))
    concordance = float(np.mean([value for _, value in comparable]))

    targets = sorted(primary["target"].unique())
    rng = np.random.default_rng(seed)
    boot = []
    by_target = {target: [value for name, value in comparable if name == target] for target in targets}
    for _ in range(5000):
        selected = rng.choice(targets, size=len(targets), replace=True)
        values = [value for target in selected for value in by_target[target]]
        boot.append(np.mean(values))

    permutation_values = []
    for _ in range(9999):
        permuted = primary.copy()
        permuted["neighborhood"] = permuted.groupby("target")["neighborhood"].transform(
            lambda values: rng.permutation(values.to_numpy())
        )
        correct = []
        for _, group in permuted.groupby("target"):
            records = group.to_dict("records")
            for left in range(len(records)):
                for right in range(left + 1, len(records)):
                    sd = records[left]["neighborhood"] - records[right]["neighborhood"]
                    if sd == 0:
                        continue
                    ed = (
                        records[left]["relative_rmse_improvement_mean"]
                        - records[right]["relative_rmse_improvement_mean"]
                    )
                    correct.append(float(sd * ed > 0))
        permutation_values.append(np.mean(correct))
    concordance_p = (1 + np.sum(np.asarray(permutation_values) >= concordance)) / (len(permutation_values) + 1)

    # Cochran Q is an omnibus check that edge effects differ beyond their
    # bootstrap uncertainty.  It is not used to identify individual edges.
    se = (
        primary["relative_rmse_ci_hi"].to_numpy(float)
        - primary["relative_rmse_ci_lo"].to_numpy(float)
    ) / (2 * 1.96)
    weights = 1 / np.clip(se, 1e-6, None) ** 2
    fixed = np.sum(weights * effect) / np.sum(weights)
    q = float(np.sum(weights * (effect - fixed) ** 2))
    q_df = len(effect) - 1
    q_p = float(stats.chi2.sf(q, q_df))

    return pd.DataFrame([
        {"test": "spearman_neighborhood_vs_confirmation_effect", "estimate": spearman.statistic, "ci_lo": np.nan, "ci_hi": np.nan, "p_value": spearman.pvalue, "n": len(primary)},
        {"test": "within_target_pairwise_concordance", "estimate": concordance, "ci_lo": np.percentile(boot, 2.5), "ci_hi": np.percentile(boot, 97.5), "p_value": concordance_p, "n": len(comparable)},
        {"test": "cochran_q_edge_heterogeneity", "estimate": q, "ci_lo": np.nan, "ci_hi": np.nan, "p_value": q_p, "n": q_df},
    ])


def main() -> None:
    ensure_output_dirs()
    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    print("Loading designated tasks", flush=True)
    tasks = {task_id: load_task(task_id, spec) for task_id, spec in design["tasks"].items()}
    print("Building shared feature spaces", flush=True)
    build_feature_spaces(tasks)
    partitions, inventory = partition_targets(design, tasks)
    inventory.to_csv(RESULTS / "knowledge_map_task_inventory.csv", index=False)
    print("Fitting leakage-safe source models", flush=True)
    source_models, source_quality = fit_source_models(design, tasks, partitions)
    source_quality.to_csv(RESULTS / "knowledge_map_source_quality.csv", index=False)
    source_quality_lookup = source_quality.set_index(["target", "source"])["group_cv_r2_mean"].to_dict()

    discovery_repeats = int(design["inference"]["discovery_repeats"])
    confirmation_repeats = int(design["inference"]["confirmation_repeats"])
    base_seed = int(design["seed"])
    all_repeats = []
    all_predictions = []
    summaries = []
    feature_lookup: dict[tuple[str, str], np.ndarray] = {}
    sample_lookup: dict[tuple[str, str], list[np.ndarray]] = {}

    for target_id, target_spec in design["targets"].items():
        print(f"Primary discovery/confirmation: {target_id}", flush=True)
        target = tasks[target_id]
        split = partitions[target_id]
        for stage, repeats in (("discovery", discovery_repeats), ("confirmation", confirmation_repeats)):
            samples = training_samples(
                split["development"], split["budget"], repeats,
                base_seed + stable_offset(f"{target_id}:{stage}") % 1_000_000,
            )
            sample_lookup[(target_id, stage)] = samples
        for edge in target_spec["sources"]:
            source_id = edge["task"]
            feature = np.asarray(source_models[(target_id, source_id)].predict(np.asarray(target.X)), dtype=float)
            feature_lookup[(target_id, source_id)] = feature
            raw_overlap = len(
                set(tasks[source_id].frame["material_key"])
                & set(target.frame.loc[np.r_[split["discovery"], split["confirmation"]], "material_key"])
            )
            for stage in ("discovery", "confirmation"):
                repeats, predictions, summary = evaluate_edge(
                    target,
                    feature,
                    sample_lookup[(target_id, stage)],
                    split[stage],
                    target_ridge(),
                    "ridge-primary",
                    target_id,
                    source_id,
                    stage,
                    base_seed + stable_offset(f"interval:{target_id}:{source_id}:{stage}") % 1_000_000,
                )
                summary.update({
                    "target_label": target.spec["label"],
                    "source_label": tasks[source_id].spec["label"],
                    "target_domain": target.spec["domain"],
                    "source_domain": tasks[source_id].spec["domain"],
                    "neighborhood": int(edge["neighborhood"]),
                    "relation": edge["relation"],
                    "rationale": edge["rationale"],
                    "source_group_cv_r2_mean": source_quality_lookup[(target_id, source_id)],
                    "raw_source_target_evaluation_key_overlap": raw_overlap,
                    "source_model_evaluation_key_overlap_after_exclusion": 0,
                })
                all_repeats.append(repeats)
                all_predictions.append(predictions)
                summaries.append(summary)

    pd.DataFrame(summaries).to_csv(RESULTS / "knowledge_map_primary_checkpoint.csv", index=False)

    primary_summary = pd.DataFrame(summaries)
    discovery = primary_summary[primary_summary["stage"] == "discovery"].copy()
    discovery["selected_for_internal_confirmation"] = (
        (discovery["relative_rmse_improvement_mean"] >= design["inference"]["candidate_min_relative_rmse"])
        & (discovery["relative_rmse_ci_lo"] >= design["inference"]["candidate_ci_floor"])
    )
    candidate_keys = set(zip(
        discovery.loc[discovery["selected_for_internal_confirmation"], "target"],
        discovery.loc[discovery["selected_for_internal_confirmation"], "source"],
    ))

    confirmation = primary_summary[primary_summary["stage"] == "confirmation"].copy()
    confirmation["discovery_selected"] = [
        (target, source) in candidate_keys
        for target, source in zip(confirmation["target"], confirmation["source"])
    ]

    # Target-only learning curves convert prediction lift into target-equivalent
    # measurements saved.  Curves are estimated only on the confirmation test.
    curve_frames = []
    curve_repeats = int(design["inference"]["learning_curve_repeats"])
    for target_id in design["targets"]:
        print(f"Learning curve: {target_id}", flush=True)
        split = partitions[target_id]
        curve_frames.append(baseline_learning_curve(
            tasks[target_id], split["development"], split["confirmation"], split["budget"],
            curve_repeats,
            base_seed + stable_offset(f"curve:{target_id}") % 1_000_000,
        ))
    learning_curves = pd.concat(curve_frames, ignore_index=True)
    equivalents = []
    for _, row in confirmation.iterrows():
        curve = learning_curves[learning_curves["target"] == row["target"]]
        equivalent, fraction, status = target_equivalent_samples(
            curve, row["aug_rmse_mean"], int(row["train_n"])
        )
        equivalents.append((equivalent, fraction, status))
    confirmation["target_equivalent_n"] = [value[0] for value in equivalents]
    confirmation["target_sample_fraction_saved"] = [value[1] for value in equivalents]
    confirmation["target_equivalence_status"] = [value[2] for value in equivalents]

    # Feature-mapping permutation tests and nonlinear learner sensitivity are
    # performed only for discovery-selected edges; selection and confirmation
    # use disjoint target entities.
    null_frames = []
    sensitivity_frames = []
    raw_pvalues = []
    candidate_rows = []
    for row_index, row in confirmation[confirmation["discovery_selected"]].iterrows():
        target_id, source_id = row["target"], row["source"]
        print(f"Candidate placebo/sensitivity: {source_id} -> {target_id}", flush=True)
        split = partitions[target_id]
        permutation_repeats = int(design["inference"]["permutation_training_repeats"])
        placebo_samples = sample_lookup[(target_id, "confirmation")][:permutation_repeats]
        pvalue, null = feature_permutation_test(
            tasks[target_id], feature_lookup[(target_id, source_id)],
            placebo_samples, split["confirmation"],
            row["mse_improvement_mean"], int(design["inference"]["feature_permutations"]),
            base_seed + stable_offset(f"permutation:{target_id}:{source_id}") % 1_000_000,
        )
        null["target"] = target_id
        null["source"] = source_id
        null_frames.append(null)
        raw_pvalues.append(pvalue)
        candidate_rows.append(row_index)
        for learner_label, learner in (
            ("random-forest-sensitivity", random_forest(base_seed, 100)),
            ("extra-trees-sensitivity", extra_trees(base_seed, 100)),
        ):
            repeats, predictions, summary = evaluate_edge(
                tasks[target_id], feature_lookup[(target_id, source_id)],
                sample_lookup[(target_id, "confirmation")][
                    :int(design["inference"]["sensitivity_repeats"])
                ], split["confirmation"],
                learner, learner_label, target_id, source_id, "confirmation",
                base_seed + stable_offset(f"sensitivity:{target_id}:{source_id}:{learner_label}") % 1_000_000,
            )
            sensitivity_frames.append(summary)
    confirmation["permutation_p_raw"] = np.nan
    confirmation["permutation_p_holm"] = np.nan
    if candidate_rows:
        confirmation.loc[candidate_rows, "permutation_p_raw"] = raw_pvalues
        confirmation.loc[candidate_rows, "permutation_p_holm"] = holm_adjust(raw_pvalues)
    sensitivity = pd.DataFrame(sensitivity_frames)

    sensitivity_positive = {}
    for (target_id, source_id), group in sensitivity.groupby(["target", "source"]):
        sensitivity_positive[(target_id, source_id)] = int(
            (group["relative_rmse_improvement_mean"] > 0).sum()
        )
    confirmation["learners_positive_of_three"] = [
        int(row["relative_rmse_improvement_mean"] > 0)
        + sensitivity_positive.get((row["target"], row["source"]), 0)
        for _, row in confirmation.iterrows()
    ]

    statuses = []
    for _, row in confirmation.iterrows():
        if (
            row["discovery_selected"]
            and row["relative_rmse_improvement_mean"] >= design["inference"]["confirmed_min_relative_rmse"]
            and row["relative_rmse_ci_lo"] > 0
            and pd.notna(row["permutation_p_holm"])
            and row["permutation_p_holm"] < 0.05
            and row["target_sample_fraction_saved"] >= design["inference"]["confirmed_min_target_sample_fraction_saved"]
            and row["learners_positive_of_three"] >= 2
            and row["source_group_cv_r2_mean"] > 0
        ):
            status = "internally-confirmed-awaits-external-replication"
        elif row["relative_rmse_ci_lo"] >= -0.02 and row["relative_rmse_ci_hi"] <= 0.02:
            status = "practically-equivalent"
        elif row["relative_rmse_ci_hi"] < 0 and row["relative_rmse_improvement_mean"] <= -0.05:
            status = "harmful"
        elif row["discovery_selected"] and row["relative_rmse_improvement_mean"] > 0:
            status = "suggestive-not-confirmed"
        else:
            status = "unresolved"
        statuses.append(status)
    confirmation["edge_status"] = statuses

    discovery.to_csv(RESULTS / "knowledge_map_discovery.csv", index=False)
    confirmation.to_csv(RESULTS / "knowledge_map_edges.csv", index=False)
    source_quality.to_csv(RESULTS / "knowledge_map_source_quality.csv", index=False)
    inventory.to_csv(RESULTS / "knowledge_map_task_inventory.csv", index=False)
    learning_curves.to_csv(RESULTS / "knowledge_map_learning_curves.csv", index=False)
    sensitivity.to_csv(RESULTS / "knowledge_map_sensitivity.csv", index=False)
    pd.concat(all_repeats, ignore_index=True).to_csv(
        RESULTS / "knowledge_map_primary_repeats.csv", index=False
    )
    pd.concat(all_predictions, ignore_index=True).to_csv(
        RESULTS / "knowledge_map_primary_predictions.csv", index=False
    )
    if null_frames:
        pd.concat(null_frames, ignore_index=True).to_csv(
            RESULTS / "knowledge_map_permutation_null.csv", index=False
        )
    tests = neighborhood_tests(confirmation, base_seed)
    tests.to_csv(RESULTS / "knowledge_map_neighborhood_tests.csv", index=False)

    print("\nTask inventory")
    print(inventory.to_string(index=False))
    print("\nSource quality")
    print(source_quality[["target", "source", "training_n_after_target_evaluation_exclusion", "group_cv_r2_mean"]].to_string(index=False))
    print("\nEdge statuses")
    print(confirmation[[
        "target", "source", "neighborhood", "relative_rmse_improvement_mean",
        "relative_rmse_ci_lo", "relative_rmse_ci_hi", "target_sample_fraction_saved",
        "permutation_p_holm", "learners_positive_of_three", "edge_status",
    ]].sort_values(["edge_status", "relative_rmse_improvement_mean"], ascending=[True, False]).to_string(index=False))
    print("\nNeighborhood tests")
    print(tests.to_string(index=False))


if __name__ == "__main__":
    main()
