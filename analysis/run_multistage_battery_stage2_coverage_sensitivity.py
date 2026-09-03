"""Run the explicitly post-release 22-group battery coverage sensitivity.

The frozen 23-group primary test remains non-evaluable.  This script preserves
the frozen modeling and inferential machinery but never labels its output as a
confirmatory or preregistered success.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import r2_score

try:
    from analysis.freeze_multistage_battery_stage1_source import canonical_group, new_model, transform
except ModuleNotFoundError:
    from freeze_multistage_battery_stage1_source import canonical_group, new_model, transform


ROOT = Path(__file__).resolve().parents[1]
STAGE2_DIR = ROOT / "analysis" / "results" / "multistage_battery_stage2"
ENDPOINTS = STAGE2_DIR / "stage2_capacity_endpoints.csv"
RELEASE_AUDIT = STAGE2_DIR / "STAGE2_RELEASE_AUDIT.json"
META = ROOT / "analysis" / "results" / "multistage_battery_file_map" / "experiments_meta.csv"
FREEZE_DIR = ROOT / "analysis" / "results" / "multistage_battery_stage1_source_freeze"
SOURCE_FEATURES = FREEZE_DIR / "stage2_outcome_free_source_features.csv"
CONTROL_FEATURES = FREEZE_DIR / "stage2_frozen_control_features.csv"
PREPROCESSING = FREEZE_DIR / "preprocessing_spec.json"
SENSITIVITY_DIR = ROOT / "analysis" / "results" / "multistage_battery_stage2_coverage_sensitivity"
SPECIFICATION = SENSITIVITY_DIR / "POSTRELEASE_SENSITIVITY_SPECIFICATION.json"
MERGE_AMENDMENT = ROOT / "analysis" / "MULTISTAGE_BATTERY_POSTRELEASE_MERGE_AMENDMENT.md"
SPLITS = SENSITIVITY_DIR / "postrelease_outer_split_plan.json"
APPLICABILITY = SENSITIVITY_DIR / "postrelease_applicability_plan.csv"
OUTPUT_DIR = SENSITIVITY_DIR / "analysis"
SEED = 20260720
BOOTSTRAPS = 10_000
SIGN_FLIPS = 9_999
CCA_COLUMNS = [
    "centered_source_feature",
    "source_distance",
    "target_distance",
    "source_uncertainty_normalized",
    "provenance_compatibility",
    "applicability",
    "borrow_allowed",
]
POLICY_EXTRA = {
    "adjacency_only": ["source_prediction"],
    "global_credibility": ["global_credibility_source_feature"],
    "wrong_property": ["wrong_property_mass_prediction"],
    "shuffled_source": ["shuffled_source_prediction"],
    "random_features": [f"random_feature_{index}" for index in range(1, 7)],
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rmse(y_true: np.ndarray, prediction: np.ndarray) -> float:
    return float(np.sqrt(np.mean((y_true - prediction) ** 2)))


def holm_two(p_values: dict[str, float]) -> dict[str, float]:
    ordered = sorted(p_values, key=p_values.get)
    return {
        ordered[0]: min(1.0, 2.0 * p_values[ordered[0]]),
        ordered[1]: min(1.0, max(2.0 * p_values[ordered[0]], p_values[ordered[1]])),
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    release = json.loads(RELEASE_AUDIT.read_text(encoding="utf-8"))
    specification = json.loads(SPECIFICATION.read_text(encoding="utf-8"))
    if release["status"] != "non-evaluable-stage2-release" or release["coverage_gate_pass"]:
        raise AssertionError("The frozen 23-group primary must remain non-evaluable")
    if specification["status"] != "specified-postrelease-exploratory-sensitivity":
        raise AssertionError("Post-release sensitivity was not explicitly specified")
    if specification["endpoint_table_sha256"] != sha256(ENDPOINTS):
        raise AssertionError("Stage 2 endpoint table changed after sensitivity specification")
    if specification["postrelease_split_plan_sha256"] != sha256(SPLITS):
        raise AssertionError("Post-release split plan changed after specification")
    if specification["postrelease_applicability_plan_sha256"] != sha256(APPLICABILITY):
        raise AssertionError("Post-release applicability plan changed after specification")
    if specification["analysis_runner_sha256"] != sha256(Path(__file__).resolve()):
        raise AssertionError("Sensitivity analysis code changed after specification")
    if specification["infrastructure_amendment_sha256"] != sha256(MERGE_AMENDMENT):
        raise AssertionError("Documented merge amendment changed after specification")

    endpoints = pd.read_csv(
        ENDPOINTS,
        dtype={"file_id": str, "serial_internal": str, "serial": str, "stage": str},
    )
    endpoints = endpoints.loc[endpoints["status"].eq("extracted-stage2")].copy()
    meta = pd.read_csv(META, dtype={"serial_internal": str, "serial": str, "stage": str})
    meta = meta.loc[meta["stage"].eq("2")].copy()
    meta["condition_group"] = meta.apply(canonical_group, axis=1)
    source = pd.read_csv(SOURCE_FEATURES, dtype={"file_id": str, "serial_internal": str, "serial": str})
    controls = pd.read_csv(CONTROL_FEATURES, dtype={"file_id": str})
    data = endpoints.merge(
        meta,
        on=["serial_internal", "serial", "stage", "lab", "type", "tp", "cell", "sampling"],
        validate="one_to_one",
    )
    data = data.merge(
        source,
        on=["file_id", "serial_internal", "serial", "type", "condition_group", "lab", "tp", "cell", "sampling"],
        validate="one_to_one",
    )
    data = data.merge(
        controls.drop(
            columns=["serial_internal", "serial", "type", "condition_group", "wrong_property_mass_prediction"]
        ),
        on="file_id",
        validate="one_to_one",
    ).sort_values(["type", "condition_group", "file_id"]).reset_index(drop=True)
    if len(data) != 135 or data["condition_group"].nunique() != 22:
        raise AssertionError("Sensitivity data do not match the specified 135 cells and 22 groups")

    splits = json.loads(SPLITS.read_text(encoding="utf-8"))
    specs = json.loads(PREPROCESSING.read_text(encoding="utf-8"))
    applicability = pd.read_csv(APPLICABILITY, dtype={"file_id": str, "borrow_allowed": bool})
    if set(splits) != set(data["condition_group"].unique()):
        raise AssertionError("Sensitivity split plan does not cover exactly the observable groups")

    base_by_type: dict[str, dict[str, np.ndarray]] = {}
    for aging_type in ("k", "z"):
        part = data.loc[data["type"].eq(aging_type)].copy()
        matrix, _ = transform(part, specs[aging_type])
        base_by_type[aging_type] = dict(zip(part["file_id"], matrix))

    def base_matrix(rows: pd.DataFrame) -> np.ndarray:
        types = rows["type"].unique()
        if len(types) != 1:
            raise AssertionError("A target model received mixed aging types")
        return np.vstack([base_by_type[types[0]][file_id] for file_id in rows["file_id"]])

    def app_matrix(rows: pd.DataFrame, scope: str, outer: str, nested: str = "") -> np.ndarray:
        selected = applicability.loc[
            applicability["scope"].eq(scope) & applicability["outer_heldout_group"].eq(outer)
        ].copy()
        if scope == "nested_validation":
            selected = selected.loc[selected["nested_heldout_group"].fillna("").eq(nested)]
        lookup = selected.set_index("file_id")
        if not set(rows["file_id"]).issubset(lookup.index):
            raise AssertionError(f"Applicability rows missing for {scope}, {outer}, {nested}")
        return lookup.loc[rows["file_id"], CCA_COLUMNS].astype(float).to_numpy()

    gate_cache: dict[tuple, tuple[float, bool]] = {}

    def training_gate(aging_type: str, selected_groups: list[str], outer: str) -> float:
        key = (aging_type, tuple(selected_groups))
        if key in gate_cache:
            return gate_cache[key][0]
        target_errors: list[float] = []
        cca_errors: list[float] = []
        for nested in selected_groups:
            train_rows = data.loc[
                data["condition_group"].isin([group for group in selected_groups if group != nested])
            ].copy()
            validation_rows = data.loc[data["condition_group"].eq(nested)].copy()
            x_train = base_matrix(train_rows)
            x_validation = base_matrix(validation_rows)
            y_train = train_rows["q_rel_end_percent"].to_numpy(dtype=float)
            y_validation = validation_rows["q_rel_end_percent"].to_numpy(dtype=float)
            target_model = new_model().fit(x_train, y_train)
            target_errors.append(rmse(y_validation, target_model.predict(x_validation)))
            cca_model = new_model().fit(
                np.hstack([x_train, app_matrix(train_rows, "outer_train_fit", outer)]), y_train
            )
            cca_errors.append(
                rmse(
                    y_validation,
                    cca_model.predict(
                        np.hstack([x_validation, app_matrix(validation_rows, "nested_validation", outer, nested)])
                    ),
                )
            )
        gain = 1.0 - float(np.mean(cca_errors)) / float(np.mean(target_errors))
        gate_cache[key] = (gain, True)
        return gain

    predictions: list[dict] = []
    gate_records: list[dict] = []
    for outer, split in sorted(splits.items()):
        gains = {
            aging_type: training_gate(aging_type, split["target_training_groups_by_type"][aging_type], outer)
            for aging_type in ("k", "z")
        }
        equal_stratum_gain = 0.5 * (gains["k"] + gains["z"])
        gate_pass = equal_stratum_gain > 0.02 and gains["k"] > 0 and gains["z"] > 0
        gate_records.append({
            "outer_heldout_group": outer,
            "calendar_relative_rmse_gain": gains["k"],
            "cycle_relative_rmse_gain": gains["z"],
            "equal_stratum_relative_rmse_gain": equal_stratum_gain,
            "gate_pass": gate_pass,
        })

        aging_type = split["aging_type"]
        selected_groups = split["target_training_groups_by_type"][aging_type]
        train_rows = data.loc[data["condition_group"].isin(selected_groups)].copy()
        test_rows = data.loc[data["condition_group"].eq(outer)].copy()
        x_train = base_matrix(train_rows)
        x_test = base_matrix(test_rows)
        y_train = train_rows["q_rel_end_percent"].to_numpy(dtype=float)
        policy_predictions: dict[str, np.ndarray] = {}
        target_model = new_model().fit(x_train, y_train)
        policy_predictions["target_only"] = target_model.predict(x_test)
        for policy, columns in POLICY_EXTRA.items():
            model = new_model().fit(
                np.hstack([x_train, train_rows[columns].to_numpy(dtype=float)]), y_train
            )
            policy_predictions[policy] = model.predict(
                np.hstack([x_test, test_rows[columns].to_numpy(dtype=float)])
            )
        if gate_pass:
            cca_model = new_model().fit(
                np.hstack([x_train, app_matrix(train_rows, "outer_train_fit", outer)]), y_train
            )
            policy_predictions["cca_v2"] = cca_model.predict(
                np.hstack([x_test, app_matrix(test_rows, "outer_test", outer)])
            )
        else:
            policy_predictions["cca_v2"] = policy_predictions["target_only"].copy()

        for policy, values in policy_predictions.items():
            for (_, row), prediction in zip(test_rows.iterrows(), values):
                predictions.append({
                    "file_id": row["file_id"],
                    "serial_internal": row["serial_internal"],
                    "serial": row["serial"],
                    "type": aging_type,
                    "condition_group": outer,
                    "policy": policy,
                    "observed": row["q_rel_end_percent"],
                    "prediction": float(prediction),
                    "residual": float(row["q_rel_end_percent"] - prediction),
                    "source_distance": float(row["source_distance"]),
                    "gate_pass": gate_pass,
                })

    prediction_table = pd.DataFrame(predictions).sort_values(["policy", "type", "condition_group", "file_id"])
    gate_table = pd.DataFrame(gate_records).sort_values("outer_heldout_group")
    prediction_path = OUTPUT_DIR / "stage2_outer_predictions.csv"
    gate_path = OUTPUT_DIR / "training_only_gate.csv"
    prediction_table.to_csv(prediction_path, index=False, lineterminator="\n")
    gate_table.to_csv(gate_path, index=False, lineterminator="\n")

    grouped = prediction_table.groupby(["type", "condition_group", "policy"], as_index=False).agg(
        condition_rmse=("residual", lambda values: float(np.sqrt(np.mean(np.square(values))))),
        n_cells=("residual", "size"),
        source_distance=("source_distance", "mean"),
    )
    group_error_path = OUTPUT_DIR / "condition_group_errors.csv"
    grouped.to_csv(group_error_path, index=False, lineterminator="\n")
    wide = grouped.pivot(index=["type", "condition_group"], columns="policy", values="condition_rmse").reset_index()

    comparators = {
        "adjacency_only": "CCA-v2 minus adjacency-only",
        "target_only": "CCA-v2 minus endpoint-matched target-only",
    }
    rng = np.random.default_rng(SEED)
    inference: dict[str, dict] = {}
    raw_p: dict[str, float] = {}
    bootstrap_rows: list[dict] = []
    for comparator, label in comparators.items():
        parts = {
            aging_type: wide.loc[wide["type"].eq(aging_type)].reset_index(drop=True)
            for aging_type in ("k", "z")
        }
        stratum_effects = {
            aging_type: 1.0 - part["cca_v2"].mean() / part[comparator].mean()
            for aging_type, part in parts.items()
        }
        observed = 0.5 * (stratum_effects["k"] + stratum_effects["z"])
        boot = np.empty(BOOTSTRAPS)
        boot_k = np.empty(BOOTSTRAPS)
        boot_z = np.empty(BOOTSTRAPS)
        for index in range(BOOTSTRAPS):
            effects = {}
            for aging_type, part in parts.items():
                sampled = part.iloc[rng.integers(0, len(part), len(part))]
                effects[aging_type] = 1.0 - sampled["cca_v2"].mean() / sampled[comparator].mean()
            boot_k[index], boot_z[index] = effects["k"], effects["z"]
            boot[index] = 0.5 * (effects["k"] + effects["z"])
            bootstrap_rows.append({
                "comparison": label,
                "bootstrap": index,
                "effect": boot[index],
                "calendar_effect": boot_k[index],
                "cycle_effect": boot_z[index],
            })

        null = np.empty(SIGN_FLIPS)
        for index in range(SIGN_FLIPS):
            permuted_effects = {}
            for aging_type, part in parts.items():
                midpoint = 0.5 * (part["cca_v2"].to_numpy() + part[comparator].to_numpy())
                half_difference = 0.5 * (part["cca_v2"].to_numpy() - part[comparator].to_numpy())
                signs = rng.choice(np.array([-1.0, 1.0]), size=len(part))
                permuted_cca = midpoint + signs * half_difference
                permuted_comparator = midpoint - signs * half_difference
                permuted_effects[aging_type] = 1.0 - permuted_cca.mean() / permuted_comparator.mean()
            null[index] = 0.5 * (permuted_effects["k"] + permuted_effects["z"])
        p_value = float((1 + np.sum(null >= observed)) / (SIGN_FLIPS + 1))
        raw_p[label] = p_value
        inference[label] = {
            "effect": float(observed),
            "calendar_effect": float(stratum_effects["k"]),
            "cycle_effect": float(stratum_effects["z"]),
            "ci95": [float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))],
            "calendar_ci95": [float(np.quantile(boot_k, 0.025)), float(np.quantile(boot_k, 0.975))],
            "cycle_ci95": [float(np.quantile(boot_z, 0.025)), float(np.quantile(boot_z, 0.975))],
            "one_sided_sign_flip_p": p_value,
            "inferential_status": "exploratory-after-coverage-failure",
        }
    adjusted = holm_two(raw_p)
    for label, value in adjusted.items():
        inference[label]["holm_adjusted_p"] = value
    bootstrap_path = OUTPUT_DIR / "condition_cluster_bootstrap.csv"
    pd.DataFrame(bootstrap_rows).to_csv(bootstrap_path, index=False, lineterminator="\n")

    policy_summary: dict[str, dict] = {}
    for policy in sorted(prediction_table["policy"].unique()):
        policy_summary[policy] = {}
        for aging_type in ("k", "z"):
            part = grouped.loc[grouped["type"].eq(aging_type)]
            policy_error = float(part.loc[part["policy"].eq(policy), "condition_rmse"].mean())
            target_error = float(part.loc[part["policy"].eq("target_only"), "condition_rmse"].mean())
            cell_part = prediction_table.loc[
                prediction_table["type"].eq(aging_type) & prediction_table["policy"].eq(policy)
            ]
            policy_summary[policy][aging_type] = {
                "mean_condition_rmse": policy_error,
                "relative_rmse_gain_vs_target_only": 1.0 - policy_error / target_error,
                "heldout_r2": float(r2_score(cell_part["observed"], cell_part["prediction"])),
            }
        policy_summary[policy]["equal_stratum_relative_rmse_gain_vs_target_only"] = 0.5 * (
            policy_summary[policy]["k"]["relative_rmse_gain_vs_target_only"]
            + policy_summary[policy]["z"]["relative_rmse_gain_vs_target_only"]
        )

    hard_ood: dict[str, dict] = {}
    for aging_type in ("k", "z"):
        distances = grouped.loc[grouped["type"].eq(aging_type), ["condition_group", "source_distance"]].drop_duplicates()
        threshold = float(distances["source_distance"].quantile(0.75))
        groups_ood = set(distances.loc[distances["source_distance"] >= threshold, "condition_group"])
        part = grouped.loc[grouped["type"].eq(aging_type) & grouped["condition_group"].isin(groups_ood)]
        errors = part.groupby("policy")["condition_rmse"].mean()
        hard_ood[aging_type] = {
            "source_distance_q75": threshold,
            "condition_groups": sorted(groups_ood),
            "cca_v2_relative_rmse_gain_vs_target_only": float(1.0 - errors["cca_v2"] / errors["target_only"]),
            "cca_v2_relative_rmse_gain_vs_adjacency_only": float(1.0 - errors["cca_v2"] / errors["adjacency_only"]),
        }

    group_means = data.groupby("condition_group").agg(
        retention=("q_rel_end_percent", "mean"),
        charge_retention=("q_rel_charge_percent", "mean"),
        discharge_retention=("q_rel_discharge_percent", "mean"),
    )
    card_results = {
        "calendar": {
            "lead": "k|45|0.9",
            "control": "k|23|0.9",
            "lead_retention": float(group_means.loc["k|45|0.9", "retention"]),
            "control_retention": float(group_means.loc["k|23|0.9", "retention"]),
            "directional_pass": bool(group_means.loc["k|45|0.9", "retention"] < group_means.loc["k|23|0.9", "retention"]),
        },
        "cycle": {
            "lead": "z|45|0.8|0.6|1|0.26",
            "control": "z|45|0.41|0.05|1|1",
            "lead_retention": float(group_means.loc["z|45|0.8|0.6|1|0.26", "retention"]),
            "control_retention": float(group_means.loc["z|45|0.41|0.05|1|1", "retention"]),
            "directional_pass": bool(
                group_means.loc["z|45|0.8|0.6|1|0.26", "retention"]
                < group_means.loc["z|45|0.41|0.05|1|1", "retention"]
            ),
        },
    }

    pattern_pass = all(
        item["effect"] > 0.02 and item["ci95"][0] > 0 and item["holm_adjusted_p"] <= 0.05
        for item in inference.values()
    )
    absolute_guard = all(policy_summary["cca_v2"][aging_type]["heldout_r2"] > 0 for aging_type in ("k", "z"))
    borrow_guard = (
        specification["outer_test_borrowing_groups"] >= 5
        and all(value >= 1 for value in specification["outer_test_borrowing_groups_by_type"].values())
    )
    safety = inference["CCA-v2 minus endpoint-matched target-only"]
    safety_guard = safety["calendar_ci95"][1] >= -0.02 and safety["cycle_ci95"][1] >= -0.02
    summary = {
        "status": "verified-complete-postrelease-coverage-sensitivity",
        "frozen_primary_status": "non-evaluable-stage2-release",
        "confirmatory_success": False,
        "exploratory_pattern_pass": bool(pattern_pass and absolute_guard and borrow_guard and safety_guard),
        "primary_named_comparisons_reported_as_exploratory": inference,
        "policy_summary": policy_summary,
        "hard_ood_diagnostic": hard_ood,
        "diagnostic_guards": {
            "effect_interval_and_multiplicity_pattern": bool(pattern_pass),
            "absolute_utility": bool(absolute_guard),
            "borrowing_coverage": bool(borrow_guard),
            "safety": bool(safety_guard),
        },
        "training_gate_passed_outer_groups": int(gate_table["gate_pass"].sum()),
        "training_gate_total_outer_groups": len(gate_table),
        "hypothesis_card_results": card_results,
        "stage2_cells_analyzed": len(data),
        "stage2_condition_groups": int(data["condition_group"].nunique()),
        "postrelease_excluded_group": specification["excluded_condition_groups"],
        "endpoint_table_sha256": sha256(ENDPOINTS),
        "release_audit_sha256": sha256(RELEASE_AUDIT),
        "specification_sha256": sha256(SPECIFICATION),
        "split_plan_sha256": sha256(SPLITS),
        "applicability_plan_sha256": sha256(APPLICABILITY),
        "prediction_table_sha256": sha256(prediction_path),
        "gate_table_sha256": sha256(gate_path),
        "group_error_table_sha256": sha256(group_error_path),
        "bootstrap_table_sha256": sha256(bootstrap_path),
        "claim_guard": "This post-release sensitivity cannot rescue the non-evaluable 23-group primary test. A favorable pattern is method-plausibility evidence only and requires a new outcome-unseen target for confirmation.",
        "errors": [],
    }
    summary_path = OUTPUT_DIR / "POSTRELEASE_SENSITIVITY_SUMMARY.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
