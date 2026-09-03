# Post-release sensitivity merge amendment

The first execution of the 22-group post-release sensitivity stopped before
writing predictions or summaries because `wrong_property_mass_prediction` was
present in both frozen input tables. Pandas therefore renamed the two copies
with suffixes and the analysis could not find the unsuffixed control column.

The two frozen columns were compared across all 138 file IDs and were exactly
identical (maximum absolute difference 0). The implementation now drops the
duplicate copy from the control table before the one-to-one merge and retains
the copy in the source-feature table.

This is an infrastructure-only repair. It changes no endpoint, row, condition
group, split, feature value, source model, target learner, threshold, policy,
comparison, resampling procedure, decision rule, or claim boundary. The
analysis runner is re-hashed in the post-release sensitivity specification
before re-execution.
