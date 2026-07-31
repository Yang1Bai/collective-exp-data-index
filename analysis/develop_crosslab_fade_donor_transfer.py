#!/usr/bin/env python3
"""Donor-only development for transferable battery fade corrections.

This script never opens a recipient file. It compares candidate transfer
objects under leave-one-MATR-batch-out validation and writes the complete
candidate table so the final object can be frozen before recipient access.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


RESPONSE = [
    "log10_var_delta_qv",
    "log10_abs_min_delta_qv",
    "capacity_slope_2_100",
    "capacity_intercept_2_100",
    "qd100_over_qref",
    "ce_mean_10_100",
    "ce_std_10_100",
]
PROTOCOL = ["mean_charge_c_rate", "mean_discharge_c_rate"]
NORMALIZED_RESPONSE = [
    "log10_var_delta_qv_normalized",
    "log10_abs_min_delta_qv_normalized",
    "capacity_slope_over_qref",
    "capacity_intercept_over_qref",
    "qd100_over_qref",
    "ce_std_10_100",
]
OVERLAP_ROUTED_RESPONSE = [
    "capacity_slope_over_qref",
    "qd100_over_qref",
    "ce_std_10_100",
]
FEATURE_SETS = {
    "response": RESPONSE,
    "response_plus_protocol": RESPONSE + PROTOCOL,
    "normalized_response": NORMALIZED_RESPONSE,
    "normalized_response_plus_protocol": NORMALIZED_RESPONSE + PROTOCOL,
    "overlap_routed_response": OVERLAP_ROUTED_RESPONSE,
}
SEED = 20260729


def model(name: str):
    if name == "random_forest":
        return RandomForestRegressor(
            n_estimators=800, min_samples_leaf=2, max_features=0.8,
            random_state=SEED, n_jobs=-1
        )
    if name == "extra_trees":
        return ExtraTreesRegressor(
            n_estimators=800, min_samples_leaf=2, max_features=0.8,
            random_state=SEED, n_jobs=-1
        )
    if name == "hist_gradient_boosting":
        return HistGradientBoostingRegressor(
            max_iter=300, learning_rate=0.04, max_leaf_nodes=15,
            l2_regularization=1.0, random_state=SEED
        )
    if name == "ridge":
        return make_pipeline(StandardScaler(), Ridge(alpha=10.0))
    raise KeyError(name)


def robust_batch_normalize(train: pd.DataFrame, test: pd.DataFrame, columns: list[str]):
    """Unlabelled per-lab response alignment; no outcome values are used."""
    train_out, test_out = train[columns].copy(), test[columns].copy()
    for block in train["batch"].unique():
        mask = train["batch"] == block
        center = train.loc[mask, columns].median()
        scale = (train.loc[mask, columns].quantile(0.75)
                 - train.loc[mask, columns].quantile(0.25)).replace(0, 1.0)
        train_out.loc[mask] = (train.loc[mask, columns] - center) / scale
    center = test[columns].median()
    scale = (test[columns].quantile(0.75) - test[columns].quantile(0.25)).replace(0, 1.0)
    test_out = (test[columns] - center) / scale
    return train_out.to_numpy(float), test_out.to_numpy(float)


def evaluate(table: pd.DataFrame):
    y = np.log10(table["life"].to_numpy(float))
    own = table["own_log10_life"].to_numpy(float)
    rows, prediction_rows = [], []
    learners = ["random_forest", "extra_trees", "hist_gradient_boosting", "ridge"]
    for feature_name, columns in FEATURE_SETS.items():
        for alignment in ["absolute", "within_lab_robust"]:
            for target in ["absolute_log_life", "differential_correction"]:
                for learner in learners:
                    pred = np.full(len(table), np.nan)
                    for block in sorted(table["batch"].unique()):
                        test = table["batch"] == block
                        train = ~test
                        if alignment == "absolute":
                            X_train = table.loc[train, columns].to_numpy(float)
                            X_test = table.loc[test, columns].to_numpy(float)
                        else:
                            X_train, X_test = robust_batch_normalize(
                                table.loc[train], table.loc[test], columns
                            )
                        fit_y = y[train] if target == "absolute_log_life" else y[train] - own[train]
                        fitted = model(learner).fit(X_train, fit_y)
                        raw = fitted.predict(X_test)
                        pred[test] = raw if target == "absolute_log_life" else own[test] + raw
                    error = pred - y
                    row = {
                        "feature_set": feature_name,
                        "alignment": alignment,
                        "transfer_object": target,
                        "learner": learner,
                        "oof_spearman": float(spearmanr(pred, y).statistic),
                        "oof_rmse_log10_life": float(np.sqrt(np.mean(error**2))),
                        "oof_r2_log10_life": float(
                            1 - np.sum(error**2) / np.sum((y - y.mean())**2)
                        ),
                        "relative_rmse_gain_over_own_curve": float(
                            1 - np.sqrt(np.mean(error**2))
                            / np.sqrt(np.mean((own - y)**2))
                        ),
                    }
                    rows.append(row)
                    for index, value in enumerate(pred):
                        prediction_rows.append(
                            {
                                **{key: row[key] for key in [
                                    "feature_set", "alignment", "transfer_object", "learner"
                                ]},
                                "cell_id": table.iloc[index]["cell_id"],
                                "batch": table.iloc[index]["batch"],
                                "log10_life_true": y[index],
                                "own_curve_prediction": own[index],
                                "oof_prediction": value,
                            }
                        )
    results = pd.DataFrame(rows).sort_values(
        ["oof_spearman", "oof_rmse_log10_life"], ascending=[False, True]
    )
    return results, pd.DataFrame(prediction_rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--donor-table", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    table = pd.read_csv(args.donor_table)
    required = RESPONSE + NORMALIZED_RESPONSE + PROTOCOL + [
        "life", "own_log10_life", "batch", "cell_id", "censored"
    ]
    valid = table[required].notna().all(axis=1) & ~table["censored"].astype(bool)
    table = table.loc[valid].reset_index(drop=True)
    results, predictions = evaluate(table)
    results_path = args.out / "crosslab_fade_raw_donor_candidate_methods.csv"
    pred_path = args.out / "crosslab_fade_raw_donor_candidate_predictions.csv.gz"
    results.to_csv(results_path, index=False)
    predictions.to_csv(pred_path, index=False, compression="gzip")
    best = results.iloc[0].to_dict()
    summary = {
        "status": "donor-only-development-complete",
        "recipient_files_opened": False,
        "donor_cells": int(len(table)),
        "candidate_methods": int(len(results)),
        "selection_rule": (
            "highest leave-one-batch-out Spearman; ties within 0.01 choose lower "
            "RMSE, then simpler learner"
        ),
        "best_candidate": best,
        "gate_passes_oof_spearman_at_least_0_5": bool(best["oof_spearman"] >= 0.5),
    }
    (args.out / "crosslab_fade_raw_donor_method_development.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
