"""Map Figshare archive IDs to battery stages using metadata text only.

The program downloads each ZIP but opens only ``*_meta.txt`` members. Numeric
CSV members are never opened. Results are checkpointed so a remote run can
resume after interruption without redownloading completed archives.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import time
import urllib.request
import zipfile
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTICLE_ID = 25975315
ARTICLE_API = f"https://api.figshare.com/v2/articles/{ARTICLE_ID}"
EXPECTED_METADATA_SHA256 = "3a0dcf34dd881be49ad06b40257ce2288a2601c3e62b1a27bb30f456b9931fc4"
EXPECTED_FILE_COUNT = 280
EXPECTED_ARCHIVE_COUNT = 279
EXPECTED_STAGE_COUNTS = {"1": 141, "2": 138}
SERIAL_RE = re.compile(r"^Internal cell serial:\s*(.+?)\s*$", re.MULTILINE)
LAB_RE = re.compile(r"^Laboratory identifier:\s*(.+?)\s*$", re.MULTILINE)
TESTPOINT_RE = re.compile(r"^Testpoint:\s*(.+?)\s*$", re.MULTILINE)
START_DATE_RE = re.compile(r"^Measurement start date:\s*(.+?)\s*$", re.MULTILINE)
TESTPOINT_TOKEN_RE = re.compile(r"(?:TP_)?([kz]\d{2})", re.IGNORECASE)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch_bytes(url: str, retries: int = 4) -> bytes:
    error: Exception | None = None
    for attempt in range(retries):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "collective-exp-preoutcome-audit/1.0"})
            with urllib.request.urlopen(request, timeout=120) as response:
                return response.read()
        except Exception as exc:  # pragma: no cover - network dependent
            error = exc
            time.sleep(2 ** attempt)
    raise RuntimeError(f"download failed after {retries} attempts: {url}") from error


def download_file(url: str, destination: Path, expected_bytes: int, retries: int = 4) -> None:
    error: Exception | None = None
    partial = destination.with_suffix(destination.suffix + ".part")
    for attempt in range(retries):
        try:
            partial.unlink(missing_ok=True)
            request = urllib.request.Request(url, headers={"User-Agent": "collective-exp-preoutcome-audit/1.0"})
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


def parse_metadata_text(text: str) -> dict[str, str]:
    fields = {}
    for name, pattern in [
        ("internal_serial", SERIAL_RE),
        ("laboratory", LAB_RE),
        ("testpoint", TESTPOINT_RE),
        ("measurement_start_date", START_DATE_RE),
    ]:
        match = pattern.search(text)
        if match:
            fields[name] = match.group(1).strip()
    if "internal_serial" not in fields:
        raise ValueError("Internal cell serial is absent from archive metadata")
    return fields


def normalize_testpoint_token(value: str) -> str | None:
    match = TESTPOINT_TOKEN_RE.search(value)
    return match.group(1).lower() if match else None


def inspect_archive(
    file_record: dict,
    rows_by_key: dict[tuple[str, str], dict],
    rows_by_serial: dict[str, list[dict]],
    download_dir: Path,
    keep: bool,
) -> dict:
    file_id = int(file_record["id"])
    archive = download_dir / f"{file_id}.zip"
    started = time.time()
    try:
        if not archive.is_file() or archive.stat().st_size != int(file_record["size"]):
            archive.unlink(missing_ok=True)
            download_file(file_record["download_url"], archive, int(file_record["size"]))
        archive_hash = sha256(archive)
        with zipfile.ZipFile(archive) as zipped:
            meta_entries = sorted(
                (
                    entry for entry in zipped.infolist()
                    if not entry.is_dir() and entry.filename.lower().endswith("_meta.txt")
                ),
                key=lambda entry: entry.filename,
            )
            csv_entries = [
                entry for entry in zipped.infolist()
                if not entry.is_dir() and entry.filename.lower().endswith(".csv")
            ]
            if not meta_entries:
                raise ValueError("archive has no *_meta.txt member")
            evidence = meta_entries[0]
            with zipped.open(evidence, "r") as handle:
                text = handle.read(65536).decode("utf-8-sig", errors="replace")
            parsed = parse_metadata_text(text)
            internal = parsed["internal_serial"]
            archive_serial = Path(file_record["name"]).stem
            key = (internal, archive_serial)
            candidates = rows_by_serial.get(archive_serial, [])
            if key not in rows_by_key:
                return {
                    "status": "unresolved-metadata-conflict",
                    "file_id": file_id,
                    "archive_name": file_record["name"],
                    "archive_bytes": int(file_record["size"]),
                    "archive_sha256": archive_hash,
                    "zip_entries": len(zipped.infolist()),
                    "metadata_entries": len(meta_entries),
                    "numeric_csv_entries_present_but_not_opened": len(csv_entries),
                    "numeric_csv_entries_opened": False,
                    "mapping_evidence_entry": evidence.filename,
                    "archive_internal_serial": internal,
                    "archive_testpoint_raw": parsed.get("testpoint", ""),
                    "archive_lab_raw": parsed.get("laboratory", ""),
                    "measurement_start_date": parsed.get("measurement_start_date", ""),
                    "candidate_stages": ";".join(sorted(row["stage"] for row in candidates)),
                    "mapping_method": "pending-complementary-stage-resolution",
                    "metadata_conflict_flags": "archive_internal_serial_conflicts_with_experiments_meta",
                    "error": f"exact (internal serial, archive serial) key {key!r} is absent",
                    "elapsed_seconds": round(time.time() - started, 3),
                }
            row = rows_by_key[key]
            if parsed.get("laboratory") and parsed["laboratory"] != row["lab"]:
                raise ValueError(f"laboratory {parsed['laboratory']!r} != metadata {row['lab']!r}")
            expected_tp = f"{row['type']}{int(float(row['tp'])):02d}"
            flags = []
            if parsed.get("testpoint"):
                raw_testpoint = parsed["testpoint"]
                if normalize_testpoint_token(raw_testpoint) != expected_tp.lower():
                    flags.append("testpoint_metadata_conflict")
                elif raw_testpoint.lower() != expected_tp.lower():
                    flags.append("testpoint_format_variant")
            return {
                "status": "mapped-metadata-only",
                "file_id": file_id,
                "archive_name": file_record["name"],
                "archive_bytes": int(file_record["size"]),
                "archive_sha256": archive_hash,
                "zip_entries": len(zipped.infolist()),
                "metadata_entries": len(meta_entries),
                "numeric_csv_entries_present_but_not_opened": len(csv_entries),
                "numeric_csv_entries_opened": False,
                "mapping_evidence_entry": evidence.filename,
                "archive_internal_serial": internal,
                "archive_testpoint_raw": parsed.get("testpoint", ""),
                "archive_lab_raw": parsed.get("laboratory", ""),
                "measurement_start_date": parsed.get("measurement_start_date", ""),
                "serial_internal": row["serial_internal"],
                "serial": row["serial"],
                "stage": row["stage"],
                "lab": row["lab"],
                "type": row["type"],
                "tp": row["tp"],
                "cell": row["cell"],
                "sampling": row["sampling"],
                "mapping_method": "exact-archive-serial-plus-internal-serial",
                "metadata_conflict_flags": ";".join(flags),
                "error": "",
                "elapsed_seconds": round(time.time() - started, 3),
            }
    except Exception as exc:
        return {
            "status": "error",
            "file_id": file_id,
            "archive_name": file_record.get("name"),
            "archive_bytes": int(file_record.get("size", 0)),
            "numeric_csv_entries_opened": False,
            "error": f"{type(exc).__name__}: {exc}",
            "elapsed_seconds": round(time.time() - started, 3),
        }
    finally:
        if not keep:
            archive.unlink(missing_ok=True)


def resolve_complementary_stages(rows: list[dict], rows_by_serial: dict[str, list[dict]]) -> list[dict]:
    """Resolve a conflicting archive only from its already mapped twin.

    A filename reused across Stage 1 and Stage 2 has exactly two metadata
    candidates. If one archive with that name is mapped by the exact composite
    key, the other archive is assigned to the remaining stage. No file order,
    numeric CSV member, date cutoff, or outcome is used.
    """
    mapped_stages: dict[str, set[str]] = {}
    for row in rows:
        if row.get("status") == "mapped-metadata-only":
            mapped_stages.setdefault(row["archive_name"], set()).add(row["stage"])
    resolved = []
    for row in rows:
        if row.get("status") != "unresolved-metadata-conflict":
            resolved.append(row)
            continue
        archive_serial = Path(row["archive_name"]).stem
        candidates = rows_by_serial.get(archive_serial, [])
        candidate_stages = {candidate["stage"] for candidate in candidates}
        known_stages = mapped_stages.get(row["archive_name"], set())
        remaining = candidate_stages - known_stages
        if len(candidates) != 2 or candidate_stages != {"1", "2"} or len(known_stages) != 1 or len(remaining) != 1:
            resolved.append(row)
            continue
        stage = next(iter(remaining))
        candidate = next(candidate for candidate in candidates if candidate["stage"] == stage)
        updated = dict(row)
        updated.update({
            "status": "mapped-metadata-only",
            "serial_internal": candidate["serial_internal"],
            "serial": candidate["serial"],
            "stage": candidate["stage"],
            "lab": candidate["lab"],
            "type": candidate["type"],
            "tp": candidate["tp"],
            "cell": candidate["cell"],
            "sampling": candidate["sampling"],
            "mapping_method": "archive-serial-plus-complement-of-exactly-mapped-twin-stage",
            "error": "",
        })
        resolved.append(updated)
        mapped_stages.setdefault(row["archive_name"], set()).add(stage)
    return resolved


def resolve_with_validated_date_envelopes(
    rows: list[dict],
    rows_by_serial: dict[str, list[dict]],
    minimum_per_stage: int = 20,
) -> tuple[list[dict], dict]:
    """Resolve only residual conflicts inside non-overlapping lab date envelopes.

    Envelopes are calibrated exclusively from rows mapped without dates by the
    exact-key or complementary-twin rules. Each lab must have at least the
    frozen minimum in both stages, and the two closed intervals must not
    overlap. An unresolved row must fall inside exactly one interval.
    """
    allowed_calibration_methods = {
        "exact-archive-serial-plus-internal-serial",
        "archive-serial-plus-complement-of-exactly-mapped-twin-stage",
    }
    dates: dict[tuple[str, str], list[datetime]] = {}
    for row in rows:
        if row.get("status") != "mapped-metadata-only":
            continue
        if row.get("mapping_method") not in allowed_calibration_methods:
            continue
        raw_date = row.get("measurement_start_date", "")
        if not raw_date:
            continue
        try:
            parsed_date = datetime.strptime(raw_date, "%d.%m.%Y")
        except ValueError:
            continue
        dates.setdefault((row["lab"], row["stage"]), []).append(parsed_date)

    envelopes: dict[str, dict[str, dict]] = {}
    labs = {lab for lab, _ in dates}
    for lab in sorted(labs):
        stage1 = dates.get((lab, "1"), [])
        stage2 = dates.get((lab, "2"), [])
        if len(stage1) < minimum_per_stage or len(stage2) < minimum_per_stage:
            continue
        intervals = {
            "1": (min(stage1), max(stage1)),
            "2": (min(stage2), max(stage2)),
        }
        if not (intervals["1"][1] < intervals["2"][0] or intervals["2"][1] < intervals["1"][0]):
            continue
        envelopes[lab] = {
            stage: {
                "n": len(dates[(lab, stage)]),
                "min": interval[0].date().isoformat(),
                "max": interval[1].date().isoformat(),
            }
            for stage, interval in intervals.items()
        }

    resolved = []
    for row in rows:
        if row.get("status") != "unresolved-metadata-conflict":
            resolved.append(row)
            continue
        lab = row.get("archive_lab_raw", "")
        raw_date = row.get("measurement_start_date", "")
        if lab not in envelopes or not raw_date:
            resolved.append(row)
            continue
        try:
            parsed_date = datetime.strptime(raw_date, "%d.%m.%Y").date()
        except ValueError:
            resolved.append(row)
            continue
        matching_stages = []
        for stage, interval in envelopes[lab].items():
            if datetime.fromisoformat(interval["min"]).date() <= parsed_date <= datetime.fromisoformat(interval["max"]).date():
                matching_stages.append(stage)
        archive_serial = Path(row["archive_name"]).stem
        candidates = rows_by_serial.get(archive_serial, [])
        candidate_stages = {candidate["stage"] for candidate in candidates}
        if len(matching_stages) != 1 or len(candidates) != 2 or candidate_stages != {"1", "2"}:
            resolved.append(row)
            continue
        stage = matching_stages[0]
        candidate = next(candidate for candidate in candidates if candidate["stage"] == stage)
        flags = [flag for flag in row.get("metadata_conflict_flags", "").split(";") if flag]
        flags.append("validated_lab_date_envelope_required_after_both_twin_internal_serials_conflicted")
        updated = dict(row)
        updated.update({
            "status": "mapped-metadata-only",
            "serial_internal": candidate["serial_internal"],
            "serial": candidate["serial"],
            "stage": candidate["stage"],
            "lab": candidate["lab"],
            "type": candidate["type"],
            "tp": candidate["tp"],
            "cell": candidate["cell"],
            "sampling": candidate["sampling"],
            "mapping_method": "archive-serial-plus-validated-lab-date-envelope",
            "metadata_conflict_flags": ";".join(dict.fromkeys(flags)),
            "error": "",
        })
        resolved.append(updated)
    return resolved, envelopes


def write_checkpoint(path: Path, rows: list[dict]) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    os.replace(temp, path)


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = [
        "file_id", "archive_name", "archive_bytes", "archive_sha256",
        "zip_entries", "metadata_entries", "numeric_csv_entries_present_but_not_opened",
        "numeric_csv_entries_opened", "mapping_evidence_entry", "archive_internal_serial",
        "archive_testpoint_raw", "archive_lab_raw", "measurement_start_date",
        "serial_internal", "serial", "stage", "lab", "type", "tp", "cell", "sampling",
        "mapping_method", "metadata_conflict_flags", "candidate_stages", "status",
        "error", "elapsed_seconds",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=ROOT / "analysis" / "results" / "multistage_battery_file_map")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--max-files", type=int, default=0, help="Pilot limit; zero maps all archives.")
    parser.add_argument("--keep-archives", action="store_true")
    args = parser.parse_args()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    download_dir = output / "downloads"
    download_dir.mkdir(exist_ok=True)
    checkpoint = output / "archive_map_checkpoint.json"

    article_bytes = fetch_bytes(ARTICLE_API)
    (output / "figshare_article_api.json").write_bytes(article_bytes)
    article = json.loads(article_bytes)
    files = list(article["files"])
    if len(files) != EXPECTED_FILE_COUNT:
        raise AssertionError(f"Figshare file count changed: {len(files)}")
    metadata_record = next(file for file in files if file["name"] == "experiments_meta.csv")
    metadata_path = output / "experiments_meta.csv"
    download_file(metadata_record["download_url"], metadata_path, int(metadata_record["size"]))
    if sha256(metadata_path) != EXPECTED_METADATA_SHA256:
        raise AssertionError("experiments_meta.csv SHA256 changed")
    with metadata_path.open("r", encoding="utf-8-sig", newline="") as handle:
        metadata_rows = [
            {str(key).strip(): value for key, value in row.items()}
            for row in csv.DictReader(handle)
        ]
    rows_by_key = {
        (row["serial_internal"], row["serial"]): row
        for row in metadata_rows
    }
    if len(rows_by_key) != EXPECTED_ARCHIVE_COUNT:
        raise AssertionError("(serial_internal, serial) is not unique across 279 metadata rows")
    rows_by_serial: dict[str, list[dict]] = {}
    for row in metadata_rows:
        rows_by_serial.setdefault(row["serial"], []).append(row)

    existing = []
    if checkpoint.is_file():
        existing = json.loads(checkpoint.read_text(encoding="utf-8"))
        existing = resolve_complementary_stages(existing, rows_by_serial)
        existing, _ = resolve_with_validated_date_envelopes(existing, rows_by_serial)
    completed = {}
    for row in existing:
        if row.get("status") != "mapped-metadata-only":
            continue
        normalized = dict(row)
        normalized.setdefault("archive_internal_serial", normalized.get("serial_internal", ""))
        normalized.setdefault("archive_testpoint_raw", "")
        normalized.setdefault("archive_lab_raw", normalized.get("lab", ""))
        normalized.setdefault("measurement_start_date", "")
        normalized.setdefault("mapping_method", "exact-archive-serial-plus-internal-serial")
        normalized.setdefault("metadata_conflict_flags", "")
        normalized.setdefault("error", "")
        completed[int(normalized["file_id"])] = normalized
    archives = sorted((file for file in files if file["name"] != "experiments_meta.csv"), key=lambda item: int(item["id"]))
    pending = [file for file in archives if int(file["id"]) not in completed]
    if args.max_files:
        pending = pending[: args.max_files]
    print(json.dumps({"archives": len(archives), "already_mapped": len(completed), "pending_this_run": len(pending), "workers": args.workers}, indent=2), flush=True)

    results = dict(completed)
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        futures = {
            executor.submit(inspect_archive, record, rows_by_key, rows_by_serial, download_dir, args.keep_archives): record
            for record in pending
        }
        for index, future in enumerate(as_completed(futures), start=1):
            row = future.result()
            results[int(row["file_id"])] = row
            ordered = [results[key] for key in sorted(results)]
            write_checkpoint(checkpoint, ordered)
            print(f"[{index}/{len(pending)}] file_id={row['file_id']} status={row['status']}", flush=True)

    ordered = resolve_complementary_stages(
        [results[key] for key in sorted(results)],
        rows_by_serial,
    )
    ordered, date_envelopes = resolve_with_validated_date_envelopes(
        ordered,
        rows_by_serial,
    )
    write_checkpoint(checkpoint, ordered)
    write_csv(output / "archive_file_stage_map.csv", ordered)
    mapped = [row for row in ordered if row["status"] == "mapped-metadata-only"]
    errors = [row for row in ordered if row["status"] != "mapped-metadata-only"]
    full_run = args.max_files == 0
    stage_counts = Counter(row["stage"] for row in mapped)
    unique_internal_serials = len({row["serial_internal"] for row in mapped})
    unique_mapping_keys = len({(row["serial_internal"], row["serial"]) for row in mapped})
    conflict_counts = Counter(
        flag
        for row in mapped
        for flag in str(row.get("metadata_conflict_flags", "")).split(";")
        if flag
    )
    mapping_method_counts = Counter(row.get("mapping_method", "") for row in mapped)
    validation_errors = []
    if errors:
        validation_errors.append(f"{len(errors)} archives failed metadata-only mapping")
    if full_run:
        if len(mapped) != EXPECTED_ARCHIVE_COUNT:
            validation_errors.append(f"mapped {len(mapped)} of {EXPECTED_ARCHIVE_COUNT} archives")
        if unique_mapping_keys != EXPECTED_ARCHIVE_COUNT:
            validation_errors.append(f"mapped {unique_mapping_keys} unique (internal serial, serial) pairs")
        if dict(stage_counts) != EXPECTED_STAGE_COUNTS:
            validation_errors.append(f"stage counts changed: {dict(stage_counts)}")
    summary = {
        "status": "verified-complete-metadata-only-map" if full_run and not validation_errors else ("pilot-complete" if not validation_errors else "invalid"),
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "article_id": ARTICLE_ID,
        "article_api_sha256": sha256(output / "figshare_article_api.json"),
        "experiments_meta_sha256": sha256(metadata_path),
        "archives_expected": EXPECTED_ARCHIVE_COUNT,
        "archives_mapped": len(mapped),
        "unique_internal_serials": unique_internal_serials,
        "unique_internal_serial_serial_pairs": unique_mapping_keys,
        "stage_counts": dict(stage_counts),
        "mapping_method_counts": dict(mapping_method_counts),
        "metadata_conflict_counts": dict(conflict_counts),
        "validated_lab_date_envelopes": date_envelopes,
        "numeric_csv_entries_opened": False,
        "mapper_sha256": sha256(Path(__file__).resolve()),
        "preoutcome_freeze_sha256": sha256(ROOT / "analysis" / "target_metadata" / "multistage_battery_preoutcome_freeze.json"),
        "map_csv_sha256": sha256(output / "archive_file_stage_map.csv"),
        "validation_errors": validation_errors,
    }
    (output / "COMPLETE.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)
    if validation_errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
