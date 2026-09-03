# Literature-guided neighboring-knowledge transfer: method-development findings

## Decision

The next Balam experiment should test one frozen candidate only:

> **planned experimental state + chemical-system-cross-fitted UTS prediction +
> a tree-based YS model**

This candidate is worth a robustness run because it repaired the hardest
chemical-system OOD region consistently in the local screen.  The run remains
post-selection validation, because the MPEA outcomes used to select the method
have already been inspected.

## What the literature changed

The literature does not support indiscriminate pooling of databases.  The most
relevant successful methods share four design choices:

1. **Modular sharing rather than full pooling.** The 2026 cross-material
   catalyst model uses separate surface and bulk branches connected by a small,
   physically interpretable shared representation
   ([Moon et al., *Nature Materials*](https://doi.org/10.1038/s41563-026-02622-6)).
2. **Task-conditioned routing.** Mixture-of-experts transfer can outperform
   pairwise transfer, but negative pairwise edges remain common
   ([Chang et al., *npj Computational Materials*](https://doi.org/10.1038/s41524-022-00929-x)).
3. **Transferability must be estimated before expensive transfer.** Regression
   transferability estimators and cross-modal source selection are useful for
   screening sources, not proof that the selected edge will improve OOD
   prediction
   ([Nguyen et al., UAI 2023](https://proceedings.mlr.press/v216/nguyen23a.html);
   [CroMEL, *npj Computational Materials*](https://doi.org/10.1038/s41524-025-01723-1)).
4. **OOD must be constructed explicitly.** Random splits overstate
   generalization, and no model dominates every materials OOD construction
   ([Li et al., *npj Computational Materials*](https://doi.org/10.1038/s41524-024-01316-4)).

The practical implication is that a donor database should be treated as a
conditional expert.  It should be activated only after matching measurement
state, endpoint mechanism and support, and its signal must be cross-fitted under
the same novelty contract encountered at deployment.

## What failed before the successful candidate

Three increasingly sophisticated ideas failed under strict leakage control:

- Cross-fitted residual stacking removed the earlier apparent polymer gain.
  The previous large signal was mainly a mismatch between donor features seen
  during target training and those available on genuinely new identities.
- A task-conditioned partial-label neural model was unstable at 15--30 target
  labels.  Large multitask literature results do not transfer automatically to
  this small-data regime.
- Same-endpoint Caltech-to-OBELiX transfer improved the in-distribution region
  but harmed Q4.  A hard support gate prevented most of the damage, but did not
  create OOD rescue.

These failures show that source selection, model complexity and endpoint
similarity are not sufficient if the representation omits the experimental
state.

## Data-contract correction

The unified MPEA task retained formula and outcome but discarded processing,
phase, test mode, temperature, microstructure and density.  The raw experimental
table contains:

- 1,067 positive YS rows across 150 elemental systems;
- 539 positive UTS rows across 93 systems;
- 495 rows with paired YS and UTS;
- processing metadata for 1,036 YS rows;
- test temperature for all 1,067 YS rows;
- microstructure for 1,016 YS rows.

The corrected experiment therefore predicts YS at the row-level experimental
state.  The primary deployment contract uses composition, processing route,
phase family, test mode, test temperature and calculated density.  An elemental
system is the indivisible split unit.

## Local screen

The fixed split contained 639 development rows and 428 evaluation rows in 59
held elemental systems.  Every donor prediction on a target-training fold was
made by a UTS model excluding that fold's systems and all evaluation systems.
The UTS donor achieved group-OOD OOF R² = 0.667 under the planned-state
contract.

| Target labels | Contrast in Q4 | Relative RMSE gain | Positive runs | Augmented Q4 R² |
|---:|---|---:|---:|---:|
| 30 | composition → planned-state target | +10.50% | 8/9 | −0.134 |
| 30 | planned-state → + predicted UTS | +2.55% [−1.73, +6.84] | 6/9 | −0.083 |
| 60 | composition → planned-state target | +15.59% [+7.13, +24.05] | 8/9 | −0.326 |
| 60 | planned-state → + predicted UTS | **+12.24% [+7.78, +16.70]** | **9/9** | **+0.008** |
| 60 | planned-state → shuffled UTS control | +1.57% [−11.84, +14.99] | 4/9 | −0.116 |
| 60 | planned-state → measured UTS ceiling | +44.75% | 9/9 | +0.438 |

The bracketed intervals are descriptive t intervals across the declared
model-by-draw runs; those runs are correlated and are not the final inferential
unit.  Elemental-system bootstrap inference is frozen for the Balam run.

The selected predicted-UTS method recovers roughly one quarter of the measured
UTS ceiling.  This is scientifically more informative than claiming that a
generic transfer algorithm succeeded: nearby endpoint knowledge is valuable,
but only part of it is recoverable from the present state representation.

For the two tree learners alone, the selected method improved Q4 RMSE by about
13.3% and produced mean Q4 R² of about 0.24.  The residual-anchor alternative
had a larger point estimate but changed sign in three of nine runs, so it was
rejected in favor of the stable concatenation candidate.

## What this establishes—and what it does not

The result supports a sharpened mechanism:

> Neighbor knowledge becomes useful when the recipient state is explicit, the
> donor endpoint is physically adjacent, and donor features are generated under
> the same held-system contract as deployment.

It does not yet establish general cross-domain transfer.  MPEA UTS and YS are
neighboring endpoints in one experimental program.  Its role in the paper is a
mechanistic demonstration of how the borrowing map can be made actionable,
alongside the independent database-level edges and the negative-transfer map.

## Balam robustness result

The frozen Balam run completed and independently verified 60 model-by-draw
runs, 25,680 row predictions, 59 held elemental systems, and 100,000 two-way
cluster-bootstrap replicates. The primary result was:

- pooled Q4 relative RMSE gain: **+9.21% [4.43,14.37%]**;
- positive model-by-draw runs: **55/60**;
- pooled augmented Q4 R²: **0.103**;
- architecture-matched shuffled-donor Q4 gain:
  **−0.26% [−1.81,1.01%]**;
- real-minus-architecture-matched-shuffled Q4 gain:
  **+9.47 percentage points [4.80,14.34]**;
- measured-UTS Q4 ceiling: **+47.70%**, augmented R²=0.679.

The Q1 gain was +7.21% [3.05,11.52%]. The Q4-minus-Q1 contrast was +2.00
percentage points [−4.66,8.62%], so the method is not claimed to be
OOD-exclusive. The Q4 R² interval also crossed zero [−0.151,0.291]. Both frozen
gates passed, with the correct classification **stable on this experimental
programme**. The result supports state-matched neighboring-endpoint borrowing
as an actionable method while retaining its post-selection, non-prospective
claim boundary.

The V1 shuffled comparison used a residual-anchor control and is not used for
source-specific inference. The frozen V2 correction retained the primary
architecture, data, split, draws, learners and inference, and changed only the
shuffled donor to the identical concatenation architecture. V2 independently
verified all hashes and passed both frozen gates.
