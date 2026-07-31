# Synthetic-smoke implementation amendment

A fully synthetic smoke test, performed before any formal fatigue model was
fit, found that the curve-level target table renamed `composition_key` to
`material_key` before the leave-one-composition source-card routine accessed
the original column name.

The implementation now retains `composition_key` and adds `material_key` as an
alias for composition featurization. No scientific method, data release,
split, model, control, inferential procedure, or gate was changed. The
implementation hash must be regenerated before formal execution.
