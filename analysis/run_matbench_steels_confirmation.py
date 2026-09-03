"""Independent Matbench-steels test of a mechanical knowledge-borrowing edge.

The design in ``matbench_steels_confirmation_design.json`` was written before
the first target-outcome modeling run.  The target is the experimental
Matbench steel yield-strength task, evaluated on its official five folds with
only 30 target labels available inside each official training fold.  Source
models are fitted to independent datasets after excluding every exact target
composition.  Same-row Matbench tensile strength and elongation are never used
as target-model inputs.
"""
from __future__ import annotations

import hashlib
import json
import urllib.request
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.base import clone
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score
from sklearn.model_selection import GroupKFold, cross_val_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from common import RESULTS, composition_features, ensure_output_dirs, extra_trees, load_property, random_forest
from run_external_confirmation import (
    evaluate,
    summarize_predictions,
    training_samples,
)
from run_knowledge_map import (
    TaskData,
    load_task,
    source_model,
    stable_offset,
    target_equivalent_samples,
)


HERE = Path(__file__).resolve().parent
DESIGN_PATH = HERE / "matbench_steels_confirmation_design.json"
MAP_DESIGN_PATH = HERE / "knowledge_map_design.json"


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load_official_validation(spec: dict[str, Any]) -> dict[str, Any]:
    """Read the pinned upstream split file and verify it byte-for-byte."""
    local = (
        Path.home()
        / ".collective_data_cache"
        / "matbench"
        / spec["path"]
    )
    if local.exists():
        raw = local.read_bytes()
    else:
        request = urllib.request.Request(
            spec["raw_url"], headers={"User-Agent": "collective-exp-data-index/0.3"}
        )
        with urllib.request.urlopen(request, timeout=180) as response:
            raw = response.read()
    observed = _sha256(raw)
    if observed != spec["sha256"]:
        raise RuntimeError(f"Matbench validation hash mismatch: {observed} != {spec['sha256']}")
    validation = json.loads(raw)
    metadata = validation["metadata"]
    if int(metadata["n_splits"]) != int(spec["folds"]):
        raise AssertionError("Unexpected number of Matbench folds")
    if int(metadata["random_state"]) != int(spec["random_state_reported_upstream"]):
        raise AssertionError("Unexpected upstream Matbench random state")
    if bool(metadata["shuffle"]) != bool(spec["shuffle_reported_upstream"]):
        raise AssertionError("Unexpected upstream Matbench shuffle setting")
    return validation["splits"][spec["task"]]


def load_target(design: dict[str, Any]) -> tuple[TaskData, np.ndarray]:
    spec = design["target_dataset"]
    raw = load_property("matbench-steels", spec["target"])
    if len(raw) != int(spec["n_rows_expected"]):
        raise AssertionError(f"Matbench target rows: {len(raw)} != {spec['n_rows_expected']}")
    if raw["source_row_id"].duplicated().any():
        raise AssertionError("Matbench source identifiers are not unique")
    if raw["material_key"].duplicated().any():
        raise AssertionError("Canonical Matbench steel compositions are not unique")
    frame = raw[["source_row_id", "material_raw", "material_key", "value"]].copy()
    frame = frame.sort_values("source_row_id").reset_index(drop=True)
    if (frame["value"] <= 0).any():
        raise AssertionError("Yield strength must be positive before log10 transform")
    frame["value"] = np.log10(frame["value"].to_numpy(float))
    frame["group"] = frame["material_key"]
    # Reuse the generic external evaluator; the constant is not a model input.
    frame["year"] = 0
    task_spec = {
        "dataset": "matbench-steels",
        "property": spec["target"],
        "kind": "formula",
        "transform": spec["target_transform"],
        "domain": "experimental steels",
        "label": "Matbench steel yield strength",
    }
    task = TaskData("matbench_steel_ys", task_spec, frame)
    source_x = composition_features(frame["material_key"].tolist()).astype(np.float32)
    # Removing columns that are constant across all 312 target compositions is
    # exactly information-preserving for the target learner and makes the
    # frozen 999-permutation test roughly two orders of magnitude cheaper.
    varying = np.ptp(source_x, axis=0) > 0
    task.X = source_x[:, varying]
    task.spec["target_feature_columns_kept"] = int(varying.sum())
    task.spec["source_feature_columns_kept"] = int(source_x.shape[1])
    return task, source_x


def official_splits(
    task: TaskData, validation: dict[str, Any]
) -> dict[str, dict[str, np.ndarray]]:
    id_to_index = {
        str(source_id): int(index)
        for index, source_id in enumerate(task.frame["source_row_id"])
    }
    all_ids = set(id_to_index)
    seen_tests: list[str] = []
    splits: dict[str, dict[str, np.ndarray]] = {}
    for fold_id in sorted(validation):
        fold = validation[fold_id]
        train_ids = [str(value) for value in fold["train"]]
        test_ids = [str(value) for value in fold["test"]]
        if set(train_ids) & set(test_ids):
            raise AssertionError(f"Official Matbench split overlap in {fold_id}")
        if set(train_ids) | set(test_ids) != all_ids:
            raise AssertionError(f"Official Matbench split coverage failure in {fold_id}")
        development = np.asarray([id_to_index[value] for value in train_ids], dtype=int)
        test = np.asarray([id_to_index[value] for value in test_ids], dtype=int)
        material_overlap = (
            set(task.frame.loc[development, "material_key"])
            & set(task.frame.loc[test, "material_key"])
        )
        if material_overlap:
            raise AssertionError(f"Canonical composition crosses {fold_id}: {len(material_overlap)}")
        splits[fold_id] = {
            "development": np.sort(development),
            "test": np.sort(test),
        }
        seen_tests.extend(test_ids)
    if len(seen_tests) != len(all_ids) or set(seen_tests) != all_ids:
        raise AssertionError("Official Matbench test folds do not partition the target rows")
    return splits


def load_source_models(
    design: dict[str, Any], map_design: dict[str, Any], target_keys: set[str]
) -> tuple[dict[str, TaskData], dict[str, Any], pd.DataFrame]:
    edge_specs = [design["primary_hypothesis"], *design["controls"]]
    source_ids = [edge["source"] for edge in edge_specs]
    tasks: dict[str, TaskData] = {}
    models: dict[str, Any] = {}
    rows: list[dict[str, Any]] = []
    for source_id in source_ids:
        task = load_task(source_id, map_design["tasks"][source_id])
        task.X = composition_features(task.frame["material_key"].tolist()).astype(np.float32)
        raw_overlap = set(task.frame["material_key"]) & target_keys
        keep = ~task.frame["material_key"].isin(raw_overlap)
        indices = np.flatnonzero(keep.to_numpy())
        training = task.frame.loc[keep].copy()
        x = np.asarray(task.X)[indices]
        y = training["value"].to_numpy(float)
        groups = training["group"].astype(str).to_numpy()
        if len(training) < 25 or len(np.unique(groups)) < 3:
            raise RuntimeError(f"Insufficient leakage-safe source data for {source_id}")
        seed = int(design["seed"]) + stable_offset(source_id) % 1_000_000
        cv = GroupKFold(n_splits=min(5, len(np.unique(groups))))
        scores = cross_val_score(
            source_model(task, seed, cv=True),
            x,
            y,
            groups=groups,
            cv=cv.split(x, y, groups),
            scoring="r2",
            n_jobs=1,
        )
        fitted = source_model(task, seed).fit(x, y)
        tasks[source_id] = task
        models[source_id] = fitted
        rows.append(
            {
                "source": source_id,
                "source_n_total": len(task.frame),
                "source_n_after_target_exclusion": len(training),
                "raw_target_key_overlap": len(raw_overlap),
                "post_exclusion_overlap": 0,
                "source_groups": int(training["group"].nunique()),
                "group_cv_r2_mean": float(np.mean(scores)),
                "group_cv_r2_sd": float(np.std(scores, ddof=1)),
                "group_cv_r2_min": float(np.min(scores)),
            }
        )
    return tasks, models, pd.DataFrame(rows)


def edge_specs(design: dict[str, Any]) -> list[dict[str, Any]]:
    return [design["primary_hypothesis"], *design["controls"]]


def target_ridge_exact():
    """The frozen alpha=10 learner with a deterministic exact solver."""
    return make_pipeline(StandardScaler(), Ridge(alpha=10.0, solver="cholesky"))


def baseline_learning_curve_exact(
    task: TaskData,
    splits: dict[str, dict[str, np.ndarray]],
    budgets: list[int],
    repeats: int,
    seed: int,
    *,
    anchor_budget: int | None = None,
    anchor_samples: dict[str, list[np.ndarray]] | None = None,
) -> pd.DataFrame:
    x = np.asarray(task.X)
    y = task.frame["value"].to_numpy(float)
    rows: list[dict[str, Any]] = []
    for budget in budgets:
        fold_sse = {repeat: [0.0, 0] for repeat in range(repeats)}
        for fold_id, split in splits.items():
            if budget == anchor_budget and anchor_samples is not None:
                fold_samples = anchor_samples[fold_id][:repeats]
            else:
                fold_samples = training_samples(
                    split["development"], budget, repeats, seed + stable_offset(fold_id)
                )
            for repeat, train in enumerate(fold_samples):
                prediction = clone(target_ridge_exact()).fit(x[train], y[train]).predict(
                    x[split["test"]]
                )
                fold_sse[repeat][0] += float(
                    np.sum((y[split["test"]] - prediction) ** 2)
                )
                fold_sse[repeat][1] += len(split["test"])
        rmses = [np.sqrt(sse / n) for sse, n in fold_sse.values()]
        rows.append(
            {
                "target": task.task_id,
                "train_n": budget,
                "rmse_mean": float(np.mean(rmses)),
            }
        )
    curve = pd.DataFrame(rows)
    curve["rmse_monotone"] = IsotonicRegression(increasing=False).fit_transform(
        curve["train_n"], curve["rmse_mean"]
    )
    rho = float(stats.spearmanr(curve["train_n"], curve["rmse_mean"]).statistic)
    valid = bool(rho < 0 and curve.iloc[-1]["rmse_mean"] < curve.iloc[0]["rmse_mean"])
    curve["learning_curve_spearman_rho"] = rho
    curve["valid_for_target_equivalence"] = valid
    return curve


def fold_summary(repeats: pd.DataFrame) -> dict[str, float]:
    output: dict[str, float] = {}
    for fold_id, group in repeats.groupby("fold"):
        output[f"effect_{fold_id}"] = float(group["relative_rmse_improvement"].mean())
        output[f"base_r2_{fold_id}"] = float(group["base_r2"].mean())
        output[f"aug_r2_{fold_id}"] = float(group["aug_r2"].mean())
    return output


def fast_primary_permutation_test(
    task: TaskData,
    feature: np.ndarray,
    samples: dict[str, list[np.ndarray]],
    splits: dict[str, dict[str, np.ndarray]],
    permutations: int,
    seed: int,
) -> tuple[float, pd.DataFrame]:
    """Vectorized equivalent of the frozen Ridge feature-mapping placebo.

    The target pipeline is StandardScaler followed by Ridge(alpha=10).  For a
    fixed train set, the scaled base design and its regularized inverse do not
    change across feature permutations.  A block-matrix update therefore
    evaluates all candidate feature mappings together without changing the
    estimand or reducing the requested number of permutations.
    """
    x = np.asarray(task.X, dtype=float)
    y = task.frame["value"].to_numpy(float)
    rng = np.random.default_rng(seed)
    candidates = np.empty((len(feature), permutations + 1), dtype=float)
    candidates[:, 0] = feature
    for permutation in range(permutations):
        candidates[:, permutation + 1] = feature[rng.permutation(len(feature))]

    improvements = np.zeros(permutations + 1, dtype=float)
    fit_count = 0
    checked_against_sklearn = False
    alpha = 10.0
    for fold_id, split in splits.items():
        test = split["test"]
        for train in samples[fold_id]:
            x_mean = x[train].mean(axis=0)
            x_scale = x[train].std(axis=0)
            x_scale[x_scale == 0] = 1.0
            z_train = (x[train] - x_mean) / x_scale
            z_test = (x[test] - x_mean) / x_scale
            y_mean = float(y[train].mean())
            y_centered = y[train] - y_mean
            regularized = z_train.T @ z_train + alpha * np.eye(z_train.shape[1])
            a_inv = np.linalg.solve(regularized, np.eye(regularized.shape[0]))
            base_rhs = z_train.T @ y_centered
            base_coef = a_inv @ base_rhs
            base_prediction = z_test @ base_coef + y_mean
            base_mse = float(np.mean((y[test] - base_prediction) ** 2))

            candidate_train = candidates[train]
            candidate_mean = candidate_train.mean(axis=0)
            candidate_scale = candidate_train.std(axis=0)
            candidate_scale[candidate_scale == 0] = 1.0
            candidate_train = (candidate_train - candidate_mean) / candidate_scale
            candidate_test = (candidates[test] - candidate_mean) / candidate_scale
            cross = z_train.T @ candidate_train
            a_inv_cross = a_inv @ cross
            denominator = (
                np.sum(candidate_train**2, axis=0)
                + alpha
                - np.sum(cross * a_inv_cross, axis=0)
            )
            numerator = candidate_train.T @ y_centered - cross.T @ base_coef
            candidate_coef = numerator / denominator
            base_block_coef = base_coef[:, None] - a_inv_cross * candidate_coef
            predictions = (
                z_test @ base_block_coef
                + candidate_test * candidate_coef
                + y_mean
            )
            candidate_mse = np.mean((y[test, None] - predictions) ** 2, axis=0)
            improvements += base_mse - candidate_mse
            fit_count += 1

            if not checked_against_sklearn:
                sklearn_base = clone(target_ridge_exact()).fit(x[train], y[train])
                sklearn_aug = clone(target_ridge_exact()).fit(
                    np.column_stack([x[train], feature[train]]), y[train]
                )
                sklearn_base_mse = float(
                    np.mean((y[test] - sklearn_base.predict(x[test])) ** 2)
                )
                sklearn_aug_mse = float(
                    np.mean(
                        (
                            y[test]
                            - sklearn_aug.predict(
                                np.column_stack([x[test], feature[test]])
                            )
                        )
                        ** 2
                    )
                )
                if not np.isclose(base_mse, sklearn_base_mse, rtol=5e-4, atol=1e-9):
                    raise AssertionError("Vectorized baseline Ridge does not match sklearn")
                if not np.isclose(candidate_mse[0], sklearn_aug_mse, rtol=5e-4, atol=1e-9):
                    raise AssertionError("Vectorized augmented Ridge does not match sklearn")
                checked_against_sklearn = True

    improvements /= fit_count
    observed = float(improvements[0])
    null_values = improvements[1:]
    p_value = (1 + int(np.sum(null_values >= observed))) / (permutations + 1)
    null = pd.DataFrame(
        {
            "permutation": np.arange(permutations, dtype=int),
            "mean_mse_improvement": null_values,
            "observed_mean_mse_improvement": observed,
        }
    )
    return p_value, null


def main() -> None:
    ensure_output_dirs()
    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    map_design = json.loads(MAP_DESIGN_PATH.read_text(encoding="utf-8"))
    inference = design["inference"]
    seed = int(design["seed"])

    target, target_source_x = load_target(design)
    validation = load_official_validation(design["official_split"])
    splits = official_splits(target, validation)
    target_keys = set(target.frame["material_key"])
    source_tasks, source_models, source_quality = load_source_models(
        design, map_design, target_keys
    )
    source_quality.to_csv(
        RESULTS / "matbench_steels_external_source_quality.csv", index=False
    )
    quality = source_quality.set_index("source")

    samples = {
        fold_id: training_samples(
            split["development"],
            int(inference["target_budget"]),
            int(inference["training_repeats"]),
            seed + stable_offset(f"matbench:{fold_id}") % 1_000_000,
        )
        for fold_id, split in splits.items()
    }

    summaries: list[dict[str, Any]] = []
    all_repeats: list[pd.DataFrame] = []
    all_predictions: list[pd.DataFrame] = []
    features: dict[str, np.ndarray] = {}
    for edge in edge_specs(design):
        source_id = edge["source"]
        feature = source_models[source_id].predict(target_source_x)
        features[source_id] = feature
        repeats, predictions = evaluate(
            target,
            feature,
            samples,
            splits,
            target_ridge_exact(),
            "ridge-primary",
            target.task_id,
            source_id,
        )
        summary = summarize_predictions(
            predictions,
            seed + stable_offset(f"matbench-bootstrap:{source_id}"),
            int(inference["bootstrap_replicates"]),
        )
        summary.update(fold_summary(repeats))
        summary.update(
            {
                "target": target.task_id,
                "source": source_id,
                "target_label": target.spec["label"],
                "source_label": source_tasks[source_id].spec["label"],
                "neighborhood": int(edge["neighborhood"]),
                "relation": edge["relation"],
                "rationale": edge["rationale"],
                "train_n": int(inference["target_budget"]),
                "test_n_total_per_repeat": int(sum(len(value["test"]) for value in splits.values())),
                "source_group_cv_r2_mean": float(quality.loc[source_id, "group_cv_r2_mean"]),
                "raw_source_target_key_overlap": int(quality.loc[source_id, "raw_target_key_overlap"]),
                "source_model_evaluation_key_overlap_after_exclusion": 0,
            }
        )
        summaries.append(summary)
        all_repeats.append(repeats)
        all_predictions.append(predictions)

    edges = pd.DataFrame(summaries)
    curve = baseline_learning_curve_exact(
        target,
        splits,
        inference["learning_curve_budgets"],
        int(inference["learning_curve_repeats"]),
        seed + stable_offset("matbench-learning-curve"),
        anchor_budget=int(inference["target_budget"]),
        anchor_samples=samples,
    )
    equivalents = [
        target_equivalent_samples(
            curve, float(row["aug_rmse_mean"]), int(inference["target_budget"])
        )
        for _, row in edges.iterrows()
    ]
    edges["target_equivalent_n"] = [value[0] for value in equivalents]
    edges["target_sample_fraction_saved"] = [value[1] for value in equivalents]
    edges["target_equivalence_status"] = [value[2] for value in equivalents]

    primary_source = design["primary_hypothesis"]["source"]
    permutation_samples = {
        fold_id: fold_samples[: int(inference["permutation_training_repeats"])]
        for fold_id, fold_samples in samples.items()
    }
    p_value, null = fast_primary_permutation_test(
        target,
        features[primary_source],
        permutation_samples,
        splits,
        int(inference["feature_permutations"]),
        seed + stable_offset("matbench-primary-permutation"),
    )
    null["target"] = target.task_id
    null["source"] = primary_source
    null.to_csv(
        RESULTS / "matbench_steels_external_permutation_null.csv", index=False
    )
    edges["primary_permutation_p"] = np.nan
    edges.loc[edges["source"] == primary_source, "primary_permutation_p"] = p_value

    sensitivity_rows: list[dict[str, Any]] = []
    sensitivity_samples = {
        fold_id: fold_samples[: int(inference["sensitivity_repeats"])]
        for fold_id, fold_samples in samples.items()
    }
    for learner_label, learner in (
        ("random-forest-sensitivity", random_forest(seed, 240)),
        ("extra-trees-sensitivity", extra_trees(seed, 240)),
    ):
        repeats, predictions = evaluate(
            target,
            features[primary_source],
            sensitivity_samples,
            splits,
            learner,
            learner_label,
            target.task_id,
            primary_source,
        )
        item = summarize_predictions(
            predictions,
            seed + stable_offset(f"matbench-{learner_label}"),
            int(inference["bootstrap_replicates"]),
        )
        item.update(fold_summary(repeats))
        item["learner"] = learner_label
        sensitivity_rows.append(item)
    sensitivity = pd.DataFrame(sensitivity_rows)
    primary_ridge_positive = bool(
        edges.loc[
            edges["source"] == primary_source,
            "relative_rmse_improvement_mean",
        ].iloc[0]
        > 0
    )
    positive_learners = int(primary_ridge_positive) + int(
        (sensitivity["relative_rmse_improvement_mean"] > 0).sum()
    )

    primary = edges.loc[edges["source"] == primary_source].iloc[0]
    fold_effects = [float(primary[f"effect_fold_{index}"]) for index in range(5)]
    gates = {
        "relative_rmse_at_least_5pct": bool(
            primary["relative_rmse_improvement_mean"]
            >= float(inference["external_min_relative_rmse"])
        ),
        "cluster_bootstrap_ci_above_zero": bool(primary["relative_rmse_ci_lo"] > 0),
        "positive_augmented_r2": bool(primary["pooled_aug_r2"] > 0),
        "positive_effect_in_all_five_official_folds": bool(all(value > 0 for value in fold_effects)),
        "target_sample_fraction_saved_at_least_30pct": bool(
            primary["target_sample_fraction_saved"]
            >= float(inference["external_min_target_sample_fraction_saved"])
        ),
        "at_least_two_of_three_learners_positive": bool(
            positive_learners >= int(inference["external_min_positive_learners_of_three"])
        ),
        "source_group_cv_r2_positive": bool(primary["source_group_cv_r2_mean"] > 0),
        "zero_post_exclusion_composition_overlap": bool(
            primary["source_model_evaluation_key_overlap_after_exclusion"] == 0
        ),
        "primary_permutation_p_below_0_05": bool(p_value < 0.05),
        "learning_curve_valid_for_equivalence": bool(
            curve["valid_for_target_equivalence"].iloc[0]
        ),
    }
    rescue_supported = bool(all(gates.values()))
    if rescue_supported:
        status = "externally-useful-rescue-gate-passed"
    elif (
        primary["relative_rmse_ci_lo"] > 0
        and primary["pooled_aug_r2"] > 0
        and all(value > 0 for value in fold_effects)
        and p_value < 0.05
    ):
        status = "directionally-replicated-with-positive-utility-below-full-rescue-gate"
    elif primary["relative_rmse_ci_hi"] < 0:
        status = "harmful"
    else:
        status = "unresolved"
    edges["edge_status"] = np.where(
        edges["source"] == primary_source,
        status,
        np.where(
            (edges["relative_rmse_ci_lo"] > 0)
            & (edges["relative_rmse_improvement_mean"] >= 0.05),
            "exploratory-positive",
            np.where(edges["relative_rmse_ci_hi"] < 0, "harmful", "unresolved"),
        ),
    )
    edges["primary_positive_learners_of_three"] = np.where(
        edges["source"] == primary_source, positive_learners, np.nan
    )

    all_repeat_frame = pd.concat(all_repeats, ignore_index=True)
    all_prediction_frame = pd.concat(all_predictions, ignore_index=True)
    edges.to_csv(RESULTS / "matbench_steels_external_edges.csv", index=False)
    curve.to_csv(RESULTS / "matbench_steels_external_learning_curve.csv", index=False)
    sensitivity.to_csv(RESULTS / "matbench_steels_external_sensitivity.csv", index=False)
    all_repeat_frame.to_csv(RESULTS / "matbench_steels_external_repeats.csv", index=False)
    all_prediction_frame.to_csv(RESULTS / "matbench_steels_external_predictions.csv", index=False)

    # Pooled R2 is recomputed here as a guard against a future summarizer change.
    primary_predictions = all_prediction_frame[
        all_prediction_frame["source"] == primary_source
    ]
    pooled_augmented_r2_check = r2_score(
        primary_predictions["y"], primary_predictions["augmented"]
    )
    if not np.isclose(pooled_augmented_r2_check, primary["pooled_aug_r2"]):
        raise AssertionError("Pooled augmented R2 summary mismatch")

    summary = {
        "analysis_status": design["status"],
        "target": target.task_id,
        "target_rows": len(target.frame),
        "official_folds": len(splits),
        "target_budget_per_fold": int(inference["target_budget"]),
        "primary_source": primary_source,
        "relative_rmse_improvement": float(primary["relative_rmse_improvement_mean"]),
        "relative_rmse_ci": [
            float(primary["relative_rmse_ci_lo"]),
            float(primary["relative_rmse_ci_hi"]),
        ],
        "pooled_base_r2": float(primary["pooled_base_r2"]),
        "pooled_augmented_r2": float(primary["pooled_aug_r2"]),
        "fold_effects": fold_effects,
        "target_equivalent_n": float(primary["target_equivalent_n"]),
        "target_sample_fraction_saved": float(primary["target_sample_fraction_saved"]),
        "primary_permutation_p": float(p_value),
        "positive_learners_of_three": int(positive_learners),
        "source_group_cv_r2_mean": float(primary["source_group_cv_r2_mean"]),
        "raw_source_target_composition_overlap": int(primary["raw_source_target_key_overlap"]),
        "post_exclusion_overlap": 0,
        "same_row_matbench_tensile_strength_used_as_input": False,
        "gates": gates,
        "rescue_claim_supported": rescue_supported,
        "decision": status,
    }
    (RESULTS / "matbench_steels_external_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )

    print("\nMatbench steels external edges")
    print(
        edges[
            [
                "source",
                "neighborhood",
                "relative_rmse_improvement_mean",
                "relative_rmse_ci_lo",
                "relative_rmse_ci_hi",
                "pooled_base_r2",
                "pooled_aug_r2",
                "target_sample_fraction_saved",
                "primary_permutation_p",
                "edge_status",
            ]
        ].to_string(index=False)
    )
    print("\nPrimary gate audit")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
