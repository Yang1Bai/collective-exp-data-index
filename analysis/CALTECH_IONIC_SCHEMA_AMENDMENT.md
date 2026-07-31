# Caltech ionic-conductor schema-only amendment

Frozen at `2026-07-16T22:49:34Z`, after downloading the target file and
verifying its prespecified MD5, but before running any target summary,
quality statistic, model, split, ranking, or policy comparison.

The original frozen design is
`analysis/caltech_ionic_external_policy_design.json` with SHA-256
`a3178927ccd050d8d4b94f8af9a9f5539bb926c321e46d601ee5d4d8594f4d7c`.
The downloaded file has MD5 `d1fcf7c9a7694c8f466932721b76b168`, matching
the prespecified checksum.

## Reason

The repository headers use dataset-specific concatenations that are
semantically unambiguous but do not exactly match the frozen alias strings.
This amendment changes only header resolution. It does not alter any row,
outcome transform, quality threshold, split, feature, policy, endpoint,
comparison, multiplicity correction, or decision gate.

The following exact one-to-one mappings are frozen:

| Target role | Exact CSV header |
|---|---|
| composition | `compound` |
| room-temperature ionic conductivity | `conductivity_siemens_per_cm` |
| source article DOI | `conductivity_doi` |
| ICSD grouping identifier | `icsd_collectioncode` |
| lowest extrapolation temperature | `lowest_extrapolation_temperature_K` |

All five columns are required and must resolve exactly once. The temperature
column is explicitly in kelvin, so the prespecified near-room-temperature
sensitivity is available.

## Disclosure

The command used to inspect the header accidentally printed the first two data
rows as well as the header. It exposed two conductivity values. Neither value
was summarized or used to choose this amendment, and no analytical rule was
changed after they were seen. This is a minor protocol deviation and must be
reported with the external benchmark; the target remains outcome-unseen in the
sense relevant to model, endpoint, threshold, and strategy selection, but it is
not literally true that no row-level value was displayed after download.
