"""Fit and freeze Stage 1 source features while Stage 2 outcomes remain sealed."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.metrics import r2_score


ROOT = Path(__file__).resolve().parents[1]
STAGE1_DIR = ROOT / "analysis" / "results" / "multistage_battery_stage1"
SOURCE_TABLE = STAGE1_DIR / "stage1_source_table.csv"
SOURCE_AUDIT = STAGE1_DIR / "STAGE1_DATA_QUALITY_AUDIT.json"
META = ROOT / "analysis" / "results" / "multistage_battery_file_map" / "experiments_meta.csv"
MAP = ROOT / "analysis" / "results" / "multistage_battery_file_map" / "archive_file_stage_map.csv"
DESIGN = ROOT / "analysis" / "multistage_battery_cca_v2_design.json"
OUT = ROOT / "analysis" / "results" / "multistage_battery_stage1_source_freeze"
NUMERIC = ["amb_temp_tp", "soc_max_tp", "dod_tp", "c_ch_tp", "c_dch_tp", "m_0", "R_1khz_0", "U_0"]
CATEGORICAL = ["lab", "sampling"]
CONDITIONS = {"k": ["amb_temp_tp", "soc_max_tp"], "z": ["amb_temp_tp", "soc_max_tp", "dod_tp", "c_ch_tp", "c_dch_tp"]}
SEED = 20260720


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_group(row: pd.Series) -> str:
    columns = CONDITIONS[row["type"]]
    return row["type"] + "|" + "|".join(format(float(row[column]), ".12g") for column in columns)


def group_hash(group: str) -> str:
    return hashlib.sha256(group.encode("utf-8")).hexdigest()


def feature_spec(stage1: pd.DataFrame, stage2: pd.DataFrame, aging_type: str) -> dict:
    train = stage1.loc[stage1["type"].eq(aging_type)]
    combined = pd.concat([train, stage2.loc[stage2["type"].eq(aging_type)]], ignore_index=True)
    medians = {column: float(train[column].median()) for column in NUMERIC}
    ranges = {column: float(train[column].max() - train[column].min()) for column in NUMERIC}
    retained_numeric = [column for column in NUMERIC if ranges[column] > 0]
    categories = {
        column: sorted(str(value) for value in combined[column].dropna().unique())
        for column in CATEGORICAL
    }
    return {
        "aging_type": aging_type,
        "numeric_columns": retained_numeric,
        "dropped_zero_range_numeric": [column for column in NUMERIC if column not in retained_numeric],
        "numeric_medians": medians,
        "numeric_ranges": ranges,
        "categorical_levels": categories,
    }


def transform(frame: pd.DataFrame, spec: dict, exclude_numeric: set[str] | None = None) -> tuple[np.ndarray, list[str]]:
    exclude_numeric = exclude_numeric or set()
    arrays: list[np.ndarray] = []
    names: list[str] = []
    for column in spec["numeric_columns"]:
        if column in exclude_numeric:
            continue
        values = frame[column].to_numpy(dtype=float)
        scaled = (values - spec["numeric_medians"][column]) / spec["numeric_ranges"][column]
        arrays.append(scaled[:, None])
        names.append(column)
    for column, levels in spec["categorical_levels"].items():
        values = frame[column].astype(str).to_numpy()
        for level in levels:
            arrays.append((values == level).astype(float)[:, None])
            names.append(f"{column}={level}")
    return np.hstack(arrays), names


def new_model() -> ExtraTreesRegressor:
    return ExtraTreesRegressor(
        n_estimators=500,
        min_samples_leaf=2,
        max_features=1.0,
        bootstrap=False,
        random_state=SEED,
        n_jobs=-1,
    )


def tree_std(model: ExtraTreesRegressor, matrix: np.ndarray) -> np.ndarray:
    predictions = np.vstack([tree.predict(matrix) for tree in model.estimators_])
    return predictions.std(axis=0, ddof=1)


def cross_fit(frame: pd.DataFrame, matrix: np.ndarray, target: str) -> tuple[np.ndarray, np.ndarray]:
    predictions = np.full(len(frame), np.nan)
    uncertainty = np.full(len(frame), np.nan)
    groups = frame["condition_group"].to_numpy()
    y = frame[target].to_numpy(dtype=float)
    for heldout in sorted(set(groups)):
        test = groups == heldout
        train = ~test
        model = new_model()
        model.fit(matrix[train], y[train])
        predictions[test] = model.predict(matrix[test])
        uncertainty[test] = tree_std(model, matrix[test])
    return predictions, uncertainty


def condition_scaler(stage1: pd.DataFrame, aging_type: str) -> dict:
    columns = CONDITIONS[aging_type]
    groups = stage1.loc[stage1["type"].eq(aging_type), ["condition_group", *columns]].drop_duplicates()
    minima = groups[columns].min()
    ranges = groups[columns].max() - minima
    retained = [column for column in columns if ranges[column] > 0]
    return {
        "columns": retained,
        "minima": {column: float(minima[column]) for column in retained},
        "ranges": {column: float(ranges[column]) for column in retained},
    }


def scaled_conditions(frame: pd.DataFrame, scaler: dict) -> np.ndarray:
    columns = scaler["columns"]
    matrix = frame[columns].to_numpy(dtype=float)
    minima = np.array([scaler["minima"][column] for column in columns])
    ranges = np.array([scaler["ranges"][column] for column in columns])
    return (matrix - minima) / ranges


def nearest_distance(query: np.ndarray, reference: np.ndarray) -> np.ndarray:
    return np.sqrt(((query[:, None, :] - reference[None, :, :]) ** 2).sum(axis=2)).min(axis=1)


def maximin_training_groups(groups: pd.DataFrame, heldout: str, budget: int, scaler: dict) -> list[str]:
    available = groups.loc[~groups["condition_group"].eq(heldout)].copy()
    available["tie_hash"] = available["condition_group"].map(group_hash)
    coordinates = {row["condition_group"]: vector for (_, row), vector in zip(available.iterrows(), scaled_conditions(available, scaler))}
    first = available.sort_values("tie_hash").iloc[0]["condition_group"]
    selected = [first]
    while len(selected) < budget:
        candidates = [group for group in coordinates if group not in selected]
        scores = []
        for group in candidates:
            minimum = min(float(np.linalg.norm(coordinates[group] - coordinates[chosen])) for chosen in selected)
            scores.append((minimum, group_hash(group), group))
        best_distance = max(score[0] for score in scores)
        tied = [score for score in scores if np.isclose(score[0], best_distance, rtol=0, atol=1e-12)]
        selected.append(min(tied, key=lambda score: score[1])[2])
    return selected


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    source_audit = json.loads(SOURCE_AUDIT.read_text(encoding="utf-8"))
    if source_audit["status"] != "verified-stage1-source-ready":
        raise AssertionError("Stage 1 source table did not pass data-quality audit")
    source_all = pd.read_csv(SOURCE_TABLE, dtype={"stage": str, "serial_internal": str, "serial": str})
    stage1 = source_all.loc[source_all["status"].eq("extracted-stage1")].copy()
    meta = pd.read_csv(META, dtype={"stage": str, "serial_internal": str, "serial": str})
    stage2 = meta.loc[meta["stage"].eq("2")].copy()
    stage2["condition_group"] = stage2.apply(canonical_group, axis=1)
    with MAP.open("r", encoding="utf-8-sig", newline="") as handle:
        stage2_map = pd.DataFrame([row for row in csv.DictReader(handle) if row["stage"] == "2"])
    stage2 = stage2.merge(
        stage2_map[["file_id", "serial_internal", "serial", "stage", "mapping_method", "metadata_conflict_flags"]],
        on=["serial_internal", "serial", "stage"], how="left", validate="one_to_one",
    )
    if stage2["file_id"].isna().any() or len(stage2) != 138:
        raise AssertionError("Stage 2 outcome-free metadata did not join to all 138 mapped archives")

    oof_parts: list[pd.DataFrame] = []
    stage2_parts: list[pd.DataFrame] = []
    model_summaries: dict[str, dict] = {}
    split_plan: dict[str, dict] = {}
    preprocessing: dict[str, dict] = {}
    group_tables: dict[str, pd.DataFrame] = {}
    condition_scalers: dict[str, dict] = {}
    for aging_type in ("k", "z"):
        train = stage1.loc[stage1["type"].eq(aging_type)].copy().reset_index(drop=True)
        target = stage2.loc[stage2["type"].eq(aging_type)].copy().reset_index(drop=True)
        spec = feature_spec(stage1, stage2, aging_type)
        x_train, feature_names = transform(train, spec)
        x_target, observed_names = transform(target, spec)
        if feature_names != observed_names:
            raise AssertionError("Stage 1 and Stage 2 feature columns differ")
        oof_prediction, oof_tree_std = cross_fit(train, x_train, "q_rel_end_percent")
        residual_sd = float(np.std(train["q_rel_end_percent"].to_numpy() - oof_prediction, ddof=1))
        if not np.isfinite(residual_sd) or residual_sd <= 0:
            raise AssertionError(f"invalid Stage 1 residual SD for type {aging_type}")
        final_model = new_model().fit(x_train, train["q_rel_end_percent"].to_numpy(dtype=float))
        source_prediction = final_model.predict(x_target)
        source_uncertainty = np.clip(tree_std(final_model, x_target) / residual_sd, 0, 5)
        joblib.dump(final_model, OUT / f"stage1_{aging_type}_retention_extratrees.joblib", compress=3)

        wrong_x_train, wrong_names = transform(train, spec, exclude_numeric={"m_0"})
        wrong_x_target, wrong_target_names = transform(target, spec, exclude_numeric={"m_0"})
        if wrong_names != wrong_target_names:
            raise AssertionError("wrong-property feature columns differ")
        wrong_model = new_model().fit(wrong_x_train, train["m_0"].to_numpy(dtype=float))
        wrong_prediction = wrong_model.predict(wrong_x_target)
        joblib.dump(wrong_model, OUT / f"stage1_{aging_type}_mass_wrong_property_extratrees.joblib", compress=3)

        scaler = condition_scaler(stage1, aging_type)
        source_groups = train[["condition_group", *CONDITIONS[aging_type]]].drop_duplicates()
        source_coordinates = scaled_conditions(source_groups, scaler)
        source_distance = nearest_distance(scaled_conditions(target, scaler), source_coordinates)
        labs = set(train["lab"].astype(str))
        sampling = set(train["sampling"].astype(str))
        provenance = np.array([
            1.0 if str(row.lab) in labs and str(row.sampling) in sampling else 0.5
            for row in target.itertuples()
        ])
        oof_mean = float(np.mean(oof_prediction))

        oof = train[["serial_internal", "serial", "condition_group", "lab", "type", "tp", "cell", "q_rel_end_percent"]].copy()
        oof["source_oof_prediction"] = oof_prediction
        oof["source_oof_tree_std"] = oof_tree_std
        oof["source_oof_residual"] = oof["q_rel_end_percent"] - oof["source_oof_prediction"]
        oof_parts.append(oof)

        frozen = target[["file_id", "serial_internal", "serial", "condition_group", "lab", "type", "tp", "cell", "sampling"]].copy()
        frozen["source_prediction"] = source_prediction
        frozen["source_prediction_center"] = oof_mean
        frozen["source_prediction_centered"] = source_prediction - oof_mean
        frozen["source_uncertainty_normalized"] = source_uncertainty
        frozen["source_distance"] = source_distance
        frozen["provenance_compatibility"] = provenance
        frozen["wrong_property_mass_prediction"] = wrong_prediction
        stage2_parts.append(frozen)

        groups = target[["condition_group", *CONDITIONS[aging_type]]].drop_duplicates().sort_values("condition_group")
        group_tables[aging_type] = groups
        condition_scalers[aging_type] = scaler
        model_summaries[aging_type] = {
            "stage1_cells": len(train),
            "stage1_condition_groups": int(train["condition_group"].nunique()),
            "stage2_cells_predicted_without_outcomes": len(target),
            "stage2_condition_groups": int(target["condition_group"].nunique()),
            "source_oof_r2": float(r2_score(train["q_rel_end_percent"], oof_prediction)),
            "source_oof_rmse": float(np.sqrt(np.mean((train["q_rel_end_percent"].to_numpy() - oof_prediction) ** 2))),
            "source_oof_residual_sd": residual_sd,
            "source_oof_prediction_mean": oof_mean,
            "feature_names": feature_names,
            "wrong_property_feature_names": wrong_names,
            "condition_scaler": scaler,
        }
        preprocessing[aging_type] = spec

    for heldout in sorted(stage2["condition_group"].unique()):
        heldout_type = heldout.split("|", 1)[0]
        selected_by_type = {
            "k": maximin_training_groups(group_tables["k"], heldout, 4, condition_scalers["k"]),
            "z": maximin_training_groups(group_tables["z"], heldout, 6, condition_scalers["z"]),
        }
        selected_all = selected_by_type["k"] + selected_by_type["z"]
        split_plan[heldout] = {
            "aging_type": heldout_type,
            "heldout_group": heldout,
            "target_training_groups_by_type": selected_by_type,
            "target_training_groups": selected_all,
            "target_label_budget_groups": 10,
            "target_label_budget_by_type": {"k": 4, "z": 6},
        }

    oof_table = pd.concat(oof_parts, ignore_index=True).sort_values(["type", "condition_group", "serial"])
    frozen_table = pd.concat(stage2_parts, ignore_index=True).sort_values(["type", "condition_group", "serial"])
    oof_path = OUT / "stage1_group_cross_fitted_predictions.csv"
    frozen_path = OUT / "stage2_outcome_free_source_features.csv"
    splits_path = OUT / "stage2_outer_split_plan.json"
    preprocessing_path = OUT / "preprocessing_spec.json"
    oof_table.to_csv(oof_path, index=False, lineterminator="\n")
    frozen_table.to_csv(frozen_path, index=False, lineterminator="\n")
    splits_path.write_text(json.dumps(split_plan, indent=2) + "\n", encoding="utf-8")
    preprocessing_path.write_text(json.dumps(preprocessing, indent=2) + "\n", encoding="utf-8")

    summary = {
        "status": "verified-stage1-source-and-stage2-outcome-free-features-frozen",
        "stage1_numeric_outcomes_used": True,
        "stage2_numeric_outcomes_opened": False,
        "stage2_cells": len(frozen_table),
        "stage2_condition_groups": len(split_plan),
        "outer_split_count": len(split_plan),
        "model_summaries": model_summaries,
        "source_table_sha256": sha256(SOURCE_TABLE),
        "source_audit_sha256": sha256(SOURCE_AUDIT),
        "oof_table_sha256": sha256(oof_path),
        "stage2_source_features_sha256": sha256(frozen_path),
        "outer_split_plan_sha256": sha256(splits_path),
        "preprocessing_spec_sha256": sha256(preprocessing_path),
        "model_sha256": {
            path.name: sha256(path) for path in sorted(OUT.glob("*.joblib"))
        },
        "claim_guard": "These are source-only models and outcome-free target features. They generate the locked borrowing prior but provide no evidence that borrowing improves Stage 2 prediction.",
        "errors": [],
    }
    summary_path = OUT / "STAGE1_SOURCE_FREEZE.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
