# Analysed data resources

Start with the collaborator-facing
[`DATABASE_GUIDE.md`](DATABASE_GUIDE.md). It connects the complete broad
catalog to every task-specific resource that entered this project and explains
the difference between discovery, analysis, and paper evidence.

[`ANALYSED_RESOURCE_LEDGER.csv`](ANALYSED_RESOURCE_LEDGER.csv) records every
named external resource that materially entered an audit, donor model,
recipient model, control, readiness screen, or Edison-generated research path.
It is intentionally broader than the few databases showcased in the main
paper and narrower than the 127-resource discovery catalog.

The ledger distinguishes `catalogued`, `analysed`, `audit-only`, and
`AI-proposed` resources. Inclusion does not imply that an edge was successful.
The scientific disposition of each attempted edge is maintained separately in
[`research/evidence/ATTEMPT_LEDGER.csv`](../evidence/ATTEMPT_LEDGER.csv).

## Redistribution rule

Third-party raw files are not committed from the local `Dataset/`, `data/`, or
temporary download directories. Each upstream dataset keeps its own licence.
Where a licence is `Unknown` or `verify-upstream`, users must inspect the linked
record before downloading, redistributing, or building a derivative release.
The repository contains only original analysis code, hashes, compact derived
summaries, and small validation artefacts whose inclusion is necessary for the
scientific audit trail.

The broader resource index is available in [`catalog/catalog.csv`](../../catalog/catalog.csv).
