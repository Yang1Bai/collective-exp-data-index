"""Outcome-blind schema audit for Battery Materials Property Database v2.0.

This script intentionally does not read table rows. It verifies the archive,
lists members, and records CSV headers / SQLite schemas only. A second,
format-specific audit is generated only after this schema report identifies
the released representation.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sqlite3
import tempfile
import zipfile
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DESIGN_PATH = HERE / "battery_conductivity_borrowing_design.json"
DEFAULT_ARCHIVE = (
    ROOT
    / "data"
    / "external"
    / "battery_conductivity_borrowing"
    / "battery-v2.zip"
)
DEFAULT_OUTPUT = (
    HERE / "results" / "battery_conductivity_archive_schema.json"
)


def file_hash(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def csv_header(raw: bytes) -> list[str]:
    text = raw.decode("utf-8-sig", errors="replace")
    reader = csv.reader(io.StringIO(text))
    return next(reader, [])


def sqlite_schema(raw: bytes) -> dict[str, list[str]]:
    descriptor, temporary_name = tempfile.mkstemp(suffix=".sqlite")
    temporary_path = Path(temporary_name)
    try:
        with open(descriptor, "wb", closefd=True) as handle:
            handle.write(raw)
        connection = sqlite3.connect(
            f"file:{temporary_path.as_posix()}?mode=ro", uri=True
        )
        try:
            tables = [
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table' ORDER BY name"
                )
            ]
            return {
                table: [
                    row[1]
                    for row in connection.execute(
                        f'PRAGMA table_info("{table}")'
                    )
                ]
                for table in tables
            }
        finally:
            connection.close()
    finally:
        temporary_path.unlink(missing_ok=True)


def member_schema(archive: zipfile.ZipFile, info: zipfile.ZipInfo) -> Any:
    suffix = Path(info.filename).suffix.lower()
    if suffix in {".csv", ".tsv"}:
        with archive.open(info) as handle:
            first_line = handle.readline()
        return {
            "kind": suffix.lstrip("."),
            "columns": csv_header(first_line),
        }
    if suffix in {".sqlite", ".sqlite3", ".db"}:
        with archive.open(info) as handle:
            raw = handle.read()
        return {"kind": "sqlite", "tables": sqlite_schema(raw)}
    if suffix == ".json":
        return {
            "kind": "json",
            "note": (
                "Keys are not inspected in the schema-only stage because "
                "streaming the released JSON could expose property values."
            ),
        }
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    expected = design["dataset"]
    archive_path = args.archive.resolve()
    if not archive_path.exists():
        raise FileNotFoundError(archive_path)
    if archive_path.stat().st_size != expected["expected_bytes"]:
        raise RuntimeError("Battery archive byte size does not match freeze")
    md5 = file_hash(archive_path, "md5")
    if md5 != expected["expected_md5"]:
        raise RuntimeError("Battery archive MD5 does not match freeze")

    members: list[dict[str, Any]] = []
    with zipfile.ZipFile(archive_path) as archive:
        bad_member = archive.testzip()
        if bad_member is not None:
            raise RuntimeError(f"Corrupt ZIP member: {bad_member}")
        for info in archive.infolist():
            record: dict[str, Any] = {
                "name": info.filename,
                "bytes": info.file_size,
                "compressed_bytes": info.compress_size,
                "is_directory": info.is_dir(),
            }
            if not info.is_dir():
                schema = member_schema(archive, info)
                if schema is not None:
                    record["schema"] = schema
            members.append(record)

    report = {
        "status": "schema-audited-outcome-blind",
        "design_sha256": file_hash(DESIGN_PATH, "sha256"),
        "archive": str(archive_path),
        "archive_bytes": archive_path.stat().st_size,
        "archive_md5": md5,
        "archive_sha256": file_hash(archive_path, "sha256"),
        "numeric_property_values_read": False,
        "members": members,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
