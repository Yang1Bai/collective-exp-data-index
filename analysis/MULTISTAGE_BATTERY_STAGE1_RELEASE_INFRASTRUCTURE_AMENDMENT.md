# Stage 1 release infrastructure amendment

The first authorized Stage 1-only pass reached all 141 allowlisted archives
while Stage 2 remained sealed. It exposed two implementation facts:

1. A timed-out shell invocation continued in the background and briefly
   competed with the retained invocation for five `.zip.part` files.
2. Three Stage 1 archives contain no `*_AT_T23.csv` member. Under the already
   frozen no-substitution rule these cells are endpoint-missing; they are not
   computational download failures.

The original runner also allowed a Windows/OneDrive file-lock error during
post-extraction ZIP deletion to terminate the whole run even after the verified
endpoint checkpoint had been written.

Before any Stage 2 numeric row was opened, the runner was amended only to:

- reuse both successful and endpoint-missing checkpoints;
- classify a frozen extractor validity failure as `missing-endpoint`, retaining
  its exact reason rather than substituting a file, temperature, or endpoint;
- treat failure to delete an already processed raw ZIP as cleanup-only; and
- declare the Stage 1 release complete when all 141 allowlisted archives are
  accounted for as either evaluable or endpoint-missing and no download/hash/
  infrastructure errors remain.

No endpoint formula, step code, temperature, source/target assignment, learner,
split, applicability rule, threshold, comparison, or inferential decision was
changed. The five file-contention records must be rerun under the amended
runner. The three endpoint-missing cells remain missing without imputation.
Stage 2 remains fully sealed.
