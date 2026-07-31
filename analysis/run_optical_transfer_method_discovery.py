"""Large development-only search for state-aware optical transfer strategies."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
from pathlib import Path

import numpy as np
import pandas as pd
import rdkit
import sklearn
from joblib import Parallel, delayed
from rdkit import Chem, RDLogger
from rdkit.Chem import rdFingerprintGenerator
from scipy import stats
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DESIGN_PATH = HERE / "optical_photocatalysis_borrowing_design.json"
CONFIG_PATH = HERE / "optical_transfer_method_discovery_config.json"
AUDIT_PATH = HERE / "results" / "optical_photocatalysis_pair_audit.json"
METADATA_PATH = HERE / "results" / "optical_photocatalysis_target_metadata.csv"
GLOBAL_SUMMARY_PATH = (
    HERE / "results" / "optical_photocatalysis_source_skill.json"
)
GLOBAL_FEATURE_PATH = (
    HERE / "results" / "optical_photocatalysis_donor_features.csv"
)
STATE_SUMMARY_PATH = (
    HERE / "results" / "optical_state_matched_donor_summary.json"
)
STATE_VERIFIED_PATH = (
    HERE / "results" / "optical_state_matched_donor_VERIFIED.json"
)
STATE_FEATURE_PATH = (
    HERE / "results" / "optical_state_matched_donor_features.csv"
)
DRAW_PATH = HERE / "results" / "optical_transfer_method_discovery_draws.csv"
DRAW_MANIFEST_PATH = (
    HERE / "results" / "optical_transfer_method_discovery_draws_manifest.json"
)
TARGET_PATH = (
    ROOT
    / "data"
    / "external"
    / "optical_photocatalysis"
    / "SC-012-D1SC02150H-s005.csv"
)
REGISTRY_PATH = (
    HERE / "results" / "optical_transfer_method_registry.json"
)
METRICS_PATH = (
    HERE / "results" / "optical_transfer_method_discovery_metrics.csv"
)
CANDIDATE_SUMMARY_PATH = (
    HERE / "results" / "optical_transfer_method_candidate_summary.csv"
)
SUMMARY_PATH = (
    HERE / "results" / "optical_transfer_method_discovery_summary.json"
)

SEED = 20260726
RDLogger.DisableLog("rdApp.error")


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def feature_matrix(smiles_values: list[str]) -> np.ndarray:
    generator = rdFingerprintGenerator.GetMorganGenerator(
        radius=2, fpSize=2048, includeChirality=True
    )
    output = np.zeros((len(smiles_values), 2048), dtype=np.uint8)
    for row, smiles in enumerate(smiles_values):
        molecule = Chem.MolFromSmiles(smiles)
        if molecule is None:
            raise RuntimeError(f"Audited target structure no longer parses: {smiles}")
        output[row] = generator.GetFingerprintAsNumPy(molecule).astype(
            np.uint8, copy=False
        )
    return output


def impute_from_training(
    training: np.ndarray, evaluation: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    training = training.astype(float, copy=True)
    evaluation = evaluation.astype(float, copy=True)
    medians = np.nanmedian(training, axis=0)
    medians[~np.isfinite(medians)] = 0.0
    train_missing = ~np.isfinite(training)
    eval_missing = ~np.isfinite(evaluation)
    if train_missing.any():
        training[train_missing] = np.take(medians, np.where(train_missing)[1])
    if eval_missing.any():
        evaluation[eval_missing] = np.take(medians, np.where(eval_missing)[1])
    return training, evaluation


def rank_from_training(
    training: np.ndarray, evaluation: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    train_output = np.zeros_like(training, dtype=float)
    eval_output = np.zeros_like(evaluation, dtype=float)
    denominator = float(len(training) + 1)
    for column in range(training.shape[1]):
        ordered = np.sort(training[:, column])
        train_output[:, column] = (
            np.searchsorted(ordered, training[:, column], side="right")
            / denominator
        )
        eval_output[:, column] = (
            np.searchsorted(ordered, evaluation[:, column], side="right")
            / denominator
        )
    return train_output, eval_output


def shuffled_columns(
    training: np.ndarray, evaluation: np.ndarray, seed: int
) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    train_output = training.copy()
    eval_output = evaluation.copy()
    for column in range(training.shape[1]):
        train_output[:, column] = training[
            rng.permutation(len(training)), column
        ]
        eval_output[:, column] = evaluation[
            rng.permutation(len(evaluation)), column
        ]
    return train_output, eval_output


def make_rf(settings: dict[str, object], seed: int) -> RandomForestRegressor:
    return RandomForestRegressor(
        n_estimators=int(settings["n_estimators_per_seed"]),
        min_samples_leaf=int(settings["min_samples_leaf"]),
        max_features=float(settings["max_features"]),
        random_state=seed,
        n_jobs=1,
    )


def rf_ensemble_prediction(
    train_x: np.ndarray,
    train_y: np.ndarray,
    eval_x: np.ndarray,
    eval_y: np.ndarray,
    settings: dict[str, object],
    seed_base: int,
) -> tuple[np.ndarray, float]:
    predictions: list[np.ndarray] = []
    seed_rmses: list[float] = []
    for seed_index in range(int(settings["seeds_per_candidate"])):
        estimator = make_rf(settings, seed_base + seed_index)
        estimator.fit(train_x, train_y)
        prediction = estimator.predict(eval_x)
        predictions.append(prediction)
        seed_rmses.append(
            math.sqrt(mean_squared_error(eval_y, prediction))
        )
    return (
        np.mean(np.vstack(predictions), axis=0),
        float(np.std(seed_rmses, ddof=1)) if len(seed_rmses) > 1 else 0.0,
    )


def inner_target_oof(
    train_x: np.ndarray,
    train_y: np.ndarray,
    groups: np.ndarray,
    settings: dict[str, object],
    seed_base: int,
) -> np.ndarray:
    unique_groups = len(set(groups.astype(str)))
    folds = min(5, unique_groups)
    splitter = GroupKFold(
        n_splits=folds, shuffle=True, random_state=seed_base
    )
    output = np.full(len(train_y), np.nan)
    seeds = int(settings["inner_oof_seeds_for_residual_and_fusion"])
    for fold, (fit_rows, held_rows) in enumerate(
        splitter.split(train_x, train_y, groups)
    ):
        fold_predictions = []
        for seed_index in range(seeds):
            estimator = make_rf(
                settings, seed_base + 1000 * fold + seed_index
            )
            estimator.fit(train_x[fit_rows], train_y[fit_rows])
            fold_predictions.append(estimator.predict(train_x[held_rows]))
        output[held_rows] = np.mean(np.vstack(fold_predictions), axis=0)
    if not np.isfinite(output).all():
        raise RuntimeError("Incomplete inner target OOF prediction")
    return output


def ridge_group_cv(
    train_x: np.ndarray,
    train_y: np.ndarray,
    groups: np.ndarray,
    alphas: list[float],
    seed: int,
) -> tuple[object, np.ndarray, float]:
    folds = min(5, len(set(groups.astype(str))))
    splitter = GroupKFold(n_splits=folds, shuffle=True, random_state=seed)
    split_rows = list(splitter.split(train_x, train_y, groups))
    alpha_oof: dict[float, np.ndarray] = {}
    alpha_mse: dict[float, float] = {}
    for alpha in alphas:
        oof = np.full(len(train_y), np.nan)
        for fit_rows, held_rows in split_rows:
            estimator = make_pipeline(
                StandardScaler(),
                Ridge(alpha=float(alpha)),
            )
            estimator.fit(train_x[fit_rows], train_y[fit_rows])
            oof[held_rows] = estimator.predict(train_x[held_rows])
        alpha_oof[float(alpha)] = oof
        alpha_mse[float(alpha)] = float(mean_squared_error(train_y, oof))
    selected_alpha = min(alpha_mse, key=lambda value: (alpha_mse[value], value))
    final_estimator = make_pipeline(
        StandardScaler(), Ridge(alpha=selected_alpha)
    )
    final_estimator.fit(train_x, train_y)
    return final_estimator, alpha_oof[selected_alpha], selected_alpha


def metric_row(
    method: str,
    prediction: np.ndarray,
    truth: np.ndarray,
    seed_rmse_sd: float,
    metadata: dict[str, object],
) -> dict[str, object]:
    spearman = stats.spearmanr(truth, prediction).statistic
    return {
        **metadata,
        "method": method,
        "rmse": float(math.sqrt(mean_squared_error(truth, prediction))),
        "mae": float(mean_absolute_error(truth, prediction)),
        "r2": float(r2_score(truth, prediction)),
        "spearman": float(spearman) if np.isfinite(spearman) else float("nan"),
        "forest_seed_rmse_sd": seed_rmse_sd,
    }


def subset_columns(
    columns: list[str], slugs: list[str], prefix: str
) -> list[str]:
    return [
        column
        for column in columns
        if column.startswith(prefix)
        and any(column.endswith(slug) for slug in slugs)
    ]


def build_blocks(
    global_summary: dict[str, object],
    global_features: pd.DataFrame,
    state_summary: dict[str, object],
    state_features: pd.DataFrame,
) -> dict[str, dict[str, object]]:
    blocks: dict[str, dict[str, object]] = {}
    global_columns = []
    for property_name in global_summary["admitted_properties"]:
        slug = global_summary["properties"][property_name]["slug"]
        global_columns.extend([f"pred_{slug}", f"unc_{slug}"])
    blocks["global_all_environment"] = {
        "frame": global_features,
        "columns": global_columns,
        "support_columns": ["max_similarity_to_retained_donor"],
    }
    for scope_name in (
        "water_methanol",
        "aqueous_small_alcohol",
        "self_host_solid",
    ):
        blocks[scope_name] = {
            "frame": state_features,
            "columns": list(
                state_summary["admitted_feature_columns_by_scope"][scope_name]
            ),
            "support_columns": [f"support_{scope_name}"],
        }
    blocks["aqueous_plus_solid"] = {
        "frame": state_features,
        "columns": [
            *blocks["aqueous_small_alcohol"]["columns"],
            *blocks["self_host_solid"]["columns"],
        ],
        "support_columns": [
            "support_aqueous_small_alcohol",
            "support_self_host_solid",
        ],
    }
    return blocks


def build_registry(
    blocks: dict[str, dict[str, object]],
    subsets: dict[str, list[str]],
) -> list[dict[str, object]]:
    registry: list[dict[str, object]] = [
        {
            "method": "target_structure_only",
            "family": "baseline",
            "is_transfer_candidate": False,
        },
        {
            "method": "target_structure_plus_calculated",
            "family": "baseline",
            "is_transfer_candidate": False,
        },
        {
            "method": "target_structure_plus_gaussian",
            "family": "gaussian_control",
            "is_transfer_candidate": False,
        },
    ]
    for block_name, block in blocks.items():
        columns = list(block["columns"])
        for subset_name, slugs in subsets.items():
            prediction_columns = subset_columns(columns, slugs, "pred_")
            uncertainty_columns = subset_columns(columns, slugs, "unc_")
            if not prediction_columns:
                continue
            for family in (
                "direct_rank_predictions",
                "support_gated_rank_predictions",
            ):
                method = f"{family}::{block_name}::{subset_name}"
                control = f"shuffled_{family}::{block_name}::{subset_name}"
                registry.extend(
                    [
                        {
                            "method": method,
                            "family": family,
                            "block": block_name,
                            "subset": subset_name,
                            "prediction_columns": prediction_columns,
                            "uncertainty_columns": uncertainty_columns,
                            "matched_control": control,
                            "is_transfer_candidate": True,
                        },
                        {
                            "method": control,
                            "family": f"shuffled_{family}",
                            "block": block_name,
                            "subset": subset_name,
                            "prediction_columns": prediction_columns,
                            "uncertainty_columns": uncertainty_columns,
                            "is_transfer_candidate": False,
                        },
                    ]
                )
        full_predictions = subset_columns(columns, subsets["full"], "pred_")
        full_uncertainties = subset_columns(columns, subsets["full"], "unc_")
        if not full_predictions:
            continue
        for family in (
            "direct_rank_predictions_uncertainty",
            "direct_raw_predictions",
        ):
            method = f"{family}::{block_name}::full"
            control = f"shuffled_{family}::{block_name}::full"
            registry.extend(
                [
                    {
                        "method": method,
                        "family": family,
                        "block": block_name,
                        "subset": "full",
                        "prediction_columns": full_predictions,
                        "uncertainty_columns": full_uncertainties,
                        "matched_control": control,
                        "is_transfer_candidate": True,
                    },
                    {
                        "method": control,
                        "family": f"shuffled_{family}",
                        "block": block_name,
                        "subset": "full",
                        "prediction_columns": full_predictions,
                        "uncertainty_columns": full_uncertainties,
                        "is_transfer_candidate": False,
                    },
                ]
            )
        for family in ("residual_ridge", "late_fusion_ridge"):
            method = f"{family}::{block_name}::full"
            control = f"shuffled_{family}::{block_name}::full"
            registry.extend(
                [
                    {
                        "method": method,
                        "family": family,
                        "block": block_name,
                        "subset": "full",
                        "prediction_columns": full_predictions,
                        "uncertainty_columns": full_uncertainties,
                        "matched_control": control,
                        "is_transfer_candidate": True,
                    },
                    {
                        "method": control,
                        "family": f"shuffled_{family}",
                        "block": block_name,
                        "subset": "full",
                        "prediction_columns": full_predictions,
                        "uncertainty_columns": full_uncertainties,
                        "is_transfer_candidate": False,
                    },
                ]
            )
    methods = [str(item["method"]) for item in registry]
    if len(methods) != len(set(methods)):
        raise RuntimeError("Duplicate discovery method name")
    return registry


def transformed_block(
    method_item: dict[str, object],
    block: dict[str, object],
    training_mask: np.ndarray,
    evaluation_mask: np.ndarray,
    seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    frame = block["frame"]
    prediction_columns = list(method_item["prediction_columns"])
    uncertainty_columns = list(method_item["uncertainty_columns"])
    pred_train = frame.loc[training_mask, prediction_columns].to_numpy(float)
    pred_eval = frame.loc[evaluation_mask, prediction_columns].to_numpy(float)
    unc_train = (
        frame.loc[training_mask, uncertainty_columns].to_numpy(float)
        if uncertainty_columns
        else np.empty((int(training_mask.sum()), 0))
    )
    unc_eval = (
        frame.loc[evaluation_mask, uncertainty_columns].to_numpy(float)
        if uncertainty_columns
        else np.empty((int(evaluation_mask.sum()), 0))
    )
    family = str(method_item["family"])
    shuffled = family.startswith("shuffled_")
    base_family = family.removeprefix("shuffled_")

    if base_family == "direct_raw_predictions":
        train_x, eval_x = pred_train, pred_eval
    else:
        pred_rank_train, pred_rank_eval = rank_from_training(
            pred_train, pred_eval
        )
        unc_rank_train, unc_rank_eval = (
            rank_from_training(unc_train, unc_eval)
            if unc_train.shape[1]
            else (unc_train, unc_eval)
        )
        if base_family == "direct_rank_predictions":
            train_x, eval_x = pred_rank_train, pred_rank_eval
        elif base_family in {
            "direct_rank_predictions_uncertainty",
            "residual_ridge",
            "late_fusion_ridge",
        }:
            train_x = np.column_stack([pred_rank_train, unc_rank_train])
            eval_x = np.column_stack([pred_rank_eval, unc_rank_eval])
        elif base_family == "support_gated_rank_predictions":
            support_columns = list(block["support_columns"])
            support_train = frame.loc[
                training_mask, support_columns
            ].to_numpy(float)
            support_eval = frame.loc[
                evaluation_mask, support_columns
            ].to_numpy(float)
            support_reliability_train = np.clip(
                (np.mean(support_train, axis=1) - 0.2) / 0.6, 0.0, 1.0
            )
            support_reliability_eval = np.clip(
                (np.mean(support_eval, axis=1) - 0.2) / 0.6, 0.0, 1.0
            )
            if unc_rank_train.shape[1]:
                uncertainty_reliability_train = 1.0 - np.mean(
                    unc_rank_train, axis=1
                )
                uncertainty_reliability_eval = 1.0 - np.mean(
                    unc_rank_eval, axis=1
                )
            else:
                uncertainty_reliability_train = np.ones(len(pred_rank_train))
                uncertainty_reliability_eval = np.ones(len(pred_rank_eval))
            reliability_train = (
                support_reliability_train * uncertainty_reliability_train
            )
            reliability_eval = (
                support_reliability_eval * uncertainty_reliability_eval
            )
            train_x = np.column_stack(
                [
                    (pred_rank_train - 0.5)
                    * reliability_train[:, np.newaxis],
                    reliability_train,
                ]
            )
            eval_x = np.column_stack(
                [
                    (pred_rank_eval - 0.5)
                    * reliability_eval[:, np.newaxis],
                    reliability_eval,
                ]
            )
        else:
            raise RuntimeError(f"Unknown donor transform family: {base_family}")
    if shuffled:
        train_x, eval_x = shuffled_columns(train_x, eval_x, seed)
    return train_x, eval_x


def run_draw(
    budget: int,
    repeat: int,
    metadata: pd.DataFrame,
    structure_x: np.ndarray,
    calculated_x: np.ndarray,
    blocks: dict[str, dict[str, object]],
    registry: list[dict[str, object]],
    draws: pd.DataFrame,
    config: dict[str, object],
) -> list[dict[str, object]]:
    draw = draws[(draws["budget"] == budget) & (draws["repeat"] == repeat)]
    training_keys = set(
        draw.loc[draw["role"] == "training", "target_key"].astype(str)
    )
    excluded_keys = set(
        draw.loc[
            draw["role"] == "excluded_boundary_scaffold", "target_key"
        ].astype(str)
    )
    keys = metadata["target_key"].astype(str)
    training_mask = keys.isin(training_keys).to_numpy()
    evaluation_mask = (~keys.isin(training_keys | excluded_keys)).to_numpy()
    if int(training_mask.sum()) != budget:
        raise RuntimeError(f"Budget drift: {budget}/{repeat}")
    train_groups = metadata.loc[training_mask, "scaffold"].astype(str).to_numpy()
    eval_groups = set(
        metadata.loc[evaluation_mask, "scaffold"].astype(str)
    )
    if set(train_groups) & eval_groups:
        raise RuntimeError(f"Scaffold leakage: {budget}/{repeat}")

    train_y = metadata.loc[training_mask, "log1p_her"].to_numpy(float)
    eval_y = metadata.loc[evaluation_mask, "log1p_her"].to_numpy(float)
    structure_train = structure_x[training_mask]
    structure_eval = structure_x[evaluation_mask]
    calc_train, calc_eval = impute_from_training(
        calculated_x[training_mask], calculated_x[evaluation_mask]
    )
    rf_settings = config["recipient_random_forest"]
    seed_base = SEED + budget * 100000000 + repeat * 100000
    base_prediction, base_seed_sd = rf_ensemble_prediction(
        structure_train,
        train_y,
        structure_eval,
        eval_y,
        rf_settings,
        seed_base,
    )
    inner_base = inner_target_oof(
        structure_train,
        train_y,
        train_groups,
        rf_settings,
        seed_base + 20000,
    )
    rows = [
        metric_row(
            "target_structure_only",
            base_prediction,
            eval_y,
            base_seed_sd,
            {
                "budget": budget,
                "repeat": repeat,
                "training_rows": int(training_mask.sum()),
                "evaluation_rows": int(evaluation_mask.sum()),
            },
        )
    ]
    calc_prediction, calc_seed_sd = rf_ensemble_prediction(
        np.column_stack([structure_train, calc_train]),
        train_y,
        np.column_stack([structure_eval, calc_eval]),
        eval_y,
        rf_settings,
        seed_base + 30000,
    )
    rows.append(
        metric_row(
            "target_structure_plus_calculated",
            calc_prediction,
            eval_y,
            calc_seed_sd,
            rows[0]
            | {
                "budget": budget,
                "repeat": repeat,
                "training_rows": int(training_mask.sum()),
                "evaluation_rows": int(evaluation_mask.sum()),
            },
        )
    )
    global_block = blocks["global_all_environment"]
    gaussian_dimension = max(1, len(global_block["columns"]))
    rng = np.random.default_rng(seed_base + 40000)
    gaussian_train = rng.standard_normal((budget, gaussian_dimension))
    gaussian_eval = rng.standard_normal(
        (int(evaluation_mask.sum()), gaussian_dimension)
    )
    gaussian_prediction, gaussian_seed_sd = rf_ensemble_prediction(
        np.column_stack([structure_train, gaussian_train]),
        train_y,
        np.column_stack([structure_eval, gaussian_eval]),
        eval_y,
        rf_settings,
        seed_base + 50000,
    )
    rows.append(
        metric_row(
            "target_structure_plus_gaussian",
            gaussian_prediction,
            eval_y,
            gaussian_seed_sd,
            {
                "budget": budget,
                "repeat": repeat,
                "training_rows": int(training_mask.sum()),
                "evaluation_rows": int(evaluation_mask.sum()),
            },
        )
    )

    alphas = [float(value) for value in config["ridge"]["alphas"]]
    blend_weights = [
        float(value) for value in config["ridge"]["blend_weights_for_donor"]
    ]
    for method_index, method_item in enumerate(registry[3:], start=3):
        method_name = str(method_item["method"])
        block = blocks[str(method_item["block"])]
        donor_train, donor_eval = transformed_block(
            method_item,
            block,
            training_mask,
            evaluation_mask,
            seed_base + 60000 + method_index,
        )
        family = str(method_item["family"])
        base_family = family.removeprefix("shuffled_")
        if base_family in {
            "direct_rank_predictions",
            "direct_rank_predictions_uncertainty",
            "support_gated_rank_predictions",
            "direct_raw_predictions",
        }:
            prediction, seed_sd = rf_ensemble_prediction(
                np.column_stack([structure_train, donor_train]),
                train_y,
                np.column_stack([structure_eval, donor_eval]),
                eval_y,
                rf_settings,
                seed_base + 1000000 + method_index * 100,
            )
            extra = {}
        elif base_family == "residual_ridge":
            residual = train_y - inner_base
            residual_estimator, _, alpha = ridge_group_cv(
                donor_train,
                residual,
                train_groups,
                alphas,
                seed_base + 2000000 + method_index,
            )
            prediction = np.clip(
                base_prediction + residual_estimator.predict(donor_eval),
                0.0,
                None,
            )
            seed_sd = float("nan")
            extra = {"selected_alpha": alpha, "selected_donor_weight": float("nan")}
        elif base_family == "late_fusion_ridge":
            donor_estimator, donor_oof, alpha = ridge_group_cv(
                donor_train,
                train_y,
                train_groups,
                alphas,
                seed_base + 3000000 + method_index,
            )
            weight_rmse = {
                weight: math.sqrt(
                    mean_squared_error(
                        train_y,
                        (1.0 - weight) * inner_base + weight * donor_oof,
                    )
                )
                for weight in blend_weights
            }
            selected_weight = min(
                weight_rmse, key=lambda value: (weight_rmse[value], value)
            )
            donor_prediction = donor_estimator.predict(donor_eval)
            prediction = np.clip(
                (1.0 - selected_weight) * base_prediction
                + selected_weight * donor_prediction,
                0.0,
                None,
            )
            seed_sd = float("nan")
            extra = {
                "selected_alpha": alpha,
                "selected_donor_weight": selected_weight,
            }
        else:
            raise RuntimeError(f"Unknown discovery family: {family}")
        row = metric_row(
            method_name,
            prediction,
            eval_y,
            seed_sd,
            {
                "budget": budget,
                "repeat": repeat,
                "training_rows": int(training_mask.sum()),
                "evaluation_rows": int(evaluation_mask.sum()),
                **extra,
            },
        )
        rows.append(row)
    return rows


def summarize_candidates(
    metrics: pd.DataFrame,
    registry: list[dict[str, object]],
    config: dict[str, object],
) -> tuple[pd.DataFrame, dict[str, object] | None]:
    registry_lookup = {str(item["method"]): item for item in registry}
    pivots = {
        int(budget): rows.pivot(index="repeat", columns="method", values="rmse")
        for budget, rows in metrics.groupby("budget")
    }
    candidate_rows = []
    rule = config["selection_rule"]
    primary_budget = int(rule["primary_budget"])
    for item in registry:
        if not bool(item.get("is_transfer_candidate", False)):
            continue
        method = str(item["method"])
        control = str(item["matched_control"])
        output: dict[str, object] = {
            "method": method,
            "family": item["family"],
            "block": item["block"],
            "subset": item["subset"],
            "matched_control": control,
        }
        mean_gains = {}
        for budget, pivot in pivots.items():
            baseline = pivot["target_structure_only"]
            gain = (baseline - pivot[method]) / baseline
            control_gain = (pivot[control] - pivot[method]) / pivot[control]
            mean_gains[budget] = float(gain.mean())
            output[f"mean_gain_budget_{budget}"] = float(gain.mean())
            output[f"median_gain_budget_{budget}"] = float(gain.median())
            output[f"positive_fraction_budget_{budget}"] = float(
                np.mean(gain > 0)
            )
            output[f"mean_gain_over_shuffled_budget_{budget}"] = float(
                control_gain.mean()
            )
        output["minimum_gain_across_budgets"] = float(min(mean_gains.values()))
        eligible = bool(
            mean_gains[primary_budget]
            >= float(rule["minimum_mean_relative_rmse_gain"])
            and output[f"positive_fraction_budget_{primary_budget}"]
            >= float(rule["minimum_positive_draw_fraction"])
            and all(
                mean_gains[int(budget)] >= 0
                for budget in rule["must_have_nonnegative_mean_gain_at_budgets"]
            )
            and output[f"mean_gain_over_shuffled_budget_{primary_budget}"] > 0
        )
        output["eligible_for_blind_freeze"] = eligible
        candidate_rows.append(output)
    candidate_summary = pd.DataFrame(candidate_rows).sort_values(
        [
            "eligible_for_blind_freeze",
            "minimum_gain_across_budgets",
            f"mean_gain_budget_{primary_budget}",
        ],
        ascending=[False, False, False],
    )
    eligible_rows = candidate_summary[
        candidate_summary["eligible_for_blind_freeze"]
    ]
    selected = (
        eligible_rows.iloc[0].to_dict() if len(eligible_rows) else None
    )
    return candidate_summary, selected


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jobs", type=int, default=1)
    arguments = parser.parse_args()

    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    global_summary = json.loads(
        GLOBAL_SUMMARY_PATH.read_text(encoding="utf-8")
    )
    state_summary = json.loads(STATE_SUMMARY_PATH.read_text(encoding="utf-8"))
    state_verified = json.loads(
        STATE_VERIFIED_PATH.read_text(encoding="utf-8")
    )
    draw_manifest = json.loads(
        DRAW_MANIFEST_PATH.read_text(encoding="utf-8")
    )
    if audit["design_sha256"] != file_hash(DESIGN_PATH):
        raise RuntimeError("Design changed after pair audit")
    if draw_manifest["method_config_sha256"] != file_hash(CONFIG_PATH):
        raise RuntimeError("Discovery config changed after draws were frozen")
    if state_summary["method_config_sha256"] != file_hash(CONFIG_PATH):
        raise RuntimeError("State source config mismatch")
    if state_verified["summary_sha256"] != file_hash(STATE_SUMMARY_PATH):
        raise RuntimeError("State source verification mismatch")
    if global_summary["feature_sha256"] != file_hash(GLOBAL_FEATURE_PATH):
        raise RuntimeError("Global donor feature mismatch")
    if state_summary["feature_sha256"] != file_hash(STATE_FEATURE_PATH):
        raise RuntimeError("State donor feature mismatch")
    if (
        file_hash(TARGET_PATH)
        != design["target"]["development_file"]["required_sha256"]
    ):
        raise RuntimeError("Development target file changed")

    metadata = (
        pd.read_csv(METADATA_PATH)
        .query("split == 'development'")
        .sort_values("target_key")
        .reset_index(drop=True)
    )
    global_features = (
        pd.read_csv(GLOBAL_FEATURE_PATH)
        .query("split == 'development'")
        .sort_values("target_key")
        .reset_index(drop=True)
    )
    state_features = (
        pd.read_csv(STATE_FEATURE_PATH)
        .query("split == 'development'")
        .sort_values("target_key")
        .reset_index(drop=True)
    )
    if not (
        metadata["target_key"].equals(global_features["target_key"])
        and metadata["target_key"].equals(state_features["target_key"])
    ):
        raise RuntimeError("Recipient feature tables do not align")

    blocks = build_blocks(
        global_summary, global_features, state_summary, state_features
    )
    registry = build_registry(blocks, config["property_subsets"])
    registry_payload = {
        "status": "registry-frozen-from-source-only-admissions",
        "created_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "method_config_sha256": file_hash(CONFIG_PATH),
        "global_source_summary_sha256": file_hash(GLOBAL_SUMMARY_PATH),
        "state_source_summary_sha256": file_hash(STATE_SUMMARY_PATH),
        "methods": registry,
        "method_count": len(registry),
        "recipient_outcome_access_for_registry": False,
    }
    REGISTRY_PATH.write_text(
        json.dumps(registry_payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    target = pd.read_csv(TARGET_PATH)
    target["target_key"] = "development:" + target["ID"].astype(str)
    target = metadata[["target_key"]].merge(
        target, on="target_key", how="left", validate="one_to_one"
    )
    her_columns = [column for column in target.columns if "HER" in column]
    if len(her_columns) != 1:
        raise RuntimeError("Could not identify development HER column")
    outcome_column = her_columns[0]
    her = pd.to_numeric(target[outcome_column], errors="coerce")
    if her.isna().any() or (her < 0).any():
        raise RuntimeError("Development HER contains missing or negative values")
    metadata["log1p_her"] = np.log1p(her.to_numpy(float))

    calculated_columns = [
        "EA* (V)",
        "EA (V)",
        "Sr (a.u.)",
        "Δσ (Ang)",
        "H_CT (Ang)",
        "ΔD (a.u.)",
        "E_eb (eV)",
        "E_sol (eV)",
        "E_b (eV)",
        "S1-S0 (eV)",
        "S1-T1 (eV)",
    ]
    calculated_x = target[calculated_columns].apply(
        pd.to_numeric, errors="coerce"
    ).to_numpy(float)
    structure_x = feature_matrix(metadata["canonical_smiles"].astype(str).tolist())
    draws = pd.read_csv(DRAW_PATH)
    budgets = [int(value) for value in draw_manifest["budgets"]]
    repeats = int(draw_manifest["repeats_per_budget"])
    nested_rows = Parallel(n_jobs=arguments.jobs, verbose=10)(
        delayed(run_draw)(
            budget,
            repeat,
            metadata,
            structure_x,
            calculated_x,
            blocks,
            registry,
            draws,
            config,
        )
        for budget in budgets
        for repeat in range(repeats)
    )
    metrics = pd.DataFrame(
        [row for task_rows in nested_rows for row in task_rows]
    ).sort_values(["budget", "repeat", "method"])
    metrics.to_csv(METRICS_PATH, index=False, lineterminator="\n")
    candidate_summary, selected = summarize_candidates(
        metrics, registry, config
    )
    candidate_summary.to_csv(
        CANDIDATE_SUMMARY_PATH, index=False, lineterminator="\n"
    )
    summary = {
        "status": (
            "development-discovery-candidate-selected"
            if selected is not None
            else "development-discovery-abstained"
        ),
        "created_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "design_sha256": file_hash(DESIGN_PATH),
        "method_config_sha256": file_hash(CONFIG_PATH),
        "implementation_sha256": file_hash(Path(__file__)),
        "pair_audit_sha256": file_hash(AUDIT_PATH),
        "global_source_summary_sha256": file_hash(GLOBAL_SUMMARY_PATH),
        "state_source_summary_sha256": file_hash(STATE_SUMMARY_PATH),
        "state_source_verified_sha256": file_hash(STATE_VERIFIED_PATH),
        "draw_manifest_sha256": file_hash(DRAW_MANIFEST_PATH),
        "draw_sha256": file_hash(DRAW_PATH),
        "registry_sha256": file_hash(REGISTRY_PATH),
        "metrics_sha256": file_hash(METRICS_PATH),
        "candidate_summary_sha256": file_hash(CANDIDATE_SUMMARY_PATH),
        "method_count": len(registry),
        "metric_rows": int(len(metrics)),
        "selected_strategy": selected,
        "eligible_candidate_count": int(
            candidate_summary["eligible_for_blind_freeze"].sum()
        ),
        "top_candidates": candidate_summary.head(20).to_dict(orient="records"),
        "blind_outcome_access": (
            "The blind target file was not opened, parsed, hashed, or joined."
        ),
        "claim_guard": config["claim_guard"],
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
            "rdkit": rdkit.__version__,
        },
    }
    SUMMARY_PATH.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
