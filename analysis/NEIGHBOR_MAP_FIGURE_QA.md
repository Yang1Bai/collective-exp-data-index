# Neighbor-map exploration figure QA

## Export and layout audit

- Core conclusion: pass. The figure distinguishes predictive augmentation from OOD proposal-ranking utility.
- Archetype: asymmetric five-panel quantitative composite with one schematic-led panel.
- Backend: Python/matplotlib only for plotting, preview, and all exports.
- Final size: 7.2 in (183 mm) wide by 6.15 in high before tight bounding-box trimming.
- Typography: 6.0–9.4 pt sans-serif; bold lowercase panel labels; editable SVG text and PDF TrueType text (`svg.fonttype=none`, `pdf.fonttype=42`).
- Color: teal/blue/purple encode qualified sources; wrong controls remain gray; marker shape independently encodes external versus hard OOD.
- Exports: editable SVG, vector PDF, 300 dpi PNG, and 600 dpi LZW-compressed TIFF.
- Visual inspection: panel labels, titles, axes, legends, confidence intervals, and footer were inspected at the exported 183 mm layout; no clipping or unresolved overlap remains.

## Statistical legend audit

### Panel b

- Unit: source-policy pair summarized over two candidate scopes.
- Center: mean admission rate and mean source weight.
- Source skill: provenance-aware source out-of-fold R² from the frozen source-quality table.
- Baseline: the 0.20 wrong-source admission ceiling is a prespecified gate, not a confidence interval.
- Source data: `analysis/results/figure_neighbor_map_panel_b.csv`.

### Panel c

- Unit: seed-level AUC20 policy contrast summarized within the complete external and hard-OOD candidate pools.
- Center: mean AUC20 increment over target-only.
- Interval: frozen bootstrap 95% confidence interval.
- Multiple comparison: Holm-adjusted decision gate from the verified Caltech benchmark; no displayed policy passes all frozen gates.
- Source data: `analysis/results/figure_neighbor_map_panel_c.csv`.

### Panel d

- Unit: candidate entity under a static acquisition ranking.
- Metric: cumulative top-5% hit area through acquisition 20 (AUC20); direct labels report recovered top-5% entity count.
- Scopes: 144 external candidates and 58 hard-OOD candidates from a 483-composition Caltech target.
- Variability: randomized references are seed means; deterministic static policies have no seed interval.
- Source data: `analysis/results/figure_neighbor_map_panel_d.csv`.

### Panel e

- Unit: connected formula/DOI/ICSD provenance component; within-group outcome aggregation is the maximum.
- Metric: distinct-group AUC through acquisition 20.
- Null: 5,000 paired shuffled-source rankings conditional on the fixed target pool.
- Test: one-sided conditional randomization; p=0.0020 externally and p=0.0030 in hard OOD.
- Multiplicity and evidence status: this is outcome-informed method development on one target, not independent confirmation; p-values are displayed as conditional diagnostics rather than a new confirmatory family.
- Source data: `analysis/results/figure_neighbor_map_panel_e.csv`.

## Integrity and traceability

No microscopy or selectively processed raster data are present. Every quantitative mark is regenerated from the listed CSV files or verified JSON-derived tables. The earlier separate Caltech and family-first figures remain available for decomposition and regression comparison.
