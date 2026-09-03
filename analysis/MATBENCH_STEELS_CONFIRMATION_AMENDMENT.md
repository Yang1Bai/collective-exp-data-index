# Matbench steels confirmation implementation amendment

Date: 2026-07-14

The design file `matbench_steels_confirmation_design.json` was frozen before
the first target-outcome modeling run. The first execution produced no result
artifacts because the direct 999-permutation implementation exceeded the
runtime limit. A vectorized block-matrix implementation was then added. Its
pre-result numerical self-check showed that the repository's generic
`Ridge(alpha=10, solver="lsqr")` target learner was an approximate solution:
on the first fixed Matbench train/test sample its MSE was 0.0389760, whereas
the exact Ridge solution was 0.0388643.

Before any Matbench target conclusion was produced, this analysis was amended
to use `Ridge(alpha=10, solver="cholesky")` consistently for the primary edge,
the baseline learning curve, and the feature-mapping permutation test. The
vectorized test is checked against that exact scikit-learn pipeline before it
continues. No dataset, official fold, sampled target budget, source model,
feature representation, hypothesis, success threshold, bootstrap count,
permutation count, or decision rule was changed. This is a numerical-solver
implementation amendment, not an outcome-driven analytical amendment.

After the first completed result, QA identified two summary-only bugs. First,
the model-robustness counter initialized the primary learner as positive even
when its observed effect was negative. Second, the target-equivalence curve
used a different random n=30 sample sequence from the primary comparison; in
this high-variance small-sample setting that could report apparent sample
savings even when the paired augmented model was worse. The counter now uses
the observed primary sign, and the learning curve is anchored to the exact
primary n=30 samples. These corrections do not change any prediction,
bootstrap interval, fold effect, or permutation statistic. The first completed
run already failed the rescue decision; both corrections make that failure
more, not less, explicit.
