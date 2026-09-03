"""Independent audit of the Edison SolventSeg rank-transfer result.

The script first reproduces the reported row-pooled Spearman result, then
re-evaluates the same predictions using formulation-level and fixed-temperature
estimands that correspond more directly to screening unseen formulations.
It also checks baseline sensitivity and a shuffled-donor-label falsifier.
"""

from __future__ import annotations

import itertools
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr, t
from sklearn.compose import TransformedTargetRegressor
from sklearn.ensemble import (
    ExtraTreesRegressor,
    HistGradientBoostingRegressor,
    RandomForestRegressor,
)
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler


HERE = Path(__file__).resolve().parent
RECIPIENT_PATH = HERE / "SolventSeg_LiPF6_EC_EMC_harmonized.csv"
DONOR_PATH = HERE / "CALiSol23_LiPF6_EC_EMC_harmonized.csv"
SPLIT_PATH = HERE / "SolventSeg_formulation_OOD_splits.csv"
EDISON_REPLICATES_PATH = HERE / "solventseg_rank_transfer_replicate_results.csv"
EDISON_FOLDS_PATH = HERE / "solventseg_rank_transfer_fold_results.csv"

FEATURES = ["EC_wt", "EMC_wt", "LiPF6_wt", "temperature_C"]
TARGET = "conductivity_mS_cm"
RANDOM_STATE = 2025


def safe_spearman(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    if len(y_true) < 3 or np.unique(y_true).size < 2 or np.unique(y_pred).size < 2:
        return float("nan")
    return float(spearmanr(y_true, y_pred).statistic)


def mean_finite(values: list[float]) -> float:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    return float(np.mean(arr)) if arr.size else float("nan")


def prediction_metrics(test: pd.DataFrame, prediction: np.ndarray) -> dict[str, float]:
    scored = test.copy()
    scored["prediction"] = np.asarray(prediction, dtype=float)

    within_temperature = []
    for _, group in scored.groupby("temperature_C", sort=True):
        within_temperature.append(
            safe_spearman(
                group[TARGET].to_numpy(),
                group["prediction"].to_numpy(),
            )
        )

    at_25 = scored.loc[np.isclose(scored["temperature_C"], 25.0)]
    rho_25 = safe_spearman(
        at_25[TARGET].to_numpy(),
        at_25["prediction"].to_numpy(),
    )

    formulation = (
        scored.groupby("formulation_id", as_index=False)
        .agg(true_mean=(TARGET, "mean"), predicted_mean=("prediction", "mean"))
    )
    formulation_mean_rho = safe_spearman(
        formulation["true_mean"].to_numpy(),
        formulation["predicted_mean"].to_numpy(),
    )

    true_at_25 = at_25[TARGET].to_numpy(dtype=float)
    pred_at_25 = at_25["prediction"].to_numpy(dtype=float)
    if len(at_25) > 0:
        selected = int(np.argmax(pred_at_25))
        true_best = float(np.max(true_at_25))
        selected_true = float(true_at_25[selected])
        span = float(np.max(true_at_25) - np.min(true_at_25))
        normalized_regret = (
            (true_best - selected_true) / span if span > 0 else float("nan")
        )
        top1_hit = float(np.isclose(selected_true, true_best))
        k = max(1, int(math.ceil(len(at_25) * 0.25)))
        true_top = set(np.argsort(true_at_25)[-k:])
        pred_top = set(np.argsort(pred_at_25)[-k:])
        top_quartile_precision = len(true_top & pred_top) / k
    else:
        normalized_regret = float("nan")
        top1_hit = float("nan")
        top_quartile_precision = float("nan")

    return {
        "row_pooled_rho": safe_spearman(
            scored[TARGET].to_numpy(), scored["prediction"].to_numpy()
        ),
        "within_temperature_mean_rho": mean_finite(within_temperature),
        "temperature_25C_rho": rho_25,
        "formulation_mean_rho": formulation_mean_rho,
        "temperature_25C_top1_hit": top1_hit,
        "temperature_25C_top_quartile_precision": top_quartile_precision,
        "temperature_25C_normalized_regret": normalized_regret,
    }


def model_panel() -> dict[str, object]:
    return {
        "edison_hgbr_leaf5": HistGradientBoostingRegressor(
            random_state=RANDOM_STATE,
            min_samples_leaf=5,
        ),
        "target_linear": LinearRegression(),
        "target_ridge_quadratic": make_pipeline(
            PolynomialFeatures(degree=2, include_bias=False),
            StandardScaler(),
            Ridge(alpha=1.0),
        ),
        "target_random_forest": RandomForestRegressor(
            n_estimators=300,
            min_samples_leaf=1,
            max_features=1.0,
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
        "target_extra_trees": ExtraTreesRegressor(
            n_estimators=300,
            min_samples_leaf=1,
            max_features=1.0,
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
        "temperature_only_linear": LinearRegression(),
    }


def model_features(name: str, frame: pd.DataFrame) -> np.ndarray:
    if name == "temperature_only_linear":
        return frame[["temperature_C"]].to_numpy(dtype=float)
    return frame[FEATURES].to_numpy(dtype=float)


def one_sided_sign_flip_p(differences: np.ndarray) -> float:
    differences = np.asarray(differences, dtype=float)
    differences = differences[np.isfinite(differences)]
    observed = float(np.mean(differences))
    if len(differences) == 0:
        return float("nan")
    null_means = [
        float(np.mean(differences * np.asarray(signs, dtype=float)))
        for signs in itertools.product([-1.0, 1.0], repeat=len(differences))
    ]
    return float(np.mean(np.asarray(null_means) >= observed - 1e-15))


def fold_inference(fold_values: pd.DataFrame) -> dict[str, float | int]:
    values = fold_values.to_numpy(dtype=float)
    values = values[np.isfinite(values)]
    n = int(len(values))
    if n < 2:
        return {
            "n_folds": n,
            "mean": float(np.mean(values)) if n else float("nan"),
            "ci95_low": float("nan"),
            "ci95_high": float("nan"),
            "one_sided_t_p": float("nan"),
            "exact_sign_flip_p": one_sided_sign_flip_p(values),
        }
    mean = float(np.mean(values))
    se = float(np.std(values, ddof=1) / math.sqrt(n))
    t_stat = mean / se if se > 0 else float("inf")
    critical = float(t.ppf(0.975, n - 1))
    return {
        "n_folds": n,
        "mean": mean,
        "ci95_low": mean - critical * se,
        "ci95_high": mean + critical * se,
        "one_sided_t_p": float(t.sf(t_stat, n - 1)),
        "exact_sign_flip_p": one_sided_sign_flip_p(values),
    }


def main() -> None:
    recipient = pd.read_csv(RECIPIENT_PATH)
    donor = pd.read_csv(DONOR_PATH)
    splits = pd.read_csv(SPLIT_PATH)
    edison_reps = pd.read_csv(EDISON_REPLICATES_PATH)
    edison_folds = pd.read_csv(EDISON_FOLDS_PATH)

    recipient = recipient.merge(
        splits[["formulation_id", "kmeans_cluster"]].drop_duplicates(),
        on="formulation_id",
        how="left",
        validate="many_to_one",
    )
    assert len(recipient) == 180
    assert recipient["formulation_id"].nunique() == 36
    assert set(recipient.groupby("formulation_id").size()) == {5}
    assert recipient["kmeans_cluster"].notna().all()

    donor_model = HistGradientBoostingRegressor(random_state=RANDOM_STATE)
    donor_model.fit(donor[FEATURES], donor[TARGET])

    replicate_rows: list[dict[str, object]] = []
    transfer_fold_rows: list[dict[str, object]] = []
    for fold in sorted(recipient["kmeans_cluster"].unique()):
        train_pool = recipient.loc[recipient["kmeans_cluster"] != fold].copy()
        test = recipient.loc[recipient["kmeans_cluster"] == fold].copy()
        transfer_prediction = donor_model.predict(test[FEATURES])
        transfer_metrics = prediction_metrics(test, transfer_prediction)
        transfer_fold_rows.append({"fold": int(fold), **transfer_metrics})

        fold_reps = edison_reps.loc[edison_reps["fold"] == fold]
        assert len(fold_reps) == 30
        for _, edison_row in fold_reps.iterrows():
            anchor_ids = [
                int(value)
                for value in str(edison_row["anchor_formulation_ids"]).split("|")
            ]
            anchors = train_pool.loc[
                train_pool["formulation_id"].isin(anchor_ids)
            ].copy()
            assert len(anchor_ids) == 3
            assert len(anchors) == 15

            for model_name, model in model_panel().items():
                x_train = model_features(model_name, anchors)
                x_test = model_features(model_name, test)
                model.fit(x_train, anchors[TARGET].to_numpy(dtype=float))
                baseline_prediction = model.predict(x_test)
                baseline_metrics = prediction_metrics(test, baseline_prediction)
                row: dict[str, object] = {
                    "fold": int(fold),
                    "replicate": int(edison_row["replicate"]),
                    "anchor_formulation_ids": edison_row[
                        "anchor_formulation_ids"
                    ],
                    "baseline_model": model_name,
                    "n_anchor_rows": len(anchors),
                    "n_test_rows": len(test),
                }
                for metric, transfer_value in transfer_metrics.items():
                    baseline_value = baseline_metrics[metric]
                    row[f"transfer_{metric}"] = transfer_value
                    row[f"baseline_{metric}"] = baseline_value
                    if "regret" in metric:
                        row[f"improvement_{metric}"] = (
                            baseline_value - transfer_value
                        )
                    else:
                        row[f"improvement_{metric}"] = (
                            transfer_value - baseline_value
                        )
                replicate_rows.append(row)

    replicate_metrics = pd.DataFrame(replicate_rows)
    transfer_folds = pd.DataFrame(transfer_fold_rows)

    original = replicate_metrics.loc[
        replicate_metrics["baseline_model"] == "edison_hgbr_leaf5"
    ].sort_values(["fold", "replicate"])
    supplied = edison_reps.sort_values(["fold", "replicate"])
    exact_reproduction = {
        "max_abs_transfer_rho_error": float(
            np.max(
                np.abs(
                    original["transfer_row_pooled_rho"].to_numpy()
                    - supplied["transfer_rho"].to_numpy()
                )
            )
        ),
        "max_abs_baseline_rho_error": float(
            np.max(
                np.abs(
                    original["baseline_row_pooled_rho"].to_numpy()
                    - supplied["baseline_rho"].to_numpy()
                )
            )
        ),
        "max_abs_difference_error": float(
            np.max(
                np.abs(
                    original["improvement_row_pooled_rho"].to_numpy()
                    - supplied["rho_difference"].to_numpy()
                )
            )
        ),
    }

    metric_names = [
        "row_pooled_rho",
        "within_temperature_mean_rho",
        "temperature_25C_rho",
        "formulation_mean_rho",
        "temperature_25C_top1_hit",
        "temperature_25C_top_quartile_precision",
        "temperature_25C_normalized_regret",
    ]
    inference_rows: list[dict[str, object]] = []
    for model_name, group in replicate_metrics.groupby("baseline_model"):
        for metric in metric_names:
            improvement_col = f"improvement_{metric}"
            per_fold = group.groupby("fold")[improvement_col].mean()
            stats = fold_inference(per_fold)
            inference_rows.append(
                {
                    "baseline_model": model_name,
                    "metric": metric,
                    **stats,
                    "transfer_mean_across_folds": float(
                        group.groupby("fold")[f"transfer_{metric}"].mean().mean()
                    ),
                    "baseline_mean_across_folds": float(
                        group.groupby("fold")[f"baseline_{metric}"].mean().mean()
                    ),
                }
            )
    inference = pd.DataFrame(inference_rows)

    # Label-shuffled donor falsifier. All recipient outcomes and OOD splits stay fixed.
    shuffled_rows: list[dict[str, object]] = []
    donor_y = donor[TARGET].to_numpy(dtype=float)
    donor_x = donor[FEATURES]
    rng = np.random.default_rng(20260730)
    for permutation in range(200):
        shuffled_model = HistGradientBoostingRegressor(random_state=RANDOM_STATE)
        shuffled_model.fit(donor_x, rng.permutation(donor_y))
        fold_metrics: list[dict[str, float]] = []
        for fold in sorted(recipient["kmeans_cluster"].unique()):
            test = recipient.loc[recipient["kmeans_cluster"] == fold]
            fold_metrics.append(
                prediction_metrics(
                    test,
                    shuffled_model.predict(test[FEATURES]),
                )
            )
        shuffled_rows.append(
            {
                "permutation": permutation + 1,
                **{
                    metric: mean_finite([row[metric] for row in fold_metrics])
                    for metric in metric_names
                },
            }
        )
    shuffled = pd.DataFrame(shuffled_rows)

    observed_transfer = {
        metric: float(transfer_folds[metric].mean()) for metric in metric_names
    }
    shuffled_assessment: dict[str, dict[str, float]] = {}
    for metric in metric_names:
        null = shuffled[metric].to_numpy(dtype=float)
        null = null[np.isfinite(null)]
        observed = observed_transfer[metric]
        if "regret" in metric:
            empirical_p = float((1 + np.sum(null <= observed)) / (1 + len(null)))
        else:
            empirical_p = float((1 + np.sum(null >= observed)) / (1 + len(null)))
        shuffled_assessment[metric] = {
            "observed": observed,
            "shuffled_mean": float(np.mean(null)),
            "shuffled_q95": float(np.quantile(null, 0.95)),
            "empirical_one_sided_p": empirical_p,
        }

    reported_fold_mean = float(edison_folds["mean_rho_difference"].mean())
    reproduced_fold_mean = float(
        original.groupby("fold")["improvement_row_pooled_rho"].mean().mean()
    )
    summary = {
        "status": "independent-audit-complete",
        "software": {
            "numpy": np.__version__,
            "pandas": pd.__version__,
        },
        "data": {
            "recipient_rows": len(recipient),
            "recipient_formulations": int(recipient["formulation_id"].nunique()),
            "donor_rows": len(donor),
            "folds": int(recipient["kmeans_cluster"].nunique()),
            "anchor_replicates_per_fold": 30,
        },
        "exact_reproduction": exact_reproduction,
        "reported_delta_rho": reported_fold_mean,
        "reproduced_delta_rho": reproduced_fold_mean,
        "difference": reproduced_fold_mean - reported_fold_mean,
        "shuffled_donor_assessment": shuffled_assessment,
        "interpretive_guard": (
            "The reported row-pooled Spearman mixes composition and temperature. "
            "Within-temperature, 25 C, and formulation-aggregated metrics are the "
            "decision-relevant checks for screening unseen formulations. Alternative "
            "target-only baselines are post-hoc robustness diagnostics, not new "
            "confirmatory estimands."
        ),
    }

    replicate_metrics.to_csv(HERE / "independent_metric_recalculation.csv", index=False)
    transfer_folds.to_csv(HERE / "independent_transfer_fold_metrics.csv", index=False)
    inference.to_csv(HERE / "independent_baseline_sensitivity.csv", index=False)
    shuffled.to_csv(HERE / "independent_shuffled_donor_controls.csv", index=False)
    (HERE / "independent_audit_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print("\nBaseline sensitivity:")
    print(
        inference.loc[
            inference["metric"].isin(
                [
                    "row_pooled_rho",
                    "within_temperature_mean_rho",
                    "temperature_25C_rho",
                    "formulation_mean_rho",
                    "temperature_25C_top_quartile_precision",
                ]
            )
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
