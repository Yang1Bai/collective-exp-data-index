# Neighbor-map exploration figure QA

- **Core conclusion:** Caltech ranking utility is selective under finite-seed
  empirical nulls; family-first allocation can advance external AUC without
  demonstrating additional top-hit recall beyond the best single donor.
- **Evidence chain:** panel b audits source qualification; panel c shows the
  null adaptive augmentation result; panel d displays observed static rankings
  against the shuffled-source 95% interval and four-test Holm values; panel e
  compares family-first directly with the best single neighboring donor.
- **Archetype:** quantitative grid with a workflow header.
- **Backend:** Python/matplotlib only.
- **Final size:** 7.2 inches (182.9 mm) wide.
- **Source-data traceability:** panels use the Caltech policy utility table,
  family-first portfolio metrics and the review-triggered corrective inference
  summary. No observations were sampled or removed for the figure revision.
- **Statistics:** the panel-d null is 100 shuffled-source seeds per scope;
  one-sided finite-sample empirical p values use the plus-one correction and
  are Holm-adjusted across two donors by two scopes. Only hard-OOD ESTM remains
  below 0.05. Panel e reports AUC20 differences from the best single donor;
  recall differences are zero in both scopes.
- **Exports:** SVG and PDF retain editable text; PNG is 300 dpi; TIFF is 600
  dpi.
- **Automated preflight:** 14 pass, 0 warning, 0 fail.
- **Visual inspection:** no clipping or panel-label collisions were observed at
  final width after shortening panel-d p-value labels.
