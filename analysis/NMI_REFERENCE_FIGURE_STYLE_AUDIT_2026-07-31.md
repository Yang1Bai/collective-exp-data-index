# NMI and Nature reference-figure audit

## Decision

The previous workflow graphic used four equal-width cards, large headings and
text-heavy symbols. It communicated sequence, but it read as a presentation
dashboard rather than a scientific figure. The replacement uses the visual
grammar shared by the supplied Nature Machine Intelligence and Nature-family
papers: a scientific-object-led hero panel, a single causal flow, restrained
colour, and a compact quantitative evidence strip.

## Transferable visual moves from the supplied papers

| Reference PDF | Figure language observed | Element adopted here |
|---|---|---|
| `s42256-025-01173-w.pdf` | Molecular objects anchor a predictive/generative loop; the model is secondary to the scientific objects. | The overview begins with crystal, catalytic-interface and molecular-mixture programmes rather than database icons. |
| `s42256-026-01214-y.pdf` | A large architecture schematic is paired with compact dataset-composition panels. | One dominant transfer scene is paired with three result panels. |
| `s42256-026-01226-8.pdf` | Molecular mechanism, masking operation and application context are connected in one figure without decorative cards. | The transferable object is drawn as a relation moving through four scientific gates into an OOD landscape. |
| `s42256-026-01206-y.pdf` | Directional flow is explicit and alternative outcomes remain visually distinct. | Qualified transfer and abstention have separate teal and coral paths. |
| `s43588-026-00986-y.pdf` | Repeated small multiples use one consistent visual grammar and palette. | The 40-edge failure benchmark is a compact 8 × 5 repeated-mark matrix. |
| `s41586-025-09922-y.pdf` | Claim-bearing figures prioritize quantitative comparisons over ornamental illustration. | The lower strip reports effect estimates, intervals and rank outcomes rather than generic success icons. |
| `s42256-026-01277-x.pdf` | A broad framework is decomposed into a main workflow and explicit validation tasks. | The figure separates the transfer mechanism from prediction, screening and rejection endpoints. |

The remaining supplied papers reinforced the same constraints: limited colour
roles, lowercase panel letters, concise in-panel text, no decorative shadows,
and scientific objects that establish domain meaning before architecture
details.

## Final visual contract

- Full-width 181.6 mm figure on white.
- Panel **a** occupies approximately half the area and carries the scientific
  story: three neighbouring experimental object classes, candidate edges, four
  gates, a sparse measured region and an OOD candidate region.
- Panels **b--d** carry only claim-bearing quantities: 0/40 generic edges,
  routed RMSE effects with intervals, accepted screening, and a frozen
  rejection.
- Navy/blue identifies measured recipient evidence; orange identifies OOD
  candidates; teal/green identifies admitted knowledge; coral identifies
  harmful or rejected transfer; grey is structural context only.
- No database-card motif, no circular badges, no decorative framing, no 3D
  gloss, and no generated numerical marks.

## Generative-model boundary

An AI-generated, text-free scientific-object layer was used only to test the
composition. The submission figure was redrawn in Python with vector
primitives. The generated raster is retained as a design record and is not
embedded in the final SVG, PDF, PNG or TIFF.
