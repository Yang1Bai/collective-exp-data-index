"""Task-conditioned, partial-label multi-task local screen.

The shared expert is inspired by property-token multi-task models: every
observed material-property pair is a training row, so missing property labels
are never imputed.  Source rows matching target evaluation identities (or the
current target meta-fold) are excluded.  A grouped out-of-fold blend can return
exactly to the target-only learner.
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
from sklearn.model_selection import GroupKFold
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler

from common import RESULTS, ensure_output_dirs, sample_groups
from run_knowledge_map import build_feature_spaces, load_task, partition_targets
from run_multi_target_ood_borrowing import (
    DESIGN_PATH as PARENT_DESIGN_PATH,
    assign_group_quartiles,
    make_target_learner,
    regression_metrics,
    stable_seed,
    validate_freeze,
)
from run_safe_mamb_local_screen import grouped_folds, objective, pseudo_ood_mask


HERE = Path(__file__).resolve().parent
DESIGN_PATH = HERE / "task_conditioned_partial_label_design.json"
KNOWLEDGE_MAP_DESIGN = HERE / "knowledge_map_design.json"
OUTPUT = RESULTS / "task_conditioned_mtl_local_screen.csv"
SUMMARY = RESULTS / "task_conditioned_mtl_local_summary.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


class TaskConditionedExpert:
    def __init__(
        self,
        task_ids: list[str],
        kind: str,
        hidden: tuple[int, ...],
        alpha: float,
        maximum_iterations: int,
        seed: int,
    ) -> None:
        self.task_ids = task_ids
        self.task_index = {
            task_id: index for index, task_id in enumerate(task_ids)
        }
        self.kind = kind
        self.x_scaler = StandardScaler()
        self.model = MLPRegressor(
            hidden_layer_sizes=hidden,
            activation="relu",
            solver="adam",
            alpha=alpha,
            batch_size="auto",
            learning_rate_init=0.001,
            max_iter=maximum_iterations,
            early_stopping=True,
            validation_fraction=0.15,
            n_iter_no_change=25,
            random_state=seed,
        )
        self.y_location: dict[str, float] = {}
        self.y_scale: dict[str, float] = {}

    def _augment(self, x: np.ndarray, task_id: str) -> np.ndarray:
        token = np.zeros((len(x), len(self.task_ids)), dtype=float)
        token[:, self.task_index[task_id]] = 1.0
        return np.column_stack([x, token])

    def fit(
        self,
        blocks: list[tuple[str, np.ndarray, np.ndarray]],
    ) -> "TaskConditionedExpert":
        augmented: list[np.ndarray] = []
        standardized_y: list[np.ndarray] = []
        sample_weight: list[np.ndarray] = []
        for task_id, x, y in blocks:
            location = float(np.mean(y))
            scale = float(np.std(y, ddof=1)) if len(y) > 1 else 1.0
            if not np.isfinite(scale) or scale < 1e-12:
                scale = 1.0
            self.y_location[task_id] = location
            self.y_scale[task_id] = scale
            augmented.append(self._augment(x, task_id))
            standardized_y.append((y - location) / scale)
            sample_weight.append(np.full(len(y), 1.0 / len(y)))
        train_x = np.row_stack(augmented)
        train_y = np.concatenate(standardized_y)
        weights = np.concatenate(sample_weight)
        weights *= len(weights) / weights.sum()
        scaled_x = self.x_scaler.fit_transform(train_x)
        self.model.fit(scaled_x, train_y, sample_weight=weights)
        return self

    def predict(self, task_id: str, x: np.ndarray) -> np.ndarray:
        augmented = self._augment(x, task_id)
        standardized = self.model.predict(self.x_scaler.transform(augmented))
        return (
            standardized * self.y_scale[task_id]
            + self.y_location[task_id]
        )


def training_blocks(
    target_id: str,
    source_ids: list[str],
    tasks: dict[str, Any],
    target_fit: np.ndarray,
    excluded_keys: set[str],
) -> list[tuple[str, np.ndarray, np.ndarray]]:
    target = tasks[target_id]
    blocks: list[tuple[str, np.ndarray, np.ndarray]] = [
        (
            target_id,
            np.asarray(target.X)[target_fit],
            target.frame.loc[target_fit, "value"].to_numpy(float),
        )
    ]
    for source_id in source_ids:
        source = tasks[source_id]
        keep = ~source.frame["material_key"].astype(str).isin(excluded_keys)
        indices = np.flatnonzero(keep.to_numpy())
        if len(indices) < 10:
            raise RuntimeError(
                f"{source_id}->{target_id} has only {len(indices)} "
                "identity-safe multi-task rows"
            )
        blocks.append(
            (
                source_id,
                np.asarray(source.X)[indices],
                source.frame.loc[keep, "value"].to_numpy(float),
            )
        )
    return blocks


def fit_mtl_oof_and_final(
    target_id: str,
    source_ids: list[str],
    tasks: dict[str, Any],
    partitions: dict[str, dict[str, Any]],
    train: np.ndarray,
    evaluation: np.ndarray,
    folds: list[tuple[np.ndarray, np.ndarray]],
    method: dict[str, Any],
    seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    target = tasks[target_id]
    evaluation_keys = set(
        target.frame.loc[evaluation, "material_key"].astype(str)
    )
    task_ids = [target_id, *source_ids]
    hidden = tuple(int(value) for value in method["architecture"])
    oof = np.full(len(train), np.nan)
    for fold_id, (fit_local, held_local) in enumerate(folds):
        held_global = train[held_local]
        excluded = evaluation_keys | set(
            target.frame.loc[held_global, "material_key"].astype(str)
        )
        expert = TaskConditionedExpert(
            task_ids,
            target.spec["kind"],
            hidden,
            float(method["alpha"]),
            int(method["maximum_iterations"]),
            stable_seed(seed, "mtl-oof", str(fold_id)),
        ).fit(
            training_blocks(
                target_id,
                source_ids,
                tasks,
                train[fit_local],
                excluded,
            )
        )
        oof[held_local] = expert.predict(
            target_id, np.asarray(target.X)[held_global]
        )
    if not np.isfinite(oof).all():
        raise AssertionError("Incomplete multi-task OOF prediction")

    final_expert = TaskConditionedExpert(
        task_ids,
        target.spec["kind"],
        hidden,
        float(method["alpha"]),
        int(method["maximum_iterations"]),
        stable_seed(seed, "mtl-final"),
    ).fit(
        training_blocks(
            target_id,
            source_ids,
            tasks,
            train,
            evaluation_keys,
        )
    )
    final = final_expert.predict(
        target_id, np.asarray(target.X)[evaluation]
    )
    return oof, final


def target_oof_and_final(
    learner_name: str,
    x: np.ndarray,
    y: np.ndarray,
    train: np.ndarray,
    evaluation: np.ndarray,
    folds: list[tuple[np.ndarray, np.ndarray]],
    trees: int,
    seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    oof = np.full(len(train), np.nan)
    for fold_id, (fit_local, held_local) in enumerate(folds):
        model = make_target_learner(
            learner_name,
            stable_seed(seed, "target-oof", str(fold_id)),
            trees,
        ).fit(x[train[fit_local]], y[train[fit_local]])
        oof[held_local] = model.predict(x[train[held_local]])
    final_model = make_target_learner(
        learner_name, stable_seed(seed, "target-final"), trees
    ).fit(x[train], y[train])
    return oof, final_model.predict(x[evaluation])


def choose_blend(
    y: np.ndarray,
    baseline: np.ndarray,
    borrowed: np.ndarray,
    x: np.ndarray,
    grid: list[float],
) -> tuple[float, float]:
    tail = pseudo_ood_mask(x)
    best_blend = 0.0
    best_objective = objective(y, baseline, tail)
    for blend in grid:
        prediction = (1.0 - blend) * baseline + blend * borrowed
        value = objective(y, prediction, tail)
        if value < best_objective:
            best_objective = value
            best_blend = blend
    return best_blend, best_objective


def main() -> None:
    args = parse_args()
    ensure_output_dirs()
    if (OUTPUT.exists() or SUMMARY.exists()) and not args.overwrite:
        raise FileExistsError("Task-conditioned outputs exist; pass --overwrite")

    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    parent_ood = json.loads(PARENT_DESIGN_PATH.read_text(encoding="utf-8"))
    parent = json.loads(KNOWLEDGE_MAP_DESIGN.read_text(encoding="utf-8"))
    frozen_hashes = validate_freeze(parent_ood)
    targets = design["screen_targets"]
    repeats = args.repeats or int(design["local_repeats"])
    needed = set(targets)
    for target_id in targets:
        needed.update(
            edge["task"] for edge in parent["targets"][target_id]["sources"]
        )
    tasks = {
        task_id: load_task(task_id, spec)
        for task_id, spec in parent["tasks"].items()
        if task_id in needed
    }
    build_feature_spaces(tasks)
    analysis_parent = deepcopy(parent)
    analysis_parent["targets"] = {
        target_id: deepcopy(parent["targets"][target_id])
        for target_id in targets
    }
    partitions, _ = partition_targets(analysis_parent, tasks)

    trees = int(parent_ood["learners"]["tree_estimators"])
    blend_grid = [
        float(value) for value in design["safety_blend"]["grid"]
    ]
    base_seed = int(parent_ood["seed"])
    rows: list[dict[str, Any]] = []

    for target_id in targets:
        target = tasks[target_id]
        split = partitions[target_id]
        evaluation = np.sort(
            np.r_[split["discovery"], split["confirmation"]]
        )
        strata = assign_group_quartiles(
            target_id,
            target,
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
        q1_local = np.flatnonzero(np.isin(evaluation, q1))
        q4_local = np.flatnonzero(np.isin(evaluation, q4))
        eligible = [
            edge["task"]
            for edge in analysis_parent["targets"][target_id]["sources"]
            if int(edge.get("neighborhood", 0)) >= 1
            and edge["relation"] != "distant-control"
        ]
        wrong = parent_ood["targets"][target_id]["wrong_source"]
        bundles = {
            "task_conditioned_bundle_safe_blend": eligible,
            "task_conditioned_wrong_safe_blend": [wrong],
        }
        x = np.asarray(target.X, dtype=float)
        y = target.frame["value"].to_numpy(float)
        development = split["development"]
        groups = (
            target.frame.loc[development, "group"].astype(str).to_numpy()
        )

        for repeat in range(repeats):
            draw_seed = stable_seed(
                base_seed, "task-conditioned", target_id, str(repeat)
            )
            rng = np.random.default_rng(draw_seed)
            local = sample_groups(groups, int(split["budget"]), rng)
            train = development[local]
            train_groups = (
                target.frame.loc[train, "group"].astype(str).to_numpy()
            )
            folds = grouped_folds(train_groups, 3)
            borrowed: dict[str, tuple[np.ndarray, np.ndarray]] = {}
            for method_name, sources in bundles.items():
                borrowed[method_name] = fit_mtl_oof_and_final(
                    target_id,
                    sources,
                    tasks,
                    partitions,
                    train,
                    evaluation,
                    folds,
                    design["shared_expert"],
                    stable_seed(draw_seed, method_name),
                )

            for learner_name in design["learners"]:
                baseline_oof, baseline_final = target_oof_and_final(
                    learner_name,
                    x,
                    y,
                    train,
                    evaluation,
                    folds,
                    trees,
                    stable_seed(draw_seed, learner_name),
                )
                for method_name, sources in bundles.items():
                    borrowed_oof, borrowed_final = borrowed[method_name]
                    blend, selected_objective = choose_blend(
                        y[train],
                        baseline_oof,
                        borrowed_oof,
                        x[train],
                        blend_grid,
                    )
                    prediction = (
                        (1.0 - blend) * baseline_final
                        + blend * borrowed_final
                    )
                    q1_metrics = regression_metrics(
                        y[q1],
                        baseline_final[q1_local],
                        prediction[q1_local],
                    )
                    q4_metrics = regression_metrics(
                        y[q4],
                        baseline_final[q4_local],
                        prediction[q4_local],
                    )
                    rows.append({
                        "target": target_id,
                        "method": method_name,
                        "learner": learner_name,
                        "repeat": repeat,
                        "sources": "|".join(sources),
                        "blend": blend,
                        "selected_objective": selected_objective,
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
                    })

    frame = pd.DataFrame(rows)
    frame.to_csv(OUTPUT, index=False)
    grouped = (
        frame.groupby(["target", "method"], as_index=False)
        .agg(
            q1_relative_rmse_gain=("q1_relative_rmse_gain", "mean"),
            q4_relative_rmse_gain=("q4_relative_rmse_gain", "mean"),
            gain_specific=("gain_specific", "mean"),
            q4_r2=("q4_r2", "mean"),
            positive_q4_fraction=(
                "q4_relative_rmse_gain",
                lambda values: float(np.mean(np.asarray(values) > 0)),
            ),
            nonzero_blend_fraction=(
                "blend",
                lambda values: float(np.mean(np.asarray(values) > 0)),
            ),
            mean_blend=("blend", "mean"),
            cells=("q4_r2", "size"),
        )
        .sort_values(["target", "method"])
    )
    summary = {
        "status": "task-conditioned-local-screen-complete",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "claim_guard": design["claim_guard"],
        "frozen_hashes": frozen_hashes,
        "targets": targets,
        "repeats": repeats,
        "learners": design["learners"],
        "rows": len(frame),
        "grouped_results": grouped.to_dict(orient="records"),
    }
    SUMMARY.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(grouped.to_string(index=False), flush=True)
    print(json.dumps(summary, indent=2, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
