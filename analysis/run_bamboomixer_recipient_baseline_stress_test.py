"""Stress-test donor ranking against a broad recipient-only baseline family."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor, RandomForestRegressor
from sklearn.kernel_ridge import KernelRidge
from sklearn.linear_model import Ridge
from sklearn.metrics import pairwise_distances
from sklearn.neighbors import KNeighborsRegressor

from common import RESULTS
from electrolyte_programme_interaction_common import (
    exact_formulation_signature,
    load_solventseg,
    percentile_rank,
    sha256,
)
from mixture_response_transfer_common import (
    maximin_anchors,
    mixture_features,
    nonanchor_test_indices,
    response_target,
    stable_seed,
)
from run_bamboomixer_cross_database_interaction import (
    compact_target_space,
    rank_metrics,
)


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DESIGN = HERE / "bamboomixer_cross_database_interaction_design.json"
PREDICTIONS = (
    RESULTS
    / "bamboomixer_cross_database_interaction_solventseg_predictions.csv"
)
OUTPUT = (
    RESULTS
    / "bamboomixer_recipient_baseline_stress_test_metrics.csv"
)
SUMMARY = (
    RESULTS
    / "bamboomixer_recipient_baseline_stress_test_summary.json"
)


def resolve(raw: str) -> Path:
    path = Path(raw).expanduser()
    return path if path.is_absolute() else ROOT / path


def quantiles(values: pd.Series) -> list[float]:
    return [
        float(values.quantile(0.025)),
        float(values.quantile(0.975)),
    ]


def main() -> None:
    design = json.loads(DESIGN.read_text(encoding="utf-8"))
    solvent_path = resolve(design["inputs"]["solventseg"]["path"])
    if sha256(solvent_path) != design["inputs"]["solventseg"]["sha256"]:
        raise AssertionError("SolventSeg input changed")
    records, frame = load_solventseg(solvent_path)
    x = mixture_features(records)
    y = response_target(records)
    fixed = np.flatnonzero(
        np.isclose(frame["temperature_C"].to_numpy(float), 25.0)
    )
    x = x[fixed]
    y = y[fixed]
    groups = np.asarray(
        [exact_formulation_signature(records[index]) for index in fixed]
    )
    compact = compact_target_space(x)
    distances = pairwise_distances(compact)
    nonzero = distances[distances > 1e-12]
    gamma = float(1.0 / np.median(nonzero) ** 2)
    stored = pd.read_csv(PREDICTIONS)
    stored = stored[
        np.isclose(stored["temperature_C"].to_numpy(float), 25.0)
    ].reset_index(drop=True)
    source_score = stored[
        "prediction_programme_balanced_portfolio"
    ].to_numpy(float)
    if not np.allclose(stored["truth_log10"], y, rtol=1e-12, atol=1e-12):
        raise AssertionError("Stored SolventSeg row order changed")

    rows = []
    for budget in (3, 5, 10):
        for draw in range(100):
            anchors = maximin_anchors(
                compact,
                groups,
                budget=budget,
                start_index=stable_seed(
                    "solventseg-anchor",
                    budget,
                    draw,
                ),
            )
            test = nonanchor_test_indices(groups, anchors)
            models = {}
            for alpha in (0.1, 1.0, 10.0, 100.0):
                models[f"ridge_alpha_{alpha:g}"] = Ridge(alpha=alpha)
            for alpha in (0.1, 1.0, 10.0):
                models[f"rbf_kernel_ridge_alpha_{alpha:g}"] = KernelRidge(
                    alpha=alpha,
                    kernel="rbf",
                    gamma=gamma,
                )
            for neighbours in (1, 3, 5):
                models[f"knn_{neighbours}"] = KNeighborsRegressor(
                    n_neighbors=min(neighbours, len(anchors)),
                    weights="distance",
                )
            models["random_forest"] = RandomForestRegressor(
                n_estimators=300,
                min_samples_leaf=1,
                max_features=0.7,
                random_state=stable_seed(
                    "recipient-rf",
                    budget,
                    draw,
                ),
                n_jobs=1,
            )
            models["extra_trees"] = ExtraTreesRegressor(
                n_estimators=300,
                min_samples_leaf=1,
                max_features=0.7,
                random_state=stable_seed(
                    "recipient-et",
                    budget,
                    draw,
                ),
                n_jobs=1,
            )
            predictions = {}
            for name, model in models.items():
                model.fit(compact[anchors], y[anchors])
                predictions[name] = np.asarray(
                    model.predict(compact[test]),
                    dtype=float,
                )
            predictions["recipient_rank_ensemble"] = np.mean(
                np.vstack(
                    [
                        percentile_rank(prediction)
                        for prediction in predictions.values()
                    ]
                ),
                axis=0,
            )
            predictions[
                "programme_balanced_source_portfolio"
            ] = source_score[test]
            for name, prediction in predictions.items():
                rows.append(
                    {
                        "anchor_budget": budget,
                        "draw": draw,
                        "model": name,
                        "n_anchor_formulations": len(anchors),
                        "n_test_formulations": len(test),
                        **rank_metrics(y[test], prediction),
                    }
                )
    metrics = pd.DataFrame(rows)
    metrics.to_csv(OUTPUT, index=False)
    primary = metrics[metrics["anchor_budget"].eq(5)]
    source = primary[
        primary["model"].eq("programme_balanced_source_portfolio")
    ].set_index("draw")
    recipient = primary[
        ~primary["model"].eq("programme_balanced_source_portfolio")
    ]
    macro = (
        recipient.groupby("model")[
            ["spearman", "top_quartile_precision", "normalized_regret"]
        ]
        .mean()
        .sort_values("spearman", ascending=False)
    )
    strongest = str(macro.index[0])
    strongest_draw = recipient[
        recipient["model"].eq(strongest)
    ].set_index("draw")
    spearman_difference = (
        source["spearman"] - strongest_draw["spearman"]
    )
    oracle = (
        recipient.groupby("draw")
        .agg(
            spearman=("spearman", "max"),
            top_quartile_precision=("top_quartile_precision", "max"),
            normalized_regret=("normalized_regret", "min"),
        )
    )
    oracle_spearman_difference = source["spearman"] - oracle["spearman"]
    decision = bool(
        float(source["spearman"].mean()) > float(macro["spearman"].max())
        and quantiles(spearman_difference)[0] > 0
        and float(oracle_spearman_difference.mean()) >= -0.05
    )
    summary = {
        "status": "complete-post-outcome-recipient-baseline-stress-test",
        "design_sha256": sha256(DESIGN),
        "predictions_sha256": sha256(PREDICTIONS),
        "rows": len(metrics),
        "anchor_budgets": [3, 5, 10],
        "draws_per_budget": 100,
        "rbf_gamma_from_unlabelled_pool": gamma,
        "five_anchor": {
            "source_portfolio": {
                key: float(source[key].mean())
                for key in (
                    "spearman",
                    "top_quartile_precision",
                    "normalized_regret",
                )
            },
            "recipient_macro": macro.reset_index().to_dict(
                orient="records"
            ),
            "strongest_average_recipient_model": strongest,
            "source_minus_strongest_spearman": {
                "mean": float(spearman_difference.mean()),
                "ci95": quantiles(spearman_difference),
            },
            "source_minus_oracle_spearman": {
                "mean": float(oracle_spearman_difference.mean()),
                "ci95": quantiles(oracle_spearman_difference),
            },
            "passes_adversarial_spearman_gate": decision,
        },
        "claim_guard": (
            "This outcome-inspected sensitivity can challenge baseline "
            "dependence but cannot provide independent confirmation."
        ),
    }
    SUMMARY.write_text(
        json.dumps(summary, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
