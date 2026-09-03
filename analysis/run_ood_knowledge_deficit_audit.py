"""Quantify target-only OOD degradation and localize frozen source effects.

This is a post-outcome diagnostic. It cannot revise the completed OBELiX
screening or sequential-acquisition decisions.
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
from scipy.stats import spearmanr
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from run_obelix_ood_discovery import load_frozen_input, make_model, sample_groups


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis"
RESULTS = ANALYSIS / "results"
DESIGN_PATH = ANALYSIS / "ood_knowledge_deficit_design.json"
INPUT_PATH = RESULTS / "obelix_ood_discovery_input.npz"
INPUT_META_PATH = RESULTS / "obelix_ood_discovery_input_meta.json"
RANDOM_SEED = 20260718


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_seed(label: str) -> int:
    return int(hashlib.sha256(label.encode("utf-8")).hexdigest()[:8], 16)


def nearest_distance(test_x: np.ndarray, train_x: np.ndarray) -> np.ndarray:
    distances = np.full(len(test_x), np.inf, dtype=float)
    for start in range(0, len(train_x), 64):
        block = train_x[start : start + 64]
        squared = np.sum((test_x[:, None, :] - block[None, :, :]) ** 2, axis=2)
        distances = np.minimum(distances, np.sqrt(np.min(squared, axis=1)))
    return distances


def distance_quartiles(distance: np.ndarray) -> np.ndarray:
    order = np.argsort(distance, kind="mergesort")
    quartile = np.empty(len(distance), dtype=int)
    for rank, index in enumerate(order):
        quartile[index] = min(4, 1 + math.floor(4 * rank / len(distance)))
    return quartile


def safe_spearman(left: np.ndarray, right: np.ndarray) -> float:
    if len(left) < 3 or np.std(left) == 0 or np.std(right) == 0:
        return float("nan")
    return float(spearmanr(left, right).statistic)


def metric_row(
    *,
    repeat: int,
    requested_budget: int,
    budget: int,
    learner: str,
    source: str,
    scope: str,
    y: np.ndarray,
    prediction: np.ndarray,
) -> dict:
    return {
        "repeat": repeat,
        "requested_budget": requested_budget,
        "budget": budget,
        "learner": learner,
        "source": source,
        "scope": scope,
        "n": int(len(y)),
        "rmse": float(mean_squared_error(y, prediction) ** 0.5),
        "mae": float(mean_absolute_error(y, prediction)),
        "r2": float(r2_score(y, prediction)) if len(y) >= 2 else float("nan"),
        "spearman": safe_spearman(y, prediction),
    }


def one_task(
    *,
    repeat: int,
    budget: int,
    learner: str,
    target: pd.DataFrame,
    arrays: dict[str, np.ndarray],
    standardized_x: np.ndarray,
) -> tuple[list[dict], dict]:
    train_pool = np.flatnonzero(target["split"].to_numpy() == "train")
    test_indices = np.flatnonzero(target["split"].to_numpy() == "test")
    local = sample_groups(
        target.loc[train_pool, "group"].astype(str).tolist(),
        budget,
        np.random.default_rng(stable_seed(f"sample:{repeat}:{budget}")),
    )
    train_indices = train_pool[local]
    x_train = arrays["composition_features"][train_indices]
    x_test = arrays["composition_features"][test_indices]
    y_train = target.loc[train_indices, "value"].to_numpy(float)
    y_test = target.loc[test_indices, "value"].to_numpy(float)

    distance = nearest_distance(
        standardized_x[test_indices], standardized_x[train_indices]
    )
    quartile = distance_quartiles(distance)
    hard_ood = target.loc[test_indices, "hard_ood_selected"].to_numpy(bool)

    source_features: dict[str, np.ndarray | None] = {
        "target_only": None,
        "thermoelectric_neighbor": arrays["thermoelectric_prior"],
        "alloy_control": arrays["alloy_control"],
        "catalysis_control": arrays["catalysis_control"],
    }
    shuffled = arrays["thermoelectric_prior"].copy()
    rng = np.random.default_rng(stable_seed(f"shuffle:{repeat}:{budget}"))
    shuffled = shuffled[rng.permutation(len(shuffled))]
    source_features["shuffled_thermoelectric"] = shuffled

    metrics: list[dict] = []
    baseline_prediction: np.ndarray | None = None
    for source, feature in source_features.items():
        if feature is None:
            model_train = x_train
            model_test = x_test
        else:
            model_train = np.column_stack([x_train, feature[train_indices]])
            model_test = np.column_stack([x_test, feature[test_indices]])
        model = make_model(
            learner,
            stable_seed(f"model:{repeat}:{budget}:{learner}:{source}"),
        )
        model.fit(model_train, y_train)
        prediction = model.predict(model_test)
        if source == "target_only":
            baseline_prediction = prediction

        masks: dict[str, np.ndarray] = {
            "all": np.ones(len(test_indices), dtype=bool),
            "hard_ood_fixed": hard_ood,
        }
        masks.update({f"ood_q{q}": quartile == q for q in range(1, 5)})
        for scope, mask in masks.items():
            if int(mask.sum()) < 2:
                continue
            metrics.append(
                metric_row(
                    repeat=repeat,
                    requested_budget=budget,
                    budget=len(train_indices),
                    learner=learner,
                    source=source,
                    scope=scope,
                    y=y_test[mask],
                    prediction=prediction[mask],
                )
            )

    if baseline_prediction is None:
        raise AssertionError("Target-only prediction was not generated")
    diagnostic = {
        "repeat": repeat,
        "requested_budget": budget,
        "budget": int(len(train_indices)),
        "learner": learner,
        "error_distance_spearman": safe_spearman(
            np.abs(y_test - baseline_prediction), distance
        ),
        "distance_mean": float(np.mean(distance)),
        "distance_q25": float(np.quantile(distance, 0.25)),
        "distance_q75": float(np.quantile(distance, 0.75)),
    }
    return metrics, diagnostic


def paired_contrasts(metrics: pd.DataFrame) -> pd.DataFrame:
    keys = ["repeat", "requested_budget", "budget", "learner", "scope"]
    baseline = metrics[metrics["source"] == "target_only"][keys + ["rmse"]].rename(
        columns={"rmse": "baseline_rmse"}
    )
    augmented = metrics[metrics["source"] != "target_only"].copy()
    merged = augmented.merge(baseline, on=keys, how="left", validate="many_to_one")
    merged["relative_rmse_reduction"] = (
        merged["baseline_rmse"] - merged["rmse"]
    ) / merged["baseline_rmse"]
    return merged[
        keys
        + [
            "source",
            "baseline_rmse",
            "rmse",
            "relative_rmse_reduction",
            "r2",
            "mae",
            "spearman",
            "n",
        ]
    ]


def bootstrap_mean(values: np.ndarray, rng: np.random.Generator, n_boot: int) -> dict:
    clean = np.asarray(values, dtype=float)
    clean = clean[np.isfinite(clean)]
    if len(clean) == 0:
        return {"mean": None, "ci_low": None, "ci_high": None, "n": 0}
    draws = rng.choice(clean, size=(n_boot, len(clean)), replace=True).mean(axis=1)
    return {
        "mean": float(np.mean(clean)),
        "ci_low": float(np.quantile(draws, 0.025)),
        "ci_high": float(np.quantile(draws, 0.975)),
        "n": int(len(clean)),
    }


def build_summary(
    *,
    design: dict,
    input_metadata: dict,
    metrics: pd.DataFrame,
    diagnostics: pd.DataFrame,
    contrasts: pd.DataFrame,
    repeats: int,
) -> dict:
    primary_budget = int(design["primary_budget"])
    learner = "extra-trees-primary"
    rng = np.random.default_rng(RANDOM_SEED)
    n_boot = int(design["inference"]["bootstrap_replicates"])

    primary_metrics = metrics[
        (metrics["requested_budget"] == primary_budget)
        & (metrics["learner"] == learner)
        & (metrics["source"] == "target_only")
    ]
    pivot = primary_metrics.pivot_table(
        index="repeat", columns="scope", values="rmse", aggfunc="first"
    ).dropna(subset=["ood_q1", "ood_q4"])
    ood_gap = pivot["ood_q4"].to_numpy() - pivot["ood_q1"].to_numpy()
    primary_diagnostics = diagnostics[
        (diagnostics["requested_budget"] == primary_budget)
        & (diagnostics["learner"] == learner)
    ]
    high_ood = contrasts[
        (contrasts["requested_budget"] == primary_budget)
        & (contrasts["learner"] == learner)
        & (contrasts["scope"] == "ood_q4")
    ]
    source_pivot = high_ood.pivot_table(
        index="repeat",
        columns="source",
        values="relative_rmse_reduction",
        aggfunc="first",
    )
    control_columns = [
        "alloy_control",
        "catalysis_control",
        "shuffled_thermoelectric",
    ]
    specificity = (
        source_pivot["thermoelectric_neighbor"]
        - source_pivot[control_columns].max(axis=1)
    ).to_numpy()

    aggregated = (
        metrics.groupby(
            ["requested_budget", "learner", "source", "scope"], as_index=False
        )
        .agg(
            repeats=("repeat", "nunique"),
            mean_rmse=("rmse", "mean"),
            mean_mae=("mae", "mean"),
            mean_r2=("r2", "mean"),
            mean_spearman=("spearman", "mean"),
        )
        .to_dict(orient="records")
    )
    return {
        "status": (
            "post-outcome-diagnostic-complete"
            if repeats == int(design["repeats"])
            else "smoke-diagnostic"
        ),
        "claim_guard": design["claim_guard"],
        "design_sha256": sha256_file(DESIGN_PATH),
        "input_sha256": input_metadata["input_sha256"],
        "repeats": repeats,
        "label_budgets": design["label_budgets"],
        "primary": {
            "target_only_high_minus_low_ood_rmse": bootstrap_mean(
                ood_gap, rng, n_boot
            ),
            "target_only_abs_error_distance_spearman": bootstrap_mean(
                primary_diagnostics["error_distance_spearman"].to_numpy(),
                rng,
                n_boot,
            ),
            "thermoelectric_high_ood_relative_rmse_reduction": bootstrap_mean(
                source_pivot["thermoelectric_neighbor"].to_numpy(), rng, n_boot
            ),
            "thermoelectric_minus_best_control_high_ood": bootstrap_mean(
                specificity, rng, n_boot
            ),
        },
        "aggregated_metrics": aggregated,
        "metric_rows": int(len(metrics)),
        "contrast_rows": int(len(contrasts)),
        "diagnostic_rows": int(len(diagnostics)),
        "inference_warning": design["inference"]["warning"],
    }


def validate_design(design: dict, metadata: dict, arrays: dict, target: pd.DataFrame) -> None:
    if metadata["input_sha256"] != sha256_file(INPUT_PATH):
        raise AssertionError("Frozen input hash mismatch")
    if set(target["split"]) != {"train", "test"}:
        raise AssertionError("Unexpected split labels")
    train_groups = set(target.loc[target["split"] == "train", "group"])
    test_groups = set(target.loc[target["split"] == "test", "group"])
    if train_groups & test_groups:
        raise AssertionError("Official train/test groups overlap")
    if arrays["composition_features"].shape[1] != metadata["composition_feature_count"]:
        raise AssertionError("Composition feature count changed")
    if sorted(design["label_budgets"]) != design["label_budgets"]:
        raise AssertionError("Label budgets must be sorted")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=None)
    parser.add_argument("--workers", type=int, default=int(os.environ.get("OOD_WORKERS", "1")))
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--output-prefix", default="ood_knowledge_deficit")
    args = parser.parse_args()

    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    metadata, arrays, target = load_frozen_input(INPUT_PATH, INPUT_META_PATH)
    validate_design(design, metadata, arrays, target)
    if args.validate_only:
        print(
            json.dumps(
                {
                    "status": "validated",
                    "design_sha256": sha256_file(DESIGN_PATH),
                    "input_sha256": metadata["input_sha256"],
                    "train": int((target["split"] == "train").sum()),
                    "test": int((target["split"] == "test").sum()),
                },
                indent=2,
            )
        )
        return

    repeats = int(args.repeats or design["repeats"])
    if repeats < 1 or repeats > int(design["repeats"]):
        raise ValueError("repeats must be between 1 and the frozen formal count")
    x = arrays["composition_features"].astype(float)
    train_mask = target["split"].to_numpy() == "train"
    mean = x[train_mask].mean(axis=0)
    scale = x[train_mask].std(axis=0)
    scale[scale == 0] = 1.0
    standardized_x = (x - mean) / scale

    tasks = [
        (repeat, budget, learner)
        for repeat in range(repeats)
        for budget in design["label_budgets"]
        for learner in design["learners"]
    ]
    outputs = Parallel(n_jobs=args.workers, verbose=10)(
        delayed(one_task)(
            repeat=repeat,
            budget=budget,
            learner=learner,
            target=target,
            arrays=arrays,
            standardized_x=standardized_x,
        )
        for repeat, budget, learner in tasks
    )
    metric_records = [row for metric_rows, _ in outputs for row in metric_rows]
    diagnostic_records = [row for _, row in outputs]
    metrics = pd.DataFrame(metric_records).sort_values(
        ["requested_budget", "learner", "source", "scope", "repeat"]
    )
    diagnostics = pd.DataFrame(diagnostic_records).sort_values(
        ["requested_budget", "learner", "repeat"]
    )
    contrasts = paired_contrasts(metrics).sort_values(
        ["requested_budget", "learner", "source", "scope", "repeat"]
    )
    summary = build_summary(
        design=design,
        input_metadata=metadata,
        metrics=metrics,
        diagnostics=diagnostics,
        contrasts=contrasts,
        repeats=repeats,
    )

    RESULTS.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(RESULTS / f"{args.output_prefix}_metrics.csv", index=False)
    diagnostics.to_csv(
        RESULTS / f"{args.output_prefix}_diagnostics.csv", index=False
    )
    contrasts.to_csv(RESULTS / f"{args.output_prefix}_contrasts.csv", index=False)
    (RESULTS / f"{args.output_prefix}_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary["primary"], indent=2))


if __name__ == "__main__":
    main()
