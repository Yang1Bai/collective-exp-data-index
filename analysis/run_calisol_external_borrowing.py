"""Frozen cross-article replication of local electrolyte knowledge borrowing.

The design is fixed in ``calisol_external_borrowing_design.json``.  The outer
test unit is a source article, not a row or a formulation.  For every target
prediction, source-temperature models exclude the held-out article and exact
held-out chemistry identities.  Development source priors are leave-one-
article-out predictions.  This supports a multi-article local-condition claim
only; it is not a cross-domain or universal transfer test.
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
from sklearn.ensemble import ExtraTreesRegressor, RandomForestRegressor
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from common import RESULTS, ensure_output_dirs
from run_knowledge_map import stable_offset, target_equivalent_samples


HERE = Path(__file__).resolve().parent
DESIGN_PATH = HERE / "calisol_external_borrowing_design.json"
TARGET_ID = "calisol_conductivity_minus_40_C"
NUMERICAL_ZERO = 1e-12


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load_raw(design: dict[str, Any]) -> pd.DataFrame:
    spec = design["dataset"]
    cache = Path.home() / ".collective_data_cache" / "calisol-23" / spec["file_name"]
    if cache.exists():
        raw = cache.read_bytes()
    else:
        request = urllib.request.Request(
            spec["raw_url"], headers={"User-Agent": "collective-exp-data-index/0.3"}
        )
        with urllib.request.urlopen(request, timeout=300) as response:
            raw = response.read()
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_bytes(raw)
    observed = sha256(raw)
    if observed != spec["raw_sha256"]:
        raise RuntimeError(f"CALiSol raw hash mismatch: {observed} != {spec['raw_sha256']}")
    frame = pd.read_csv(cache)
    if len(frame) != int(spec["raw_rows_expected"]):
        raise AssertionError(f"CALiSol rows: {len(frame)} != {spec['raw_rows_expected']}")
    if frame["doi"].nunique() != int(spec["literature_articles_expected"]):
        raise AssertionError("Unexpected CALiSol article count")
    frame["salt"] = frame["salt"].astype(str).str.strip()
    for column in ["k", "T", "c", *solvent_columns(frame)]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    required = [
        "doi",
        "k",
        "T",
        "c",
        "salt",
        "c units",
        "solvent ratio type",
        *solvent_columns(frame),
    ]
    missing = sorted(set(required) - set(frame.columns))
    if missing:
        raise AssertionError(f"Missing CALiSol columns: {missing}")
    if frame[["doi", "T", "c", "salt", "c units", "solvent ratio type"]].isna().any().any():
        raise AssertionError("Missing required CALiSol identity or condition fields")
    return frame


def solvent_columns(frame: pd.DataFrame) -> list[str]:
    marker = frame.columns.get_loc("solvent ratio type") + 1
    return list(frame.columns[marker:])


def chemistry_keys(frame: pd.DataFrame, solvents: list[str]) -> pd.Series:
    def one(row: pd.Series) -> str:
        tokens = [
            str(row["salt"]).strip(),
            f"{float(row['c']):.8f}",
            str(row["c units"]),
            str(row["solvent ratio type"]),
            *[f"{float(row[column]):.8f}" for column in solvents],
        ]
        return hashlib.sha256("|".join(tokens).encode("utf-8")).hexdigest()

    return frame.apply(one, axis=1)


def prepare_tasks(
    raw: pd.DataFrame, design: dict[str, Any]
) -> tuple[pd.DataFrame, dict[int, pd.DataFrame], np.ndarray, dict[int, np.ndarray], list[str], pd.DataFrame]:
    solvents = solvent_columns(raw)
    frame = raw.copy()
    frame["chemistry_key"] = chemistry_keys(frame, solvents)
    frame["temperature_C"] = frame["T"] - 273.15
    target_temperature = int(design["split"]["target_temperature_C"])
    source_temperatures = [
        int(design["inference"]["primary_source_temperature_C"]),
        *[int(value) for value in design["inference"]["negative_control_source_temperatures_C"]],
    ]
    temperatures = [target_temperature, *source_temperatures]
    feature_columns = ["c", *solvents]
    categorical_columns = ["salt", "c units", "solvent ratio type"]

    tables: dict[int, pd.DataFrame] = {}
    structure_rows: list[dict[str, Any]] = []
    for temperature in temperatures:
        selected = frame[(frame["temperature_C"] - temperature).abs() <= 2.5].copy()
        raw_rows = len(selected)
        table = (
            selected.groupby(["doi", "chemistry_key"], as_index=False)
            .agg(
                conductivity=("k", "median"),
                observed_temperature_C=("temperature_C", "median"),
                raw_rows=("k", "size"),
                **{column: (column, "first") for column in [*categorical_columns, *feature_columns]},
            )
            .sort_values(["doi", "chemistry_key"])
            .reset_index(drop=True)
        )
        table = table[
            np.isfinite(table["conductivity"])
            & (table["conductivity"] > NUMERICAL_ZERO)
        ].copy().reset_index(drop=True)
        table["nominal_temperature_C"] = temperature
        table["value"] = np.log10(table["conductivity"].to_numpy(float))
        table["unit_key"] = table["doi"].astype(str) + "|" + table["chemistry_key"].astype(str)
        tables[temperature] = table
        structure_rows.append(
            {
                "nominal_temperature_C": temperature,
                "raw_rows_in_window": raw_rows,
                "paper_specific_formulations_before_outcome_filter": int(
                    selected.groupby(["doi", "chemistry_key"]).ngroups
                ),
                "eligible_positive_formulations": len(table),
                "articles": int(table["doi"].nunique()),
                "salts": int(table["salt"].nunique()),
                "active_solvent_columns": int(sum((table[solvents] != 0).any(axis=0))),
            }
        )

    target = tables.pop(target_temperature).copy()
    cross_article_count = target.groupby("chemistry_key")["doi"].nunique()
    duplicate_chemistry = set(cross_article_count[cross_article_count > 1].index)
    target = target[~target["chemistry_key"].isin(duplicate_chemistry)].copy()
    target = target.sort_values("unit_key").reset_index(drop=True)
    if len(duplicate_chemistry) != int(
        design["qualification_audit"]["cross_article_duplicate_chemistry_keys_excluded"]
    ):
        raise AssertionError("CALiSol cross-article target identity count changed")
    if len(target) != int(design["qualification_audit"]["expected_target_units_after_all_frozen_filters"]):
        raise AssertionError(f"CALiSol target units: {len(target)}")

    combined = pd.concat(
        [
            target.assign(_table=f"target_{target_temperature}"),
            *[table.assign(_table=f"source_{temperature}") for temperature, table in tables.items()],
        ],
        ignore_index=True,
    )
    encoded_categorical = pd.get_dummies(
        combined[categorical_columns].astype(str),
        columns=categorical_columns,
        dtype=float,
    )
    numeric = combined[feature_columns].astype(float).reset_index(drop=True)
    encoded = pd.concat([numeric, encoded_categorical.reset_index(drop=True)], axis=1)
    encoded = encoded.reindex(sorted(encoded.columns), axis=1)
    if not np.isfinite(encoded.to_numpy(float)).all():
        raise AssertionError("Non-finite CALiSol composition feature")
    feature_names = encoded.columns.astype(str).tolist()
    start = 0
    target_x = encoded.iloc[start : start + len(target)].to_numpy(np.float32)
    start += len(target)
    source_x: dict[int, np.ndarray] = {}
    for temperature, table in tables.items():
        source_x[temperature] = encoded.iloc[start : start + len(table)].to_numpy(np.float32)
        start += len(table)
    if start != len(encoded):
        raise AssertionError("CALiSol feature alignment failure")
    return (
        target,
        tables,
        target_x,
        source_x,
        feature_names,
        pd.DataFrame(structure_rows),
    )


def article_splits(target: pd.DataFrame) -> tuple[dict[str, dict[str, np.ndarray]], pd.DataFrame]:
    counts = (
        target.groupby("doi").size().rename("target_units").reset_index().sort_values(
            ["target_units", "doi"], ascending=[False, True], kind="stable"
        )
    )
    fold_articles: list[list[str]] = [[] for _ in range(5)]
    fold_sizes = [0] * 5
    for row in counts.itertuples(index=False):
        fold = min(range(5), key=lambda value: (fold_sizes[value], value))
        fold_articles[fold].append(str(row.doi))
        fold_sizes[fold] += int(row.target_units)
    splits: dict[str, dict[str, np.ndarray]] = {}
    rows: list[dict[str, Any]] = []
    for fold, articles in enumerate(fold_articles):
        fold_id = f"fold_{fold}"
        test = np.flatnonzero(target["doi"].isin(articles).to_numpy())
        development = np.flatnonzero(~target["doi"].isin(articles).to_numpy())
        splits[fold_id] = {"development": development, "test": test}
        for article in articles:
            rows.append(
                {
                    "fold": fold_id,
                    "article_doi": article,
                    "target_units": int((target["doi"] == article).sum()),
                    "fold_test_units": len(test),
                }
            )
    union = np.concatenate([split["test"] for split in splits.values()])
    if len(union) != len(target) or len(np.unique(union)) != len(target):
        raise AssertionError("CALiSol article folds do not partition the target")
    if len(set(target.loc[union, "doi"])) != target["doi"].nunique():
        raise AssertionError("CALiSol article fold coverage failure")
    return splits, pd.DataFrame(rows)


def group_balanced_sample(
    indices: np.ndarray, groups: np.ndarray, n: int, seed: int
) -> np.ndarray:
    if len(indices) < n:
        raise RuntimeError(f"Only {len(indices)} development units for budget {n}")
    rng = np.random.default_rng(seed)
    pools: dict[str, list[int]] = {}
    for group in sorted(set(groups[indices].astype(str))):
        values = indices[groups[indices].astype(str) == group].copy()
        rng.shuffle(values)
        pools[group] = values.tolist()
    chosen: list[int] = []
    while len(chosen) < n:
        active = [group for group, values in pools.items() if values]
        if not active:
            raise AssertionError("Group-balanced sampler exhausted early")
        active = list(np.asarray(active)[rng.permutation(len(active))])
        for group in active:
            if len(chosen) == n:
                break
            chosen.append(pools[str(group)].pop())
    return np.asarray(sorted(chosen), dtype=int)


def build_samples(
    target: pd.DataFrame,
    splits: dict[str, dict[str, np.ndarray]],
    n: int,
    repeats: int,
    seed: int,
) -> dict[str, list[np.ndarray]]:
    groups = target["doi"].astype(str).to_numpy()
    return {
        fold_id: [
            group_balanced_sample(
                split["development"], groups, n, seed + stable_offset(f"{fold_id}:{repeat}")
            )
            for repeat in range(repeats)
        ]
        for fold_id, split in splits.items()
    }


def source_forest(seed: int, *, n_jobs: int = 1):
    return RandomForestRegressor(
        n_estimators=300,
        min_samples_leaf=2,
        max_features=1.0,
        random_state=seed,
        n_jobs=n_jobs,
    )


def target_forest(seed: int, *, n_jobs: int = 1):
    return RandomForestRegressor(
        n_estimators=300,
        min_samples_leaf=2,
        max_features=1.0,
        random_state=seed,
        n_jobs=n_jobs,
    )


def target_extra_trees(seed: int, *, n_jobs: int = 1):
    return ExtraTreesRegressor(
        n_estimators=300,
        min_samples_leaf=2,
        max_features=1.0,
        random_state=seed,
        n_jobs=n_jobs,
    )


def target_ridge(_: int, *, n_jobs: int = 1):
    del n_jobs
    return make_pipeline(StandardScaler(), Ridge(alpha=10.0, solver="cholesky"))


def shuffled_within_articles(frame: pd.DataFrame, y: np.ndarray, seed: int) -> np.ndarray:
    output = y.copy()
    rng = np.random.default_rng(seed)
    for _, group in frame.groupby("doi", sort=True):
        indices = group.index.to_numpy(int)
        output[indices] = y[indices][rng.permutation(len(indices))]
    return output


def source_features_for_target(
    target: pd.DataFrame,
    source: pd.DataFrame,
    target_x: np.ndarray,
    source_x: np.ndarray,
    splits: dict[str, dict[str, np.ndarray]],
    seed: int,
    *,
    shuffle_labels: bool = False,
) -> tuple[dict[str, np.ndarray], pd.DataFrame, pd.DataFrame]:
    y_source = source["value"].to_numpy(float)
    source_doi = source["doi"].astype(str)
    source_chemistry = source["chemistry_key"].astype(str)
    feature_by_fold: dict[str, np.ndarray] = {}
    quality_rows: list[dict[str, Any]] = []
    quality_predictions: list[dict[str, Any]] = []

    def fit_predict(
        train_mask: np.ndarray,
        prediction_x: np.ndarray,
        local_seed: int,
    ) -> tuple[np.ndarray, int]:
        train_indices = np.flatnonzero(train_mask)
        if len(train_indices) < 30:
            raise RuntimeError("Too few source rows after article and identity exclusions")
        y_fit = y_source.copy()
        if shuffle_labels:
            y_fit = shuffled_within_articles(source, y_fit, local_seed + 917)
        model = source_forest(local_seed, n_jobs=1).fit(
            source_x[train_indices], y_fit[train_indices]
        )
        return model.predict(prediction_x), len(train_indices)

    for fold_id, split in splits.items():
        local_seed = seed + stable_offset(f"source:{fold_id}") % 1_000_000
        test = split["test"]
        development = split["development"]
        test_articles = set(target.loc[test, "doi"].astype(str))
        feature = np.full(len(target), np.nan, dtype=float)
        dev_training_counts: list[int] = []

        for article in sorted(target.loc[development, "doi"].astype(str).unique()):
            prediction_indices = development[
                target.loc[development, "doi"].astype(str).to_numpy() == article
            ]
            forbidden_chemistry = set(
                target.loc[prediction_indices, "chemistry_key"].astype(str)
            )
            train_mask = (
                ~source_doi.isin(test_articles | {article})
                & ~source_chemistry.isin(forbidden_chemistry)
            ).to_numpy()
            prediction, train_n = fit_predict(
                train_mask,
                target_x[prediction_indices],
                local_seed + stable_offset(f"dev:{article}") % 1_000_000,
            )
            feature[prediction_indices] = prediction
            dev_training_counts.append(train_n)

        test_chemistry = set(target.loc[test, "chemistry_key"].astype(str))
        final_train_mask = (
            ~source_doi.isin(test_articles) & ~source_chemistry.isin(test_chemistry)
        ).to_numpy()
        feature[test], final_train_n = fit_predict(
            final_train_mask,
            target_x[test],
            local_seed + 800_000,
        )
        if np.isnan(feature).any():
            raise AssertionError(f"Incomplete CALiSol source feature in {fold_id}")
        feature_by_fold[fold_id] = feature

        source_test_mask = source_doi.isin(test_articles).to_numpy()
        source_test_indices = np.flatnonzero(source_test_mask)
        source_test_chemistry = set(source.loc[source_test_indices, "chemistry_key"].astype(str))
        quality_train_mask = (
            ~source_doi.isin(test_articles) & ~source_chemistry.isin(source_test_chemistry)
        ).to_numpy()
        if len(source_test_indices):
            source_prediction, quality_train_n = fit_predict(
                quality_train_mask,
                source_x[source_test_indices],
                local_seed + 900_000,
            )
            fold_r2 = float(r2_score(y_source[source_test_indices], source_prediction))
            for position, source_index in enumerate(source_test_indices):
                quality_predictions.append(
                    {
                        "fold": fold_id,
                        "article_doi": str(source.loc[source_index, "doi"]),
                        "unit_key": str(source.loc[source_index, "unit_key"]),
                        "y": float(y_source[source_index]),
                        "prediction": float(source_prediction[position]),
                        "labels_shuffled": bool(shuffle_labels),
                    }
                )
        else:
            quality_train_n = int(quality_train_mask.sum())
            fold_r2 = np.nan
        quality_rows.append(
            {
                "fold": fold_id,
                "held_out_articles": len(test_articles),
                "held_out_article_dois": ";".join(sorted(test_articles)),
                "target_test_units": len(test),
                "source_test_units": len(source_test_indices),
                "source_training_units_for_target_test": final_train_n,
                "source_training_units_for_quality_test": quality_train_n,
                "minimum_source_training_units_for_development_prior": min(dev_training_counts),
                "source_test_articles_seen_during_fit": 0,
                "source_test_exact_chemistry_seen_during_fit": 0,
                "source_test_r2": fold_r2,
                "labels_shuffled": bool(shuffle_labels),
            }
        )
    quality = pd.DataFrame(quality_rows)
    quality_prediction_frame = pd.DataFrame(quality_predictions)
    if quality_prediction_frame.empty:
        pooled = float("nan")
    else:
        pooled = float(
            r2_score(quality_prediction_frame["y"], quality_prediction_frame["prediction"])
        )
    quality["pooled_source_article_oof_r2"] = pooled
    return feature_by_fold, quality, quality_prediction_frame


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
        model_seed = seed + stable_offset(f"target:{learner_label}:{fold_id}:{repeat}") % 1_000_000
        prediction = learner_factory(model_seed, n_jobs=1).fit(x[train], y[train]).predict(
            x[split["test"]]
        )
        return (fold_id, repeat), prediction

    fitted = Parallel(n_jobs=parallel_jobs, prefer="processes", verbose=0)(
        delayed(one_fit)(*job) for job in jobs
    )
    return dict(fitted)


def evaluate_edge(
    target: pd.DataFrame,
    x: np.ndarray,
    y: np.ndarray,
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
        model_seed = seed + stable_offset(f"target:{learner_label}:{fold_id}:{repeat}") % 1_000_000
        augmented = learner_factory(model_seed, n_jobs=1).fit(
            np.column_stack([x[train], feature[train]]), y[train]
        )
        if baseline_predictions is None:
            baseline = learner_factory(model_seed, n_jobs=1).fit(x[train], y[train])
            base_prediction = baseline.predict(x[test])
        else:
            base_prediction = baseline_predictions[(fold_id, repeat)]
        aug_prediction = augmented.predict(np.column_stack([x[test], feature[test]]))
        base_rmse = float(np.sqrt(np.mean((y[test] - base_prediction) ** 2)))
        aug_rmse = float(np.sqrt(np.mean((y[test] - aug_prediction) ** 2)))
        repeat_row = {
            "target": TARGET_ID,
            "source": source_label,
            "learner": learner_label,
            "fold": fold_id,
            "repeat": repeat,
            "train_n": len(train),
            "train_articles": int(target.loc[train, "doi"].nunique()),
            "test_n": len(test),
            "test_articles": int(target.loc[test, "doi"].nunique()),
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
                "target": TARGET_ID,
                "source": source_label,
                "learner": learner_label,
                "fold": fold_id,
                "repeat": repeat,
                "material_key": str(target.loc[index, "unit_key"]),
                "article_doi": str(target.loc[index, "doi"]),
                "chemistry_key": str(target.loc[index, "chemistry_key"]),
                "y": float(y[index]),
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
    return (
        pd.DataFrame([item[0] for item in results]),
        pd.DataFrame([row for item in results for row in item[1]]),
        pd.DataFrame([item[2] for item in results if item[2] is not None]),
    )


def summarize_article_hierarchical(
    predictions: pd.DataFrame, seed: int, n_boot: int
) -> dict[str, float]:
    values = predictions.copy()
    values["base_sse"] = (values["y"] - values["baseline"]) ** 2
    values["aug_sse"] = (values["y"] - values["augmented"]) ** 2
    repeats = sorted(values["repeat"].unique())
    matrices: dict[str, dict[str, np.ndarray]] = {}
    for article, group in values.groupby("article_doi", sort=True):
        keys = sorted(group["material_key"].unique())
        matrices[str(article)] = {
            column: (
                group.pivot(index="repeat", columns="material_key", values=column)
                .reindex(index=repeats, columns=keys)
                .to_numpy(float)
            )
            for column in ("base_sse", "aug_sse")
        }
    per_repeat = (
        values.groupby("repeat", as_index=False)
        .agg(base_sse=("base_sse", "sum"), aug_sse=("aug_sse", "sum"), n=("y", "size"))
    )
    base_rmse = np.sqrt(per_repeat["base_sse"] / per_repeat["n"])
    aug_rmse = np.sqrt(per_repeat["aug_sse"] / per_repeat["n"])
    relative = (base_rmse - aug_rmse) / base_rmse

    article_names = sorted(matrices)
    rng = np.random.default_rng(seed)
    boot = np.empty(n_boot, dtype=float)
    for iteration in range(n_boot):
        repeat_index = rng.integers(0, len(repeats), size=len(repeats))
        sampled_articles = rng.integers(0, len(article_names), size=len(article_names))
        base_total = aug_total = 0.0
        n_total = 0
        for article_index in sampled_articles:
            article = matrices[article_names[int(article_index)]]
            n_entities = article["base_sse"].shape[1]
            entity_index = rng.integers(0, n_entities, size=n_entities)
            base_total += article["base_sse"][repeat_index][:, entity_index].sum()
            aug_total += article["aug_sse"][repeat_index][:, entity_index].sum()
            n_total += len(repeat_index) * len(entity_index)
        base = np.sqrt(base_total / n_total)
        augmented = np.sqrt(aug_total / n_total)
        boot[iteration] = (base - augmented) / base
    output = {
        "base_rmse_mean": float(base_rmse.mean()),
        "aug_rmse_mean": float(aug_rmse.mean()),
        "relative_rmse_improvement_mean": float(relative.mean()),
        "relative_rmse_ci_lo": float(np.percentile(boot, 2.5)),
        "relative_rmse_ci_hi": float(np.percentile(boot, 97.5)),
        "pooled_base_r2": float(r2_score(values["y"], values["baseline"])),
        "pooled_aug_r2": float(r2_score(values["y"], values["augmented"])),
        "bootstrap_articles": len(article_names),
    }
    for fold, group in values.groupby("fold"):
        by_repeat = group.groupby("repeat").agg(
            base_sse=("base_sse", "sum"), aug_sse=("aug_sse", "sum"), n=("y", "size")
        )
        fold_base = np.sqrt(by_repeat["base_sse"] / by_repeat["n"])
        fold_aug = np.sqrt(by_repeat["aug_sse"] / by_repeat["n"])
        output[f"effect_{fold}"] = float(((fold_base - fold_aug) / fold_base).mean())
    return output


def learning_curve(
    target: pd.DataFrame,
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
            results = [
                (
                    repeat,
                    float(
                        np.sum(
                            (y[split["test"]] - baseline_predictions_at_30[(fold_id, repeat)]) ** 2
                        )
                    ),
                    len(split["test"]),
                )
                for fold_id, split in splits.items()
                for repeat in range(active_repeats)
            ]
        else:
            active_repeats = repeats
            budget_samples = build_samples(
                target,
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

            def one_fit(fold_id, split, repeat, train):
                model_seed = seed + stable_offset(f"curve:{budget}:{fold_id}:{repeat}") % 1_000_000
                prediction = target_forest(model_seed, n_jobs=1).fit(x[train], y[train]).predict(
                    x[split["test"]]
                )
                return repeat, float(np.sum((y[split["test"]] - prediction) ** 2)), len(
                    split["test"]
                )

            results = Parallel(n_jobs=parallel_jobs, prefer="processes", verbose=0)(
                delayed(one_fit)(*job) for job in jobs
            )
        repeat_sse = {repeat: [0.0, 0] for repeat in range(active_repeats)}
        for repeat, sse, n in results:
            repeat_sse[repeat][0] += sse
            repeat_sse[repeat][1] += n
        rmses = np.asarray([np.sqrt(sse / n) for sse, n in repeat_sse.values()])
        rows.append(
            {
                "target": TARGET_ID,
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


def stratified_mapping_permutation_test(
    target: pd.DataFrame,
    x: np.ndarray,
    y: np.ndarray,
    feature_by_fold: dict[str, np.ndarray],
    samples: dict[str, list[np.ndarray]],
    splits: dict[str, dict[str, np.ndarray]],
    permutations: int,
    seed: int,
    parallel_jobs: int,
) -> tuple[float, float, pd.DataFrame]:
    baseline_sse = observed_aug_sse = 0.0
    fixed: list[tuple[str, np.ndarray, np.ndarray, np.ndarray, int]] = []
    groups = target["doi"].astype(str).to_numpy()
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
        fixed.append((fold_id, train, test, feature, model_seed))
    observed = (baseline_sse - observed_aug_sse) / baseline_sse

    def permute_within(values: np.ndarray, indices: np.ndarray, rng: np.random.Generator) -> np.ndarray:
        output = values[indices].copy()
        local_groups = groups[indices]
        for group in sorted(set(local_groups)):
            positions = np.flatnonzero(local_groups == group)
            output[positions] = output[positions][rng.permutation(len(positions))]
        return output

    def one_permutation(permutation: int) -> float:
        rng = np.random.default_rng(seed + 10_000 + permutation)
        augmented_sse = 0.0
        for _, train, test, feature, model_seed in fixed:
            permuted_train = permute_within(feature, train, rng)
            permuted_test = permute_within(feature, test, rng)
            augmented = target_forest(model_seed, n_jobs=1).fit(
                np.column_stack([x[train], permuted_train]), y[train]
            )
            prediction = augmented.predict(np.column_stack([x[test], permuted_test]))
            augmented_sse += float(np.sum((y[test] - prediction) ** 2))
        return (baseline_sse - augmented_sse) / baseline_sse

    null_values = Parallel(n_jobs=parallel_jobs, prefer="processes", verbose=0)(
        delayed(one_permutation)(permutation) for permutation in range(permutations)
    )
    null = pd.DataFrame(
        {
            "permutation": np.arange(permutations, dtype=int),
            "relative_mse_improvement": null_values,
            "observed_relative_mse_improvement": float(observed),
            "fixed_target_subset_repeat": 0,
            "permutation_strata": "source_article_doi",
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
    parser.add_argument("--quick", action="store_true", help="Smoke test; writes quick artifacts only")
    parser.add_argument("--jobs", type=int, default=-1)
    args = parser.parse_args()
    ensure_output_dirs()
    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    inference = design["inference"]
    run = quick_or_full(design, args.quick)
    seed = int(design["seed"])
    prefix = "quick_calisol_external" if args.quick else "calisol_external"

    raw = load_raw(design)
    target, sources, x, source_x, feature_names, structure = prepare_tasks(raw, design)
    splits, fold_frame = article_splits(target)
    y = target["value"].to_numpy(float)
    target_groups = target["doi"].astype(str).to_numpy()
    samples = build_samples(
        target,
        splits,
        int(design["split"]["target_budget_per_fold"]),
        run["target_repeats"],
        seed,
    )

    primary_temperature = int(inference["primary_source_temperature_C"])
    control_temperatures = [int(value) for value in inference["negative_control_source_temperatures_C"]]
    features: dict[str, dict[str, np.ndarray]] = {}
    source_quality_frames: list[pd.DataFrame] = []
    source_prediction_frames: list[pd.DataFrame] = []
    placebo_label = f"shuffled_temperature_{primary_temperature}_C"
    source_specs = [
        (f"temperature_{temperature}_C", temperature, False)
        for temperature in [primary_temperature, *control_temperatures]
    ] + [(placebo_label, primary_temperature, True)]

    def one_source_run(label: str, temperature: int, shuffled: bool):
        return label, temperature, source_features_for_target(
            target,
            sources[temperature],
            x,
            source_x[temperature],
            splits,
            seed + stable_offset(label) % 1_000_000,
            shuffle_labels=shuffled,
        )

    available_jobs = 5 if args.jobs < 0 else max(1, min(int(args.jobs), 5))
    source_runs = Parallel(n_jobs=available_jobs, prefer="processes", verbose=0)(
        delayed(one_source_run)(*spec) for spec in source_specs
    )
    for label, source_temperature, (feature, quality, quality_predictions) in source_runs:
        features[label] = feature
        for frame in (quality, quality_predictions):
            frame["source"] = label
            frame["source_temperature_C"] = source_temperature
            frame["target_temperature_C"] = int(design["split"]["target_temperature_C"])
        source_quality_frames.append(quality)
        source_prediction_frames.append(quality_predictions)
    source_quality = pd.concat(source_quality_frames, ignore_index=True)
    source_quality_predictions = pd.concat(source_prediction_frames, ignore_index=True)

    baseline_predictions = precompute_baseline_predictions(
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
    repeat_frames: list[pd.DataFrame] = []
    prediction_frames: list[pd.DataFrame] = []
    importance_frames: list[pd.DataFrame] = []
    edge_labels = [
        *[f"temperature_{temperature}_C" for temperature in [primary_temperature, *control_temperatures]],
        placebo_label,
    ]
    for label in edge_labels:
        repeats, predictions, importance = evaluate_edge(
            target,
            x,
            y,
            features[label],
            samples,
            splits,
            target_forest,
            "random-forest-primary",
            label,
            seed,
            args.jobs,
            baseline_predictions,
        )
        summary = summarize_article_hierarchical(
            predictions,
            seed + stable_offset(f"bootstrap:{label}") % 1_000_000,
            run["bootstrap"],
        )
        source_temperature = primary_temperature if label == placebo_label else int(
            label.removeprefix("temperature_").removesuffix("_C")
        )
        quality = source_quality[source_quality["source"] == label]
        summary.update(
            {
                "target": TARGET_ID,
                "source": label,
                "target_temperature_C": int(design["split"]["target_temperature_C"]),
                "source_temperature_C": source_temperature,
                "absolute_temperature_distance_C": abs(
                    source_temperature - int(design["split"]["target_temperature_C"])
                ),
                "relation": (
                    "shuffled-source-placebo"
                    if label == placebo_label
                    else (
                        "adjacent-condition-primary"
                        if source_temperature == primary_temperature
                        else "temperature-distance-control"
                    )
                ),
                "train_n": int(design["split"]["target_budget_per_fold"]),
                "target_units": len(target),
                "target_articles": int(target["doi"].nunique()),
                "source_test_articles_seen_during_fit": 0,
                "source_test_exact_chemistry_seen_during_fit": 0,
                "source_pooled_article_oof_r2": float(quality["pooled_source_article_oof_r2"].iloc[0]),
            }
        )
        edge_rows.append(summary)
        repeat_frames.append(repeats)
        prediction_frames.append(predictions)
        if not importance.empty:
            importance_frames.append(importance)
    edges = pd.DataFrame(edge_rows)

    curve = learning_curve(
        target,
        x,
        y,
        samples,
        splits,
        [int(value) for value in inference["learning_curve_budgets"]],
        run["curve_repeats"],
        seed + stable_offset("calisol-learning-curve"),
        args.jobs,
        baseline_predictions,
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
    p_value, observed_permutation_statistic, permutation_null = stratified_mapping_permutation_test(
        target,
        x,
        y,
        features[primary_label],
        samples,
        splits,
        run["permutations"],
        seed + stable_offset("calisol-primary-permutation"),
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
        ("ridge-sensitivity", target_ridge),
    ):
        repeats, predictions, importance = evaluate_edge(
            target,
            x,
            y,
            features[primary_label],
            sensitivity_samples,
            splits,
            learner_factory,
            learner_label,
            primary_label,
            seed,
            args.jobs,
        )
        item = summarize_article_hierarchical(
            predictions,
            seed + stable_offset(f"sensitivity:{learner_label}") % 1_000_000,
            run["bootstrap"],
        )
        item["learner"] = learner_label
        sensitivity_rows.append(item)
        repeat_frames.append(repeats)
        prediction_frames.append(predictions)
        if not importance.empty:
            importance_frames.append(importance)
    sensitivity = pd.DataFrame(sensitivity_rows)

    primary = edges[edges["source"] == primary_label].iloc[0]
    placebo = edges[edges["source"] == placebo_label].iloc[0]
    positive_learners = int(primary["relative_rmse_improvement_mean"] > 0) + int(
        (sensitivity["relative_rmse_improvement_mean"] > 0).sum()
    )
    temperature_edges = edges[edges["relation"] != "shuffled-source-placebo"].sort_values(
        "absolute_temperature_distance_C"
    )
    effects = temperature_edges["relative_rmse_improvement_mean"].to_numpy(float)
    distances = temperature_edges["absolute_temperature_distance_C"].to_numpy(float)
    distance_rho = float(stats.spearmanr(distances, effects).statistic)
    strict_distance_order = bool(np.all(np.diff(effects) < 0))
    fold_effects = [float(primary[f"effect_fold_{fold}"]) for fold in range(5)]
    gates = {
        "relative_rmse_at_least_5pct": bool(
            primary["relative_rmse_improvement_mean"]
            >= float(inference["minimum_relative_rmse_reduction"])
        ),
        "article_hierarchical_bootstrap_ci_above_zero": bool(primary["relative_rmse_ci_lo"] > 0),
        "positive_augmented_r2": bool(primary["pooled_aug_r2"] > 0),
        "positive_effect_in_all_five_article_folds": bool(all(value > 0 for value in fold_effects)),
        "target_sample_fraction_saved_at_least_30pct": bool(
            primary["target_sample_fraction_saved"]
            >= float(inference["minimum_target_sample_fraction_saved"])
        ),
        "at_least_two_of_three_target_learners_positive": bool(
            positive_learners >= int(inference["minimum_positive_learners_of_three"])
        ),
        "source_article_oof_r2_positive": bool(primary["source_pooled_article_oof_r2"] > 0),
        "zero_test_articles_seen_by_source_model": bool(
            primary["source_test_articles_seen_during_fit"] == 0
        ),
        "zero_exact_test_chemistries_seen_by_source_model": bool(
            primary["source_test_exact_chemistry_seen_during_fit"] == 0
        ),
        "article_stratified_permutation_p_below_0_05": bool(p_value < 0.05),
        "learning_curve_valid_for_equivalence": bool(curve["valid_for_target_equivalence"].iloc[0]),
        "primary_exceeds_each_distant_temperature_control": bool(
            primary["relative_rmse_improvement_mean"]
            > temperature_edges[temperature_edges["source"] != primary_label][
                "relative_rmse_improvement_mean"
            ].max()
        ),
        "effect_strictly_decreases_with_temperature_distance": strict_distance_order,
        "shuffled_source_not_positive_at_95pct": bool(placebo["relative_rmse_ci_lo"] <= 0),
        "shuffled_source_smaller_than_primary": bool(
            placebo["relative_rmse_improvement_mean"] < primary["relative_rmse_improvement_mean"]
        ),
    }
    rescue_supported = bool(all(gates.values()))
    if rescue_supported:
        decision = "independent-multi-article-local-rescue-gate-passed"
    elif primary["relative_rmse_ci_hi"] < 0:
        decision = "adjacent-source-harmful-across-articles"
    elif primary["relative_rmse_ci_lo"] > 0 and primary["pooled_aug_r2"] > 0:
        decision = "directional-cross-article-borrowing-below-full-rescue-gate"
    else:
        decision = "cross-article-borrowing-unresolved"
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

    all_repeats = pd.concat(repeat_frames, ignore_index=True)
    all_predictions = pd.concat(prediction_frames, ignore_index=True)
    all_importance = (
        pd.concat(importance_frames, ignore_index=True) if importance_frames else pd.DataFrame()
    )
    structure.to_csv(RESULTS / f"{prefix}_temperature_structure.csv", index=False)
    fold_frame.to_csv(RESULTS / f"{prefix}_outer_folds.csv", index=False)
    source_quality.to_csv(RESULTS / f"{prefix}_source_quality.csv", index=False)
    source_quality_predictions.to_csv(
        RESULTS / f"{prefix}_source_quality_predictions.csv", index=False
    )
    edges.to_csv(RESULTS / f"{prefix}_edges.csv", index=False)
    curve.to_csv(RESULTS / f"{prefix}_learning_curve.csv", index=False)
    sensitivity.to_csv(RESULTS / f"{prefix}_sensitivity.csv", index=False)
    all_repeats.to_csv(RESULTS / f"{prefix}_repeats.csv", index=False)
    all_predictions.to_csv(RESULTS / f"{prefix}_predictions.csv", index=False)
    if not all_importance.empty:
        all_importance.to_csv(RESULTS / f"{prefix}_feature_importance.csv", index=False)
    permutation_null.to_csv(RESULTS / f"{prefix}_permutation_null.csv", index=False)

    primary_importance = all_importance[
        (all_importance["source"] == primary_label)
        & (all_importance["learner"] == "random-forest-primary")
    ]
    summary = {
        "analysis_status": design["status"],
        "interpretation_scope": "independent multi-article local-condition replication within liquid-electrolyte conductivity; not cross-domain field rescue",
        "raw_rows": len(raw),
        "literature_articles": int(raw["doi"].nunique()),
        "target_units": len(target),
        "target_articles": int(target["doi"].nunique()),
        "composition_features_after_one_hot_encoding": len(feature_names),
        "outer_folds": len(splits),
        "target_temperature_C": int(design["split"]["target_temperature_C"]),
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
        "permutation_observed_relative_mse_improvement": float(observed_permutation_statistic),
        "positive_target_learners_of_three": int(positive_learners),
        "source_article_oof_r2": float(primary["source_pooled_article_oof_r2"]),
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
        "test_articles_seen_by_source_model": 0,
        "exact_test_chemistries_seen_by_source_model": 0,
        "article_doi_used_as_predictor": False,
        "temperature_or_curve_fit_features_used": False,
        "quick_smoke_test": bool(args.quick),
        "gates": gates,
        "rescue_claim_supported": rescue_supported,
        "decision": decision,
    }
    (RESULTS / f"{prefix}_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print("\nCALiSol cross-article edges")
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
