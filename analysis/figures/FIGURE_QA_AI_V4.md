# AI-v4 main-figure QA record

## Canonical exports

- `knowledge_borrowing_overview_ai_v4`
- `figure2_failure_benchmark_nmi_v2`
- `figure3_relation_transfer_nmi_v2`
- `figure4_ordinal_screening_nmi_v2`

Each canonical figure is available as PDF, SVG, 300 dpi PNG and 600 dpi
LZW-compressed TIFF at 183 mm double-column width.

## Figure 1 visual contract

Figure 1 has one visual argument rather than a collection of mini-panels:
neighbouring experimental programmes remain on the left, candidate information
is tested by four ordered gates, and only one narrow relation or candidate-order
signal enters the sparse OOD recipient. Blue solid cubes represent measured
anchors; orange open cubes represent unmeasured candidates; teal denotes an
accepted path and coral an abstaining path.

The generated panel is explicitly conceptual. It contains no dataset names,
measurements, numerical claims or generated labels. All scientific words are
editable vector overlays. All numbers in panel b are loaded from
`source_data/knowledge_borrowing_overview_ai_v4.csv` and are checked against the
committed analysis outputs by `analysis/verify_main_figures_ai_v4.py`.

## Generative-asset provenance

The built-in image generator was used with the author's supplied image as a
style and composition reference, not as a literal edit. The complete prompt,
source paths, asset dimensions and scientific safeguards are recorded in
`assets/knowledge_borrowing_hero_ai_v4_provenance.md`.

## Visual QA checklist

- exact 183 mm page width and height below the 170 mm limit;
- no clipping, overlap or illegible gate labels at full size or half size;
- generated conceptual image remains visually subordinate to vector labels and
  committed quantitative evidence;
- consistent navy/blue, teal, orange and coral semantics across Figures 1-4;
- no fabricated data marks or pseudo-text in the generated asset;
- editable text in PDF and SVG, with the conceptual raster embedded once;
- final PDF independently rendered with Poppler before release.

## Final render audit

The final PDF reports one 518.74 x 374.17 pt page, equivalent to 183 x 132
mm. It was independently rendered with Poppler at 180 dpi and 90 dpi. The
full-size render showed no clipping, font substitution, colour shift or label
collision. The half-size render retained the left-to-right storyline and the
three headline decisions; small supporting statistics remain legible at the
intended double-column placement. The four gate labels were shortened to
Inputs, State, Relation and Falsifier after the first composite revealed label
crowding.
