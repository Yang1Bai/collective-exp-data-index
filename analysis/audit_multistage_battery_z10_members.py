"""Audit ZIP member names for the three Stage 2 z10 archives.

This audit deliberately reads only the ZIP central directory.  It never opens
or parses a CSV member and therefore cannot manufacture a substitute endpoint.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTICLE = ROOT / "analysis" / "results" / "multistage_battery_file_map" / "figshare_article_api.json"
MAP = ROOT / "analysis" / "results" / "multistage_battery_file_map" / "archive_file_stage_map.csv"
OUTPUT = ROOT / "analysis" / "results" / "multistage_battery_stage2" / "Z10_MEMBER_AUDIT.json"
FILE_IDS = {"47631232", "47632315", "47632330"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def classify_member(name: str) -> dict[str, bool]:
    leaf = Path(name).name
    return {
        "is_csv": leaf.lower().endswith(".csv"),
        "is_meta": leaf.lower().endswith("_meta.txt"),
        "is_et_t23": leaf.lower().endswith("_et_t23.csv"),
        "is_at_t23": leaf.lower().endswith("_at_t23.csv"),
    }


def main() -> None:
    article = json.loads(ARTICLE.read_text(encoding="utf-8"))
    files = {str(item["id"]): item for item in article["files"] if str(item["id"]) in FILE_IDS}
    if set(files) != FILE_IDS:
        raise AssertionError("The frozen article metadata does not contain all three z10 files")

    records: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="battery-z10-members-") as temporary:
        temporary_path = Path(temporary)
        for file_id in sorted(FILE_IDS):
            metadata = files[file_id]
            archive = temporary_path / metadata["name"]
            request = urllib.request.Request(metadata["download_url"], headers={"User-Agent": "collective-exp-data-audit/1.0"})
            with urllib.request.urlopen(request, timeout=180) as response, archive.open("wb") as handle:
                shutil.copyfileobj(response, handle)
            observed_sha = sha256(archive)
            with zipfile.ZipFile(archive) as zipped:
                members = [item.filename for item in zipped.infolist() if not item.is_dir()]
            classified = [dict(name=name, **classify_member(name)) for name in members]
            records.append({
                "file_id": file_id,
                "archive_name": metadata["name"],
                "archive_bytes": archive.stat().st_size,
                "archive_sha256": observed_sha,
                "member_count": len(classified),
                "csv_member_count": sum(item["is_csv"] for item in classified),
                "metadata_member_count": sum(item["is_meta"] for item in classified),
                "et_t23_csv_count": sum(item["is_et_t23"] for item in classified),
                "at_t23_csv_count": sum(item["is_at_t23"] for item in classified),
                "members": classified,
            })

    audit = {
        "status": "verified-structural-endpoint-absence",
        "scope": "ZIP central-directory member names only; no member contents opened",
        "file_ids": sorted(FILE_IDS),
        "archives": records,
        "all_have_exactly_one_et_t23": all(item["et_t23_csv_count"] == 1 for item in records),
        "all_lack_at_t23": all(item["at_t23_csv_count"] == 0 for item in records),
        "numeric_csv_rows_opened": False,
        "substitution_attempted": False,
        "claim_guard": "This audit proves structural absence of the frozen AT_T23 endpoint. It does not authorize another temperature, time point, endpoint, or condition group as a replacement.",
    }
    if not audit["all_lack_at_t23"]:
        audit["status"] = "unexpected-at-t23-member-found"
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in audit.items() if key != "archives"}, indent=2))


if __name__ == "__main__":
    main()
