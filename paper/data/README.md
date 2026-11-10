# Data access and article source data

The repository stores frozen designs, compact derived results, selected
harmonized validation tables and a tracked integrated snapshot. It does not
claim ownership of third-party raw data and does not re-host those data unless
the upstream terms permit the specific retained artifact.

- [`datasets.csv`](datasets.csv) maps all 15 third-party resources used in the
  submitted study to their upstream access page, DOI, licence, redistribution
  status and repository representation.
- [`article_source_data.csv`](article_source_data.csv) lists each headline
  number, its full-precision value and the exact JSON path from which it is
  read.
- The repository-wide authoritative resource and redistribution ledger is
  [`research/data/ANALYSED_RESOURCE_LEDGER.csv`](../../research/data/ANALYSED_RESOURCE_LEDGER.csv).
- Code is covered by the repository [`LICENSE`](../../LICENSE); catalog
  metadata authored here is covered by [`LICENSE-DATA.md`](../../LICENSE-DATA.md).
  Upstream data retain their own terms.

For reproducibility, cite both this repository release and the original data
publication or record shown in `datasets.csv`. An open download URL is not by
itself a redistribution licence.

The manifest's `repository_representation` column identifies the normalized,
harmonized or derived artifact used for audit. It does not imply that the raw
third-party source is redistributed here. Every row is explicitly marked
`not redistributed` in accordance with the submitted Data availability
statement.

The retired OCx24 direct dataset page currently returns 404, so the manifest
uses FAIR Chemistry's current official OCx24 publication entry. The retained
repository artifact remains a derived snapshot; the link must not be described
as a direct raw-data download.
