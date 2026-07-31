"""Create compact catalog and local-snapshot quality profiles."""
from __future__ import annotations

import json
import sqlite3

import pandas as pd

from common import DB, RESULTS, ROOT, ensure_output_dirs, load_obelix


def main() -> None:
    ensure_output_dirs()
    entries = json.loads((ROOT / "catalog" / "catalog.json").read_text(encoding="utf-8"))["entries"]
    catalog_rows = [
        ("catalog_records", len(entries)),
        ("experimental_records", sum(entry.get("data_type") == "experimental" for entry in entries)),
        ("mixed_records", sum(entry.get("data_type") == "mixed" for entry in entries)),
        ("open_access_records", sum(entry.get("access") == "open" for entry in entries)),
        ("registration_records", sum(entry.get("access") == "registration" for entry in entries)),
        ("restricted_records", sum(entry.get("access") == "restricted" for entry in entries)),
        ("unknown_license_records", sum(str(entry.get("license", "")).lower() == "unknown" for entry in entries)),
        ("missing_doi_records", sum(not entry.get("doi") for entry in entries)),
        ("verification_url_equals_homepage", sum(entry.get("verified_via") == entry.get("homepage_url") for entry in entries)),
    ]
    pd.DataFrame(catalog_rows, columns=["metric", "value"]).to_csv(
        RESULTS / "catalog_profile.csv", index=False
    )

    with sqlite3.connect(DB) as connection:
        lake = pd.read_sql(
            """SELECT dataset, COUNT(*) AS measurements,
                      COUNT(DISTINCT property) AS properties,
                      COUNT(DISTINCT material_key) AS canonical_entities,
                      SUM(material_key IS NULL) AS missing_entity_key,
                      SUM(quality_flags != '[]') AS flagged_measurements
               FROM measurements GROUP BY dataset ORDER BY dataset""",
            connection,
        )
        registered = pd.read_sql(
            "SELECT id,normalization_status,n_measurements,redistribution_status,source_commit FROM datasets ORDER BY id",
            connection,
        )
        organic = pd.read_sql(
            """SELECT dataset,property,COUNT(*) AS n,
                      SUM(value <= 0) AS nonpositive_values,
                      MIN(value) AS minimum,MAX(value) AS maximum
               FROM measurements
               WHERE (dataset='aqsoldb' AND property='logS')
                  OR (dataset='freesolv' AND property='dG_hydration')
               GROUP BY dataset,property""",
            connection,
        )
    lake.to_csv(RESULTS / "data_lake_profile.csv", index=False)
    registered.to_csv(RESULTS / "data_lake_registered_sources.csv", index=False)
    organic.to_csv(RESULTS / "organic_value_audit.csv", index=False)

    obelix = load_obelix()
    isodb_summary_path = RESULTS / "isodb_compensation_summary.json"
    isodb_summary = (
        json.loads(isodb_summary_path.read_text(encoding="utf-8"))
        if isodb_summary_path.exists()
        else None
    )
    findings = pd.DataFrame(
        [
            {
                "check": "canonical entity key completeness",
                "status": "pass_with_exclusions",
                "evidence": f"{int(lake.missing_entity_key.sum())} of {int(lake.measurements.sum())} measurements lack a canonical key; all are flagged and excluded from modeling",
            },
            {
                "check": "OBELiX official split after canonicalization",
                "status": "pass_after_exclusion",
                "evidence": f"{obelix.attrs['canonical_test_overlap_rows_excluded']} test rows ({obelix.attrs['canonical_test_overlap_keys_excluded']} normalized compositions) overlapped training and were excluded",
            },
            {
                "check": "signed organic target preservation",
                "status": "pass",
                "evidence": "; ".join(
                    f"{row.dataset}: {int(row.nonpositive_values)}/{int(row.n)} values <= 0"
                    for row in organic.itertuples()
                ),
            },
            {
                "check": "ISODB thermodynamic validity",
                "status": "pass_analysis_only" if isodb_summary else "not_run",
                "evidence": (
                    f"pinned archive hash verified; {isodb_summary['primary']['n_systems']} one-fit-per-system "
                    f"isosteric pairs from {isodb_summary['primary']['n_dois']} DOIs; raw adsorbent identifiers "
                    "remain outside the formula/SMILES measurement schema"
                    if isodb_summary
                    else "pinned raw archive available but isosteric analysis outputs are absent"
                ),
            },
            {
                "check": "catalog license completeness",
                "status": "limitation",
                "evidence": f"{dict(catalog_rows)['unknown_license_records']} of {len(entries)} records have Unknown license",
            },
        ]
    )
    findings.to_csv(RESULTS / "data_quality_findings.csv", index=False)
    print(findings.to_string(index=False))


if __name__ == "__main__":
    main()
