# Nature-v3 main-figure QA record

## Canonical exports

- `knowledge_borrowing_overview_nature_v3`
- `figure2_failure_benchmark_nmi_v2`
- `figure3_relation_transfer_nmi_v2`
- `figure4_ordinal_screening_nmi_v2`

Each canonical figure is exported as editable SVG, editable-text PDF, 300 dpi
PNG, and 600 dpi LZW-compressed TIFF at 183 mm double-column width.

## Figure 1 redesign

The previous four-panel overview was rejected during visual audit because it
compressed the workflow, failure benchmark, effect forest, and screening result
into a second summary dashboard. The v3 design uses one dominant scientific
workflow and one compact evidence strip. Its visual hero is the relation/order
signal that crosses four explicit checks while the source database remains in
place. Numerical evidence is limited to the three operational outcomes:
prediction, screening, and abstention.

The design follows the current Nature research-figure specifications used for
the audit: 183 mm double-column width, maximum height below 170 mm, editable
Arial text, 5-7 pt body text, 8 pt bold lowercase panel labels, ordered panels,
and vector-first export. Colour is restricted to scientific marks and
directional decisions; explanatory text is dark neutral.

## Cross-figure visual audit

- Figure 2 retains the strongest relation-transport failure as its dominant
  evidence panel, with the 40-edge benchmark and conjunctive gate subordinate.
- Figure 3 retains the transfer-distance schematic as its anchor and separates
  complete prediction from falsifier results.
- Figure 4 retains the 13-model ordering benchmark as its dominant evidence
  panel and isolates the frozen programme boundary in a separate panel.
- Across all four figures, navy/blue denotes measured recipient evidence,
  teal/green denotes accepted transfer, orange denotes held-out candidates or
  ranking-only evidence, coral denotes rejection or harm, and grey denotes
  baselines and construction lines.

## Semantic verification

`analysis/verify_main_figures_nature_v3.py` checks all canonical exports and
the numerical anchors against the result tables, including:

- 40 real generic edges and zero complete passes;
- the alloy transported-coefficient failure;
- four controlled catalyst effects;
- unseen-salt raw R2 and Spearman correlation;
- five-anchor source and recipient ordering plus top-quartile precision; and
- the frozen second-recipient abstention decision.

## Visual QA

All canonical PDFs were rendered independently with Poppler at 180 dpi and at
half-size. The final PDF page widths are 518.738 pt (183.0 mm) for every main
figure; heights are 114.3, 143, 151, and 150 mm for Figures 1-4, respectively,
all below the 170 mm Nature limit. The inspection checked clipping, font
substitution, panel order, title/label collisions, line visibility, and whether
the main scientific message remains legible without reading the caption.

The audit triggered three corrections beyond the Figure 1 redesign: Figure 2
gate annotations were moved inside the fixed page boundary, Figure 3 received a
shorter unclipped falsifier title, and Figure 4 received a separated boundary
heading plus additional bottom clearance. No clipping remained in the final
rendered PDFs.
