# Frozen replication protocol: CALiSol ranking in the FINALES campaign

## Purpose

This is the single highest-priority claim-upgrade experiment for the
manuscript. It tests whether the ordinal conductivity signal independently
reproduced in SolventSeg survives in a second experimental programme without
changing the donor model, transferred object, target-label budget, or success
logic.

The protocol was written before downloading either FINALES server archive or
opening any row-level FINALES conductivity result. The aggregate findings in
the associated article were known: the campaign identified a region of high
ionic conductivity. No candidate-level ordering, conductivity table, or model
contrast from this project was inspected when the protocol was frozen.

## Why this target is eligible

FINALES is an independent autonomous experimental programme for LiPF6 in
ethylene carbonate and ethyl methyl carbonate. It provides the four input
variables used by the fixed CALiSol donor—three mixture fractions and
temperature—and preserves timestamps, method identity, result status, and
quality metadata. Experimental measurements can therefore be separated from
molecular-dynamics estimates and evaluated in chronological order. The
Materials Cloud deposit is open under CC BY 4.0 and is linked to the
peer-reviewed article.

The target is scientifically useful because it distinguishes three
explanations of the SolventSeg result:

1. a genuinely portable ordinal conductivity surface;
2. a result specific to SolventSeg's structured 4-by-9 formulation grid;
3. a temperature or smoothness artifact that disappears in an adaptive,
   time-ordered experimental campaign.

## Fixed donor and transferred object

The donor is the exact 410-row CALiSol LiPF6/EC/EMC artifact used in the
independent SolventSeg reproduction. A
`HistGradientBoostingRegressor(random_state=2025)` is fitted once to EC, EMC,
LiPF6, and temperature. Its raw prediction is used only to rank eligible
FINALES candidates. It is never residual-fitted or recalibrated with FINALES
outcomes.

The transferred object is therefore an **ordinal candidate score**, not an
absolute conductivity prediction. Absolute RMSE cannot validate this
experiment.

## Outcome-unseen recipient construction

Only valid experimental ASAB conductivity results are eligible. Simulations,
failed or pending records, calibration-only records, cycle-life results, and
records failing the published quality status are excluded. Repeated
measurements of one formulation remain one candidate unit and cannot cross
the anchor/evaluation boundary.

The primary recipient is the November 2023 multi-task phase. Records are
ordered chronologically. The first three distinct eligible experimental
formulations are the only target-labelled anchors. Every later formulation is
held out. The hard-OOD scope is the 40% of later formulations farthest from
the anchors in outcome-free standardized composition space.

The September 2023 single-task phase is a secondary replication. It is not
pooled with the primary phase and cannot rescue a failed primary test.

## Primary estimand

Temperature changes conductivity and can inflate a pooled rank correlation.
The primary metric therefore compares only pairs of held-out formulations
measured within 1 °C. For each eligible pair, the predicted and measured order
must agree. Pairwise concordance is the fraction of agreeing non-tied pairs.
The primary effect is

\[
\Delta C =
C_{\mathrm{CALiSol\ rank}} -
\max_m C_{\mathrm{recipient\ baseline},m}.
\]

If fewer than 50 pairs are available, the temperature tolerance is widened
once to 2 °C. Fewer than 50 pairs after that makes the primary test ineligible.
The practical gate is \(\Delta C\ge 0.10\).

Secondary metrics are within-temperature-bin Spearman correlation,
top-quartile precision, normalized regret, the hard-OOD subset, and the
single-task phase. Pooled Spearman is reported only as a
temperature-confounded diagnostic. Top-1 success is not a claim-bearing
metric.

## Controls and inference

The fixed donor is compared with:

- Extra Trees, histogram gradient boosting, and a linear target-only model
  trained on the same three anchor formulations;
- 2,000 CALiSol donor-label permutations;
- a deterministic, size- and support-matched non-LiPF6 carbonate donor when
  CALiSol supplies enough eligible rows;
- temperature-only and salt-fraction-only rankings.

Uncertainty resamples unique formulations, not rows. The primary test uses
20,000 formulation-cluster bootstrap replicates. Donor specificity uses the
2,000 label permutations. The multi-task concordance contrast is the sole
confirmatory test; all other comparisons are secondary.

## Decision

A positive result requires every gate in
`analysis/finales_rank_replication_design.json`, including a 0.10 practical
concordance advantage, a bootstrap interval above zero, donor-label
permutation \(p\le 0.05\), improved top-quartile precision and regret, and
superiority to the support-matched wrong donor when that control is eligible.

A null or harmful result remains claim-bearing: it limits the SolventSeg
ranking edge to one recipient or identifies adaptive-campaign shift as a
boundary. No failed gate may be replaced after outcome access.

## Source records known at freeze

- Dataset DOI: `10.24435/materialscloud:qt-1s`
- Article DOI: `10.1002/aenm.202403263`
- Primary archive MD5: `68e6797a70b121baa18380215d55638a`
- Secondary archive MD5: `bc7eb8d7b741f8bba859ff3d280719cd`
- Fixed donor SHA256:
  `56b17f0e067daa00a9ea79eb5c7810c498e6e0f4ca2f699623b1c483b2ad177c`

The next action is to hash this design, download the two small server
archives, verify their MD5 values, and perform a schema-only extraction before
any model reads conductivity outcomes.
