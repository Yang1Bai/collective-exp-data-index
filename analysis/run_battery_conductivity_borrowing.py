"""Run the frozen conductivity-to-capacity OOD borrowing benchmark."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from scipy import sparse, stats
from sklearn.ensemble import ExtraTreesRegressor, RandomForestRegressor
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)


HERE = Path(__file__).resolve().parent
DESIGN_PATH = HERE / "battery_conductivity_borrowing_design.json"
IMPLEMENTATION_PATH = HERE / "battery_conductivity_implementation.json"
CARDS_PATH = HERE / "results" / "battery_conductivity_source_cards.csv"
SOURCE_SUMMARY_PATH = (
    HERE / "results" / "battery_conductivity_source_summary.json"
)
RESULTS = HERE / "results"

METHODS = [
    "recipient_only",
    "recipient_plus_real_conductivity",
    "recipient_plus_shuffled_conductivity",
    "recipient_plus_voltage_control",
    "recipient_plus_energy_control",
    "recipient_plus_gaussian_control",
]
SCOPES = [
    "supported_hard_ood_40pct",
    "source_supported_external",
    "full_external",
    "strict_early_cycle_external",
]
CONTRASTS = {
    "real_vs_recipient_only": (
        "recipient_plus_real_conductivity",
        "recipient_only",
    ),
    "real_vs_shuffled_conductivity": (
        "recipient_plus_real_conductivity",
        "recipient_plus_shuffled_conductivity",
    ),
    "real_vs_voltage_control": (
        "recipient_plus_real_conductivity",
        "recipient_plus_voltage_control",
    ),
    "real_vs_energy_control": (
        "recipient_plus_real_conductivity",
        "recipient_plus_energy_control",
    ),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_int(value: str) -> int:
    return int(hashlib.sha256(value.encode("utf-8")).hexdigest()[:8], 16)


def build_material_features(
    cards: pd.DataFrame, config: dict[str, Any]
) -> sparse.csr_matrix:
    representation = config["representation"]
    vectorizer = HashingVectorizer(
        analyzer=representation["analyzer"],
        ngram_range=tuple(representation["ngram_range"]),
        n_features=representation["n_features"],
        alternate_sign=representation["alternate_sign"],
        norm=representation["norm"],
        lowercase=True,
        dtype=np.float32,
    )
    return vectorizer.transform(cards["material_normalized"]).tocsr()


def build_state_features(cards: pd.DataFrame) -> sparse.csr_matrix:
    current = pd.to_numeric(
        cards["current_a_per_g"], errors="coerce"
    ).to_numpy(float)
    cycle = pd.to_numeric(
        cards["cycle_number"], errors="coerce"
    ).to_numpy(float)
    cycle_missing = ~np.isfinite(cycle)
    cycle_filled = np.where(cycle_missing, 0.0, np.maximum(cycle, 0.0))
    type_text = cards["Type"].fillna("").astype(str).str.lower()
    state = np.column_stack(
        [
            np.log10(np.maximum(current, 1e-12)),
            np.log1p(cycle_filled),
            cycle_missing.astype(float),
            type_text.str.contains("anode", regex=False).astype(float),
            type_text.str.contains("cathode", regex=False).astype(float),
            (
                ~type_text.str.contains("anode|cathode", regex=True)
            ).astype(float),
        ]
    ).astype(np.float32)
    return sparse.csr_matrix(state)


def card_block(cards: pd.DataFrame, prefix: str) -> sparse.csr_matrix:
    columns = [
        f"{prefix}_prediction",
        f"{prefix}_dispersion",
        f"{prefix}_support",
        f"{prefix}_missing",
    ]
    values = cards[columns].apply(
        pd.to_numeric, errors="coerce"
    ).to_numpy(np.float32)
    if not np.isfinite(values).all():
        raise RuntimeError(f"Nonfinite card block: {prefix}")
    return sparse.csr_matrix(values)


def learner(
    name: str, config: dict[str, Any], seed: int, n_estimators: int
) -> Any:
    benchmark = config["recipient_benchmark"]
    kwargs = {
        "n_estimators": n_estimators,
        "min_samples_leaf": benchmark["min_samples_leaf"],
        "max_features": benchmark["max_features"],
        "random_state": seed,
        "n_jobs": 1,
    }
    if name == "extra_trees":
        return ExtraTreesRegressor(**kwargs)
    if name == "random_forest":
        return RandomForestRegressor(**kwargs)
    raise KeyError(name)


def metric_row(
    y_true: np.ndarray,
    prediction: np.ndarray,
    base: dict[str, Any],
) -> dict[str, Any]:
    if len(y_true) < 2:
        return {
            **base,
            "n_eval": int(len(y_true)),
            "rmse": float("nan"),
            "mae": float("nan"),
            "r2": float("nan"),
            "spearman": float("nan"),
        }
    return {
        **base,
        "n_eval": int(len(y_true)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, prediction))),
        "mae": float(mean_absolute_error(y_true, prediction)),
        "r2": float(r2_score(y_true, prediction)),
        "spearman": float(stats.spearmanr(y_true, prediction).statistic),
    }


def target_similarity(
    material_features: sparse.csr_matrix,
    training_rows: np.ndarray,
    external_rows: np.ndarray,
) -> np.ndarray:
    similarities = material_features[external_rows] @ material_features[
        training_rows
    ].T
    if sparse.issparse(similarities):
        maximum = similarities.max(axis=1).toarray().ravel()
    else:
        maximum = np.asarray(similarities).max(axis=1)
    return np.clip(maximum, 0.0, 1.0)


def scope_masks(
    cards: pd.DataFrame,
    external_rows: np.ndarray,
    similarity: np.ndarray,
    support_threshold: float,
) -> dict[str, np.ndarray]:
    support = pd.to_numeric(
        cards.loc[external_rows, "conductivity_support"], errors="coerce"
    ).to_numpy(float)
    supported = np.isfinite(support) & (support >= support_threshold)
    hard = np.zeros(len(external_rows), dtype=bool)
    if supported.any():
        cutoff = float(np.quantile(similarity[supported], 0.4))
        hard = supported & (similarity <= cutoff)
    early = (
        cards.loc[external_rows, "is_early_cycle"]
        .astype(str)
        .str.lower()
        .isin(["true", "1"])
        .to_numpy()
    )
    return {
        "supported_hard_ood_40pct": hard,
        "source_supported_external": supported,
        "full_external": np.ones(len(external_rows), dtype=bool),
        "strict_early_cycle_external": early,
    }


def one_task(
    repeat: int,
    budget: int,
    learner_name: str,
    cards: pd.DataFrame,
    base_features: sparse.csr_matrix,
    material_features: sparse.csr_matrix,
    card_features: dict[str, sparse.csr_matrix],
    development_rows: np.ndarray,
    external_rows: np.ndarray,
    config: dict[str, Any],
    n_estimators: int,
    include_predictions: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    benchmark = config["recipient_benchmark"]
    seed = int(benchmark["seed_base"] + repeat * 101 + budget * 7)
    rng = np.random.default_rng(seed)
    if len(development_rows) < budget:
        raise RuntimeError(f"Label budget {budget} exceeds development pool")
    training_rows = np.sort(
        rng.choice(development_rows, size=budget, replace=False)
    )
    similarity = target_similarity(
        material_features, training_rows, external_rows
    )
    masks = scope_masks(
        cards,
        external_rows,
        similarity,
        config["source_cards"]["support_threshold"],
    )
    y = pd.to_numeric(
        cards["capacity_mAh_g"], errors="raise"
    ).to_numpy(float)
    y_train = np.log1p(y[training_rows])
    gaussian = sparse.csr_matrix(
        rng.normal(size=(len(cards), 4)).astype(np.float32)
    )
    method_blocks = {
        "recipient_only": None,
        "recipient_plus_real_conductivity": card_features["conductivity"],
        "recipient_plus_shuffled_conductivity": card_features[
            "shuffled_conductivity"
        ],
        "recipient_plus_voltage_control": card_features["voltage"],
        "recipient_plus_energy_control": card_features["energy"],
        "recipient_plus_gaussian_control": gaussian,
    }

    metrics: list[dict[str, Any]] = []
    predictions: list[dict[str, Any]] = []
    for method_index, method in enumerate(METHODS):
        block = method_blocks[method]
        features = (
            base_features
            if block is None
            else sparse.hstack([base_features, block], format="csr")
        )
        model = learner(
            learner_name,
            config,
            seed=seed + method_index * 1009,
            n_estimators=n_estimators,
        )
        model.fit(features[training_rows], y_train)
        prediction = np.expm1(model.predict(features[external_rows]))
        prediction = np.maximum(prediction, 0.0)
        for scope in SCOPES:
            mask = masks[scope]
            metrics.append(
                metric_row(
                    y[external_rows][mask],
                    prediction[mask],
                    {
                        "repeat": repeat,
                        "budget": budget,
                        "learner": learner_name,
                        "method": method,
                        "scope": scope,
                        "n_train": budget,
                    },
                )
            )
        if include_predictions:
            for local_index, row_index in enumerate(external_rows):
                predictions.append(
                    {
                        "repeat": repeat,
                        "budget": budget,
                        "learner": learner_name,
                        "method": method,
                        "target_id": cards.at[row_index, "target_id"],
                        "doi_normalized": cards.at[
                            row_index, "doi_normalized"
                        ],
                        "y_true": y[row_index],
                        "prediction": float(prediction[local_index]),
                        "supported_hard_ood_40pct": bool(
                            masks["supported_hard_ood_40pct"][local_index]
                        ),
                        "source_supported_external": bool(
                            masks["source_supported_external"][local_index]
                        ),
                        "full_external": True,
                        "strict_early_cycle_external": bool(
                            masks["strict_early_cycle_external"][local_index]
                        ),
                    }
                )
    return metrics, predictions


def paired_gain_table(
    metrics: pd.DataFrame,
    method: str,
    reference: str,
) -> pd.DataFrame:
    keys = ["repeat", "budget", "learner", "scope"]
    left = metrics.loc[
        metrics["method"].eq(method), keys + ["rmse", "r2"]
    ].rename(columns={"rmse": "method_rmse", "r2": "method_r2"})
    right = metrics.loc[
        metrics["method"].eq(reference), keys + ["rmse", "r2"]
    ].rename(columns={"rmse": "reference_rmse", "r2": "reference_r2"})
    paired = left.merge(right, on=keys, validate="one_to_one")
    paired["relative_rmse_gain"] = (
        paired["reference_rmse"] - paired["method_rmse"]
    ) / paired["reference_rmse"]
    paired["r2_gain"] = paired["method_r2"] - paired["reference_r2"]
    return paired


def doi_cluster_inference(
    predictions: pd.DataFrame,
    method: str,
    reference: str,
    scope: str,
    bootstrap_replicates: int,
    seed: int,
) -> tuple[float, float, float]:
    subset = predictions.loc[
        predictions["method"].isin([method, reference])
        & predictions[scope].astype(bool)
    ].copy()
    keys = [
        "repeat",
        "budget",
        "learner",
        "target_id",
        "doi_normalized",
        "y_true",
    ]
    pivot = subset.pivot_table(
        index=keys,
        columns="method",
        values="prediction",
        aggfunc="first",
    ).dropna()
    method_loss = np.square(
        pivot.index.get_level_values("y_true").to_numpy(float)
        - pivot[method].to_numpy(float)
    )
    reference_loss = np.square(
        pivot.index.get_level_values("y_true").to_numpy(float)
        - pivot[reference].to_numpy(float)
    )
    cluster = pd.DataFrame(
        {
            "doi": pivot.index.get_level_values("doi_normalized"),
            "method_loss": method_loss,
            "reference_loss": reference_loss,
        }
    ).groupby("doi", as_index=False).agg(
        method_loss=("method_loss", "mean"),
        reference_loss=("reference_loss", "mean"),
    )
    if len(cluster) < 5:
        return float("nan"), float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    method_values = cluster["method_loss"].to_numpy(float)
    reference_values = cluster["reference_loss"].to_numpy(float)
    samples = np.empty(bootstrap_replicates, dtype=float)
    for index in range(bootstrap_replicates):
        rows = rng.integers(0, len(cluster), size=len(cluster))
        samples[index] = 1.0 - math.sqrt(
            method_values[rows].mean() / reference_values[rows].mean()
        )
    ci_low, ci_high = np.quantile(samples, [0.025, 0.975])
    loss_difference = reference_values - method_values
    signs = rng.choice(
        np.array([-1.0, 1.0]),
        size=(bootstrap_replicates, len(cluster)),
        replace=True,
    )
    random_means = (signs * loss_difference).mean(axis=1)
    observed = float(loss_difference.mean())
    p_value = float(
        (1 + np.count_nonzero(np.abs(random_means) >= abs(observed)))
        / (bootstrap_replicates + 1)
    )
    return float(ci_low), float(ci_high), p_value


def holm_adjust(p_values: list[float]) -> list[float]:
    values = np.asarray(p_values, dtype=float)
    order = np.argsort(values)
    adjusted = np.empty_like(values)
    running = 0.0
    total = len(values)
    for rank, index in enumerate(order):
        candidate = (total - rank) * values[index]
        running = max(running, candidate)
        adjusted[index] = min(1.0, running)
    return adjusted.tolist()


def make_contrasts(
    metrics: pd.DataFrame,
    predictions: pd.DataFrame,
    config: dict[str, Any],
) -> pd.DataFrame:
    benchmark = config["recipient_benchmark"]
    primary_budget = benchmark["primary_label_budget"]
    bootstrap_replicates = config["inference"]["bootstrap_replicates"]
    rows = []
    for learner_name in sorted(metrics["learner"].unique()):
        for scope in SCOPES:
            family_rows = []
            for contrast_index, (
                contrast_name,
                (method, reference),
            ) in enumerate(CONTRASTS.items()):
                paired = paired_gain_table(metrics, method, reference)
                selected = paired.loc[
                    paired["budget"].eq(primary_budget)
                    & paired["learner"].eq(learner_name)
                    & paired["scope"].eq(scope)
                ]
                ci_low, ci_high, p_value = doi_cluster_inference(
                    predictions.loc[
                        predictions["budget"].eq(primary_budget)
                        & predictions["learner"].eq(learner_name)
                    ],
                    method,
                    reference,
                    scope,
                    bootstrap_replicates,
                    seed=2026072790 + contrast_index,
                )
                family_rows.append(
                    {
                        "contrast": contrast_name,
                        "method": method,
                        "reference": reference,
                        "budget": primary_budget,
                        "learner": learner_name,
                        "scope": scope,
                        "repeats": int(len(selected)),
                        "mean_relative_rmse_gain": float(
                            selected["relative_rmse_gain"].mean()
                        ),
                        "median_relative_rmse_gain": float(
                            selected["relative_rmse_gain"].median()
                        ),
                        "positive_repeat_fraction": float(
                            (selected["relative_rmse_gain"] > 0).mean()
                        ),
                        "mean_r2_gain": float(selected["r2_gain"].mean()),
                        "cluster_ci95_low": ci_low,
                        "cluster_ci95_high": ci_high,
                        "cluster_randomization_p": p_value,
                    }
                )
            adjusted = holm_adjust(
                [row["cluster_randomization_p"] for row in family_rows]
            )
            for row, adjusted_p in zip(family_rows, adjusted):
                row["holm_p"] = adjusted_p
                rows.append(row)
    return pd.DataFrame(rows)


def success_gate(
    metrics: pd.DataFrame,
    contrasts: pd.DataFrame,
    config: dict[str, Any],
    design: dict[str, Any],
) -> dict[str, Any]:
    primary_budget = config["recipient_benchmark"]["primary_label_budget"]
    primary_learner = "extra_trees"
    primary_scope = "supported_hard_ood_40pct"
    selected = contrasts.loc[
        contrasts["budget"].eq(primary_budget)
        & contrasts["learner"].eq(primary_learner)
        & contrasts["scope"].eq(primary_scope)
    ].set_index("contrast")
    real = selected.loc["real_vs_recipient_only"]
    shuffled = selected.loc["real_vs_shuffled_conductivity"]
    voltage = selected.loc["real_vs_voltage_control"]
    energy = selected.loc["real_vs_energy_control"]
    real_metrics = metrics.loc[
        metrics["budget"].eq(primary_budget)
        & metrics["learner"].eq(primary_learner)
        & metrics["scope"].eq(primary_scope)
        & metrics["method"].eq("recipient_plus_real_conductivity")
    ]
    full_real = metrics.loc[
        metrics["budget"].eq(primary_budget)
        & metrics["learner"].eq(primary_learner)
        & metrics["scope"].eq("full_external")
        & metrics["method"].eq("recipient_plus_real_conductivity")
    ]
    full_base = metrics.loc[
        metrics["budget"].eq(primary_budget)
        & metrics["learner"].eq(primary_learner)
        & metrics["scope"].eq("full_external")
        & metrics["method"].eq("recipient_only")
    ]
    full_gain = float(
        (
            full_base["rmse"].to_numpy()
            - full_real["rmse"].to_numpy()
        ).mean()
        / full_base["rmse"].mean()
    )
    gate = design["inference"]["success_gate"]
    checks = {
        "minimum_mean_relative_rmse_gain": (
            real["mean_relative_rmse_gain"]
            >= gate["minimum_mean_relative_rmse_gain"]
        ),
        "cluster_ci_lower_positive": real["cluster_ci95_low"] > 0,
        "holm_p_below": real["holm_p"] < gate["holm_p_below"],
        "absolute_r2_positive": real_metrics["r2"].mean() > 0,
        "minimum_gain_over_shuffled_source": (
            shuffled["mean_relative_rmse_gain"]
            >= gate["minimum_gain_over_shuffled_source"]
        ),
        "better_than_voltage_control": (
            voltage["mean_relative_rmse_gain"] > 0
        ),
        "better_than_energy_control": (
            energy["mean_relative_rmse_gain"] > 0
        ),
        "positive_repeat_fraction": (
            real["positive_repeat_fraction"]
            >= gate["positive_repeat_fraction_at_least"]
        ),
        "no_full_external_harm": (
            full_gain >= -gate["maximum_full_external_rmse_harm"]
        ),
    }
    return {
        "passed": bool(all(checks.values())),
        "checks": {key: bool(value) for key, value in checks.items()},
        "primary_mean_relative_rmse_gain": float(
            real["mean_relative_rmse_gain"]
        ),
        "primary_cluster_ci95": [
            float(real["cluster_ci95_low"]),
            float(real["cluster_ci95_high"]),
        ],
        "primary_holm_p": float(real["holm_p"]),
        "primary_mean_absolute_r2": float(real_metrics["r2"].mean()),
        "full_external_mean_relative_rmse_gain": full_gain,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cards", type=Path, default=CARDS_PATH)
    parser.add_argument("--source-summary", type=Path, default=SOURCE_SUMMARY_PATH)
    parser.add_argument("--workers", type=int, default=max(1, os.cpu_count() or 1))
    parser.add_argument("--repeats", type=int)
    parser.add_argument("--n-estimators", type=int)
    parser.add_argument("--budgets", type=int, nargs="+")
    parser.add_argument("--learners", nargs="+")
    parser.add_argument("--metrics-output", type=Path, default=RESULTS / "battery_conductivity_metrics.csv")
    parser.add_argument("--predictions-output", type=Path, default=RESULTS / "battery_conductivity_primary_predictions.csv.gz")
    parser.add_argument("--contrasts-output", type=Path, default=RESULTS / "battery_conductivity_contrasts.csv")
    parser.add_argument("--summary-output", type=Path, default=RESULTS / "battery_conductivity_formal_summary.json")
    parser.add_argument("--complete-output", type=Path, default=RESULTS / "battery_conductivity_complete.json")
    args = parser.parse_args()

    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    config = json.loads(IMPLEMENTATION_PATH.read_text(encoding="utf-8"))
    source_summary = json.loads(args.source_summary.read_text(encoding="utf-8"))
    if source_summary["status"] != "source-card-gate-passed":
        raise RuntimeError("Conductivity source card failed its frozen skill gate")
    if source_summary["cards_sha256"] != sha256(args.cards):
        raise RuntimeError("Source cards changed after source-only gate")
    benchmark = config["recipient_benchmark"]
    repeats = args.repeats or benchmark["repeats"]
    n_estimators = args.n_estimators or benchmark["n_estimators"]
    budgets = args.budgets or benchmark["label_budgets"]
    learners = args.learners or benchmark["learners"]

    cards = pd.read_csv(args.cards, low_memory=False, keep_default_na=False)
    material_features = build_material_features(cards, config)
    state_features = build_state_features(cards)
    base_features = sparse.hstack(
        [material_features, state_features], format="csr"
    )
    card_features = {
        prefix: card_block(cards, prefix)
        for prefix in [
            "conductivity",
            "shuffled_conductivity",
            "voltage",
            "energy",
        ]
    }
    folds = np.array(
        [
            stable_int(str(value))
            % benchmark["external_publication_modulus"]
            for value in cards["doi_normalized"]
        ]
    )
    external_rows = np.flatnonzero(
        folds == benchmark["external_publication_remainder"]
    )
    development_rows = np.flatnonzero(
        folds != benchmark["external_publication_remainder"]
    )
    primary_budget = benchmark["primary_label_budget"]
    jobs = [
        (repeat, budget, learner_name)
        for repeat in range(repeats)
        for budget in budgets
        for learner_name in learners
    ]
    outputs = Parallel(n_jobs=args.workers, verbose=10)(
        delayed(one_task)(
            repeat,
            budget,
            learner_name,
            cards,
            base_features,
            material_features,
            card_features,
            development_rows,
            external_rows,
            config,
            n_estimators,
            include_predictions=(budget == primary_budget),
        )
        for repeat, budget, learner_name in jobs
    )
    metric_rows = [row for metrics, _ in outputs for row in metrics]
    prediction_rows = [
        row for _, predictions in outputs for row in predictions
    ]
    metrics = pd.DataFrame(metric_rows)
    predictions = pd.DataFrame(prediction_rows)
    args.metrics_output.parent.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(args.metrics_output, index=False)
    predictions.to_csv(
        args.predictions_output, index=False, compression="gzip"
    )
    contrasts = make_contrasts(metrics, predictions, config)
    contrasts.to_csv(args.contrasts_output, index=False)
    gate = success_gate(metrics, contrasts, config, design)

    summary = {
        "status": "formal-benchmark-complete",
        "design_sha256": sha256(DESIGN_PATH),
        "implementation_sha256": sha256(IMPLEMENTATION_PATH),
        "cards_sha256": sha256(args.cards),
        "source_summary_sha256": sha256(args.source_summary),
        "cards_rows": int(len(cards)),
        "development_rows": int(len(development_rows)),
        "external_rows": int(len(external_rows)),
        "repeats": repeats,
        "budgets": budgets,
        "learners": learners,
        "n_estimators": n_estimators,
        "metric_rows": int(len(metrics)),
        "prediction_rows": int(len(predictions)),
        "contrasts": int(len(contrasts)),
        "formal_success_gate": gate,
        "claim_guard": config["claim_guard"],
    }
    args.summary_output.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    complete = {
        **summary,
        "metrics_sha256": sha256(args.metrics_output),
        "predictions_sha256": sha256(args.predictions_output),
        "contrasts_sha256": sha256(args.contrasts_output),
        "summary_sha256": sha256(args.summary_output),
    }
    args.complete_output.write_text(
        json.dumps(complete, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(complete, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
