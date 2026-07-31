"""Independently verify the outcome-blind battery borrowing audit."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd


HERE = Path(__file__).resolve().parent
DESIGN = HERE / "battery_conductivity_borrowing_design.json"
AUDIT = HERE / "results" / "battery_conductivity_preoutcome_audit.json"
METADATA = (
    HERE / "results" / "battery_conductivity_metadata_no_outcomes.csv"
)
FORBIDDEN = {"Value", "Raw_value", "value", "Title", "Journal"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    design = json.loads(DESIGN.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    metadata = pd.read_csv(METADATA, dtype=str, keep_default_na=False)

    if audit["design_sha256"] != sha256(DESIGN):
        raise AssertionError("Design hash changed after audit")
    if audit["metadata_sha256"] != sha256(METADATA):
        raise AssertionError("Outcome-free metadata hash mismatch")
    if audit["numeric_property_values_read"] is not False:
        raise AssertionError("Audit claims numeric outcome access")
    if FORBIDDEN.intersection(audit["read_columns"]):
        raise AssertionError("Audit read a forbidden column")
    if FORBIDDEN.intersection(metadata.columns):
        raise AssertionError("Outcome-free metadata contains forbidden data")
    if len(metadata) != audit["all_records"]:
        raise AssertionError("Metadata row count mismatch")

    required = {
        "property_class",
        "material_normalized",
        "doi_normalized",
        "unit_text",
        "condition_text",
        "has_rate",
        "has_cycle",
        "has_temperature",
        "cycle_number",
        "current_value_number",
        "is_early_cycle",
        "is_gravimetric_capacity",
    }
    if not required.issubset(metadata.columns):
        raise AssertionError("Outcome-free metadata is incomplete")

    expected_status = (
        "eligible-preoutcome"
        if all(audit["gate_checks"].values())
        else "ineligible-preoutcome"
    )
    if audit["status"] != expected_status:
        raise AssertionError("Pre-outcome decision does not match gates")

    claim = {
        "status": "verified-preoutcome",
        "eligibility": audit["status"],
        "design_sha256": audit["design_sha256"],
        "metadata_sha256": audit["metadata_sha256"],
        "failed_gates": audit["errors"],
        "claim_guard": design["claim_guard"],
    }
    print(json.dumps(claim, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
