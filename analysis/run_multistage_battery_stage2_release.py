"""Authorized Stage 2 endpoint release; validates the complete pre-outcome freeze."""

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

import pandas as pd

try:
    from analysis.extract_multistage_battery_capacity import CapacityExtractionError, extract_cell_endpoint
    from analysis.freeze_multistage_battery_stage1_source import canonical_group
except ModuleNotFoundError:
    from extract_multistage_battery_capacity import CapacityExtractionError, extract_cell_endpoint
    from freeze_multistage_battery_stage1_source import canonical_group


ROOT = Path(__file__).resolve().parents[1]
SELF = Path(__file__).resolve()
ALLOWLIST = ROOT / "analysis" / "results" / "multistage_battery_stage2_allowlist.csv"
ALLOWLIST_AUDIT = ROOT / "analysis" / "results" / "multistage_battery_stage2_allowlist_audit.json"
MAP = ROOT / "analysis" / "results" / "multistage_battery_file_map" / "archive_file_stage_map.csv"
META = ROOT / "analysis" / "results" / "multistage_battery_file_map" / "experiments_meta.csv"
SCHEMA = ROOT / "analysis" / "multistage_battery_endpoint_schema.json"
EXTRACTOR = ROOT / "analysis" / "extract_multistage_battery_capacity.py"
DESIGN = ROOT / "analysis" / "multistage_battery_cca_v2_design.json"
HEADER_REPORT = ROOT / "analysis" / "results" / "multistage_battery_header_schema.json"
FREEZE_DIR = ROOT / "analysis" / "results" / "multistage_battery_stage1_source_freeze"
SOURCE_FREEZE = FREEZE_DIR / "STAGE1_SOURCE_FREEZE.json"
SOURCE_FEATURES = FREEZE_DIR / "stage2_outcome_free_source_features.csv"
SPLITS = FREEZE_DIR / "stage2_outer_split_plan.json"
APPLICABILITY = FREEZE_DIR / "stage2_applicability_plan.csv"
APPLICABILITY_AUDIT = FREEZE_DIR / "STAGE2_APPLICABILITY_FREEZE.json"
CONTROLS = FREEZE_DIR / "stage2_frozen_control_features.csv"
CONTROL_AUDIT = FREEZE_DIR / "STAGE2_CONTROL_FEATURE_FREEZE.json"
CARDS = ROOT / "analysis" / "multistage_battery_source_inspiration_cards.json"
ANALYSIS_RUNNER = ROOT / "analysis" / "run_multistage_battery_stage2_analysis.py"
ENCODING_AMENDMENT = ROOT / "analysis" / "MULTISTAGE_BATTERY_STAGE2_HEADER_EXTENSION_AMENDMENT_V4.md"
RELEASE = ROOT / "analysis" / "multistage_battery_stage2_release.json"
DEFAULT_DIR = ROOT / "analysis" / "results" / "multistage_battery_stage2"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_release() -> tuple[dict, list[dict[str, str]]]:
    release = json.loads(RELEASE.read_text(encoding="utf-8"))
    expected = {
        "allowlist_sha256": sha256(ALLOWLIST), "allowlist_audit_sha256": sha256(ALLOWLIST_AUDIT),
        "archive_map_sha256": sha256(MAP), "endpoint_schema_sha256": sha256(SCHEMA),
        "endpoint_extractor_sha256": sha256(EXTRACTOR), "design_sha256": sha256(DESIGN),
        "header_report_sha256": sha256(HEADER_REPORT), "stage1_source_freeze_sha256": sha256(SOURCE_FREEZE),
        "stage2_source_features_sha256": sha256(SOURCE_FEATURES), "outer_split_plan_sha256": sha256(SPLITS),
        "applicability_plan_sha256": sha256(APPLICABILITY), "applicability_audit_sha256": sha256(APPLICABILITY_AUDIT),
        "control_features_sha256": sha256(CONTROLS), "control_audit_sha256": sha256(CONTROL_AUDIT),
        "hypothesis_cards_sha256": sha256(CARDS), "analysis_runner_sha256": sha256(ANALYSIS_RUNNER),
        "metadata_encoding_amendment_sha256": sha256(ENCODING_AMENDMENT),
        "release_runner_sha256": sha256(SELF),
    }
    for field, actual in expected.items():
        if release.get(field) != actual:
            raise AssertionError(f"Stage 2 release hash mismatch: {field}")
    if release.get("released_stage") != "2" or release.get("authorized_archives") != 138:
        raise AssertionError("Stage 2 release authorization is invalid")
    with ALLOWLIST.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 138 or {row["stage"] for row in rows} != {"2"}:
        raise AssertionError("Stage 2 allowlist is not exactly 138 Stage 2 archives")
    return release, rows


def download_file(url: str, destination: Path, expected_bytes: int, retries: int = 5) -> None:
    partial = destination.with_suffix(".zip.part")
    error: Exception | None = None
    for attempt in range(retries):
        try:
            partial.unlink(missing_ok=True)
            request = urllib.request.Request(url, headers={"User-Agent": "collective-exp-stage2-release/1.0"})
            with urllib.request.urlopen(request, timeout=180) as response, partial.open("wb") as handle:
                shutil.copyfileobj(response, handle, length=1024 * 1024)
            if partial.stat().st_size != expected_bytes:
                raise IOError(f"size mismatch: {partial.stat().st_size} != {expected_bytes}")
            os.replace(partial, destination)
            return
        except Exception as exc:
            error = exc
            partial.unlink(missing_ok=True)
            time.sleep(2 ** attempt)
    raise RuntimeError(f"download failed after {retries} attempts: {url}") from error


def process_one(row: dict[str, str], raw_dir: Path, checkpoint_dir: Path, keep_archive: bool) -> dict:
    file_id = row["file_id"]
    checkpoint = checkpoint_dir / f"{file_id}.json"
    if checkpoint.is_file():
        previous = json.loads(checkpoint.read_text(encoding="utf-8"))
        success_reusable = previous.get("status") == "extracted-stage2"
        missing_reusable = (
            previous.get("status") == "missing-endpoint"
            and previous.get("endpoint_extractor_sha256") == sha256(EXTRACTOR)
        )
        if (success_reusable or missing_reusable) and previous.get("archive_sha256") == row["archive_sha256"]:
            return previous
    archive = raw_dir / f"{file_id}.zip"
    started = time.time()
    try:
        if not archive.is_file() or archive.stat().st_size != int(row["archive_bytes"]):
            archive.unlink(missing_ok=True)
            download_file(row["download_url"], archive, int(row["archive_bytes"]))
        observed = sha256(archive)
        if observed != row["archive_sha256"]:
            raise IOError(f"archive SHA256 mismatch: {observed}")
        endpoint = extract_cell_endpoint(archive)
        result = {
            "status": "extracted-stage2", "file_id": file_id,
            "archive_name": row["archive_name"], "archive_sha256": observed,
            "serial_internal": row["serial_internal"], "serial": row["serial"], "stage": "2",
            "lab": row["lab"], "type": row["type"], "tp": row["tp"], "cell": row["cell"],
            "sampling": row["sampling"], "mapping_method": row["mapping_method"],
            "metadata_conflict_flags": row["metadata_conflict_flags"], **endpoint,
            "endpoint_extractor_sha256": sha256(EXTRACTOR),
            "elapsed_seconds": round(time.time() - started, 3), "error": "",
        }
    except Exception as exc:
        result = {
            "status": "missing-endpoint" if isinstance(exc, CapacityExtractionError) else "error",
            "file_id": file_id, "archive_name": row["archive_name"],
            "archive_sha256": row["archive_sha256"], "serial_internal": row["serial_internal"],
            "serial": row["serial"], "stage": "2", "lab": row["lab"], "type": row["type"],
            "tp": row["tp"], "cell": row["cell"], "sampling": row["sampling"],
            "mapping_method": row["mapping_method"], "metadata_conflict_flags": row["metadata_conflict_flags"],
            "endpoint_extractor_sha256": sha256(EXTRACTOR),
            "elapsed_seconds": round(time.time() - started, 3), "error": f"{type(exc).__name__}: {exc}",
        }
    checkpoint.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if not keep_archive:
        try:
            archive.unlink(missing_ok=True)
        except PermissionError:
            pass
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_DIR)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--keep-archives", action="store_true")
    args = parser.parse_args()
    release, allowlist = validate_release()
    raw_dir = args.output_dir / "raw_archives"
    checkpoint_dir = args.output_dir / "checkpoint"
    raw_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict] = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = {pool.submit(process_one, row, raw_dir, checkpoint_dir, args.keep_archives): row["file_id"] for row in allowlist}
        for index, future in enumerate(as_completed(futures), start=1):
            result = future.result()
            results.append(result)
            print(f"[{index}/138] file_id={result['file_id']} status={result['status']}", flush=True)
    results.sort(key=lambda row: int(row["file_id"]))
    columns = sorted({key for row in results for key in row})
    table_path = args.output_dir / "stage2_capacity_endpoints.csv"
    with table_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore", lineterminator="\n")
        writer.writeheader(); writer.writerows(results)

    table = pd.DataFrame(results)
    meta = pd.read_csv(META, dtype={"serial_internal": str, "serial": str, "stage": str})
    meta = meta.loc[meta["stage"].eq("2")].copy()
    meta["condition_group"] = meta.apply(canonical_group, axis=1)
    coverage = table.merge(meta[["serial_internal", "serial", "condition_group"]], on=["serial_internal", "serial"], validate="one_to_one")
    evaluable = coverage.loc[coverage["status"].eq("extracted-stage2")]
    per_group = evaluable.groupby("condition_group").size()
    all_groups = sorted(meta["condition_group"].unique())
    minimum = min(int(per_group.get(group, 0)) for group in all_groups)
    counts = Counter(table["status"])
    accounted = counts.get("extracted-stage2", 0) + counts.get("missing-endpoint", 0)
    coverage_pass = len(evaluable) / 138 >= 0.80 and minimum >= 2 and len(all_groups) == 23
    complete = accounted == 138 and counts.get("error", 0) == 0
    status = "verified-complete-stage2-release" if complete and coverage_pass else ("non-evaluable-stage2-release" if complete else "incomplete-stage2-release")
    audit = {
        "status": status, "released_stage": "2", "allowlisted_archives": 138,
        "status_counts": dict(counts), "evaluable_stage2_cells": len(evaluable),
        "missing_endpoint_stage2_cells": counts.get("missing-endpoint", 0),
        "stage2_condition_groups": len(all_groups), "minimum_cells_per_condition_group": minimum,
        "coverage_fraction": len(evaluable) / 138, "coverage_gate_pass": coverage_pass,
        "endpoint_table_sha256": sha256(table_path), "release_manifest_sha256": sha256(RELEASE),
        "missing_endpoint_reasons": table.loc[table["status"].eq("missing-endpoint"), "error"].tolist(),
        "errors": table.loc[table["status"].eq("error"), "error"].tolist(),
        "claim_guard": release["claim_guard"],
    }
    audit_path = args.output_dir / "STAGE2_RELEASE_AUDIT.json"
    audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))
    raise SystemExit(0 if status.startswith("verified-") else 1)


if __name__ == "__main__":
    main()
