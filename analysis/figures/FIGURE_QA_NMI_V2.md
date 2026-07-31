# Main-figure QA record

## Canonical exports

- `knowledge_borrowing_overview_nmi_v2`
- `figure2_failure_benchmark_nmi_v2`
- `figure3_relation_transfer_nmi_v2`
- `figure4_ordinal_screening_nmi_v2`

Each figure is exported as editable SVG, editable-text PDF, 300 dpi PNG, and
600 dpi LZW-compressed TIFF at 183 mm double-column width.

## Static preflight

All four source scripts pass the Nature-figure strict preflight with zero
warnings and zero failures. The checks cover source syntax, publication-safe
font configuration, minimum text size, colour-map choice, editable text,
vector and raster exports, raster resolution, final width, data exclusions,
demo-data boundaries, log guards, and backend consistency.

## Semantic verification

`analysis/verify_main_figures_nmi_v2.py` independently checks the canonical
exports and the main numerical anchors against the result tables. The current
verification status is `verified-complete`:

- 40 real generic donor-feature edges and zero complete passes;
- alloy source \(R^2=0.790\) and transported \(R^2=-3.006\);
- catalyst relative RMSE effects of +3.19%, +16.35%, -10.38%, and +26.07%;
- external unseen-salt raw \(R^2=0.62944\) and Spearman \(\rho=0.87083\);
- five-anchor source \(\rho=0.91030\), best fixed recipient
  \(\rho=0.53664\), and \(\Delta\rho=0.37366\);
- frozen second-recipient decision `not-replicated`.

## Visual QA

All PDFs were rendered independently with Poppler at 180 dpi and inspected for
clipping, font substitution, panel-order errors, and title/label collisions.
The final design uses one dominant evidence panel per figure, scientific object
glyphs rather than generic database icons, and directional colour only for
accepted, ranking-only, and rejected routes.

## Claim-boundary note

Figure 3 labels the catalyst composition relation as post-primary. Figure 4
keeps Spearman correlation for the first recipient and pairwise concordance for
the frozen second recipient in separate subpanels so that the metrics are not
treated as numerically interchangeable.
