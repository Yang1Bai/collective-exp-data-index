"""Develop and stress-test a physics-aware electrolyte borrowing route.

This is explicitly post-publication method development.  The source relation
is learned from experimental conductivity records spanning previously measured
lithium salts.  LiAsF6 is absent from all source records and is evaluated as a
complete external salt system.  Exact target formulations used for anchoring
are excluded wholesale from scoring.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

from common import RESULTS, ensure_output_dirs
from mixture_response_transfer_common import (
    CHEMISTRY_FEATURE_DIM,
    STATE_FEATURE_NAMES,
    conductivity_records,
    fit_shrinkage_adapter,
    fit_source_forest,
    formula_signature,
    load_json_records,
    maximin_anchors,
    mixture_features,
    nonanchor_test_indices,
    regression_metrics,
    response_target,
    salt_identity,
    sha256,
    source_predict,
    stable_seed,
)


HERE = Path(__file__).resolve().parent
DESIGN_PATH = HERE / "bamboomixer_response_transfer_design.json"
DEFAULT_DATA_DIR = HERE / "external_data" / "bamboomixer_response_transfer"
PREFIX = "bamboomixer_response_transfer"


def source_contains_salt(record: dict, salt: str) -> bool:
    return salt in {str(component["name"]) for component in record["salts"]}


def external_scope_indices(
    source_records: list[dict],
) -> dict[str, np.ndarray]:
    salts = np.asarray([salt_identity(record) for record in source_records])
    all_indices = np.arange(len(source_records))
    scopes = {
        "all_source_salts": all_indices,
        "state_only": all_indices,
        "chemistry_permuted": all_indices,
        "without_LiPF6": np.asarray(
            [
                index
                for index, record in enumerate(source_records)
                if not source_contains_salt(record, "LiPF6")
            ],
            dtype=int,
        ),
        "LiPF6_only": np.flatnonzero(salts == "LiPF6"),
        "LiBOB_wrong_salt_control": np.flatnonzero(salts == "LiBOB"),
        "LiBF4_fluorinated_control": np.flatnonzero(salts == "LiBF4"),
    }
    if any(len(indices) < 100 for indices in scopes.values()):
        raise AssertionError("A declared source scope became too small")
    return scopes


def fit_external_predictions(
    source_records: list[dict],
    x_source: np.ndarray,
    y_source: np.ndarray,
    x_target: np.ndarray,
    *,
    seeds: list[int],
    n_estimators: int,
) -> tuple[pd.DataFrame, dict[str, np.ndarray]]:
    scopes = external_scope_indices(source_records)
    seed_rows: list[dict[str, Any]] = []
    ensemble: dict[str, list[np.ndarray]] = {scope: [] for scope in scopes}
    for scope, indices in scopes.items():
        for seed in seeds:
            state_only = scope == "state_only"
            permutation = None
            if scope == "chemistry_permuted":
                permutation = np.random.default_rng(
                    stable_seed("chemistry-permutation", seed)
                ).permutation(len(indices))
            model = fit_source_forest(
                x_source[indices],
                y_source[indices],
                seed=seed,
                n_estimators=n_estimators,
                state_only=state_only,
                chemistry_permutation=permutation,
            )
            prediction = source_predict(
                model,
                x_target,
                state_only=state_only,
            )
            ensemble[scope].append(prediction)
            seed_rows.append(
                {
                    "scope": scope,
                    "seed": seed,
                    "source_rows": len(indices),
                    "prediction_mean": float(prediction.mean()),
                    "prediction_sd": float(prediction.std(ddof=1)),
                }
            )
    mean_predictions = {
        scope: np.mean(np.vstack(values), axis=0)
        for scope, values in ensemble.items()
    }
    return pd.DataFrame(seed_rows), mean_predictions


def prediction_table(
    target_records: list[dict],
    y_target: np.ndarray,
    predictions: dict[str, np.ndarray],
) -> pd.DataFrame:
    groups = [formula_signature(record) for record in target_records]
    rows: list[dict[str, Any]] = []
    for scope, values in predictions.items():
        for index, prediction in enumerate(values):
            rows.append(
                {
                    "target_row": index,
                    "formula_group": groups[index],
                    "scope": scope,
                    "y_log10_conductivity": float(y_target[index]),
                    "prediction_log10_conductivity": float(prediction),
                    "y_conductivity": float(10.0 ** y_target[index]),
                    "prediction_conductivity": float(10.0**prediction),
                }
            )
    return pd.DataFrame(rows)


def metric_table(
    y_target: np.ndarray,
    predictions: dict[str, np.ndarray],
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"scope": scope, **regression_metrics(y_target, prediction)}
            for scope, prediction in predictions.items()
        ]
    ).sort_values("scope")


def bootstrap_external_contrasts(
    y_target: np.ndarray,
    predictions: dict[str, np.ndarray],
    formula_groups: np.ndarray,
    *,
    repetitions: int,
    seed: int,
) -> pd.DataFrame:
    groups = np.asarray(formula_groups).astype(str)
    unique_groups = np.asarray(sorted(set(groups)))
    members = {group: np.flatnonzero(groups == group) for group in unique_groups}
    rng = np.random.default_rng(seed)
    full = predictions["all_source_salts"]
    comparators = [
        "state_only",
        "chemistry_permuted",
        "without_LiPF6",
        "LiPF6_only",
        "LiBOB_wrong_salt_control",
        "LiBF4_fluorinated_control",
    ]
    rows = []
    for repetition in range(repetitions):
        sampled = rng.choice(unique_groups, size=len(unique_groups), replace=True)
        indices = np.concatenate([members[group] for group in sampled])
        full_metrics = regression_metrics(y_target[indices], full[indices])
        for comparator in comparators:
            control_metrics = regression_metrics(
                y_target[indices],
                predictions[comparator][indices],
            )
            rows.append(
                {
                    "repetition": repetition,
                    "comparator": comparator,
                    "relative_log_rmse_gain": (
                        1.0
                        - full_metrics["log_rmse"] / control_metrics["log_rmse"]
                    ),
                    "spearman_gain": (
                        full_metrics["spearman"] - control_metrics["spearman"]
                    ),
                    "raw_r2_gain": full_metrics["raw_r2"]
                    - control_metrics["raw_r2"],
                }
            )
    return pd.DataFrame(rows)


def compact_target_space(x_target: np.ndarray, components: int = 12) -> np.ndarray:
    chemistry = StandardScaler().fit_transform(
        x_target[:, :CHEMISTRY_FEATURE_DIM]
    )
    n_components = min(components, len(x_target) - 1, chemistry.shape[1])
    reduced = PCA(n_components=n_components, random_state=0).fit_transform(chemistry)
    state = StandardScaler().fit_transform(
        x_target[:, CHEMISTRY_FEATURE_DIM:]
    )
    return np.column_stack([reduced, state])


def anchor_metrics(
    x_target: np.ndarray,
    y_target: np.ndarray,
    formula_groups: np.ndarray,
    source_prediction: np.ndarray,
    *,
    budgets: list[int],
    draws: int,
    alpha: float,
) -> pd.DataFrame:
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
    rows: list[dict[str, Any]] = []
    for budget in budgets:
        for draw in range(draws):
            anchors = maximin_anchors(
                compact,
                formula_groups,
                budget=budget,
                start_index=stable_seed("anchor", budget, draw),
            )
            test = nonanchor_test_indices(formula_groups, anchors)
            adapter = fit_shrinkage_adapter(
                source_prediction[anchors],
                state[anchors],
                y_target[anchors],
                alpha=alpha,
            )
            adapted = adapter.predict(source_prediction[test], state[test])
            if budget == 1:
                target_only = np.full(len(test), float(y_target[anchors[0]]))
            else:
                target_model = Ridge(alpha=10.0)
                target_model.fit(compact[anchors], y_target[anchors])
                target_only = target_model.predict(compact[test])
            predictions = {
                "source_frozen": source_prediction[test],
                "source_shrinkage_adapter": adapted,
                "target_only_ridge": target_only,
                "anchor_constant": np.full(
                    len(test),
                    float(y_target[anchors].mean()),
                ),
            }
            anchor_groups = set(formula_groups[anchors].astype(str))
            if anchor_groups.intersection(formula_groups[test].astype(str)):
                raise AssertionError("Anchor formulation leakage")
            for model, prediction in predictions.items():
                rows.append(
                    {
                        "anchor_budget": budget,
                        "draw": draw,
                        "model": model,
                        "n_anchor_rows": len(anchors),
                        "n_anchor_formulations": len(anchor_groups),
                        "n_test_rows": len(test),
                        "n_test_formulations": len(
                            set(formula_groups[test].astype(str))
                        ),
                        "anchor_formula_groups": json.dumps(
                            sorted(anchor_groups),
                            separators=(",", ":"),
                        ),
                        **regression_metrics(y_target[test], prediction),
                    }
                )
    return pd.DataFrame(rows)


def salt_exclusion_portfolio(
    source_records: list[dict],
    x_source: np.ndarray,
    y_source: np.ndarray,
    *,
    minimum_rows: int,
    seeds: list[int],
    n_estimators: int,
    quick: bool,
) -> pd.DataFrame:
    exact_salts = np.asarray([salt_identity(record) for record in source_records])
    counts = Counter(exact_salts)
    eligible = [
        salt
        for salt, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        if "+" not in salt and count >= minimum_rows
    ]
    if quick:
        eligible = eligible[:4]
    rows = []
    for target_salt in eligible:
        target = np.flatnonzero(exact_salts == target_salt)
        train = np.asarray(
            [
                index
                for index, record in enumerate(source_records)
                if not source_contains_salt(record, target_salt)
            ],
            dtype=int,
        )
        for state_only in (False, True):
            seed_predictions = []
            for seed in seeds:
                model = fit_source_forest(
                    x_source[train],
                    y_source[train],
                    seed=stable_seed("portfolio", target_salt, seed, state_only),
                    n_estimators=n_estimators,
                    state_only=state_only,
                )
                seed_predictions.append(
                    source_predict(
                        model,
                        x_source[target],
                        state_only=state_only,
                    )
                )
            prediction = np.mean(np.vstack(seed_predictions), axis=0)
            rows.append(
                {
                    "target_salt": target_salt,
                    "target_rows": len(target),
                    "source_rows": len(train),
                    "model": "state_only" if state_only else "full_mixture",
                    **regression_metrics(y_source[target], prediction),
                }
            )
    return pd.DataFrame(rows)


def quantile_interval(values: pd.Series) -> list[float]:
    return [
        float(values.quantile(0.025)),
        float(values.quantile(0.975)),
    ]


def make_summary(
    design: dict,
    source_records: list[dict],
    target_records: list[dict],
    external_metrics: pd.DataFrame,
    bootstrap: pd.DataFrame,
    anchors: pd.DataFrame,
    portfolio: pd.DataFrame,
) -> dict:
    by_scope = external_metrics.set_index("scope")
    full = by_scope.loc["all_source_salts"]
    primary_anchor = int(design["evaluation"]["primary_anchor_budget"])
    anchor_primary = anchors[anchors["anchor_budget"] == primary_anchor]
    anchor_macro = (
        anchor_primary.groupby("model", sort=True)[
            ["log_rmse", "spearman", "raw_r2"]
        ]
        .mean()
        .to_dict(orient="index")
    )
    bootstrap_summary = {}
    for comparator, group in bootstrap.groupby("comparator", sort=True):
        bootstrap_summary[comparator] = {
            "relative_log_rmse_gain_mean": float(
                group["relative_log_rmse_gain"].mean()
            ),
            "relative_log_rmse_gain_ci95": quantile_interval(
                group["relative_log_rmse_gain"]
            ),
            "spearman_gain_mean": float(group["spearman_gain"].mean()),
            "spearman_gain_ci95": quantile_interval(group["spearman_gain"]),
            "raw_r2_gain_mean": float(group["raw_r2_gain"].mean()),
            "raw_r2_gain_ci95": quantile_interval(group["raw_r2_gain"]),
        }
    portfolio_pivot = portfolio.pivot(
        index="target_salt",
        columns="model",
        values=["log_rmse", "spearman"],
    )
    portfolio_positive = 0
    for target_salt in portfolio_pivot.index:
        if (
            portfolio_pivot.loc[target_salt, ("log_rmse", "full_mixture")]
            < portfolio_pivot.loc[target_salt, ("log_rmse", "state_only")]
            and portfolio_pivot.loc[target_salt, ("spearman", "full_mixture")]
            > portfolio_pivot.loc[target_salt, ("spearman", "state_only")]
        ):
            portfolio_positive += 1
    return {
        "status": "complete-method-development",
        "design_sha256": sha256(DESIGN_PATH),
        "source_rows": len(source_records),
        "source_salts": len(set(map(salt_identity, source_records))),
        "target_rows": len(target_records),
        "target_exact_formulations": len(
            set(map(formula_signature, target_records))
        ),
        "external_zero_shot": {
            "full_mixture": {
                key: float(full[key])
                for key in (
                    "log_rmse",
                    "log_r2",
                    "raw_rmse",
                    "raw_r2",
                    "spearman",
                )
            },
            "contrasts": bootstrap_summary,
        },
        "five_anchor_macro": anchor_macro,
        "salt_exclusion_portfolio": {
            "targets": int(portfolio["target_salt"].nunique()),
            "full_beats_state_on_rmse_and_rank": int(portfolio_positive),
        },
        "claim_guard": design["claim_guard"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()
    ensure_output_dirs()
    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    source_path = args.data_dir / "bamboomixer_original_data.json"
    target_path = args.data_dir / "LiAsF6_conductivity.json"
    if sha256(source_path) != design["sources"]["source_sha256"]:
        raise RuntimeError("Source data hash mismatch")
    if sha256(target_path) != design["sources"]["target_sha256"]:
        raise RuntimeError("Target data hash mismatch")

    source_records = conductivity_records(load_json_records(source_path))
    target_records = conductivity_records(load_json_records(target_path))
    if len(source_records) != int(design["eligibility"]["source_expected_rows"]):
        raise AssertionError("Source conductivity row count changed")
    if len(target_records) != int(design["eligibility"]["target_expected_rows"]):
        raise AssertionError("Target conductivity row count changed")
    if any(source_contains_salt(record, "LiAsF6") for record in source_records):
        raise AssertionError("LiAsF6 leaked into source records")

    x_source = mixture_features(source_records)
    x_target = mixture_features(target_records)
    y_source = response_target(source_records)
    y_target = response_target(target_records)
    configured = design["models"]["source_forest"]
    seeds = [int(value) for value in configured["seeds"]]
    n_estimators = int(configured["n_estimators"])
    bootstrap_repetitions = int(
        design["evaluation"]["group_bootstrap_repetitions"]
    )
    anchor_draws = int(design["evaluation"]["coverage_anchor_draws"])
    if args.quick:
        seeds = seeds[:1]
        n_estimators = 80
        bootstrap_repetitions = 100
        anchor_draws = 10

    seed_audit, external_predictions = fit_external_predictions(
        source_records,
        x_source,
        y_source,
        x_target,
        seeds=seeds,
        n_estimators=n_estimators,
    )
    predictions = prediction_table(
        target_records,
        y_target,
        external_predictions,
    )
    external_metrics = metric_table(y_target, external_predictions)
    formula_groups = np.asarray(
        [formula_signature(record) for record in target_records]
    )
    bootstrap = bootstrap_external_contrasts(
        y_target,
        external_predictions,
        formula_groups,
        repetitions=bootstrap_repetitions,
        seed=stable_seed("external-bootstrap", design["evaluation"]["primary_external_target"]),
    )
    anchors = anchor_metrics(
        x_target,
        y_target,
        formula_groups,
        external_predictions["all_source_salts"],
        budgets=[int(value) for value in design["evaluation"]["anchor_budgets"]],
        draws=anchor_draws,
        alpha=float(design["models"]["few_shot_adapter"]["alpha"]),
    )
    portfolio = salt_exclusion_portfolio(
        source_records,
        x_source,
        y_source,
        minimum_rows=int(
            design["evaluation"]["salt_exclusion_portfolio_minimum_rows"]
        ),
        seeds=seeds,
        n_estimators=n_estimators,
        quick=args.quick,
    )
    summary = make_summary(
        design,
        source_records,
        target_records,
        external_metrics,
        bootstrap,
        anchors,
        portfolio,
    )
    summary["mode"] = "quick" if args.quick else "formal"

    outputs = {
        "seed_audit": seed_audit,
        "external_predictions": predictions,
        "external_metrics": external_metrics,
        "external_group_bootstrap": bootstrap,
        "anchor_metrics": anchors,
        "salt_portfolio": portfolio,
    }
    for name, frame in outputs.items():
        frame.to_csv(
            RESULTS / f"{PREFIX}_{name}.csv",
            index=False,
        )
    (RESULTS / f"{PREFIX}_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

