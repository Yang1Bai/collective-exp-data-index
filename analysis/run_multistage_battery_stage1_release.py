"""Download and extract only the frozen Stage 1 battery outcomes.

The runner refuses every file ID outside the 141-row Stage 1 allowlist and
validates all pre-outcome hashes before making a network request. Stage 2 is
never downloaded or opened by this program.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import time
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

try:
    from analysis.extract_multistage_battery_capacity import CapacityExtractionError, extract_cell_endpoint
except ModuleNotFoundError:  # Direct execution as analysis/<script>.py.
    from extract_multistage_battery_capacity import CapacityExtractionError, extract_cell_endpoint


ROOT = Path(__file__).resolve().parents[1]
SELF = Path(__file__).resolve()
ALLOWLIST = ROOT / "analysis" / "results" / "multistage_battery_stage1_allowlist.csv"
ALLOWLIST_AUDIT = ROOT / "analysis" / "results" / "multistage_battery_stage1_allowlist_audit.json"
MAP = ROOT / "analysis" / "results" / "multistage_battery_file_map" / "archive_file_stage_map.csv"
SCHEMA = ROOT / "analysis" / "multistage_battery_endpoint_schema.json"
EXTRACTOR = ROOT / "analysis" / "extract_multistage_battery_capacity.py"
DESIGN = ROOT / "analysis" / "multistage_battery_cca_v2_design.json"
HEADER_REPORT = ROOT / "analysis" / "results" / "multistage_battery_header_schema.json"
RELEASE = ROOT / "analysis" / "multistage_battery_stage1_release.json"
INFRASTRUCTURE_AMENDMENT = ROOT / "analysis" / "MULTISTAGE_BATTERY_STAGE1_RELEASE_INFRASTRUCTURE_AMENDMENT.md"
DEFAULT_DIR = ROOT / "analysis" / "results" / "multistage_battery_stage1"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_release() -> tuple[dict, list[dict[str, str]]]:
    release = json.loads(RELEASE.read_text(encoding="utf-8"))
    expected = {
        "allowlist_sha256": sha256(ALLOWLIST),
        "allowlist_audit_sha256": sha256(ALLOWLIST_AUDIT),
        "archive_map_sha256": sha256(MAP),
        "endpoint_schema_sha256": sha256(SCHEMA),
        "endpoint_extractor_sha256": sha256(EXTRACTOR),
        "design_sha256": sha256(DESIGN),
        "header_report_sha256": sha256(HEADER_REPORT),
        "runner_sha256": sha256(SELF),
        "infrastructure_amendment_sha256": sha256(INFRASTRUCTURE_AMENDMENT),
    }
    for field, actual in expected.items():
        if release.get(field) != actual:
            raise AssertionError(f"Stage 1 release hash mismatch: {field}")
    if release.get("released_stage") != "1" or release.get("stage2_numeric_release") is not False:
        raise AssertionError("Release manifest does not enforce Stage 1-only access")

    with ALLOWLIST.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 141 or {row["stage"] for row in rows} != {"1"}:
        raise AssertionError("Allowlist is not exactly the 141 Stage 1 archives")
    with MAP.open("r", encoding="utf-8-sig", newline="") as handle:
        mapped = {row["file_id"]: row["stage"] for row in csv.DictReader(handle)}
    if any(mapped.get(row["file_id"]) != "1" for row in rows):
        raise AssertionError("Allowlist includes an archive not frozen as Stage 1")
    return release, rows


def download_file(url: str, destination: Path, expected_bytes: int, retries: int = 5) -> None:
    partial = destination.with_suffix(".zip.part")
    error: Exception | None = None
    for attempt in range(retries):
        try:
            partial.unlink(missing_ok=True)
            request = urllib.request.Request(url, headers={"User-Agent": "collective-exp-stage1-release/1.0"})
            with urllib.request.urlopen(request, timeout=180) as response, partial.open("wb") as handle:
                shutil.copyfileobj(response, handle, length=1024 * 1024)
            if partial.stat().st_size != expected_bytes:
                raise IOError(f"size mismatch: {partial.stat().st_size} != {expected_bytes}")
            os.replace(partial, destination)
            return
        except Exception as exc:  # pragma: no cover - network dependent
            error = exc
            partial.unlink(missing_ok=True)
            time.sleep(2 ** attempt)
    raise RuntimeError(f"download failed after {retries} attempts: {url}") from error


def process_one(row: dict[str, str], raw_dir: Path, checkpoint_dir: Path, keep_archive: bool) -> dict:
    file_id = row["file_id"]
    checkpoint = checkpoint_dir / f"{file_id}.json"
    if checkpoint.is_file():
        previous = json.loads(checkpoint.read_text(encoding="utf-8"))
        if previous.get("status") in {"extracted-stage1", "missing-endpoint"} and previous.get("archive_sha256") == row["archive_sha256"]:
            return previous
    archive = raw_dir / f"{file_id}.zip"
    started = time.time()
    try:
        if not archive.is_file() or archive.stat().st_size != int(row["archive_bytes"]):
            archive.unlink(missing_ok=True)
            download_file(row["download_url"], archive, int(row["archive_bytes"]))
        observed_hash = sha256(archive)
        if observed_hash != row["archive_sha256"]:
            raise IOError(f"archive SHA256 mismatch: {observed_hash}")
        endpoint = extract_cell_endpoint(archive)
        result = {
            "status": "extracted-stage1",
            "file_id": file_id,
            "archive_name": row["archive_name"],
            "archive_sha256": observed_hash,
            "serial_internal": row["serial_internal"],
            "serial": row["serial"],
            "stage": "1",
            "lab": row["lab"],
            "type": row["type"],
            "tp": row["tp"],
            "cell": row["cell"],
            "sampling": row["sampling"],
            "mapping_method": row["mapping_method"],
            "metadata_conflict_flags": row["metadata_conflict_flags"],
            **endpoint,
            "elapsed_seconds": round(time.time() - started, 3),
            "error": "",
        }
    except Exception as exc:  # pragma: no cover - archive dependent
        status = "missing-endpoint" if isinstance(exc, CapacityExtractionError) else "error"
        result = {
            "status": status,
            "file_id": file_id,
            "archive_name": row["archive_name"],
            "archive_sha256": row["archive_sha256"],
            "serial_internal": row["serial_internal"],
            "serial": row["serial"],
            "stage": "1",
            "lab": row["lab"],
            "type": row["type"],
            "tp": row["tp"],
            "cell": row["cell"],
            "sampling": row["sampling"],
            "mapping_method": row["mapping_method"],
            "metadata_conflict_flags": row["metadata_conflict_flags"],
            "elapsed_seconds": round(time.time() - started, 3),
            "error": f"{type(exc).__name__}: {exc}",
        }
    checkpoint.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if not keep_archive:
        try:
            archive.unlink(missing_ok=True)
        except PermissionError:
            # Cleanup is not scientific evidence. A validated checkpoint remains
            # authoritative; a later run may delete a temporarily locked ZIP.
            pass
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_DIR)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--keep-archives", action="store_true")
    args = parser.parse_args()
    release, allowlist = validate_release()
    output_dir = args.output_dir
    raw_dir = output_dir / "raw_archives"
    checkpoint_dir = output_dir / "checkpoint"
    raw_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict] = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = {
            pool.submit(process_one, row, raw_dir, checkpoint_dir, args.keep_archives): row["file_id"]
            for row in allowlist
        }
        for index, future in enumerate(as_completed(futures), start=1):
            result = future.result()
            results.append(result)
            print(f"[{index}/141] file_id={result['file_id']} status={result['status']}", flush=True)
    results.sort(key=lambda row: int(row["file_id"]))
    columns = sorted({key for row in results for key in row})
    table_path = output_dir / "stage1_capacity_endpoints.csv"
    with table_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(results)
    counts = Counter(row["status"] for row in results)
    processed = counts.get("extracted-stage1", 0) + counts.get("missing-endpoint", 0)
    audit = {
        "status": "verified-complete-stage1-release" if processed == 141 and counts.get("error", 0) == 0 else "incomplete-stage1-release",
        "released_stage": "1",
        "stage2_archives_downloaded": 0,
        "stage2_numeric_data_rows_opened": False,
        "allowlisted_archives": 141,
        "evaluable_stage1_cells": counts.get("extracted-stage1", 0),
        "missing_endpoint_stage1_cells": counts.get("missing-endpoint", 0),
        "status_counts": dict(counts),
        "endpoint_table_sha256": sha256(table_path),
        "release_manifest_sha256": sha256(RELEASE),
        "claim_guard": release["claim_guard"],
        "missing_endpoint_reasons": [row["error"] for row in results if row["status"] == "missing-endpoint"],
        "errors": [row["error"] for row in results if row["status"] == "error"],
    }
    audit_path = output_dir / "STAGE1_RELEASE_AUDIT.json"
    audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))
    raise SystemExit(0 if audit["status"].startswith("verified-") else 1)


if __name__ == "__main__":
    main()
