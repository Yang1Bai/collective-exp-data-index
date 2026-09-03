# Locked blind statistical plan

This plan was frozen while Balam job 71570 was pending, before the
development-gate result and before any blind hydrogen-evolution value was
inspected.

The primary analysis uses the 60-label recipient budget and all 100
outcome-independent scaffold draws. The experimental observations are the
blind molecules; chemical dependence is handled by clustering molecules by
canonical Bemis–Murcko scaffold. The 100 label-budget draws are computational
replicates describing sensitivity to which recipient measurements happen to
be available. They are not treated as 100 additional experimental samples.

The primary effect is the mean paired relative reduction in log-transformed
hydrogen-evolution RMSE within the frozen hard-OOD 40% scope. Its 95% interval
comes from 10,000 paired hierarchical bootstrap replicates that resample blind
scaffolds and label-budget draws while preserving method pairing. One-sided
paired scaffold sign randomization tests are applied to three named
comparisons, with Holm correction across that family.

A transfer edge is accepted only when all frozen conditions hold: at least 5%
mean OOD RMSE improvement over the target-only model; a positive lower
bootstrap bound; Holm-adjusted \(p<0.05\); positive mean draw-specific absolute
\(R^2\); improvement over the matched shuffled donor; and no more than 2%
mean RMSE harm over the complete blind set. Statistical significance alone is
therefore insufficient.

Every method, OOD scope, null control and secondary endpoint will be reported,
including null or harmful results. Passing the gate supports one retrospective
experimental-database borrowing edge; it does not prove prospective discovery
or universality.
