# CALiSol external-borrowing implementation record

This file separates the frozen scientific design from implementation and
quality-control changes made after the first attempted execution.

## Before target-outcome modeling

- The raw CALiSol-23 file was hash-pinned and audited for schema, article
  counts, temperature coverage, formulation repetition, missing values, and
  numerical zeros.
- No conductivity correlation, regression, transfer effect, or model outcome
  was used to select the target or source edge.
- The target was fixed at -40 degC because it was the coldest 10 degC grid
  slice represented by at least ten source articles, permitting five
  paper-disjoint outer folds. The nearest -30 degC task was fixed as primary;
  -20, 0, and 20 degC were fixed as increasing-distance controls.
- The complete feature set, article-disjoint and exact-chemistry exclusions,
  target budget, learner settings, bootstrap, permutation, learning-curve
  budgets, practical threshold, sample-saving threshold, and rescue decision
  rule were written to `calisol_external_borrowing_design.json` before the
  first target-outcome model run.
- This is an internal design lock, not an externally time-stamped
  preregistration.

## Implementation-only corrections

1. The first quick smoke test stopped before producing an effect because a
   filtered source table retained non-contiguous pandas indices. Resetting the
   row index after the prespecified numerical-zero filter fixed positional
   alignment. No row, hypothesis, feature, model, or gate changed.
2. A successful quick run was then repeated after parallelizing the five
   independent source/control fits. The serial and process-parallel quick
   outputs were numerically identical, including source predictions, target
   effects, folds, and gate values. This was a scheduling change only.
3. The local data-lake normalizer initially rejected solvent component names
   beginning with digits. Adding a `SOLV_` namespace prefix repaired mixture
   keys. One raw row with a negative digitized salt concentration is retained
   in the raw SQL table but excluded from normalized measurements. Neither row
   enters the frozen -40/-30/-20/0/20 degC analysis.
4. The DTU item DOI was version-qualified from repository metadata after the
   run. This corrects provenance text only; the file URL, hash, and contents
   are unchanged.

## Formal run and independent QA

- Formal settings: 100 target-label repetitions, 5,000 hierarchical
  bootstrap replicates resampling repetitions, articles, and formulations,
  999 source-feature mapping permutations stratified within source article,
  60 learning-curve repetitions (with the exact 100-repeat n=30 anchor), and
  40 repetitions for each sensitivity learner.
- The primary prediction table contains exactly 89,100 rows: 891 held-out
  paper-specific formulations x 100 repetitions. Every formulation is tested
  once per repetition.
- Baseline predictions are exactly identical across the four real sources and
  the shuffled placebo (maximum rowwise spread 0).
- Recomputed pooled R2, mean relative RMSE effect, fold effects, fixed-subset
  permutation p value, and the n=30 learning-curve anchor match the released
  summaries to floating-point precision.
- All held-out article and exact-chemistry overlap counters are zero.

## Frozen result retained without edge switching

The adjacent -30 to -40 degC edge reduces RMSE by 1.61%, with an
article-hierarchical 95% interval of -2.14% to +4.21%. Baseline and augmented
cross-article R2 are -0.049 and -0.014. Two of five article folds are harmful,
the estimated target-label fraction saved is 16.9%, and the temperature
controls are not monotonically ordered. A fixed first-subset mapping test is
small (p=0.004), but it cannot override the repeated-effect interval,
practical, absolute-utility, fold, sample-saving, and adjacency gates.

The decision is therefore `cross-article-borrowing-unresolved`; no alternative
CALiSol temperature edge was promoted after seeing the outcomes.
