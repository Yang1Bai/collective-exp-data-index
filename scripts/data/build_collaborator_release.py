#!/usr/bin/env python3
"""Build private collaborator data assets and file-level manifests.

The release intentionally excludes article PDFs, rendered figures, notebooks,
source code, and model outputs from the additional Dataset/ collection. It
includes all files under data/, because that directory is the project's local
analysis-ready data workspace, and tabular/archive inputs under Dataset/.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import shutil
import sys
import zipfile


ROOT = Path(__file__).resolve().parents[2]
TAG = "collaborator-data-v2026.08.04"
OUT = ROOT / "tmp" / TAG
COLLAB = ROOT / "collaboration_data"
CORE_ASSET = "collective-exp-analysis-ready-v2026.08.04.zip"
CANDIDATE_ASSET = "collective-exp-candidate-tables-v2026.08.04.zip"
CANDIDATE_EXTENSIONS = {".csv", ".xlsx", ".xls", ".zip", ".data", ".pck", ".json"}
EXCLUDED_PARTS = {".ipynb_checkpoints", "__pycache__"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_source_rules() -> list[dict[str, str]]:
    with (COLLAB / "SOURCE_LICENSE_MATRIX.csv").open(
        encoding="utf-8-sig", newline=""
    ) as handle:
        rules = list(csv.DictReader(handle))
    return sorted(rules, key=lambda row: len(row["source_prefix"]), reverse=True)


def source_rule(rel: str, rules: list[dict[str, str]]) -> dict[str, str]:
    normalized = rel.replace("\\", "/")
    for rule in rules:
        prefix = rule["source_prefix"].rstrip("/")
        if normalized == prefix or normalized.startswith(prefix + "/"):
            return rule
    if normalized.startswith("Dataset/"):
        return {
            "resource_name": "Additional collaborator-provided candidate table",
            "source_url": "user-provided local collection",
            "upstream_licence": "unknown",
            "collaboration_status": "collaborator-restricted",
            "notes": "Verify source and rights before public redistribution",
        }
    raise RuntimeError(f"No source/licence rule for {rel}")


def selected_files() -> tuple[list[Path], list[Path]]:
    core = sorted(path for path in (ROOT / "data").rglob("*") if path.is_file())
    candidates = []
    for path in sorted((ROOT / "Dataset").rglob("*")):
        if not path.is_file():
            continue
        if any(part in EXCLUDED_PARTS for part in path.parts):
            continue
        if path.suffix.lower() in CANDIDATE_EXTENSIONS:
            candidates.append(path)
    if not core:
        raise RuntimeError("No files found under data/")
    if not candidates:
        raise RuntimeError("No candidate tables found under Dataset/")
    return core, candidates


def manifest_rows(
    asset: str, files: list[Path], rules: list[dict[str, str]]
) -> list[dict[str, object]]:
    rows = []
    for path in files:
        rel = path.relative_to(ROOT).as_posix()
        rule = source_rule(rel, rules)
        rows.append(
            {
                "asset": asset,
                "path": rel,
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
                "resource_name": rule["resource_name"],
                "source_url": rule["source_url"],
                "upstream_licence": rule["upstream_licence"],
                "collaboration_status": rule["collaboration_status"],
            }
        )
    return rows


def write_manifest(rows: list[dict[str, object]]) -> None:
    fields = [
        "asset",
        "path",
        "bytes",
        "sha256",
        "resource_name",
        "source_url",
        "upstream_licence",
        "collaboration_status",
    ]
    with (COLLAB / "DATA_FILE_MANIFEST.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def build_zip(asset: str, files: list[Path]) -> Path:
    destination = OUT / asset
    with zipfile.ZipFile(
        destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6
    ) as archive:
        for path in files:
            archive.write(path, path.relative_to(ROOT).as_posix())
        for metadata in (
            COLLAB / "README.md",
            COLLAB / "SOURCE_LICENSE_MATRIX.csv",
            COLLAB / "DATA_FILE_MANIFEST.csv",
        ):
            archive.write(metadata, metadata.relative_to(ROOT).as_posix())
    return destination


def validate_zip(path: Path, expected: list[Path]) -> None:
    expected_names = {item.relative_to(ROOT).as_posix() for item in expected}
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        bad = archive.testzip()
    missing = expected_names - names
    if bad or missing:
        raise RuntimeError(
            f"Archive validation failed for {path.name}: bad={bad}, missing={len(missing)}"
        )


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    COLLAB.mkdir(parents=True, exist_ok=True)

    rules = load_source_rules()
    core, candidates = selected_files()
    rows = manifest_rows(CORE_ASSET, core, rules) + manifest_rows(
        CANDIDATE_ASSET, candidates, rules
    )
    write_manifest(rows)

    core_zip = build_zip(CORE_ASSET, core)
    candidate_zip = build_zip(CANDIDATE_ASSET, candidates)
    validate_zip(core_zip, core)
    validate_zip(candidate_zip, candidates)

    assets = [core_zip, candidate_zip]
    with (COLLAB / "RELEASE_ASSET_CHECKSUMS.sha256").open(
        "w", encoding="ascii", newline="\n"
    ) as handle:
        for path in assets:
            handle.write(f"{sha256(path)}  {path.name}\n")

    summary = {
        "tag": TAG,
        "status": "validated",
        "core_files": len(core),
        "candidate_files": len(candidates),
        "manifest_rows": len(rows),
        "assets": [
            {"name": path.name, "bytes": path.stat().st_size, "sha256": sha256(path)}
            for path in assets
        ],
        "excluded_from_candidate_asset": (
            "PDFs, images, notebooks, code, logs, and derived presentation figures"
        ),
        "visibility_guard": (
            "Private collaborators only until every verify-upstream or unknown source is cleared."
        ),
    }
    (COLLAB / "BUILD_SUMMARY.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
