# Multi-target OOD borrowing figure QA

## Evidence and statistics

- **Pass:** Figure uses only the independently verified formal result.
- **Pass:** Eight designated edges, 40 inherited real edges, and all ten frozen
  gate components are represented.
- **Pass:** Designated-edge intervals are the reported hierarchical intervals;
  non-designated points are shown descriptively in the ID–OOD plane.
- **Pass:** The 5% practical threshold, zero-effect line, absolute-utility
  failures, wrong and shuffled controls, learner sensitivity, Holm correction,
  and identity-overlap check remain visible.
- **Pass:** Programme-level wording identifies seven programme clusters rather
  than treating eight target tasks as independent programmes.
- **Pass:** The figure does not call any edge OOD repair and does not convert
  the post-outcome benchmark into prospective confirmation.

## Visual inspection

- **Pass:** One hero forest panel is supported by a protocol schematic,
  ID-versus-OOD effect map, and gate matrix.
- **Pass:** Panel labels, titles, axis labels, edge names, interval annotation,
  and gate labels are legible at the exported double-column size.
- **Pass:** Within-database and cross-database edges use stable blue and teal
  encodings; gate status uses both color and `P/F` symbols.
- **Pass:** No title, annotation, legend, or axis-label overlap remained in the
  final PNG inspection.
- **Pass:** No rainbow map or color-only pass/fail encoding is used.

## Export inspection

- **SVG:** 104,720 bytes; 172 editable `<text>` nodes.
- **PDF:** 111,597 bytes; TrueType text requested with `pdf.fonttype=42`.
- **PNG:** 2,385 × 1,813 pixels at approximately 300 dpi.
- **TIFF:** 4,762 × 3,626 pixels at 600 dpi with LZW compression.
- **Source data:** panel-specific CSV files are emitted to `analysis/results/`.
- **Reproducibility:** `make_multi_target_ood_borrowing_figure.py` rebuilds all
  four exports from the verified result tables.

## Claim boundary

The figure establishes heterogeneity and the failure of generic feature
injection to satisfy a conjunctive OOD-repair rule. It retains a robust
within-database alloy error reduction as evidence that useful borrowing exists,
while showing that the gain is not OOD-specific and does not produce positive
absolute OOD R². It does not establish cross-database OOD repair or prospective
discovery acceleration.
