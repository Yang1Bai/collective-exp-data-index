"""Run the post-diagnostic neighborhood-transfer policy benchmark.

The policy family was chosen after inspecting the completed OBELiX campaign.
Results are method-development evidence only and cannot redefine that campaign.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

try:
    from .run_obelix_ood_discovery import (
        INPUT_META_PATH,
        INPUT_PATH,
        RESULTS,
        initial_indices,
        load_frozen_input,
        make_model,
        stable_seed,
        true_hit_set,
    )
except ImportError:
    from run_obelix_ood_discovery import (
        INPUT_META_PATH,
        INPUT_PATH,
        RESULTS,
        initial_indices,
        load_frozen_input,
        make_model,
        stable_seed,
        true_hit_set,
    )


ANALYSIS = Path(__file__).resolve().parent
DESIGN_PATH = ANALYSIS / "neighbor_transfer_policy_design.json"
POLICIES = [
    "uniform_random",
    "target_ucb_beta1",
    "target_mean_greedy",
    "composition_novelty",
    "thermoelectric_prior_static",
    "target_source_rank_fusion",
    "target_source_novelty_rank_fusion",
    "alloy_prior_static_control",
    "catalysis_prior_static_control",
    "shuffled_thermoelectric_static_control",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def percentile_rank(values: np.ndarray) -> np.ndarray:
    return pd.Series(np.asarray(values, dtype=float)).rank(
        method="average", pct=True
    ).to_numpy(float)


def composition_novelty(
    candidate_features: np.ndarray, labelled_features: np.ndarray
) -> np.ndarray:
    squared = np.sum(
        (candidate_features[:, None, :] - labelled_features[None, :, :]) ** 2,
        axis=2,
    )
    return np.sqrt(np.min(squared, axis=1))


def stable_argmax(score: np.ndarray, pool: list[int], target: pd.DataFrame) -> int:
    best = np.flatnonzero(score == np.max(score))
    if len(best) == 1:
        return int(best[0])
    return int(
        min(best, key=lambda position: target.at[pool[int(position)], "material_key"])
    )


def policy_score(
    *,
    policy: str,
    target: pd.DataFrame,
    x: np.ndarray,
    y: np.ndarray,
    priors: dict[str, np.ndarray],
    pool: list[int],
    labelled: list[int],
    seed: int,
    step: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    mean = np.full(len(pool), np.nan)
    spread = np.full(len(pool), np.nan)
    novelty = composition_novelty(x[pool], x[labelled])
    if policy == "composition_novelty":
        return novelty, mean, spread, novelty
    static_prior = {
        "thermoelectric_prior_static": "thermoelectric_prior",
        "alloy_prior_static_control": "alloy_control",
        "catalysis_prior_static_control": "catalysis_control",
        "shuffled_thermoelectric_static_control": "shuffled_thermoelectric",
    }
    if policy in static_prior:
        return priors[static_prior[policy]][pool], mean, spread, novelty

    model = make_model(
        "extra-trees-primary", stable_seed(f"policy:{policy}:{seed}:{step}")
    ).fit(x[labelled], y[labelled])
    tree_predictions = np.asarray(
        [tree.predict(x[pool]) for tree in model.estimators_], dtype=float
    )
    mean = tree_predictions.mean(axis=0)
    spread = tree_predictions.std(axis=0)
    if policy == "target_ucb_beta1":
        score = mean + spread
    elif policy == "target_mean_greedy":
        score = mean
    elif policy == "target_source_rank_fusion":
        score = percentile_rank(mean) + percentile_rank(
            priors["thermoelectric_prior"][pool]
        )
    elif policy == "target_source_novelty_rank_fusion":
        score = (
            percentile_rank(mean)
            + percentile_rank(priors["thermoelectric_prior"][pool])
            + 0.5 * (percentile_rank(novelty) - 0.5)
        )
    else:
        raise ValueError(policy)
    return score, mean, spread, novelty


def run_campaign(
    *,
    policy: str,
    target: pd.DataFrame,
    x: np.ndarray,
    y: np.ndarray,
    priors: dict[str, np.ndarray],
    candidates: list[int],
    initial: list[int],
    hit_set: set[int],
    budget: int,
    seed: int,
) -> tuple[int, list[dict]]:
    pool = list(candidates)
    labelled = list(initial)
    trajectory: list[dict] = []
    first_hit = budget + 1
    if policy == "uniform_random":
        rng = np.random.default_rng(stable_seed(f"random:{seed}:{len(pool)}"))
        order = list(rng.permutation(pool))
        for step, chosen in enumerate(order[:budget], start=1):
            is_hit = chosen in hit_set
            trajectory.append(
                {
                    "step": step,
                    "chosen_index": int(chosen),
                    "chosen_key": target.at[chosen, "material_key"],
                    "chosen_y": float(y[chosen]),
                    "is_true_top5_hit": bool(is_hit),
                    "acquisition_score": np.nan,
                    "acquisition_mean": np.nan,
                    "acquisition_spread": np.nan,
                    "composition_novelty": np.nan,
                }
            )
            if is_hit and first_hit == budget + 1:
                first_hit = step
        return first_hit, trajectory

    for step in range(1, budget + 1):
        score, mean, spread, novelty = policy_score(
            policy=policy,
            target=target,
            x=x,
            y=y,
            priors=priors,
            pool=pool,
            labelled=labelled,
            seed=seed,
            step=step,
        )
        position = stable_argmax(score, pool, target)
        chosen = pool.pop(position)
        labelled.append(chosen)
        is_hit = chosen in hit_set
        trajectory.append(
            {
                "step": step,
                "chosen_index": int(chosen),
                "chosen_key": target.at[chosen, "material_key"],
                "chosen_y": float(y[chosen]),
                "is_true_top5_hit": bool(is_hit),
                "acquisition_score": float(score[position]),
                "acquisition_mean": (
                    float(mean[position]) if np.isfinite(mean[position]) else np.nan
                ),
                "acquisition_spread": (
                    float(spread[position])
                    if np.isfinite(spread[position])
                    else np.nan
                ),
                "composition_novelty": float(novelty[position]),
            }
        )
        if is_hit and first_hit == budget + 1:
            first_hit = step
    return first_hit, trajectory


def run_seed(
    *,
    seed: int,
    scope: str,
    target: pd.DataFrame,
    x: np.ndarray,
    priors: dict[str, np.ndarray],
    candidates: list[int],
    hit_set: set[int],
    budget: int,
    initial_n: int,
) -> tuple[list[dict], list[dict]]:
    y = target["value"].to_numpy(float)
    initial = initial_indices(target, seed, initial_n)
    reaches: list[dict] = []
    trajectories: list[dict] = []
    for policy in POLICIES:
        reach, trajectory = run_campaign(
            policy=policy,
            target=target,
            x=x,
            y=y,
            priors=priors,
            candidates=candidates,
            initial=initial,
            hit_set=hit_set,
            budget=budget,
            seed=seed,
        )
        reaches.append(
            {
                "scope": scope,
                "seed": seed,
                "policy": policy,
                "candidate_n": len(candidates),
                "true_hit_n": len(hit_set),
                "initial_target_n": len(initial),
                "budget": budget,
                "experiments_to_hit": reach,
                "censored": reach > budget,
            }
        )
        trajectories.extend(
            {
                "scope": scope,
                "seed": seed,
                "policy": policy,
                **row,
            }
            for row in trajectory
        )
    return reaches, trajectories


def signflip_p(effect: np.ndarray, label: str, draws: int) -> float:
    observed = float(np.mean(effect))
    rng = np.random.default_rng(stable_seed(f"policy-sign:{label}"))
    exceed = 0
    remaining = draws
    while remaining:
        batch = min(1000, remaining)
        signs = rng.choice((-1.0, 1.0), size=(batch, len(effect)))
        exceed += int(np.sum(np.mean(signs * effect, axis=1) >= observed))
        remaining -= batch
    return float((exceed + 1) / (draws + 1))


def contrast(
    reaches: pd.DataFrame,
    *,
    scope: str,
    family: str,
    left: str,
    right: str,
    bootstrap_n: int,
    signflip_n: int,
) -> tuple[dict, pd.DataFrame]:
    local = reaches[reaches["scope"] == scope]
    paired = local.pivot(index="seed", columns="policy", values="experiments_to_hit")
    effect = (paired[right] - paired[left]).to_numpy(float)
    label = f"{scope}:{family}:{left}:{right}"
    rng = np.random.default_rng(stable_seed(f"policy-boot:{label}"))
    indices = rng.integers(0, len(effect), size=(bootstrap_n, len(effect)))
    bootstrap = np.mean(effect[indices], axis=1)
    right_mean = float(paired[right].mean())
    result = {
        "scope": scope,
        "family": family,
        "left_policy": left,
        "right_policy": right,
        "seeds": int(len(effect)),
        "left_mean_experiments": float(paired[left].mean()),
        "right_mean_experiments": right_mean,
        "mean_experiments_saved_by_left": float(np.mean(effect)),
        "bootstrap_95": [
            float(value) for value in np.quantile(bootstrap, [0.025, 0.975])
        ],
        "relative_saved_vs_right": float(np.mean(effect) / right_mean),
        "fraction_seeds_left_improves": float(np.mean(effect > 0)),
        "fraction_seeds_tied": float(np.mean(effect == 0)),
        "signflip_p_one_sided": signflip_p(effect, label, signflip_n),
        "left_censor_fraction": float(
            np.mean(paired[left] > int(local["budget"].iloc[0]))
        ),
        "right_censor_fraction": float(
            np.mean(paired[right] > int(local["budget"].iloc[0]))
        ),
    }
    bootstrap_frame = pd.DataFrame(
        {
            "scope": scope,
            "family": family,
            "left_policy": left,
            "right_policy": right,
            "bootstrap": np.arange(bootstrap_n),
            "mean_experiments_saved_by_left": bootstrap,
        }
    )
    return result, bootstrap_frame


def holm_adjust(frame: pd.DataFrame) -> pd.Series:
    adjusted = pd.Series(index=frame.index, dtype=float)
    order = frame["signflip_p_one_sided"].sort_values().index.tolist()
    running = 0.0
    total = len(order)
    for rank, index in enumerate(order):
        candidate = min(1.0, (total - rank) * frame.at[index, "signflip_p_one_sided"])
        running = max(running, candidate)
        adjusted.at[index] = running
    return adjusted


def add_gates(row: dict) -> dict:
    gates = {
        "holm_p_le_0_05": bool(row["holm_p"] <= 0.05),
        "ci_lower_above_zero": bool(row["bootstrap_95"][0] > 0),
        "mean_saved_ge_5": bool(row["mean_experiments_saved_by_left"] >= 5),
        "relative_saved_ge_0_25": bool(row["relative_saved_vs_right"] >= 0.25),
        "fraction_improved_ge_0_60": bool(
            row["fraction_seeds_left_improves"] >= 0.60
        ),
        "censoring_not_higher": bool(
            row["left_censor_fraction"] <= row["right_censor_fraction"]
        ),
    }
    row["gates"] = gates
    row["passes_development_gates"] = bool(all(gates.values()))
    return row


def secondary_utility(
    trajectories: pd.DataFrame,
    *,
    target: pd.DataFrame,
    pool_by_scope: dict[str, list[int]],
    horizons: tuple[int, ...] = (5, 10, 20, 40),
) -> pd.DataFrame:
    rows: list[dict] = []
    for (scope, seed, policy), local in trajectories.groupby(
        ["scope", "seed", "policy"], sort=False
    ):
        local = local.sort_values("step")
        hits = local["is_true_top5_hit"].astype(bool).to_numpy()
        cumulative = np.cumsum(hits)
        pool = pool_by_scope[str(scope)]
        pool_max = float(target.loc[pool, "value"].max())
        true_hit_n = max(1, math.ceil(0.05 * len(pool)))
        record = {
            "scope": scope,
            "seed": int(seed),
            "policy": policy,
            "cumulative_hit_auc_to_40": float(np.sum(cumulative)),
        }
        for horizon in horizons:
            local_horizon = local.iloc[:horizon]
            hit_count = int(local_horizon["is_true_top5_hit"].astype(bool).sum())
            best_y = float(local_horizon["chosen_y"].max())
            record[f"top5_hits_at_{horizon}"] = hit_count
            record[f"top5_recall_at_{horizon}"] = float(hit_count / true_hit_n)
            record[f"best_y_at_{horizon}"] = best_y
            record[f"regret_to_pool_max_at_{horizon}"] = float(pool_max - best_y)
        rows.append(record)
    return pd.DataFrame(rows)


def main(
    *,
    input_path: Path,
    input_metadata_path: Path,
    output_dir: Path,
    validate_only: bool,
) -> None:
    design_bytes = DESIGN_PATH.read_bytes()
    design = json.loads(design_bytes)
    metadata, arrays, target = load_frozen_input(input_path, input_metadata_path)
    if metadata["input_sha256"] != design["input"]["required_input_sha256"]:
        raise AssertionError("Policy design and frozen input hash disagree")
    x = np.asarray(arrays["composition_features"], dtype=float)
    priors = {
        "thermoelectric_prior": np.asarray(arrays["thermoelectric_prior"], dtype=float),
        "alloy_control": np.asarray(arrays["alloy_control"], dtype=float),
        "catalysis_control": np.asarray(arrays["catalysis_control"], dtype=float),
    }
    shuffle_rng = np.random.default_rng(20260714)
    priors["shuffled_thermoelectric"] = shuffle_rng.permutation(
        priors["thermoelectric_prior"]
    )
    official = target.index[target["split"] == "test"].astype(int).tolist()
    hard = [index for index in official if target.at[index, "hard_ood_selected"]]
    pool_by_scope = {"official_test": official, "hard_ood_40pct": hard}
    design_hash = hashlib.sha256(design_bytes).hexdigest()
    if validate_only:
        print(
            json.dumps(
                {
                    "status": "validated",
                    "design_sha256": design_hash,
                    "input_sha256": metadata["input_sha256"],
                    "policies": POLICIES,
                    "candidate_pools": {
                        scope: len(pool) for scope, pool in pool_by_scope.items()
                    },
                },
                indent=2,
            )
        )
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_root = output_dir / "neighbor_transfer_policy_checkpoints" / (
        f"{design_hash[:12]}-{metadata['input_sha256'][:12]}"
    )
    checkpoint_root.mkdir(parents=True, exist_ok=True)
    seeds = int(design["campaign"]["paired_seeds"])
    budget = int(design["campaign"]["budget"])
    initial_n = int(design["campaign"]["initial_target_labels"])
    workers = max(1, int(os.environ.get("OOD_WORKERS", min(20, os.cpu_count() or 1))))
    batch_size = max(1, int(os.environ.get("OOD_BATCH_SIZE", workers)))
    reach_parts: list[pd.DataFrame] = []
    trajectory_parts: list[pd.DataFrame] = []
    for scope, candidates in pool_by_scope.items():
        hit_set = true_hit_set(target, candidates)
        for start in range(0, seeds, batch_size):
            stop = min(seeds, start + batch_size)
            stem = f"{scope}__{start:04d}-{stop:04d}"
            reach_path = checkpoint_root / f"{stem}__reach.csv"
            trajectory_path = checkpoint_root / f"{stem}__trajectory.csv"
            if not (reach_path.exists() and trajectory_path.exists()):
                completed = Parallel(n_jobs=workers, verbose=0)(
                    delayed(run_seed)(
                        seed=seed,
                        scope=scope,
                        target=target,
                        x=x,
                        priors=priors,
                        candidates=candidates,
                        hit_set=hit_set,
                        budget=budget,
                        initial_n=initial_n,
                    )
                    for seed in range(start, stop)
                )
                reach_rows = [row for batch in completed for row in batch[0]]
                trajectory_rows = [row for batch in completed for row in batch[1]]
                pd.DataFrame(reach_rows).to_csv(reach_path, index=False)
                pd.DataFrame(trajectory_rows).to_csv(trajectory_path, index=False)
            reach_parts.append(pd.read_csv(reach_path))
            trajectory_parts.append(pd.read_csv(trajectory_path))

    reaches = pd.concat(reach_parts, ignore_index=True)
    trajectories = pd.concat(trajectory_parts, ignore_index=True)
    expected_rows = len(pool_by_scope) * seeds * len(POLICIES)
    if len(reaches) != expected_rows:
        raise AssertionError(f"Expected {expected_rows} reach rows, found {len(reaches)}")
    if not all(
        len(group) == seeds
        for _, group in reaches.groupby(["scope", "policy"], sort=False)
    ):
        raise AssertionError("Incomplete paired policy seed coverage")
    expected_trajectory_rows = len(pool_by_scope) * seeds * len(POLICIES) * budget
    if len(trajectories) != expected_trajectory_rows:
        raise AssertionError(
            f"Expected {expected_trajectory_rows} trajectory rows, found "
            f"{len(trajectories)}"
        )

    comparisons = [
        ("policy_validity", "target_mean_greedy", "uniform_random"),
        ("policy_validity", "composition_novelty", "uniform_random"),
        ("source_only", "thermoelectric_prior_static", "uniform_random"),
        ("source_only", "thermoelectric_prior_static", "alloy_prior_static_control"),
        ("source_only", "thermoelectric_prior_static", "catalysis_prior_static_control"),
        (
            "source_only",
            "thermoelectric_prior_static",
            "shuffled_thermoelectric_static_control",
        ),
        ("incremental_borrowing", "target_source_rank_fusion", "target_mean_greedy"),
        (
            "incremental_borrowing",
            "target_source_novelty_rank_fusion",
            "target_mean_greedy",
        ),
        ("failure_anatomy", "target_mean_greedy", "target_ucb_beta1"),
        ("failure_anatomy", "target_source_rank_fusion", "target_ucb_beta1"),
    ]
    bootstrap_n = int(design["inference"]["paired_bootstrap_replicates"])
    signflip_n = int(design["inference"]["paired_sign_flip_draws"])
    contrast_rows: list[dict] = []
    bootstrap_parts: list[pd.DataFrame] = []
    for scope in pool_by_scope:
        for family, left, right in comparisons:
            result, bootstrap = contrast(
                reaches,
                scope=scope,
                family=family,
                left=left,
                right=right,
                bootstrap_n=bootstrap_n,
                signflip_n=signflip_n,
            )
            contrast_rows.append(result)
            bootstrap_parts.append(bootstrap)
    contrasts = pd.DataFrame(contrast_rows)
    contrasts["holm_p"] = np.nan
    for (_, family), local in contrasts.groupby(["scope", "family"], sort=False):
        if family == "failure_anatomy":
            contrasts.loc[local.index, "holm_p"] = local["signflip_p_one_sided"]
        else:
            contrasts.loc[local.index, "holm_p"] = holm_adjust(local)
    contrast_records = [add_gates(row) for row in contrasts.to_dict("records")]
    contrasts_flat = pd.json_normalize(contrast_records, sep="__")

    reach_path = output_dir / "neighbor_transfer_policy_reach.csv"
    trajectory_path = output_dir / "neighbor_transfer_policy_trajectories.csv"
    contrast_path = output_dir / "neighbor_transfer_policy_contrasts.csv"
    bootstrap_path = output_dir / "neighbor_transfer_policy_bootstrap.csv"
    utility_path = output_dir / "neighbor_transfer_policy_secondary_utility.csv"
    summary_path = output_dir / "neighbor_transfer_policy_summary.json"
    reaches.to_csv(reach_path, index=False)
    trajectories.to_csv(trajectory_path, index=False)
    contrasts_flat.to_csv(contrast_path, index=False)
    pd.concat(bootstrap_parts, ignore_index=True).to_csv(bootstrap_path, index=False)
    utility = secondary_utility(
        trajectories, target=target, pool_by_scope=pool_by_scope
    )
    utility.to_csv(utility_path, index=False)

    policy_summary = (
        reaches.groupby(["scope", "policy"], sort=True)
        .agg(
            seeds=("seed", "size"),
            mean_experiments=("experiments_to_hit", "mean"),
            median_experiments=("experiments_to_hit", "median"),
            censor_fraction=("censored", "mean"),
        )
        .reset_index()
        .to_dict("records")
    )
    utility_summary = (
        utility.groupby(["scope", "policy"], sort=True)
        .mean(numeric_only=True)
        .reset_index()
        .drop(columns=["seed"])
        .to_dict("records")
    )
    summary = {
        "analysis_status": "exploratory-post-diagnostic-method-selection",
        "design_sha256": design_hash,
        "input_sha256": metadata["input_sha256"],
        "policies": policy_summary,
        "secondary_utility": utility_summary,
        "contrasts": contrast_records,
        "claim_guard": design["claim_guard"],
    }
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    complete = {
        "status": "complete",
        "design_sha256": design_hash,
        "input_sha256": metadata["input_sha256"],
        "summary_sha256": sha256_file(summary_path),
    }
    (output_dir / "neighbor_transfer_policy_COMPLETE.json").write_text(
        json.dumps(complete, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=INPUT_PATH)
    parser.add_argument("--input-metadata", type=Path, default=INPUT_META_PATH)
    parser.add_argument("--output-dir", type=Path, default=RESULTS)
    parser.add_argument("--validate-only", action="store_true")
    arguments = parser.parse_args()
    main(
        input_path=arguments.input,
        input_metadata_path=arguments.input_metadata,
        output_dir=arguments.output_dir,
        validate_only=arguments.validate_only,
    )
