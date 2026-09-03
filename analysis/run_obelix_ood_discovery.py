"""Run the frozen OBELiX official-test OOD sequential discovery simulation."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from sklearn.ensemble import ExtraTreesRegressor, RandomForestRegressor

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis"
RESULTS = ANALYSIS / "results"
DESIGN_PATH = ANALYSIS / "obelix_ood_discovery_design.json"
INPUT_PATH = RESULTS / "obelix_ood_discovery_input.npz"
INPUT_META_PATH = RESULTS / "obelix_ood_discovery_input_meta.json"
RANDOM_SEED = 20260713


def stable_seed(label: str) -> int:
    return int(hashlib.sha256(label.encode("utf-8")).hexdigest()[:8], 16)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_array(values: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(values).tobytes()).hexdigest()


def sample_groups(
    groups: list[str], target_n: int, rng: np.random.Generator
) -> np.ndarray:
    """Select intact groups with the frozen deterministic near-target rule."""
    members: dict[str, list[int]] = defaultdict(list)
    for index, group in enumerate(groups):
        members[str(group)].append(index)
    order = list(members)
    rng.shuffle(order)
    selected: list[int] = []
    deferred: list[str] = []
    for group in order:
        candidate = members[group]
        if len(selected) + len(candidate) <= target_n:
            selected.extend(candidate)
        else:
            deferred.append(group)
    if len(selected) < int(0.8 * target_n) and deferred:
        best = min(
            deferred,
            key=lambda group: abs(target_n - len(selected) - len(members[group])),
        )
        selected.extend(members[best])
    if len(selected) < 10:
        raise RuntimeError(f"Could only sample {len(selected)} grouped observations")
    return np.asarray(sorted(selected), dtype=int)


def load_frozen_input(input_path: Path, metadata_path: Path):
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    observed_input_hash = sha256_file(input_path)
    if observed_input_hash != metadata["input_sha256"]:
        raise AssertionError(
            f"Frozen input hash changed: {observed_input_hash} != {metadata['input_sha256']}"
        )
    with np.load(input_path, allow_pickle=False) as archive:
        arrays = {name: archive[name] for name in archive.files}
    for name, expected_hash in metadata["array_sha256"].items():
        observed_hash = sha256_array(arrays[name])
        if observed_hash != expected_hash:
            raise AssertionError(
                f"Frozen array hash changed for {name}: {observed_hash} != {expected_hash}"
            )
    required = {
        "row_index",
        "material_key",
        "value",
        "split",
        "group",
        "hard_ood_selected",
        "composition_features",
        "thermoelectric_prior",
        "alloy_control",
        "catalysis_control",
    }
    missing = required - set(arrays)
    if missing:
        raise AssertionError(f"Frozen input is missing arrays: {sorted(missing)}")
    row_count = len(arrays["row_index"])
    if row_count != metadata["rows"] or not np.array_equal(
        arrays["row_index"], np.arange(row_count)
    ):
        raise AssertionError("Frozen row identities are incomplete or reordered")
    if arrays["composition_features"].shape != (
        row_count,
        metadata["composition_feature_count"],
    ):
        raise AssertionError("Frozen composition feature shape changed")
    target = pd.DataFrame(
        {
            "material_key": arrays["material_key"].astype(str),
            "value": arrays["value"].astype(float),
            "split": arrays["split"].astype(str),
            "group": arrays["group"].astype(str),
            "hard_ood_selected": arrays["hard_ood_selected"].astype(bool),
        }
    )
    return metadata, arrays, target


def true_hit_set(target: pd.DataFrame, indices: list[int]) -> set[int]:
    ordered = target.loc[indices, ["material_key", "value"]].copy()
    ordered["index"] = ordered.index
    ordered = ordered.sort_values(
        ["value", "material_key"], ascending=[False, True], kind="mergesort"
    )
    count = max(1, math.ceil(0.05 * len(ordered)))
    return set(ordered.iloc[:count]["index"].astype(int))


def initial_indices(target: pd.DataFrame, seed: int, n: int) -> list[int]:
    train = target[target["split"] == "train"].reset_index()
    local = sample_groups(
        train["group"].tolist(), n, np.random.default_rng(RANDOM_SEED + seed)
    )
    return train.loc[local, "index"].astype(int).tolist()


def make_model(family: str, random_state: int):
    if family == "extra-trees-primary":
        return ExtraTreesRegressor(
            n_estimators=80,
            min_samples_leaf=2,
            max_features=0.7,
            random_state=random_state,
            n_jobs=1,
        )
    if family == "random-forest-sensitivity":
        return RandomForestRegressor(
            n_estimators=120,
            min_samples_leaf=2,
            max_features=0.7,
            random_state=random_state,
            n_jobs=1,
        )
    raise ValueError(family)


def campaign(
    *,
    target: pd.DataFrame,
    features: np.ndarray | None,
    candidate_indices: list[int],
    initial: list[int],
    hit_set: set[int],
    budget: int,
    seed: int,
    strategy: str,
    model_family: str,
) -> tuple[int, list[dict]]:
    pool = list(candidate_indices)
    labelled = list(initial)
    trajectory: list[dict] = []
    if strategy == "random_control":
        rng = np.random.default_rng(stable_seed(f"random:{seed}:{len(pool)}"))
        ordered = list(rng.permutation(pool))
        for step, chosen in enumerate(ordered[:budget], start=1):
            is_hit = chosen in hit_set
            trajectory.append(
                {
                    "step": step,
                    "chosen_index": chosen,
                    "chosen_key": target.at[chosen, "material_key"],
                    "chosen_y": target.at[chosen, "value"],
                    "is_true_top5_hit": is_hit,
                    "acquisition_mean": np.nan,
                    "acquisition_sd": np.nan,
                }
            )
            if is_hit:
                return step, trajectory
        return budget + 1, trajectory

    if features is None:
        raise ValueError("Model strategy requires features")
    y = target["value"].to_numpy(float)
    for step in range(1, budget + 1):
        random_state = stable_seed(f"{model_family}:{seed}:{step}")
        model = make_model(model_family, random_state).fit(
            features[labelled], y[labelled]
        )
        tree_predictions = np.asarray(
            [tree.predict(features[pool]) for tree in model.estimators_]
        )
        mean = tree_predictions.mean(axis=0)
        sd = tree_predictions.std(axis=0)
        acquisition = mean + sd
        # Stable identity tie-break after maximizing the acquisition score.
        best = np.flatnonzero(acquisition == acquisition.max())
        if len(best) > 1:
            position = min(best, key=lambda pos: target.at[pool[int(pos)], "material_key"])
        else:
            position = int(best[0])
        chosen = pool.pop(int(position))
        labelled.append(chosen)
        is_hit = chosen in hit_set
        trajectory.append(
            {
                "step": step,
                "chosen_index": chosen,
                "chosen_key": target.at[chosen, "material_key"],
                "chosen_y": y[chosen],
                "is_true_top5_hit": is_hit,
                "acquisition_mean": float(mean[position]),
                "acquisition_sd": float(sd[position]),
            }
        )
        if is_hit:
            return step, trajectory
    return budget + 1, trajectory


def run_seed_strategies(
    *,
    target: pd.DataFrame,
    feature_sets: dict[str, np.ndarray],
    candidates: list[int],
    hit_set: set[int],
    budget: int,
    initial_n: int,
    seed: int,
    scope: str,
    model_family: str,
    strategies: list[str],
) -> tuple[list[dict], list[dict]]:
    initial = initial_indices(target, seed, initial_n)
    reach_rows: list[dict] = []
    trajectory_rows: list[dict] = []
    for strategy in strategies:
        features = None if strategy == "random_control" else feature_sets[strategy]
        reach, trajectory = campaign(
            target=target,
            features=features,
            candidate_indices=candidates,
            initial=initial,
            hit_set=hit_set,
            budget=budget,
            seed=seed,
            strategy=strategy,
            model_family=model_family,
        )
        reach_rows.append(
            {
                "scope": scope,
                "model_family": model_family,
                "seed": seed,
                "strategy": strategy,
                "candidate_n": len(candidates),
                "true_hit_n": len(hit_set),
                "initial_target_n": len(initial),
                "budget": budget,
                "experiments_to_hit": reach,
                "censored": reach > budget,
            }
        )
        trajectory_rows.extend(
            {
                "scope": scope,
                "model_family": model_family,
                "seed": seed,
                "strategy": strategy,
                **row,
            }
            for row in trajectory
        )
    return reach_rows, trajectory_rows


def paired_inference(
    reaches: pd.DataFrame,
    *,
    scope: str,
    model_family: str,
    strategy: str,
    bootstrap_n: int,
    sign_flip_n: int,
) -> tuple[dict, pd.DataFrame]:
    local = reaches[
        (reaches["scope"] == scope) & (reaches["model_family"] == model_family)
    ]
    paired = local.pivot(index="seed", columns="strategy", values="experiments_to_hit")
    effect = (paired["target_only"] - paired[strategy]).to_numpy(float)
    rng = np.random.default_rng(stable_seed(f"boot:{scope}:{model_family}:{strategy}"))
    indices = rng.integers(0, len(effect), size=(bootstrap_n, len(effect)))
    bootstrap = effect[indices].mean(axis=1)
    observed = float(effect.mean())
    sign_rng = np.random.default_rng(stable_seed(f"sign:{scope}:{model_family}:{strategy}"))
    exceed = 0
    remaining = sign_flip_n
    while remaining:
        batch = min(1000, remaining)
        signs = sign_rng.choice((-1.0, 1.0), size=(batch, len(effect)))
        exceed += int(np.sum((signs * effect).mean(axis=1) >= observed))
        remaining -= batch
    p_value = (exceed + 1) / (sign_flip_n + 1)
    baseline_mean = float(paired["target_only"].mean())
    result = {
        "scope": scope,
        "model_family": model_family,
        "strategy": strategy,
        "seeds": len(effect),
        "target_only_mean_experiments": baseline_mean,
        "strategy_mean_experiments": float(paired[strategy].mean()),
        "target_only_median_experiments": float(paired["target_only"].median()),
        "strategy_median_experiments": float(paired[strategy].median()),
        "mean_experiments_saved": observed,
        "bootstrap_95": [float(x) for x in np.quantile(bootstrap, [0.025, 0.975])],
        "relative_mean_experiments_saved": observed / baseline_mean,
        "fraction_seeds_improved": float(np.mean(effect > 0)),
        "fraction_seeds_tied": float(np.mean(effect == 0)),
        "signflip_p_one_sided": float(p_value),
        "target_only_censor_fraction": float(np.mean(paired["target_only"] > local["budget"].iloc[0])),
        "strategy_censor_fraction": float(np.mean(paired[strategy] > local["budget"].iloc[0])),
    }
    boot = pd.DataFrame(
        {
            "scope": scope,
            "model_family": model_family,
            "strategy": strategy,
            "bootstrap": np.arange(bootstrap_n),
            "mean_experiments_saved": bootstrap,
        }
    )
    return result, boot


def core_gates(result: dict) -> dict[str, bool]:
    return {
        "p_le_0_05": bool(result["signflip_p_one_sided"] <= 0.05),
        "ci_lower_above_zero": bool(result["bootstrap_95"][0] > 0),
        "mean_saved_ge_5": bool(result["mean_experiments_saved"] >= 5),
        "relative_saved_ge_0_25": bool(
            result["relative_mean_experiments_saved"] >= 0.25
        ),
        "fraction_seed_improved_ge_0_60": bool(
            result["fraction_seeds_improved"] >= 0.60
        ),
    }


def main(
    *,
    input_path: Path = INPUT_PATH,
    input_metadata_path: Path = INPUT_META_PATH,
    validate_only: bool = False,
) -> None:
    design_bytes = DESIGN_PATH.read_bytes()
    design = json.loads(design_bytes)
    input_metadata, arrays, target = load_frozen_input(
        input_path, input_metadata_path
    )
    design_hash = hashlib.sha256(design_bytes).hexdigest()
    if input_metadata["design_sha256"] != design_hash:
        raise AssertionError(
            "Frozen input was not created against the current campaign design"
        )
    x = np.asarray(arrays["composition_features"], dtype=float)
    test_indices = target.index[target["split"] == "test"].astype(int).tolist()
    if len(test_indices) != 110:
        raise AssertionError(f"Expected 110 official-test candidates, found {len(test_indices)}")

    hard_indices = [
        index for index in test_indices if target.at[index, "hard_ood_selected"]
    ]
    if len(hard_indices) != 44:
        raise AssertionError(f"Expected 44 hard-OOD candidates, found {len(hard_indices)}")

    prior = {
        "thermoelectric_prior": np.asarray(arrays["thermoelectric_prior"]),
        "alloy_control": np.asarray(arrays["alloy_control"]),
        "catalysis_control": np.asarray(arrays["catalysis_control"]),
    }
    shuffle_rng = np.random.default_rng(20260714)
    prior["shuffled_thermoelectric_control"] = shuffle_rng.permutation(
        prior["thermoelectric_prior"]
    )
    feature_sets = {"target_only": x}
    feature_sets.update(
        {name: np.column_stack([x, values]) for name, values in prior.items()}
    )

    pool_by_scope = {"official_test": test_indices, "hard_ood_40pct": hard_indices}
    if validate_only:
        print(
            json.dumps(
                {
                    "status": "validated",
                    "input_sha256": input_metadata["input_sha256"],
                    "design_sha256": design_hash,
                    "rows": len(target),
                    "composition_features": int(x.shape[1]),
                    "candidate_pools": {
                        name: len(indices) for name, indices in pool_by_scope.items()
                    },
                    "source_target_exact_overlaps": input_metadata[
                        "source_target_exact_overlaps"
                    ],
                },
                indent=2,
            ),
            flush=True,
        )
        return

    primary_seeds = int(design["acquisition"]["primary_seeds"])
    sensitivity_seeds = int(design["acquisition"]["sensitivity_model"]["seeds"])
    budget = int(design["acquisition"]["budget"])
    initial_n = int(design["initial_labels"]["n"])
    strategies = [
        "target_only",
        "thermoelectric_prior",
        "alloy_control",
        "catalysis_control",
        "shuffled_thermoelectric_control",
        "random_control",
    ]

    reach_rows: list[dict] = []
    trajectory_rows: list[dict] = []
    model_runs = [
        ("extra-trees-primary", primary_seeds, strategies),
        (
            "random-forest-sensitivity",
            sensitivity_seeds,
            ["target_only", "thermoelectric_prior"],
        ),
    ]
    worker_count = max(1, int(os.environ.get("OOD_WORKERS", min(20, os.cpu_count() or 1))))
    batch_size = max(1, int(os.environ.get("OOD_BATCH_SIZE", worker_count)))
    checkpoint_namespace = (
        f"{design_hash[:12]}-{input_metadata['input_sha256'][:12]}"
    )
    checkpoint_root = (
        RESULTS / "obelix_ood_discovery_checkpoints" / checkpoint_namespace
    )
    checkpoint_root.mkdir(parents=True, exist_ok=True)
    print(
        f"Running frozen campaign with {worker_count} workers, batch size "
        f"{batch_size}, checkpoint {checkpoint_namespace}",
        flush=True,
    )
    for scope, candidates in pool_by_scope.items():
        hit_set = true_hit_set(target, candidates)
        for model_family, seed_n, model_strategies in model_runs:
            for start in range(0, seed_n, batch_size):
                stop = min(seed_n, start + batch_size)
                stem = f"{scope}__{model_family}__{start:04d}-{stop:04d}"
                reach_checkpoint = checkpoint_root / f"{stem}__reach.csv"
                trajectory_checkpoint = checkpoint_root / f"{stem}__trajectory.csv"
                if reach_checkpoint.exists() and trajectory_checkpoint.exists():
                    batch_reach_frame = pd.read_csv(reach_checkpoint)
                    batch_trajectory_frame = pd.read_csv(trajectory_checkpoint)
                    expected_rows = (stop - start) * len(model_strategies)
                    expected_seeds = set(range(start, stop))
                    if len(batch_reach_frame) != expected_rows or set(
                        batch_reach_frame["seed"].astype(int)
                    ) != expected_seeds:
                        raise AssertionError(
                            f"Incomplete or stale reach checkpoint: {reach_checkpoint}"
                        )
                    print(f"Resumed checkpoint {stem}", flush=True)
                else:
                    # Independent deterministic seeds are parallelized as
                    # separate processes; each tree ensemble stays single-threaded.
                    batch = Parallel(n_jobs=worker_count, backend="loky")(
                        delayed(run_seed_strategies)(
                            target=target,
                            feature_sets=feature_sets,
                            candidates=candidates,
                            hit_set=hit_set,
                            budget=budget,
                            initial_n=initial_n,
                            seed=seed,
                            scope=scope,
                            model_family=model_family,
                            strategies=model_strategies,
                        )
                        for seed in range(start, stop)
                    )
                    batch_reaches: list[dict] = []
                    batch_trajectories: list[dict] = []
                    for seed_reaches, seed_trajectories in batch:
                        batch_reaches.extend(seed_reaches)
                        batch_trajectories.extend(seed_trajectories)
                    batch_reach_frame = pd.DataFrame(batch_reaches)
                    batch_trajectory_frame = pd.DataFrame(batch_trajectories)
                    reach_temporary = reach_checkpoint.with_suffix(".csv.tmp")
                    trajectory_temporary = trajectory_checkpoint.with_suffix(
                        ".csv.tmp"
                    )
                    batch_reach_frame.to_csv(reach_temporary, index=False)
                    batch_trajectory_frame.to_csv(trajectory_temporary, index=False)
                    reach_temporary.replace(reach_checkpoint)
                    trajectory_temporary.replace(trajectory_checkpoint)
                reach_rows.extend(batch_reach_frame.to_dict("records"))
                trajectory_rows.extend(batch_trajectory_frame.to_dict("records"))
                print(
                    f"{scope} {model_family}: completed {stop}/{seed_n} seeds",
                    flush=True,
                )

    reaches = pd.DataFrame(reach_rows).sort_values(
        ["scope", "model_family", "seed", "strategy"], kind="mergesort"
    ).reset_index(drop=True)
    trajectories = pd.DataFrame(trajectory_rows).sort_values(
        ["scope", "model_family", "seed", "strategy", "step"], kind="mergesort"
    ).reset_index(drop=True)
    inference_rows: list[dict] = []
    boot_frames: list[pd.DataFrame] = []
    for scope in pool_by_scope:
        for model_family, _, model_strategies in model_runs:
            for strategy in model_strategies:
                if strategy == "target_only":
                    continue
                result, boot = paired_inference(
                    reaches,
                    scope=scope,
                    model_family=model_family,
                    strategy=strategy,
                    bootstrap_n=int(design["inference"]["bootstrap_replicates"]),
                    sign_flip_n=int(design["inference"]["sign_flip_draws"]),
                )
                result["core_gates"] = core_gates(result)
                result["passes_core_gates"] = bool(all(result["core_gates"].values()))
                inference_rows.append(result)
                boot_frames.append(boot)

    lookup = {
        (row["scope"], row["model_family"], row["strategy"]): row
        for row in inference_rows
    }
    primary = lookup[("official_test", "extra-trees-primary", "thermoelectric_prior")]
    sensitivity = lookup[
        ("official_test", "random-forest-sensitivity", "thermoelectric_prior")
    ]
    control_names = [
        "alloy_control",
        "catalysis_control",
        "shuffled_thermoelectric_control",
    ]
    controls_clean = not any(
        lookup[("official_test", "extra-trees-primary", name)]["passes_core_gates"]
        for name in control_names
    )
    primary["improvement_gates"] = {
        **primary["core_gates"],
        "random_forest_sensitivity_mean_positive": bool(
            sensitivity["mean_experiments_saved"] > 0
        ),
        "prespecified_prior_controls_clean": controls_clean,
    }
    improvement = bool(all(primary["improvement_gates"].values()))
    shortlist_n = math.ceil(0.10 * len(test_indices))
    crossing = bool(
        primary["target_only_median_experiments"] > shortlist_n
        and primary["strategy_median_experiments"] <= shortlist_n
    )
    primary["rescue_crossing"] = {
        "shortlist_n": shortlist_n,
        "target_only_median_above_shortlist": bool(
            primary["target_only_median_experiments"] > shortlist_n
        ),
        "prior_median_within_shortlist": bool(
            primary["strategy_median_experiments"] <= shortlist_n
        ),
    }
    primary["passes_improvement_gates"] = improvement
    primary["passes_rescue_crossing"] = crossing
    primary["decision_status"] = (
        "OOD-discovery-rescue"
        if improvement and crossing
        else "OOD-discovery-improvement"
        if improvement
        else "directional-only"
        if primary["mean_experiments_saved"] > 0
        else "unresolved-or-harmful"
    )

    reaches.to_csv(RESULTS / "obelix_ood_discovery_reach.csv", index=False)
    trajectories.to_csv(RESULTS / "obelix_ood_discovery_trajectories.csv", index=False)
    inference_frame = pd.DataFrame(inference_rows)
    for column in ("bootstrap_95", "core_gates", "improvement_gates", "rescue_crossing"):
        if column in inference_frame:
            inference_frame[column] = inference_frame[column].map(
                lambda value: json.dumps(value) if isinstance(value, (dict, list)) else value
            )
    inference_frame.to_csv(RESULTS / "obelix_ood_discovery_edges.csv", index=False)
    pd.concat(boot_frames, ignore_index=True).to_csv(
        RESULTS / "obelix_ood_discovery_bootstrap.csv", index=False
    )

    summary = {
        "analysis_status": "frozen-post-existing-results-official-test-OOD-sequential-discovery",
        "design_sha256": design_hash,
        "input_sha256": input_metadata["input_sha256"],
        "execution_checkpoint_namespace": checkpoint_namespace,
        "design_frozen_utc": design["frozen_utc"],
        "candidate_pools": {name: len(indices) for name, indices in pool_by_scope.items()},
        "source_target_exact_overlaps": input_metadata[
            "source_target_exact_overlaps"
        ],
        "primary_official_test_result": primary,
        "random_forest_sensitivity": sensitivity,
        "official_test_controls": {
            name: lookup[("official_test", "extra-trees-primary", name)]
            for name in [*control_names, "random_control"]
        },
        "hard_ood_secondary": {
            "thermoelectric_primary_model": lookup[
                ("hard_ood_40pct", "extra-trees-primary", "thermoelectric_prior")
            ],
            "thermoelectric_sensitivity_model": lookup[
                (
                    "hard_ood_40pct",
                    "random-forest-sensitivity",
                    "thermoelectric_prior",
                )
            ],
        },
        "claim_guard": design["claim_guard"],
    }
    (RESULTS / "obelix_ood_discovery_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=INPUT_PATH)
    parser.add_argument("--input-metadata", type=Path, default=INPUT_META_PATH)
    parser.add_argument("--validate-only", action="store_true")
    arguments = parser.parse_args()
    main(
        input_path=arguments.input,
        input_metadata_path=arguments.input_metadata,
        validate_only=arguments.validate_only,
    )
