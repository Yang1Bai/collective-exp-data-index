# E6 implementation amendment

The E6 scientific design and its SHA-256 were fixed before the first E6
prediction run. A quick smoke execution then exposed one audit-label error.

The source filtering correctly removed the held-out article and every exact
held-out chemistry before fitting. However, the leakage table stored the
number of rows removed by this filter under names that could be read as
post-filter residual leakage. The gate consequently treated successful
exclusions as retained leakage.

The implementation now records separate pre-exclusion and post-exclusion
counts. Only post-exclusion counts enter the leakage gate. No row selection,
feature, anchor, model, prediction, estimand, inference procedure, threshold
or scientific interpretation changed. The quick smoke predictions and effect
estimates are unaffected. Formal results must be generated after this
implementation-only correction.

The first formal verification also found an output-serialization ambiguity:
each `unit_key` already contains a vertical bar, while multiple anchor keys
were initially joined by the same character. Anchor keys are now serialized
as a JSON array. This changes only machine readability of the released
prediction table. The formal computation is rerun so that every released file
and checksum corresponds to the unambiguous representation.
