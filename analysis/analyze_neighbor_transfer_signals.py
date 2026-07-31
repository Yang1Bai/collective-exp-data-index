"""Diagnose where neighborhood information enters OBELiX OOD decisions.

This is explicitly post-result method development. It decomposes the first
acquisition into target mean, ensemble spread, source rank, and composition
coverage without changing the completed frozen sequential decision.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.model_selection import GroupKFold

try:
    from .run_obelix_ood_discovery import (
        INPUT_META_PATH,
        INPUT_PATH,
        initial_indices,
        load_frozen_input,
        make_model,
        true_hit_set,
    )
except ImportError:
    from run_obelix_ood_discovery import (
        INPUT_META_PATH,
        INPUT_PATH,
        initial_indices,
        load_frozen_input,
        make_model,
        true_hit_set,
    )


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis"
RESULTS = ANALYSIS / "results"
DESIGN_PATH = ANALYSIS / "neighbor_transfer_methods_design.json"
DETAIL_PATH = RESULTS / "neighbor_transfer_signal_diagnostics.csv"
SUMMARY_PATH = RESULTS / "neighbor_transfer_signal_summary.json"


def safe_spearman(left: np.ndarray, right: np.ndarray) -> float:
    left = np.asarray(left, dtype=float)
    right = np.asarray(right, dtype=float)
    if np.nanstd(left) == 0 or np.nanstd(right) == 0:
        return float("nan")
    return float(stats.spearmanr(left, right).statistic)


def safe_pearson(left: np.ndarray, right: np.ndarray) -> float:
    left = np.asarray(left, dtype=float)
    right = np.asarray(right, dtype=float)
    if np.nanstd(left) == 0 or np.nanstd(right) == 0:
        return float("nan")
    return float(stats.pearsonr(left, right).statistic)


def percentile_rank(values: np.ndarray) -> np.ndarray:
    return pd.Series(np.asarray(values, dtype=float)).rank(
        method="average", pct=True
    ).to_numpy(float)


def rank_metrics(
    *,
    score: np.ndarray,
    pool: list[int],
    hit_set: set[int],
    target: pd.DataFrame,
) -> dict[str, float]:
    keys = target.loc[pool, "material_key"].astype(str).to_numpy()
    values = target.loc[pool, "value"].to_numpy(float)
    order = np.lexsort((keys, -np.asarray(score, dtype=float)))
    ordered_indices = [pool[int(position)] for position in order]
    first_hit_rank = next(
        rank
        for rank, target_index in enumerate(ordered_indices, start=1)
        if target_index in hit_set
    )
    shortlist_n = max(1, math.ceil(0.10 * len(pool)))
    shortlist_hits = sum(index in hit_set for index in ordered_indices[:shortlist_n])
    recall = shortlist_hits / len(hit_set)
    expected_recall = shortlist_n / len(pool)
    return {
        "first_hit_rank": float(first_hit_rank),
        "first_hit_fraction": float(first_hit_rank / len(pool)),
        "top10_recall_top5": float(recall),
        "top10_enrichment": float(recall / expected_recall),
        "score_outcome_spearman": safe_spearman(score, values),
    }


def composition_novelty(
    candidate_features: np.ndarray, labelled_features: np.ndarray
) -> np.ndarray:
    squared = np.sum(
        (candidate_features[:, None, :] - labelled_features[None, :, :]) ** 2,
        axis=2,
    )
    return np.sqrt(np.min(squared, axis=1))


def prediction_components(model, features: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    tree_predictions = np.asarray(
        [tree.predict(features) for tree in model.estimators_], dtype=float
    )
    return tree_predictions.mean(axis=0), tree_predictions.std(axis=0)


def signal_anatomy(
    target: pd.DataFrame,
    x: np.ndarray,
    prior: np.ndarray,
    pool_by_scope: dict[str, list[int]],
    seeds: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    y = target["value"].to_numpy(float)
    rank_rows: list[dict] = []
    uncertainty_rows: list[dict] = []
    for seed in range(seeds):
        initial = initial_indices(target, seed, 30)
        model = make_model("extra-trees-primary", seed).fit(x[initial], y[initial])
        initial_rho = safe_spearman(prior[initial], y[initial])
        credibility_weight = float(np.clip(initial_rho, -0.5, 0.5))
        for scope, pool in pool_by_scope.items():
            hit_set = true_hit_set(target, pool)
            mean, spread = prediction_components(model, x[pool])
            novelty = composition_novelty(x[pool], x[initial])
            prior_pool = prior[pool]
            mean_rank = percentile_rank(mean)
            prior_rank = percentile_rank(prior_pool)
            novelty_rank = percentile_rank(novelty)
            scores = {
                "target_mean": mean,
                "ucb_beta_0.25": mean + 0.25 * spread,
                "ucb_beta_0.5": mean + 0.5 * spread,
                "ucb_beta_1": mean + spread,
                "ucb_beta_2": mean + 2.0 * spread,
                "ensemble_spread_only": spread,
                "composition_novelty_only": novelty,
                "thermoelectric_prior_high": prior_pool,
                "thermoelectric_prior_low": -prior_pool,
                "equal_positive_rank_fusion": mean_rank + prior_rank,
                "credibility_weighted_signed_rank_fusion": (
                    mean_rank + credibility_weight * (prior_rank - 0.5)
                ),
                "target_mean_novelty_rank_fusion": (
                    mean_rank + 0.5 * (novelty_rank - 0.5)
                ),
            }
            for score_name, score in scores.items():
                rank_rows.append(
                    {
                        "scope": scope,
                        "seed": seed,
                        "score": score_name,
                        "initial_source_spearman": initial_rho,
                        "source_weight": (
                            credibility_weight
                            if score_name == "credibility_weighted_signed_rank_fusion"
                            else np.nan
                        ),
                        **rank_metrics(
                            score=score,
                            pool=pool,
                            hit_set=hit_set,
                            target=target,
                        ),
                    }
                )
            outcomes = y[pool]
            uncertainty_rows.append(
                {
                    "scope": scope,
                    "seed": seed,
                    "ensemble_spread_absolute_error_spearman": safe_spearman(
                        spread, np.abs(outcomes - mean)
                    ),
                    "ensemble_spread_outcome_spearman": safe_spearman(
                        spread, outcomes
                    ),
                    "target_mean_outcome_spearman": safe_spearman(mean, outcomes),
                    "mean_absolute_error": float(np.mean(np.abs(outcomes - mean))),
                }
            )
    return pd.DataFrame(rank_rows), pd.DataFrame(uncertainty_rows)


def residual_diagnostics(
    target: pd.DataFrame,
    x: np.ndarray,
    prior: np.ndarray,
    pool_by_scope: dict[str, list[int]],
) -> dict:
    y = target["value"].to_numpy(float)
    train = target.index[target["split"] == "train"].to_numpy(int)
    groups = target.loc[train, "group"].astype(str).to_numpy()
    oof = np.full(len(train), np.nan)
    splitter = GroupKFold(n_splits=5)
    for fold, (fit_position, test_position) in enumerate(
        splitter.split(x[train], y[train], groups), start=1
    ):
        fit_index = train[fit_position]
        test_index = train[test_position]
        model = make_model("extra-trees-primary", 9000 + fold).fit(
            x[fit_index], y[fit_index]
        )
        oof[test_position] = model.predict(x[test_index])
    if not np.isfinite(oof).all():
        raise AssertionError("Group OOF prediction is incomplete")
    train_residual = y[train] - oof
    full_model = make_model("extra-trees-primary", 9999).fit(x[train], y[train])
    result = {
        "official_train": {
            "n": int(len(train)),
            "source_outcome_spearman": safe_spearman(prior[train], y[train]),
            "source_outcome_pearson": safe_pearson(prior[train], y[train]),
            "source_target_model_residual_spearman": safe_spearman(
                prior[train], train_residual
            ),
            "source_target_model_residual_pearson": safe_pearson(
                prior[train], train_residual
            ),
            "target_oof_outcome_spearman": safe_spearman(oof, y[train]),
        }
    }
    for scope, pool in pool_by_scope.items():
        predicted = full_model.predict(x[pool])
        residual = y[pool] - predicted
        result[scope] = {
            "n": int(len(pool)),
            "source_outcome_spearman": safe_spearman(prior[pool], y[pool]),
            "source_outcome_pearson": safe_pearson(prior[pool], y[pool]),
            "source_target_model_residual_spearman": safe_spearman(
                prior[pool], residual
            ),
            "source_target_model_residual_pearson": safe_pearson(
                prior[pool], residual
            ),
            "target_model_outcome_spearman": safe_spearman(predicted, y[pool]),
        }
    return result


def summarize_scores(frame: pd.DataFrame) -> list[dict]:
    rows: list[dict] = []
    for (scope, score), local in frame.groupby(["scope", "score"], sort=True):
        rows.append(
            {
                "scope": scope,
                "score": score,
                "seeds": int(len(local)),
                "first_hit_rank_mean": float(local["first_hit_rank"].mean()),
                "first_hit_rank_median": float(local["first_hit_rank"].median()),
                "first_hit_fraction_mean": float(local["first_hit_fraction"].mean()),
                "first_hit_fraction_seed_quantile_95": [
                    float(value)
                    for value in local["first_hit_fraction"].quantile([0.025, 0.975])
                ],
                "top10_recall_top5_mean": float(local["top10_recall_top5"].mean()),
                "top10_enrichment_mean": float(local["top10_enrichment"].mean()),
                "score_outcome_spearman_mean": float(
                    local["score_outcome_spearman"].mean()
                ),
            }
        )
    return rows


def main() -> None:
    design_bytes = DESIGN_PATH.read_bytes()
    design = json.loads(design_bytes)
    metadata, arrays, target = load_frozen_input(INPUT_PATH, INPUT_META_PATH)
    x = np.asarray(arrays["composition_features"], dtype=float)
    prior = np.asarray(arrays["thermoelectric_prior"], dtype=float)
    test = target.index[target["split"] == "test"].astype(int).tolist()
    hard = [index for index in test if target.at[index, "hard_ood_selected"]]
    pool_by_scope = {"official_test": test, "hard_ood_40pct": hard}
    rank_frame, uncertainty_frame = signal_anatomy(
        target=target,
        x=x,
        prior=prior,
        pool_by_scope=pool_by_scope,
        seeds=int(design["stage_1_signal_anatomy"]["seeds"]),
    )
    detail = rank_frame.merge(
        uncertainty_frame, on=["scope", "seed"], how="left", validate="many_to_one"
    )
    detail.to_csv(DETAIL_PATH, index=False)

    uncertainty_summary = []
    for scope, local in uncertainty_frame.groupby("scope", sort=True):
        uncertainty_summary.append(
            {
                "scope": scope,
                "seeds": int(len(local)),
                "spread_absolute_error_spearman_mean": float(
                    local["ensemble_spread_absolute_error_spearman"].mean()
                ),
                "spread_outcome_spearman_mean": float(
                    local["ensemble_spread_outcome_spearman"].mean()
                ),
                "target_mean_outcome_spearman_mean": float(
                    local["target_mean_outcome_spearman"].mean()
                ),
            }
        )

    credibility = rank_frame[
        rank_frame["score"] == "credibility_weighted_signed_rank_fusion"
    ].copy()
    credibility_summary = []
    for scope, local in credibility.groupby("scope", sort=True):
        target_mean = rank_frame[
            (rank_frame["scope"] == scope) & (rank_frame["score"] == "target_mean")
        ].set_index("seed")
        local = local.set_index("seed")
        realized_saving = (
            target_mean["first_hit_rank"] - local["first_hit_rank"]
        ).to_numpy(float)
        credibility_summary.append(
            {
                "scope": scope,
                "initial_source_spearman_mean": float(
                    local["initial_source_spearman"].mean()
                ),
                "initial_source_spearman_quantile_95": [
                    float(value)
                    for value in local["initial_source_spearman"].quantile(
                        [0.025, 0.975]
                    )
                ],
                "mean_source_weight": float(local["source_weight"].mean()),
                "fraction_weights_positive": float(np.mean(local["source_weight"] > 0)),
                "credibility_realized_rank_saving_spearman": safe_spearman(
                    local["initial_source_spearman"].to_numpy(float),
                    realized_saving,
                ),
                "mean_rank_saved_vs_target_mean": float(realized_saving.mean()),
            }
        )

    summary = {
        "analysis_status": "post-result-signal-anatomy; cannot redefine frozen OBELiX decisions",
        "design_sha256": hashlib.sha256(design_bytes).hexdigest(),
        "input_sha256": metadata["input_sha256"],
        "seeds": int(design["stage_1_signal_anatomy"]["seeds"]),
        "candidate_pools": {scope: len(pool) for scope, pool in pool_by_scope.items()},
        "uniform_random_full_ranking_reference": {
            scope: {
                "candidate_n": int(len(pool)),
                "true_hit_n": int(len(true_hit_set(target, pool))),
                "exact_expected_first_hit_rank": float(
                    (len(pool) + 1) / (len(true_hit_set(target, pool)) + 1)
                ),
                "exact_expected_first_hit_fraction": float(
                    ((len(pool) + 1) / (len(true_hit_set(target, pool)) + 1))
                    / len(pool)
                ),
            }
            for scope, pool in pool_by_scope.items()
        },
        "score_summary": summarize_scores(rank_frame),
        "uncertainty_summary": uncertainty_summary,
        "residual_diagnostics": residual_diagnostics(
            target=target, x=x, prior=prior, pool_by_scope=pool_by_scope
        ),
        "credibility_summary": credibility_summary,
        "claim_guard": design["stage_1_signal_anatomy"]["claim_guard"],
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
