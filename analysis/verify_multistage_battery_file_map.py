"""Independently verify the metadata-only Figshare archive-to-stage map."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


EXPECTED_ROWS = 279
EXPECTED_STAGES = {"1": 141, "2": 138}


def sha256(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest


def verify(directory: Path) -> dict:
    complete_path = directory / "COMPLETE.json"
    map_path = directory / "archive_file_stage_map.csv"
    errors = []
    if not complete_path.is_file() or not map_path.is_file():
        return {"status": "invalid", "errors": ["COMPLETE.json or archive_file_stage_map.csv is missing"]}
    complete = json.loads(complete_path.read_text(encoding="utf-8"))
    with map_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    file_ids = [row["file_id"] for row in rows]
    serials = [row["serial_internal"] for row in rows]
    mapping_keys = [(row["serial_internal"], row["serial"]) for row in rows]
    stage_serial_keys = [(row["stage"], row["serial"]) for row in rows]
    stages = Counter(row["stage"] for row in rows)
    if complete.get("status") != "verified-complete-metadata-only-map":
        errors.append("remote completion status is not verified-complete-metadata-only-map")
    if len(rows) != EXPECTED_ROWS:
        errors.append(f"map rows {len(rows)} != {EXPECTED_ROWS}")
    if len(set(file_ids)) != EXPECTED_ROWS:
        errors.append("file IDs are not unique")
    if len(set(mapping_keys)) != EXPECTED_ROWS:
        errors.append("(internal serial, serial) mapping keys are not unique")
    if len(set(stage_serial_keys)) != EXPECTED_ROWS:
        errors.append("(stage, serial) mapping keys are not unique")
    if dict(stages) != EXPECTED_STAGES:
        errors.append(f"stage counts changed: {dict(stages)}")
    if any(row["status"] != "mapped-metadata-only" for row in rows):
        errors.append("at least one archive is not metadata-only mapped")
    if any(row["numeric_csv_entries_opened"].lower() != "false" for row in rows):
        errors.append("at least one record claims a numeric CSV member was opened")
    if any(not row["mapping_evidence_entry"].lower().endswith("_meta.txt") for row in rows):
        errors.append("at least one mapping does not cite a *_meta.txt member")
    if any(len(row["archive_sha256"]) != 64 for row in rows):
        errors.append("at least one archive SHA256 is missing")
    allowed_methods = {
        "exact-archive-serial-plus-internal-serial",
        "archive-serial-plus-complement-of-exactly-mapped-twin-stage",
        "archive-serial-plus-validated-lab-date-envelope",
    }
    if any(row.get("mapping_method") not in allowed_methods for row in rows):
        errors.append("at least one archive uses an unapproved mapping method")
    conflict_counts = Counter(
        flag
        for row in rows
        for flag in row.get("metadata_conflict_flags", "").split(";")
        if flag
    )
    method_counts = Counter(row.get("mapping_method", "") for row in rows)
    if complete.get("metadata_conflict_counts") != dict(conflict_counts):
        errors.append("metadata conflict counts differ from COMPLETE.json")
    if complete.get("mapping_method_counts") != dict(method_counts):
        errors.append("mapping method counts differ from COMPLETE.json")
    date_rows = [
        row for row in rows
        if row.get("mapping_method") == "archive-serial-plus-validated-lab-date-envelope"
    ]
    if date_rows and not complete.get("validated_lab_date_envelopes"):
        errors.append("date-envelope mappings lack a frozen calibration audit")
    if complete.get("map_csv_sha256") != sha256(map_path):
        errors.append("map CSV hash differs from COMPLETE.json")
    return {
        "status": "verified-complete-metadata-only-map" if not errors else "invalid",
        "rows": len(rows),
        "unique_file_ids": len(set(file_ids)),
        "unique_internal_serials": len(set(serials)),
        "unique_internal_serial_serial_pairs": len(set(mapping_keys)),
        "unique_stage_serial_pairs": len(set(stage_serial_keys)),
        "stage_counts": dict(stages),
        "mapping_method_counts": dict(method_counts),
        "metadata_conflict_counts": dict(conflict_counts),
        "numeric_csv_entries_opened": False,
        "map_csv_sha256": sha256(map_path),
        "errors": errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    parser.add_argument("--output", type=Path, help="Optional path for the verification JSON.")
    args = parser.parse_args()
    result = verify(args.directory.resolve())
    rendered = json.dumps(result, indent=2)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    raise SystemExit(0 if result["status"].startswith("verified-") else 1)


if __name__ == "__main__":
    main()
