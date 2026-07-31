# OPV optical borrowing: portable ZIP-member amendment

## Trigger

The first formal Balam job (`71577`) failed before the metadata audit and
before any row-level OPV outcome was opened.  Python on Linux reported that
`data/opv_devices_strict_molecular_benchmark.csv` was absent from the target
ZIP, although the same frozen archive and member passed the Windows audit.

## Root cause

The public OPV-DB ZIP was produced with platform-dependent directory
separators.  Python on Windows normalizes the stored member name, whereas
Python on Linux can expose the backslash-containing name literally.  Exact
lookup with a forward-slash path was therefore platform dependent.  The
archive SHA256 remained
`3a8199aa3e9e78e20bbb486240972aa361d8ea69fa69d27ce42de45c3ada0095`.

## Permitted implementation change

The audit and formal outcome loader now compare ZIP member names only after
replacing backslashes with forward slashes, then open the exact stored member
returned by the archive.  The remote submission preflight checks both the
frozen archive SHA256 and the normalized member name before requesting a
compute node.

No dataset, row, split, label draw, donor scope, feature, learner, contrast,
inference rule, success gate or claim boundary changed.  No row-level PCE,
open-circuit voltage, short-circuit current density or fill factor was read
while diagnosing or implementing this amendment.

## Lifecycle consequence

Job `71577` is an infrastructure-only failure and is excluded from scientific
inference.  The replacement formal job remains the first outcome-opening run
of the frozen design.

The first replacement submission attempt also stopped on the login node,
before `sbatch`, because the remote tar configuration refused to replace
checkpoint files left by the previous package.  Remote extraction now uses
GNU tar's explicit `--overwrite` option inside the fixed project root.  This
only replaces files named in the newly uploaded, hash-reported package; it
does not delete unrelated or generated results.  This second infrastructure
change likewise occurred before any row-level target outcome was opened and
does not alter the formal analysis.

Replacement job `71578` passed archive and environment preflight, then stopped
after the outcome-free metadata audit because the frozen metadata byte hash
had been produced with Windows CRLF line endings while Linux emitted LF line
endings.  The table had 21,721 line endings and no lone carriage returns; the
platform-dependent bytes, rather than scientific content, caused the drift.
The audit now explicitly writes LF via pandas' `lineterminator` argument.
The design is re-anchored to that platform-independent serialization, and
label draws are regenerated from the still outcome-free table.  No target
outcome was read, and no analytical choice or success threshold changed.

Before another submission, a three-stage outcome-free preflight was added.
It verifies the actual tar members against the workspace, all frozen code and
data hashes, normalized ZIP membership, metadata semantics, DOI-group split
integrity, label-draw identity, source/target overlap sentinels and the eight
frozen solid-source checkpoints.  It runs locally and again on the Balam
login node; after the metadata audit it is repeated on the compute node, and
after strict source training it verifies exact target-molecule coverage,
finite features and every new checkpoint before the formal outcome loader is
allowed to run.  The full-node CPU request was also changed from 64 to 128 to
match Balam's four-GPU node allocation, while the frozen recipient analysis
continues to use 64 parallel workers.  These are verification and resource
declaration changes only.
