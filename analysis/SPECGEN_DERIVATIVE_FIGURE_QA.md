# Figure 3 QA: controlled OER relation transfer

## Export and layout

- Target: *Digital Discovery* full paper.
- Final size: 171 mm × 127 mm, matching the current RSC double-column width
  and remaining below the 233 mm maximum height.
- Backend: Python only for plotting, preview, export and programmatic QA.
- Exports: editable SVG, editable-text PDF, 600 dpi LZW-compressed TIFF and
  300 dpi PNG preview.
- Font: Arial-compatible sans serif fallback; 7 pt body/ticks and 8.5 pt bold
  panel labels at final size.
- Visual inspection: passed at final aspect ratio. No clipped labels, panel
  collisions, redundant legends or ambiguous route colours remain.
- Colour safety: route is encoded by colour and direct text. Positive, ranking
  only and rejection states therefore remain interpretable without colour.
- Current RSC guidance checked on 30 July 2026: figures may use colour free of
  charge; TIFF should be at least 600 dpi; PDF is accepted; double-column width
  is 17.1 cm and maximum height is 23.3 cm.

## Statistical legend

### Panel b

- `n` definition: 126 catalysts in each complete held-out derivative system.
- Metric: Spearman rank correlation between unchanged donor prediction and
  recipient OER outcome.
- Baselines: 720-feature spectral donor and six-slot composition donor.
- Null: 500 source-outcome permutations, refitting the same donor
  architecture on every permutation.
- Multiple comparison: one-sided permutation p values corrected by Holm across
  the four derivative systems; exact values are in the figure source CSV.
- Display: composition shuffled-source distributions are pale violins; the
  dashed line is the prespecified practical rho = 0.30 gate.

### Panel c

- `n` definition: 126 candidates per derivative system.
- Label budget: five recipient labels per draw.
- Repetitions: 200 fixed random anchor draws per derivative.
- Baseline: three-nearest-neighbour interpolation using the same five target
  anchors and composition distance but no donor prediction.
- Borrowed model: donor composition prediction plus three-nearest-neighbour
  interpolation of the five observed target residuals.
- Metrics: relative RMSE gain and Spearman gain over the matched target-only
  baseline.
- Point: pooled candidate-by-draw effect.
- Interval: percentile 95% interval from 500 candidate-identity bootstrap
  resamples, retaining all anchor-draw predictions for each resampled
  candidate.
- Direction: positive RMSE gain means lower borrowed-model error.

### Panel d

- `n` definition: 20 later synthesized candidates per derivative system.
- Metric: Spearman rank correlation for the unchanged donor prediction.
- Test: 100,000 one-sided fixed target-label permutations.
- Multiple comparison: Holm correction across A–D; adjusted p values are
  printed next to the points.
- Interpretation guard: candidates were selected by the source study's
  workflow. This is temporal rank corroboration, not an unbiased acquisition or
  prospective discovery trial.

## Source-data and integrity checks

- Figure source data:
  `results/specgen_derivative_oer_figure_source_data.csv` (20 rows).
- Claim-bearing inputs:
  `specgen_derivative_zero_label_metrics.csv`,
  `specgen_composition_secondary_shuffle.csv`,
  `specgen_composition_secondary_summary.json`, and
  `specgen_top20_temporal_metrics.csv`.
- Independent result verifier: passed; 500 composition null rows, 800
  five-label draw rows and 80 temporal candidate rows are complete.
- SVG contains 91 editable text nodes; the PDF yields selectable text.
- TIFF dimensions are 4038 × 3000 px at 600 dpi.
- No raster experimental image, crop, contrast adjustment, pseudo-colour,
  stitching or reused image panel is present.

## Claim boundary

The figure supports a controlled within-programme mechanism demonstration:
derivatives B and D improve both prediction and ranking, A is ranking-only, and
C is rejected because prediction worsens. It does not support four independent
replications, universal composition transfer, cross-laboratory transfer or
prospective discovery acceleration. The composition analysis remains a
disclosed post-primary result because it was promoted after the planned
composition control was inspected.
