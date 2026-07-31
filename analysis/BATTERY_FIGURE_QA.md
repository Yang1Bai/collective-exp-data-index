# Battery continuous-borrowing figure QA

## Export and layout audit

- Core conclusion: pass. A continuous credible Stage 1 feature is the nominated policy; hard CCA-v2 qualification over-abstains.
- Archetype: schematic-led five-panel quantitative composite.
- Backend: Python/matplotlib only for plotting, preview, and all exports.
- Final size: 7.2 in (183 mm) wide by 6.1 in high before tight bounding-box trimming.
- Typography: 5.6–9.4 pt sans-serif; bold lowercase panel labels; editable SVG text and PDF TrueType text (`svg.fonttype=none`, `pdf.fonttype=42`).
- Color: calendar and cycle strata use blue and purple with independent circle/square encodings; upper-quartile source distance is additionally encoded by open markers.
- Exports: editable SVG, vector PDF, 300 dpi PNG, and 600 dpi LZW-compressed TIFF.
- Visual inspection: the coverage warning, forest annotations, hard-OOD markers, gate counts, legends, and footer were inspected at final layout; no clipping or unresolved overlap remains.

## Statistical legend audit

### Panel a

- Split: Stage 1 measurements precede and are frozen before Stage 2 outcomes.
- Released target: 138 Stage 2 cells in 23 condition groups.
- Missingness: three cells in one z10 condition group lack the required AT_T23 endpoint; 135 cells in 22 groups remain.
- Consequence: the frozen 23-group primary is non-evaluable and is not replaced by the sensitivity analysis.
- Source data: `analysis/results/figure_battery_panel_a.csv`.

### Panel b

- Unit: held-out condition group, with calendar and cycle effects combined by equal-stratum weighting.
- Metric: relative reduction in mean condition-level RMSE; positive values favor adjacent-source borrowing.
- Center: observed equal-stratum mean contrast.
- Interval: 95% group-bootstrap interval from the post-release diagnostic.
- Test: one-sided sign-flip test with Holm adjustment across the four displayed controls.
- Baselines: endpoint-matched target-only, wrong-property source, within-source shuffle, and matched random features.
- Evidence status: outcome-guided post-release method development.
- Source data: `analysis/results/figure_battery_panel_b.csv`.

### Panel c

- Unit: one held-out condition group; n=8 calendar groups and n=14 cycle groups.
- Metric: relative condition-RMSE gain over target-only.
- OOD definition: outlined symbols are at or above the type-specific 75th percentile of Stage 1 source-condition distance.
- Summary: 7/8 calendar and 10/14 cycle groups improve; hard-OOD aggregate effects are −1.24% and +5.56%, respectively.
- Source data: `analysis/results/figure_battery_panel_c.csv`.

### Panel d

- Unit: held-out condition group.
- Gate: training-only CCA-v2 source-borrowing decision.
- Summary: 4/22 admitted overall, 4/8 calendar, and 0/14 cycle.
- Source data: `analysis/results/figure_battery_panel_d.csv`.

### Panel e

- Unit: one prewritten source-inspired lead and one matched control in each of the calendar and cycle strata.
- Endpoint: terminal retention at the target programme endpoint; lower is favorable for the prespecified direction.
- Result: calendar 93.51 versus 96.83; cycle 88.93 versus 91.75.
- Inference: directional card checks only; no confidence interval or population-level p-value is claimed.
- Source data: `analysis/results/figure_battery_panel_e.csv`.

## Integrity and traceability

No microscopy or selectively processed raster data are present. All quantitative marks are regenerated from the verified Stage 2 release audit, post-release sensitivity summary, condition borrowing map, and training-only gate table. The figure footer and contract explicitly prevent reinterpretation as a rescued confirmatory primary or prospective discovery result.
