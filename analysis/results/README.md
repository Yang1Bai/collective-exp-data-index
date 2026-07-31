# Analysis result policy

This directory versions compact scientific results: JSON summaries, decision
records, checksums, independent-verification reports, small contrast tables,
and figure source data. Large row-level predictions, repeated bootstrap draws,
model checkpoints, embeddings, and scheduler archives are excluded from Git
because they are deterministic intermediates and can exceed GitHub's file-size
limits.

The code, frozen designs, environment specifications, input hashes, and compact
verification outputs required to reconstruct those intermediates remain in the
repository. The public attempt index is
[`research/evidence/ATTEMPT_LEDGER.csv`](../../research/evidence/ATTEMPT_LEDGER.csv),
and the experiment-by-experiment command map is
[`analysis/README.md`](../README.md).
