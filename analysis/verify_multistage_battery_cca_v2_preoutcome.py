"""Verify the multi-stage battery CCA-v2 freeze without reading target outcomes."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / "analysis" / "multistage_battery_cca_v2_design.json"
PROTOCOL = ROOT / "analysis" / "MULTISTAGE_BATTERY_CCA_V2_PROTOCOL.md"
METADATA = ROOT / "analysis" / "target_metadata" / "multistage_battery_preoutcome_metadata.json"
ARCHITECTURE = ROOT / "analysis" / "cca_gate_v2_architecture.json"
FREEZE = ROOT / "analysis" / "target_metadata" / "multistage_battery_preoutcome_freeze.json"
REGISTRY = ROOT / "analysis" / "core_story_experiment_registry.json"
CATALOG = ROOT / "catalog" / "catalog.json"
SELF = Path(__file__).resolve()
MAP_DIR = ROOT / "analysis" / "results" / "multistage_battery_file_map"
MAP_CSV = MAP_DIR / "archive_file_stage_map.csv"
MAP_COMPLETE = MAP_DIR / "COMPLETE.json"
MAP_VERIFIED = MAP_DIR / "INDEPENDENT_VERIFICATION.json"
HEADER_REPORT = ROOT / "analysis" / "results" / "multistage_battery_header_schema.json"
ENDPOINT_SCHEMA = ROOT / "analysis" / "multistage_battery_endpoint_schema.json"
ENDPOINT_AMENDMENT = ROOT / "analysis" / "MULTISTAGE_BATTERY_ENDPOINT_SCHEMA_AMENDMENT.md"
HEADER_INSPECTOR = ROOT / "analysis" / "inspect_multistage_battery_headers.py"
HEADER_VERIFIER = ROOT / "analysis" / "verify_multistage_battery_header_schema.py"
LIFECYCLE_AMENDMENT = ROOT / "analysis" / "MULTISTAGE_BATTERY_PREOUTCOME_VERIFIER_LIFECYCLE_AMENDMENT.md"
STAGE2_RELEASE_AUDIT = ROOT / "analysis" / "results" / "multistage_battery_stage2" / "STAGE2_RELEASE_AUDIT.json"
ORIGINAL_VERIFIER_SHA256 = "bcf5a6791b7ca788daec45030e2227d660415d65da61ca530eb28ba6a9cb78be"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def validate_metadata_csv(path: Path, metadata: dict, errors: list[str]) -> dict:
    profile: dict = {"path": str(path), "checked": False}
    if not path.is_file():
        errors.append(f"metadata CSV not found: {path}")
        return profile
    expected = metadata["figshare_file_manifest"]["experiments_meta"]
    require(sha256(path) == expected["sha256"], "experiments_meta SHA256 mismatch", errors)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    normalized = [{str(k).strip(): v for k, v in row.items()} for row in rows]
    stage = Counter(row["stage"] for row in normalized)
    stage_type = Counter((row["stage"], row["type"]) for row in normalized)
    expected_profile = metadata["experiments_metadata_profile"]
    require(len(rows) == expected_profile["rows"], "metadata row count mismatch", errors)
    require(stage == Counter({"1": 141, "2": 138}), "stage cell counts changed", errors)
    require(
        stage_type == Counter({("1", "k"): 66, ("1", "z"): 75, ("2", "k"): 66, ("2", "z"): 72}),
        "stage/type cell counts changed",
        errors,
    )
    outcome_tokens = {"capacity", "retention", "cycle_life", "soh", "q_at", "q_et"}
    columns = {column.strip().lower() for column in (rows[0].keys() if rows else [])}
    require(not (columns & outcome_tokens), "metadata CSV unexpectedly contains outcome columns", errors)
    profile.update({"checked": True, "sha256": sha256(path), "rows": len(rows)})
    return profile


def validate_preoutcome(metadata_csv: Path | None = None) -> dict:
    errors: list[str] = []
    required = [
        DESIGN, PROTOCOL, METADATA, ARCHITECTURE, FREEZE, REGISTRY, CATALOG,
        SELF, MAP_CSV, MAP_COMPLETE, MAP_VERIFIED, HEADER_REPORT,
        ENDPOINT_SCHEMA, ENDPOINT_AMENDMENT, HEADER_INSPECTOR, HEADER_VERIFIER,
        LIFECYCLE_AMENDMENT,
    ]
    for path in required:
        require(path.is_file(), f"missing required file: {path.relative_to(ROOT)}", errors)
    if errors:
        return {"status": "invalid", "errors": errors}

    design = json.loads(DESIGN.read_text(encoding="utf-8"))
    metadata = json.loads(METADATA.read_text(encoding="utf-8"))
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    architecture = json.loads(ARCHITECTURE.read_text(encoding="utf-8"))
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    map_complete = json.loads(MAP_COMPLETE.read_text(encoding="utf-8"))
    map_verified = json.loads(MAP_VERIFIED.read_text(encoding="utf-8"))
    header_report = json.loads(HEADER_REPORT.read_text(encoding="utf-8"))
    endpoint_schema = json.loads(ENDPOINT_SCHEMA.read_text(encoding="utf-8"))

    expected_hashes = {
        "design_sha256": sha256(DESIGN),
        "protocol_sha256": sha256(PROTOCOL),
        "metadata_snapshot_sha256": sha256(METADATA),
        "architecture_sha256": sha256(ARCHITECTURE),
        "header_report_sha256": sha256(HEADER_REPORT),
        "endpoint_schema_sha256": sha256(ENDPOINT_SCHEMA),
        "endpoint_amendment_sha256": sha256(ENDPOINT_AMENDMENT),
        "header_inspector_sha256": sha256(HEADER_INSPECTOR),
        "header_verifier_sha256": sha256(HEADER_VERIFIER),
    }
    for field, actual in expected_hashes.items():
        require(freeze.get(field) == actual, f"freeze hash mismatch: {field}", errors)
    require(
        freeze.get("verifier_sha256") == ORIGINAL_VERIFIER_SHA256,
        "historical pre-outcome verifier hash changed in the freeze",
        errors,
    )

    require(design["parent_architecture_sha256"] == sha256(ARCHITECTURE), "design parent architecture changed", errors)
    require(design["version"] == 5, "target design is not the corrected version 5 freeze", errors)
    require(architecture["primary_family"]["comparisons"] == design["primary_inference"]["comparisons"], "primary family differs from CCA-v2 architecture", errors)
    require(len(design["primary_inference"]["comparisons"]) == 2, "primary family must contain exactly two comparisons", errors)
    require(design["training_only_borrowing_gate"]["dead_zone"] == 0.02, "borrowing dead zone changed", errors)
    require(design["outer_evaluation"]["held_out_groups"] == 23, "held-out condition count changed", errors)
    require(design["analysis_units"]["independent_evaluation_unit"].startswith("Stage 2 condition group"), "independent unit is not the Stage 2 condition group", errors)
    require(design["endpoints"]["primary"]["transform"] == "none", "primary endpoint transform changed", errors)
    require("Q_charge_step21 + Q_discharge_step22" in design["endpoints"]["primary"]["symbol"], "RPT mean-capacity endpoint changed", errors)
    require(design["primary_inference"]["multiplicity"].startswith("Holm correction over exactly"), "primary multiplicity changed", errors)

    access = metadata["outcome_access_record"]
    require(access.get("raw_archives_downloaded_for_schema_pilot") == 3, "schema pilot archive count changed", errors)
    require(access.get("schema_pilot_file_ids") == [47627050, 47627620, 47627104], "schema pilot file IDs changed", errors)
    require(access.get("raw_archives_downloaded_for_first_full_metadata_map") == 279, "full metadata-map archive count changed", errors)
    require(access.get("csv_header_members_opened") is True, "CSV header access was not disclosed", errors)
    require(access.get("csv_header_lines_read") == 32, "CSV header-line count changed", errors)
    require(access.get("numeric_csv_data_rows_opened") is False, "numeric CSV data row was opened during schema audit", errors)
    require(access.get("numeric_csv_data_rows_parsed") is False, "numeric CSV data row was parsed during schema audit", errors)
    for field in [
        "stage1_numeric_outcomes_parsed",
        "stage2_numeric_outcomes_parsed",
        "stage2_high_performing_conditions_inspected",
    ]:
        require(access.get(field) is False, f"outcome-free sentinel failed: {field}", errors)
    profile = metadata["experiments_metadata_profile"]
    require(profile["rows"] == 279, "metadata row count changed", errors)
    require(profile["stage_cell_counts"] == {"1": 141, "2": 138}, "stage cell counts changed", errors)
    geometry = metadata["outcome_free_condition_geometry"]
    require(geometry["calendar"]["stage2_unique_conditions"] == 8, "calendar condition count changed", errors)
    require(geometry["cycle"]["stage2_unique_conditions"] == 15, "cycle condition count changed", errors)
    require(geometry["calendar"]["exact_stage1_stage2_overlap"] == 0, "calendar overlap is nonzero", errors)
    require(geometry["cycle"]["exact_stage1_stage2_overlap"] == 0, "cycle overlap is nonzero", errors)
    manifest = metadata["figshare_file_manifest"]
    require(manifest["file_count"] == 280, "Figshare file count changed", errors)
    require(manifest["duplicate_filename_groups"] == 138, "duplicate-name hazard changed", errors)
    require(metadata["hard_retrieval_gate"]["status"] == "verified-complete-metadata-only-map", "retrieval method or execution status changed", errors)
    final_mapping = metadata["hard_retrieval_gate"]["final_mapping"]
    require(final_mapping["map_sha256"] == sha256(MAP_CSV), "final map hash changed", errors)
    require(final_mapping["complete_sha256"] == sha256(MAP_COMPLETE), "mapping COMPLETE hash changed", errors)
    require(final_mapping["independent_verification_sha256"] == sha256(MAP_VERIFIED), "mapping verification hash changed", errors)
    require(map_complete["status"] == "verified-complete-metadata-only-map", "mapping COMPLETE status failed", errors)
    require(map_verified["status"] == "verified-complete-metadata-only-map", "independent mapping status failed", errors)
    require(map_verified["rows"] == 279, "independent mapping row count changed", errors)
    require(map_verified["stage_counts"] == {"1": 141, "2": 138}, "independent mapping stage counts changed", errors)
    require(map_verified["numeric_csv_entries_opened"] is False, "mapping claims a numeric CSV member was opened", errors)
    require(header_report["status"] == "verified-header-only", "header-only report status failed", errors)
    require(header_report["inspected_archive_count"] == 3, "header-only archive count changed", errors)
    require(header_report["csv_header_lines_read"] == 32, "header-only line count changed", errors)
    require(header_report["numeric_csv_data_rows_opened"] is False, "header report claims a numeric data row was opened", errors)
    require(
        header_report["distinct_csv_headers"] == ["run_time,c_vol,c_cur,c_surf_temp,amb_temp,step_type"],
        "header-only CSV schema changed",
        errors,
    )
    require(endpoint_schema["capacity_extractor"]["charge_step_type"] == 21, "charge step code changed", errors)
    require(endpoint_schema["capacity_extractor"]["discharge_step_type"] == 22, "discharge step code changed", errors)
    require(
        endpoint_schema["capacity_extractor"]["primary_endpoint"] == "Q_rel_end_percent = 100 * Q_RPT_AT_T23 / Q_RPT_ET_T23",
        "endpoint-schema primary formula changed",
        errors,
    )

    require(len(catalog["entries"]) >= 118, "current catalog lost records from the 118-entry freeze", errors)
    require(any(entry["id"] == "multistage-liion-aging-dataset" for entry in catalog["entries"]), "target record is absent from the current catalog", errors)
    require(freeze["catalog_sha256"] == metadata["catalog_snapshot"]["sha256"], "frozen historical catalog hash is inconsistent", errors)
    cs13 = next((item for item in registry["experiments"] if item["id"] == "CS13"), None)
    require(cs13 is not None, "CS13 missing from experiment registry", errors)
    if cs13:
        require(
            cs13["status"] in {"preoutcome-frozen", "complete-boundary"},
            "CS13 has an undocumented lifecycle status",
            errors,
        )
        require(str(DESIGN.relative_to(ROOT)).replace("\\", "/") in cs13["design_paths"], "CS13 does not register the target design", errors)
        if cs13["status"] == "complete-boundary":
            require(STAGE2_RELEASE_AUDIT.is_file(), "completed CS13 lacks its Stage 2 release audit", errors)
            if STAGE2_RELEASE_AUDIT.is_file():
                release = json.loads(STAGE2_RELEASE_AUDIT.read_text(encoding="utf-8"))
                require(
                    release.get("status") == "non-evaluable-stage2-release",
                    "completed CS13 release status differs from the documented boundary",
                    errors,
                )
            release_relative = str(STAGE2_RELEASE_AUDIT.relative_to(ROOT)).replace("\\", "/")
            require(release_relative in cs13["evidence_paths"], "CS13 does not register its release audit", errors)

    csv_profile = {"checked": False}
    if metadata_csv is not None:
        csv_profile = validate_metadata_csv(metadata_csv, metadata, errors)

    return {
        "status": "verified-preoutcome-endpoint-schema" if not errors else "invalid",
        "design_sha256": sha256(DESIGN),
        "metadata_snapshot_sha256": sha256(METADATA),
        "architecture_sha256": sha256(ARCHITECTURE),
        "historical_verifier_sha256": ORIGINAL_VERIFIER_SHA256,
        "current_lifecycle_verifier_sha256": sha256(SELF),
        "lifecycle_amendment_sha256": sha256(LIFECYCLE_AMENDMENT),
        "target_cells": 138,
        "stage2_condition_groups": 23,
        "exact_stage1_stage2_condition_overlap": 0,
        "raw_target_outcomes_opened": False,
        "numeric_csv_data_rows_opened": False,
        "retrieval_gate": metadata["hard_retrieval_gate"]["status"],
        "schema_pilot_archives_downloaded": 3,
        "csv_header_lines_read": 32,
        "full_metadata_map_archives_downloaded": 279,
        "metadata_csv": csv_profile,
        "claim_guard": design["claim_guard"],
        "errors": errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata-csv", type=Path, help="Optional experiments_meta.csv to verify against the frozen hash.")
    args = parser.parse_args()
    result = validate_preoutcome(args.metadata_csv)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["status"].startswith("verified-") else 1)


if __name__ == "__main__":
    main()
