"""Run E6: provenance-anchored neighboring-condition contrast transfer.

This is a post-outcome-motivated mechanistic reanalysis.  The design in
``calisol_anchored_delta_transfer_design.json`` must exist before this script
is run.  Complete source articles are the independent units.  Target-anchor
outcomes are used only to restore the held-out article's absolute scale and
are never scored as test observations.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score
from sklearn.preprocessing import StandardScaler

from common import RESULTS, ensure_output_dirs
from run_calisol_external_borrowing import load_raw, prepare_tasks


HERE = Path(__file__).resolve().parent
DESIGN_PATH = HERE / "calisol_anchored_delta_transfer_design.json"
UPSTREAM_DESIGN_PATH = HERE / "calisol_external_borrowing_design.json"
PREFIX = "calisol_anchored_delta"
PRIMARY_ALPHA = 10.0
ALPHAS = (10.0, 1.0, 100.0)


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_seed(*tokens: object) -> int:
    raw = "|".join(str(token) for token in tokens).encode("utf-8")
    return int(hashlib.sha256(raw).hexdigest()[:8], 16)


def article_weights(groups: np.ndarray) -> np.ndarray:
    values, counts = np.unique(groups.astype(str), return_counts=True)
    lookup = {value: count for value, count in zip(values, counts, strict=True)}
    weights = np.asarray([1.0 / lookup[str(group)] for group in groups], dtype=float)
    return weights / weights.mean()


def keep_contrast_groups(groups: np.ndarray) -> np.ndarray:
    values, counts = np.unique(groups.astype(str), return_counts=True)
    valid = set(values[counts >= 2])
    return np.asarray([str(group) in valid for group in groups], dtype=bool)


@dataclass
class DeltaModel:
    scaler: StandardScaler
    model: Ridge
    source_rows: int
    source_articles: int

    def predict_change(self, x_from: np.ndarray, x_to: np.ndarray) -> np.ndarray:
        z_from = self.scaler.transform(np.atleast_2d(x_from))
        z_to = self.scaler.transform(np.atleast_2d(x_to))
        if len(z_from) == 1 and len(z_to) > 1:
            z_from = np.repeat(z_from, len(z_to), axis=0)
        return self.model.predict(z_to - z_from)


@dataclass
class AbsoluteModel:
    scaler: StandardScaler
    model: Ridge
    source_rows: int
    source_articles: int

    def predict(self, x: np.ndarray) -> np.ndarray:
        return self.model.predict(self.scaler.transform(np.atleast_2d(x)))


def fit_delta_model(
    x: np.ndarray,
    y: np.ndarray,
    groups: np.ndarray,
    alpha: float,
    shuffle_seed: int | None = None,
) -> DeltaModel:
    eligible = keep_contrast_groups(groups)
    x = np.asarray(x[eligible], dtype=float)
    y = np.asarray(y[eligible], dtype=float)
    groups = groups[eligible].astype(str)
    weights = article_weights(groups)
    scaler = StandardScaler()
    scaler.fit(x, sample_weight=weights)
    z = scaler.transform(x)

    if shuffle_seed is not None:
        rng = np.random.default_rng(shuffle_seed)
        shuffled = y.copy()
        for article in sorted(set(groups)):
            indices = np.flatnonzero(groups == article)
            shuffled[indices] = y[indices][rng.permutation(len(indices))]
        y = shuffled

    z_centered = np.empty_like(z)
    y_centered = np.empty_like(y)
    for article in sorted(set(groups)):
        indices = np.flatnonzero(groups == article)
        z_centered[indices] = z[indices] - z[indices].mean(axis=0)
        y_centered[indices] = y[indices] - y[indices].mean()

    model = Ridge(alpha=float(alpha), fit_intercept=False, solver="cholesky")
    model.fit(z_centered, y_centered, sample_weight=weights)
    return DeltaModel(
        scaler=scaler,
        model=model,
        source_rows=len(y),
        source_articles=len(set(groups)),
    )


def fit_absolute_model(
    x: np.ndarray,
    y: np.ndarray,
    groups: np.ndarray,
    alpha: float,
) -> AbsoluteModel:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    groups = groups.astype(str)
    weights = article_weights(groups)
    scaler = StandardScaler()
    scaler.fit(x, sample_weight=weights)
    z = scaler.transform(x)
    model = Ridge(alpha=float(alpha), fit_intercept=True, solver="cholesky")
    model.fit(z, y, sample_weight=weights)
    return AbsoluteModel(
        scaler=scaler,
        model=model,
        source_rows=len(y),
        source_articles=len(set(groups)),
    )


def select_feature_anchors(
    x: np.ndarray,
    unit_keys: np.ndarray,
    scaler: StandardScaler,
    budget: int,
) -> np.ndarray:
    z = scaler.transform(np.asarray(x, dtype=float))
    distances = ((z[:, None, :] - z[None, :, :]) ** 2).sum(axis=2)
    medoid_score = distances.mean(axis=1)
    best = np.flatnonzero(np.isclose(medoid_score, medoid_score.min()))
    first = min(best, key=lambda index: str(unit_keys[index]))
    selected = [int(first)]
    while len(selected) < budget:
        minimum_distance = distances[:, selected].min(axis=1)
        minimum_distance[selected] = -np.inf
        best_distance = np.nanmax(minimum_distance)
        candidates = np.flatnonzero(np.isclose(minimum_distance, best_distance))
        chosen = min(candidates, key=lambda index: str(unit_keys[index]))
        selected.append(int(chosen))
    return np.asarray(selected, dtype=int)


def delta_predictions(
    model: DeltaModel,
    x: np.ndarray,
    y: np.ndarray,
    anchors: np.ndarray,
    test: np.ndarray,
) -> np.ndarray:
    predictions = []
    for anchor in anchors:
        change = model.predict_change(x[anchor], x[test])
        predictions.append(float(y[anchor]) + change)
    return np.mean(np.vstack(predictions), axis=0)


def absolute_predictions(
    model: AbsoluteModel,
    x: np.ndarray,
    y: np.ndarray,
    anchors: np.ndarray,
    test: np.ndarray,
) -> np.ndarray:
    anchor_raw = model.predict(x[anchors])
    offset = float(np.mean(y[anchors] - anchor_raw))
    return model.predict(x[test]) + offset


def prediction_rows(
    article: str,
    target_article: pd.DataFrame,
    target_x: np.ndarray,
    anchor_local: np.ndarray,
    test_local: np.ndarray,
    budget: int,
    alpha: float,
    models: dict[str, DeltaModel | AbsoluteModel],
) -> list[dict[str, Any]]:
    y = target_article["value"].to_numpy(float)
    unit_keys = target_article["unit_key"].astype(str).to_numpy()
    anchor_keys = json.dumps(
        unit_keys[anchor_local].astype(str).tolist(), separators=(",", ":")
    )
    rows: list[dict[str, Any]] = []
    predictions: dict[str, np.ndarray] = {
        "anchor_constant": np.full(len(test_local), float(y[anchor_local].mean())),
        "neighbor_delta_ridge": delta_predictions(
            models["neighbor_delta_ridge"], target_x, y, anchor_local, test_local
        ),
        "neighbor_absolute_ridge": absolute_predictions(
            models["neighbor_absolute_ridge"], target_x, y, anchor_local, test_local
        ),
        "wrong_condition_delta": delta_predictions(
            models["wrong_condition_delta"], target_x, y, anchor_local, test_local
        ),
        "same_condition_delta_ceiling": delta_predictions(
            models["same_condition_delta_ceiling"],
            target_x,
            y,
            anchor_local,
            test_local,
        ),
    }
    for model_id, values in predictions.items():
        if model_id == "anchor_constant" and alpha != PRIMARY_ALPHA:
            continue
        for local_index, prediction in zip(test_local, values, strict=True):
            rows.append(
                {
                    "article_doi": article,
                    "anchor_budget": budget,
                    "alpha": alpha,
                    "model": model_id,
                    "unit_key": unit_keys[local_index],
                    "anchor_unit_keys": anchor_keys,
                    "y": float(y[local_index]),
                    "prediction": float(prediction),
                    "is_anchor": False,
                }
            )
    return rows


def article_metrics(predictions: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    group_columns = ["article_doi", "anchor_budget", "alpha", "model"]
    for keys, group in predictions.groupby(group_columns, sort=True):
        y = group["y"].to_numpy(float)
        pred = group["prediction"].to_numpy(float)
        rows.append(
            {
                **dict(zip(group_columns, keys, strict=True)),
                "n_nonanchor": len(group),
                "rmse": float(np.sqrt(np.mean((y - pred) ** 2))),
                "mae": float(np.mean(np.abs(y - pred))),
                "r2": float(r2_score(y, pred)) if len(group) >= 2 else np.nan,
            }
        )
    return pd.DataFrame(rows)


def macro_summary(predictions: pd.DataFrame, metrics: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for keys, group in metrics.groupby(["anchor_budget", "alpha", "model"], sort=True):
        budget, alpha, model = keys
        selected = predictions[
            (predictions["anchor_budget"] == budget)
            & (predictions["alpha"] == alpha)
            & (predictions["model"] == model)
        ]
        rows.append(
            {
                "anchor_budget": int(budget),
                "alpha": float(alpha),
                "model": str(model),
                "articles": int(group["article_doi"].nunique()),
                "nonanchor_rows": len(selected),
                "macro_rmse": float(group["rmse"].mean()),
                "macro_mae": float(group["mae"].mean()),
                "pooled_rmse": float(
                    np.sqrt(np.mean((selected["y"] - selected["prediction"]) ** 2))
                ),
                "pooled_r2": float(r2_score(selected["y"], selected["prediction"])),
            }
        )
    return pd.DataFrame(rows)


def exact_sign_flip_p(differences: np.ndarray) -> float:
    differences = np.asarray(differences, dtype=float)
    observed = float(differences.mean())
    signs = np.asarray(list(itertools.product((-1.0, 1.0), repeat=len(differences))))
    null = (signs * differences[None, :]).mean(axis=1)
    return float(np.mean(null >= observed - 1e-15))


def bootstrap_gain(
    delta_rmse: np.ndarray,
    reference_rmse: np.ndarray,
    replicates: int,
    seed: int,
) -> tuple[float, float, np.ndarray]:
    rng = np.random.default_rng(seed)
    n = len(delta_rmse)
    indices = rng.integers(0, n, size=(replicates, n))
    gains = 1.0 - (
        delta_rmse[indices].mean(axis=1) / reference_rmse[indices].mean(axis=1)
    )
    lo, hi = np.quantile(gains, [0.025, 0.975])
    return float(lo), float(hi), gains


def primary_effect(
    predictions: pd.DataFrame,
    metrics: pd.DataFrame,
    design: dict[str, Any],
) -> dict[str, Any]:
    selector = (metrics["anchor_budget"] == 1) & (metrics["alpha"] == PRIMARY_ALPHA)
    primary_metrics = metrics[selector].copy()
    pivot = primary_metrics.pivot(
        index="article_doi", columns="model", values="rmse"
    ).sort_index()
    delta = pivot["neighbor_delta_ridge"].to_numpy(float)
    absolute = pivot["neighbor_absolute_ridge"].to_numpy(float)
    anchor = pivot["anchor_constant"].to_numpy(float)
    gain_absolute = float(1.0 - delta.mean() / absolute.mean())
    gain_anchor = float(1.0 - delta.mean() / anchor.mean())
    lo, hi, _ = bootstrap_gain(
        delta,
        absolute,
        int(design["inference"]["article_cluster_bootstrap_replicates"]),
        int(design["inference"]["bootstrap_seed"]),
    )
    sign_flip_p = exact_sign_flip_p(absolute - delta)
    selected = predictions[
        (predictions["anchor_budget"] == 1)
        & (predictions["alpha"] == PRIMARY_ALPHA)
        & (predictions["model"] == "neighbor_delta_ridge")
    ]
    return {
        "articles": len(pivot),
        "macro_rmse_neighbor_delta": float(delta.mean()),
        "macro_rmse_neighbor_absolute": float(absolute.mean()),
        "macro_rmse_anchor_constant": float(anchor.mean()),
        "relative_macro_rmse_gain_vs_neighbor_absolute": gain_absolute,
        "relative_macro_rmse_gain_vs_anchor_constant": gain_anchor,
        "article_bootstrap_ci95": [lo, hi],
        "exact_one_sided_sign_flip_p": sign_flip_p,
        "positive_articles_vs_neighbor_absolute": int(np.sum(delta < absolute)),
        "pooled_nonanchor_r2": float(r2_score(selected["y"], selected["prediction"])),
        "article_effects": [
            {
                "article_doi": article,
                "rmse_neighbor_delta": float(row["neighbor_delta_ridge"]),
                "rmse_neighbor_absolute": float(row["neighbor_absolute_ridge"]),
                "relative_gain": float(
                    1.0
                    - row["neighbor_delta_ridge"]
                    / row["neighbor_absolute_ridge"]
                ),
            }
            for article, row in pivot.iterrows()
        ],
    }


def fit_fold_models(
    target: pd.DataFrame,
    sources: dict[int, pd.DataFrame],
    target_x_all: np.ndarray,
    source_x: dict[int, np.ndarray],
    heldout_article: str,
    alpha: float,
) -> tuple[dict[str, DeltaModel | AbsoluteModel], dict[str, int]]:
    test_chemistries = set(
        target.loc[target["doi"].astype(str) == heldout_article, "chemistry_key"].astype(str)
    )

    def source_arrays(
        temperature: int,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, int]]:
        frame = sources[temperature]
        pre_exact_overlap = int(
            (
                (frame["doi"].astype(str) != heldout_article)
                & frame["chemistry_key"].astype(str).isin(test_chemistries)
            ).sum()
        )
        pre_article_rows = int(
            (frame["doi"].astype(str) == heldout_article).sum()
        )
        keep = (frame["doi"].astype(str) != heldout_article) & (
            ~frame["chemistry_key"].astype(str).isin(test_chemistries)
        )
        retained = frame.loc[keep]
        audit = {
            "preexclusion_exact_test_chemistry_rows": pre_exact_overlap,
            "preexclusion_heldout_article_rows": pre_article_rows,
            "postexclusion_exact_test_chemistry_rows": int(
                retained["chemistry_key"].astype(str).isin(test_chemistries).sum()
            ),
            "postexclusion_heldout_article_rows": int(
                (retained["doi"].astype(str) == heldout_article).sum()
            ),
        }
        return (
            source_x[temperature][keep.to_numpy()],
            retained["value"].to_numpy(float),
            retained["doi"].astype(str).to_numpy(),
            audit,
        )

    x_neighbor, y_neighbor, g_neighbor, neighbor_audit = source_arrays(-30)
    x_wrong, y_wrong, g_wrong, wrong_audit = source_arrays(20)

    same_keep = target["doi"].astype(str) != heldout_article
    x_same = target_x_all[same_keep.to_numpy()]
    y_same = target.loc[same_keep, "value"].to_numpy(float)
    g_same = target.loc[same_keep, "doi"].astype(str).to_numpy()

    models: dict[str, DeltaModel | AbsoluteModel] = {
        "neighbor_delta_ridge": fit_delta_model(
            x_neighbor, y_neighbor, g_neighbor, alpha
        ),
        "neighbor_absolute_ridge": fit_absolute_model(
            x_neighbor, y_neighbor, g_neighbor, alpha
        ),
        "wrong_condition_delta": fit_delta_model(x_wrong, y_wrong, g_wrong, alpha),
        "same_condition_delta_ceiling": fit_delta_model(
            x_same, y_same, g_same, alpha
        ),
    }
    audit = {
        **{f"neighbor_{key}": value for key, value in neighbor_audit.items()},
        **{f"wrong_{key}": value for key, value in wrong_audit.items()},
    }
    return models, audit


def run_shuffled_null(
    design: dict[str, Any],
    target: pd.DataFrame,
    sources: dict[int, pd.DataFrame],
    target_x_all: np.ndarray,
    source_x: dict[int, np.ndarray],
    eligible_articles: list[str],
    real_primary: dict[str, Any],
) -> pd.DataFrame:
    absolute_rmse = {
        row["article_doi"]: row["rmse_neighbor_absolute"]
        for row in real_primary["article_effects"]
    }
    rows: list[dict[str, Any]] = []
    for permutation in range(int(design["inference"]["shuffled_delta_permutations"])):
        article_rmse: dict[str, float] = {}
        for article in eligible_articles:
            article_mask = target["doi"].astype(str) == article
            article_indices = np.flatnonzero(article_mask.to_numpy())
            article_frame = target.iloc[article_indices].reset_index(drop=True)
            article_x = target_x_all[article_indices]
            test_chemistries = set(article_frame["chemistry_key"].astype(str))
            source = sources[-30]
            keep = (source["doi"].astype(str) != article) & (
                ~source["chemistry_key"].astype(str).isin(test_chemistries)
            )
            x_train = source_x[-30][keep.to_numpy()]
            y_train = source.loc[keep, "value"].to_numpy(float)
            groups = source.loc[keep, "doi"].astype(str).to_numpy()
            model = fit_delta_model(
                x_train,
                y_train,
                groups,
                PRIMARY_ALPHA,
                shuffle_seed=stable_seed(
                    design["inference"]["bootstrap_seed"], "shuffle", permutation, article
                ),
            )
            anchors = select_feature_anchors(
                article_x,
                article_frame["unit_key"].astype(str).to_numpy(),
                model.scaler,
                1,
            )
            test = np.asarray(
                [index for index in range(len(article_frame)) if index not in set(anchors)],
                dtype=int,
            )
            prediction = delta_predictions(
                model,
                article_x,
                article_frame["value"].to_numpy(float),
                anchors,
                test,
            )
            article_rmse[article] = float(
                np.sqrt(
                    np.mean(
                        (
                            article_frame.loc[test, "value"].to_numpy(float)
                            - prediction
                        )
                        ** 2
                    )
                )
            )
        shuffled_macro = float(np.mean(list(article_rmse.values())))
        absolute_macro = float(np.mean([absolute_rmse[a] for a in eligible_articles]))
        rows.append(
            {
                "permutation": permutation,
                "macro_rmse_shuffled_delta": shuffled_macro,
                "macro_rmse_neighbor_absolute": absolute_macro,
                "relative_gain_vs_neighbor_absolute": 1.0
                - shuffled_macro / absolute_macro,
            }
        )
    return pd.DataFrame(rows)


def run_random_anchor_sensitivity(
    design: dict[str, Any],
    target: pd.DataFrame,
    target_x_all: np.ndarray,
    sources: dict[int, pd.DataFrame],
    source_x: dict[int, np.ndarray],
    eligible_articles: list[str],
) -> pd.DataFrame:
    fold_models: dict[str, dict[str, DeltaModel | AbsoluteModel]] = {}
    for article in eligible_articles:
        fold_models[article], _ = fit_fold_models(
            target,
            sources,
            target_x_all,
            source_x,
            article,
            PRIMARY_ALPHA,
        )
    rows: list[dict[str, Any]] = []
    repeats = int(design["inference"]["random_anchor_repetitions"])
    for repeat in range(repeats):
        for budget in design["deployment_contract"]["anchor_budgets"]:
            delta_rmse: list[float] = []
            absolute_rmse: list[float] = []
            for article in eligible_articles:
                indices = np.flatnonzero((target["doi"].astype(str) == article).to_numpy())
                frame = target.iloc[indices].reset_index(drop=True)
                x = target_x_all[indices]
                y = frame["value"].to_numpy(float)
                rng = np.random.default_rng(
                    stable_seed(
                        design["inference"]["bootstrap_seed"],
                        "anchor",
                        repeat,
                        budget,
                        article,
                    )
                )
                anchors = np.sort(rng.choice(len(frame), size=int(budget), replace=False))
                test = np.asarray(
                    [index for index in range(len(frame)) if index not in set(anchors)],
                    dtype=int,
                )
                models = fold_models[article]
                delta_pred = delta_predictions(
                    models["neighbor_delta_ridge"], x, y, anchors, test
                )
                absolute_pred = absolute_predictions(
                    models["neighbor_absolute_ridge"], x, y, anchors, test
                )
                delta_rmse.append(
                    float(np.sqrt(np.mean((y[test] - delta_pred) ** 2)))
                )
                absolute_rmse.append(
                    float(np.sqrt(np.mean((y[test] - absolute_pred) ** 2)))
                )
            rows.append(
                {
                    "repeat": repeat,
                    "anchor_budget": int(budget),
                    "macro_rmse_neighbor_delta": float(np.mean(delta_rmse)),
                    "macro_rmse_neighbor_absolute": float(np.mean(absolute_rmse)),
                    "relative_gain_vs_neighbor_absolute": float(
                        1.0 - np.mean(delta_rmse) / np.mean(absolute_rmse)
                    ),
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()
    ensure_output_dirs()
    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    upstream = json.loads(UPSTREAM_DESIGN_PATH.read_text(encoding="utf-8"))
    if not str(design["status"]).startswith("post-outcome-motivated"):
        raise AssertionError("Unexpected E6 evidential status")
    if design["data"]["raw_sha256"] != upstream["dataset"]["raw_sha256"]:
        raise AssertionError("E6 and upstream CALiSol raw hashes differ")

    raw = load_raw(upstream)
    target, sources, target_x_all, source_x, feature_names, structure = prepare_tasks(
        raw, upstream
    )
    counts = target.groupby(target["doi"].astype(str)).size().sort_index()
    minimum = int(
        design["deployment_contract"]["common_scope_minimum_target_units_per_article"]
    )
    eligible_articles = sorted(counts[counts >= minimum].index.astype(str))
    target_common = target[target["doi"].astype(str).isin(eligible_articles)]
    if len(eligible_articles) != int(
        design["deployment_contract"]["common_scope_expected_articles"]
    ):
        raise AssertionError("E6 eligible article count changed")
    if len(target_common) != int(
        design["deployment_contract"]["common_scope_expected_target_units"]
    ):
        raise AssertionError("E6 common-scope target count changed")

    all_rows: list[dict[str, Any]] = []
    leakage_rows: list[dict[str, Any]] = []
    for article in eligible_articles:
        article_indices = np.flatnonzero(
            (target["doi"].astype(str) == article).to_numpy()
        )
        article_frame = target.iloc[article_indices].reset_index(drop=True)
        article_x = target_x_all[article_indices]
        for alpha in ALPHAS:
            models, audit = fit_fold_models(
                target,
                sources,
                target_x_all,
                source_x,
                article,
                alpha,
            )
            leakage_rows.append(
                {
                    "article_doi": article,
                    "alpha": alpha,
                    **audit,
                    "neighbor_delta_source_rows": models[
                        "neighbor_delta_ridge"
                    ].source_rows,
                    "neighbor_delta_source_articles": models[
                        "neighbor_delta_ridge"
                    ].source_articles,
                }
            )
            anchor_scaler = models["neighbor_delta_ridge"].scaler
            for budget in design["deployment_contract"]["anchor_budgets"]:
                anchors = select_feature_anchors(
                    article_x,
                    article_frame["unit_key"].astype(str).to_numpy(),
                    anchor_scaler,
                    int(budget),
                )
                anchor_set = set(anchors)
                test = np.asarray(
                    [
                        index
                        for index in range(len(article_frame))
                        if index not in anchor_set
                    ],
                    dtype=int,
                )
                all_rows.extend(
                    prediction_rows(
                        article,
                        article_frame,
                        article_x,
                        anchors,
                        test,
                        int(budget),
                        alpha,
                        models,
                    )
                )

    predictions = pd.DataFrame(all_rows).sort_values(
        ["anchor_budget", "alpha", "model", "article_doi", "unit_key"],
        kind="stable",
    )
    metrics = article_metrics(predictions)
    macro = macro_summary(predictions, metrics)
    primary = primary_effect(predictions, metrics, design)

    if args.quick:
        shuffled = run_shuffled_null(
            {**design, "inference": {**design["inference"], "shuffled_delta_permutations": 9}},
            target,
            sources,
            target_x_all,
            source_x,
            eligible_articles,
            primary,
        )
        random_anchor = run_random_anchor_sensitivity(
            {
                **design,
                "inference": {**design["inference"], "random_anchor_repetitions": 5},
            },
            target,
            target_x_all,
            sources,
            source_x,
            eligible_articles,
        )
    else:
        shuffled = run_shuffled_null(
            design,
            target,
            sources,
            target_x_all,
            source_x,
            eligible_articles,
            primary,
        )
        random_anchor = run_random_anchor_sensitivity(
            design,
            target,
            target_x_all,
            sources,
            source_x,
            eligible_articles,
        )

    shuffled_median = float(shuffled["relative_gain_vs_neighbor_absolute"].median())
    shuffled_p = float(
        (1 + (shuffled["relative_gain_vs_neighbor_absolute"]
              >= primary["relative_macro_rmse_gain_vs_neighbor_absolute"]).sum())
        / (1 + len(shuffled))
    )
    primary["median_shuffled_relative_gain"] = shuffled_median
    primary["gain_advantage_over_median_shuffled"] = float(
        primary["relative_macro_rmse_gain_vs_neighbor_absolute"] - shuffled_median
    )
    primary["shuffled_delta_permutation_p"] = shuffled_p

    leakages = pd.DataFrame(leakage_rows)
    zero_leakage = bool(
        (leakages["neighbor_postexclusion_exact_test_chemistry_rows"] == 0).all()
        and (leakages["wrong_postexclusion_exact_test_chemistry_rows"] == 0).all()
        and (leakages["neighbor_postexclusion_heldout_article_rows"] == 0).all()
        and (leakages["wrong_postexclusion_heldout_article_rows"] == 0).all()
    )
    gate_spec = design["success_gate"]
    gates = {
        "gain_vs_absolute_at_least_5pct": bool(
            primary["relative_macro_rmse_gain_vs_neighbor_absolute"]
            >= gate_spec["minimum_relative_macro_rmse_gain_vs_absolute_neighbor"]
        ),
        "article_bootstrap_ci_lower_above_zero": bool(
            primary["article_bootstrap_ci95"][0] > 0
        ),
        "exact_sign_flip_p_at_most_0_05": bool(
            primary["exact_one_sided_sign_flip_p"]
            <= gate_spec["exact_one_sided_sign_flip_p_at_most"]
        ),
        "positive_articles_at_least_8_of_11": bool(
            primary["positive_articles_vs_neighbor_absolute"]
            >= gate_spec["minimum_positive_articles_of_11"]
        ),
        "pooled_nonanchor_r2_positive": bool(primary["pooled_nonanchor_r2"] > 0),
        "gain_vs_anchor_constant_at_least_5pct": bool(
            primary["relative_macro_rmse_gain_vs_anchor_constant"]
            >= gate_spec["minimum_relative_macro_rmse_gain_vs_anchor_constant"]
        ),
        "advantage_over_median_shuffled_at_least_3pp": bool(
            primary["gain_advantage_over_median_shuffled"]
            >= gate_spec["minimum_gain_advantage_over_median_shuffled_delta"]
        ),
        "shuffled_permutation_p_at_most_0_05": bool(
            primary["shuffled_delta_permutation_p"]
            <= gate_spec["shuffled_delta_permutation_p_at_most"]
        ),
        "zero_article_or_chemistry_leakage": zero_leakage,
    }
    decision = (
        "mechanistic-rescue"
        if all(gates.values())
        else (
            "contrast-transfer-harmful"
            if primary["relative_macro_rmse_gain_vs_neighbor_absolute"] < 0
            else "contrast-transfer-unresolved"
        )
    )

    summary = {
        "status": "quick-smoke" if args.quick else "complete",
        "evidential_status": design["status"],
        "design_sha256": file_sha256(DESIGN_PATH),
        "upstream_design_sha256": file_sha256(UPSTREAM_DESIGN_PATH),
        "raw_sha256": design["data"]["raw_sha256"],
        "target_units_all": len(target),
        "target_articles_all": int(target["doi"].nunique()),
        "common_scope_units": len(target_common),
        "common_scope_articles": len(eligible_articles),
        "common_scope_article_dois": eligible_articles,
        "features": len(feature_names),
        "source_structure": structure.to_dict(orient="records"),
        "primary": primary,
        "gates": gates,
        "decision": decision,
        "random_anchor_sensitivity": {
            str(int(budget)): {
                "median_relative_gain": float(group["relative_gain_vs_neighbor_absolute"].median()),
                "q10_q90": [
                    float(group["relative_gain_vs_neighbor_absolute"].quantile(0.1)),
                    float(group["relative_gain_vs_neighbor_absolute"].quantile(0.9)),
                ],
                "positive_repetitions": int(
                    (group["relative_gain_vs_neighbor_absolute"] > 0).sum()
                ),
                "repetitions": len(group),
            }
            for budget, group in random_anchor.groupby("anchor_budget")
        },
        "claim_guard": design["interpretation_policy"],
    }

    predictions.to_csv(RESULTS / f"{PREFIX}_predictions.csv", index=False)
    metrics.to_csv(RESULTS / f"{PREFIX}_article_metrics.csv", index=False)
    macro.to_csv(RESULTS / f"{PREFIX}_macro_metrics.csv", index=False)
    shuffled.to_csv(RESULTS / f"{PREFIX}_shuffled_null.csv", index=False)
    random_anchor.to_csv(
        RESULTS / f"{PREFIX}_random_anchor_sensitivity.csv", index=False
    )
    leakages.to_csv(RESULTS / f"{PREFIX}_leakage_audit.csv", index=False)
    (RESULTS / f"{PREFIX}_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
