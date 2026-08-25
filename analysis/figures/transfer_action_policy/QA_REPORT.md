# Figure QA report

## Figure 5

- Conclusion test: pass. The three panels lead directly to `PREDICT`, `RANK`, and `WITHHOLD` at recipient-qualified endpoint resolution.
- Statistical integrity: pass. Point estimates and intervals are read from `transferability_evidence_cards.json`; no values were estimated from artwork.
- Visual inspection: pass at original PNG resolution. Titles, interval annotations, action labels, axis labels, and support notes are visible without overlap or clipping.
- Export integrity: pass. SVG retains 38 editable text nodes; PDF is one 183-mm-wide page; PNG is 450 dpi; LZW TIFF is 600 dpi.

## Figure 6

- Conclusion test: pass. Missing route metadata lead to data recovery, whereas a bridge experiment is restricted to a route-complete, feasible, falsifier-passing but decision-ambiguous case.
- Integrity boundary: pass. The figure reports a readiness audit and policy states; it does not plot or imply an unobserved synthesis-route effect.
- Visual inspection: pass at original PNG resolution. Flow arrows, YES/NO checklist states, current verdict, counts, and panel labels are visible without overlap or clipping.
- Export integrity: pass. SVG retains 48 editable text nodes; PDF is one 183-mm-wide page; PNG is 450 dpi; LZW TIFF is 600 dpi.

## Scope boundary

- This repository package verifies the generated figure files and source data.
- Manuscript DOCX derivatives are intentionally excluded from this standalone code-and-figure PR.
