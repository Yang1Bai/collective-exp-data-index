# Starrydata verifier amendment after Balam Job 70828

## Scope

Balam Job 70828 completed the formal Starrydata prediction and matched-
specificity computations, then failed inside the independent exploration
verifier before the TRI OER programme began. The failure was a dataframe-schema
error, not a failed scientific gate: both the outcome-joined target table and
the frozen source-prediction table contained `component_id`, but the verifier
merged them only on `entity_id`. Pandas therefore renamed the two columns to
`component_id_x` and `component_id_y`; the verifier then requested the absent
unsuffixed `component_id` column and raised `KeyError`.

## Permitted correction

The verifier now:

1. checks one-to-one entity coverage and exact agreement between the target and
   frozen `component_id` assignments;
2. merges only the three frozen rank columns needed for the conditional
   source-rank permutation; and
3. preserves the target table's original `component_id` column.

No target outcome, source rank, component assignment, policy order, model,
learner, representation, hypothesis card, endpoint, multiplicity family, seed,
or success threshold is changed. The correction cannot change the reported
formal metrics; it only allows the prespecified independent verifier to execute.

## Audit rule

The amendment and corrected verifier must be packaged together. The verified
result records this amendment's SHA-256 hash. Job 70828 remains archived as a
failed infrastructure/verification attempt and is not counted as a completed
scientific run.
