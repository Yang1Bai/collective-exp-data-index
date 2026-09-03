# State-matched MPEA control amendment V2

The first verified Balam run correctly evaluated the frozen primary contrast
between the state-aware target model and the same model augmented with a
chemical-system-cross-fitted UTS prediction. It therefore supports the primary
target-only effect.

Its shuffled-source comparison was not architecture-matched: the real donor
entered by feature concatenation, whereas the shuffled donor entered a
residual-anchor model. This does not invalidate the real-versus-target-only
contrast, but it prevents the V1 real-minus-shuffled estimate from being used as
source-specific evidence.

V2 changes one item only. Fold-wise shuffled UTS predictions now enter the
identical concatenation architecture, learner, seed, target-label draw and
evaluation rows as the real donor. The target task, planned-state covariates,
elemental-system split, n=60 budget, 30 draws, two tree learners, Q1/Q4
definitions and two-way cluster bootstrap remain unchanged. V1 is retained in
full; V2 supersedes only its shuffled-source contrast.
