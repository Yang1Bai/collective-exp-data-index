# Stage 2 endpoint-coverage boundary and post-release sensitivity policy

## Frozen primary decision

The Stage 2 release accounted for all 138 allowlisted cells. The frozen 23 °C
capacity endpoint was extracted for 135 cells, while all three cells in
condition group `z|35|0.8|0.5|0.9|1.1` lacked an `AT_T23` member. Consequently,
the prespecified requirement of at least two evaluable cells in every one of
the 23 condition groups failed. The confirmatory temporal borrowing test is
therefore **non-evaluable**, irrespective of the 97.8% cell-level coverage.

No other temperature, diagnostic time point, endpoint, or condition is used to
replace the missing group. The original frozen split plan and analysis remain
unexecuted because some target-training budgets include the unavailable group.

## Permitted post-release sensitivity

The remaining 135 cells and 22 complete condition groups may be used only in a
post-release, missingness-driven sensitivity analysis. The sensitivity must:

1. retain the frozen endpoint, predictors, source features, learner, local
   applicability formula, threshold, training-only gate, controls, two named
   comparisons, resampling counts, and effect definitions;
2. exclude only the structurally non-evaluable condition group;
3. regenerate every deterministic maximin target-training budget over the 22
   observable groups before running any model on the released outcomes;
4. retain condition group as the independent evaluation unit and preserve
   separate calendar and cycle strata;
5. report estimates, cluster-bootstrap intervals, sign-flip p-values, Holm
   values, absolute utility, borrowing coverage, and all controls; and
6. label every result exploratory and incapable of rescuing or replacing the
   failed 23-group primary test.

Because the missingness pattern and Stage 2 values were known before this
sensitivity was specified, a favorable sensitivity result can support method
plausibility and define a future confirmatory design, but it cannot establish a
prospective or preregistered success.
