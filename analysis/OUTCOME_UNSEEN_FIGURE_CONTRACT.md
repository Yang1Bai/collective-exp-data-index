# Outcome-unseen validation figure contract

- **Core conclusion:** outcome-unseen validation separates a small reverse-
  transport direction from full predictive utility: Starrydata shows a positive
  directional interval but fails multiplicity, absolute-utility, specificity,
  policy, and hypothesis-card gates; TRI OER shows no predictive benefit; the
  two-target mean is null and heterogeneous.
- **Archetype:** asymmetric quantitative validation grid with the target-level
  forest plot as the hero panel.
- **Backend:** Python/matplotlib exclusively for drawing, previewing, export,
  and visual QA.
- **Target/output:** *Digital Discovery*, double-column 183 mm width; editable
  SVG/PDF, 600 dpi TIFF, and 300 dpi PNG.
- **Panel a — independent-target inference:** relative RMSE effects and 95%
  intervals for Starrydata reverse transport, four-plate TRI OER, and their
  two-target random-effects synthesis. Full-gate status and absolute utility are
  labelled directly.
- **Panel b — frozen gate matrix:** direction, Holm-corrected inference,
  absolute utility, learner/representation robustness, matched specificity,
  exploration policy, and prewritten hypothesis cards for both targets.
- **Panel c — robustness envelope:** mean n=30 hardest-OOD relative RMSE effect
  for every frozen learner-representation cell. These are conditional repeat
  summaries, not independent-target intervals.
- **Panel d — prewritten hypotheses:** Holm-adjusted p values for all six frozen
  source-derived hypothesis cards. Sign encodes the paired mean effect; the
  0.05 threshold is explicit.
- **Evidence hierarchy:** panel a decides the predictive replication claim;
  panel b shows why a directional Starrydata interval does not constitute a
  full pass; panel c demonstrates representation/learner heterogeneity; panel d
  prevents post-outcome scientific-story replacement.
- **Statistics:** Starrydata two-level repeat × component/provenance bootstrap,
  100 repeats, three learners, two representations, and Holm correction over
  three primary contrasts; TRI four independent plates, 100 repeats per plate,
  exact plate-sign randomization, random-effects synthesis, three learners, two
  representations, and Holm correction; two-target random-effects synthesis.
- **Source data:** panel-specific CSV files are generated directly from the two
  portable `VALIDATED` JSON files, the two formal hypothesis-test tables, and
  the multi-target summary.
- **Image integrity:** all marks and annotations are generated from verified
  compact outputs; no manual graphical adjustment.
- **Reviewer risks shown:** neither new target passes the full prediction gate;
  Starrydata absolute R2 is negative; TRI has zero plates with positive absolute
  R2; the pooled interval crosses zero with I2 about 77%; all six prewritten
  hypotheses fail Holm correction; seed/repeat variation is not presented as
  independent-target replication.
