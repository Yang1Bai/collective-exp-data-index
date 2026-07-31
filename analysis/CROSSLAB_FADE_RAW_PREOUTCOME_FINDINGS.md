# Raw cross-laboratory fade transfer — pre-outcome stopping result

**Decision:** stop before formal outcome access. The sealed HUST 80%-SOH outcome
release has not been opened by the analysis stage.

## What passed

- All four raw MATR batches were restored: 180 cells, 178 valid donor cells.
- Correctly restricting \(\Delta Q(V)\) to the discharge branch fixed a
  source-processing error.
- The original early-response-to-degradation-coefficient mapping passed its
  donor-only batch-out gate: Spearman 0.6128.
- A normalized response random forest selected without HUST outcomes achieved
  donor batch-out Spearman 0.6497, RMSE 0.12721 log-life, and \(R^2=0.4427\).
- The raw HUST boundary builder found 77/77 cells with complete cycles-1-to-100
  features. No post-cycle-100 value, total cycle count, or life statistic was
  reported to method development.

## Why the edge stopped

The first response representation rejected 77/77 HUST cells as outside MATR
support (donor 90th-percentile Mahalanobis threshold 3.256; closest HUST
distance 13.154). Per-cell capacity normalization reduced the closest distance
to 4.434, but the donor threshold was 3.122 and the gate still rejected 77/77.

An outcome-free featurewise audit then applied a fixed common-support rule:
retain a feature only if at least 80% of HUST early values lie inside the MATR
1st–99th percentile interval. It retained:

1. capacity slope divided by the cell's own reference capacity;
2. cycle-100 capacity divided by the reference capacity;
3. coulombic-efficiency standard deviation.

Those overlapping channels carried no transferable donor signal. Across
leave-one-MATR-batch-out tests, every model failed; the best absolute-life
candidate had Spearman −0.353 and \(R^2=-0.252\). The informative
\(\Delta Q(V)\) channels were precisely the channels with inadequate
cross-laboratory support.

## Scientific interpretation

This is a clean pre-outcome falsification of the MATR→HUST edge, not a failed
formal prediction. Early-response knowledge exists within MATR, but the
response components that predict life do not occupy the HUST operating
envelope. The contract therefore abstains before borrowing. Opening the HUST
life labels would add no valid evidence and is prohibited for this edge.

The next recipient must be chosen on the basis of **candidate-time response
support**, not chemistry name alone. A same-chemistry label such as “LFP” is
insufficient when cycling protocol and degradation trajectory shift the
informative response coordinates.
