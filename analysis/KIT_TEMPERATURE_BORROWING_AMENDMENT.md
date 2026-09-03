# KIT temperature-borrowing implementation log

The confirmatory-style design in `kit_temperature_borrowing_design.json` was
written before any target-outcome model was run. It is an internal design lock,
not an external preregistration.

## 2026-07-14: smoke test and computation-only optimization

The first `--quick` smoke test used the frozen target/source temperatures,
features, formulation-level split, learners, and decision gates, but only 3
target-sampling repeats, 100 bootstrap draws, 9 mapping permutations, 2
sensitivity repeats, and 2 learning-curve repeats. These deliberately reduced
settings are encoded in the script and all smoke-test files have a `quick_`
prefix. They are not manuscript evidence.

The smoke test completed without a data-integrity or leakage assertion. It
showed that repeatedly invoking tree-level parallelism was slower than fitting
single-threaded forests concurrently across independent fold/repeat jobs. Before
the full run, the implementation was changed to parallelize across those jobs
and to keep each individual forest single-threaded. Tree count (300), random
seeds, train/test membership, outcomes, features, source cross-fitting, target
learners, repeat counts, bootstrap count, permutation count, hypotheses, and all
decision thresholds are unchanged. A direct check found a maximum prediction
difference of `4.44e-16` between the two scheduling modes for a fixed seed; the
change is computational scheduling only.

No primary edge, control, feature, threshold, or interpretation was changed in
response to the smoke-test outcomes.

## 2026-07-14: common-random-number baseline correction

Review of the smoke-test edge table showed that the baseline random-forest
seed included the source-edge label. Consequently, each source edge was being
compared with a slightly different random realization of the composition-only
baseline. Before the full run, the edge label was removed from the target-model
seed and the identical baseline predictions were cached and reused across all
primary and control source edges. This is the appropriate common-random-number
comparison and prevents forest randomness from contaminating the temperature-
distance ordering. The augmented models use the same fold/repeat seed as their
paired baseline. The correction applies symmetrically to every source edge and
does not change any data, hypothesis, learner, feature, repeat count, or gate.

Process-level parallelism was selected after a scheduling benchmark (40 frozen
300-tree fits: 3.38 s with eight processes versus 15.14 s with eight threads).
This changes only execution order. The full evidence run uses eight processes.

## 2026-07-14: exact n=30 learning-curve anchor

The first full result passed all encoded gates. A subsequent independent
recalculation from the row-level prediction artifact reproduced the primary
effect and pooled R2 values exactly, confirmed 108 held-out formulations per
repeat, confirmed identical baselines across source edges, and recomputed the
999-permutation p-value as 0.001. The audit also found that the learning curve's
nominal n=30 anchor used the same 30 formulations but a separate random-forest
seed and only the first 60 repeats. This does not affect the primary effect,
confidence interval, R2, fold directions, feature importance, source quality,
permutation test, placebo, or distance ordering. It can, however, slightly
change the interpolated target-label equivalence.

Before reporting sample savings, the n=30 curve point was changed to reuse the
exact cached composition-only predictions from all 100 primary repeats. Other
curve budgets retain the frozen 60 repeats. The curve artifact now records the
repeat count used at every budget. The complete analysis is rerun after this
correction; the corrected sample-equivalence result supersedes the first full
run. No hypothesis, outcome, feature, model, split, or decision threshold was
changed.

## Post-outcome sample-equivalence uncertainty diagnostic

The frozen label-saving gate was defined on the learning-curve point estimate.
To expose the stability of that interpolation, a separate diagnostic rebuilt
formulation-level target-only errors at every curve budget and used 5,000
conditional bootstrap replicates over formulations and training-subset
repetitions. The point estimate remains n=47.884 and 37.35% saved, but the
diagnostic interval is n=38.38--59.89 and 21.84--49.91% saved; 80.52% of
replicates meet the frozen 30% point threshold. This post-outcome analysis does
not redefine the frozen decision. It requires the manuscript to describe the
sample-saving magnitude as uncertain.

An initial implementation of this diagnostic used the global design seed for
the non-n=30 learning-curve budgets instead of the frozen
`kit-learning-curve` seed namespace. Reconciliation against the formal curve
identified the mismatch before release. That diagnostic draft was discarded;
the final diagnostic reproduces the formal budget-wise means and standard
deviations exactly. The frozen KIT effect, interval, p-value, and decision were
unaffected.
