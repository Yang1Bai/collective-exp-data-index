"""Specify the missingness-driven 22-group Stage 2 sensitivity after release."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from analysis.freeze_multistage_battery_applicability_plan import (
        THRESHOLD,
        append_scope,
        distance_to_groups,
    )
    from analysis.freeze_multistage_battery_stage1_source import (
        CONDITIONS,
        canonical_group,
        maximin_training_groups,
    )
except ModuleNotFoundError:
    from freeze_multistage_battery_applicability_plan import THRESHOLD, append_scope, distance_to_groups
    from freeze_multistage_battery_stage1_source import CONDITIONS, canonical_group, maximin_training_groups


ROOT = Path(__file__).resolve().parents[1]
STAGE2 = ROOT / "analysis" / "results" / "multistage_battery_stage2"
ENDPOINTS = STAGE2 / "stage2_capacity_endpoints.csv"
RELEASE_AUDIT = STAGE2 / "STAGE2_RELEASE_AUDIT.json"
BOUNDARY = ROOT / "analysis" / "MULTISTAGE_BATTERY_STAGE2_COVERAGE_BOUNDARY.md"
META = ROOT / "analysis" / "results" / "multistage_battery_file_map" / "experiments_meta.csv"
SOURCE_DIR = ROOT / "analysis" / "results" / "multistage_battery_stage1_source_freeze"
SOURCE_FEATURES = SOURCE_DIR / "stage2_outcome_free_source_features.csv"
SOURCE_FREEZE = SOURCE_DIR / "STAGE1_SOURCE_FREEZE.json"
ORIGINAL_SPLITS = SOURCE_DIR / "stage2_outer_split_plan.json"
ORIGINAL_APPLICABILITY = SOURCE_DIR / "stage2_applicability_plan.csv"
OUTPUT_DIR = ROOT / "analysis" / "results" / "multistage_battery_stage2_coverage_sensitivity"
SPLITS_OUTPUT = OUTPUT_DIR / "postrelease_outer_split_plan.json"
APPLICABILITY_OUTPUT = OUTPUT_DIR / "postrelease_applicability_plan.csv"
MANIFEST_OUTPUT = OUTPUT_DIR / "POSTRELEASE_SENSITIVITY_SPECIFICATION.json"
ANALYSIS_RUNNER = ROOT / "analysis" / "run_multistage_battery_stage2_coverage_sensitivity.py"
MERGE_AMENDMENT = ROOT / "analysis" / "MULTISTAGE_BATTERY_POSTRELEASE_MERGE_AMENDMENT.md"
EXPECTED_MISSING_GROUP = "z|35|0.8|0.5|0.9|1.1"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    release = json.loads(RELEASE_AUDIT.read_text(encoding="utf-8"))
    if release["status"] != "non-evaluable-stage2-release" or release["coverage_gate_pass"]:
        raise AssertionError("This sensitivity is permitted only after the frozen primary coverage gate fails")

    endpoints = pd.read_csv(
        ENDPOINTS,
        dtype={"file_id": str, "serial_internal": str, "serial": str, "stage": str},
    )
    meta = pd.read_csv(META, dtype={"serial_internal": str, "serial": str, "stage": str})
    meta = meta.loc[meta["stage"].eq("2")].copy()
    meta["condition_group"] = meta.apply(canonical_group, axis=1)
    status = endpoints[["file_id", "serial_internal", "serial", "stage", "status", "error"]].merge(
        meta[["serial_internal", "serial", "stage", "condition_group", "type"]],
        on=["serial_internal", "serial", "stage"],
        how="left",
        validate="one_to_one",
    )
    missing = status.loc[~status["status"].eq("extracted-stage2")].copy()
    missing_groups = sorted(missing["condition_group"].dropna().unique())
    if len(missing) != 3 or missing_groups != [EXPECTED_MISSING_GROUP]:
        raise AssertionError(f"Unexpected Stage 2 missingness pattern: {missing_groups}, n={len(missing)}")
    if not missing["error"].str.contains(r"expected exactly one \*_AT_T23.csv; found 0", regex=True).all():
        raise AssertionError("The excluded group is not uniformly missing the frozen AT_T23 endpoint")

    evaluable_ids = set(status.loc[status["status"].eq("extracted-stage2"), "file_id"])
    features = pd.read_csv(
        SOURCE_FEATURES,
        dtype={"file_id": str, "serial_internal": str, "serial": str},
    )
    features = features.loc[features["file_id"].isin(evaluable_ids)].copy()
    if len(features) != 135 or features["condition_group"].nunique() != 22:
        raise AssertionError("The post-release sensitivity must contain 135 cells in 22 complete groups")
    if EXPECTED_MISSING_GROUP in set(features["condition_group"]):
        raise AssertionError("The structurally missing group remained in the sensitivity feature table")

    all_condition_columns = sorted(set(sum(CONDITIONS.values(), [])))
    features = features.merge(
        meta[["serial_internal", "serial", *all_condition_columns]],
        on=["serial_internal", "serial"],
        how="left",
        validate="one_to_one",
    )
    source_summary = json.loads(SOURCE_FREEZE.read_text(encoding="utf-8"))
    group_tables = {
        aging_type: features.loc[features["type"].eq(aging_type), ["condition_group", *CONDITIONS[aging_type]]]
        .drop_duplicates()
        .sort_values("condition_group")
        for aging_type in ("k", "z")
    }

    splits: dict[str, dict] = {}
    for heldout in sorted(features["condition_group"].unique()):
        selected_by_type = {
            "k": maximin_training_groups(
                group_tables["k"], heldout, 4, source_summary["model_summaries"]["k"]["condition_scaler"]
            ),
            "z": maximin_training_groups(
                group_tables["z"], heldout, 6, source_summary["model_summaries"]["z"]["condition_scaler"]
            ),
        }
        selected = selected_by_type["k"] + selected_by_type["z"]
        if heldout in selected or EXPECTED_MISSING_GROUP in selected:
            raise AssertionError("Held-out or structurally missing group entered a target-training budget")
        splits[heldout] = {
            "aging_type": heldout.split("|", 1)[0],
            "heldout_group": heldout,
            "target_training_groups_by_type": selected_by_type,
            "target_training_groups": selected,
            "target_label_budget_groups": 10,
            "target_label_budget_by_type": {"k": 4, "z": 6},
            "postrelease_reason": "deterministic maximin regeneration after structural endpoint absence",
        }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    SPLITS_OUTPUT.write_text(json.dumps(splits, indent=2) + "\n", encoding="utf-8")

    groups = features[["type", "condition_group", *all_condition_columns]].drop_duplicates("condition_group")
    records: list[dict] = []
    for outer_heldout, split in sorted(splits.items()):
        aging_type = split["aging_type"]
        scaler = source_summary["model_summaries"][aging_type]["condition_scaler"]
        selected = split["target_training_groups"]
        selected_by_type = split["target_training_groups_by_type"]
        outer_candidates = features.loc[features["condition_group"].eq(outer_heldout)]
        outer_reference = groups.loc[groups["condition_group"].isin(selected_by_type[aging_type])]
        append_scope(
            records,
            outer_candidates,
            distance_to_groups(outer_candidates, outer_reference, scaler),
            "outer_test",
            outer_heldout,
        )
        training_candidates = features.loc[features["condition_group"].isin(selected)]
        append_scope(records, training_candidates, np.zeros(len(training_candidates)), "outer_train_fit", outer_heldout)
        for nested_heldout in selected:
            nested_type = nested_heldout.split("|", 1)[0]
            nested_scaler = source_summary["model_summaries"][nested_type]["condition_scaler"]
            nested_candidates = features.loc[features["condition_group"].eq(nested_heldout)]
            nested_reference = groups.loc[
                groups["condition_group"].isin(
                    [group for group in selected_by_type[nested_type] if group != nested_heldout]
                )
            ]
            append_scope(
                records,
                nested_candidates,
                distance_to_groups(nested_candidates, nested_reference, nested_scaler),
                "nested_validation",
                outer_heldout,
                nested_heldout,
            )

    applicability = pd.DataFrame(records).sort_values(
        ["type", "outer_heldout_group", "scope", "nested_heldout_group", "candidate_group", "file_id"]
    )
    applicability.to_csv(APPLICABILITY_OUTPUT, index=False, lineterminator="\n")
    outer = applicability.loc[applicability["scope"].eq("outer_test")]
    manifest = {
        "status": "specified-postrelease-exploratory-sensitivity",
        "primary_23_group_status": "non-evaluable-stage2-release",
        "target_outcomes_opened_before_specification": True,
        "selection_basis": "structural endpoint availability only; no outcome value used to select the excluded group",
        "excluded_condition_groups": [EXPECTED_MISSING_GROUP],
        "excluded_cells": 3,
        "retained_cells": len(features),
        "retained_condition_groups": len(splits),
        "retained_groups_by_type": {
            aging_type: int(group_tables[aging_type]["condition_group"].nunique()) for aging_type in ("k", "z")
        },
        "target_label_budget_by_type": {"k": 4, "z": 6},
        "applicability_threshold": THRESHOLD,
        "applicability_rows": len(applicability),
        "outer_test_borrowing_groups": int(outer.loc[outer["borrow_allowed"], "outer_heldout_group"].nunique()),
        "outer_test_borrowing_groups_by_type": {
            aging_type: int(part.loc[part["borrow_allowed"], "outer_heldout_group"].nunique())
            for aging_type, part in outer.groupby("type")
        },
        "unchanged_from_frozen_analysis": [
            "endpoint", "source features", "target predictors", "learner", "applicability formula and threshold",
            "training-only gate", "controls", "two comparisons", "effect definitions", "10000 bootstraps",
            "9999 sign flips", "Holm correction", "absolute utility and safety diagnostics",
        ],
        "changed_after_release": [
            "exclude the sole structurally non-evaluable condition group",
            "regenerate deterministic maximin target-training budgets over the 22 observable groups",
            "downgrade every decision and p-value to exploratory sensitivity evidence",
        ],
        "release_audit_sha256": sha256(RELEASE_AUDIT),
        "endpoint_table_sha256": sha256(ENDPOINTS),
        "boundary_document_sha256": sha256(BOUNDARY),
        "original_split_plan_sha256": sha256(ORIGINAL_SPLITS),
        "original_applicability_plan_sha256": sha256(ORIGINAL_APPLICABILITY),
        "postrelease_split_plan_sha256": sha256(SPLITS_OUTPUT),
        "postrelease_applicability_plan_sha256": sha256(APPLICABILITY_OUTPUT),
        "analysis_runner_sha256": sha256(ANALYSIS_RUNNER),
        "infrastructure_amendment_sha256": sha256(MERGE_AMENDMENT),
        "claim_guard": "This sensitivity cannot rescue or replace the non-evaluable frozen 23-group primary test. It may estimate plausibility and guide a new independent confirmatory program.",
        "errors": [],
    }
    MANIFEST_OUTPUT.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
