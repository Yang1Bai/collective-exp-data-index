"""Validate catalog/catalog.json.

Checks:
  - every entry conforms to catalog/schema.json (uses `jsonschema` if
    installed, otherwise a stdlib-only structural check)
  - ids are unique and kebab-case
  - no duplicate DOIs
  - required fields present and non-empty

Exit code is non-zero if any error is found (CI-friendly).
    python scripts/validate_catalog.py
"""
from __future__ import annotations

import json
import re

import common

ID_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
ENUMS = {
    "domain": {"materials", "chemistry"},
    "data_type": {"experimental", "computational", "mixed"},
    "access": {"open", "registration", "restricted"},
}
REQUIRED = ["id", "name", "description", "domain", "subdomain",
            "data_type", "access", "homepage_url"]


def lite_check(entries: list) -> list[str]:
    errors: list[str] = []
    seen_ids: set[str] = set()
    seen_doi: dict[str, str] = {}
    for i, e in enumerate(entries):
        tag = e.get("id", f"#{i}")
        for f in REQUIRED:
            if not e.get(f):
                errors.append(f"[{tag}] missing required field '{f}'")
        eid = e.get("id", "")
        if eid and not ID_RE.match(eid):
            errors.append(f"[{tag}] id is not kebab-case")
        if eid in seen_ids:
            errors.append(f"[{tag}] duplicate id")
        seen_ids.add(eid)
        for f, allowed in ENUMS.items():
            v = e.get(f)
            if v is not None and v not in allowed:
                errors.append(f"[{tag}] {f}='{v}' not in {sorted(allowed)}")
        url = e.get("homepage_url", "")
        if url and not url.startswith("http"):
            errors.append(f"[{tag}] homepage_url is not a URL: {url}")
        d = (e.get("doi") or "").lower()
        if d and d in seen_doi:
            errors.append(f"[{tag}] duplicate DOI shared with '{seen_doi[d]}'")
        elif d:
            seen_doi[d] = eid
    return errors


def schema_check(entries: list) -> list[str]:
    try:
        import jsonschema  # type: ignore
    except Exception:
        return []  # handled by lite_check
    with open(common.SCHEMA_JSON, "r", encoding="utf-8") as fh:
        schema = json.load(fh)
    validator = jsonschema.Draft7Validator(schema)
    errors: list[str] = []
    for e in entries:
        for err in validator.iter_errors(e):
            errors.append(f"[{e.get('id', '?')}] schema: {err.message}")
    return errors


def main() -> int:
    catalog = common.load_catalog()
    entries = common.entries_of(catalog)
    errors = lite_check(entries) + schema_check(entries)

    print(f"Validated {len(entries)} entries.")
    if errors:
        print(f"\n{len(errors)} problem(s) found:")
        for e in errors:
            print("  -", e)
        return 1
    print("OK - no problems found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
