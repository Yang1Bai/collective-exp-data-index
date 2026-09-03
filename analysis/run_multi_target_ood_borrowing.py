"""Run the frozen multi-target OOD knowledge-borrowing benchmark.

The benchmark reuses the exact tasks, partitions, representations, and directed
edges in ``knowledge_map_design.json``.  It asks whether a donor prediction
feature improves a recipient specifically in the evaluation groups farthest
from the complete recipient-development support.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from rdkit import Chem, DataStructs
from rdkit.Chem import rdFingerprintGenerator
from sklearn.base import clone
from sklearn.ensemble import ExtraTreesRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from common import RESULTS, ensure_output_dirs, holm_adjust, sample_groups
from run_knowledge_map import (
    DESIGN_PATH as PARENT_DESIGN_PATH,
    TaskData,
    build_feature_spaces,
    fit_source_models,
    load_task,
    partition_targets,
    stable_offset,
)


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DESIGN_PATH = HERE / "multi_target_ood_borrowing_design.json"
DB_PATH = ROOT / "data" / "collective.sqlite"
PARENT_RUNNER_PATH = HERE / "run_knowledge_map.py"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_seed(base: int, *parts: str) -> int:
    return int(base + stable_offset("|".join(parts)) % 1_000_000_000)


def validate_freeze(design: dict[str, Any]) -> dict[str, str]:
    files = {
        "parent_design_sha256": sha256_file(PARENT_DESIGN_PATH),
        "data_snapshot_sha256": sha256_file(DB_PATH),
        "parent_runner_sha256_at_freeze": sha256_file(PARENT_RUNNER_PATH),
    }
    expected = design["provenance"]
    for key, actual in files.items():
        if actual != expected[key]:
            raise AssertionError(
                f"Frozen input changed for {key}: expected {expected[key]}, found {actual}"
            )
    return files


def formula_entity_distances(
    x: np.ndarray, development: np.ndarray, evaluation: np.ndarray
) -> np.ndarray:
    reference = np.asarray(x[development], dtype=np.float64)
    query = np.asarray(x[evaluation], dtype=np.float64)
    mean = reference.mean(axis=0)
    scale = reference.std(axis=0)
    scale[scale == 0] = 1.0
    reference = (reference - mean) / scale
    query = (query - mean) / scale
    output = np.empty(len(query), dtype=float)
    block_size = 128
    for start in range(0, len(query), block_size):
        block = query[start : start + block_size]
        squared = (
            np.sum(block**2, axis=1)[:, None]
            + np.sum(reference**2, axis=1)[None, :]
            - 2.0 * block @ reference.T
        )
        output[start : start + len(block)] = np.sqrt(
            np.maximum(squared.min(axis=1), 0.0)
        )
    return output


def molecule_entity_distances(
    frame: pd.DataFrame, development: np.ndarray, evaluation: np.ndarray
) -> np.ndarray:
    generator = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=1024)

    def fingerprint(index: int):
        molecule = Chem.MolFromSmiles(str(frame.at[index, "material_key"]))
        if molecule is None:
            raise ValueError(f"Invalid canonical SMILES at row {index}")
        return generator.GetFingerprint(molecule)

    reference = [fingerprint(int(index)) for index in development]
    output = np.empty(len(evaluation), dtype=float)
    for position, index in enumerate(evaluation):
        similarities = DataStructs.BulkTanimotoSimilarity(
            fingerprint(int(index)), reference
        )
        output[position] = 1.0 - float(max(similarities))
    return output


def assign_group_quartiles(
    target_id: str,
    task: TaskData,
    development: np.ndarray,
    evaluation: np.ndarray,
) -> pd.DataFrame:
    """Assign intact evaluation groups to fixed feature-distance quartiles."""
    if task.spec["kind"] == "formula":
        entity_distance = formula_entity_distances(
            np.asarray(task.X), development, evaluation
        )
    elif task.spec["kind"] == "molecule":
        entity_distance = molecule_entity_distances(
            task.frame, development, evaluation
        )
    else:
        raise ValueError(f"Unsupported task kind: {task.spec['kind']}")

    rows = task.frame.loc[evaluation, ["material_key", "group"]].copy()
    rows.insert(0, "entity_index", evaluation)
    rows["entity_distance"] = entity_distance
    grouped = (
        rows.groupby("group", as_index=False)
        .agg(
            group_distance=("entity_distance", "median"),
            group_n=("entity_distance", "size"),
        )
        .assign(
            tie_break=lambda value: value["group"].map(
                lambda group: stable_offset(f"{target_id}|{group}")
            )
        )
        .sort_values(["group_distance", "tie_break", "group"], kind="mergesort")
        .reset_index(drop=True)
    )
    group_scope: dict[str, str] = {}
    for quartile, positions in enumerate(np.array_split(np.arange(len(grouped)), 4), 1):
        for position in positions:
            group_scope[str(grouped.at[int(position), "group"])] = f"q{quartile}"
    rows["scope"] = rows["group"].astype(str).map(group_scope)
    rows = rows.merge(
        grouped[["group", "group_distance", "group_n"]],
        on="group",
        how="left",
        validate="many_to_one",
    )
    rows.insert(0, "target", target_id)
    if rows["scope"].isna().any():
        raise AssertionError(f"Missing OOD scope for {target_id}")
    if rows.groupby("group")["scope"].nunique().max() != 1:
        raise AssertionError(f"An evaluation group crosses OOD strata for {target_id}")
    return rows.sort_values("entity_index").reset_index(drop=True)


def make_target_learner(name: str, seed: int, trees: int):
    if name == "ridge_alpha_10":
        return make_pipeline(StandardScaler(), Ridge(alpha=10.0, solver="lsqr"))
    if name == "random_forest":
        return RandomForestRegressor(
            n_estimators=trees,
            min_samples_leaf=2,
            max_features=0.7,
            random_state=seed,
            n_jobs=1,
        )
    if name == "extra_trees":
        return ExtraTreesRegressor(
            n_estimators=trees,
            min_samples_leaf=2,
            max_features=0.7,
            random_state=seed,
            n_jobs=1,
        )
    raise ValueError(f"Unknown learner: {name}")


def regression_metrics(
    y: np.ndarray, baseline: np.ndarray, augmented: np.ndarray
) -> dict[str, float]:
    base_rmse = math.sqrt(mean_squared_error(y, baseline))
    aug_rmse = math.sqrt(mean_squared_error(y, augmented))
    return {
        "n": int(len(y)),
        "base_r2": float(r2_score(y, baseline)),
        "aug_r2": float(r2_score(y, augmented)),
        "delta_r2": float(r2_score(y, augmented) - r2_score(y, baseline)),
        "base_rmse": float(base_rmse),
        "aug_rmse": float(aug_rmse),
        "relative_rmse_gain": float((base_rmse - aug_rmse) / base_rmse),
        "delta_mae": float(
            mean_absolute_error(y, baseline) - mean_absolute_error(y, augmented)
        ),
    }


@dataclass(frozen=True)
class TargetRunInput:
    target_id: str
    x: np.ndarray
    y: np.ndarray
    groups: np.ndarray
    train_index: np.ndarray
    evaluation: np.ndarray
    scope_by_index: dict[int, str]
    source_features: dict[str, np.ndarray]
    primary_source: str
    trees: int
    base_seed: int


def grouped_error_rows(
    target_id: str,
    source_id: str,
    repeat: int,
    scope: str,
    indices: np.ndarray,
    groups: np.ndarray,
    y: np.ndarray,
    baseline: np.ndarray,
    augmented: np.ndarray,
) -> list[dict[str, Any]]:
    frame = pd.DataFrame(
        {
            "group": groups[indices].astype(str),
            "base_sse": (y[indices] - baseline[indices]) ** 2,
            "aug_sse": (y[indices] - augmented[indices]) ** 2,
        }
    )
    grouped = (
        frame.groupby("group", as_index=False)
        .agg(base_sse=("base_sse", "sum"), aug_sse=("aug_sse", "sum"), n=("base_sse", "size"))
    )
    return [
        {
            "target": target_id,
            "source": source_id,
            "learner": "ridge_alpha_10",
            "repeat": repeat,
            "scope": scope,
            "group": row.group,
            "base_sse": float(row.base_sse),
            "aug_sse": float(row.aug_sse),
            "n": int(row.n),
        }
        for row in grouped.itertuples(index=False)
    ]


def evaluate_one_repeat(
    item: TargetRunInput, learner_name: str, repeat: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    model_seed = stable_seed(item.base_seed, item.target_id, learner_name, str(repeat))
    learner = make_target_learner(learner_name, model_seed, item.trees)
    baseline_model = clone(learner).fit(
        item.x[item.train_index], item.y[item.train_index]
    )
    baseline_all = baseline_model.predict(item.x)
    scope_indices = {
        "all": item.evaluation,
        "q1": np.asarray(
            [index for index in item.evaluation if item.scope_by_index[int(index)] == "q1"],
            dtype=int,
        ),
        "q4": np.asarray(
            [index for index in item.evaluation if item.scope_by_index[int(index)] == "q4"],
            dtype=int,
        ),
    }
    metric_rows: list[dict[str, Any]] = []
    contrast_rows: list[dict[str, Any]] = []
    error_rows: list[dict[str, Any]] = []
    for source_id, feature in item.source_features.items():
        augmented_x = np.column_stack([item.x, feature])
        augmented_model = clone(learner).fit(
            augmented_x[item.train_index], item.y[item.train_index]
        )
        augmented_all = augmented_model.predict(augmented_x)
        by_scope: dict[str, dict[str, float]] = {}
        for scope, indices in scope_indices.items():
            result = regression_metrics(
                item.y[indices], baseline_all[indices], augmented_all[indices]
            )
            by_scope[scope] = result
            metric_rows.append(
                {
                    "target": item.target_id,
                    "source": source_id,
                    "learner": learner_name,
                    "repeat": repeat,
                    "scope": scope,
                    "train_n": int(len(item.train_index)),
                    **result,
                }
            )
        contrast_rows.append(
            {
                "target": item.target_id,
                "source": source_id,
                "learner": learner_name,
                "repeat": repeat,
                "train_n": int(len(item.train_index)),
                "gain_all": by_scope["all"]["relative_rmse_gain"],
                "gain_id": by_scope["q1"]["relative_rmse_gain"],
                "gain_ood": by_scope["q4"]["relative_rmse_gain"],
                "gain_specific": (
                    by_scope["q4"]["relative_rmse_gain"]
                    - by_scope["q1"]["relative_rmse_gain"]
                ),
                "base_ood_r2": by_scope["q4"]["base_r2"],
                "aug_ood_r2": by_scope["q4"]["aug_r2"],
            }
        )
        if learner_name == "ridge_alpha_10" and source_id == item.primary_source:
            for scope in ("q1", "q4"):
                indices = scope_indices[scope]
                error_rows.extend(
                    grouped_error_rows(
                        item.target_id,
                        source_id,
                        repeat,
                        scope,
                        indices,
                        item.groups,
                        item.y,
                        baseline_all,
                        augmented_all,
                    )
                )
    return metric_rows, contrast_rows, error_rows


def repeat_bootstrap_interval(
    values: np.ndarray, n_boot: int, seed: int
) -> tuple[float, float]:
    values = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    weights = rng.multinomial(
        len(values), np.full(len(values), 1.0 / len(values)), size=n_boot
    )
    estimates = weights @ values / len(values)
    return tuple(float(value) for value in np.percentile(estimates, [2.5, 97.5]))


def hierarchical_gain_bootstrap(
    group_errors: pd.DataFrame, n_boot: int, seed: int
) -> dict[str, tuple[float, float]]:
    repeats = sorted(group_errors["repeat"].unique())
    if not repeats:
        raise ValueError("No group errors supplied")
    rng = np.random.default_rng(seed)
    repeat_weights = rng.multinomial(
        len(repeats), np.full(len(repeats), 1.0 / len(repeats)), size=n_boot
    ).astype(float)
    boot: dict[str, np.ndarray] = {}
    for scope in ("q1", "q4"):
        frame = group_errors[group_errors["scope"] == scope]
        groups = sorted(frame["group"].unique())
        if not groups:
            raise ValueError(f"No groups for {scope}")
        matrices: dict[str, np.ndarray] = {}
        for column in ("base_sse", "aug_sse"):
            matrices[column] = (
                frame.pivot(index="repeat", columns="group", values=column)
                .reindex(index=repeats, columns=groups)
                .fillna(0.0)
                .to_numpy(float)
            )
        group_n = (
            frame.groupby("group")["n"]
            .first()
            .reindex(groups)
            .to_numpy(float)
        )
        group_weights = rng.multinomial(
            len(groups), np.full(len(groups), 1.0 / len(groups)), size=n_boot
        ).astype(float)
        base_by_group = repeat_weights @ matrices["base_sse"]
        aug_by_group = repeat_weights @ matrices["aug_sse"]
        base_sse = np.sum(base_by_group * group_weights, axis=1)
        aug_sse = np.sum(aug_by_group * group_weights, axis=1)
        denominator = len(repeats) * (group_weights @ group_n)
        base_rmse = np.sqrt(base_sse / denominator)
        aug_rmse = np.sqrt(aug_sse / denominator)
        boot[scope] = (base_rmse - aug_rmse) / base_rmse
    boot["specific"] = boot["q4"] - boot["q1"]
    return {
        name: tuple(
            float(value)
            for value in np.percentile(values[np.isfinite(values)], [2.5, 97.5])
        )
        for name, values in boot.items()
    }


def sign_flip_pvalue(values: np.ndarray, permutations: int, seed: int) -> float:
    values = np.asarray(values, dtype=float)
    observed = float(values.mean())
    if len(values) <= 20 and permutations >= 2 ** len(values):
        masks = np.arange(2 ** len(values), dtype=np.uint64)[:, None]
        bits = ((masks >> np.arange(len(values), dtype=np.uint64)) & 1).astype(float)
        signs = 2.0 * bits - 1.0
        null = signs @ values / len(values)
        return float(np.mean(null >= observed))
    rng = np.random.default_rng(seed)
    exceed = 0
    remaining = permutations
    while remaining:
        size = min(2000, remaining)
        signs = rng.choice(np.asarray([-1.0, 1.0]), size=(size, len(values)))
        null = signs @ values / len(values)
        exceed += int(np.sum(null >= observed))
        remaining -= size
    return float((1 + exceed) / (permutations + 1))


def classify_edge(row: pd.Series, gate: dict[str, Any]) -> str:
    if bool(row.get("is_designated_primary", False)):
        criteria = [
            row["gain_ood_mean"] >= gate["mean_ood_relative_rmse_gain_minimum"],
            row["gain_ood_ci_lo"] > gate["hierarchical_ood_gain_ci_lower_above"],
            row["aug_ood_r2_mean"] > gate["mean_augmented_ood_r2_above"],
            row["positive_ood_repeat_fraction"]
            >= gate["positive_ood_gain_repeat_fraction_minimum"],
            row["gain_specific_ci_lo"]
            > gate["hierarchical_gain_specific_ci_lower_above"],
            row["primary_minus_wrong_ci_lo"]
            > gate["primary_minus_wrong_ood_gain_ci_lower_above"],
            row["primary_minus_shuffled_ci_lo"]
            > gate["primary_minus_shuffled_ood_gain_ci_lower_above"],
            row["positive_ood_learners"]
            >= gate["learners_with_positive_mean_ood_gain_minimum"],
            row["holm_p"] < gate["holm_adjusted_one_sided_p_below"],
            row["post_exclusion_overlap"]
            == gate["post_exclusion_identity_overlap_equals"],
        ]
        if all(bool(value) for value in criteria):
            return "ood-repair-gate-passed"
    if row["gain_ood_ci_lo"] > 0 and row["gain_ood_mean"] > 0:
        return "ood-improvement-not-specific"
    if row["gain_ood_mean"] > 0:
        return "directional-ood-improvement"
    if row["gain_ood_mean"] < 0 and row["gain_ood_ci_hi"] < 0:
        return "harmful"
    return "unresolved"


def summarize_edges(
    contrasts: pd.DataFrame,
    group_errors: pd.DataFrame,
    source_quality: pd.DataFrame,
    design: dict[str, Any],
    n_boot: int,
    permutations: int,
) -> pd.DataFrame:
    primary_learner = design["learners"]["primary"]
    primary = contrasts[contrasts["learner"] == primary_learner].copy()
    metadata = source_quality.set_index(["target", "source"])
    rows: list[dict[str, Any]] = []
    base_seed = int(design["seed"])
    for (target, source), frame in primary.groupby(["target", "source"], sort=True):
        target_spec = design["targets"][target]
        is_primary = source == target_spec["primary_source"]
        if is_primary:
            intervals = hierarchical_gain_bootstrap(
                group_errors[
                    (group_errors["target"] == target)
                    & (group_errors["source"] == source)
                ],
                n_boot,
                stable_seed(base_seed, target, source, "hierarchical"),
            )
            interval_method = "hierarchical-repeat-and-group-bootstrap"
            p_value = sign_flip_pvalue(
                frame["gain_ood"].to_numpy(float),
                permutations,
                stable_seed(base_seed, target, source, "sign-flip"),
            )
        else:
            intervals = {
                "q1": repeat_bootstrap_interval(
                    frame["gain_id"].to_numpy(float),
                    n_boot,
                    stable_seed(base_seed, target, source, "id-repeat-bootstrap"),
                ),
                "q4": repeat_bootstrap_interval(
                    frame["gain_ood"].to_numpy(float),
                    n_boot,
                    stable_seed(base_seed, target, source, "ood-repeat-bootstrap"),
                ),
                "specific": repeat_bootstrap_interval(
                    frame["gain_specific"].to_numpy(float),
                    n_boot,
                    stable_seed(base_seed, target, source, "specific-repeat-bootstrap"),
                ),
            }
            interval_method = "repeat-bootstrap-exploratory"
            p_value = float("nan")

        wrong_source = target_spec["wrong_source"]
        shuffled_source = f"shuffled::{target_spec['primary_source']}"
        if is_primary:
            wrong = primary[
                (primary["target"] == target) & (primary["source"] == wrong_source)
            ].sort_values("repeat")
            shuffled = primary[
                (primary["target"] == target) & (primary["source"] == shuffled_source)
            ].sort_values("repeat")
            ordered = frame.sort_values("repeat")
            if not (
                ordered["repeat"].to_list()
                == wrong["repeat"].to_list()
                == shuffled["repeat"].to_list()
            ):
                raise AssertionError(f"Unpaired control repeats for {target}")
            wrong_diff = (
                ordered["gain_ood"].to_numpy(float)
                - wrong["gain_ood"].to_numpy(float)
            )
            shuffled_diff = (
                ordered["gain_ood"].to_numpy(float)
                - shuffled["gain_ood"].to_numpy(float)
            )
            wrong_ci = repeat_bootstrap_interval(
                wrong_diff, n_boot, stable_seed(base_seed, target, "wrong-control")
            )
            shuffled_ci = repeat_bootstrap_interval(
                shuffled_diff,
                n_boot,
                stable_seed(base_seed, target, "shuffled-control"),
            )
        else:
            wrong_diff = np.asarray([np.nan])
            shuffled_diff = np.asarray([np.nan])
            wrong_ci = (float("nan"), float("nan"))
            shuffled_ci = (float("nan"), float("nan"))

        learner_means = (
            contrasts[
                (contrasts["target"] == target) & (contrasts["source"] == source)
            ]
            .groupby("learner")["gain_ood"]
            .mean()
        )
        quality = metadata.loc[(target, source)]
        rows.append(
            {
                "target": target,
                "source": source,
                "programme_cluster": target_spec["programme_cluster"],
                "primary_edge_class": target_spec["primary_edge_class"]
                if is_primary
                else quality["edge_class"],
                "relation": quality["relation"],
                "neighborhood": quality["neighborhood"],
                "is_designated_primary": is_primary,
                "is_wrong_control": source == wrong_source,
                "is_shuffled_control": bool(quality["is_shuffled_control"]),
                "repeats": int(len(frame)),
                "gain_all_mean": float(frame["gain_all"].mean()),
                "gain_id_mean": float(frame["gain_id"].mean()),
                "gain_id_ci_lo": intervals["q1"][0],
                "gain_id_ci_hi": intervals["q1"][1],
                "gain_ood_mean": float(frame["gain_ood"].mean()),
                "gain_ood_ci_lo": intervals["q4"][0],
                "gain_ood_ci_hi": intervals["q4"][1],
                "gain_specific_mean": float(frame["gain_specific"].mean()),
                "gain_specific_ci_lo": intervals["specific"][0],
                "gain_specific_ci_hi": intervals["specific"][1],
                "base_ood_r2_mean": float(frame["base_ood_r2"].mean()),
                "aug_ood_r2_mean": float(frame["aug_ood_r2"].mean()),
                "positive_ood_repeat_fraction": float((frame["gain_ood"] > 0).mean()),
                "positive_ood_learners": int((learner_means > 0).sum()),
                "learners_evaluated": int(len(learner_means)),
                "one_sided_sign_flip_p": p_value,
                "holm_p": float("nan"),
                "primary_minus_wrong_mean": float(np.nanmean(wrong_diff))
                if is_primary
                else float("nan"),
                "primary_minus_wrong_ci_lo": wrong_ci[0],
                "primary_minus_wrong_ci_hi": wrong_ci[1],
                "primary_minus_shuffled_mean": float(np.nanmean(shuffled_diff))
                if is_primary
                else float("nan"),
                "primary_minus_shuffled_ci_lo": shuffled_ci[0],
                "primary_minus_shuffled_ci_hi": shuffled_ci[1],
                "post_exclusion_overlap": int(quality["post_exclusion_overlap"]),
                "interval_method": interval_method,
            }
        )
    summary = pd.DataFrame(rows)
    primary_mask = summary["is_designated_primary"]
    summary.loc[primary_mask, "holm_p"] = holm_adjust(
        summary.loc[primary_mask, "one_sided_sign_flip_p"].to_numpy(float)
    )
    summary["classification"] = summary.apply(
        classify_edge, axis=1, gate=design["edge_gate"]
    )
    return summary.sort_values(
        ["target", "is_designated_primary", "neighborhood", "source"],
        ascending=[True, False, False, True],
    ).reset_index(drop=True)


def programme_bootstrap(
    primary_edges: pd.DataFrame, n_boot: int, seed: int
) -> tuple[float, float, float, pd.DataFrame]:
    programme = (
        primary_edges.groupby("programme_cluster", as_index=False)
        .agg(
            mean_primary_ood_gain=("gain_ood_mean", "mean"),
            primary_edges=("target", "size"),
            full_pass_edges=(
                "classification",
                lambda value: int((value == "ood-repair-gate-passed").sum()),
            ),
        )
        .sort_values("programme_cluster")
        .reset_index(drop=True)
    )
    values = programme["mean_primary_ood_gain"].to_numpy(float)
    rng = np.random.default_rng(seed)
    weights = rng.multinomial(
        len(values), np.full(len(values), 1.0 / len(values)), size=n_boot
    )
    bootstrap = weights @ values / len(values)
    ci_lo, ci_hi = np.percentile(bootstrap, [2.5, 97.5])
    return float(values.mean()), float(ci_lo), float(ci_hi), programme


def flatten(items: Iterable[list[dict[str, Any]]]) -> list[dict[str, Any]]:
    return [row for group in items for row in group]


def output_paths(smoke: bool) -> dict[str, Path]:
    stem = "multi_target_ood_smoke" if smoke else "multi_target_ood"
    return {
        "strata": RESULTS / f"{stem}_strata.csv",
        "source_quality": RESULTS / f"{stem}_source_quality.csv",
        "metrics": RESULTS / f"{stem}_metrics.csv",
        "contrasts": RESULTS / f"{stem}_contrasts.csv",
        "group_errors": RESULTS / f"{stem}_group_errors.csv",
        "edge_summary": RESULTS / f"{stem}_edge_summary.csv",
        "target_summary": RESULTS / f"{stem}_target_summary.csv",
        "summary": RESULTS / f"{stem}_summary.json",
        "complete": RESULTS / f"{stem}_COMPLETE.json",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--jobs", type=int, default=1)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    ensure_output_dirs()
    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    paths = output_paths(args.smoke)
    if paths["complete"].exists() and not args.overwrite:
        raise FileExistsError(
            f"{paths['complete']} already exists; use --overwrite only for an intentional rerun"
        )
    frozen_hashes = validate_freeze(design)
    parent = json.loads(PARENT_DESIGN_PATH.read_text(encoding="utf-8"))
    included = design["eligibility"]["included_targets"]
    if set(included) != set(design["targets"]):
        raise AssertionError("Eligibility target list and target specifications disagree")

    print("Loading inherited tasks and feature spaces", flush=True)
    tasks = {
        task_id: load_task(task_id, spec)
        for task_id, spec in parent["tasks"].items()
        if task_id in parent["targets"]
        or any(
            task_id == edge["task"]
            for target_spec in parent["targets"].values()
            for edge in target_spec["sources"]
        )
    }
    build_feature_spaces(tasks)
    full_parent = deepcopy(parent)
    partitions, partition_table = partition_targets(full_parent, tasks)

    minimum_groups = int(design["eligibility"]["minimum_evaluation_groups"])
    for target in included:
        evaluation = np.r_[
            partitions[target]["discovery"], partitions[target]["confirmation"]
        ]
        groups = tasks[target].frame.loc[evaluation, "group"].nunique()
        if groups < minimum_groups:
            raise AssertionError(f"Included target {target} has only {groups} evaluation groups")
    for target in design["eligibility"]["excluded_targets"]:
        evaluation = np.r_[
            partitions[target]["discovery"], partitions[target]["confirmation"]
        ]
        groups = tasks[target].frame.loc[evaluation, "group"].nunique()
        if groups >= minimum_groups:
            raise AssertionError(
                f"Excluded target {target} now has {groups} groups and meets eligibility"
            )

    analysis_parent = deepcopy(parent)
    analysis_parent["targets"] = {
        target: deepcopy(parent["targets"][target]) for target in included
    }
    if any(len(value["sources"]) != 5 for value in analysis_parent["targets"].values()):
        raise AssertionError("The benchmark requires five inherited sources per target")
    real_edges = sum(len(value["sources"]) for value in analysis_parent["targets"].values())
    if real_edges != 40:
        raise AssertionError(f"Expected 40 inherited real edges, found {real_edges}")

    print("Assigning fixed feature-distance OOD strata", flush=True)
    strata_frames: list[pd.DataFrame] = []
    for target in included:
        evaluation = np.sort(
            np.r_[
                partitions[target]["discovery"], partitions[target]["confirmation"]
            ]
        )
        strata_frames.append(
            assign_group_quartiles(
                target,
                tasks[target],
                partitions[target]["development"],
                evaluation,
            )
        )
    strata = pd.concat(strata_frames, ignore_index=True)

    print("Fitting leakage-excluded donor models", flush=True)
    donor_models, quality = fit_source_models(analysis_parent, tasks, partitions)
    metadata_rows: list[dict[str, Any]] = []
    source_features_by_target: dict[str, dict[str, np.ndarray]] = {}
    for target in included:
        target_spec = design["targets"][target]
        inherited_edges = {
            edge["task"]: edge for edge in analysis_parent["targets"][target]["sources"]
        }
        if target_spec["primary_source"] not in inherited_edges:
            raise AssertionError(f"Primary source missing from inherited edges for {target}")
        if target_spec["wrong_source"] not in inherited_edges:
            raise AssertionError(f"Wrong source missing from inherited edges for {target}")
        source_features: dict[str, np.ndarray] = {}
        for source, edge in inherited_edges.items():
            if tasks[source].spec["kind"] != tasks[target].spec["kind"]:
                raise AssertionError(f"Representation mismatch for {source}->{target}")
            source_features[source] = np.asarray(
                donor_models[(target, source)].predict(np.asarray(tasks[target].X)),
                dtype=np.float32,
            )
            row = quality[
                (quality["target"] == target) & (quality["source"] == source)
            ].iloc[0]
            metadata_rows.append(
                {
                    **row.to_dict(),
                    "relation": edge["relation"],
                    "neighborhood": int(edge["neighborhood"]),
                    "edge_class": "real-inherited-edge",
                    "is_shuffled_control": False,
                    "parent_source": "",
                }
            )
        primary = target_spec["primary_source"]
        shuffled_id = f"shuffled::{primary}"
        rng = np.random.default_rng(stable_seed(int(design["seed"]), target, "shuffle"))
        source_features[shuffled_id] = source_features[primary][
            rng.permutation(len(source_features[primary]))
        ]
        primary_quality = next(
            row
            for row in metadata_rows
            if row["target"] == target and row["source"] == primary
        )
        metadata_rows.append(
            {
                **primary_quality,
                "source": shuffled_id,
                "label": f"Shuffled {primary_quality['label']}",
                "relation": "shuffled-control",
                "neighborhood": -1,
                "edge_class": "shuffled-control",
                "is_shuffled_control": True,
                "parent_source": primary,
            }
        )
        source_features_by_target[target] = source_features
    source_quality = pd.DataFrame(metadata_rows)
    if (source_quality["post_exclusion_overlap"] != 0).any():
        raise AssertionError("Non-zero donor/evaluation identity overlap after exclusion")

    repeats = int(
        design["inference"]["smoke_repeats"]
        if args.smoke
        else design["inference"]["formal_repeats"]
    )
    n_boot = int(
        design["inference"]["smoke_bootstrap_resamples"]
        if args.smoke
        else design["inference"]["formal_bootstrap_resamples"]
    )
    permutations = int(
        design["inference"]["smoke_sign_flip_permutations"]
        if args.smoke
        else design["inference"]["formal_sign_flip_permutations"]
    )
    learners = [design["learners"]["primary"], *design["learners"]["sensitivities"]]

    run_inputs: dict[tuple[str, int], TargetRunInput] = {}
    for target in included:
        task = tasks[target]
        development = partitions[target]["development"]
        budget = int(partitions[target]["budget"])
        target_strata = strata[strata["target"] == target]
        evaluation = target_strata["entity_index"].to_numpy(int)
        scope_by_index = dict(
            zip(
                target_strata["entity_index"].astype(int),
                target_strata["scope"].astype(str),
            )
        )
        for repeat in range(repeats):
            rng = np.random.default_rng(
                stable_seed(int(design["seed"]), target, "target-draw", str(repeat))
            )
            local = sample_groups(
                task.frame.loc[development, "group"].astype(str).to_numpy(),
                budget,
                rng,
            )
            train_index = development[local]
            run_inputs[(target, repeat)] = TargetRunInput(
                target_id=target,
                x=np.asarray(task.X, dtype=np.float32),
                y=task.frame["value"].to_numpy(float),
                groups=task.frame["group"].astype(str).to_numpy(),
                train_index=np.asarray(train_index, dtype=int),
                evaluation=np.asarray(evaluation, dtype=int),
                scope_by_index=scope_by_index,
                source_features=source_features_by_target[target],
                primary_source=design["targets"][target]["primary_source"],
                trees=int(design["learners"]["tree_estimators"]),
                base_seed=int(design["seed"]),
            )

    jobs = [
        delayed(evaluate_one_repeat)(run_inputs[(target, repeat)], learner, repeat)
        for target in included
        for learner in learners
        for repeat in range(repeats)
    ]
    print(
        f"Running {len(jobs)} target/learner/repeat comparisons with {args.jobs} workers",
        flush=True,
    )
    evaluated = Parallel(
        n_jobs=args.jobs,
        verbose=10,
        max_nbytes="10M",
        mmap_mode="r",
    )(jobs)
    metric_rows = flatten(result[0] for result in evaluated)
    contrast_rows = flatten(result[1] for result in evaluated)
    error_rows = flatten(result[2] for result in evaluated)
    metrics_frame = pd.DataFrame(metric_rows)
    contrasts = pd.DataFrame(contrast_rows)
    group_errors = pd.DataFrame(error_rows)

    expected_sources = 6
    expected_metric_rows = len(included) * len(learners) * repeats * expected_sources * 3
    expected_contrast_rows = len(included) * len(learners) * repeats * expected_sources
    if len(metrics_frame) != expected_metric_rows:
        raise AssertionError(
            f"Expected {expected_metric_rows} metric rows, found {len(metrics_frame)}"
        )
    if len(contrasts) != expected_contrast_rows:
        raise AssertionError(
            f"Expected {expected_contrast_rows} contrast rows, found {len(contrasts)}"
        )

    print("Computing frozen edge gates and programme inference", flush=True)
    edge_summary = summarize_edges(
        contrasts, group_errors, source_quality, design, n_boot, permutations
    )
    primary_edges = edge_summary[edge_summary["is_designated_primary"]].copy()
    programme_mean, programme_ci_lo, programme_ci_hi, programme = programme_bootstrap(
        primary_edges,
        n_boot,
        stable_seed(int(design["seed"]), "programme-bootstrap"),
    )
    passed_clusters = int(
        programme.loc[programme["full_pass_edges"] > 0, "programme_cluster"].nunique()
    )
    cross_database = primary_edges[
        primary_edges["primary_edge_class"] == "cross-database-neighbor"
    ]
    cross_database_passes = int(
        (cross_database["classification"] == "ood-repair-gate-passed").sum()
    )
    cohort_gate = design["cohort_gate"]
    selective_cohort_pass = bool(
        passed_clusters
        >= cohort_gate["minimum_independent_programme_clusters_with_full_primary_edge_pass"]
        and programme_ci_lo
        > cohort_gate["programme_bootstrap_mean_primary_ood_gain_ci_lower_above"]
    )
    cross_database_upgrade_pass = bool(
        selective_cohort_pass
        and cross_database_passes
        >= cohort_gate["cross_database_upgrade_minimum_full_passes"]
    )

    target_summary = primary_edges[
        [
            "target",
            "programme_cluster",
            "source",
            "primary_edge_class",
            "gain_id_mean",
            "gain_ood_mean",
            "gain_specific_mean",
            "gain_ood_ci_lo",
            "gain_ood_ci_hi",
            "gain_specific_ci_lo",
            "gain_specific_ci_hi",
            "base_ood_r2_mean",
            "aug_ood_r2_mean",
            "positive_ood_repeat_fraction",
            "primary_minus_wrong_mean",
            "primary_minus_shuffled_mean",
            "positive_ood_learners",
            "one_sided_sign_flip_p",
            "holm_p",
            "classification",
        ]
    ].copy()

    for key, frame in (
        ("strata", strata),
        ("source_quality", source_quality),
        ("metrics", metrics_frame),
        ("contrasts", contrasts),
        ("group_errors", group_errors),
        ("edge_summary", edge_summary),
        ("target_summary", target_summary),
    ):
        frame.to_csv(paths[key], index=False)

    summary = {
        "status": "smoke-complete" if args.smoke else "formal-complete",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "smoke" if args.smoke else "formal",
        "design_sha256": sha256_file(DESIGN_PATH),
        **frozen_hashes,
        "targets": len(included),
        "programme_clusters": int(primary_edges["programme_cluster"].nunique()),
        "real_edges": real_edges,
        "shuffled_controls": len(included),
        "evaluated_source_features": int(
            source_quality[["target", "source"]].drop_duplicates().shape[0]
        ),
        "learners": learners,
        "repeats": repeats,
        "bootstrap_resamples": n_boot,
        "sign_flip_permutations": permutations,
        "rows": {
            "strata": len(strata),
            "source_quality": len(source_quality),
            "metrics": len(metrics_frame),
            "contrasts": len(contrasts),
            "group_errors": len(group_errors),
            "edge_summary": len(edge_summary),
            "target_summary": len(target_summary),
        },
        "primary_edge_classifications": {
            str(key): int(value)
            for key, value in primary_edges["classification"].value_counts().items()
        },
        "programme_inference": {
            "mean_primary_ood_gain": programme_mean,
            "ci95": [programme_ci_lo, programme_ci_hi],
            "programme_clusters_with_full_pass": passed_clusters,
            "selective_ood_repair_cohort_gate_passed": selective_cohort_pass,
        },
        "cross_database_inference": {
            "designated_edges": int(len(cross_database)),
            "full_passes": cross_database_passes,
            "cross_database_upgrade_gate_passed": cross_database_upgrade_pass,
        },
        "claim_guard": design["claim_guard"],
    }
    paths["summary"].write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    output_hashes = {
        path.name: sha256_file(path)
        for name, path in paths.items()
        if name != "complete" and path.exists()
    }
    complete = {
        "status": summary["status"],
        "created_utc": summary["created_utc"],
        "design_sha256": summary["design_sha256"],
        "output_hashes": output_hashes,
        "claim_guard": design["claim_guard"],
    }
    paths["complete"].write_text(
        json.dumps(complete, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
