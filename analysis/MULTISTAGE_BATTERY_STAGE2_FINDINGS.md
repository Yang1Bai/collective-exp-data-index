# Multi-stage battery Stage 2 findings

## What the frozen test decided

The protected release accounted for all 138 Stage 2 cells. The paper-defined
23 °C mean charge/discharge RPT-capacity endpoint was extracted for 135 cells.
All three cells in cycle-aging condition `z|35|0.8|0.5|0.9|1.1` had an initial
`ET_T23` file but no terminal `AT_T23` file. A central-directory audit of the
three deposited ZIP archives independently confirmed this structural absence
without opening any CSV member.

The prespecified gate required at least two evaluable cells in every one of the
23 condition groups. Its minimum was zero, so the frozen confirmatory temporal
CCA-v2 test is **non-evaluable**. The 97.8% cell-level coverage cannot override
the missing independent condition group, and no other temperature or endpoint
was substituted.

## Disclosed 22-group sensitivity

After the coverage failure, a missingness-driven sensitivity retained the 135
cells in 22 complete condition groups (8 calendar and 14 cycle groups). Every
maximin target-training budget was regenerated over the observable groups. The
endpoint, precomputed Stage 1 source features, target predictors, ExtraTrees
learner, applicability formula and threshold, training-only gate, controls,
effect definitions, 10,000 condition-cluster bootstraps, 9,999 sign flips, and
Holm procedure were unchanged.

CCA-v2 did not pass the sensitivity pattern:

- versus target-only: 3.47% equal-stratum relative RMSE gain, 95% cluster
  interval −0.59% to 9.30%, Holm-adjusted p=0.3692;
- versus adjacency-only: −2.80%, 95% interval −8.79% to 5.06%, adjusted
  p=0.766;
- CCA-v2 had positive held-out R² in both strata, but its training-only gate
  activated in only 4/22 outer conditions, all in calendar aging; for all 14
  cycle conditions it reverted exactly to target-only.

Thus the complex hard gate did not improve the simpler source-feature policy.
This result is an independently reconstructed post-release sensitivity and
cannot rescue the non-evaluable frozen primary.

## Outcome-guided strategy diagnostic

Because adjacency-only was numerically stronger in the complete sensitivity,
it was selected after outcome inspection for an explicitly post hoc diagnostic.
The policy itself was not newly fitted to the result: it is the prespecified
target learner augmented by the precomputed continuous Stage 1 degradation
prediction. Condition group remains the independent unit.

Against target-only, continuous neighboring-source borrowing reduced
equal-stratum mean condition RMSE by **6.12%** (calendar 7.95%; cycle 4.30%),
with a 95% condition-cluster interval of **2.56% to 9.16%**, one-sided paired
sign-flip p=0.0036, and Holm-adjusted p=0.0108 over four disclosed diagnostic
comparisons. Absolute held-out R² was 0.334 for calendar aging and 0.462 for
cycle aging. It improved 7/8 calendar and 10/14 cycle condition groups.

The source signal was not reproduced by matched controls:

- versus the Stage 1 wrong-property source: +6.85% [3.50%, 10.04%], adjusted
  p=0.0036;
- versus the within-type shuffled source: +11.72% [1.72%, 24.02%], adjusted
  p=0.0356;
- versus six equal-capacity random features: +7.47% [3.42%, 10.75%], adjusted
  p=0.0140.

The global-credibility feature produced predictions identical to adjacency-only
to numerical precision because a positive scalar rescaling preserves split
order for this tree learner; it is therefore not an independent control here.

The highest source-distance quartile remains heterogeneous: adjacency borrowing
was −1.24% over target-only in the two calendar groups but +5.56% in the four
cycle groups. The result supports selective neighboring-condition borrowing,
not a monotonic rule that transfer must improve every OOD region.

## Source-inspired scientific hypotheses

Both hypotheses written from Stage 1 before Stage 2 outcome release had the
predicted direction. The high-temperature/high-SOC calendar lead retained
93.51% capacity versus 96.83% in its matched control. The high-temperature,
high-SOC, high-DOD cycle lead retained 88.93% versus 91.75% in its matched
control. These are condition-level validation signals, not mechanistic proof or
prospective discoveries.

## What this changes

This battery program supplies a useful strategy result even though it does not
supply a confirmatory win. Upstream source credibility plus a simple continuous
source prediction transferred better than a complex hard gate. The actionable
candidate for a new independent test is therefore:

> qualify the neighboring experimental source before transfer; inject its
> continuous prediction into the target learner; retain wrong-property,
> shuffled-source, random-feature and target-only controls; use local support
> as a diagnostic or smooth weight rather than a cross-stratum hard veto.

That candidate now requires a new target whose endpoint coverage and split plan
are verified before any outcome access. Until then, the battery evidence is a
strong, reproducible method-development result with a failed confirmatory
coverage gate—not a claim of prospective discovery or experiments saved.
