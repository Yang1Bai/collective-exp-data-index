# Recipient-only baseline stress test

Status: **post-outcome sensitivity analysis**.

The formal cross-database interaction benchmark had already been inspected
before this stress test was specified. This analysis therefore cannot upgrade
the work to independent confirmation. Its sole purpose is adversarial: test
whether the observed donor-ranking advantage is an artefact of comparing
against a single weak recipient-only ridge model.

## Frozen sensitivity family

At each of the existing outcome-blind maximin anchor selections (3, 5 and 10
labelled formulations at 25 °C), fit the following recipient-only models using
the identical compact chemistry-plus-state representation:

- ridge regression with alpha 0.1, 1, 10 or 100;
- radial-basis kernel ridge with alpha 0.1, 1 or 10 and gamma fixed from the
  median non-zero distance in the complete unlabelled recipient pool;
- distance-weighted k-nearest neighbours with k = 1, 3 or 5, truncated to the
  available anchor count;
- Random Forest with 300 trees;
- Extra Trees with 300 trees;
- an equal percentile-rank ensemble of all declared recipient-only models.

No held-out outcome may choose a hyperparameter for deployment. For an
additional deliberately conservative check, construct an **oracle envelope**
that takes the best held-out Spearman, precision and regret achieved by any
declared recipient-only model separately in each draw. This oracle is not a
usable method; it is a stress-test ceiling.

## Decision rule

The source portfolio retains a credible data-poor ranking advantage only if,
at the five-anchor budget:

1. its mean Spearman exceeds that of every individual recipient-only model;
2. the 2.5th percentile of its draw-wise Spearman difference from the
   best-average recipient model is above zero; and
3. its mean Spearman is not lower than the non-deployable oracle envelope by
   more than 0.05.

Precision and normalized regret are reported as supporting metrics, not used
to replace a failed Spearman condition.

