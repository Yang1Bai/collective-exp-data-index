"""Outcome-informed local screen for state-matched MPEA knowledge borrowing.

The target is experimental yield strength (YS); the neighboring donor endpoint
is ultimate tensile strength (UTS).  Elemental systems are kept intact across
the split.  Donor predictions used on target-training rows are cross-fitted by
elemental system, so their information contract matches genuinely unseen
evaluation systems.

This is method development.  It must not be presented as confirmatory evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from scipy import stats
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from common import DB, RESULTS, composition_features, ensure_output_dirs, sample_groups
from run_knowledge_map import balanced_group_partition
from scripts.localdb.build_localdb import canonical_formula


HERE = Path(__file__).resolve().parent
DESIGN_PATH = HERE / "state_matched_mpea_borrowing_design.json"
OUTPUT = RESULTS / "state_matched_mpea_borrowing_screen.csv"
PREDICTION_OUTPUT = RESULTS / "state_matched_mpea_borrowing_predictions.csv"
SUMMARY = RESULTS / "state_matched_mpea_borrowing_summary.json"

YS_COLUMN = "PROPERTY: YS (MPa)"
UTS_COLUMN = "PROPERTY: UTS (MPa)"
FORMULA_COLUMN = "FORMULA"
COMP_PREFIX = "composition_"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int)
    parser.add_argument("--trees", type=int)
    parser.add_argument("--design-path", type=Path, default=DESIGN_PATH)
    parser.add_argument("--output-prefix", default="state_matched_mpea_borrowing")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def stable_seed(*parts: Any) -> int:
    digest = hashlib.sha256("|".join(map(str, parts)).encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "little")


def elemental_system(key: str) -> str:
    return "|".join(sorted(token.split(":", 1)[0] for token in key.split("|")))


def load_raw() -> pd.DataFrame:
    with sqlite3.connect(DB) as connection:
        raw = pd.read_sql("SELECT rowid AS raw_row_id, * FROM raw_mpea", connection)
    parsed = raw[FORMULA_COLUMN].map(canonical_formula)
    raw["material_key"] = parsed.map(lambda item: item[0])
    raw["canonicalization_flag"] = parsed.map(lambda item: item[1])
    raw = raw[raw["material_key"].notna()].copy()
    raw["group"] = raw["material_key"].map(elemental_system)
    comp = composition_features(raw["material_key"].astype(str).tolist())
    comp_frame = pd.DataFrame(
        comp,
        index=raw.index,
        columns=[f"{COMP_PREFIX}{index:03d}" for index in range(comp.shape[1])],
    )
    return pd.concat([raw, comp_frame], axis=1).reset_index(drop=True)


def task_frame(raw: pd.DataFrame, outcome: str) -> pd.DataFrame:
    frame = raw.copy()
    frame["value_raw"] = pd.to_numeric(frame[outcome], errors="coerce")
    frame = frame[np.isfinite(frame["value_raw"]) & (frame["value_raw"] > 0)].copy()
    frame["value"] = np.log10(frame["value_raw"].to_numpy(float))
    return frame.reset_index(drop=True)


def feature_columns(design: dict[str, Any], contract: str) -> tuple[list[str], list[str]]:
    comp = [column for column in design["_all_columns"] if column.startswith(COMP_PREFIX)]
    spec = design["deployment_contracts"][contract]
    numeric = comp + list(spec["numeric"])
    categorical = list(spec["categorical"])
    return numeric, categorical


def preprocessing(numeric: Sequence[str], categorical: Sequence[str]) -> ColumnTransformer:
    transformers: list[tuple[str, Any, Sequence[str]]] = [
        (
            "numeric",
            Pipeline(
                [
                    ("impute", SimpleImputer(strategy="median", keep_empty_features=True)),
                    ("scale", StandardScaler()),
                ]
            ),
            list(numeric),
        )
    ]
    if categorical:
        transformers.append(
            (
                "categorical",
                Pipeline(
                    [
                        (
                            "impute",
                            SimpleImputer(
                                strategy="most_frequent",
                                keep_empty_features=True,
                            ),
                        ),
                        (
                            "onehot",
                            OneHotEncoder(
                                handle_unknown="ignore",
                                sparse_output=False,
                            ),
                        ),
                    ]
                ),
                list(categorical),
            )
        )
    return ColumnTransformer(transformers, remainder="drop")


def learner(name: str, seed: int, trees: int):
    if name == "ridge_alpha_10":
        return Ridge(alpha=10.0, solver="lsqr")
    if name == "random_forest":
        return RandomForestRegressor(
            n_estimators=trees,
            min_samples_leaf=2,
            max_features=0.7,
            random_state=seed,
            n_jobs=-1,
        )
    if name == "extra_trees":
        return ExtraTreesRegressor(
            n_estimators=trees,
            min_samples_leaf=2,
            max_features=0.7,
            random_state=seed,
            n_jobs=-1,
        )
    raise ValueError(name)


def model(
    name: str,
    numeric: Sequence[str],
    categorical: Sequence[str],
    seed: int,
    trees: int,
) -> Pipeline:
    return Pipeline(
        [
            ("features", preprocessing(numeric, categorical)),
            ("model", learner(name, seed, trees)),
        ]
    )


def source_model(
    numeric: Sequence[str],
    categorical: Sequence[str],
    seed: int,
    trees: int,
) -> Pipeline:
    return model("extra_trees", numeric, categorical, seed, trees)


def shuffled(values: np.ndarray, seed: int) -> np.ndarray:
    output = np.asarray(values, dtype=float).copy()
    np.random.default_rng(seed).shuffle(output)
    return output


def crossfitted_donor_signal(
    source: pd.DataFrame,
    target_train: pd.DataFrame,
    target_eval: pd.DataFrame,
    numeric: Sequence[str],
    categorical: Sequence[str],
    seed: int,
    trees: int,
    *,
    shuffle_outcome: bool,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    """Return system-cross-fitted train and final evaluation UTS predictions."""
    eval_groups = set(target_eval["group"].astype(str))
    train_groups = target_train["group"].astype(str).to_numpy()
    unique = np.unique(train_groups)
    folds = min(5, len(unique))
    if folds < 2:
        raise RuntimeError("Too few target-training systems for donor cross-fitting")
    prediction_train = np.full(len(target_train), np.nan)
    splitter = GroupKFold(n_splits=folds)
    dummy = np.zeros(len(target_train))
    fold_training_sizes: list[int] = []
    for fold_id, (_, held) in enumerate(splitter.split(dummy, dummy, train_groups)):
        held_groups = set(train_groups[held])
        keep = ~source["group"].astype(str).isin(eval_groups | held_groups)
        source_fit = source.loc[keep]
        if len(source_fit) < 30:
            raise RuntimeError(f"Only {len(source_fit)} source rows remain in donor fold")
        y_fit = source_fit["value"].to_numpy(float)
        if shuffle_outcome:
            y_fit = shuffled(y_fit, stable_seed(seed, "shuffle", fold_id))
        fitted = source_model(
            numeric,
            categorical,
            stable_seed(seed, "donor-fold", fold_id),
            trees,
        ).fit(source_fit, y_fit)
        prediction_train[held] = fitted.predict(target_train.iloc[held])
        fold_training_sizes.append(len(source_fit))
    if not np.isfinite(prediction_train).all():
        raise AssertionError("Incomplete cross-fitted donor predictions")

    keep_final = ~source["group"].astype(str).isin(eval_groups)
    source_final = source.loc[keep_final]
    y_final = source_final["value"].to_numpy(float)
    if shuffle_outcome:
        y_final = shuffled(y_final, stable_seed(seed, "shuffle-final"))
    fitted_final = source_model(
        numeric,
        categorical,
        stable_seed(seed, "donor-final"),
        trees,
    ).fit(source_final, y_final)
    prediction_eval = fitted_final.predict(target_eval)
    audit = {
        "source_final_n": int(len(source_final)),
        "source_final_groups": int(source_final["group"].nunique()),
        "source_fold_min_n": int(min(fold_training_sizes)),
        "source_fold_max_n": int(max(fold_training_sizes)),
        "evaluation_groups_excluded": int(len(eval_groups)),
    }
    return prediction_train, prediction_eval, audit


def source_group_oof_quality(
    source: pd.DataFrame,
    allowed_groups: set[str],
    numeric: Sequence[str],
    categorical: Sequence[str],
    seed: int,
    trees: int,
) -> float:
    subset = source[source["group"].astype(str).isin(allowed_groups)].reset_index(drop=True)
    groups = subset["group"].astype(str).to_numpy()
    splits = min(5, len(np.unique(groups)))
    if splits < 2:
        return float("nan")
    prediction = np.full(len(subset), np.nan)
    dummy = np.zeros(len(subset))
    for fold_id, (fit_index, held_index) in enumerate(
        GroupKFold(n_splits=splits).split(dummy, dummy, groups)
    ):
        fitted = source_model(
            numeric,
            categorical,
            stable_seed(seed, "source-quality", fold_id),
            trees,
        ).fit(subset.iloc[fit_index], subset.iloc[fit_index]["value"])
        prediction[held_index] = fitted.predict(subset.iloc[held_index])
    return float(r2_score(subset["value"], prediction))


def composition_quartiles(
    train: pd.DataFrame,
    evaluation: pd.DataFrame,
    comp_columns: Sequence[str],
) -> tuple[dict[int, str], dict[int, float]]:
    scaler = StandardScaler().fit(train[list(comp_columns)])
    train_x = scaler.transform(train[list(comp_columns)])
    eval_x = scaler.transform(evaluation[list(comp_columns)])
    distances = cdist(eval_x, train_x).min(axis=1)
    work = evaluation[["group"]].copy()
    work["local_index"] = np.arange(len(evaluation))
    work["distance"] = distances
    grouped = (
        work.groupby("group", as_index=False)
        .agg(distance=("distance", "median"))
        .assign(
            tie=lambda value: value["group"].map(
                lambda group: stable_seed("quartile", group)
            )
        )
        .sort_values(["distance", "tie", "group"], kind="mergesort")
        .reset_index(drop=True)
    )
    scope_by_group: dict[str, str] = {}
    for quartile, positions in enumerate(np.array_split(np.arange(len(grouped)), 4), 1):
        for position in positions:
            scope_by_group[str(grouped.at[int(position), "group"])] = f"q{quartile}"
    scopes = {
        int(row.local_index): scope_by_group[str(row.group)]
        for row in work.itertuples()
    }
    distance_map = {
        int(row.local_index): float(row.distance)
        for row in work.itertuples()
    }
    return scopes, distance_map


def metrics(y: np.ndarray, baseline: np.ndarray, augmented: np.ndarray) -> dict[str, float]:
    base_rmse = math.sqrt(mean_squared_error(y, baseline))
    aug_rmse = math.sqrt(mean_squared_error(y, augmented))
    return {
        "n": int(len(y)),
        "base_rmse": float(base_rmse),
        "aug_rmse": float(aug_rmse),
        "relative_rmse_gain": float((base_rmse - aug_rmse) / base_rmse),
        "base_r2": float(r2_score(y, baseline)),
        "aug_r2": float(r2_score(y, augmented)),
        "delta_r2": float(r2_score(y, augmented) - r2_score(y, baseline)),
        "delta_mae": float(
            mean_absolute_error(y, baseline) - mean_absolute_error(y, augmented)
        ),
    }


def fit_predictions(
    target_train: pd.DataFrame,
    target_eval: pd.DataFrame,
    y_train: np.ndarray,
    numeric: list[str],
    categorical: list[str],
    learner_name: str,
    seed: int,
    trees: int,
    donor_train: np.ndarray,
    donor_eval: np.ndarray,
) -> dict[str, np.ndarray]:
    state = model(learner_name, numeric, categorical, seed, trees)
    state.fit(target_train, y_train)
    state_prediction = state.predict(target_eval)

    concat_train = target_train.copy()
    concat_eval = target_eval.copy()
    concat_train["_predicted_uts"] = donor_train
    concat_eval["_predicted_uts"] = donor_eval
    concat = model(
        learner_name,
        [*numeric, "_predicted_uts"],
        categorical,
        stable_seed(seed, "concat"),
        trees,
    )
    concat.fit(concat_train, y_train)

    residual = model(
        learner_name,
        numeric,
        categorical,
        stable_seed(seed, "residual"),
        trees,
    )
    residual.fit(target_train, y_train - donor_train)
    residual_prediction = donor_eval + residual.predict(target_eval)
    return {
        "state_only": state_prediction,
        "state_plus_crossfitted_predicted_uts": concat.predict(concat_eval),
        "predicted_uts_residual_anchor": residual_prediction,
    }


def summarize(rows: pd.DataFrame, design: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    summary_rows: list[dict[str, Any]] = []
    keys = ["contract", "budget", "method", "scope"]
    for values, group in rows.groupby(keys, dropna=False):
        labels = {
            key: (value.item() if isinstance(value, np.generic) else value)
            for key, value in zip(keys, values)
        }
        gains = group["relative_rmse_gain"].to_numpy(float)
        if len(gains) > 1:
            sem = stats.sem(gains)
            critical = stats.t.ppf(0.975, len(gains) - 1)
            ci = [float(gains.mean() - critical * sem), float(gains.mean() + critical * sem)]
        else:
            ci = [float("nan"), float("nan")]
        summary_rows.append(
            {
                **labels,
                "runs": int(len(group)),
                "mean_relative_rmse_gain": float(gains.mean()),
                "ci95": ci,
                "positive_runs": int((gains > 0).sum()),
                "mean_base_r2": float(group["base_r2"].mean()),
                "mean_aug_r2": float(group["aug_r2"].mean()),
                "mean_delta_r2": float(group["delta_r2"].mean()),
            }
        )

    screen = design["screen"]
    gate_spec = design["balam_escalation_gate"]
    primary = pd.DataFrame(summary_rows)
    query = (
        (primary["contract"] == screen["primary_contract"])
        & (primary["budget"] == screen["primary_budget"])
        & (primary["method"] == screen["primary_method"])
    )
    cells = primary.loc[query].set_index("scope")
    q4 = cells.loc["q4"]
    q1 = cells.loc["q1"]
    shuffled = primary[
        (primary["contract"] == screen["primary_contract"])
        & (primary["budget"] == screen["primary_budget"])
        & (
            primary["method"]
            == screen.get(
                "shuffled_control_method",
                "shuffled_uts_residual_anchor",
            )
        )
        & (primary["scope"] == "q4")
    ].iloc[0]
    checks = {
        "mean_q4_gain": bool(
            q4["mean_relative_rmse_gain"]
            >= gate_spec["mean_q4_relative_rmse_gain_at_least"]
        ),
        "positive_q4_runs": bool(
            q4["positive_runs"] >= gate_spec["positive_q4_runs_at_least"]
        ),
        "positive_q4_r2": bool(q4["mean_aug_r2"] > 0),
        "ood_specificity": bool(
            q4["mean_relative_rmse_gain"] > q1["mean_relative_rmse_gain"]
        ),
        "beats_shuffled": bool(
            q4["mean_relative_rmse_gain"] > shuffled["mean_relative_rmse_gain"]
        ),
    }
    gate = {
        "checks": checks,
        "pass": bool(all(checks.values())),
        "decision": (
            "eligible-for-frozen-balam-confirmation"
            if all(checks.values())
            else "do-not-submit-balam"
        ),
    }
    return summary_rows, gate


def main() -> None:
    args = parse_args()
    ensure_output_dirs()
    design_path = args.design_path.resolve()
    output = RESULTS / f"{args.output_prefix}_screen.csv"
    prediction_output = RESULTS / f"{args.output_prefix}_predictions.csv"
    summary_output = RESULTS / f"{args.output_prefix}_summary.json"
    if any(path.exists() for path in [output, prediction_output, summary_output]) and not args.overwrite:
        raise FileExistsError("Outputs already exist; pass --overwrite")
    design_text = design_path.read_text(encoding="utf-8")
    design = json.loads(design_text)
    raw = load_raw()
    design["_all_columns"] = list(raw.columns)
    target = task_frame(raw, YS_COLUMN)
    source = task_frame(raw, UTS_COLUMN)
    comp_columns = [column for column in raw if column.startswith(COMP_PREFIX)]

    partition_seed = int(design["data"]["partition"]["seed"])
    development_index, discovery_index, confirmation_index = balanced_group_partition(
        target,
        (
            float(design["data"]["partition"]["development"]),
            float(design["data"]["partition"]["discovery"]),
            float(design["data"]["partition"]["confirmation"]),
        ),
        partition_seed,
        "group",
    )
    evaluation_index = np.sort(np.r_[discovery_index, confirmation_index])
    development = target.loc[development_index].reset_index(drop=True)
    evaluation = target.loc[evaluation_index].reset_index(drop=True)
    if set(development["group"]) & set(evaluation["group"]):
        raise AssertionError("Elemental-system leakage across target split")

    repeats = args.repeats or int(design["screen"]["repeats"])
    trees = args.trees or int(design["screen"]["tree_estimators"])
    rows: list[dict[str, Any]] = []
    prediction_rows: list[dict[str, Any]] = []
    donor_quality: dict[str, float] = {}
    audits: list[dict[str, Any]] = []

    for contract in design["deployment_contracts"]:
        numeric, categorical = feature_columns(design, contract)
        allowed_source_groups = set(development["group"].astype(str))
        donor_quality[contract] = source_group_oof_quality(
            source,
            allowed_source_groups,
            numeric,
            categorical,
            stable_seed(partition_seed, contract),
            trees,
        )
        for budget in design["screen"]["target_label_budgets"]:
            for repeat in range(repeats):
                rng = np.random.default_rng(stable_seed(partition_seed, contract, budget, repeat))
                local = sample_groups(
                    development["group"].astype(str).to_numpy(),
                    int(budget),
                    rng,
                )
                train = development.iloc[local].reset_index(drop=True)
                scopes, distances = composition_quartiles(train, evaluation, comp_columns)
                real_train, real_eval, audit = crossfitted_donor_signal(
                    source,
                    train,
                    evaluation,
                    numeric,
                    categorical,
                    stable_seed(partition_seed, contract, budget, repeat, "real"),
                    trees,
                    shuffle_outcome=False,
                )
                wrong_train, wrong_eval, _ = crossfitted_donor_signal(
                    source,
                    train,
                    evaluation,
                    numeric,
                    categorical,
                    stable_seed(partition_seed, contract, budget, repeat, "shuffle"),
                    trees,
                    shuffle_outcome=True,
                )
                audits.append(
                    {
                        "contract": contract,
                        "budget": int(budget),
                        "repeat": repeat,
                        "target_train_n": int(len(train)),
                        "target_train_groups": int(train["group"].nunique()),
                        **audit,
                    }
                )
                y_train = train["value"].to_numpy(float)
                y_eval = evaluation["value"].to_numpy(float)
                composition_numeric = list(comp_columns)
                for learner_name in design["screen"]["learners"]:
                    seed = stable_seed(
                        partition_seed, contract, budget, repeat, learner_name
                    )
                    comp_fit = model(
                        learner_name,
                        composition_numeric,
                        [],
                        stable_seed(seed, "composition"),
                        trees,
                    ).fit(train, y_train)
                    comp_prediction = comp_fit.predict(evaluation)
                    real_predictions = fit_predictions(
                        train,
                        evaluation,
                        y_train,
                        numeric,
                        categorical,
                        learner_name,
                        seed,
                        trees,
                        real_train,
                        real_eval,
                    )
                    wrong_predictions = fit_predictions(
                        train,
                        evaluation,
                        y_train,
                        numeric,
                        categorical,
                        learner_name,
                        seed,
                        trees,
                        wrong_train,
                        wrong_eval,
                    )
                    shuffled_residual = model(
                        learner_name,
                        numeric,
                        categorical,
                        stable_seed(seed, "shuffled-residual"),
                        trees,
                    ).fit(train, y_train - wrong_train)
                    shuffled_prediction = wrong_eval + shuffled_residual.predict(evaluation)

                    contrasts = {
                        "state_only": (comp_prediction, real_predictions["state_only"]),
                        "state_plus_crossfitted_predicted_uts": (
                            real_predictions["state_only"],
                            real_predictions["state_plus_crossfitted_predicted_uts"],
                        ),
                        "predicted_uts_residual_anchor": (
                            real_predictions["state_only"],
                            real_predictions["predicted_uts_residual_anchor"],
                        ),
                        "state_plus_crossfitted_shuffled_uts": (
                            real_predictions["state_only"],
                            wrong_predictions[
                                "state_plus_crossfitted_predicted_uts"
                            ],
                        ),
                        "shuffled_uts_residual_anchor": (
                            real_predictions["state_only"],
                            shuffled_prediction,
                        ),
                    }
                    scope_indices = {
                        "all": np.arange(len(evaluation), dtype=int),
                        **{
                            scope: np.asarray(
                                [index for index in range(len(evaluation)) if scopes[index] == scope],
                                dtype=int,
                            )
                            for scope in ("q1", "q2", "q3", "q4")
                        },
                    }
                    for method_name, (baseline, augmented) in contrasts.items():
                        for scope, indices in scope_indices.items():
                            result = metrics(
                                y_eval[indices],
                                baseline[indices],
                                augmented[indices],
                            )
                            rows.append(
                                {
                                    "contract": contract,
                                    "budget": int(budget),
                                    "repeat": repeat,
                                    "learner": learner_name,
                                    "method": method_name,
                                    "scope": scope,
                                    **result,
                                }
                            )
                    for index, row in evaluation.iterrows():
                        prediction_rows.append(
                            {
                                "contract": contract,
                                "budget": int(budget),
                                "repeat": repeat,
                                "learner": learner_name,
                                "raw_row_id": int(row["raw_row_id"]),
                                "material_key": row["material_key"],
                                "group": row["group"],
                                "scope": scopes[index],
                                "composition_distance": distances[index],
                                "observed_log10_ys": y_eval[index],
                                "composition_only": comp_prediction[index],
                                "state_only": real_predictions["state_only"][index],
                                "state_plus_predicted_uts": real_predictions[
                                    "state_plus_crossfitted_predicted_uts"
                                ][index],
                                "predicted_uts_residual_anchor": real_predictions[
                                    "predicted_uts_residual_anchor"
                                ][index],
                                "state_plus_shuffled_uts": wrong_predictions[
                                    "state_plus_crossfitted_predicted_uts"
                                ][index],
                                "shuffled_uts_residual_anchor": shuffled_prediction[index],
                                "predicted_log10_uts": real_eval[index],
                            }
                        )

                # Separate auxiliary-measurement ceiling on paired rows.
                paired_train_pool = development[
                    pd.to_numeric(development[UTS_COLUMN], errors="coerce").gt(0)
                ].reset_index(drop=True)
                paired_eval = evaluation[
                    pd.to_numeric(evaluation[UTS_COLUMN], errors="coerce").gt(0)
                ].reset_index(drop=True)
                if len(paired_train_pool) >= 15 and len(paired_eval) >= 12:
                    paired_local = sample_groups(
                        paired_train_pool["group"].astype(str).to_numpy(),
                        int(budget),
                        np.random.default_rng(
                            stable_seed(partition_seed, contract, budget, repeat, "paired")
                        ),
                    )
                    paired_train = paired_train_pool.iloc[paired_local].reset_index(drop=True)
                    paired_scopes, _ = composition_quartiles(
                        paired_train, paired_eval, comp_columns
                    )
                    paired_train["_measured_uts"] = np.log10(
                        pd.to_numeric(paired_train[UTS_COLUMN]).to_numpy(float)
                    )
                    paired_eval["_measured_uts"] = np.log10(
                        pd.to_numeric(paired_eval[UTS_COLUMN]).to_numpy(float)
                    )
                    paired_y_train = paired_train["value"].to_numpy(float)
                    paired_y_eval = paired_eval["value"].to_numpy(float)
                    for learner_name in design["screen"]["learners"]:
                        seed = stable_seed(
                            partition_seed,
                            contract,
                            budget,
                            repeat,
                            learner_name,
                            "ceiling",
                        )
                        base = model(
                            learner_name,
                            numeric,
                            categorical,
                            seed,
                            trees,
                        ).fit(paired_train, paired_y_train).predict(paired_eval)
                        residual = model(
                            learner_name,
                            numeric,
                            categorical,
                            stable_seed(seed, "residual"),
                            trees,
                        ).fit(
                            paired_train,
                            paired_y_train - paired_train["_measured_uts"].to_numpy(),
                        )
                        augmented = (
                            paired_eval["_measured_uts"].to_numpy()
                            + residual.predict(paired_eval)
                        )
                        paired_scope_indices = {
                            "all": np.arange(len(paired_eval), dtype=int),
                            **{
                                scope: np.asarray(
                                    [
                                        index
                                        for index in range(len(paired_eval))
                                        if paired_scopes[index] == scope
                                    ],
                                    dtype=int,
                                )
                                for scope in ("q1", "q2", "q3", "q4")
                            },
                        }
                        for scope, indices in paired_scope_indices.items():
                            if len(indices) < 2:
                                continue
                            rows.append(
                                {
                                    "contract": contract,
                                    "budget": int(budget),
                                    "repeat": repeat,
                                    "learner": learner_name,
                                    "method": "measured_uts_residual_ceiling",
                                    "scope": scope,
                                    **metrics(
                                        paired_y_eval[indices],
                                        base[indices],
                                        augmented[indices],
                                    ),
                                }
                            )

    result_frame = pd.DataFrame(rows)
    prediction_frame = pd.DataFrame(prediction_rows)
    summary_rows, gate = summarize(
        result_frame[
            result_frame["method"] != "measured_uts_residual_ceiling"
        ],
        design,
    )
    result_frame.to_csv(output, index=False)
    prediction_frame.to_csv(prediction_output, index=False)
    summary_payload = {
        "status": "complete-method-development",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "design_sha256": hashlib.sha256(design_text.encode("utf-8")).hexdigest(),
        "data": {
            "target_rows": int(len(target)),
            "target_groups": int(target["group"].nunique()),
            "source_rows": int(len(source)),
            "source_groups": int(source["group"].nunique()),
            "development_rows": int(len(development)),
            "evaluation_rows": int(len(evaluation)),
            "evaluation_groups": int(evaluation["group"].nunique()),
        },
        "donor_group_oof_r2": donor_quality,
        "audits": audits,
        "summaries": summary_rows,
        "balam_escalation_gate": gate,
        "claim_guard": design["claim_guard"],
    }
    summary_output.write_text(
        json.dumps(summary_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps(summary_payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
