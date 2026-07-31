WITH caltech_adaptive_gains(
    label,
    scope,
    policy,
    mean_auc20_gain,
    ci_lo,
    ci_hi,
    holm_p,
    passes_all_frozen_gates
) AS (
    VALUES
        ('External — OBELiX residual', 'external candidate', 'OBELiX residual', -0.06, -0.30, 0.12, 1.000, 0),
        ('External — ESTM residual', 'external candidate', 'ESTM residual', -0.06, -0.23, 0.07, 1.000, 0),
        ('External — multisource residual', 'external candidate', 'multisource residual', -0.09, -0.34, 0.09, 1.000, 0),
        ('Hard OOD — OBELiX residual', 'hard OOD 40%', 'OBELiX residual', 1.10, -0.38, 2.59, 0.588, 0),
        ('Hard OOD — ESTM residual', 'hard OOD 40%', 'ESTM residual', -0.07, -1.11, 0.91, 1.000, 0),
        ('Hard OOD — multisource residual', 'hard OOD 40%', 'multisource residual', 1.27, -0.75, 3.22, 0.657, 0)
)
SELECT
    label,
    scope,
    policy,
    mean_auc20_gain,
    ci_lo,
    ci_hi,
    holm_p,
    passes_all_frozen_gates
FROM caltech_adaptive_gains;
