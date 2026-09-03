"""Independent, rolling-time confirmation of the alloy knowledge-borrowing edge.

The protocol is frozen in ``external_confirmation_design.json``.  BIRDSHOT is
an experimental campaign independent of the Borg source data.  Earlier
campaign years provide at most 30 target measurements and the next year is a
fixed, canonical-composition-disjoint test population.
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.base import clone
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold, cross_val_score

from common import (
    RESULTS,
    composition_features,
    ensure_output_dirs,
    extra_trees,
    load_property,
    metrics,
    random_forest,
)
from run_knowledge_map import (
    TaskData,
    apply_transform,
    chemical_system,
    load_task,
    source_model,
    stable_offset,
    target_equivalent_samples,
    target_ridge,
)

HERE = Path(__file__).resolve().parent
DESIGN_PATH = HERE / "external_confirmation_design.json"
MAP_DESIGN_PATH = HERE / "knowledge_map_design.json"


def load_birdshot_target(task_id: str, spec: dict[str, Any]) -> TaskData:
    raw = load_property("birdshot-high-entropy-alloy-campaign", spec["property"])
    parsed = raw["conditions_json"].map(json.loads)
    raw["year"] = parsed.map(lambda item: int(float(item["campaign_year"])))
    process_keys = [
        "cold_work_percent_reduction",
        "holding_time_h",
        "grain_size_um",
    ]
    for key in process_keys:
        raw[key] = parsed.map(lambda item, name=key: item.get(name, np.nan))
    raw = raw[raw["value"] > 0].copy()
    frame = (
        raw.groupby(["year", "material_key"], as_index=False)
        .agg(
            value=("value", "median"),
            n_raw=("value", "size"),
            material_raw=("material_raw", "first"),
            cold_work_percent_reduction=("cold_work_percent_reduction", "median"),
            holding_time_h=("holding_time_h", "median"),
            grain_size_um=("grain_size_um", "median"),
        )
        .sort_values(["year", "material_key"])
        .reset_index(drop=True)
    )
    frame["value"] = apply_transform(frame["value"], spec["transform"])
    frame["group"] = frame["material_key"]
    task_spec = {
        "dataset": "birdshot-high-entropy-alloy-campaign",
        "property": spec["property"],
        "kind": "formula",
        "transform": spec["transform"],
        "domain": "multi-principal-element alloy",
        "label": spec["label"],
    }
    task = TaskData(task_id, task_spec, frame)
    task.X = composition_features(frame["material_key"].tolist()).astype(np.float32)
    return task


def load_sources(design: dict[str, Any], map_design: dict[str, Any], all_target_keys: set[str]):
    source_ids = sorted({edge["task"] for target in design["targets"].values() for edge in target["sources"]})
    tasks: dict[str, TaskData] = {}
    models: dict[str, Any] = {}
    rows = []
    for source_id in source_ids:
        task = load_task(source_id, map_design["tasks"][source_id])
        task.X = composition_features(task.frame["material_key"].tolist()).astype(np.float32)
        overlap = set(task.frame["material_key"]) & all_target_keys
        keep = ~task.frame["material_key"].isin(overlap)
        indices = np.flatnonzero(keep.to_numpy())
        training = task.frame.loc[keep].copy()
        x = np.asarray(task.X)[indices]
        y = training["value"].to_numpy(float)
        groups = training["group"].astype(str).to_numpy()
        seed = int(design["seed"]) + stable_offset(source_id) % 1_000_000
        cv = GroupKFold(n_splits=min(3, len(np.unique(groups))))
        scores = cross_val_score(
            source_model(task, seed, cv=True), x, y,
            cv=cv.split(x, y, groups), scoring="r2", n_jobs=1,
        )
        model = source_model(task, seed).fit(x, y)
        tasks[source_id] = task
        models[source_id] = model
        rows.append({
            "source": source_id,
            "source_n_total": len(task.frame),
            "source_n_after_birdshot_exclusion": len(training),
            "raw_birdshot_key_overlap": len(overlap),
            "post_exclusion_overlap": 0,
            "source_groups": int(training["group"].nunique()),
            "group_cv_r2_mean": float(np.mean(scores)),
            "group_cv_r2_sd": float(np.std(scores, ddof=1)),
        })
    return tasks, models, pd.DataFrame(rows)


def rolling_splits(task: TaskData, design: dict[str, Any]) -> dict[str, dict[str, np.ndarray]]:
    splits = {}
    for fold in design["split"]["folds"]:
        development = task.frame.index[task.frame["year"].isin(fold["development_years"])].to_numpy(int)
        test = task.frame.index[task.frame["year"] == fold["test_year"]].to_numpy(int)
        overlap = set(task.frame.loc[development, "material_key"]) & set(task.frame.loc[test, "material_key"])
        if len(overlap) != int(design["split"]["canonical_material_overlap_allowed"]):
            raise AssertionError(f"{task.task_id}/{fold['id']} canonical overlap: {len(overlap)}")
        splits[fold["id"]] = {"development": development, "test": test}
    return splits


def training_samples(indices: np.ndarray, n: int, repeats: int, seed: int) -> list[np.ndarray]:
    if len(indices) < n:
        raise RuntimeError(f"Only {len(indices)} development entities for budget {n}")
    return [
        np.sort(np.random.default_rng(seed + repeat).choice(indices, size=n, replace=False))
        for repeat in range(repeats)
    ]


def evaluate(
    task: TaskData,
    feature: np.ndarray,
    split_samples: dict[str, list[np.ndarray]],
    splits: dict[str, dict[str, np.ndarray]],
    learner,
    learner_label: str,
    target_id: str,
    source_id: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    x = np.asarray(task.X)
    y = task.frame["value"].to_numpy(float)
    repeat_rows = []
    prediction_rows = []
    for fold_id, split in splits.items():
        test = split["test"]
        for repeat, train in enumerate(split_samples[fold_id]):
            baseline = clone(learner).fit(x[train], y[train])
            augmented = clone(learner).fit(
                np.column_stack([x[train], feature[train]]), y[train]
            )
            base_prediction = baseline.predict(x[test])
            aug_prediction = augmented.predict(np.column_stack([x[test], feature[test]]))
            result = metrics(y[test], base_prediction, aug_prediction)
            repeat_rows.append({
                "target": target_id,
                "source": source_id,
                "learner": learner_label,
                "fold": fold_id,
                "repeat": repeat,
                "train_n": len(train),
                "test_n": len(test),
                "relative_rmse_improvement": result["delta_rmse"] / result["base_rmse"],
                **result,
            })
            for position, index in enumerate(test):
                prediction_rows.append({
                    "target": target_id,
                    "source": source_id,
                    "learner": learner_label,
                    "fold": fold_id,
                    "repeat": repeat,
                    "material_key": task.frame.loc[index, "material_key"],
                    "year": int(task.frame.loc[index, "year"]),
                    "y": y[index],
                    "baseline": base_prediction[position],
                    "augmented": aug_prediction[position],
                })
    return pd.DataFrame(repeat_rows), pd.DataFrame(prediction_rows)


def summarize_predictions(predictions: pd.DataFrame, seed: int, n_boot: int) -> dict[str, float]:
    values = predictions.copy()
    values["base_sse"] = (values["y"] - values["baseline"]) ** 2
    values["aug_sse"] = (values["y"] - values["augmented"]) ** 2
    repeats = sorted(values["repeat"].unique())
    fold_matrices = {}
    for fold, group in values.groupby("fold"):
        keys = sorted(group["material_key"].unique())
        matrices = {}
        for column in ("base_sse", "aug_sse"):
            matrices[column] = (
                group.pivot(index="repeat", columns="material_key", values=column)
                .reindex(index=repeats, columns=keys)
                .to_numpy(float)
            )
        fold_matrices[fold] = matrices

    per_repeat = values.groupby(["repeat", "fold"], as_index=False).agg(
        base_sse=("base_sse", "sum"), aug_sse=("aug_sse", "sum"), n=("y", "size")
    ).groupby("repeat", as_index=False).sum(numeric_only=True)
    base_rmse = np.sqrt(per_repeat["base_sse"] / per_repeat["n"])
    aug_rmse = np.sqrt(per_repeat["aug_sse"] / per_repeat["n"])
    relative = (base_rmse - aug_rmse) / base_rmse

    rng = np.random.default_rng(seed)
    boot = np.empty(n_boot, dtype=float)
    for iteration in range(n_boot):
        repeat_index = rng.integers(0, len(repeats), size=len(repeats))
        base_total = aug_total = 0.0
        n_total = 0
        for matrices in fold_matrices.values():
            n_entities = matrices["base_sse"].shape[1]
            entity_index = rng.integers(0, n_entities, size=n_entities)
            base_total += matrices["base_sse"][repeat_index][:, entity_index].sum()
            aug_total += matrices["aug_sse"][repeat_index][:, entity_index].sum()
            n_total += len(repeat_index) * len(entity_index)
        base = np.sqrt(base_total / n_total)
        aug = np.sqrt(aug_total / n_total)
        boot[iteration] = (base - aug) / base

    output = {
        "base_rmse_mean": float(base_rmse.mean()),
        "aug_rmse_mean": float(aug_rmse.mean()),
        "relative_rmse_improvement_mean": float(relative.mean()),
        "relative_rmse_ci_lo": float(np.percentile(boot, 2.5)),
        "relative_rmse_ci_hi": float(np.percentile(boot, 97.5)),
        "pooled_base_r2": float(r2_score(values["y"], values["baseline"])),
        "pooled_aug_r2": float(r2_score(values["y"], values["augmented"])),
    }
    for fold, group in values.groupby("fold"):
        by_repeat = group.groupby("repeat").agg(base_sse=("base_sse", "sum"), aug_sse=("aug_sse", "sum"), n=("y", "size"))
        fold_base = np.sqrt(by_repeat["base_sse"] / by_repeat["n"])
        fold_aug = np.sqrt(by_repeat["aug_sse"] / by_repeat["n"])
        output[f"effect_{fold}"] = float(((fold_base - fold_aug) / fold_base).mean())
    return output


def baseline_learning_curve(
    task: TaskData,
    splits: dict[str, dict[str, np.ndarray]],
    budgets: list[int],
    repeats: int,
    seed: int,
) -> pd.DataFrame:
    x = np.asarray(task.X)
    y = task.frame["value"].to_numpy(float)
    rows = []
    for budget in budgets:
        fold_sse = {repeat: [0.0, 0] for repeat in range(repeats)}
        for fold_id, split in splits.items():
            samples = training_samples(split["development"], budget, repeats, seed + stable_offset(fold_id))
            for repeat, train in enumerate(samples):
                prediction = clone(target_ridge()).fit(x[train], y[train]).predict(x[split["test"]])
                fold_sse[repeat][0] += float(np.sum((y[split["test"]] - prediction) ** 2))
                fold_sse[repeat][1] += len(split["test"])
        rmses = [np.sqrt(sse / n) for sse, n in fold_sse.values()]
        rows.append({"target": task.task_id, "train_n": budget, "rmse_mean": float(np.mean(rmses))})
    curve = pd.DataFrame(rows)
    curve["rmse_monotone"] = IsotonicRegression(increasing=False).fit_transform(curve["train_n"], curve["rmse_mean"])
    rho = float(stats.spearmanr(curve["train_n"], curve["rmse_mean"]).statistic)
    valid = bool(rho < 0 and curve.iloc[-1]["rmse_mean"] < curve.iloc[0]["rmse_mean"])
    curve["learning_curve_spearman_rho"] = rho
    curve["valid_for_target_equivalence"] = valid
    return curve


def primary_permutation_test(
    task: TaskData,
    feature: np.ndarray,
    samples: dict[str, list[np.ndarray]],
    splits: dict[str, dict[str, np.ndarray]],
    permutations: int,
    seed: int,
) -> tuple[float, pd.DataFrame]:
    x = np.asarray(task.X)
    y = task.frame["value"].to_numpy(float)
    baseline_mse = {}
    for fold_id, split in splits.items():
        baseline_mse[fold_id] = []
        for train in samples[fold_id]:
            prediction = clone(target_ridge()).fit(x[train], y[train]).predict(x[split["test"]])
            baseline_mse[fold_id].append(mean_squared_error(y[split["test"]], prediction))

    def mean_improvement(candidate: np.ndarray) -> float:
        values = []
        for fold_id, split in splits.items():
            for repeat, train in enumerate(samples[fold_id]):
                model = clone(target_ridge()).fit(np.column_stack([x[train], candidate[train]]), y[train])
                prediction = model.predict(np.column_stack([x[split["test"]], candidate[split["test"]]]))
                values.append(baseline_mse[fold_id][repeat] - mean_squared_error(y[split["test"]], prediction))
        return float(np.mean(values))

    observed = mean_improvement(feature)
    rng = np.random.default_rng(seed)
    rows = []
    years = task.frame["year"].to_numpy(int)
    for permutation in range(permutations):
        permuted = feature.copy()
        for year in np.unique(years):
            indices = np.flatnonzero(years == year)
            permuted[indices] = feature[rng.permutation(indices)]
        rows.append({"permutation": permutation, "mean_mse_improvement": mean_improvement(permuted)})
    null = pd.DataFrame(rows)
    pvalue = (1 + int((null["mean_mse_improvement"] >= observed).sum())) / (len(null) + 1)
    null["observed_mean_mse_improvement"] = observed
    return pvalue, null


def neighborhood_tests(edges: pd.DataFrame) -> pd.DataFrame:
    spearman = stats.spearmanr(edges["neighborhood"], edges["relative_rmse_improvement_mean"])
    comparable = []
    for _, group in edges.groupby("target"):
        records = group.to_dict("records")
        for left in range(len(records)):
            for right in range(left + 1, len(records)):
                score_delta = records[left]["neighborhood"] - records[right]["neighborhood"]
                if score_delta:
                    effect_delta = records[left]["relative_rmse_improvement_mean"] - records[right]["relative_rmse_improvement_mean"]
                    comparable.append(float(score_delta * effect_delta > 0))
    return pd.DataFrame([
        {"test": "spearman_neighborhood_vs_external_effect", "estimate": spearman.statistic, "p_value": spearman.pvalue, "n": len(edges)},
        {"test": "within_target_pairwise_concordance", "estimate": float(np.mean(comparable)), "p_value": np.nan, "n": len(comparable)},
    ])


def main() -> None:
    warnings.filterwarnings("ignore", message=".*sklearn.utils.parallel.delayed.*")
    ensure_output_dirs()
    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    map_design = json.loads(MAP_DESIGN_PATH.read_text(encoding="utf-8"))
    base_seed = int(design["seed"])
    inference = design["inference"]

    targets = {task_id: load_birdshot_target(task_id, spec) for task_id, spec in design["targets"].items()}
    all_target_keys = set().union(*(set(task.frame["material_key"]) for task in targets.values()))
    source_tasks, source_models, source_quality = load_sources(design, map_design, all_target_keys)
    source_quality.to_csv(RESULTS / "external_confirmation_source_quality.csv", index=False)
    quality_lookup = source_quality.set_index("source")["group_cv_r2_mean"].to_dict()

    all_repeats = []
    all_predictions = []
    summaries = []
    sample_lookup = {}
    split_lookup = {}
    feature_lookup = {}
    for target_id, target_spec in design["targets"].items():
        print(f"External rolling evaluation: {target_id}", flush=True)
        target = targets[target_id]
        splits = rolling_splits(target, design)
        split_lookup[target_id] = splits
        samples = {
            fold_id: training_samples(
                split["development"], int(inference["target_budget"]), int(inference["training_repeats"]),
                base_seed + stable_offset(f"{target_id}:{fold_id}") % 1_000_000,
            )
            for fold_id, split in splits.items()
        }
        sample_lookup[target_id] = samples
        for edge in target_spec["sources"]:
            source_id = edge["task"]
            feature = source_models[source_id].predict(np.asarray(target.X))
            feature_lookup[(target_id, source_id)] = feature
            repeats, predictions = evaluate(
                target, feature, samples, splits, target_ridge(), "ridge-primary", target_id, source_id
            )
            summary = summarize_predictions(
                predictions, base_seed + stable_offset(f"bootstrap:{target_id}:{source_id}"),
                int(inference["bootstrap_replicates"]),
            )
            summary.update({
                "target": target_id,
                "source": source_id,
                "target_label": target_spec["label"],
                "source_label": source_tasks[source_id].spec["label"],
                "neighborhood": edge["neighborhood"],
                "relation": edge["relation"],
                "rationale": edge["rationale"],
                "train_n": int(inference["target_budget"]),
                "test_n_year2": len(splits["year1_to_year2"]["test"]),
                "test_n_year3": len(splits["years1_2_to_year3"]["test"]),
                "source_group_cv_r2_mean": quality_lookup[source_id],
                "raw_source_birdshot_key_overlap": int(source_quality.set_index("source").loc[source_id, "raw_birdshot_key_overlap"]),
                "source_model_evaluation_key_overlap_after_exclusion": 0,
            })
            summaries.append(summary)
            all_repeats.append(repeats)
            all_predictions.append(predictions)

    edges = pd.DataFrame(summaries)
    learning_curves = []
    for target_id, target in targets.items():
        learning_curves.append(baseline_learning_curve(
            target, split_lookup[target_id], inference["learning_curve_budgets"],
            int(inference["learning_curve_repeats"]), base_seed + stable_offset(f"curve:{target_id}"),
        ))
    curves = pd.concat(learning_curves, ignore_index=True)
    equivalents = []
    for _, row in edges.iterrows():
        curve = curves[curves["target"] == row["target"]]
        if bool(curve["valid_for_target_equivalence"].iloc[0]):
            equivalents.append(target_equivalent_samples(curve, row["aug_rmse_mean"], int(row["train_n"])))
        else:
            equivalents.append((np.nan, np.nan, "unavailable-nonmonotone-temporal-learning-curve"))
    edges["target_equivalent_n"] = [item[0] for item in equivalents]
    edges["target_sample_fraction_saved"] = [item[1] for item in equivalents]
    edges["target_equivalence_status"] = [item[2] for item in equivalents]

    primary = design["primary_hypothesis"]
    primary_key = (primary["target"], primary["source"])
    primary_samples = {
        fold: samples[: int(inference["permutation_training_repeats"])]
        for fold, samples in sample_lookup[primary["target"]].items()
    }
    print("Primary within-year feature permutation test", flush=True)
    pvalue, null = primary_permutation_test(
        targets[primary["target"]], feature_lookup[primary_key], primary_samples,
        split_lookup[primary["target"]], int(inference["feature_permutations"]),
        base_seed + stable_offset("primary-permutation"),
    )
    null["target"], null["source"] = primary_key
    null.to_csv(RESULTS / "external_confirmation_permutation_null.csv", index=False)
    edges["primary_permutation_p"] = np.nan
    edges.loc[(edges["target"] == primary_key[0]) & (edges["source"] == primary_key[1]), "primary_permutation_p"] = pvalue

    sensitivity_rows = []
    for learner_label, learner in (
        ("random-forest-sensitivity", random_forest(base_seed, 200)),
        ("extra-trees-sensitivity", extra_trees(base_seed, 200)),
    ):
        repeats, predictions = evaluate(
            targets[primary["target"]], feature_lookup[primary_key],
            {fold: samples[: int(inference["sensitivity_repeats"])] for fold, samples in sample_lookup[primary["target"]].items()},
            split_lookup[primary["target"]], learner, learner_label, primary["target"], primary["source"],
        )
        item = summarize_predictions(predictions, base_seed + stable_offset(learner_label), int(inference["bootstrap_replicates"]))
        item["learner"] = learner_label
        sensitivity_rows.append(item)
    sensitivity = pd.DataFrame(sensitivity_rows)
    sensitivity.to_csv(RESULTS / "external_confirmation_sensitivity.csv", index=False)
    positive_learners = 1 + int((sensitivity["relative_rmse_improvement_mean"] > 0).sum())

    edge_status = []
    for _, row in edges.iterrows():
        is_primary = (row["target"], row["source"]) == primary_key
        if is_primary and (
            row["relative_rmse_improvement_mean"] >= inference["external_min_relative_rmse"]
            and row["relative_rmse_ci_lo"] > 0
            and row["effect_year1_to_year2"] > 0
            and row["effect_years1_2_to_year3"] > 0
            and row["target_sample_fraction_saved"] >= inference["external_min_target_sample_fraction_saved"]
            and positive_learners >= inference["external_min_positive_learners_of_three"]
            and row["source_group_cv_r2_mean"] > 0
            and pvalue < 0.05
        ):
            status = "externally-confirmed"
        elif is_primary and (
            row["relative_rmse_ci_lo"] > 0
            and row["effect_year1_to_year2"] > 0
            and row["effect_years1_2_to_year3"] > 0
            and positive_learners >= inference["external_min_positive_learners_of_three"]
            and row["source_group_cv_r2_mean"] > 0
            and pvalue < 0.05
        ):
            status = "directionally-replicated-below-practical-gate"
        elif row["relative_rmse_ci_lo"] > 0 and row["relative_rmse_improvement_mean"] >= 0.05:
            status = "exploratory-positive"
        elif row["relative_rmse_ci_lo"] >= -0.02 and row["relative_rmse_ci_hi"] <= 0.02:
            status = "practically-equivalent"
        elif row["relative_rmse_ci_hi"] < 0:
            status = "harmful"
        else:
            status = "unresolved"
        edge_status.append(status)
    edges["edge_status"] = edge_status
    edges["primary_positive_learners_of_three"] = np.where(
        (edges["target"] == primary_key[0]) & (edges["source"] == primary_key[1]), positive_learners, np.nan
    )

    tests = neighborhood_tests(edges)
    edges.to_csv(RESULTS / "external_confirmation_edges.csv", index=False)
    curves.to_csv(RESULTS / "external_confirmation_learning_curves.csv", index=False)
    pd.concat(all_repeats, ignore_index=True).to_csv(RESULTS / "external_confirmation_repeats.csv", index=False)
    pd.concat(all_predictions, ignore_index=True).to_csv(RESULTS / "external_confirmation_predictions.csv", index=False)
    tests.to_csv(RESULTS / "external_confirmation_neighborhood_tests.csv", index=False)

    print("\nExternal edge summary")
    print(edges[[
        "target", "source", "neighborhood", "relative_rmse_improvement_mean",
        "relative_rmse_ci_lo", "relative_rmse_ci_hi", "effect_year1_to_year2",
        "effect_years1_2_to_year3", "target_sample_fraction_saved", "primary_permutation_p",
        "edge_status",
    ]].to_string(index=False))
    print("\nPrimary learner sensitivity")
    print(sensitivity[["learner", "relative_rmse_improvement_mean", "relative_rmse_ci_lo", "relative_rmse_ci_hi"]].to_string(index=False))
    print("\nNeighborhood tests")
    print(tests.to_string(index=False))


if __name__ == "__main__":
    main()
