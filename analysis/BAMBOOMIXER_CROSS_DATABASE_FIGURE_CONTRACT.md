# Figure contract — cross-database electrolyte ranking

Core conclusion: Separately trained neighbouring conductivity programmes
substantially improve five-label candidate ranking in SolventSeg, but not
absolute calibration or the complete FINALES boundary; the correct route is a
programme-specific shortlist.

Figure archetype: asymmetric quantitative grid.

Target journal/output: *Digital Discovery* full paper; double-column,
183 × 132 mm; editable SVG and PDF plus 600-dpi TIFF and 300-dpi PNG.

Backend: Python/Matplotlib only.

Panel map:

- **a:** source programmes, overlap audit, equal-programme combination, and
  recipient.
- **b (hero):** five-anchor Spearman distributions for all 13 recipient-only
  configurations, their per-draw oracle, and the source portfolio.
- **c:** paired source advantages over the strongest fixed recipient, the
  recipient oracle, and the broad single donor.
- **d:** endpoint routing: absolute-prediction contrasts fail, while the
  complete FINALES reuse check supplies a programme boundary.

Evidence hierarchy:

- hero: source \(\rho=0.910\) versus strongest recipient \(\rho=0.537\);
- validation: source-minus-recipient and source-minus-oracle intervals;
- controls: zero target overlap, source-source overlap disclosure,
  absolute-calibration abstention, and FINALES boundary.

Statistics:

- \(n=100\) outcome-independent anchor selections at five labelled
  formulations;
- interval bars are 2.5th–97.5th percentiles across anchor selections;
- absolute-prediction intervals use 5,000 formulation-grouped bootstrap
  resamples;
- FINALES panel reports the complete 16-candidate multitask evaluation.

Reviewer risks:

- SolventSeg outcomes were inspected before portfolio design: label every
  panel as method development, not confirmation.
- The recipient oracle is an adversarial ceiling, not a deployable model.
- Multi-source gain over the broad donor is small and must not be called large
  synergy.
- Strong rank does not establish calibrated prediction or prospective
  discovery.
