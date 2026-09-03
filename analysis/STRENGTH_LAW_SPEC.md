# Cross-dataset strength-law transport diagnostic

Status: post-external-confirmation diagnostic; not preregistered and not used
to select the UTS-to-yield-strength borrowing edge.

## Question

Does a strong direct relation calibrated between ultimate tensile strength
(UTS) and yield strength (YS) in Borg transport unchanged to the independent
BIRDSHOT campaign?

## Frozen analysis

1. Pair UTS and YS only when they occur in the same source row; do not join
   measurements merely because they share a nominal composition.
2. Fit `log10(YS) = intercept + slope * log10(UTS)` separately in Borg and
   BIRDSHOT.
3. Fit the Borg relation without BIRDSHOT observations and evaluate it on every
   BIRDSHOT row.  Exact canonical composition overlap must be zero.
4. Treat canonical composition as the resampling cluster.  Use 5,000
   independent two-dataset cluster bootstraps for coefficient differences,
   predicted YS separation at the pooled median log-UTS, UTS/YS ratio
   differences, and Borg-to-BIRDSHOT external R-squared.
5. A failure of coefficient transport rejects this particular universal linear
   calibration; it does not prove that no conditional or nonlinear mechanical
   relation exists.
