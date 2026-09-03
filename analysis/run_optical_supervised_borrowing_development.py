"""Evaluate one focused supervised borrowing strategy on development OOD splits."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import rdkit
import sklearn
from joblib import Parallel, delayed
from rdkit import Chem, RDLogger
from rdkit.Chem import rdFingerprintGenerator
from scipy import stats
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CONFIG_PATH = HERE / "optical_supervised_borrowing_config.json"
DESIGN_PATH = HERE / "optical_photocatalysis_borrowing_design.json"
AUDIT_PATH = HERE / "results" / "optical_photocatalysis_pair_audit.json"
METADATA_PATH = HERE / "results" / "optical_photocatalysis_target_metadata.csv"
DRAW_PATH = HERE / "results" / "optical_transfer_method_discovery_draws.csv"
SCOPE_PATH = HERE / "results" / "optical_supervised_borrowing_scopes.csv"
SCOPE_MANIFEST_PATH = (
    HERE / "results" / "optical_supervised_borrowing_scopes_manifest.json"
)
SOURCE_SUMMARY_PATH = (
    HERE / "results" / "optical_supervised_source_summary.json"
)
EMBEDDING_PATH = (
    HERE / "results" / "optical_supervised_source_embeddings.npz"
)
SCALAR_FEATURE_PATH = (
    HERE / "results" / "optical_photocatalysis_donor_features.csv"
)
TARGET_PATH = (
    ROOT
    / "data"
    / "external"
    / "optical_photocatalysis"
    / "SC-012-D1SC02150H-s005.csv"
)
METRICS_PATH = (
    HERE / "results" / "optical_supervised_borrowing_metrics.csv"
)
CONTRAST_PATH = (
    HERE / "results" / "optical_supervised_borrowing_contrasts.csv"
)
SUMMARY_PATH = (
    HERE / "results" / "optical_supervised_borrowing_summary.json"
)
RELEASE_PATH = (
    HERE / "results" / "optical_supervised_borrowing_release.json"
)

RDLogger.DisableLog("rdApp.error")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def seed32(value: int) -> int:
    return int(value % (2**32 - 1))


def feature_matrix(smiles_values: list[str]) -> np.ndarray:
    generator = rdFingerprintGenerator.GetMorganGenerator(
        radius=2, fpSize=2048, includeChirality=True
    )
    output = np.zeros((len(smiles_values), 2048), dtype=np.uint8)
    for row, smiles in enumerate(smiles_values):
        molecule = Chem.MolFromSmiles(smiles)
        if molecule is None:
            raise RuntimeError(f"Audited target structure no longer parses: {smiles}")
        output[row] = generator.GetFingerprintAsNumPy(molecule)
    return output


def make_regressor(
    settings: dict[str, Any], seed: int
) -> RandomForestRegressor:
    return RandomForestRegressor(
        n_estimators=int(settings["n_estimators"]),
        min_samples_leaf=int(settings["min_samples_leaf"]),
        max_features=float(settings["max_features"]),
        random_state=seed32(seed),
        n_jobs=1,
    )


def make_classifier(
    settings: dict[str, Any], seed: int
) -> RandomForestClassifier:
    return RandomForestClassifier(
        n_estimators=int(settings["n_estimators"]),
        min_samples_leaf=int(settings["min_samples_leaf"]),
        max_features=float(settings["max_features"]),
        class_weight="balanced",
        random_state=seed32(seed),
        n_jobs=1,
    )


def direct_prediction(
    train_x: np.ndarray,
    train_y: np.ndarray,
    eval_x: np.ndarray,
    settings: dict[str, Any],
    seed_base: int,
    seeds: int,
) -> np.ndarray:
    output = []
    for seed_index in range(seeds):
        estimator = make_regressor(settings, seed_base + seed_index)
        estimator.fit(train_x, train_y)
        output.append(estimator.predict(eval_x))
    return np.mean(np.vstack(output), axis=0)


def hurdle_prediction(
    train_x: np.ndarray,
    train_y: np.ndarray,
    eval_x: np.ndarray,
    settings: dict[str, Any],
    seed_base: int,
    seeds: int,
) -> tuple[np.ndarray, bool]:
    active = train_y > 0
    if int(active.sum()) < 5 or int((~active).sum()) < 5:
        return (
            direct_prediction(
                train_x,
                train_y,
                eval_x,
                settings,
                seed_base,
                seeds,
            ),
            True,
        )
    output = []
    for seed_index in range(seeds):
        classifier = make_classifier(
            settings, seed_base + 10000 + seed_index
        )
        regressor = make_regressor(
            settings, seed_base + 20000 + seed_index
        )
        classifier.fit(train_x, active)
        regressor.fit(train_x[active], train_y[active])
        active_column = list(classifier.classes_).index(True)
        probability = classifier.predict_proba(eval_x)[:, active_column]
        output.append(probability * regressor.predict(eval_x))
    return np.mean(np.vstack(output), axis=0), False


def target_oof_prediction(
    train_x: np.ndarray,
    train_y: np.ndarray,
    groups: np.ndarray,
    settings: dict[str, Any],
    seed_base: int,
) -> tuple[np.ndarray, int]:
    folds = min(
        int(settings["inner_group_folds"]),
        len(set(groups.astype(str))),
    )
    if folds < 2:
        raise RuntimeError("Insufficient target scaffolds for inner OOF")
    splitter = GroupKFold(
        n_splits=folds, shuffle=True, random_state=seed32(seed_base)
    )
    output = np.full(len(train_y), np.nan)
    fallback_folds = 0
    for fold, (fit_rows, held_rows) in enumerate(
        splitter.split(train_x, train_y, groups)
    ):
        prediction, fallback = hurdle_prediction(
            train_x[fit_rows],
            train_y[fit_rows],
            train_x[held_rows],
            settings,
            seed_base + 100000 * (fold + 1),
            int(settings["inner_oof_seeds"]),
        )
        output[held_rows] = prediction
        fallback_folds += int(fallback)
    if not np.isfinite(output).all():
        raise RuntimeError("Incomplete target OOF prediction")
    return output, fallback_folds


def impute_from_training(
    training: np.ndarray, evaluation: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    training = training.astype(float, copy=True)
    evaluation = evaluation.astype(float, copy=True)
    medians = np.nanmedian(training, axis=0)
    medians[~np.isfinite(medians)] = 0.0
    for values in [training, evaluation]:
        missing = ~np.isfinite(values)
        if missing.any():
            values[missing] = np.take(medians, np.where(missing)[1])
    return training, evaluation


def adapter_prediction(
    blocks_train: list[np.ndarray],
    blocks_eval: list[np.ndarray],
    train_y: np.ndarray,
    base_oof: np.ndarray,
    base_eval: np.ndarray,
    selection_base_oof: np.ndarray,
    selection_folds: list[
        tuple[np.ndarray, np.ndarray, np.ndarray]
    ],
    reliability_train: np.ndarray,
    reliability_eval: np.ndarray,
    settings: dict[str, Any],
) -> tuple[np.ndarray, float, float, float]:
    if len(blocks_train) != len(blocks_eval) or not blocks_train:
        raise ValueError("Adapter blocks must be paired and nonempty")
    residual = train_y - base_oof
    alpha_predictions: dict[float, np.ndarray] = {}
    final_predictions: dict[float, np.ndarray] = {}
    for alpha_value in settings["alphas"]:
        alpha = float(alpha_value)
        seed_oof = []
        seed_eval = []
        for train_block, eval_block in zip(
            blocks_train, blocks_eval, strict=True
        ):
            train_block, eval_block = impute_from_training(
                train_block, eval_block
            )
            oof = np.full(len(train_y), np.nan)
            for fit_rows, held_rows, fit_residual in selection_folds:
                estimator = make_pipeline(
                    StandardScaler(),
                    Ridge(alpha=alpha),
                )
                estimator.fit(train_block[fit_rows], fit_residual)
                oof[held_rows] = estimator.predict(train_block[held_rows])
            if not np.isfinite(oof).all():
                raise RuntimeError("Incomplete residual-adapter OOF")
            final = make_pipeline(
                StandardScaler(),
                Ridge(alpha=alpha),
            )
            final.fit(train_block, residual)
            seed_oof.append(oof)
            seed_eval.append(final.predict(eval_block))
        alpha_predictions[alpha] = np.mean(np.vstack(seed_oof), axis=0)
        final_predictions[alpha] = np.mean(np.vstack(seed_eval), axis=0)

    candidates = []
    for alpha, residual_oof in alpha_predictions.items():
        for weight_value in settings["correction_weights"]:
            weight = float(weight_value)
            prediction = (
                selection_base_oof
                + weight * reliability_train * residual_oof
            )
            candidates.append(
                (
                    float(mean_squared_error(train_y, prediction)),
                    weight,
                    alpha,
                )
            )
    _, selected_weight, selected_alpha = min(
        candidates, key=lambda item: (item[0], item[1], item[2])
    )
    correction = (
        selected_weight
        * reliability_eval
        * final_predictions[selected_alpha]
    )
    return (
        base_eval + correction,
        selected_alpha,
        selected_weight,
        float(np.mean(np.abs(correction))),
    )


def nested_adapter_selection_cache(
    train_x: np.ndarray,
    train_y: np.ndarray,
    groups: np.ndarray,
    target_settings: dict[str, Any],
    adapter_settings: dict[str, Any],
    seed_base: int,
) -> tuple[
    np.ndarray,
    list[tuple[np.ndarray, np.ndarray, np.ndarray]],
]:
    outer_folds = min(
        int(adapter_settings["selection_outer_group_folds"]),
        len(set(groups.astype(str))),
    )
    if outer_folds < 2:
        raise RuntimeError("Insufficient groups for nested adapter selection")
    splitter = GroupKFold(
        n_splits=outer_folds,
        shuffle=True,
        random_state=seed32(seed_base),
    )
    selection_base = np.full(len(train_y), np.nan)
    selection_folds = []
    for fold, (fit_rows, held_rows) in enumerate(
        splitter.split(train_x, train_y, groups)
    ):
        nested_settings = dict(target_settings)
        nested_settings["inner_group_folds"] = int(
            adapter_settings["selection_inner_group_folds"]
        )
        fit_oof, _ = target_oof_prediction(
            train_x[fit_rows],
            train_y[fit_rows],
            groups[fit_rows],
            nested_settings,
            seed_base + 1000000 * (fold + 1),
        )
        held_prediction, _ = hurdle_prediction(
            train_x[fit_rows],
            train_y[fit_rows],
            train_x[held_rows],
            target_settings,
            seed_base + 2000000 * (fold + 1),
            int(target_settings["inner_oof_seeds"]),
        )
        selection_base[held_rows] = held_prediction
        selection_folds.append(
            (fit_rows, held_rows, train_y[fit_rows] - fit_oof)
        )
    if not np.isfinite(selection_base).all():
        raise RuntimeError("Incomplete nested adapter base predictions")
    return selection_base, selection_folds


def metric_row(
    budget: int,
    repeat: int,
    method: str,
    scope: str,
    observed: np.ndarray,
    prediction: np.ndarray,
    selected_alpha: float | None = None,
    selected_weight: float | None = None,
    mean_absolute_correction: float | None = None,
    active_training_rows: int | None = None,
    fallback_folds: int | None = None,
    training_scaffolds: int | None = None,
    insufficient_scaffold_abstention: bool = False,
) -> dict[str, Any]:
    spearman = stats.spearmanr(observed, prediction).statistic
    return {
        "budget": int(budget),
        "repeat": int(repeat),
        "method": method,
        "scope": scope,
        "evaluation_rows": int(len(observed)),
        "rmse": float(math.sqrt(mean_squared_error(observed, prediction))),
        "mae": float(mean_absolute_error(observed, prediction)),
        "r2": float(r2_score(observed, prediction)),
        "spearman": (
            float(spearman) if np.isfinite(spearman) else np.nan
        ),
        "selected_alpha": selected_alpha,
        "selected_correction_weight": selected_weight,
        "mean_absolute_correction": mean_absolute_correction,
        "active_training_rows": active_training_rows,
        "inner_hurdle_fallback_folds": fallback_folds,
        "training_scaffolds": training_scaffolds,
        "insufficient_scaffold_abstention": bool(
            insufficient_scaffold_abstention
        ),
    }


def run_draw(
    budget: int,
    repeat: int,
    development: pd.DataFrame,
    structure_x: np.ndarray,
    draws: pd.DataFrame,
    scopes: pd.DataFrame,
    method_blocks: dict[str, list[np.ndarray]],
    method_reliability: dict[str, np.ndarray],
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    draw_rows = draws[
        (draws["budget"] == budget) & (draws["repeat"] == repeat)
    ]
    training_keys = set(
        draw_rows.loc[
            draw_rows["role"] == "training", "target_key"
        ].astype(str)
    )
    excluded_keys = set(draw_rows["target_key"].astype(str))
    train_mask = development["target_key"].astype(str).isin(training_keys)
    eval_mask = ~development["target_key"].astype(str).isin(excluded_keys)
    train_rows = np.flatnonzero(train_mask.to_numpy())
    eval_rows = np.flatnonzero(eval_mask.to_numpy())
    if len(train_rows) != budget:
        raise RuntimeError(f"Training budget drift at {budget}/{repeat}")

    y = development["log1p_her"].to_numpy(float)
    train_y = y[train_rows]
    groups = development["scaffold"].astype(str).to_numpy()[train_rows]
    training_scaffolds = len(set(groups.astype(str)))
    insufficient_scaffold_abstention = training_scaffolds < 3
    target_settings = config["target_hurdle_model"]
    seed_base = 202607260000 + 1000 * budget + repeat
    base_eval, final_fallback = hurdle_prediction(
        structure_x[train_rows],
        train_y,
        structure_x[eval_rows],
        target_settings,
        seed_base + 50000000,
        int(target_settings["final_seeds_per_draw"]),
    )
    direct_eval = direct_prediction(
        structure_x[train_rows],
        train_y,
        structure_x[eval_rows],
        target_settings,
        seed_base + 60000000,
        int(target_settings["final_seeds_per_draw"]),
    )

    predictions = {
        "target_only_direct_regression": direct_eval,
        "target_only_hurdle": base_eval,
    }
    adapter_details: dict[str, tuple[float, float, float]] = {}
    if insufficient_scaffold_abstention:
        fallback_folds = 0
        abstention_alpha = float(min(config["target_adapter"]["alphas"]))
        for method in method_blocks:
            predictions[method] = base_eval.copy()
            adapter_details[method] = (abstention_alpha, 0.0, 0.0)
    else:
        base_oof, fallback_folds = target_oof_prediction(
            structure_x[train_rows],
            train_y,
            groups,
            target_settings,
            seed_base,
        )
        selection_base_oof, selection_folds = (
            nested_adapter_selection_cache(
                structure_x[train_rows],
                train_y,
                groups,
                target_settings,
                config["target_adapter"],
                seed_base + 65000000,
            )
        )
        for method, blocks in method_blocks.items():
            prediction, alpha, weight, correction = adapter_prediction(
                [block[train_rows] for block in blocks],
                [block[eval_rows] for block in blocks],
                train_y,
                base_oof,
                base_eval,
                selection_base_oof,
                selection_folds,
                method_reliability[method][train_rows],
                method_reliability[method][eval_rows],
                config["target_adapter"],
            )
            predictions[method] = prediction
            adapter_details[method] = (alpha, weight, correction)

    scope_rows = scopes[
        (scopes["budget"] == budget) & (scopes["repeat"] == repeat)
    ].set_index("target_key")
    eval_keys = development.iloc[eval_rows]["target_key"].astype(str).to_numpy()
    if set(eval_keys) != set(scope_rows.index.astype(str)):
        raise RuntimeError(f"Dynamic scope membership drift at {budget}/{repeat}")
    hard_keys = set(
        scope_rows.loc[
            scope_rows["dynamic_hard_ood_40pct"].astype(bool)
        ].index.astype(str)
    )
    hard_mask = np.asarray([key in hard_keys for key in eval_keys])
    scope_masks = {
        "full_scaffold_separated_evaluation": np.ones(
            len(eval_rows), dtype=bool
        ),
        "dynamic_hard_ood_40pct": hard_mask,
    }

    output = []
    for method, prediction in predictions.items():
        details = adapter_details.get(method)
        for scope, mask in scope_masks.items():
            output.append(
                metric_row(
                    budget,
                    repeat,
                    method,
                    scope,
                    y[eval_rows][mask],
                    prediction[mask],
                    selected_alpha=(details[0] if details else None),
                    selected_weight=(details[1] if details else None),
                    mean_absolute_correction=(
                        details[2] if details else None
                    ),
                    active_training_rows=int((train_y > 0).sum()),
                    fallback_folds=(
                        fallback_folds + int(final_fallback)
                    ),
                    training_scaffolds=training_scaffolds,
                    insufficient_scaffold_abstention=(
                        insufficient_scaffold_abstention
                    ),
                )
            )
    return output


def summarize(
    metrics: pd.DataFrame, config: dict[str, Any]
) -> tuple[pd.DataFrame, dict[str, Any]]:
    draw_audit = metrics[
        [
            "budget",
            "repeat",
            "training_scaffolds",
            "insufficient_scaffold_abstention",
        ]
    ].drop_duplicates()
    if len(draw_audit) != (
        len(config["development"]["label_budgets"])
        * int(config["development"]["draws_per_budget"])
    ):
        raise RuntimeError("Development draw-level scaffold audit is incomplete")
    abstention_counts = (
        draw_audit[
            draw_audit["insufficient_scaffold_abstention"].astype(bool)
        ]
        .groupby("budget")
        .size()
        .reindex(
            [int(value) for value in config["development"]["label_budgets"]],
            fill_value=0,
        )
    )
    baseline = metrics[
        metrics["method"] == "target_only_hurdle"
    ][["budget", "repeat", "scope", "rmse"]].rename(
        columns={"rmse": "target_only_rmse"}
    )
    contrasts = metrics.merge(
        baseline, on=["budget", "repeat", "scope"], how="left"
    )
    contrasts["relative_rmse_gain"] = (
        contrasts["target_only_rmse"] - contrasts["rmse"]
    ) / contrasts["target_only_rmse"]
    contrast_rows = contrasts[
        contrasts["method"] != "target_only_hurdle"
    ].copy()
    grouped = (
        contrast_rows.groupby(["budget", "scope", "method"], as_index=False)
        .agg(
            mean_rmse=("rmse", "mean"),
            mean_relative_rmse_gain=("relative_rmse_gain", "mean"),
            median_relative_rmse_gain=("relative_rmse_gain", "median"),
            positive_draw_fraction=(
                "relative_rmse_gain",
                lambda values: float((values > 0).mean()),
            ),
            q025_relative_rmse_gain=(
                "relative_rmse_gain",
                lambda values: float(np.quantile(values, 0.025)),
            ),
            q975_relative_rmse_gain=(
                "relative_rmse_gain",
                lambda values: float(np.quantile(values, 0.975)),
            ),
            nonzero_correction_fraction=(
                "selected_correction_weight",
                lambda values: float((values.fillna(0) > 0).mean()),
            ),
        )
    )

    gate = config["development_release_gate"]
    primary_method = str(gate["primary_method"])
    primary_budget = int(config["development"]["primary_budget"])
    primary_scope = str(config["development"]["primary_scope"])

    def row_for(method: str, budget: int, scope: str) -> pd.Series:
        rows = grouped[
            (grouped["method"] == method)
            & (grouped["budget"] == budget)
            & (grouped["scope"] == scope)
        ]
        if len(rows) != 1:
            raise RuntimeError(
                f"Missing summary row for {method}/{budget}/{scope}"
            )
        return rows.iloc[0]

    primary = row_for(primary_method, primary_budget, primary_scope)
    shuffled = row_for(
        "shuffled_source_pretrained_residual",
        primary_budget,
        primary_scope,
    )
    state_blind = row_for(
        "state_blind_pretrained_residual",
        primary_budget,
        primary_scope,
    )
    checks: dict[str, bool] = {
        "minimum_primary_mean_gain": bool(
            primary["mean_relative_rmse_gain"]
            >= float(
                gate[
                    "minimum_mean_relative_rmse_gain_primary_scope_primary_budget"
                ]
            )
        ),
        "minimum_primary_positive_fraction": bool(
            primary["positive_draw_fraction"]
            >= float(
                gate[
                    "minimum_positive_draw_fraction_primary_scope_primary_budget"
                ]
            )
        ),
        "beats_shuffled_source": bool(
            primary["mean_relative_rmse_gain"]
            - shuffled["mean_relative_rmse_gain"]
            >= float(
                gate[
                    "minimum_mean_gain_over_shuffled_source_primary_scope_primary_budget"
                ]
            )
        ),
        "beats_state_blind": bool(
            primary["mean_relative_rmse_gain"]
            - state_blind["mean_relative_rmse_gain"]
            >= float(
                gate[
                    "minimum_mean_gain_over_state_blind_primary_scope_primary_budget"
                ]
            )
        ),
        "nonzero_correction_used": bool(
            primary["nonzero_correction_fraction"]
            >= float(
                gate[
                    "minimum_fraction_nonzero_selected_correction_primary_budget"
                ]
            )
        ),
    }
    other_budget_rows = [
        row_for(primary_method, budget, primary_scope)
        for budget in config["development"]["label_budgets"]
        if int(budget) != primary_budget
    ]
    checks["nonnegative_other_budget_hard_ood"] = all(
        float(row["mean_relative_rmse_gain"]) >= 0.0
        for row in other_budget_rows
    )
    full_rows = [
        row_for(
            primary_method,
            int(budget),
            "full_scaffold_separated_evaluation",
        )
        for budget in config["development"]["label_budgets"]
    ]
    checks["bounded_full_scope_harm"] = all(
        float(row["mean_relative_rmse_gain"])
        >= -float(gate["maximum_mean_full_scope_harm_any_budget"])
        for row in full_rows
    )
    admitted = all(checks.values())
    summary = {
        "status": (
            "development-release-approved"
            if admitted
            else "development-abstained"
        ),
        "primary_method": primary_method,
        "primary_budget": primary_budget,
        "primary_scope": primary_scope,
        "primary_mean_relative_rmse_gain": float(
            primary["mean_relative_rmse_gain"]
        ),
        "primary_positive_draw_fraction": float(
            primary["positive_draw_fraction"]
        ),
        "primary_nonzero_correction_fraction": float(
            primary["nonzero_correction_fraction"]
        ),
        "mean_gain_margin_over_shuffled": float(
            primary["mean_relative_rmse_gain"]
            - shuffled["mean_relative_rmse_gain"]
        ),
        "mean_gain_margin_over_state_blind": float(
            primary["mean_relative_rmse_gain"]
            - state_blind["mean_relative_rmse_gain"]
        ),
        "gate_checks": checks,
        "admitted_to_blind": admitted,
        "insufficient_scaffold_abstention_draws": int(
            draw_audit["insufficient_scaffold_abstention"].astype(bool).sum()
        ),
        "insufficient_scaffold_abstention_draws_by_budget": {
            str(int(budget)): int(count)
            for budget, count in abstention_counts.items()
        },
        "insufficient_scaffold_rule": (
            "Donor correction is forced to zero when a frozen labeled draw "
            "contains fewer than three unique target scaffolds; the draw "
            "remains in every aggregate metric."
        ),
        "method_summary": grouped.to_dict(orient="records"),
        "claim_guard": config["claim_guard"],
    }
    return contrast_rows, summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jobs", type=int, default=1)
    arguments = parser.parse_args()

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    scope_manifest = json.loads(
        SCOPE_MANIFEST_PATH.read_text(encoding="utf-8")
    )
    source_summary = json.loads(
        SOURCE_SUMMARY_PATH.read_text(encoding="utf-8")
    )
    if audit["design_sha256"] != sha256(DESIGN_PATH):
        raise RuntimeError("Pair design changed after audit")
    if audit["recipient"]["metadata_sha256"] != sha256(METADATA_PATH):
        raise RuntimeError("Outcome-free target metadata changed")
    if design["target"]["development_file"]["required_sha256"] != sha256(
        TARGET_PATH
    ):
        raise RuntimeError("Development target file changed")
    if sha256(DRAW_PATH) != config["development"]["reused_draw_sha256"]:
        raise RuntimeError("Frozen draw file changed")
    if scope_manifest["focused_config_sha256"] != sha256(CONFIG_PATH):
        raise RuntimeError("Dynamic OOD scopes predate focused config")
    if scope_manifest["scope_sha256"] != sha256(SCOPE_PATH):
        raise RuntimeError("Dynamic OOD scope file changed")
    if source_summary["focused_config_sha256"] != sha256(CONFIG_PATH):
        raise RuntimeError("Source representation predates focused config")
    if source_summary["embedding_sha256"] != sha256(EMBEDDING_PATH):
        raise RuntimeError("Source representation file changed")
    if not bool(source_summary["primary_scope_gate_passed"]):
        raise RuntimeError("Primary source representation skill gate failed")

    metadata = (
        pd.read_csv(METADATA_PATH)
        .query("split == 'development'")
        .sort_values("target_key")
        .reset_index(drop=True)
    )
    target = pd.read_csv(TARGET_PATH)
    outcome_column = [
        column for column in target.columns if str(column).startswith("HER")
    ]
    if len(outcome_column) != 1:
        raise RuntimeError("Development HER column is ambiguous")
    outcome = target.set_index("ID")[outcome_column[0]]
    metadata["log1p_her"] = np.log1p(
        metadata["ID"].map(outcome).to_numpy(float)
    )
    if not np.isfinite(metadata["log1p_her"]).all():
        raise RuntimeError("Development outcome join failed")

    structure_x = feature_matrix(
        metadata["canonical_smiles"].astype(str).tolist()
    )
    # The archive hash is verified against the source summary above. Pandas
    # 2.3 may serialize the plain-string key column with NumPy object dtype,
    # so apply the same narrow, type-checked compatibility rule as the
    # independent source verifier.
    with np.load(EMBEDDING_PATH, allow_pickle=True) as embeddings:
        raw_embedding_keys = embeddings["target_key"]
        if raw_embedding_keys.dtype.kind not in {"O", "U", "S"}:
            raise RuntimeError("Unexpected source target-key dtype")
        if raw_embedding_keys.dtype.kind == "O" and not all(
            isinstance(value, str)
            for value in raw_embedding_keys.tolist()
        ):
            raise RuntimeError("Non-string object in source target keys")
        embedding_keys = raw_embedding_keys.astype(str)
        key_to_row = {
            key: row for row, key in enumerate(embedding_keys)
        }
        selected_rows = np.asarray(
            [key_to_row[key] for key in metadata["target_key"].astype(str)]
        )
        aligned_blocks = [
            embeddings[key][selected_rows]
            for key in sorted(embeddings.files)
            if key.startswith("aligned_seed_")
        ]
        global_blocks = [
            embeddings[key][selected_rows]
            for key in sorted(embeddings.files)
            if key.startswith("global_seed_")
        ]
        shuffled_blocks = [
            embeddings[key][selected_rows]
            for key in sorted(embeddings.files)
            if key.startswith("shuffled_seed_")
        ]
        for name, blocks in {
            "aligned": aligned_blocks,
            "global": global_blocks,
            "shuffled": shuffled_blocks,
        }.items():
            if any(
                block.dtype.kind not in {"f", "i", "u"}
                for block in blocks
            ):
                raise RuntimeError(f"Nonnumeric {name} source embedding")
        aligned_reliability = embeddings[
            "state_aligned_reliability"
        ][selected_rows].astype(float)
        aqueous_support = embeddings[
            "support_aqueous_small_alcohol"
        ][selected_rows].astype(float)
        solid_support = embeddings[
            "support_self_host_solid"
        ][selected_rows].astype(float)

    scalar = pd.read_csv(SCALAR_FEATURE_PATH).set_index("target_key")
    scalar_columns = [
        column
        for column in scalar.columns
        if column.startswith("pred_") or column.startswith("unc_")
    ]
    scalar_block = scalar.loc[
        metadata["target_key"].astype(str), scalar_columns
    ].to_numpy(float)
    low = float(config["source_reliability"]["zero_support_tanimoto"])
    high = float(config["source_reliability"]["full_support_tanimoto"])
    global_support = metadata[
        "max_similarity_to_retained_donor"
    ].to_numpy(float)
    global_reliability = np.clip(
        (global_support - low) / (high - low), 0.0, 1.0
    )
    method_blocks = {
        "state_aligned_pretrained_residual": aligned_blocks,
        "state_blind_pretrained_residual": global_blocks,
        "shuffled_source_pretrained_residual": shuffled_blocks,
        "scalar_optical_residual": [scalar_block],
    }
    method_reliability = {
        "state_aligned_pretrained_residual": aligned_reliability,
        "state_blind_pretrained_residual": global_reliability,
        "shuffled_source_pretrained_residual": aligned_reliability,
        "scalar_optical_residual": global_reliability,
    }
    if not aligned_blocks or not global_blocks or not shuffled_blocks:
        raise RuntimeError("Required source representation block is missing")
    if np.allclose(aqueous_support, solid_support):
        raise RuntimeError("State-specific support vectors unexpectedly match")

    draws = pd.read_csv(DRAW_PATH)
    scopes = pd.read_csv(SCOPE_PATH)
    tasks = [
        (int(budget), repeat)
        for budget in config["development"]["label_budgets"]
        for repeat in range(int(config["development"]["draws_per_budget"]))
    ]
    rows = Parallel(n_jobs=arguments.jobs, verbose=10)(
        delayed(run_draw)(
            budget,
            repeat,
            metadata,
            structure_x,
            draws,
            scopes,
            method_blocks,
            method_reliability,
            config,
        )
        for budget, repeat in tasks
    )
    metrics = pd.DataFrame(
        [row for group in rows for row in group]
    ).sort_values(["budget", "repeat", "scope", "method"])
    metrics.to_csv(METRICS_PATH, index=False, lineterminator="\n")
    contrasts, summary = summarize(metrics, config)
    contrasts.to_csv(CONTRAST_PATH, index=False, lineterminator="\n")
    summary.update(
        {
            "created_utc": pd.Timestamp.now(tz="UTC").isoformat(),
            "design_sha256": sha256(DESIGN_PATH),
            "focused_config_sha256": sha256(CONFIG_PATH),
            "pair_audit_sha256": sha256(AUDIT_PATH),
            "scope_manifest_sha256": sha256(SCOPE_MANIFEST_PATH),
            "source_summary_sha256": sha256(SOURCE_SUMMARY_PATH),
            "embedding_sha256": sha256(EMBEDDING_PATH),
            "development_target_sha256": sha256(TARGET_PATH),
            "implementation_sha256": sha256(Path(__file__)),
            "metrics_sha256": sha256(METRICS_PATH),
            "contrasts_sha256": sha256(CONTRAST_PATH),
            "metric_rows": int(len(metrics)),
            "contrast_rows": int(len(contrasts)),
            "environment": {
                "python": platform.python_version(),
                "numpy": np.__version__,
                "pandas": pd.__version__,
                "scikit_learn": sklearn.__version__,
                "rdkit": rdkit.__version__,
            },
            "blind_outcome_access": (
                "No blind HER file was opened, parsed, or joined."
            ),
        }
    )
    SUMMARY_PATH.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    release = {
        "status": (
            "blind-release-candidate"
            if summary["admitted_to_blind"]
            else "blind-release-denied"
        ),
        "created_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "focused_config_sha256": sha256(CONFIG_PATH),
        "source_summary_sha256": sha256(SOURCE_SUMMARY_PATH),
        "embedding_sha256": sha256(EMBEDDING_PATH),
        "scope_manifest_sha256": sha256(SCOPE_MANIFEST_PATH),
        "development_summary_sha256": sha256(SUMMARY_PATH),
        "development_metrics_sha256": sha256(METRICS_PATH),
        "selected_method": (
            summary["primary_method"]
            if summary["admitted_to_blind"]
            else None
        ),
        "blind_outcomes_opened": False,
        "claim_guard": config["claim_guard"],
    }
    RELEASE_PATH.write_text(
        json.dumps(release, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(json.dumps(release, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
