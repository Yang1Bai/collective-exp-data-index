"""Run the frozen MPEA provenance, donor-specificity and state analysis."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold

from common import RESULTS, sample_groups
from run_knowledge_map import balanced_group_partition
from run_state_matched_mpea_borrowing_screen import (
    COMP_PREFIX,
    YS_COLUMN,
    composition_quartiles,
    load_raw,
    model,
    stable_seed,
    task_frame,
)


HERE = Path(__file__).resolve().parent
DESIGN_PATH = HERE / "mpea_provenance_specificity_design.json"
DOI_COLUMN = "REFERENCE: doi"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--design-path", type=Path, default=DESIGN_PATH)
    parser.add_argument("--output-prefix", default="mpea_provenance_specificity")
    parser.add_argument("--repeats", type=int)
    parser.add_argument("--trees", type=int)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def normalize_doi(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    text = str(value).strip().lower()
    for prefix in (
        "https://doi.org/",
        "http://doi.org/",
        "https://dx.doi.org/",
        "http://dx.doi.org/",
        "doi:",
    ):
        if text.startswith(prefix):
            text = text[len(prefix) :]
    return text.strip().rstrip(".")


def add_doi(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    output["_doi"] = output[DOI_COLUMN].map(normalize_doi)
    return output


def nonempty(values: Sequence[object]) -> set[str]:
    return {str(value) for value in values if str(value)}


def feature_columns(
    raw: pd.DataFrame, design: dict[str, Any], contract: str
) -> tuple[list[str], list[str]]:
    comp = [column for column in raw.columns if column.startswith(COMP_PREFIX)]
    spec = design["contracts"][contract]
    return comp + list(spec["numeric"]), list(spec["categorical"])


def deterministic_size_match(
    frame: pd.DataFrame, target_n: int, seed: int
) -> pd.DataFrame:
    if len(frame) < target_n:
        raise RuntimeError(f"Cannot size-match {len(frame)} source rows to {target_n}")
    if len(frame) == target_n:
        return frame.sort_values("raw_row_id", kind="mergesort").reset_index(drop=True)
    ranked = frame.copy()
    ranked["_selection_key"] = ranked["raw_row_id"].map(
        lambda row_id: stable_seed(seed, int(row_id))
    )
    ranked = ranked.sort_values(
        ["_selection_key", "raw_row_id"], kind="mergesort"
    ).head(target_n)
    return ranked.drop(columns="_selection_key").reset_index(drop=True)


def source_for_mode(
    source: pd.DataFrame,
    evaluation: pd.DataFrame,
    mode: dict[str, Any],
) -> pd.DataFrame:
    output = source.copy()
    if mode["exclude_evaluation_groups_from_donor"]:
        output = output[
            ~output["group"].astype(str).isin(
                set(evaluation["group"].astype(str))
            )
        ]
    if mode["exclude_evaluation_dois_from_donor"]:
        evaluation_dois = nonempty(evaluation["_doi"])
        output = output[
            ~output["_doi"].astype(str).isin(evaluation_dois)
            | output["_doi"].eq("")
        ]
    return output.reset_index(drop=True)


def development_for_mode(
    development: pd.DataFrame,
    evaluation: pd.DataFrame,
    mode: dict[str, Any],
) -> pd.DataFrame:
    output = development.copy()
    if mode["exclude_evaluation_dois_from_target_development"]:
        evaluation_dois = nonempty(evaluation["_doi"])
        output = output[
            ~output["_doi"].astype(str).isin(evaluation_dois)
            | output["_doi"].eq("")
        ]
    return output.reset_index(drop=True)


def shuffled(values: np.ndarray, seed: int) -> np.ndarray:
    result = np.asarray(values, dtype=float).copy()
    np.random.default_rng(seed).shuffle(result)
    return result


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
    exclude_evaluation_dois: bool,
    exclude_held_dois: bool,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    """Generate donor predictions without held-system or held-DOI access."""
    evaluation_groups = set(target_eval["group"].astype(str))
    all_evaluation_dois = nonempty(target_eval["_doi"])
    evaluation_dois = (
        all_evaluation_dois if exclude_evaluation_dois else set()
    )
    train_groups = target_train["group"].astype(str).to_numpy()
    folds = min(5, len(np.unique(train_groups)))
    if folds < 2:
        raise RuntimeError("Too few target systems for donor cross-fitting")
    prediction_train = np.full(len(target_train), np.nan)
    dummy = np.zeros(len(target_train))
    fold_sizes: list[int] = []
    fold_doi_overlap: list[int] = []
    for fold_id, (_, held) in enumerate(
        GroupKFold(n_splits=folds).split(dummy, dummy, train_groups)
    ):
        held_groups = set(train_groups[held])
        held_dois = nonempty(target_train.iloc[held]["_doi"]) if exclude_held_dois else set()
        forbidden_dois = evaluation_dois | held_dois
        keep = ~source["group"].astype(str).isin(evaluation_groups | held_groups)
        if forbidden_dois:
            keep &= ~source["_doi"].astype(str).isin(forbidden_dois) | source[
                "_doi"
            ].eq("")
        source_fit = source.loc[keep].reset_index(drop=True)
        if len(source_fit) < 30:
            raise RuntimeError(f"Only {len(source_fit)} source rows remain in donor fold")
        overlap = nonempty(source_fit["_doi"]) & forbidden_dois
        if overlap:
            raise AssertionError(f"Donor DOI leakage in fold {fold_id}: {sorted(overlap)[:3]}")
        if set(source_fit["group"].astype(str)) & (evaluation_groups | held_groups):
            raise AssertionError("Donor elemental-system leakage")
        y_fit = source_fit["value"].to_numpy(float)
        if shuffle_outcome:
            y_fit = shuffled(y_fit, stable_seed(seed, "shuffle", fold_id))
        fitted = model(
            "extra_trees",
            numeric,
            categorical,
            stable_seed(seed, "donor-fold", fold_id),
            trees,
        ).fit(source_fit, y_fit)
        prediction_train[held] = fitted.predict(target_train.iloc[held])
        fold_sizes.append(len(source_fit))
        fold_doi_overlap.append(len(overlap))
    if not np.isfinite(prediction_train).all():
        raise AssertionError("Incomplete target-training donor features")

    keep_final = ~source["group"].astype(str).isin(evaluation_groups)
    if evaluation_dois:
        keep_final &= ~source["_doi"].astype(str).isin(evaluation_dois) | source[
            "_doi"
        ].eq("")
    source_final = source.loc[keep_final].reset_index(drop=True)
    if set(source_final["group"].astype(str)) & evaluation_groups:
        raise AssertionError("Final donor model contains an evaluation system")
    if nonempty(source_final["_doi"]) & evaluation_dois:
        raise AssertionError("Final donor model contains an evaluation DOI")
    y_final = source_final["value"].to_numpy(float)
    if shuffle_outcome:
        y_final = shuffled(y_final, stable_seed(seed, "shuffle-final"))
    fitted_final = model(
        "extra_trees",
        numeric,
        categorical,
        stable_seed(seed, "donor-final"),
        trees,
    ).fit(source_final, y_final)
    prediction_eval = fitted_final.predict(target_eval)
    return (
        prediction_train,
        prediction_eval,
        {
            "source_final_n": int(len(source_final)),
            "source_final_groups": int(source_final["group"].nunique()),
            "source_final_dois": int(len(nonempty(source_final["_doi"]))),
            "source_final_evaluation_doi_overlap": int(
                len(nonempty(source_final["_doi"]) & all_evaluation_dois)
            ),
            "source_fold_min_n": int(min(fold_sizes)),
            "source_fold_max_n": int(max(fold_sizes)),
            "max_forbidden_doi_overlap": int(max(fold_doi_overlap)),
        },
    )


def group_oof_skill(
    source: pd.DataFrame,
    numeric: Sequence[str],
    categorical: Sequence[str],
    seed: int,
    trees: int,
) -> dict[str, float | int]:
    groups = source["group"].astype(str).to_numpy()
    folds = min(5, len(np.unique(groups)))
    if folds < 2:
        return {"n": len(source), "groups": len(np.unique(groups)), "oof_r2": math.nan}
    prediction = np.full(len(source), np.nan)
    dummy = np.zeros(len(source))
    for fold, (fit, held) in enumerate(
        GroupKFold(n_splits=folds).split(dummy, dummy, groups)
    ):
        fitted = model(
            "extra_trees",
            numeric,
            categorical,
            stable_seed(seed, "oof", fold),
            trees,
        ).fit(source.iloc[fit], source.iloc[fit]["value"])
        prediction[held] = fitted.predict(source.iloc[held])
    return {
        "n": int(len(source)),
        "groups": int(source["group"].nunique()),
        "dois": int(len(nonempty(source["_doi"]))),
        "oof_r2": float(r2_score(source["value"], prediction)),
        "oof_rmse": float(
            math.sqrt(mean_squared_error(source["value"], prediction))
        ),
    }


def target_predictions(
    train: pd.DataFrame,
    evaluation: pd.DataFrame,
    numeric: list[str],
    categorical: list[str],
    learner: str,
    seed: int,
    trees: int,
    donor_train: np.ndarray,
    donor_eval: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    y_train = train["value"].to_numpy(float)
    baseline = model(learner, numeric, categorical, seed, trees)
    baseline.fit(train, y_train)
    baseline_prediction = baseline.predict(evaluation)
    train_augmented = train.copy()
    eval_augmented = evaluation.copy()
    train_augmented["_donor_prediction"] = donor_train
    eval_augmented["_donor_prediction"] = donor_eval
    augmented = model(
        learner,
        [*numeric, "_donor_prediction"],
        categorical,
        stable_seed(seed, "augmented"),
        trees,
    )
    augmented.fit(train_augmented, y_train)
    return baseline_prediction, augmented.predict(eval_augmented)


def metric_row(
    observed: np.ndarray,
    baseline: np.ndarray,
    augmented: np.ndarray,
) -> dict[str, float | int]:
    base_rmse = math.sqrt(mean_squared_error(observed, baseline))
    aug_rmse = math.sqrt(mean_squared_error(observed, augmented))
    return {
        "n": int(len(observed)),
        "base_rmse": float(base_rmse),
        "aug_rmse": float(aug_rmse),
        "relative_rmse_gain": float((base_rmse - aug_rmse) / base_rmse),
        "base_r2": float(r2_score(observed, baseline)),
        "aug_r2": float(r2_score(observed, augmented)),
        "delta_r2": float(r2_score(observed, augmented) - r2_score(observed, baseline)),
    }


def split_data(
    target: pd.DataFrame, design: dict[str, Any]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    partition = design["data"]["partition"]
    development_index, discovery_index, confirmation_index = balanced_group_partition(
        target,
        (
            float(partition["development"]),
            float(partition["discovery"]),
            float(partition["confirmation"]),
        ),
        int(partition["seed"]),
        "group",
    )
    evaluation_index = np.sort(np.r_[discovery_index, confirmation_index])
    development = target.loc[development_index].reset_index(drop=True)
    evaluation = target.loc[evaluation_index].reset_index(drop=True)
    if set(development["group"]) & set(evaluation["group"]):
        raise AssertionError("Target elemental-system leakage")
    return development, evaluation


def build_conditions(design: dict[str, Any]) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    provenance = design["arms"]["provenance_ladder"]
    for mode in provenance["provenance_modes"]:
        output.append(
            {
                "condition": f"provenance__{mode}",
                "arms": "provenance_ladder",
                "provenance_mode": mode,
                "donor": provenance["donor"],
                "contract": provenance["contract"],
            }
        )
    specificity = design["arms"]["donor_specificity"]
    for donor in specificity["donors"]:
        condition = {
            "condition": f"specificity__{donor}",
            "arms": "donor_specificity",
            "provenance_mode": specificity["provenance_mode"],
            "donor": donor,
            "contract": specificity["contract"],
        }
        if donor == "uts":
            existing = next(
                row
                for row in output
                if row["provenance_mode"] == condition["provenance_mode"]
                and row["donor"] == donor
                and row["contract"] == condition["contract"]
            )
            existing["arms"] += ";donor_specificity;state_dependence"
        else:
            output.append(condition)
    state = design["arms"]["state_dependence"]
    for contract in state["contracts"]:
        if contract == specificity["contract"]:
            continue
        output.append(
            {
                "condition": f"state__{contract}",
                "arms": "state_dependence",
                "provenance_mode": state["provenance_mode"],
                "donor": state["donor"],
                "contract": contract,
            }
        )
    return output


def main() -> None:
    args = parse_args()
    RESULTS.mkdir(parents=True, exist_ok=True)
    design_path = args.design_path.resolve()
    design_text = design_path.read_text(encoding="utf-8")
    design = json.loads(design_text)
    prefix = args.output_prefix
    metrics_path = RESULTS / f"{prefix}_metrics.csv"
    predictions_path = RESULTS / f"{prefix}_predictions.csv.gz"
    audit_path = RESULTS / f"{prefix}_audit.json"
    complete_path = RESULTS / f"{prefix}_complete.json"
    outputs = [metrics_path, predictions_path, audit_path, complete_path]
    if any(path.exists() for path in outputs) and not args.overwrite:
        raise FileExistsError("Outputs already exist; pass --overwrite")

    repeats = args.repeats or int(design["model"]["repeats"])
    trees = args.trees or int(design["model"]["tree_estimators"])
    partition_seed = int(design["data"]["partition"]["seed"])
    raw = load_raw()
    raw = add_doi(raw)
    target = add_doi(task_frame(raw, YS_COLUMN))
    donor_frames = {
        key: add_doi(task_frame(raw, spec["column"]))
        for key, spec in design["donors"].items()
    }
    development, evaluation = split_data(target, design)
    evaluation_dois = nonempty(evaluation["_doi"])
    shared_development_dois = nonempty(development["_doi"]) & evaluation_dois
    comp_columns = [column for column in raw.columns if column.startswith(COMP_PREFIX)]

    modes = design["provenance_modes"]
    development_pools = {
        mode_name: development_for_mode(development, evaluation, mode)
        for mode_name, mode in modes.items()
    }
    source_pools: dict[tuple[str, str], pd.DataFrame] = {}
    for mode_name, mode in modes.items():
        for donor_name, source in donor_frames.items():
            source_pools[(mode_name, donor_name)] = source_for_mode(
                source, evaluation, mode
            )

    strict_mode = design["arms"]["donor_specificity"]["provenance_mode"]
    strict_uts_n = len(source_pools[(strict_mode, "uts")])
    for donor_name in design["arms"]["donor_specificity"]["donors"]:
        source_pools[(strict_mode, donor_name)] = deterministic_size_match(
            source_pools[(strict_mode, donor_name)],
            strict_uts_n,
            stable_seed(partition_seed, "size-match", donor_name),
        )

    conditions = build_conditions(design)
    condition_audits: list[dict[str, Any]] = []
    source_skill: list[dict[str, Any]] = []
    for condition in conditions:
        mode_name = condition["provenance_mode"]
        donor_name = condition["donor"]
        contract = condition["contract"]
        source = source_pools[(mode_name, donor_name)]
        pool = development_pools[mode_name]
        numeric, categorical = feature_columns(raw, design, contract)
        skill = group_oof_skill(
            source,
            numeric,
            categorical,
            stable_seed(partition_seed, condition["condition"], "skill"),
            trees,
        )
        source_skill.append({**condition, **skill})
        condition_audits.append(
            {
                **condition,
                "target_development_rows": int(len(pool)),
                "target_development_groups": int(pool["group"].nunique()),
                "target_development_dois": int(len(nonempty(pool["_doi"]))),
                "target_eval_doi_overlap": int(
                    len(nonempty(pool["_doi"]) & evaluation_dois)
                ),
                "source_rows": int(len(source)),
                "source_groups": int(source["group"].nunique()),
                "source_dois": int(len(nonempty(source["_doi"]))),
                "source_eval_group_overlap": int(
                    len(
                        set(source["group"].astype(str))
                        & set(evaluation["group"].astype(str))
                    )
                ),
                "source_eval_doi_overlap": int(
                    len(nonempty(source["_doi"]) & evaluation_dois)
                ),
            }
        )

    prediction_rows: list[dict[str, Any]] = []
    metric_rows: list[dict[str, Any]] = []
    donor_fit_audits: list[dict[str, Any]] = []
    transfer_budget = int(design["arms"]["provenance_ladder"]["budget"])

    for condition in conditions:
        mode_name = condition["provenance_mode"]
        donor_name = condition["donor"]
        contract = condition["contract"]
        mode = modes[mode_name]
        pool = development_pools[mode_name]
        source = source_pools[(mode_name, donor_name)]
        numeric, categorical = feature_columns(raw, design, contract)
        pool_key = "strict" if mode["exclude_evaluation_dois_from_target_development"] else "standard"
        for repeat in range(repeats):
            local = sample_groups(
                pool["group"].astype(str).to_numpy(),
                transfer_budget,
                np.random.default_rng(
                    stable_seed(partition_seed, pool_key, transfer_budget, repeat)
                ),
            )
            train = pool.iloc[local].reset_index(drop=True)
            scopes, distances = composition_quartiles(
                train, evaluation, comp_columns
            )
            donor_seed = stable_seed(
                partition_seed, mode_name, donor_name, contract, repeat
            )
            real_train, real_eval, real_audit = crossfitted_donor_signal(
                source,
                train,
                evaluation,
                numeric,
                categorical,
                donor_seed,
                trees,
                shuffle_outcome=False,
                exclude_evaluation_dois=bool(
                    mode["exclude_evaluation_dois_from_donor"]
                ),
                exclude_held_dois=bool(
                    mode["exclude_held_target_dois_inside_donor_crossfit"]
                ),
            )
            shuffled_train, shuffled_eval, shuffled_audit = crossfitted_donor_signal(
                source,
                train,
                evaluation,
                numeric,
                categorical,
                stable_seed(donor_seed, "shuffled"),
                trees,
                shuffle_outcome=True,
                exclude_evaluation_dois=bool(
                    mode["exclude_evaluation_dois_from_donor"]
                ),
                exclude_held_dois=bool(
                    mode["exclude_held_target_dois_inside_donor_crossfit"]
                ),
            )
            donor_fit_audits.append(
                {
                    **condition,
                    "repeat": repeat,
                    "target_train_n": int(len(train)),
                    "target_train_groups": int(train["group"].nunique()),
                    "target_train_dois": int(len(nonempty(train["_doi"]))),
                    "real": real_audit,
                    "shuffled": shuffled_audit,
                }
            )
            y_eval = evaluation["value"].to_numpy(float)
            for learner in design["model"]["target_learners"]:
                target_seed = stable_seed(
                    partition_seed,
                    pool_key,
                    contract,
                    transfer_budget,
                    repeat,
                    learner,
                )
                baseline, real_prediction = target_predictions(
                    train,
                    evaluation,
                    numeric,
                    categorical,
                    learner,
                    target_seed,
                    trees,
                    real_train,
                    real_eval,
                )
                shuffled_baseline, shuffled_prediction = target_predictions(
                    train,
                    evaluation,
                    numeric,
                    categorical,
                    learner,
                    target_seed,
                    trees,
                    shuffled_train,
                    shuffled_eval,
                )
                if not np.allclose(baseline, shuffled_baseline, atol=1e-12):
                    raise AssertionError("Architecture-matched baselines diverged")
                scope_indices = {
                    "all": np.arange(len(evaluation), dtype=int),
                    **{
                        scope: np.asarray(
                            [
                                index
                                for index in range(len(evaluation))
                                if scopes[index] == scope
                            ],
                            dtype=int,
                        )
                        for scope in ("q1", "q2", "q3", "q4")
                    },
                }
                for scope, indices in scope_indices.items():
                    real_metrics = metric_row(
                        y_eval[indices], baseline[indices], real_prediction[indices]
                    )
                    shuffled_metrics = metric_row(
                        y_eval[indices],
                        baseline[indices],
                        shuffled_prediction[indices],
                    )
                    metric_rows.append(
                        {
                            **condition,
                            "budget": transfer_budget,
                            "repeat": repeat,
                            "learner": learner,
                            "scope": scope,
                            **{f"real_{key}": value for key, value in real_metrics.items()},
                            **{
                                f"shuffled_{key}": value
                                for key, value in shuffled_metrics.items()
                            },
                        }
                    )
                for index, row in evaluation.iterrows():
                    prediction_rows.append(
                        {
                            **condition,
                            "budget": transfer_budget,
                            "repeat": repeat,
                            "learner": learner,
                            "raw_row_id": int(row["raw_row_id"]),
                            "material_key": row["material_key"],
                            "group": row["group"],
                            "doi": row["_doi"],
                            "scope": scopes[index],
                            "composition_distance": distances[index],
                            "observed": y_eval[index],
                            "baseline": baseline[index],
                            "real_augmented": real_prediction[index],
                            "shuffled_augmented": shuffled_prediction[index],
                            "real_donor_feature": real_eval[index],
                            "shuffled_donor_feature": shuffled_eval[index],
                        }
                    )

    learning = design["arms"]["target_label_equivalence"]
    learning_contract = learning["contract"]
    learning_mode = learning["provenance_mode"]
    learning_pool = development_pools[learning_mode]
    numeric, categorical = feature_columns(raw, design, learning_contract)
    y_eval = evaluation["value"].to_numpy(float)
    for budget in learning["budgets"]:
        for repeat in range(repeats):
            local = sample_groups(
                learning_pool["group"].astype(str).to_numpy(),
                int(budget),
                np.random.default_rng(
                    stable_seed(partition_seed, "strict", int(budget), repeat)
                ),
            )
            train = learning_pool.iloc[local].reset_index(drop=True)
            scopes, distances = composition_quartiles(
                train, evaluation, comp_columns
            )
            for learner in design["model"]["target_learners"]:
                seed = stable_seed(
                    partition_seed,
                    "strict",
                    learning_contract,
                    int(budget),
                    repeat,
                    learner,
                )
                fitted = model(learner, numeric, categorical, seed, trees)
                fitted.fit(train, train["value"])
                prediction = fitted.predict(evaluation)
                scope_indices = {
                    "all": np.arange(len(evaluation), dtype=int),
                    **{
                        scope: np.asarray(
                            [
                                index
                                for index in range(len(evaluation))
                                if scopes[index] == scope
                            ],
                            dtype=int,
                        )
                        for scope in ("q1", "q2", "q3", "q4")
                    },
                }
                for scope, indices in scope_indices.items():
                    baseline_metrics = metric_row(
                        y_eval[indices], prediction[indices], prediction[indices]
                    )
                    metric_rows.append(
                        {
                            "condition": f"target_only__budget_{budget}",
                            "arms": "target_label_equivalence",
                            "provenance_mode": learning_mode,
                            "donor": "none",
                            "contract": learning_contract,
                            "budget": int(budget),
                            "repeat": repeat,
                            "learner": learner,
                            "scope": scope,
                            "real_n": baseline_metrics["n"],
                            "real_base_rmse": baseline_metrics["base_rmse"],
                            "real_aug_rmse": baseline_metrics["aug_rmse"],
                            "real_relative_rmse_gain": 0.0,
                            "real_base_r2": baseline_metrics["base_r2"],
                            "real_aug_r2": baseline_metrics["aug_r2"],
                            "real_delta_r2": 0.0,
                            "shuffled_n": baseline_metrics["n"],
                            "shuffled_base_rmse": baseline_metrics["base_rmse"],
                            "shuffled_aug_rmse": baseline_metrics["aug_rmse"],
                            "shuffled_relative_rmse_gain": 0.0,
                            "shuffled_base_r2": baseline_metrics["base_r2"],
                            "shuffled_aug_r2": baseline_metrics["aug_r2"],
                            "shuffled_delta_r2": 0.0,
                        }
                    )
                for index, row in evaluation.iterrows():
                    prediction_rows.append(
                        {
                            "condition": f"target_only__budget_{budget}",
                            "arms": "target_label_equivalence",
                            "provenance_mode": learning_mode,
                            "donor": "none",
                            "contract": learning_contract,
                            "budget": int(budget),
                            "repeat": repeat,
                            "learner": learner,
                            "raw_row_id": int(row["raw_row_id"]),
                            "material_key": row["material_key"],
                            "group": row["group"],
                            "doi": row["_doi"],
                            "scope": scopes[index],
                            "composition_distance": distances[index],
                            "observed": y_eval[index],
                            "baseline": prediction[index],
                            "real_augmented": prediction[index],
                            "shuffled_augmented": prediction[index],
                            "real_donor_feature": np.nan,
                            "shuffled_donor_feature": np.nan,
                        }
                    )

    metric_frame = pd.DataFrame(metric_rows)
    prediction_frame = pd.DataFrame(prediction_rows)
    metric_frame.to_csv(metrics_path, index=False)
    prediction_frame.to_csv(predictions_path, index=False, compression="gzip")
    audit = {
        "status": "complete",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "design_sha256": hashlib.sha256(design_text.encode("utf-8")).hexdigest(),
        "parameters": {"repeats": repeats, "trees": trees},
        "target": {
            "rows": int(len(target)),
            "groups": int(target["group"].nunique()),
            "dois": int(len(nonempty(target["_doi"]))),
            "development_rows": int(len(development)),
            "evaluation_rows": int(len(evaluation)),
            "evaluation_groups": int(evaluation["group"].nunique()),
            "evaluation_dois": int(len(evaluation_dois)),
            "development_evaluation_shared_dois_before_strict_filter": int(
                len(shared_development_dois)
            ),
        },
        "strict_source_size_match_n": int(strict_uts_n),
        "conditions": condition_audits,
        "source_skill": source_skill,
        "donor_fit_audits": donor_fit_audits,
        "claim_guard": design["claim_guard"],
    }
    audit_path.write_text(
        json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    complete = {
        "status": "complete",
        "design_sha256": audit["design_sha256"],
        "metrics_rows": int(len(metric_frame)),
        "prediction_rows": int(len(prediction_frame)),
        "transfer_conditions": int(len(conditions)),
        "target_only_budgets": len(learning["budgets"]),
        "repeats": repeats,
        "learners": len(design["model"]["target_learners"]),
        "outputs": {
            metrics_path.name: hashlib.sha256(metrics_path.read_bytes()).hexdigest(),
            predictions_path.name: hashlib.sha256(
                predictions_path.read_bytes()
            ).hexdigest(),
            audit_path.name: hashlib.sha256(audit_path.read_bytes()).hexdigest(),
        },
        "claim_guard": design["claim_guard"],
    }
    complete_path.write_text(
        json.dumps(complete, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(complete, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
