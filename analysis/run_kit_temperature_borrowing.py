"""Leakage-safe test of local temperature-neighbor knowledge borrowing.

The frozen design is ``kit_temperature_borrowing_design.json``.  The
independent statistical unit is a unique electrolyte formulation, not an EIS
run.  Replicate runs are aggregated before splitting.  In every outer fold,
the source-temperature model excludes the held-out formulations; predictions
used as features for target-training formulations are themselves cross-fitted.

This is a within-campaign local-neighbor test.  It is deliberately not labeled
an independent-dataset or universal cross-domain replication.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from scipy import stats
from sklearn.base import clone
from sklearn.ensemble import ExtraTreesRegressor, RandomForestRegressor
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler

from common import RESULTS, ensure_output_dirs
from run_external_confirmation import summarize_predictions, training_samples
from run_knowledge_map import stable_offset, target_equivalent_samples


HERE = Path(__file__).resolve().parent
DESIGN_PATH = HERE / "kit_temperature_borrowing_design.json"
COMPONENTS = ["PC", "EC", "EMC", "LiPF_6"]


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load_raw(design: dict[str, Any]) -> pd.DataFrame:
    spec = design["dataset"]
    cache = (
        Path.home()
        / ".collective_data_cache"
        / "kit-electrolyte"
        / spec["file_name"]
    )
    if cache.exists():
        raw = cache.read_bytes()
    else:
        request = urllib.request.Request(
            spec["raw_url"],
            headers={"User-Agent": "collective-exp-data-index/0.3"},
        )
        with urllib.request.urlopen(request, timeout=300) as response:
            raw = response.read()
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_bytes(raw)
    observed = sha256(raw)
    if observed != spec["raw_sha256"]:
        raise RuntimeError(f"KIT raw hash mismatch: {observed} != {spec['raw_sha256']}")
    frame = pd.read_csv(cache, sep=";", skiprows=[1, 2])
    if len(frame) != int(spec["raw_rows_expected"]):
        raise AssertionError(f"KIT rows: {len(frame)} != {spec['raw_rows_expected']}")
    for column in [*COMPONENTS, "temperature", "EIS_conductivity"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    if frame[[*COMPONENTS, "temperature", "EIS_conductivity"]].isna().any().any():
        raise AssertionError("Missing required KIT formulation, temperature, or conductivity value")
    if (frame["EIS_conductivity"] <= 0).any():
        raise AssertionError("KIT conductivity must be positive before log10 transform")
    return frame


def formulation_key(frame: pd.DataFrame) -> pd.Series:
    values = frame[COMPONENTS].to_numpy(float)
    return pd.Series(
        ["|".join(f"{value:.6f}" for value in row) for row in values],
        index=frame.index,
        dtype=str,
    )


def prepare_formulations(
    raw: pd.DataFrame, design: dict[str, Any]
) -> tuple[pd.DataFrame, np.ndarray, dict[int, np.ndarray], pd.DataFrame]:
    raw = raw.copy()
    raw["formulation_key"] = formulation_key(raw)
    temperatures = [
        int(design["split"]["target_temperature_C"]),
        int(design["inference"]["primary_source_temperature_C"]),
        *[int(value) for value in design["inference"]["negative_control_source_temperatures_C"]],
    ]
    grouped = (
        raw[raw["temperature"].isin(temperatures)]
        .groupby(["formulation_key", "temperature"], as_index=False)
        .agg(
            conductivity=("EIS_conductivity", "median"),
            replicate_experiments=("experimentID", "nunique"),
            **{component: (component, "first") for component in COMPONENTS},
        )
    )
    counts = grouped.groupby("formulation_key")["temperature"].nunique()
    complete_keys = sorted(counts[counts == len(set(temperatures))].index)
    if len(complete_keys) != 108:
        raise AssertionError(f"Expected 108 complete target/control formulations, found {len(complete_keys)}")
    base = (
        grouped[grouped["formulation_key"].isin(complete_keys)]
        .drop_duplicates("formulation_key")
        .set_index("formulation_key")
        .loc[complete_keys]
        .reset_index()
    )
    solvent_total = base[["PC", "EC", "EMC"]].sum(axis=1).to_numpy(float)
    if np.any(solvent_total <= 0):
        raise AssertionError("Non-positive solvent total")
    x = np.column_stack(
        [
            base["PC"].to_numpy(float) / solvent_total,
            base["EC"].to_numpy(float) / solvent_total,
            base["EMC"].to_numpy(float) / solvent_total,
            base["LiPF_6"].to_numpy(float) / solvent_total,
        ]
    ).astype(np.float32)
    outcome: dict[int, np.ndarray] = {}
    for temperature in sorted(set(temperatures)):
        values = (
            grouped[
                (grouped["temperature"] == temperature)
                & grouped["formulation_key"].isin(complete_keys)
            ]
            .set_index("formulation_key")
            .loc[complete_keys, "conductivity"]
            .to_numpy(float)
        )
        outcome[temperature] = np.log10(values)
    replicate_summary = (
        grouped[grouped["formulation_key"].isin(complete_keys)]
        .groupby("temperature", as_index=False)
        .agg(
            formulations=("formulation_key", "nunique"),
            raw_experiments=("replicate_experiments", "sum"),
            median_replicates=("replicate_experiments", "median"),
            min_replicates=("replicate_experiments", "min"),
            max_replicates=("replicate_experiments", "max"),
        )
    )
    return base, x, outcome, replicate_summary


def balanced_hash_folds(keys: list[str], n_splits: int, salt: str = "") -> np.ndarray:
    digests = [
        hashlib.sha256(f"{salt}|{key}".encode("utf-8")).hexdigest()
        for key in keys
    ]
    order = np.argsort(np.asarray(digests, dtype=object), kind="stable")
    folds = np.empty(len(keys), dtype=int)
    for rank, index in enumerate(order):
        folds[index] = rank % n_splits
    return folds


def outer_splits(keys: list[str]) -> dict[str, dict[str, np.ndarray]]:
    assignment = balanced_hash_folds(keys, 5, "outer")
    splits: dict[str, dict[str, np.ndarray]] = {}
    for fold in range(5):
        test = np.flatnonzero(assignment == fold)
        development = np.flatnonzero(assignment != fold)
        if set(test) & set(development):
            raise AssertionError("KIT outer split overlap")
        splits[f"fold_{fold}"] = {"development": development, "test": test}
    test_union = np.concatenate([value["test"] for value in splits.values()])
    if len(test_union) != len(keys) or len(np.unique(test_union)) != len(keys):
        raise AssertionError("KIT outer test folds do not partition formulations")
    return splits


def source_forest(seed: int, *, n_jobs: int = 1):
    return RandomForestRegressor(
        n_estimators=300,
        min_samples_leaf=2,
        max_features=1.0,
        random_state=seed,
        n_jobs=n_jobs,
    )


def target_forest(seed: int, *, n_jobs: int = -1):
    return RandomForestRegressor(
        n_estimators=300,
        min_samples_leaf=2,
        max_features=1.0,
        random_state=seed,
        n_jobs=n_jobs,
    )


def target_extra_trees(seed: int, *, n_jobs: int = -1):
    return ExtraTreesRegressor(
        n_estimators=300,
        min_samples_leaf=2,
        max_features=1.0,
        random_state=seed,
        n_jobs=n_jobs,
    )


def target_polynomial_ridge(_: int, *, n_jobs: int = -1):
    del n_jobs
    return make_pipeline(
        PolynomialFeatures(degree=2, include_bias=False),
        StandardScaler(),
        Ridge(alpha=10.0, solver="cholesky"),
    )


def cross_fitted_source_features(
    x: np.ndarray,
    y_source: np.ndarray,
    keys: list[str],
    splits: dict[str, dict[str, np.ndarray]],
    seed: int,
    *,
    shuffle_labels: bool = False,
) -> tuple[dict[str, np.ndarray], pd.DataFrame]:
    """Create honest fold-specific source features and source-quality rows."""
    by_fold: dict[str, np.ndarray] = {}
    quality_rows: list[dict[str, Any]] = []
    all_test_y: list[np.ndarray] = []
    all_test_prediction: list[np.ndarray] = []
    for fold_id, split in splits.items():
        development = split["development"]
        test = split["test"]
        local_seed = seed + stable_offset(f"source:{fold_id}") % 1_000_000
        y_fit = y_source.copy()
        if shuffle_labels:
            rng = np.random.default_rng(local_seed + 911)
            y_fit[development] = y_fit[development][rng.permutation(len(development))]
        feature = np.full(len(y_source), np.nan, dtype=float)
        inner_assignment = balanced_hash_folds(
            [keys[index] for index in development], 5, f"inner:{fold_id}"
        )
        for inner_fold in range(5):
            inner_test = development[inner_assignment == inner_fold]
            inner_train = development[inner_assignment != inner_fold]
            model = source_forest(local_seed + inner_fold, n_jobs=1).fit(
                x[inner_train], y_fit[inner_train]
            )
            feature[inner_test] = model.predict(x[inner_test])
        final_model = source_forest(local_seed + 100, n_jobs=1).fit(
            x[development], y_fit[development]
        )
        feature[test] = final_model.predict(x[test])
        if np.isnan(feature[development]).any() or np.isnan(feature[test]).any():
            raise AssertionError(f"Incomplete source feature in {fold_id}")
        by_fold[fold_id] = feature
        fold_r2 = r2_score(y_source[test], feature[test])
        quality_rows.append(
            {
                "fold": fold_id,
                "development_formulations": len(development),
                "test_formulations": len(test),
                "source_test_formulations_seen_during_fit": 0,
                "source_test_r2": float(fold_r2),
                "labels_shuffled": bool(shuffle_labels),
            }
        )
        all_test_y.append(y_source[test])
        all_test_prediction.append(feature[test])
    pooled_r2 = r2_score(np.concatenate(all_test_y), np.concatenate(all_test_prediction))
    quality = pd.DataFrame(quality_rows)
    quality["pooled_source_oof_r2"] = float(pooled_r2)
    return by_fold, quality


def build_samples(
    splits: dict[str, dict[str, np.ndarray]], n: int, repeats: int, seed: int
) -> dict[str, list[np.ndarray]]:
    return {
        fold_id: training_samples(
            split["development"],
            n,
            repeats,
            seed + stable_offset(f"kit-samples:{fold_id}") % 1_000_000,
        )
        for fold_id, split in splits.items()
    }


def precompute_baseline_predictions(
    x: np.ndarray,
    y: np.ndarray,
    samples: dict[str, list[np.ndarray]],
    splits: dict[str, dict[str, np.ndarray]],
    learner_factory: Callable[..., Any],
    learner_label: str,
    seed: int,
    parallel_jobs: int,
) -> dict[tuple[str, int], np.ndarray]:
    jobs = [
        (fold_id, split, repeat, train)
        for fold_id, split in splits.items()
        for repeat, train in enumerate(samples[fold_id])
    ]

    def one_fit(fold_id, split, repeat, train):
        model_seed = seed + stable_offset(
            f"target:{learner_label}:{fold_id}:{repeat}"
        ) % 1_000_000
        prediction = learner_factory(model_seed, n_jobs=1).fit(
            x[train], y[train]
        ).predict(x[split["test"]])
        return (fold_id, repeat), prediction

    fitted = Parallel(n_jobs=parallel_jobs, prefer="processes", verbose=0)(
        delayed(one_fit)(*job) for job in jobs
    )
    return dict(fitted)


def evaluate_edge(
    x: np.ndarray,
    y: np.ndarray,
    keys: list[str],
    feature_by_fold: dict[str, np.ndarray],
    samples: dict[str, list[np.ndarray]],
    splits: dict[str, dict[str, np.ndarray]],
    learner_factory: Callable[..., Any],
    learner_label: str,
    source_label: str,
    seed: int,
    parallel_jobs: int,
    baseline_predictions: dict[tuple[str, int], np.ndarray] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    jobs = [
        (fold_id, split, repeat, train)
        for fold_id, split in splits.items()
        for repeat, train in enumerate(samples[fold_id])
    ]

    def one_fit(fold_id, split, repeat, train):
        test = split["test"]
        feature = feature_by_fold[fold_id]
        model_seed = seed + stable_offset(
            f"target:{learner_label}:{fold_id}:{repeat}"
        ) % 1_000_000
        # Parallelism is across independent fold/repeat fits.  Each forest is
        # single-threaded to avoid nested oversubscription; predictions match
        # the tree-parallel implementation to floating-point precision.
        augmented = learner_factory(model_seed, n_jobs=1).fit(
            np.column_stack([x[train], feature[train]]), y[train]
        )
        if baseline_predictions is None:
            baseline = learner_factory(model_seed, n_jobs=1).fit(x[train], y[train])
            base_prediction = baseline.predict(x[test])
        else:
            base_prediction = baseline_predictions[(fold_id, repeat)]
        aug_prediction = augmented.predict(
            np.column_stack([x[test], feature[test]])
        )
        base_rmse = float(np.sqrt(np.mean((y[test] - base_prediction) ** 2)))
        aug_rmse = float(np.sqrt(np.mean((y[test] - aug_prediction) ** 2)))
        repeat_row = {
            "target": "kit_conductivity_minus_30_C",
            "source": source_label,
            "learner": learner_label,
            "fold": fold_id,
            "repeat": repeat,
            "train_n": len(train),
            "test_n": len(test),
            "base_rmse": base_rmse,
            "aug_rmse": aug_rmse,
            "delta_rmse": base_rmse - aug_rmse,
            "relative_rmse_improvement": (base_rmse - aug_rmse) / base_rmse,
            "base_r2": float(r2_score(y[test], base_prediction)),
            "aug_r2": float(r2_score(y[test], aug_prediction)),
        }
        repeat_row["delta_r2"] = repeat_row["aug_r2"] - repeat_row["base_r2"]
        prediction_rows = [
            {
                "target": "kit_conductivity_minus_30_C",
                "source": source_label,
                "learner": learner_label,
                "fold": fold_id,
                "repeat": repeat,
                "material_key": keys[index],
                "year": 0,
                "y": y[index],
                "baseline": float(base_prediction[position]),
                "augmented": float(aug_prediction[position]),
            }
            for position, index in enumerate(test)
        ]
        importance_row = None
        if repeat == 0 and hasattr(augmented, "feature_importances_"):
            importance = np.asarray(augmented.feature_importances_, dtype=float)
            order = np.argsort(-importance)
            rank = int(np.flatnonzero(order == len(importance) - 1)[0] + 1)
            importance_row = {
                "source": source_label,
                "learner": learner_label,
                "fold": fold_id,
                "source_feature_importance": float(importance[-1]),
                "source_feature_rank": rank,
                "feature_count": len(importance),
            }
        return repeat_row, prediction_rows, importance_row

    results = Parallel(n_jobs=parallel_jobs, prefer="processes", verbose=0)(
        delayed(one_fit)(*job) for job in jobs
    )
    repeat_rows = [item[0] for item in results]
    prediction_rows = [row for item in results for row in item[1]]
    importance_rows = [item[2] for item in results if item[2] is not None]
    return (
        pd.DataFrame(repeat_rows),
        pd.DataFrame(prediction_rows),
        pd.DataFrame(importance_rows),
    )


def learning_curve(
    x: np.ndarray,
    y: np.ndarray,
    samples_at_30: dict[str, list[np.ndarray]],
    splits: dict[str, dict[str, np.ndarray]],
    budgets: list[int],
    repeats: int,
    seed: int,
    parallel_jobs: int,
    baseline_predictions_at_30: dict[tuple[str, int], np.ndarray],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for budget in budgets:
        if budget == 30:
            active_repeats = len(next(iter(samples_at_30.values())))
            fit_results = []
            for fold_id, split in splits.items():
                test = split["test"]
                for repeat in range(active_repeats):
                    prediction = baseline_predictions_at_30[(fold_id, repeat)]
                    fit_results.append(
                        (
                            repeat,
                            float(np.sum((y[test] - prediction) ** 2)),
                            len(test),
                        )
                    )
        else:
            active_repeats = repeats
            budget_samples = build_samples(
                splits,
                int(budget),
                active_repeats,
                seed + stable_offset(f"curve:{budget}"),
            )
            jobs = [
                (fold_id, split, repeat, train)
                for fold_id, split in splits.items()
                for repeat, train in enumerate(budget_samples[fold_id])
            ]

            def one_curve_fit(fold_id, split, repeat, train):
                test = split["test"]
                model_seed = seed + stable_offset(
                    f"curve:{budget}:{fold_id}:{repeat}"
                ) % 1_000_000
                prediction = target_forest(model_seed, n_jobs=1).fit(
                    x[train], y[train]
                ).predict(x[test])
                return repeat, float(np.sum((y[test] - prediction) ** 2)), len(test)

            fit_results = Parallel(n_jobs=parallel_jobs, prefer="processes", verbose=0)(
                delayed(one_curve_fit)(*job) for job in jobs
            )
        repeat_sse = {repeat: [0.0, 0] for repeat in range(active_repeats)}
        for repeat, sse, n in fit_results:
            repeat_sse[repeat][0] += sse
            repeat_sse[repeat][1] += n
        rmses = np.asarray(
            [np.sqrt(sse / n) for sse, n in repeat_sse.values()], dtype=float
        )
        rows.append(
            {
                "target": "kit_conductivity_minus_30_C",
                "train_n": int(budget),
                "rmse_mean": float(rmses.mean()),
                "rmse_sd": float(rmses.std(ddof=1)),
                "repeats_used": int(active_repeats),
            }
        )
    curve = pd.DataFrame(rows).sort_values("train_n").reset_index(drop=True)
    curve["rmse_monotone"] = IsotonicRegression(increasing=False).fit_transform(
        curve["train_n"], curve["rmse_mean"]
    )
    rho = float(stats.spearmanr(curve["train_n"], curve["rmse_mean"]).statistic)
    valid = bool(rho < 0 and curve.iloc[-1]["rmse_mean"] < curve.iloc[0]["rmse_mean"])
    curve["learning_curve_spearman_rho"] = rho
    curve["valid_for_target_equivalence"] = valid
    return curve


def fixed_subset_permutation_test(
    x: np.ndarray,
    y: np.ndarray,
    feature_by_fold: dict[str, np.ndarray],
    samples: dict[str, list[np.ndarray]],
    splits: dict[str, dict[str, np.ndarray]],
    permutations: int,
    seed: int,
    n_jobs: int,
) -> tuple[float, float, pd.DataFrame]:
    """One-sided mapping test on the first frozen n=30 subset in each fold."""
    baseline_sse = 0.0
    observed_aug_sse = 0.0
    n_total = 0
    for fold_id, split in splits.items():
        train = samples[fold_id][0]
        test = split["test"]
        feature = feature_by_fold[fold_id]
        model_seed = seed + stable_offset(f"permutation-model:{fold_id}") % 1_000_000
        baseline = target_forest(model_seed, n_jobs=1).fit(x[train], y[train])
        augmented = target_forest(model_seed, n_jobs=1).fit(
            np.column_stack([x[train], feature[train]]), y[train]
        )
        baseline_sse += float(np.sum((y[test] - baseline.predict(x[test])) ** 2))
        observed_aug_sse += float(
            np.sum(
                (
                    y[test]
                    - augmented.predict(np.column_stack([x[test], feature[test]]))
                )
                ** 2
            )
        )
        n_total += len(test)
    observed = (baseline_sse - observed_aug_sse) / baseline_sse

    def one_permutation(permutation: int) -> float:
        rng = np.random.default_rng(seed + 10_000 + permutation)
        augmented_sse = 0.0
        for fold_id, split in splits.items():
            train = samples[fold_id][0]
            test = split["test"]
            feature = feature_by_fold[fold_id]
            permuted_train = feature[train][rng.permutation(len(train))]
            permuted_test = feature[test][rng.permutation(len(test))]
            model_seed = seed + stable_offset(f"permutation-model:{fold_id}") % 1_000_000
            augmented = target_forest(model_seed, n_jobs=1).fit(
                np.column_stack([x[train], permuted_train]), y[train]
            )
            prediction = augmented.predict(np.column_stack([x[test], permuted_test]))
            augmented_sse += float(np.sum((y[test] - prediction) ** 2))
        return (baseline_sse - augmented_sse) / baseline_sse

    null_values = Parallel(n_jobs=n_jobs, prefer="processes", verbose=0)(
        delayed(one_permutation)(permutation) for permutation in range(permutations)
    )
    null = pd.DataFrame(
        {
            "permutation": np.arange(permutations, dtype=int),
            "relative_mse_improvement": null_values,
            "observed_relative_mse_improvement": float(observed),
            "fixed_target_subset_repeat": 0,
        }
    )
    p_value = (1 + int(np.sum(np.asarray(null_values) >= observed))) / (permutations + 1)
    return float(p_value), float(observed), null


def quick_or_full(design: dict[str, Any], quick: bool) -> dict[str, int]:
    inference = design["inference"]
    if not quick:
        return {
            "target_repeats": int(inference["target_training_repeats"]),
            "sensitivity_repeats": int(inference["sensitivity_repeats"]),
            "bootstrap": int(inference["hierarchical_bootstrap_replicates"]),
            "permutations": int(inference["fixed_subset_feature_mapping_permutations"]),
            "curve_repeats": int(inference["learning_curve_repeats"]),
        }
    return {
        "target_repeats": 3,
        "sensitivity_repeats": 2,
        "bootstrap": 100,
        "permutations": 9,
        "curve_repeats": 2,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true", help="Smoke test; writes quick_* artifacts only")
    parser.add_argument("--jobs", type=int, default=-1, help="Parallel jobs for the permutation test")
    args = parser.parse_args()

    ensure_output_dirs()
    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    inference = design["inference"]
    run = quick_or_full(design, args.quick)
    seed = int(design["seed"])
    prefix = "quick_kit_temperature" if args.quick else "kit_temperature"

    raw = load_raw(design)
    formulations, x, outcomes, replicate_summary = prepare_formulations(raw, design)
    keys = formulations["formulation_key"].astype(str).tolist()
    splits = outer_splits(keys)
    target_temperature = int(design["split"]["target_temperature_C"])
    primary_temperature = int(inference["primary_source_temperature_C"])
    control_temperatures = [
        int(value) for value in inference["negative_control_source_temperatures_C"]
    ]
    y = outcomes[target_temperature]
    samples = build_samples(
        splits,
        int(design["split"]["target_budget_per_fold"]),
        run["target_repeats"],
        seed,
    )

    features: dict[str, dict[str, np.ndarray]] = {}
    source_quality_frames: list[pd.DataFrame] = []
    for source_temperature in [primary_temperature, *control_temperatures]:
        label = f"temperature_{source_temperature}_C"
        feature, quality = cross_fitted_source_features(
            x,
            outcomes[source_temperature],
            keys,
            splits,
            seed + stable_offset(label) % 1_000_000,
        )
        features[label] = feature
        quality["source"] = label
        quality["source_temperature_C"] = source_temperature
        quality["target_temperature_C"] = target_temperature
        quality["absolute_temperature_distance_C"] = abs(
            source_temperature - target_temperature
        )
        source_quality_frames.append(quality)
    placebo_label = f"shuffled_temperature_{primary_temperature}_C"
    placebo_feature, placebo_quality = cross_fitted_source_features(
        x,
        outcomes[primary_temperature],
        keys,
        splits,
        seed + stable_offset(placebo_label) % 1_000_000,
        shuffle_labels=True,
    )
    features[placebo_label] = placebo_feature
    placebo_quality["source"] = placebo_label
    placebo_quality["source_temperature_C"] = primary_temperature
    placebo_quality["target_temperature_C"] = target_temperature
    placebo_quality["absolute_temperature_distance_C"] = abs(
        primary_temperature - target_temperature
    )
    source_quality_frames.append(placebo_quality)
    source_quality = pd.concat(source_quality_frames, ignore_index=True)

    primary_baseline_predictions = precompute_baseline_predictions(
        x,
        y,
        samples,
        splits,
        target_forest,
        "random-forest-primary",
        seed,
        args.jobs,
    )
    edge_rows: list[dict[str, Any]] = []
    all_repeats: list[pd.DataFrame] = []
    all_predictions: list[pd.DataFrame] = []
    all_importance: list[pd.DataFrame] = []
    edge_labels = [
        f"temperature_{temperature}_C"
        for temperature in [primary_temperature, *control_temperatures]
    ] + [placebo_label]
    for source_label in edge_labels:
        repeats, predictions, importance = evaluate_edge(
            x,
            y,
            keys,
            features[source_label],
            samples,
            splits,
            target_forest,
            "random-forest-primary",
            source_label,
            seed,
            args.jobs,
            baseline_predictions=primary_baseline_predictions,
        )
        summary = summarize_predictions(
            predictions,
            seed + stable_offset(f"bootstrap:{source_label}") % 1_000_000,
            run["bootstrap"],
        )
        source_temperature = primary_temperature if source_label == placebo_label else int(
            source_label.removeprefix("temperature_").removesuffix("_C")
        )
        summary.update(
            {
                "target": "kit_conductivity_minus_30_C",
                "source": source_label,
                "target_temperature_C": target_temperature,
                "source_temperature_C": source_temperature,
                "absolute_temperature_distance_C": abs(source_temperature - target_temperature),
                "relation": (
                    "shuffled-source-placebo"
                    if source_label == placebo_label
                    else (
                        "adjacent-condition-primary"
                        if source_temperature == primary_temperature
                        else "temperature-distance-control"
                    )
                ),
                "train_n": int(design["split"]["target_budget_per_fold"]),
                "independent_formulations": len(keys),
                "source_test_formulations_seen_during_fit": 0,
                "source_pooled_oof_r2": float(
                    source_quality[source_quality["source"] == source_label][
                        "pooled_source_oof_r2"
                    ].iloc[0]
                ),
            }
        )
        edge_rows.append(summary)
        all_repeats.append(repeats)
        all_predictions.append(predictions)
        if not importance.empty:
            all_importance.append(importance)
    edges = pd.DataFrame(edge_rows)

    curve = learning_curve(
        x,
        y,
        samples,
        splits,
        [int(value) for value in inference["learning_curve_budgets"]],
        run["curve_repeats"],
        seed + stable_offset("kit-learning-curve"),
        args.jobs,
        primary_baseline_predictions,
    )
    equivalents = [
        target_equivalent_samples(
            curve,
            float(row["aug_rmse_mean"]),
            int(design["split"]["target_budget_per_fold"]),
        )
        for _, row in edges.iterrows()
    ]
    edges["target_equivalent_n"] = [value[0] for value in equivalents]
    edges["target_sample_fraction_saved"] = [value[1] for value in equivalents]
    edges["target_equivalence_status"] = [value[2] for value in equivalents]

    primary_label = f"temperature_{primary_temperature}_C"
    p_value, observed_permutation_statistic, permutation_null = fixed_subset_permutation_test(
        x,
        y,
        features[primary_label],
        samples,
        splits,
        run["permutations"],
        seed + stable_offset("kit-primary-permutation"),
        args.jobs,
    )
    edges["primary_permutation_p"] = np.nan
    edges.loc[edges["source"] == primary_label, "primary_permutation_p"] = p_value

    sensitivity_rows: list[dict[str, Any]] = []
    sensitivity_samples = {
        fold_id: fold_samples[: run["sensitivity_repeats"]]
        for fold_id, fold_samples in samples.items()
    }
    for learner_label, learner_factory in (
        ("extra-trees-sensitivity", target_extra_trees),
        ("polynomial-ridge-sensitivity", target_polynomial_ridge),
    ):
        repeats, predictions, importance = evaluate_edge(
            x,
            y,
            keys,
            features[primary_label],
            sensitivity_samples,
            splits,
            learner_factory,
            learner_label,
            primary_label,
            seed,
            args.jobs,
        )
        item = summarize_predictions(
            predictions,
            seed + stable_offset(f"sensitivity:{learner_label}") % 1_000_000,
            run["bootstrap"],
        )
        item["learner"] = learner_label
        sensitivity_rows.append(item)
        all_repeats.append(repeats)
        all_predictions.append(predictions)
        if not importance.empty:
            all_importance.append(importance)
    sensitivity = pd.DataFrame(sensitivity_rows)

    primary = edges[edges["source"] == primary_label].iloc[0]
    placebo = edges[edges["source"] == placebo_label].iloc[0]
    positive_learners = int(primary["relative_rmse_improvement_mean"] > 0) + int(
        (sensitivity["relative_rmse_improvement_mean"] > 0).sum()
    )
    temperature_edges = edges[edges["relation"] != "shuffled-source-placebo"].sort_values(
        "absolute_temperature_distance_C"
    )
    effects_by_distance = temperature_edges["relative_rmse_improvement_mean"].to_numpy(float)
    distances = temperature_edges["absolute_temperature_distance_C"].to_numpy(float)
    distance_rho = float(stats.spearmanr(distances, effects_by_distance).statistic)
    strict_distance_order = bool(np.all(np.diff(effects_by_distance) < 0))
    fold_effects = [float(primary[f"effect_fold_{fold}"]) for fold in range(5)]
    primary_source_r2 = float(primary["source_pooled_oof_r2"])
    gates = {
        "relative_rmse_at_least_5pct": bool(
            primary["relative_rmse_improvement_mean"]
            >= float(inference["minimum_relative_rmse_reduction"])
        ),
        "hierarchical_bootstrap_ci_above_zero": bool(primary["relative_rmse_ci_lo"] > 0),
        "positive_augmented_r2": bool(primary["pooled_aug_r2"] > 0),
        "positive_effect_in_all_five_formulation_folds": bool(
            all(value > 0 for value in fold_effects)
        ),
        "target_sample_fraction_saved_at_least_30pct": bool(
            primary["target_sample_fraction_saved"]
            >= float(inference["minimum_target_sample_fraction_saved"])
        ),
        "at_least_two_of_three_learners_positive": bool(
            positive_learners >= int(inference["minimum_positive_learners_of_three"])
        ),
        "source_oof_r2_positive": bool(primary_source_r2 > 0),
        "zero_test_formulations_seen_by_source_model": bool(
            primary["source_test_formulations_seen_during_fit"] == 0
        ),
        "primary_permutation_p_below_0_05": bool(p_value < 0.05),
        "learning_curve_valid_for_equivalence": bool(
            curve["valid_for_target_equivalence"].iloc[0]
        ),
        "primary_exceeds_each_distant_temperature_control": bool(
            primary["relative_rmse_improvement_mean"]
            > temperature_edges[
                temperature_edges["source"] != primary_label
            ]["relative_rmse_improvement_mean"].max()
        ),
        "effect_strictly_decreases_with_temperature_distance": strict_distance_order,
        "shuffled_source_not_positive_at_95pct": bool(placebo["relative_rmse_ci_lo"] <= 0),
        "shuffled_source_smaller_than_primary": bool(
            placebo["relative_rmse_improvement_mean"]
            < primary["relative_rmse_improvement_mean"]
        ),
    }
    rescue_supported = bool(all(gates.values()))
    if rescue_supported:
        decision = "within-campaign-local-neighbor-rescue-gate-passed"
    elif primary["relative_rmse_ci_hi"] < 0:
        decision = "adjacent-source-harmful"
    elif primary["relative_rmse_ci_lo"] > 0 and primary["pooled_aug_r2"] > 0:
        decision = "directional-local-borrowing-below-full-rescue-gate"
    else:
        decision = "unresolved"

    edges["edge_status"] = np.where(
        edges["source"] == primary_label,
        decision,
        np.where(
            edges["relative_rmse_ci_lo"] > 0,
            "control-positive",
            np.where(edges["relative_rmse_ci_hi"] < 0, "harmful", "unresolved"),
        ),
    )
    edges["primary_positive_learners_of_three"] = np.where(
        edges["source"] == primary_label, positive_learners, np.nan
    )

    all_repeat_frame = pd.concat(all_repeats, ignore_index=True)
    all_prediction_frame = pd.concat(all_predictions, ignore_index=True)
    importance_frame = (
        pd.concat(all_importance, ignore_index=True)
        if all_importance
        else pd.DataFrame()
    )
    replicate_summary.to_csv(RESULTS / f"{prefix}_replicate_structure.csv", index=False)
    source_quality.to_csv(RESULTS / f"{prefix}_source_quality.csv", index=False)
    edges.to_csv(RESULTS / f"{prefix}_edges.csv", index=False)
    curve.to_csv(RESULTS / f"{prefix}_learning_curve.csv", index=False)
    sensitivity.to_csv(RESULTS / f"{prefix}_sensitivity.csv", index=False)
    all_repeat_frame.to_csv(RESULTS / f"{prefix}_repeats.csv", index=False)
    all_prediction_frame.to_csv(RESULTS / f"{prefix}_predictions.csv", index=False)
    if not importance_frame.empty:
        importance_frame.to_csv(RESULTS / f"{prefix}_feature_importance.csv", index=False)
    permutation_null.to_csv(RESULTS / f"{prefix}_permutation_null.csv", index=False)

    primary_importance = importance_frame[
        (importance_frame["source"] == primary_label)
        & (importance_frame["learner"] == "random-forest-primary")
    ]
    summary = {
        "analysis_status": design["status"],
        "interpretation_scope": "within-campaign local-neighbor rescue; not independent-dataset replication",
        "raw_rows": len(raw),
        "raw_experiment_ids": int(raw["experimentID"].nunique()),
        "independent_formulations": len(keys),
        "outer_folds": len(splits),
        "target_temperature_C": target_temperature,
        "primary_source_temperature_C": primary_temperature,
        "target_budget_per_fold": int(design["split"]["target_budget_per_fold"]),
        "primary_source": primary_label,
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
        "permutation_observed_relative_mse_improvement": observed_permutation_statistic,
        "positive_learners_of_three": int(positive_learners),
        "source_oof_r2": primary_source_r2,
        "source_feature_importance_mean": (
            float(primary_importance["source_feature_importance"].mean())
            if not primary_importance.empty
            else None
        ),
        "source_feature_rank_median": (
            float(primary_importance["source_feature_rank"].median())
            if not primary_importance.empty
            else None
        ),
        "temperature_distance_spearman_rho": distance_rho,
        "shuffled_source_effect": float(placebo["relative_rmse_improvement_mean"]),
        "shuffled_source_ci": [
            float(placebo["relative_rmse_ci_lo"]),
            float(placebo["relative_rmse_ci_hi"]),
        ],
        "test_formulations_seen_by_source_model": 0,
        "arrhenius_or_eis_fit_features_used": False,
        "quick_smoke_test": bool(args.quick),
        "gates": gates,
        "rescue_claim_supported": rescue_supported,
        "decision": decision,
    }
    (RESULTS / f"{prefix}_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )

    print("\nKIT temperature-neighbor edges")
    print(
        edges[
            [
                "source",
                "absolute_temperature_distance_C",
                "relative_rmse_improvement_mean",
                "relative_rmse_ci_lo",
                "relative_rmse_ci_hi",
                "pooled_base_r2",
                "pooled_aug_r2",
                "target_sample_fraction_saved",
            ]
        ].to_string(index=False)
    )
    print("\nDecision")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
