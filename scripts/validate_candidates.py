"""Validate the quarantined discovery-candidate queue."""

from __future__ import annotations

import json
import re
from pathlib import Path

try:
    from . import common
except ImportError:  # direct script execution
    import common


ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "catalog" / "candidates" / "candidates.json"
SCHEMA = ROOT / "catalog" / "candidate_schema.json"
ID_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
ENUMS = {
    "discovery_source": {
        "api-discovery-tdm",
        "api-discovery",
        "community-nomination",
        "manual-search",
    },
    "candidate_status": {"unreviewed", "triaged", "accepted", "rejected"},
    "record_kind": {
        "database",
        "dataset",
        "source-data-package",
        "metadata-record",
        "unknown",
    },
    "outcome_access_status": {
        "metadata-only",
        "schema-only",
        "outcome-opened",
        "unknown",
    },
}
REQUIRED = {
    "candidate_id",
    "name",
    "homepage_url",
    "discovery_source",
    "candidate_status",
    "record_kind",
    "outcome_access_status",
    "review_flags",
    "discovered_at",
}


def validate_payload(payload: dict, catalog_entries: list[dict]) -> list[str]:
    errors: list[str] = []
    if payload.get("schema_version") != 1:
        errors.append("schema_version must equal 1")
    if not payload.get("snapshot_utc"):
        errors.append("snapshot_utc is required")
    entries = payload.get("entries")
    if not isinstance(entries, list):
        return errors + ["entries must be a list"]

    catalog_ids = {entry["id"] for entry in catalog_entries}
    catalog_dois = {
        str(entry.get("doi") or "").lower(): entry["id"]
        for entry in catalog_entries
        if entry.get("doi")
    }
    seen_ids: set[str] = set()
    seen_dois: dict[str, str] = {}
    for index, entry in enumerate(entries):
        tag = entry.get("candidate_id", f"#{index}")
        missing = sorted(field for field in REQUIRED if field not in entry)
        if missing:
            errors.append(f"[{tag}] missing fields {missing}")
        candidate_id = str(entry.get("candidate_id") or "")
        if candidate_id and not ID_RE.fullmatch(candidate_id):
            errors.append(f"[{tag}] candidate_id is not kebab-case")
        if candidate_id in seen_ids:
            errors.append(f"[{tag}] duplicate candidate_id")
        seen_ids.add(candidate_id)
        for field, allowed in ENUMS.items():
            value = entry.get(field)
            if value is not None and value not in allowed:
                errors.append(f"[{tag}] {field}={value!r} not in {sorted(allowed)}")
        url = str(entry.get("homepage_url") or "")
        if url and not url.startswith(("http://", "https://")):
            errors.append(f"[{tag}] homepage_url is not an HTTP(S) URL")
        doi = str(entry.get("concept_doi") or entry.get("doi") or "").lower()
        if doi:
            if doi in seen_dois:
                errors.append(f"[{tag}] duplicate candidate DOI with {seen_dois[doi]!r}")
            seen_dois[doi] = candidate_id
        if entry.get("candidate_status") == "accepted":
            canonical_id = entry.get("canonical_record_id")
            if canonical_id not in catalog_ids:
                errors.append(
                    f"[{tag}] accepted candidate lacks a valid canonical_record_id"
                )
            if doi and doi not in catalog_dois:
                errors.append(
                    f"[{tag}] accepted candidate DOI is absent from the main catalog"
                )
    return errors


def schema_errors(payload: dict) -> list[str]:
    try:
        import jsonschema  # type: ignore
    except Exception:
        return []
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    return [f"schema: {error.message}" for error in jsonschema.Draft7Validator(schema).iter_errors(payload)]


def main() -> int:
    payload = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    catalog_entries = common.entries_of(common.load_catalog())
    errors = validate_payload(payload, catalog_entries) + schema_errors(payload)
    print(
        f"Validated {len(payload.get('entries', []))} quarantined candidates "
        f"against {len(catalog_entries)} curated records."
    )
    if errors:
        for error in errors:
            print("  -", error)
        return 1
    print("OK - candidate queue is isolated and valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
