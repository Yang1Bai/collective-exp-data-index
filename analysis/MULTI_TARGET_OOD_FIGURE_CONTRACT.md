# Multi-target OOD borrowing figure contract

## Core conclusion

Neighbor-derived features reduce error in selected OOD slices, but simple
feature injection does not automatically repair the recipient's OOD knowledge
deficit: no designated edge passes the complete OOD-specific and
absolute-utility gate.

## Figure architecture

- **Archetype:** asymmetric quantitative grid.
- **Backend:** Python/matplotlib only.
- **Final size:** 183 mm × 145 mm, double-column.
- **Panel a — frozen comparison.** Target outcomes are hidden while complete
  development features define fixed ID-like Q1 and OOD Q4 groups. Identical
  target-label draws fit target-only and donor-augmented models. The primary
  estimand is Q4 gain minus Q1 gain, with wrong and shuffled donors retained.
- **Panel b — designated-edge effects (hero).** Hierarchical 95% intervals for
  Q4 relative-RMSE gain across eight predeclared primary edges. The zero and 5%
  practical thresholds are visible.
- **Panel c — OOD gain is not synonymous with OOD-specific gain.** All 40 real
  edges are placed by Q1 and Q4 gain. The diagonal separates OOD-enriched from
  ID-enriched effects; designated edges are outlined.
- **Panel d — conjunctive gate audit.** Every component of the frozen edge gate
  is shown for all eight designated edges, together with the programme-level
  and cross-database decisions.

## Evidence hierarchy

- **Hero evidence:** panel b, the eight designated hierarchical effects.
- **Specificity evidence:** panel c, the direct OOD-versus-ID comparison.
- **Controls and robustness:** panel d, including wrong source, shuffled source,
  learner sensitivity, multiplicity, absolute utility, and identity exclusion.
- **Protocol context:** panel a.

## Statistics

- Independent evaluation units are intact element-set or Bemis–Murcko-scaffold
  groups, not model predictions or seeds.
- Designated-edge intervals resample target-training repetitions and intact
  evaluation groups.
- Wrong- and shuffled-source contrasts use paired repeat bootstraps.
- One-sided sign-flip tests are Holm-adjusted across eight designated edges.
- Programme inference resamples seven programme clusters; two OpenPoly targets
  do not count as independent programmes.

## Source data

- `results/multi_target_ood_edge_summary.csv`
- `results/multi_target_ood_target_summary.csv`
- `results/multi_target_ood_summary.json`
- figure-specific panel CSVs emitted by the plotting script

## Export contract

- Editable SVG text.
- TrueType text in PDF.
- 600 dpi TIFF plus PNG preview.
- White background, sans-serif font, restrained neutral/blue/teal palette.
- Pass/fail is encoded by both color and symbols.

## Reviewer risks addressed

- A positive relative gain is not called OOD repair unless it exceeds ID gain.
- Model-run repetitions are not presented as independent target datasets.
- Negative absolute R² remains visible.
- Non-designated edges are shown rather than silently discarded.
- The benchmark is labelled post-outcome method development and cannot replace
  an outcome-unseen external programme.
