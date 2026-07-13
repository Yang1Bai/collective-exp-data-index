"""Build catalog/catalog.json from the curated seed files.

The seed files under scripts/seed/ preserve the originally researched
records (with their `verified_via` provenance URLs). This script merges
them, normalizes fields, dedupes by id, and writes the catalog.

Run once to (re)generate the seed catalog:
    python scripts/build_seed.py
"""
from __future__ import annotations

import glob
import json
import os
from datetime import date

import common


def main() -> int:
    seed_files = sorted(glob.glob(os.path.join(common.SEED_DIR, "*_seed.json")))
    if not seed_files:
        print("No seed files found in", common.SEED_DIR)
        return 1

    raw: list[dict] = []
    for path in seed_files:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        print(f"  loaded {len(data):>3} entries from {os.path.basename(path)}")
        raw.extend(data)

    entries = [common.normalize_entry(e) for e in raw]

    # POLICY: this is an EXPERIMENTAL data index. Purely computational
    # databases (data_type == "computational") are excluded from the catalog
    # and archived to catalog/excluded_computational.json for transparency.
    # "mixed" entries stay - they contain measured data.
    comp = [e for e in entries if e["data_type"] == "computational"]
    entries = [e for e in entries if e["data_type"] != "computational"]
    if comp:
        excl_path = os.path.join(common.CATALOG_DIR, "excluded_computational.json")
        with open(excl_path, "w", encoding="utf-8") as fh:
            json.dump(comp, fh, ensure_ascii=False, indent=2)
        print(f"  [policy] excluded {len(comp)} computational-only entries "
              f"-> catalog/excluded_computational.json")

    entries, warnings = common.dedupe(entries)
    entries.sort(key=lambda e: (e["domain"], e["subdomain"], e["name"].lower()))

    for w in warnings:
        print("  [dedupe]", w)

    catalog = {
        "catalog_version": "0.1.0",
        "updated": date.today().isoformat(),
        "entry_count": len(entries),
        "note": "Metadata index only. This catalog links to datasets; it does not re-host source files. Purely computational databases are excluded by policy.",
        "entries": entries,
    }
    common.save_catalog(catalog)
    print(f"\nWrote {len(entries)} entries -> {os.path.relpath(common.CATALOG_JSON, common.ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
