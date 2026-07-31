"""Run the frozen post-outcome cross-database electrolyte interaction benchmark."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.decomposition import PCA
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

from common import RESULTS, ensure_output_dirs
from electrolyte_programme_interaction_common import (
    exact_formulation_signature,
    general_record_overlap_count,
    load_bamboo,
    load_calisol_subset,
    load_finales,
    load_kit,
    load_solventseg,
    percentile_rank,
    sha256,
    source_contains_target_family,
    validate_hash,
)
from mixture_response_transfer_common import (
    CHEMISTRY_FEATURE_DIM,
    STATE_FEATURE_NAMES,
    fit_shrinkage_adapter,
    fit_source_forest,
    maximin_anchors,
    mixture_features,
    nonanchor_test_indices,
    regression_metrics,
    response_target,
    source_predict,
    stable_seed,
)


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DESIGN_PATH = HERE / "bamboomixer_cross_database_interaction_design.json"
PREFIX = "bamboomixer_cross_database_interaction"


def output_paths() -> dict[str, Path]:
    return {
        "input_audit": RESULTS / f"{PREFIX}_input_audit.json",
        "seed_audit": RESULTS / f"{PREFIX}_seed_audit.csv",
        "solventseg_predictions": RESULTS / f"{PREFIX}_solventseg_predictions.csv",
        "solventseg_metrics": RESULTS / f"{PREFIX}_solventseg_metrics.csv",
        "solventseg_bootstrap": RESULTS / f"{PREFIX}_solventseg_bootstrap.csv",
        "solventseg_rank_permutation": RESULTS
        / f"{PREFIX}_solventseg_rank_permutation.csv",
        "solventseg_anchor_metrics": RESULTS
        / f"{PREFIX}_solventseg_anchor_metrics.csv",
        "solventseg_anchor_contrasts": RESULTS
        / f"{PREFIX}_solventseg_anchor_contrasts.csv",
        "finales_predictions": RESULTS / f"{PREFIX}_finales_predictions.csv",
        "finales_metrics": RESULTS / f"{PREFIX}_finales_metrics.csv",
        "summary": RESULTS / f"{PREFIX}_summary.json",
    }


def resolve_path(raw: str) -> Path:
    expanded = Path(raw).expanduser()
    return expanded if expanded.is_absolute() else ROOT / expanded


def rank_metrics(y_log: Sequence[float], prediction: Sequence[float]) -> dict[str, float]:
    truth = np.asarray(y_log, dtype=float)
    score = np.asarray(prediction, dtype=float)
    n = len(truth)
    if (
        n < 2
        or np.nanstd(truth) <= 1e-15
        or np.nanstd(score) <= 1e-15
    ):
        return {
            "spearman": float("nan"),
            "top_quartile_precision": float("nan"),
            "normalized_regret": float("nan"),
        }
    rho = float(stats.spearmanr(truth, score).statistic)
    k = max(1, int(math.ceil(0.25 * n)))
    true_top = set(np.argsort(truth, kind="stable")[-k:].tolist())
    predicted_top = set(np.argsort(score, kind="stable")[-k:].tolist())
    precision = len(true_top.intersection(predicted_top)) / k
    chosen = int(np.nanargmax(score))
    denominator = float(np.nanmax(truth) - np.nanmin(truth))
    regret = (
        0.0
        if denominator <= 1e-15
        else float((np.nanmax(truth) - truth[chosen]) / denominator)
    )
    return {
        "spearman": rho,
        "top_quartile_precision": float(precision),
        "normalized_regret": regret,
    }


def rank_only_metrics(
    y_log: Sequence[float],
    prediction: Sequence[float],
) -> dict[str, float]:
    """Return rank metrics without treating a percentile score as a response."""
    return {
        "n": int(len(y_log)),
        "log_rmse": float("nan"),
        "log_mae": float("nan"),
        "log_r2": float("nan"),
        "raw_rmse": float("nan"),
        "raw_mae": float("nan"),
        "raw_r2": float("nan"),
        **rank_metrics(y_log, prediction),
    }


def pairwise_concordance(
    frame: pd.DataFrame,
    prediction: np.ndarray,
    *,
    temperature_tolerance: float,
) -> tuple[float, int]:
    truth = frame["conductivity"].to_numpy(float)
    temperature = frame["temperature_C"].to_numpy(float)
    concordant = []
    for left in range(len(frame)):
        for right in range(left + 1, len(frame)):
            if abs(temperature[left] - temperature[right]) > temperature_tolerance:
                continue
            truth_delta = truth[left] - truth[right]
            prediction_delta = prediction[left] - prediction[right]
            if abs(truth_delta) <= 1e-15:
                continue
            if abs(prediction_delta) <= 1e-15:
                concordant.append(0.5)
            else:
                concordant.append(float(np.sign(truth_delta) == np.sign(prediction_delta)))
    return (
        (float(np.mean(concordant)), len(concordant))
        if concordant
        else (float("nan"), 0)
    )


def compact_target_space(x_target: np.ndarray, components: int = 20) -> np.ndarray:
    chemistry = StandardScaler().fit_transform(
        x_target[:, :CHEMISTRY_FEATURE_DIM]
    )
    n_components = min(components, len(x_target) - 1, chemistry.shape[1])
    reduced = PCA(n_components=n_components, random_state=0).fit_transform(chemistry)
    state = StandardScaler().fit_transform(
        x_target[:, CHEMISTRY_FEATURE_DIM:]
    )
    return np.column_stack([reduced, state])


def fit_programme_prediction(
    source_records: list[dict],
    target_matrices: dict[str, np.ndarray],
    *,
    arm: str,
    seeds: list[int],
    n_estimators: int,
    state_only: bool = False,
    chemistry_permuted: bool = False,
) -> tuple[dict[str, np.ndarray], list[dict[str, Any]]]:
    x_source = mixture_features(source_records)
    y_source = response_target(source_records)
    predictions = {name: [] for name in target_matrices}
    audit_rows: list[dict[str, Any]] = []
    for seed in seeds:
        permutation = None
        if chemistry_permuted:
            permutation = np.random.default_rng(
                stable_seed("chemistry-permutation", arm, seed)
            ).permutation(len(source_records))
        model = fit_source_forest(
            x_source,
            y_source,
            seed=stable_seed("source-model", arm, seed),
            n_estimators=n_estimators,
            state_only=state_only,
            chemistry_permutation=permutation,
        )
        for target, matrix in target_matrices.items():
            prediction = source_predict(model, matrix, state_only=state_only)
            predictions[target].append(prediction)
            audit_rows.append(
                {
                    "arm": arm,
                    "seed": seed,
                    "target": target,
                    "source_rows": len(source_records),
                    "prediction_mean": float(np.mean(prediction)),
                    "prediction_sd": float(np.std(prediction)),
                }
            )
    return (
        {
            target: np.mean(np.vstack(values), axis=0)
            for target, values in predictions.items()
        },
        audit_rows,
    )


def metric_rows(
    target_frame: pd.DataFrame,
    y_target: np.ndarray,
    predictions: dict[str, np.ndarray],
    splits: pd.DataFrame,
) -> pd.DataFrame:
    frame = target_frame.merge(
        splits[
            [
                "formulation_id",
                "kmeans_cluster",
                "edge_holdout",
                "edge_center_role",
            ]
        ],
        on="formulation_id",
        how="left",
        validate="many_to_one",
    )
    scopes: dict[str, np.ndarray] = {
        "all_180_rows": np.arange(len(frame), dtype=int),
        "fixed_25_C": np.flatnonzero(
            np.isclose(frame["temperature_C"].to_numpy(float), 25.0)
        ),
        "manual_edge_25_C": np.flatnonzero(
            np.isclose(frame["temperature_C"].to_numpy(float), 25.0)
            & frame["edge_holdout"].astype(bool).to_numpy()
        ),
    }
    for cluster in sorted(frame["kmeans_cluster"].dropna().astype(int).unique()):
        scopes[f"kmeans_cluster_{cluster}_25_C"] = np.flatnonzero(
            np.isclose(frame["temperature_C"].to_numpy(float), 25.0)
            & (frame["kmeans_cluster"].to_numpy(float) == cluster)
        )
    rows = []
    for scope, indices in scopes.items():
        for model, prediction in predictions.items():
            if model == "programme_balanced_rank_consensus":
                values = rank_only_metrics(
                    y_target[indices],
                    prediction[indices],
                )
            else:
                values = {
                    **regression_metrics(
                        y_target[indices],
                        prediction[indices],
                    ),
                    **rank_metrics(
                        y_target[indices],
                        prediction[indices],
                    ),
                }
            rows.append(
                {
                    "scope": scope,
                    "model": model,
                    **values,
                }
            )
    return pd.DataFrame(rows)


def resample_group_indices(
    groups: np.ndarray,
    *,
    rng: np.random.Generator,
) -> np.ndarray:
    unique = np.asarray(sorted(set(groups.astype(str))), dtype=object)
    sampled = rng.choice(unique, size=len(unique), replace=True)
    return np.concatenate(
        [np.flatnonzero(groups.astype(str) == group) for group in sampled]
    )


def bootstrap_contrasts(
    y_target: np.ndarray,
    predictions: dict[str, np.ndarray],
    formula_groups: np.ndarray,
    *,
    repetitions: int,
    seed: int,
) -> pd.DataFrame:
    contrasts = [
        ("bamboo_all", "bamboo_state_only"),
        ("bamboo_all", "bamboo_chemistry_permuted"),
        ("bamboo_all", "bamboo_without_target_family"),
        ("bamboo_all", "bamboo_target_family_only"),
        ("programme_balanced_portfolio", "bamboo_all"),
        ("programme_balanced_portfolio", "bamboo_state_only"),
        ("programme_balanced_portfolio", "bamboo_chemistry_permuted"),
        ("programme_balanced_portfolio", "calisol"),
        ("programme_balanced_portfolio", "kit"),
    ]
    rng = np.random.default_rng(seed)
    rows = []
    for repetition in range(repetitions):
        indices = resample_group_indices(formula_groups, rng=rng)
        truth = y_target[indices]
        for model, comparator in contrasts:
            first = regression_metrics(truth, predictions[model][indices])
            second = regression_metrics(truth, predictions[comparator][indices])
            rows.append(
                {
                    "repetition": repetition,
                    "model": model,
                    "comparator": comparator,
                    "relative_log_rmse_gain": float(
                        1.0 - first["log_rmse"] / second["log_rmse"]
                    ),
                    "spearman_gain": float(first["spearman"] - second["spearman"]),
                    "raw_r2_gain": float(first["raw_r2"] - second["raw_r2"]),
                }
            )
    return pd.DataFrame(rows)


def rank_permutation_table(
    y_target: np.ndarray,
    predictions: dict[str, np.ndarray],
    *,
    repetitions: int,
    seed: int,
) -> pd.DataFrame:
    models = [
        "bamboo_all",
        "bamboo_without_target_family",
        "bamboo_target_family_only",
        "calisol",
        "kit",
        "programme_balanced_portfolio",
        "programme_balanced_rank_consensus",
    ]
    rng = np.random.default_rng(seed)
    rows = []
    observed = {
        model: float(stats.spearmanr(y_target, predictions[model]).statistic)
        for model in models
    }
    exceed = {model: 0 for model in models}
    for _ in range(repetitions):
        permuted = rng.permutation(y_target)
        for model in models:
            value = float(stats.spearmanr(permuted, predictions[model]).statistic)
            exceed[model] += int(value >= observed[model] - 1e-15)
    for model in models:
        rows.append(
            {
                "model": model,
                "observed_spearman": observed[model],
                "permutations": repetitions,
                "one_sided_p": (exceed[model] + 1) / (repetitions + 1),
            }
        )
    output = pd.DataFrame(rows)
    order = output["one_sided_p"].sort_values(kind="stable").index.tolist()
    running = 0.0
    adjusted: dict[int, float] = {}
    count = len(order)
    for rank, index in enumerate(order):
        candidate = min(
            1.0,
            float(output.loc[index, "one_sided_p"]) * (count - rank),
        )
        running = max(running, candidate)
        adjusted[index] = running
    output["holm_p"] = [
        adjusted[index] for index in output.index
    ]
    return output


def anchor_tables(
    x_target: np.ndarray,
    y_target: np.ndarray,
    formula_groups: np.ndarray,
    predictions: dict[str, np.ndarray],
    *,
    budgets: list[int],
    draws: int,
    alpha: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    compact = compact_target_space(x_target)
    state_indices = [
        STATE_FEATURE_NAMES.index(name)
        for name in (
            "salt_molar_ratio",
            "log_salt_molar_ratio",
            "inverse_temperature_1000_per_K",
            "inverse_temperature_times_log_concentration",
            "inverse_temperature_times_concentration",
        )
    ]
    state = x_target[:, CHEMISTRY_FEATURE_DIM:][:, state_indices]
    source_models = [
        "bamboo_all",
        "calisol",
        "kit",
        "programme_balanced_portfolio",
    ]
    rows = []
    contrast_rows = []
    for budget in budgets:
        for draw in range(draws):
            anchors = maximin_anchors(
                compact,
                formula_groups,
                budget=budget,
                start_index=stable_seed("solventseg-anchor", budget, draw),
            )
            test = nonanchor_test_indices(formula_groups, anchors)
            target_model = Ridge(alpha=10.0)
            target_model.fit(compact[anchors], y_target[anchors])
            target_prediction = target_model.predict(compact[test])
            model_predictions: dict[str, np.ndarray] = {
                "target_only_ridge": target_prediction,
                "anchor_constant": np.full(
                    len(test), float(np.mean(y_target[anchors]))
                ),
                "programme_balanced_rank_consensus_frozen": predictions[
                    "programme_balanced_rank_consensus"
                ][test],
            }
            for model in source_models:
                frozen = predictions[model]
                adapter = fit_shrinkage_adapter(
                    frozen[anchors],
                    state[anchors],
                    y_target[anchors],
                    alpha=alpha,
                )
                model_predictions[f"{model}_frozen"] = frozen[test]
                model_predictions[f"{model}_adapted"] = adapter.predict(
                    frozen[test], state[test]
                )
            metrics_by_model = {}
            for model, prediction in model_predictions.items():
                if model == "programme_balanced_rank_consensus_frozen":
                    metrics = rank_only_metrics(y_target[test], prediction)
                else:
                    metrics = {
                        **regression_metrics(y_target[test], prediction),
                        **rank_metrics(y_target[test], prediction),
                    }
                metrics_by_model[model] = metrics
                rows.append(
                    {
                        "anchor_budget": budget,
                        "draw": draw,
                        "model": model,
                        "n_anchor_formulations": len(anchors),
                        "n_test_formulations": len(test),
                        "anchor_groups": json.dumps(
                            sorted(formula_groups[anchors].astype(str)),
                            separators=(",", ":"),
                        ),
                        **metrics,
                    }
                )
            for model in (
                "bamboo_all_frozen",
                "bamboo_all_adapted",
                "programme_balanced_portfolio_frozen",
                "programme_balanced_portfolio_adapted",
                "programme_balanced_rank_consensus_frozen",
            ):
                first = metrics_by_model[model]
                second = metrics_by_model["target_only_ridge"]
                relative_log_rmse_gain = (
                    float("nan")
                    if not np.isfinite(first["log_rmse"])
                    else float(
                        1.0 - first["log_rmse"] / second["log_rmse"]
                    )
                )
                contrast_rows.append(
                    {
                        "anchor_budget": budget,
                        "draw": draw,
                        "model": model,
                        "comparator": "target_only_ridge",
                        "relative_log_rmse_gain": relative_log_rmse_gain,
                        "spearman_gain": float(
                            first["spearman"] - second["spearman"]
                        ),
                        "top_quartile_precision_gain": float(
                            first["top_quartile_precision"]
                            - second["top_quartile_precision"]
                        ),
                        "normalized_regret_reduction": float(
                            second["normalized_regret"]
                            - first["normalized_regret"]
                        ),
                    }
                )
    return pd.DataFrame(rows), pd.DataFrame(contrast_rows)


def prediction_frame(
    target: pd.DataFrame,
    y_target: np.ndarray,
    predictions: dict[str, np.ndarray],
) -> pd.DataFrame:
    output = target.copy()
    output["truth_log10"] = y_target
    for model, prediction in predictions.items():
        output[f"prediction_{model}"] = prediction
    return output


def finales_metric_table(
    frame: pd.DataFrame,
    y_target: np.ndarray,
    predictions: dict[str, np.ndarray],
) -> pd.DataFrame:
    rows = []
    source_models = [
        "bamboo_all",
        "bamboo_without_target_family",
        "bamboo_target_family_only",
        "calisol",
        "kit",
        "programme_balanced_portfolio",
        "programme_balanced_rank_consensus",
    ]
    baseline_columns = [
        "target_extra_trees",
        "target_hist_gradient_boosting",
        "target_linear",
    ]
    for phase in sorted(frame["phase"].unique()):
        phase_mask = frame["phase"].eq(phase).to_numpy()
        evaluation = frame["split"].eq("evaluation").to_numpy()
        for hard in (False, True):
            mask = phase_mask & evaluation
            scope = f"{phase}|evaluation"
            if hard:
                mask &= frame["hard_ood_40pct"].astype(bool).to_numpy()
                scope += "|hard_ood_40pct"
            indices = np.flatnonzero(mask)
            if len(indices) < 3:
                continue
            selected = frame.iloc[indices].reset_index(drop=True)
            truth = y_target[indices]
            for model in source_models:
                score = predictions[model][indices]
                concordance, pairs = pairwise_concordance(
                    selected,
                    score,
                    temperature_tolerance=2.0,
                )
                rows.append(
                    {
                        "scope": scope,
                        "model": model,
                        "n": len(indices),
                        "temperature_matched_pairs": pairs,
                        "pairwise_concordance": concordance,
                        **rank_metrics(truth, score),
                    }
                )
            for model in baseline_columns:
                score = frame.iloc[indices][model].to_numpy(float)
                concordance, pairs = pairwise_concordance(
                    selected,
                    score,
                    temperature_tolerance=2.0,
                )
                rows.append(
                    {
                        "scope": scope,
                        "model": model,
                        "n": len(indices),
                        "temperature_matched_pairs": pairs,
                        "pairwise_concordance": concordance,
                        **rank_metrics(truth, score),
                    }
                )
    return pd.DataFrame(rows)


def interval(values: pd.Series) -> list[float]:
    finite = pd.to_numeric(values, errors="coerce").dropna()
    if finite.empty:
        return [float("nan"), float("nan")]
    return [
        float(finite.quantile(0.025)),
        float(finite.quantile(0.975)),
    ]


def make_summary(
    design: dict,
    input_audit: dict,
    metrics: pd.DataFrame,
    bootstrap: pd.DataFrame,
    rank_permutation: pd.DataFrame,
    anchor_metrics: pd.DataFrame,
    anchor_contrasts: pd.DataFrame,
    finales_metrics: pd.DataFrame,
) -> dict:
    all_rows = metrics[metrics["scope"] == "all_180_rows"].set_index("model")
    fixed = metrics[metrics["scope"] == "fixed_25_C"].set_index("model")
    contrast_summary = {}
    for (model, comparator), group in bootstrap.groupby(
        ["model", "comparator"], sort=True
    ):
        contrast_summary[f"{model}_vs_{comparator}"] = {
            "relative_log_rmse_gain_mean": float(
                group["relative_log_rmse_gain"].mean()
            ),
            "relative_log_rmse_gain_ci95": interval(
                group["relative_log_rmse_gain"]
            ),
            "spearman_gain_mean": float(group["spearman_gain"].mean()),
            "spearman_gain_ci95": interval(group["spearman_gain"]),
        }
    primary_anchor = anchor_metrics[anchor_metrics["anchor_budget"] == 5]
    anchor_macro = (
        primary_anchor.groupby("model", sort=True)[
            [
                "log_rmse",
                "log_r2",
                "spearman",
                "top_quartile_precision",
                "normalized_regret",
            ]
        ]
        .mean()
        .to_dict(orient="index")
    )
    primary_anchor_contrasts = anchor_contrasts[
        anchor_contrasts["anchor_budget"] == 5
    ]
    anchor_contrast_summary = {}
    for model, group in primary_anchor_contrasts.groupby("model", sort=True):
        anchor_contrast_summary[model] = {
            "relative_log_rmse_gain_mean": float(
                group["relative_log_rmse_gain"].mean()
            ),
            "relative_log_rmse_gain_ci95": interval(
                group["relative_log_rmse_gain"]
            ),
            "spearman_gain_mean": float(group["spearman_gain"].mean()),
            "spearman_gain_ci95": interval(group["spearman_gain"]),
            "top_quartile_precision_gain_mean": float(
                group["top_quartile_precision_gain"].mean()
            ),
            "top_quartile_precision_gain_ci95": interval(
                group["top_quartile_precision_gain"]
            ),
            "normalized_regret_reduction_mean": float(
                group["normalized_regret_reduction"].mean()
            ),
            "normalized_regret_reduction_ci95": interval(
                group["normalized_regret_reduction"]
            ),
        }
    rank_p = rank_permutation.set_index("model")[
        ["one_sided_p", "holm_p"]
    ].to_dict(orient="index")
    portfolio = all_rows.loc["programme_balanced_portfolio"]
    state = all_rows.loc["bamboo_state_only"]
    permuted = all_rows.loc["bamboo_chemistry_permuted"]
    portfolio_vs_state = contrast_summary[
        "programme_balanced_portfolio_vs_bamboo_state_only"
    ]
    portfolio_vs_permuted = contrast_summary[
        "programme_balanced_portfolio_vs_bamboo_chemistry_permuted"
    ]
    five = anchor_contrast_summary[
        "programme_balanced_portfolio_adapted"
    ]
    prediction_gate = {
        "portfolio_vs_state_relative_log_rmse_gain": float(
            1.0 - portfolio["log_rmse"] / state["log_rmse"]
        ),
        "portfolio_vs_state_relative_log_rmse_gain_ci95": portfolio_vs_state[
            "relative_log_rmse_gain_ci95"
        ],
        "portfolio_vs_permuted_relative_log_rmse_gain": float(
            1.0 - portfolio["log_rmse"] / permuted["log_rmse"]
        ),
        "portfolio_vs_permuted_relative_log_rmse_gain_ci95": (
            portfolio_vs_permuted["relative_log_rmse_gain_ci95"]
        ),
        "portfolio_log_r2": float(portfolio["log_r2"]),
        "five_anchor_vs_target_only_relative_log_rmse_gain": float(
            five["relative_log_rmse_gain_mean"]
        ),
        "five_anchor_vs_target_only_relative_log_rmse_gain_ci95": five[
            "relative_log_rmse_gain_ci95"
        ],
    }
    prediction_positive = bool(
        prediction_gate["portfolio_vs_state_relative_log_rmse_gain"] >= 0.10
        and prediction_gate[
            "portfolio_vs_state_relative_log_rmse_gain_ci95"
        ][0]
        > 0
        and prediction_gate[
            "five_anchor_vs_target_only_relative_log_rmse_gain"
        ]
        >= 0.10
        and prediction_gate[
            "five_anchor_vs_target_only_relative_log_rmse_gain_ci95"
        ][0]
        > 0
        and prediction_gate["portfolio_log_r2"] > 0
        and prediction_gate[
            "portfolio_vs_permuted_relative_log_rmse_gain"
        ]
        > 0
        and prediction_gate[
            "portfolio_vs_permuted_relative_log_rmse_gain_ci95"
        ][0]
        > 0
    )
    route = "prediction" if prediction_positive else "abstain"
    if not prediction_positive:
        rank_five = anchor_contrast_summary[
            "programme_balanced_rank_consensus_frozen"
        ]
        if (
            rank_five["spearman_gain_mean"] >= 0.10
            and rank_five["spearman_gain_ci95"][0] > 0
            and rank_five["top_quartile_precision_gain_mean"] > 0
            and rank_five["top_quartile_precision_gain_ci95"][0] >= 0
            and rank_five["normalized_regret_reduction_mean"] > 0
            and rank_five["normalized_regret_reduction_ci95"][0] >= 0
            and rank_p["programme_balanced_rank_consensus"]["holm_p"] < 0.05
        ):
            route = "ranking"
    finales_summary = (
        finales_metrics.sort_values(["scope", "model"])
        .to_dict(orient="records")
    )
    return {
        "status": "complete-post-outcome-cross-database-method-development",
        "design_sha256": sha256(DESIGN_PATH),
        "input_audit": input_audit,
        "solventseg": {
            "all_rows": {
                model: {
                    key: float(all_rows.loc[model, key])
                    for key in (
                        "log_rmse",
                        "log_r2",
                        "raw_rmse",
                        "raw_r2",
                        "spearman",
                    )
                }
                for model in all_rows.index
                if model != "programme_balanced_rank_consensus"
            },
            "fixed_25_C": {
                model: {
                    key: float(fixed.loc[model, key])
                    for key in (
                        "spearman",
                        "top_quartile_precision",
                        "normalized_regret",
                    )
                }
                for model in fixed.index
            },
            "rank_permutation_p": {
                key: {
                    test: float(value)
                    for test, value in tests.items()
                }
                for key, tests in rank_p.items()
            },
            "bootstrap_contrasts": contrast_summary,
            "five_anchor_macro": anchor_macro,
            "five_anchor_contrasts": anchor_contrast_summary,
            "routing": {
                "decision": route,
                "prediction_gate": prediction_gate,
                "claim_status": "post-outcome method development",
            },
        },
        "finales": finales_summary,
        "claim_guard": design["claim_guard"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()
    ensure_output_dirs()
    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    inputs = design["inputs"]
    resolved = {
        name: resolve_path(spec["path"])
        for name, spec in inputs.items()
        if "path" in spec
    }
    for name, path in resolved.items():
        validate_hash(path, inputs[name]["sha256"])

    bamboo = load_bamboo(resolved["bamboomixer"])
    solventseg, solventseg_frame = load_solventseg(resolved["solventseg"])
    splits = pd.read_csv(resolved["solventseg_splits"])
    calisol, calisol_frame = load_calisol_subset(resolved["calisol_subset"])
    kit, kit_frame = load_kit(resolved["kit"])
    finales, finales_frame = load_finales(
        [resolved["finales_primary"], resolved["finales_secondary"]]
    )
    if len(bamboo) != int(inputs["bamboomixer"]["eligible_conductivity_rows"]):
        raise AssertionError("BambooMixer source row count changed")
    if len(solventseg) != int(inputs["solventseg"]["rows"]):
        raise AssertionError("SolventSeg row count changed")
    if len(set(map(exact_formulation_signature, solventseg))) != int(
        inputs["solventseg"]["exact_formulations"]
    ):
        raise AssertionError("SolventSeg exact formulation count changed")
    if len(calisol) != int(inputs["calisol_subset"]["rows"]):
        raise AssertionError("CALiSol subset row count changed")
    if len(kit) != int(inputs["kit"]["aggregated_formulation_temperature_rows"]):
        raise AssertionError("KIT aggregated row count changed")

    bamboo_target_family = [
        record for record in bamboo if source_contains_target_family(record)
    ]
    bamboo_without_target_family = [
        record for record in bamboo if not source_contains_target_family(record)
    ]
    overlap_kwargs = {
        "composition_tolerance": 1e-4,
        "temperature_tolerance": 0.05,
        "outcome_tolerance": 0.01,
    }
    input_audit = {
        "bamboo_rows": len(bamboo),
        "bamboo_target_family_rows": len(bamboo_target_family),
        "bamboo_without_target_family_rows": len(bamboo_without_target_family),
        "calisol_rows": len(calisol),
        "calisol_articles": int(calisol_frame["source_doi"].nunique()),
        "kit_raw_rows": int(inputs["kit"]["raw_rows"]),
        "kit_aggregated_rows": len(kit),
        "kit_formulations": int(kit_frame["formula_key"].nunique()),
        "solventseg_rows": len(solventseg),
        "solventseg_formulations": int(solventseg_frame["formulation_id"].nunique()),
        "finales_rows": len(finales),
        "strict_record_overlap_counts": {
            "bamboo_to_calisol": general_record_overlap_count(
                bamboo, calisol, **overlap_kwargs
            ),
            "bamboo_to_kit": general_record_overlap_count(
                bamboo, kit, **overlap_kwargs
            ),
            "bamboo_to_solventseg": general_record_overlap_count(
                bamboo, solventseg, **overlap_kwargs
            ),
            "calisol_to_kit": general_record_overlap_count(
                calisol, kit, **overlap_kwargs
            ),
            "calisol_to_solventseg": general_record_overlap_count(
                calisol, solventseg, **overlap_kwargs
            ),
            "kit_to_solventseg": general_record_overlap_count(
                kit, solventseg, **overlap_kwargs
            ),
        },
        "portfolio_rule": design["overlap_policy"]["portfolio_protection"],
    }
    if input_audit["strict_record_overlap_counts"]["bamboo_to_solventseg"] != 0:
        raise AssertionError("Strict BambooMixer-to-SolventSeg record overlap")
    if input_audit["strict_record_overlap_counts"]["bamboo_to_calisol"] == 0:
        raise AssertionError("Expected disclosed BambooMixer-CALiSol overlap disappeared")

    target_records = {
        "solventseg": solventseg,
        "finales": finales,
    }
    target_matrices = {
        name: mixture_features(records) for name, records in target_records.items()
    }
    config = design["models"]["source_model"]
    seeds = [int(value) for value in config["seeds"]]
    n_estimators = int(config["n_estimators"])
    bootstraps = int(design["evaluation"]["bootstrap_formulation_repetitions"])
    permutations = int(
        design["evaluation"]["target_label_permutation_repetitions"]
    )
    anchor_draws = int(design["evaluation"]["anchor_coverage_draws"])
    if args.quick:
        seeds = seeds[:1]
        n_estimators = 80
        bootstraps = 200
        permutations = 500
        anchor_draws = 10

    source_arms = {
        "bamboo_all": (bamboo, False, False),
        "bamboo_state_only": (bamboo, True, False),
        "bamboo_chemistry_permuted": (bamboo, False, True),
        "bamboo_without_target_family": (
            bamboo_without_target_family,
            False,
            False,
        ),
        "bamboo_target_family_only": (bamboo_target_family, False, False),
        "calisol": (calisol, False, False),
        "kit": (kit, False, False),
    }
    predictions_by_target = {
        target: {} for target in target_records
    }
    seed_audit_rows = []
    for arm, (records, state_only, permuted) in source_arms.items():
        prediction, audit = fit_programme_prediction(
            records,
            target_matrices,
            arm=arm,
            seeds=seeds,
            n_estimators=n_estimators,
            state_only=state_only,
            chemistry_permuted=permuted,
        )
        for target, values in prediction.items():
            predictions_by_target[target][arm] = values
        seed_audit_rows.extend(audit)

    for target, predictions in predictions_by_target.items():
        portfolio_members = [
            predictions["bamboo_without_target_family"],
            predictions["calisol"],
            predictions["kit"],
        ]
        predictions["programme_balanced_portfolio"] = np.mean(
            np.vstack(portfolio_members), axis=0
        )
        rank_members = np.vstack(
            [percentile_rank(values) for values in portfolio_members]
        )
        # Canonical rounding makes exact rank ties portable through CSV.
        predictions["programme_balanced_rank_consensus"] = np.round(
            np.mean(rank_members, axis=0),
            decimals=12,
        )

    y_solventseg = response_target(solventseg)
    solvent_predictions = predictions_by_target["solventseg"]
    solvent_metrics = metric_rows(
        solventseg_frame,
        y_solventseg,
        solvent_predictions,
        splits,
    )
    formula_groups = solventseg_frame["formula_group"].to_numpy(str)
    bootstrap = bootstrap_contrasts(
        y_solventseg,
        solvent_predictions,
        formula_groups,
        repetitions=bootstraps,
        seed=stable_seed("solventseg-formulation-bootstrap"),
    )
    fixed_indices = np.flatnonzero(
        np.isclose(solventseg_frame["temperature_C"].to_numpy(float), 25.0)
    )
    rank_permutation = rank_permutation_table(
        y_solventseg[fixed_indices],
        {
            model: values[fixed_indices]
            for model, values in solvent_predictions.items()
        },
        repetitions=permutations,
        seed=stable_seed("solventseg-fixed25-permutation"),
    )
    anchor_metrics, anchor_contrasts = anchor_tables(
        target_matrices["solventseg"][fixed_indices],
        y_solventseg[fixed_indices],
        formula_groups[fixed_indices],
        {
            model: values[fixed_indices]
            for model, values in solvent_predictions.items()
        },
        budgets=[
            int(value)
            for value in design["evaluation"]["anchor_budgets_formulations"]
        ],
        draws=anchor_draws,
        alpha=float(design["models"]["few_shot_adapter"]["alpha"]),
    )

    y_finales = response_target(finales)
    finales_predictions = predictions_by_target["finales"]
    finales_metrics = finales_metric_table(
        finales_frame,
        y_finales,
        finales_predictions,
    )
    summary = make_summary(
        design,
        input_audit,
        solvent_metrics,
        bootstrap,
        rank_permutation,
        anchor_metrics,
        anchor_contrasts,
        finales_metrics,
    )
    if args.quick:
        summary["mode"] = "quick"
        summary["status"] = "quick-method-development"
    else:
        summary["mode"] = "formal"

    paths = output_paths()
    Path(paths["input_audit"]).write_text(
        json.dumps(input_audit, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    pd.DataFrame(seed_audit_rows).to_csv(paths["seed_audit"], index=False)
    prediction_frame(
        solventseg_frame,
        y_solventseg,
        solvent_predictions,
    ).to_csv(paths["solventseg_predictions"], index=False)
    solvent_metrics.to_csv(paths["solventseg_metrics"], index=False)
    bootstrap.to_csv(paths["solventseg_bootstrap"], index=False)
    rank_permutation.to_csv(paths["solventseg_rank_permutation"], index=False)
    anchor_metrics.to_csv(paths["solventseg_anchor_metrics"], index=False)
    anchor_contrasts.to_csv(paths["solventseg_anchor_contrasts"], index=False)
    prediction_frame(
        finales_frame,
        y_finales,
        finales_predictions,
    ).to_csv(paths["finales_predictions"], index=False)
    finales_metrics.to_csv(paths["finales_metrics"], index=False)
    paths["summary"].write_text(
        json.dumps(summary, indent=2, sort_keys=True, allow_nan=True),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True, allow_nan=True))


if __name__ == "__main__":
    main()
