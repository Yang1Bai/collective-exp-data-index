"""Local method-development screen for SAFE-MAMB.

This script deliberately focuses on three deployment contracts.  It fixes a
train/deployment mismatch in the earlier quick smoke by cross-fitting source
predictions by target material identity, then learns only a ridge-shrunk
correction to a target-only out-of-fold prediction.  A zero blend is always
available.

The screen is outcome-informed method development, not confirmatory evidence.
"""
from __future__ import annotations

import argparse
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from sklearn.base import clone
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from common import RESULTS, ensure_output_dirs, sample_groups
from run_knowledge_map import (
    build_feature_spaces,
    fit_source_models,
    load_task,
    partition_targets,
    source_model,
)
from run_multi_target_ood_borrowing import (
    DESIGN_PATH as PARENT_DESIGN_PATH,
    assign_group_quartiles,
    make_target_learner,
    regression_metrics,
    stable_seed,
    validate_freeze,
)


HERE = Path(__file__).resolve().parent
DESIGN_PATH = HERE / "safe_contract_routed_borrowing_design.json"
KNOWLEDGE_MAP_DESIGN = HERE / "knowledge_map_design.json"
OUTPUT = RESULTS / "safe_mamb_local_screen.csv"
WEIGHTS_OUTPUT = RESULTS / "safe_mamb_local_weights.csv"
SUMMARY = RESULTS / "safe_mamb_local_summary.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def grouped_folds(groups: np.ndarray, maximum: int) -> list[tuple[np.ndarray, np.ndarray]]:
    unique = np.unique(groups)
    splits = min(maximum, len(unique))
    if splits < 2:
        raise RuntimeError("At least two target groups are required")
    dummy = np.zeros(len(groups))
    return list(GroupKFold(n_splits=splits).split(dummy, dummy, groups))


def pseudo_ood_mask(x: np.ndarray) -> np.ndarray:
    """Upper quartile of leave-one-out standardized Euclidean novelty."""
    scaler = StandardScaler().fit(x)
    z = scaler.transform(x)
    distances = cdist(z, z, metric="euclidean")
    np.fill_diagonal(distances, np.inf)
    k = min(3, max(1, len(z) - 1))
    novelty = np.partition(distances, k - 1, axis=1)[:, :k].mean(axis=1)
    cutoff = np.quantile(novelty, 0.75)
    mask = novelty >= cutoff
    if mask.sum() < 2:
        mask[np.argsort(novelty)[-min(2, len(mask)):]] = True
    return mask


def objective(y: np.ndarray, prediction: np.ndarray, tail: np.ndarray) -> float:
    all_mse = mean_squared_error(y, prediction)
    tail_mse = mean_squared_error(y[tail], prediction[tail])
    return 0.5 * float(all_mse) + 0.5 * float(tail_mse)


def fit_predict_target_oof(
    learner_name: str,
    x: np.ndarray,
    y: np.ndarray,
    folds: list[tuple[np.ndarray, np.ndarray]],
    seed: int,
    trees: int,
) -> np.ndarray:
    prediction = np.full(len(y), np.nan)
    for fold_id, (fit_index, held_index) in enumerate(folds):
        model = make_target_learner(
            learner_name,
            stable_seed(seed, "target-oof", str(fold_id)),
            trees,
        ).fit(x[fit_index], y[fit_index])
        prediction[held_index] = model.predict(x[held_index])
    if not np.isfinite(prediction).all():
        raise AssertionError("Incomplete target out-of-fold prediction")
    return prediction


def crossfit_source_signal(
    target_id: str,
    source_id: str,
    tasks: dict[str, Any],
    partitions: dict[str, dict[str, Any]],
    target_train: np.ndarray,
    folds: list[tuple[np.ndarray, np.ndarray]],
    seed: int,
) -> np.ndarray:
    """Predict target-train rows after excluding their identities per fold."""
    target = tasks[target_id]
    source = tasks[source_id]
    split = partitions[target_id]
    evaluation = np.r_[split["discovery"], split["confirmation"]]
    evaluation_keys = set(
        target.frame.loc[evaluation, "material_key"].astype(str)
    )
    prediction = np.full(len(target_train), np.nan)
    source_keys = source.frame["material_key"].astype(str)
    for fold_id, (_, held_local) in enumerate(folds):
        held_global = target_train[held_local]
        held_keys = set(
            target.frame.loc[held_global, "material_key"].astype(str)
        )
        excluded = evaluation_keys | held_keys
        keep = ~source_keys.isin(excluded)
        source_index = np.flatnonzero(keep.to_numpy())
        # The formal source-quality audit uses n >= 25.  Identity
        # cross-fitting can legitimately push a small paired auxiliary task
        # just below that threshold (for example OpenPoly hardness) even
        # though its linear molecular source model remains estimable.  Never
        # relax the identity exclusion; allow the local screen only when at
        # least ten independent rows remain and let ridge shrinkage/fallback
        # reject an unstable donor.
        if len(source_index) < 10:
            raise RuntimeError(
                f"{source_id}->{target_id} has only {len(source_index)} "
                "identity-safe source rows"
            )
        model = source_model(
            source,
            stable_seed(seed, source_id, "source-oof", str(fold_id)),
            cv=True,
        ).fit(
            np.asarray(source.X)[source_index],
            source.frame.loc[keep, "value"].to_numpy(float),
        )
        prediction[held_local] = model.predict(
            np.asarray(target.X)[held_global]
        )
    if not np.isfinite(prediction).all():
        raise AssertionError(f"Incomplete source OOF signal for {source_id}")
    return prediction


def meta_oof_correction(
    z: np.ndarray,
    residual: np.ndarray,
    groups: np.ndarray,
    alpha: float,
) -> np.ndarray:
    prediction = np.full(len(residual), np.nan)
    folds = grouped_folds(groups, 3)
    for fit_index, held_index in folds:
        model = make_pipeline(
            StandardScaler(),
            Ridge(alpha=alpha, solver="lsqr"),
        ).fit(z[fit_index], residual[fit_index])
        prediction[held_index] = model.predict(z[held_index])
    if not np.isfinite(prediction).all():
        raise AssertionError("Incomplete meta out-of-fold correction")
    return prediction


def best_single_source_score(
    signal: np.ndarray,
    y: np.ndarray,
    base_oof: np.ndarray,
    groups: np.ndarray,
    tail: np.ndarray,
    alphas: list[float],
    blends: list[float],
) -> tuple[float, float, float]:
    baseline_objective = objective(y, base_oof, tail)
    best = baseline_objective
    best_alpha = alphas[-1]
    best_blend = 0.0
    residual = y - base_oof
    for alpha in alphas:
        correction = meta_oof_correction(
            signal.reshape(-1, 1), residual, groups, alpha
        )
        for blend in blends:
            candidate = base_oof + blend * correction
            value = objective(y, candidate, tail)
            if value < best:
                best = value
                best_alpha = alpha
                best_blend = blend
    score = max(0.0, (baseline_objective - best) / baseline_objective)
    return float(score), float(best_alpha), float(best_blend)


def fit_safe_stack(
    donor_oof: dict[str, np.ndarray],
    donor_final: dict[str, np.ndarray],
    eligible: list[str],
    sentinel: str,
    y_train: np.ndarray,
    base_oof: np.ndarray,
    groups: np.ndarray,
    x_train: np.ndarray,
    alphas: list[float],
    blends: list[float],
) -> tuple[np.ndarray, dict[str, Any]]:
    tail = pseudo_ood_mask(x_train)
    scores: dict[str, float] = {}
    for source in [*eligible, sentinel]:
        score, _, _ = best_single_source_score(
            donor_oof[source],
            y_train,
            base_oof,
            groups,
            tail,
            alphas,
            blends,
        )
        scores[source] = score

    selected = [source for source in eligible if scores[source] > 0.0]
    baseline_objective = objective(y_train, base_oof, tail)
    if not selected:
        return np.zeros_like(next(iter(donor_final.values()))), {
            "selected": [],
            "alpha": alphas[-1],
            "blend": 0.0,
            "baseline_objective": baseline_objective,
            "selected_objective": baseline_objective,
            "scores": scores,
        }

    z_oof = np.column_stack([donor_oof[source] for source in selected])
    z_final = np.column_stack([donor_final[source] for source in selected])
    residual = y_train - base_oof
    best = baseline_objective
    best_alpha = alphas[-1]
    best_blend = 0.0
    for alpha in alphas:
        correction_oof = meta_oof_correction(
            z_oof, residual, groups, alpha
        )
        for blend in blends:
            candidate = base_oof + blend * correction_oof
            value = objective(y_train, candidate, tail)
            if value < best:
                best = value
                best_alpha = alpha
                best_blend = blend

    if best_blend == 0.0:
        final_correction = np.zeros(len(z_final))
    else:
        model = make_pipeline(
            StandardScaler(),
            Ridge(alpha=best_alpha, solver="lsqr"),
        ).fit(z_oof, residual)
        final_correction = best_blend * model.predict(z_final)
    return final_correction, {
        "selected": selected,
        "alpha": best_alpha,
        "blend": best_blend,
        "baseline_objective": baseline_objective,
        "selected_objective": best,
        "scores": scores,
    }


def main() -> None:
    args = parse_args()
    ensure_output_dirs()
    if any(path.exists() for path in [OUTPUT, WEIGHTS_OUTPUT, SUMMARY]):
        if not args.overwrite:
            raise FileExistsError("SAFE-MAMB outputs exist; pass --overwrite")

    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    parent_ood = json.loads(PARENT_DESIGN_PATH.read_text(encoding="utf-8"))
    parent = json.loads(KNOWLEDGE_MAP_DESIGN.read_text(encoding="utf-8"))
    frozen_hashes = validate_freeze(parent_ood)
    repeats = args.repeats or int(design["local_repeats"])
    screen_targets = design["screen_targets"]

    needed = set(screen_targets)
    for target in screen_targets:
        needed.update(
            edge["task"] for edge in parent["targets"][target]["sources"]
        )
    tasks = {
        task_id: load_task(task_id, spec)
        for task_id, spec in parent["tasks"].items()
        if task_id in needed
    }
    build_feature_spaces(tasks)
    analysis_parent = deepcopy(parent)
    analysis_parent["targets"] = {
        target: deepcopy(parent["targets"][target])
        for target in screen_targets
    }
    partitions, _ = partition_targets(deepcopy(analysis_parent), tasks)
    donor_models, _ = fit_source_models(
        analysis_parent, tasks, partitions
    )

    learners = design["learners"]
    trees = int(parent_ood["learners"]["tree_estimators"])
    alphas = [float(value) for value in design["stack"]["alphas"]]
    blends = [float(value) for value in design["stack"]["blend_grid"]]
    base_seed = int(parent_ood["seed"])
    rows: list[dict[str, Any]] = []
    weight_rows: list[dict[str, Any]] = []

    for target_id in screen_targets:
        task = tasks[target_id]
        split = partitions[target_id]
        evaluation = np.sort(
            np.r_[split["discovery"], split["confirmation"]]
        )
        strata = assign_group_quartiles(
            target_id,
            task,
            split["development"],
            evaluation,
        )
        scope_by_index = dict(
            zip(strata["entity_index"].astype(int), strata["scope"].astype(str))
        )
        q1 = np.asarray(
            [index for index in evaluation if scope_by_index[int(index)] == "q1"],
            dtype=int,
        )
        q4 = np.asarray(
            [index for index in evaluation if scope_by_index[int(index)] == "q4"],
            dtype=int,
        )
        edges = analysis_parent["targets"][target_id]["sources"]
        eligible = [
            edge["task"]
            for edge in edges
            if int(edge.get("neighborhood", 0)) >= 1
            and edge["relation"] != "distant-control"
        ]
        sentinel = parent_ood["targets"][target_id]["wrong_source"]
        source_ids = list(dict.fromkeys([*eligible, sentinel]))
        final_signals = {
            source: np.asarray(
                donor_models[(target_id, source)].predict(np.asarray(task.X)),
                dtype=float,
            )
            for source in source_ids
        }
        x = np.asarray(task.X, dtype=float)
        y = task.frame["value"].to_numpy(float)
        development = split["development"]
        budget = int(split["budget"])
        development_groups = (
            task.frame.loc[development, "group"].astype(str).to_numpy()
        )

        for repeat in range(repeats):
            draw_seed = stable_seed(
                base_seed, "safe-mamb", target_id, str(repeat)
            )
            rng = np.random.default_rng(draw_seed)
            local = sample_groups(development_groups, budget, rng)
            train = development[local]
            train_groups = task.frame.loc[train, "group"].astype(str).to_numpy()
            folds = grouped_folds(train_groups, 3)
            donor_oof = {
                source: crossfit_source_signal(
                    target_id,
                    source,
                    tasks,
                    partitions,
                    train,
                    folds,
                    draw_seed,
                )
                for source in source_ids
            }
            donor_final = {
                source: final_signals[source][evaluation]
                for source in source_ids
            }

            for learner_name in learners:
                model_seed = stable_seed(
                    draw_seed, learner_name, "target"
                )
                baseline_oof = fit_predict_target_oof(
                    learner_name,
                    x[train],
                    y[train],
                    folds,
                    model_seed,
                    trees,
                )
                baseline_model = make_target_learner(
                    learner_name, model_seed, trees
                ).fit(x[train], y[train])
                baseline_eval = baseline_model.predict(x[evaluation])

                concat_x = np.column_stack(
                    [x, *[final_signals[source] for source in eligible]]
                )
                concat_model = make_target_learner(
                    learner_name, model_seed, trees
                ).fit(concat_x[train], y[train])
                concat_eval = concat_model.predict(concat_x[evaluation])

                correction, meta = fit_safe_stack(
                    donor_oof,
                    donor_final,
                    eligible,
                    sentinel,
                    y[train],
                    baseline_oof,
                    train_groups,
                    x[train],
                    alphas,
                    blends,
                )
                safe_eval = baseline_eval + correction

                for method, prediction in [
                    ("mechanism_bundle_feature_concat", concat_eval),
                    ("safe_crossfit_residual_stack", safe_eval),
                ]:
                    q1_local = np.flatnonzero(np.isin(evaluation, q1))
                    q4_local = np.flatnonzero(np.isin(evaluation, q4))
                    q1_metrics = regression_metrics(
                        y[q1],
                        baseline_eval[q1_local],
                        prediction[q1_local],
                    )
                    q4_metrics = regression_metrics(
                        y[q4],
                        baseline_eval[q4_local],
                        prediction[q4_local],
                    )
                    rows.append({
                        "target": target_id,
                        "contract": design["contracts"][target_id],
                        "method": method,
                        "learner": learner_name,
                        "repeat": repeat,
                        "train_n": len(train),
                        "q1_relative_rmse_gain": q1_metrics[
                            "relative_rmse_gain"
                        ],
                        "q4_relative_rmse_gain": q4_metrics[
                            "relative_rmse_gain"
                        ],
                        "gain_specific": q4_metrics[
                            "relative_rmse_gain"
                        ] - q1_metrics["relative_rmse_gain"],
                        "q4_r2": q4_metrics["aug_r2"],
                        "selected_sources": "|".join(meta["selected"])
                        if method == "safe_crossfit_residual_stack"
                        else "|".join(eligible),
                        "blend": meta["blend"]
                        if method == "safe_crossfit_residual_stack"
                        else np.nan,
                    })

                for source, score in meta["scores"].items():
                    weight_rows.append({
                        "target": target_id,
                        "learner": learner_name,
                        "repeat": repeat,
                        "source": source,
                        "eligible": source in eligible,
                        "sentinel": source == sentinel,
                        "transferability_score": score,
                        "selected": source in meta["selected"],
                        "stack_alpha": meta["alpha"],
                        "stack_blend": meta["blend"],
                        "baseline_objective": meta["baseline_objective"],
                        "selected_objective": meta["selected_objective"],
                    })

    frame = pd.DataFrame(rows)
    weights = pd.DataFrame(weight_rows)
    frame.to_csv(OUTPUT, index=False)
    weights.to_csv(WEIGHTS_OUTPUT, index=False)
    grouped = (
        frame.groupby(["target", "contract", "method"], as_index=False)
        .agg(
            q1_relative_rmse_gain=("q1_relative_rmse_gain", "mean"),
            q4_relative_rmse_gain=("q4_relative_rmse_gain", "mean"),
            gain_specific=("gain_specific", "mean"),
            q4_r2=("q4_r2", "mean"),
            positive_q4_fraction=(
                "q4_relative_rmse_gain",
                lambda values: float(np.mean(np.asarray(values) > 0)),
            ),
            cells=("q4_r2", "size"),
        )
        .sort_values(["target", "method"])
    )
    sentinel_summary = (
        weights.groupby(["target", "sentinel"], as_index=False)
        .agg(
            mean_transferability_score=("transferability_score", "mean"),
            positive_score_fraction=(
                "transferability_score",
                lambda values: float(np.mean(np.asarray(values) > 0)),
            ),
            selected_fraction=(
                "selected",
                lambda values: float(np.mean(np.asarray(values, dtype=bool))),
            ),
        )
        .sort_values(["target", "sentinel"])
    )
    summary = {
        "status": "safe-mamb-local-screen-complete",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "claim_guard": design["claim_guard"],
        "frozen_hashes": frozen_hashes,
        "targets": screen_targets,
        "repeats": repeats,
        "learners": learners,
        "rows": len(frame),
        "grouped_results": grouped.to_dict(orient="records"),
        "source_router_summary": sentinel_summary.to_dict(orient="records"),
    }
    SUMMARY.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(grouped.to_string(index=False), flush=True)
    print(sentinel_summary.to_string(index=False), flush=True)
    print(json.dumps(summary, indent=2, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
