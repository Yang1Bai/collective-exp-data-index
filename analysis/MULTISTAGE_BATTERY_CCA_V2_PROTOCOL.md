# Frozen temporal CCA-v2 test on multi-stage battery aging

## What this experiment can settle

This is the first target-specific execution of the frozen CCA-v2 architecture.
Stage 1 is the information-rich temporal neighbor; Stage 2 is a later,
model-informed set of battery-aging conditions whose numeric outcomes have not
been inspected under this protocol.  All 23 Stage 2 condition groups are
distinct from Stage 1 in the deposited metadata.  A positive result would show
that locally qualified neighboring-condition knowledge can improve prediction
on later OOD experimental regimes.  It would not, by itself, prove a universal
cross-domain rule or prospective laboratory discovery.

The TRI/MIT/Stanford fast-charging dataset is frozen as a secondary external
battery-aging neighbor.  It enters only if its source audit passes before Stage
2 outcomes are opened.  Failure to map it is an abstention, not permission to
choose a friendlier source.  Therefore the temporal primary test and the
cross-program claim upgrade remain visibly separate.

## Why the target is genuinely outcome-unseen

The freeze used the Scientific Data methods and data-record description, the
Figshare article API, file names and sizes, and `experiments_meta.csv`.  No
capacity-retention, resistance-growth, cycle-life, or high-performing-condition
CSV members were opened or parsed. Two archives were downloaded only to inspect
ZIP member names and `*_meta.txt`; this schema-only pilot is recorded in the
freeze. The metadata contain 141 Stage 1 cells and
138 Stage 2 cells.  Stage 2 has eight calendar-aging and fifteen cycle-aging
condition groups, with zero exact Stage 1 condition overlap.

The repository exposes 138 duplicated archive names. Filename order cannot
distinguish stages. The mapping method is now resolved, but numeric parsing is
forbidden until a complete one-to-one
`file_id -> stage -> (serial_internal, serial)` table is supported by archive-
internal metadata and hashed. `serial_internal` alone is not unique because 18
Intilion identifiers are reused across stages. Guessing from API order is a
protocol violation. Ambiguous files are excluded; insufficient coverage makes
the target non-evaluable rather than replaceable.

The first complete metadata-only pass exposed additional deposited conflicts:
44 testpoint strings were format variants, three testpoint strings conflicted,
and 49 archive-internal serials disagreed with `experiments_meta.csv`. The
frozen hierarchy therefore uses the exact `(archive serial, internal serial)`
key first. A conflicting file can be assigned only when the same archive name
has exactly one Stage 1 and one Stage 2 metadata candidate and its twin has
already been mapped by the exact key; the conflicting file then receives the
remaining stage and a permanent conflict flag. File order, numeric values, and
performance are never used to resolve stage. Dates are excluded from these two
layers and are permitted only by the final calibrated envelope below.

Three duplicate-name pairs remained because both twins had conflicting internal
serials. For these six files only, a final same-laboratory temporal envelope is
allowed. It is calibrated exclusively from files already mapped without dates,
requires at least 20 files per stage and non-overlapping closed intervals, and
requires the unresolved date to fall inside exactly one interval. The frozen
INT calibration has 42 Stage 1 files in 2021-09-30--2021-10-12 and 45 Stage 2
files in 2023-01-19--2023-02-17. The six residual files fall inside exactly one
of these intervals. This is a metadata integrity resolution, not an outcome or
performance-derived split.

## Primary scientific and statistical test

The primary endpoint is terminal relative paper-defined RPT capacity retention
at the common reference temperature of 23 degrees Celsius:

`Q_RPT = (Q_charge_step21 + Q_discharge_step22) / 2`

`Q_rel_end_percent = 100 * Q_RPT_AT_T23 / Q_RPT_ET_T23`

The official descriptor defines RPT capacity as the mean of charge and
discharge capacity. `step_type=21` is the capacity charge and `step_type=22` is
the capacity discharge. Current is integrated against `run_time` only between
adjacent records within the same selected step. This replaces the version-4
shorthand that incorrectly described the endpoint as discharge-only; the
correction was frozen before any numeric Stage 1 or Stage 2 CSV data row was
opened. Charge-only, discharge-only, charge-discharge disagreement, and the 10-
and 45-degree results are prespecified diagnostics and cannot rescue the
primary endpoint. No endpoint substitution or imputation is allowed. At least
80% of cells and two cells per retained condition group must be evaluable in
both aging strata.

Each Stage 2 condition group is held out once.  Target labels are limited to
four other calendar groups and six other cycle groups, selected by a frozen
outcome-free maximin rule.  Cells, cycles, files, trees, and resampling seeds are
not independent units; inference is over the 8 calendar and 15 cycle condition
groups.

The target-only and adjacency-only comparators use the same ExtraTrees learner.
Adjacency-only adds the unqualified Stage 1 prediction.  CCA-v2 adds a centered
Stage 1 prediction only where a frozen local-applicability function supports
borrowing.  That function combines distance to Stage 1 support, distance to
labeled Stage 2 support, Stage 1 ensemble uncertainty, and provenance
compatibility.  The source feature is zero below applicability 0.20.  A nested
training-only gate returns the exact target-only prediction unless the
cross-validated gain exceeds 2% and is positive in both aging modes.

There are exactly two primary efficacy comparisons: CCA-v2 versus adjacency-
only and CCA-v2 versus target-only.  They use 10,000 stratified condition-
cluster bootstraps, 9,999 paired condition sign flips, and Holm correction.
Success requires both mean effects above the 2% practical dead zone, both 95%
lower bounds above zero, both Holm-adjusted p-values at most 0.05, positive
held-out R2 in both strata, at least 20% borrowing coverage, no clearly harmful
stratum, and all mapping and leakage gates.

## Controls and falsification

The full run retains target-only, adjacency-only, global credibility, strongest
single source, a row-and-geometry-matched Stage 1 wrong-property model, a
within-type shuffled source, equal-capacity random features, novelty, random,
and a descriptive oracle.  A favorable source feature that cannot beat these
controls is non-specific and cannot support neighboring-knowledge borrowing.

After Stage 1 source fitting but before Stage 2 outcome release, at least one
calendar and one cycle condition-region hypothesis card must be timestamped and
hashed.  Each card records the source evidence, expected direction, physical
rationale, matched target-only region, and a falsifier.  Passing prediction does
not automatically make these cards discoveries; the matched target evidence is
reported separately.

## Immutable claim boundary

- Temporal primary passes, external TRI abstains: evidence for local temporal
  borrowing, not cross-program transfer.
- Temporal primary and external TRI pass: evidence that the same applicability
  strategy can cross one independent neighboring battery program.
- Primary fails or abstains: retain the target as a boundary and do not replace
  it.
- Fixed screening helps but prediction does not: claim OOD prioritization only.
- No result here permits the phrases “general transfer law,” “prospective
  discovery,” or “laboratory experiments saved.”

Machine-readable definitions are in
`analysis/multistage_battery_cca_v2_design.json`; the outcome-free data audit is
in `analysis/target_metadata/multistage_battery_preoutcome_metadata.json`.

## Mapping gate completion

The metadata-only mapping gate completed on 2026-07-20: all 279 archive file IDs
map uniquely to 141 Stage 1 and 138 Stage 2 cells, and the independent verifier
reconstructed the same counts and hashes. The final map uses 230 exact composite
keys, 43 complementary-twin assignments, and six validated INT date-envelope
assignments. That mapping operation opened no CSV member. A subsequent protected
header audit read exactly the first physical line of 32 CSV members across
three archives and full nonnumeric metadata companions; it opened no numeric
data row. All headers matched the published six-column schema, and each archive
contained unique ET_T23 and AT_T23 files with 23-degree metadata. The endpoint
extractor and formal version-5 amendment are now frozen. The next gate is Stage
1-only source release and source/hypothesis-card freezing; Stage 2 outcomes
remain sealed.
