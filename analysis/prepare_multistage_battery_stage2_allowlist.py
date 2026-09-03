"""Create the outcome-free Stage 2 download allowlist from frozen metadata."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAP = ROOT / "analysis" / "results" / "multistage_battery_file_map" / "archive_file_stage_map.csv"
API = ROOT / "analysis" / "results" / "multistage_battery_file_map" / "figshare_article_api.json"
OUTPUT = ROOT / "analysis" / "results" / "multistage_battery_stage2_allowlist.csv"
AUDIT = ROOT / "analysis" / "results" / "multistage_battery_stage2_allowlist_audit.json"
FIELDS = [
    "file_id", "archive_name", "archive_bytes", "archive_sha256", "download_url",
    "supplied_md5", "serial_internal", "serial", "stage", "lab", "type", "tp",
    "cell", "sampling", "mapping_method", "metadata_conflict_flags",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_rows() -> list[dict[str, str]]:
    with MAP.open("r", encoding="utf-8-sig", newline="") as handle:
        mapped = list(csv.DictReader(handle))
    api = json.loads(API.read_text(encoding="utf-8"))
    files = {str(item["id"]): item for item in api["files"]}
    rows: list[dict[str, str]] = []
    for source in mapped:
        if source["stage"] != "2":
            continue
        item = files[source["file_id"]]
        if item["name"] != source["archive_name"] or int(item["size"]) != int(source["archive_bytes"]):
            raise AssertionError(f"Figshare manifest mismatch for file_id {source['file_id']}")
        rows.append({
            "file_id": source["file_id"], "archive_name": source["archive_name"],
            "archive_bytes": source["archive_bytes"], "archive_sha256": source["archive_sha256"],
            "download_url": item["download_url"], "supplied_md5": item.get("supplied_md5", ""),
            "serial_internal": source["serial_internal"], "serial": source["serial"],
            "stage": source["stage"], "lab": source["lab"], "type": source["type"],
            "tp": source["tp"], "cell": source["cell"], "sampling": source["sampling"],
            "mapping_method": source["mapping_method"],
            "metadata_conflict_flags": source["metadata_conflict_flags"],
        })
    rows.sort(key=lambda row: int(row["file_id"]))
    if len(rows) != 138 or {row["stage"] for row in rows} != {"2"} or len({row["file_id"] for row in rows}) != 138:
        raise AssertionError("Stage 2 allowlist must contain exactly 138 unique Stage 2 archives")
    return rows


def main() -> None:
    rows = build_rows()
    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    audit = {
        "status": "verified-stage2-only-allowlist",
        "rows": 138,
        "stage_counts": {"2": 138},
        "unique_file_ids": 138,
        "stage1_file_ids_present": False,
        "numeric_csv_data_rows_opened": False,
        "archive_map_sha256": sha256(MAP),
        "figshare_api_sha256": sha256(API),
        "allowlist_sha256": sha256(OUTPUT),
    }
    AUDIT.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
