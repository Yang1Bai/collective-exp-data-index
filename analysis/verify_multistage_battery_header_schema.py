"""Verify the frozen header-only audit and endpoint schema."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from analysis.inspect_multistage_battery_headers import EXPECTED_HEADER, build_report
except ModuleNotFoundError:  # Direct execution as analysis/<script>.py.
    from inspect_multistage_battery_headers import EXPECTED_HEADER, build_report


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "analysis" / "results" / "multistage_battery_header_schema.json"
SCHEMA = ROOT / "analysis" / "multistage_battery_endpoint_schema.json"


def verify(report_path: Path = REPORT, archive_specs: list[tuple[int, str, Path]] | None = None) -> dict:
    errors: list[str] = []
    report = json.loads(report_path.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    if report.get("status") != "verified-header-only":
        errors.append("header report status is not verified-header-only")
    if report.get("numeric_csv_data_rows_opened") is not False:
        errors.append("header report does not preserve the data-row access guard")
    if report.get("numeric_csv_data_rows_parsed") is not False:
        errors.append("header report claims numeric rows were parsed")
    if report.get("inspected_archive_count") != 3:
        errors.append("expected three independently selected header-audit archives")
    if report.get("csv_header_lines_read") != 32:
        errors.append("expected 32 inspected CSV header lines")
    if report.get("distinct_csv_headers") != [EXPECTED_HEADER]:
        errors.append("CSV header profile changed")
    if schema.get("required_csv_header") != EXPECTED_HEADER.split(","):
        errors.append("endpoint schema required columns changed")
    extractor = schema.get("capacity_extractor", {})
    if extractor.get("charge_step_type") != 21 or extractor.get("discharge_step_type") != 22:
        errors.append("paper-defined capacity step codes changed")
    if "(Q_charge + Q_discharge)/2" not in extractor.get("rpt_capacity_Ah", ""):
        errors.append("RPT mean-capacity definition changed")

    independent_match = None
    if archive_specs:
        reconstructed = build_report(archive_specs, report["created_utc"])
        independent_match = reconstructed == report
        if not independent_match:
            errors.append("independent header-only reconstruction differs from frozen report")

    return {
        "status": "verified-header-and-endpoint-schema" if not errors else "invalid",
        "inspected_archives": report.get("inspected_archive_count"),
        "csv_header_lines_read": report.get("csv_header_lines_read"),
        "numeric_csv_data_rows_opened": False,
        "independent_archive_reconstruction": independent_match,
        "primary_endpoint": extractor.get("primary_endpoint"),
        "errors": errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", nargs=3, action="append", metavar=("FILE_ID", "STAGE", "PATH"))
    args = parser.parse_args()
    specs = None
    if args.archive:
        specs = [(int(file_id), stage, Path(path)) for file_id, stage, path in args.archive]
    result = verify(archive_specs=specs)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["status"].startswith("verified-") else 1)


if __name__ == "__main__":
    main()
