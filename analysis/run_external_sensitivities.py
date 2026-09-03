"""Post-confirmation budget and interpolation sensitivities for the primary edge.

These analyses were specified after seeing the fixed n=30 rolling-time result.
They therefore diagnose where borrowing works; they do not replace or redefine
the primary external decision.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from common import RESULTS, composition_features, ensure_output_dirs, metrics
from run_external_confirmation import (
    DESIGN_PATH,
    evaluate,
    load_birdshot_target,
    rolling_splits,
    summarize_predictions,
    training_samples,
)
from run_knowledge_map import (
    load_task,
    source_model,
    stable_offset,
    target_ridge,
)

MAP_DESIGN_PATH = DESIGN_PATH.with_name("knowledge_map_design.json")
BUDGETS = [8, 15, 30, 45, 60, 75]
PROCESS_COLUMNS = [
    "cold_work_percent_reduction",
    "holding_time_h",
    "grain_size_um",
]


def primary_inputs():
    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    map_design = json.loads(MAP_DESIGN_PATH.read_text(encoding="utf-8"))
    primary = design["primary_hypothesis"]
    target = load_birdshot_target(primary["target"], design["targets"][primary["target"]])
    source = load_task(primary["source"], map_design["tasks"][primary["source"]])
    source.X = composition_features(source.frame["material_key"].tolist()).astype(np.float32)
    overlap = set(source.frame["material_key"]) & set(target.frame["material_key"])
    if overlap:
        raise AssertionError(f"Unexpected source-target composition overlap: {len(overlap)}")
    model = source_model(source, int(design["seed"])).fit(source.X, source.frame["value"].to_numpy(float))
    return design, primary, target, model


def rolling_budget_sensitivity(design, primary, target, model) -> pd.DataFrame:
    splits = rolling_splits(target, design)
    feature = model.predict(np.asarray(target.X))
    rows = []
    for budget in BUDGETS:
        samples = {
            fold_id: training_samples(
                split["development"], budget, 60,
                int(design["seed"]) + stable_offset(f"budget:{budget}:{fold_id}") % 1_000_000,
            )
            for fold_id, split in splits.items()
        }
        _, predictions = evaluate(
            target, feature, samples, splits, target_ridge(), "ridge-primary",
            primary["target"], primary["source"],
        )
        item = summarize_predictions(predictions, int(design["seed"]) + budget, 2000)
        item.update({
            "budget": budget,
            "analysis_status": "post-confirmation-sensitivity",
            "estimand": "rolling-future-campaign-year",
        })
        rows.append(item)
    return pd.DataFrame(rows)


def interpolation_budget_sensitivity(design, primary, target, model) -> tuple[pd.DataFrame, pd.DataFrame]:
    # Repeated observations of the same composition are aggregated before any
    # split so an exact composition can never straddle train and test.
    frame = (
        target.frame.groupby("material_key", as_index=False)
        .agg(value=("value", "median"))
        .sort_values("material_key")
        .reset_index(drop=True)
    )
    x = composition_features(frame["material_key"].tolist()).astype(np.float32)
    y = frame["value"].to_numpy(float)
    feature = model.predict(x)
    rows = []
    for budget in BUDGETS:
        for repeat in range(200):
            rng = np.random.default_rng(int(design["seed"]) + 10_000 * budget + repeat)
            test = np.sort(rng.choice(len(frame), size=45, replace=False))
            pool = np.setdiff1d(np.arange(len(frame)), test)
            train = np.sort(rng.choice(pool, size=budget, replace=False))
            baseline = clone(target_ridge()).fit(x[train], y[train])
            augmented = clone(target_ridge()).fit(
                np.column_stack([x[train], feature[train]]), y[train]
            )
            base_prediction = baseline.predict(x[test])
            aug_prediction = augmented.predict(np.column_stack([x[test], feature[test]]))
            result = metrics(y[test], base_prediction, aug_prediction)
            rows.append({
                "budget": budget,
                "repeat": repeat,
                "test_n": len(test),
                "base_r2": result["base_r2"],
                "aug_r2": result["aug_r2"],
                "delta_r2": result["delta_r2"],
                "base_rmse": result["base_rmse"],
                "aug_rmse": result["aug_rmse"],
                "relative_rmse_improvement": result["delta_rmse"] / result["base_rmse"],
            })
    repeats = pd.DataFrame(rows)
    summary_rows = []
    for budget, group in repeats.groupby("budget"):
        summary_rows.append({
            "budget": budget,
            "base_r2_mean": group["base_r2"].mean(),
            "aug_r2_mean": group["aug_r2"].mean(),
            "delta_r2_mean": group["delta_r2"].mean(),
            "base_rmse_mean": group["base_rmse"].mean(),
            "aug_rmse_mean": group["aug_rmse"].mean(),
            "relative_rmse_improvement_mean": group["relative_rmse_improvement"].mean(),
            "relative_rmse_repeat_q025": group["relative_rmse_improvement"].quantile(0.025),
            "relative_rmse_repeat_q975": group["relative_rmse_improvement"].quantile(0.975),
            "fraction_repeats_positive": (group["relative_rmse_improvement"] > 0).mean(),
            "analysis_status": "post-confirmation-sensitivity",
            "estimand": "independent-campaign-interpolation",
        })
    return repeats, pd.DataFrame(summary_rows)


def process_aware_rolling_sensitivity(design, primary, target, model) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Condition the target model on process variables available before testing.

    Year 1 contains no process fields. Imputation and missingness indicators
    therefore live inside the learner pipeline and are fit separately within
    each sampled training fold; no future-year value is used for preprocessing.
    ``cracked`` and campaign year are deliberately excluded.
    """
    composition = composition_features(target.frame["material_key"].tolist()).astype(np.float32)
    process = target.frame[PROCESS_COLUMNS].to_numpy(float)
    target.X = np.column_stack([composition, process])
    feature = model.predict(composition)
    splits = rolling_splits(target, design)
    inference = design["inference"]
    samples = {
        fold_id: training_samples(
            split["development"],
            int(inference["target_budget"]),
            int(inference["training_repeats"]),
            int(design["seed"]) + stable_offset(f"{primary['target']}:{fold_id}") % 1_000_000,
        )
        for fold_id, split in splits.items()
    }
    learner = make_pipeline(
        SimpleImputer(strategy="median", add_indicator=True, keep_empty_features=True),
        StandardScaler(),
        Ridge(alpha=10.0, solver="lsqr"),
    )
    repeats, predictions = evaluate(
        target,
        feature,
        samples,
        splits,
        learner,
        "ridge-process-aware-sensitivity",
        primary["target"],
        primary["source"],
    )
    summary = summarize_predictions(
        predictions,
        int(design["seed"]) + stable_offset("process-aware-bootstrap"),
        int(inference["bootstrap_replicates"]),
    )
    summary.update({
        "base_r2_repeat_mean": float(repeats["base_r2"].mean()),
        "aug_r2_repeat_mean": float(repeats["aug_r2"].mean()),
        "year1_to_year2_base_r2_mean": float(repeats.loc[repeats["fold"] == "year1_to_year2", "base_r2"].mean()),
        "year1_to_year2_aug_r2_mean": float(repeats.loc[repeats["fold"] == "year1_to_year2", "aug_r2"].mean()),
        "years1_2_to_year3_base_r2_mean": float(repeats.loc[repeats["fold"] == "years1_2_to_year3", "base_r2"].mean()),
        "years1_2_to_year3_aug_r2_mean": float(repeats.loc[repeats["fold"] == "years1_2_to_year3", "aug_r2"].mean()),
        "feature_set": "element-composition-plus-pretest-process",
        "process_columns": ";".join(PROCESS_COLUMNS),
        "excluded_columns": "campaign_year;cracked",
        "analysis_status": "post-confirmation-sensitivity",
    })
    audit_rows = []
    for year, group in target.frame.groupby("year"):
        for column in PROCESS_COLUMNS:
            audit_rows.append({
                "year": int(year),
                "process_feature": column,
                "n_rows": len(group),
                "n_observed": int(group[column].notna().sum()),
                "n_missing": int(group[column].isna().sum()),
            })
    return pd.DataFrame([summary]), pd.DataFrame(audit_rows)


def write_utility_summary(process_summary: pd.DataFrame, interpolation: pd.DataFrame) -> None:
    primary_edges = pd.read_csv(RESULTS / "external_confirmation_edges.csv")
    primary = primary_edges[
        (primary_edges["target"] == "birdshot_ys")
        & (primary_edges["source"] == "alloy_uts")
    ].iloc[0]
    process = process_summary.iloc[0]
    interpolation_n30 = interpolation[interpolation["budget"] == 30].iloc[0]
    output = {
        "analysis_status": "post-confirmation-absolute-utility-audit",
        "rolling_time_composition_only": {
            "relative_rmse_improvement": float(primary["relative_rmse_improvement_mean"]),
            "pooled_base_r2": float(primary["pooled_base_r2"]),
            "pooled_augmented_r2": float(primary["pooled_aug_r2"]),
        },
        "rolling_time_process_aware": {
            "relative_rmse_improvement": float(process["relative_rmse_improvement_mean"]),
            "relative_rmse_ci": [
                float(process["relative_rmse_ci_lo"]),
                float(process["relative_rmse_ci_hi"]),
            ],
            "pooled_base_r2": float(process["pooled_base_r2"]),
            "pooled_augmented_r2": float(process["pooled_aug_r2"]),
            "features": str(process["feature_set"]),
        },
        "same_campaign_interpolation_n30": {
            "base_r2_mean": float(interpolation_n30["base_r2_mean"]),
            "augmented_r2_mean": float(interpolation_n30["aug_r2_mean"]),
            "relative_rmse_improvement_mean": float(
                interpolation_n30["relative_rmse_improvement_mean"]
            ),
            "repeat_quantile_95": [
                float(interpolation_n30["relative_rmse_repeat_q025"]),
                float(interpolation_n30["relative_rmse_repeat_q975"]),
            ],
        },
        "rescue_claim_supported": False,
        "decision": (
            "Borrowing reduces rolling-time error and survives conditioning on available "
            "pre-test process variables, but rolling-time R2 remains negative. Same-campaign "
            "interpolation has positive absolute R2, yet its repeat-level effect interval "
            "crosses zero. The evidence supports selective error reduction, not practical "
            "rescue of the external target."
        ),
    }
    (RESULTS / "external_confirmation_utility_summary.json").write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf-8"
    )


def main() -> None:
    ensure_output_dirs()
    design, primary, target, model = primary_inputs()
    rolling = rolling_budget_sensitivity(design, primary, target, model)
    interpolation_repeats, interpolation = interpolation_budget_sensitivity(
        design, primary, target, model
    )
    process_summary, process_audit = process_aware_rolling_sensitivity(
        design, primary, target, model
    )
    rolling.to_csv(RESULTS / "external_confirmation_primary_budget_sensitivity.csv", index=False)
    interpolation_repeats.to_csv(
        RESULTS / "external_confirmation_interpolation_budget_repeats.csv", index=False
    )
    interpolation.to_csv(
        RESULTS / "external_confirmation_interpolation_budget_sensitivity.csv", index=False
    )
    process_summary.to_csv(
        RESULTS / "external_confirmation_process_sensitivity.csv", index=False
    )
    process_audit.to_csv(
        RESULTS / "external_confirmation_process_feature_audit.csv", index=False
    )
    write_utility_summary(process_summary, interpolation)
    print("Rolling-time budget sensitivity")
    print(rolling[[
        "budget", "base_rmse_mean", "aug_rmse_mean", "relative_rmse_improvement_mean",
        "relative_rmse_ci_lo", "relative_rmse_ci_hi", "effect_year1_to_year2",
        "effect_years1_2_to_year3",
    ]].to_string(index=False))
    print("\nInterpolation budget sensitivity")
    print(interpolation.to_string(index=False))
    print("\nProcess-aware rolling-time sensitivity")
    print(process_summary.to_string(index=False))


if __name__ == "__main__":
    main()
