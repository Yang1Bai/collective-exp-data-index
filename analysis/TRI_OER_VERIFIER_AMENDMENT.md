# TRI OER verifier amendment after Balam Job 70861

## Scope

Balam Job 70861 completed all 7,200 frozen TRI OER model tasks and wrote the
formal prediction, component-error, specificity, exploration, hypothesis-card,
summary, and completion artifacts. The original independent verifier then
stopped because some secondary Spearman correlations were undefined. The runner
had already emitted SciPy `ConstantInputWarning` messages for those cells: a
constant truth or prediction has no rank-correlation coefficient, so SciPy
correctly records `NaN` even when every prediction and the RMSE, MAE, and R2
metrics are finite.

The formal primary result was already visible before this amendment and is a
null/negative transfer result. This amendment may not reinterpret, replace, or
drop it.

## Permitted correction

The frozen runner and original verifier remain byte-for-byte unchanged. A new
wrapper verifier:

1. requires every RMSE, MAE, and R2 value to be finite;
2. rejects infinite Spearman values;
3. preserves undefined Spearman cells as missing, counts them by plate, method,
   learner, representation, and scope, and reports the count in the verified
   result;
4. invokes all other checks and all inferential calculations from the original
   frozen verifier unchanged; and
5. records this amendment's SHA-256 hash.

Inside the structural call to the original verifier only, missing Spearman
values are replaced in a temporary copy so that its blanket finite-value guard
does not abort. The saved metrics are not altered, and Spearman is not used in
the prespecified primary prediction, specificity, exploration, or multi-target
inference.

## Resume rule

Formal artifacts from Job 70861 may be reused only if the frozen completion
sentinels and every amended verification check pass. Job 70861 remains archived
as an incomplete verification attempt. No target, plate, repeat, learner,
representation, method, policy, or hypothesis card may be rerun selectively.

## Job 70885 infrastructure note

The first resume attempt, Job 70885, stopped before importing the amended
verifier because the wrapper lacked the repository-root path initialization
used by the other directly executed analysis scripts. The wrapper now adds its
parent repository directory to `sys.path` before importing the frozen verifier.
This is an entry-point correction only; no result file was read or rewritten by
Job 70885. A direct command-line launch regression test was added.
