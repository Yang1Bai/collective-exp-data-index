"""Inspect battery archive metadata and CSV headers without reading data rows.

This is a pre-outcome audit tool.  For CSV members it reads exactly one
physical line with ``readline`` and never constructs a CSV reader.  Nonnumeric
``*_meta.txt`` members may be read in full.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "analysis" / "results" / "multistage_battery_header_schema.json"
EXPECTED_HEADER = "run_time,c_vol,c_cur,c_surf_temp,amb_temp,step_type"
MAX_HEADER_BYTES = 65_536


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_one_header(archive: zipfile.ZipFile, member: str) -> str:
    """Read one physical line and reject implausibly long or unterminated headers."""
    with archive.open(member) as handle:
        raw = handle.readline(MAX_HEADER_BYTES + 1)
    if len(raw) > MAX_HEADER_BYTES:
        raise ValueError(f"CSV header exceeds {MAX_HEADER_BYTES} bytes: {member}")
    if not raw.endswith((b"\n", b"\r")):
        raise ValueError(f"CSV first line is not newline terminated: {member}")
    return raw.decode("utf-8-sig", errors="strict").rstrip("\r\n")


def parse_meta(text: str) -> tuple[dict[str, str], dict[str, str]]:
    fields: dict[str, str] = {}
    descriptions: dict[str, str] = {}
    after_separator = False
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if re.fullmatch(r"-{5,}", line):
            after_separator = True
            continue
        if ":" not in line:
            continue
        key, value = (part.strip() for part in line.split(":", 1))
        target = descriptions if after_separator else fields
        target[key] = value
    return fields, descriptions


def classify_csv(name: str) -> str:
    base = Path(name).name
    for role in ("ET_T10", "ET_T23", "ET_T45", "AT_T10", "AT_T23", "AT_T45", "exCU", "CU", "ZYK"):
        if re.search(rf"_{re.escape(role)}\.csv$", base, flags=re.IGNORECASE):
            return role
    return "other"


def inspect_archive(file_id: int, expected_stage: str, path: Path) -> dict:
    if expected_stage not in {"1", "2"}:
        raise ValueError(f"Stage must be 1 or 2 for file_id={file_id}")
    csv_headers: dict[str, str] = {}
    meta_records: dict[str, dict] = {}
    with zipfile.ZipFile(path) as archive:
        members = sorted(archive.namelist())
        for member in members:
            lower = member.lower()
            if lower.endswith(".csv"):
                csv_headers[member] = read_one_header(archive, member)
            elif lower.endswith("_meta.txt"):
                with archive.open(member) as handle:
                    text = handle.read().decode("utf-8-sig", errors="strict")
                fields, descriptions = parse_meta(text)
                meta_records[member] = {"fields": fields, "column_descriptions": descriptions}

    roles = Counter(classify_csv(name) for name in csv_headers)
    primary: dict[str, dict] = {}
    for role in ("ET_T23", "AT_T23"):
        matches = [name for name in csv_headers if classify_csv(name) == role]
        if len(matches) != 1:
            raise ValueError(f"Expected exactly one {role} CSV in file_id={file_id}; found {len(matches)}")
        csv_name = matches[0]
        meta_name = re.sub(r"\.csv$", "_meta.txt", csv_name, flags=re.IGNORECASE)
        if meta_name not in meta_records:
            raise ValueError(f"Missing metadata companion for {csv_name}")
        setpoint = meta_records[meta_name]["fields"].get("Climate chamber temperature setpoint")
        if setpoint not in {"23°C", "23 °C"}:
            raise ValueError(f"{role} metadata setpoint is not 23°C in file_id={file_id}: {setpoint!r}")
        primary[role] = {"csv_member": csv_name, "meta_member": meta_name, "setpoint": setpoint}

    return {
        "file_id": file_id,
        "expected_stage": expected_stage,
        "archive_name": path.name,
        "archive_sha256": sha256(path),
        "archive_size_bytes": path.stat().st_size,
        "member_count": len(members),
        "csv_header_count": len(csv_headers),
        "meta_member_count": len(meta_records),
        "csv_role_counts": dict(sorted(roles.items())),
        "distinct_csv_headers": sorted(set(csv_headers.values())),
        "primary_endpoint_members": primary,
        "metadata_records": meta_records,
    }


def build_report(specs: list[tuple[int, str, Path]], created_utc: str) -> dict:
    archives = [inspect_archive(file_id, stage, path) for file_id, stage, path in specs]
    headers = sorted({header for item in archives for header in item["distinct_csv_headers"]})
    header_count = sum(item["csv_header_count"] for item in archives)
    errors: list[str] = []
    if headers != [EXPECTED_HEADER]:
        errors.append(f"unexpected CSV header profiles: {headers}")
    return {
        "status": "verified-header-only" if not errors else "invalid",
        "created_utc": created_utc,
        "audit_scope": "ZIP member names, complete nonnumeric *_meta.txt companions, and exactly the first physical line of each CSV member",
        "csv_read_method": "ZipExtFile.readline(MAX_HEADER_BYTES + 1) exactly once per CSV member; no csv/pandas parser constructed",
        "numeric_csv_data_rows_opened": False,
        "numeric_csv_data_rows_parsed": False,
        "stage1_numeric_outcomes_parsed": False,
        "stage2_numeric_outcomes_parsed": False,
        "inspected_archive_count": len(archives),
        "csv_header_lines_read": header_count,
        "expected_header": EXPECTED_HEADER,
        "distinct_csv_headers": headers,
        "archives": archives,
        "errors": errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--archive",
        nargs=3,
        action="append",
        metavar=("FILE_ID", "STAGE", "PATH"),
        required=True,
        help="Repeat for each header-only pilot archive.",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--created-utc", default=datetime.now(timezone.utc).isoformat())
    args = parser.parse_args()
    specs = [(int(file_id), stage, Path(path)) for file_id, stage, path in args.archive]
    report = build_report(specs, args.created_utc)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    raise SystemExit(0 if report["status"].startswith("verified-") else 1)


if __name__ == "__main__":
    main()
