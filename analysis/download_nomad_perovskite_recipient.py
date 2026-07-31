"""Download a versioned, analysis-ready Perovskite Database snapshot.

The NOMAD archive endpoint is rate limited to one request every five seconds.
This downloader therefore uses a single connection at a time, stores every
page before continuing, and can resume after interruption without repeating
completed pages.

Only the explicitly declared archive fields below are requested.  The raw
page payloads remain the authoritative snapshot; the CSV is a deterministic
flattened view for the borrowing audit and later modelling.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DATA_ROOT = (
    ROOT
    / "data"
    / "external"
    / "bandgap_borrowing"
    / "nomad_perovskite_v4"
)
PAGES_DIR = DATA_ROOT / "pages"
CSV_PATH = DATA_ROOT / "perovskite_solar_cell_recipient.csv"
MANIFEST_PATH = DATA_ROOT / "perovskite_solar_cell_recipient_manifest.json"

ENDPOINT = (
    "https://nomad-lab.eu/prod/v1/api/v1/entries/archive/query"
)
QUERY = {"entry_type": "PerovskiteSolarCell"}
PAGE_SIZE = 1_000
MIN_REQUEST_INTERVAL_SECONDS = 5.25


def leaves(*names: str) -> dict[str, str]:
    return {name: "*" for name in names}


# Every name below is from the public perovskite_solar_cell_database schema.
# Outcome fields are fetched because this is a retrospective development
# benchmark, not a claim of prospective preregistration.
REQUIRED: dict[str, Any] = {
    "metadata": leaves("entry_id", "upload_id", "mainfile"),
    "data": {
        "ref": leaves(
            "DOI_number",
            "publication_date",
            "journal",
        ),
        "perovskite": {
            **leaves(
                "composition_long_form",
                "composition_short_form",
                "composition_a_ions",
                "composition_a_ions_coefficients",
                "composition_b_ions",
                "composition_b_ions_coefficients",
                "composition_c_ions",
                "composition_c_ions_coefficients",
                "band_gap",
                "band_gap_estimation_basis",
            ),
            "ions": leaves(
                "name",
                "coefficients",
                "ion_type",
                "molecular_formula",
                "smile",
            ),
        },
        "cell": leaves(
            "architecture",
            "area_total",
            "area_measured",
            "stack_sequence",
            "flexible",
            "semitransparent",
        ),
        "perovskite_deposition": leaves(
            "number_of_deposition_steps",
            "procedure",
            "solvents",
            "thermal_annealing_temperature",
            "thermal_annealing_time",
        ),
        "jv": leaves(
            "default_PCE",
            "default_Voc",
            "default_Jsc",
            "default_FF",
            "default_PCE_scan_direction",
            "light_intensity",
            "light_spectra",
            "test_temperature",
        ),
    },
}

FLAT_FIELDS = [
    "entry_id",
    "upload_id",
    "mainfile",
    "doi",
    "publication_date",
    "journal",
    "composition_long_form",
    "composition_short_form",
    "composition_a_ions",
    "composition_a_ions_coefficients",
    "composition_b_ions",
    "composition_b_ions_coefficients",
    "composition_c_ions",
    "composition_c_ions_coefficients",
    "ions_json",
    "band_gap",
    "band_gap_estimation_basis",
    "cell_architecture",
    "cell_area_total",
    "cell_area_measured",
    "cell_stack_sequence",
    "cell_flexible",
    "cell_semitransparent",
    "deposition_steps",
    "deposition_procedure",
    "deposition_solvents",
    "annealing_temperature",
    "annealing_time",
    "pce",
    "voc",
    "jsc",
    "fill_factor",
    "pce_scan_direction",
    "light_intensity",
    "light_spectra",
    "test_temperature",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def atomic_gzip_json(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with gzip.open(temporary, "wb", compresslevel=6) as handle:
        handle.write(canonical_json(value))
    temporary.replace(path)


def read_gzip_json(path: Path) -> Any:
    with gzip.open(path, "rb") as handle:
        return json.loads(handle.read())


def request_page(
    page_after_value: str | None,
    *,
    attempts: int = 6,
) -> dict[str, Any]:
    pagination: dict[str, Any] = {
        "page_size": PAGE_SIZE,
        "order_by": "entry_id",
        "order": "asc",
    }
    if page_after_value:
        pagination["page_after_value"] = page_after_value
    payload = {
        "owner": "public",
        "query": QUERY,
        "pagination": pagination,
        "required": REQUIRED,
    }
    body = canonical_json(payload)
    request = urllib.request.Request(
        ENDPOINT,
        data=body,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "collective-exp-data-index/nomad-audit-1.0",
        },
        method="POST",
    )
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                result = json.load(response)
            if "data" not in result or "pagination" not in result:
                raise RuntimeError("NOMAD response omitted data or pagination")
            return result
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            retryable = error.code in {429, 500, 502, 503, 504}
            if not retryable or attempt + 1 == attempts:
                raise RuntimeError(
                    f"NOMAD request failed with HTTP {error.code}: "
                    f"{detail[:2000]}"
                ) from error
        except (TimeoutError, urllib.error.URLError) as error:
            if attempt + 1 == attempts:
                raise RuntimeError("NOMAD request repeatedly timed out") from error
        time.sleep(max(MIN_REQUEST_INTERVAL_SECONDS, 2**attempt))
    raise AssertionError("unreachable")


def page_paths() -> list[Path]:
    return sorted(PAGES_DIR.glob("page_*.json.gz"))


def validate_page_chain(paths: list[Path]) -> tuple[str | None, int, int | None]:
    next_page: str | None = None
    rows = 0
    total: int | None = None
    for index, path in enumerate(paths):
        expected = PAGES_DIR / f"page_{index:05d}.json.gz"
        if path != expected:
            raise RuntimeError(
                f"Page checkpoint is not contiguous: expected {expected.name}, "
                f"found {path.name}"
            )
        page = read_gzip_json(path)
        pagination = page["pagination"]
        page_total = int(pagination["total"])
        if total is None:
            total = page_total
        elif total != page_total:
            raise RuntimeError("NOMAD total changed within the saved snapshot")
        rows += len(page["data"])
        next_page = pagination.get("next_page_after_value")
    return next_page, rows, total


def value(section: dict[str, Any], name: str) -> Any:
    item = section.get(name)
    if isinstance(item, (dict, list)):
        return json.dumps(
            item,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    return item


def flatten(item: dict[str, Any]) -> dict[str, Any]:
    archive = item.get("archive") or {}
    metadata = archive.get("metadata") or {}
    data = archive.get("data") or {}
    ref = data.get("ref") or {}
    perovskite = data.get("perovskite") or {}
    cell = data.get("cell") or {}
    deposition = data.get("perovskite_deposition") or {}
    jv = data.get("jv") or {}
    return {
        "entry_id": metadata.get("entry_id") or item.get("entry_id"),
        "upload_id": metadata.get("upload_id") or item.get("upload_id"),
        "mainfile": metadata.get("mainfile"),
        "doi": value(ref, "DOI_number"),
        "publication_date": value(ref, "publication_date"),
        "journal": value(ref, "journal"),
        "composition_long_form": value(perovskite, "composition_long_form"),
        "composition_short_form": value(perovskite, "composition_short_form"),
        "composition_a_ions": value(perovskite, "composition_a_ions"),
        "composition_a_ions_coefficients": value(
            perovskite, "composition_a_ions_coefficients"
        ),
        "composition_b_ions": value(perovskite, "composition_b_ions"),
        "composition_b_ions_coefficients": value(
            perovskite, "composition_b_ions_coefficients"
        ),
        "composition_c_ions": value(perovskite, "composition_c_ions"),
        "composition_c_ions_coefficients": value(
            perovskite, "composition_c_ions_coefficients"
        ),
        "ions_json": value(perovskite, "ions"),
        "band_gap": value(perovskite, "band_gap"),
        "band_gap_estimation_basis": value(
            perovskite, "band_gap_estimation_basis"
        ),
        "cell_architecture": value(cell, "architecture"),
        "cell_area_total": value(cell, "area_total"),
        "cell_area_measured": value(cell, "area_measured"),
        "cell_stack_sequence": value(cell, "stack_sequence"),
        "cell_flexible": value(cell, "flexible"),
        "cell_semitransparent": value(cell, "semitransparent"),
        "deposition_steps": value(deposition, "number_of_deposition_steps"),
        "deposition_procedure": value(deposition, "procedure"),
        "deposition_solvents": value(deposition, "solvents"),
        "annealing_temperature": value(
            deposition, "thermal_annealing_temperature"
        ),
        "annealing_time": value(deposition, "thermal_annealing_time"),
        "pce": value(jv, "default_PCE"),
        "voc": value(jv, "default_Voc"),
        "jsc": value(jv, "default_Jsc"),
        "fill_factor": value(jv, "default_FF"),
        "pce_scan_direction": value(jv, "default_PCE_scan_direction"),
        "light_intensity": value(jv, "light_intensity"),
        "light_spectra": value(jv, "light_spectra"),
        "test_temperature": value(jv, "test_temperature"),
    }


def build_csv(paths: list[Path], expected_total: int) -> int:
    temporary = CSV_PATH.with_suffix(".csv.tmp")
    seen: set[str] = set()
    rows = 0
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FLAT_FIELDS)
        writer.writeheader()
        for path in paths:
            page = read_gzip_json(path)
            for item in page["data"]:
                row = flatten(item)
                entry_id = str(row["entry_id"] or "")
                if not entry_id:
                    raise RuntimeError("NOMAD row omitted entry_id")
                if entry_id in seen:
                    raise RuntimeError(f"Duplicate NOMAD entry_id: {entry_id}")
                seen.add(entry_id)
                writer.writerow(row)
                rows += 1
    if rows != expected_total:
        temporary.unlink(missing_ok=True)
        raise RuntimeError(
            f"Flattened {rows} rows but NOMAD reported {expected_total}"
        )
    temporary.replace(CSV_PATH)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Testing-only cap; omit for a complete snapshot.",
    )
    arguments = parser.parse_args()

    PAGES_DIR.mkdir(parents=True, exist_ok=True)
    paths = page_paths()
    next_page, saved_rows, total = validate_page_chain(paths)
    if paths and next_page is None and total is not None and saved_rows != total:
        raise RuntimeError("Saved final page does not match reported total")
    print(
        json.dumps(
            {
                "saved_pages": len(paths),
                "saved_rows": saved_rows,
                "reported_total": total,
                "next_page_after_value": next_page,
            },
            indent=2,
        )
    )

    pages_added = 0
    complete = bool(paths and next_page is None and saved_rows == total)
    while not complete:
        if arguments.max_pages is not None and pages_added >= arguments.max_pages:
            break
        started = time.monotonic()
        page = request_page(next_page)
        page_path = PAGES_DIR / f"page_{len(paths):05d}.json.gz"
        atomic_gzip_json(page_path, page)
        paths.append(page_path)
        pages_added += 1
        pagination = page["pagination"]
        page_total = int(pagination["total"])
        if total is None:
            total = page_total
        elif total != page_total:
            raise RuntimeError("NOMAD total changed while downloading")
        saved_rows += len(page["data"])
        next_page = pagination.get("next_page_after_value")
        complete = next_page is None
        print(
            f"[{len(paths):03d}] rows={saved_rows}/{total} "
            f"next={next_page or 'complete'}",
            flush=True,
        )
        remaining = MIN_REQUEST_INTERVAL_SECONDS - (
            time.monotonic() - started
        )
        if not complete and remaining > 0:
            time.sleep(remaining)

    if not complete:
        print("Testing cap reached; checkpoint is resumable.")
        return
    assert total is not None
    rows = build_csv(paths, total)
    page_hashes = {
        path.name: sha256(path)
        for path in paths
    }
    manifest = {
        "status": "complete",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "endpoint": ENDPOINT,
        "query": QUERY,
        "required": REQUIRED,
        "page_size": PAGE_SIZE,
        "request_interval_seconds": MIN_REQUEST_INTERVAL_SECONDS,
        "pages": len(paths),
        "rows": rows,
        "page_sha256": page_hashes,
        "csv": str(CSV_PATH.relative_to(ROOT)).replace("\\", "/"),
        "csv_sha256": sha256(CSV_PATH),
        "claim_guard": (
            "This is a live retrospective snapshot. It does not establish "
            "prospective validation, and target-side band gap may be used only "
            "as an oracle diagnostic unless a protocol explicitly says otherwise."
        ),
    }
    temporary = MANIFEST_PATH.with_suffix(".json.tmp")
    temporary.write_bytes(canonical_json(manifest) + b"\n")
    temporary.replace(MANIFEST_PATH)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
