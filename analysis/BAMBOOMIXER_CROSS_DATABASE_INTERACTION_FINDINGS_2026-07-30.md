# Cross-database electrolyte interaction: verified findings

## Decision

The benchmark routes this edge to **candidate ranking**, not absolute
conductivity prediction.

This is the strongest current retrospective example in the project that
neighboring experimental databases can repair a data-poor recipient's OOD
candidate ordering. It is not independent confirmation: SolventSeg and
FINALES outcomes had already been inspected, and BambooMixer lacks row-level
DOI provenance.

## What was transferred

Three conductivity programmes were trained separately:

- 10,012 BambooMixer measurements after removing the complete
  LiPF6/ethylene-carbonate/ethyl-methyl-carbonate target family;
- 410 CALiSol measurements from three source articles; and
- 1,089 formulation-temperature aggregates from the controlled KIT programme.

Their log-conductivity predictions were averaged with equal weight per
programme. Records were not pooled, so the 10,012-row source could not dominate
the smaller programmes. A strict record audit found 71 near-identical records
between BambooMixer and CALiSol, but zero between any source and the 180-row,
36-formulation SolventSeg recipient. The overlapping target family was removed
from the BambooMixer portfolio arm before combination.

## Primary SolventSeg result

At the fixed 25 °C endpoint, the programme-balanced source score achieved:

- Spearman \(\rho=0.918\);
- top-quartile precision \(=1.000\); and
- normalized top-candidate regret \(=0.000\).

Across 100 outcome-blind maximin selections of five labelled recipient
formulations, the unchanged source score achieved mean
\(\rho=0.910\), precision \(=0.933\), and regret \(=0.00047\).

The strongest of 13 recipient-only configurations was radial-basis kernel
ridge regression, with mean \(\rho=0.537\), precision \(=0.490\), and regret
\(=0.0393\). The source advantage was:

- \(\Delta\rho=0.374\);
- 95% anchor-coverage interval, 0.213–0.562.

Even an undeployable oracle that selected the best recipient-only model
separately after seeing each held-out draw remained below the source score:

- source-minus-oracle \(\Delta\rho=0.300\);
- 95% interval, 0.183–0.540.

The zero-label source ordering was also non-random under 10,000 target-label
permutations (Holm-adjusted one-sided \(p=0.00070\) across seven declared
source-ranking arms).

## What the database interaction added

The equal-programme log-prediction portfolio had mean five-anchor
\(\rho=0.9103\), compared with 0.8867 for the broad single BambooMixer donor.
The draw-wise gain was 0.0236 (95% interval, 0.0069–0.0397), positive in all
100 anchor selections. Top-quartile precision increased from 0.8263 to 0.9325
(mean +0.1063; 95% interval, 0–0.125).

This is a modest but reproducible portfolio gain. It supports
programme-balanced interaction as a robustness improvement; it does not imply
large multi-source synergy.

## Why this is ranking-only

The programme-balanced score did not pass the absolute-prediction gate:

- all-temperature log-RMSE was 0.342, versus 0.290 for the state-only source;
- relative gain versus state-only was −18.0%;
- formulation-bootstrap 95% interval, −44.0% to 21.1%;
- relative gain versus chemistry-permuted source was −15.1%;
- 95% interval, −30.2% to 27.2%.

Five-anchor calibration reduced RMSE relative to the recipient-only ridge by
22.8% on average, but the 95% anchor-coverage interval crossed zero
(−1.5% to 74.6%). Numerical calibration therefore remains unqualified even
though candidate ordering is strong.

## External boundary

The source portfolio did not dominate the full November 2023 FINALES
evaluation pool. In the 16-candidate multitask phase, its Spearman correlation
was 0.168, compared with 0.759 for the target linear model. Some seven-candidate
hard-OOD or single-task subsets showed positive donor ordering, but they are
too small and outcome-inspected to rescue the complete edge.

The prior frozen FINALES analysis remains the formal second-recipient boundary.
The new portfolio analysis is consistent with its conclusion: a strong
SolventSeg rank edge is programme-specific and must not be promoted to an
electrolyte-wide rule.

## Manuscript claim

**Supported:** When formulation state and endpoint are matched, separately
trained neighboring experimental programmes can provide a preserved ordinal
score that substantially improves OOD candidate ranking in a recipient with
only five labels, even when they do not improve absolute calibration.
Programme-balanced combination adds a small, reproducible gain over the broad
single donor.

**Not supported:** independent confirmation, universal electrolyte transfer,
guaranteed top-1 discovery, prospective search acceleration, or a general
benefit from pooling neighboring databases.

## Reproducibility

- Frozen design:
  `analysis/bamboomixer_cross_database_interaction_design.json`
- Formal summary:
  `analysis/results/bamboomixer_cross_database_interaction_summary.json`
- Independent verification:
  `analysis/results/bamboomixer_cross_database_interaction_verification.json`
- Recipient-baseline stress test:
  `analysis/results/bamboomixer_recipient_baseline_stress_test_summary.json`
- Stress-test verification:
  `analysis/results/bamboomixer_recipient_baseline_stress_test_verification.json`

The cross-database verifier independently recalculated 180 target predictions,
72 metric cells, 45,000 formulation-bootstrap rows, 3,300 anchor metric rows,
1,500 anchor contrasts, seven 10,000-permutation rank tests, and all 40 FINALES
metric cells. The complete repository test suite passed (117 tests).

