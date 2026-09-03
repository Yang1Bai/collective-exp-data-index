# FINALES rank-replication implementation amendment

The frozen scientific design and all numerical repetition counts remain
unchanged.

The first formal invocation stopped before any result file was written because
the evaluation table was copied before target-baseline prediction columns were
added. The implementation was corrected to construct the evaluation view after
each prediction column is added.

The next invocation did not finish within the local ten-minute execution
window. It was stopped before result serialization. The bottleneck was 2,000
serial fits of the label-permuted donor model. Pairwise concordance was
vectorized and the 2,000 independent permutations were parallelized. The donor
model class and parameters, permutation seeds, 2,000-permutation count,
20,000-bootstrap count, estimands, comparators, and decision gates are
unchanged.
