# Final manuscript SVG figures

This folder contains only the figures used by the current Draft-V2 manuscript.
Candidate layouts and superseded versions are intentionally excluded.

## Full manuscript figures

- `Figure_1.svg` — evidence landscape, LiAsF6 chemistry-state learner, catalyst representation screening, and falsification gate
- `Figure_2.svg` — broad far-OOD transfer screen and criterion-depth matrix
- `Figure_3.svg` — chemistry-state support, external predictions, and matched-control falsifiers
- `Figure_4.svg` — temperature-resolved composition landscapes, screening endpoints, sparse-budget robustness, and recipient-specific routing

## Standalone panels for manual layout

- `Figure_1a.svg` through `Figure_1d.svg`
- `Figure_4a.svg` through `Figure_4d.svg`

Figures 2 and 3 were authored as single editable SVG canvases, so their panels remain grouped within the full-figure files.
See `source_manifest.csv` for the tracked figure path and the claim-bearing
evidence mapped to every delivered file. The release SVGs are the authoritative
repository copies; temporary authoring directories are not required to use or
audit them.

## Editability note

All delivered files are valid SVG canvases with editable text, axes, annotations, and layout.
Figure 1a intentionally preserves the supplied manuscript artwork as an embedded image layer.
The dense matrix/heatmap layers in Figures 2 and 3 are also embedded image layers, while their surrounding scientific annotations remain vector objects.

The submission-wide claim map, model allowlist and article-ready links are in
[`paper/`](../../../paper/README.md).
