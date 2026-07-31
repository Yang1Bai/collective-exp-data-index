# Main-figure QA: NMI v3

## Scope

This audit covers Figures 2--4 in the streamlined manuscript. Figure 1 remains
the AI-assisted conceptual overview (`knowledge_borrowing_overview_ai_v4`).
Figures 2--4 are deterministic, data-backed Python figures.

## Figure contracts

- **Figure 2:** a real in-programme relation can fail across provenance, and
  generic donor features do not repair the declared far-OOD portfolio.
- **Figure 3:** a component-order-invariant relation can support selected OOD
  prediction, while controlled perturbations route related edges to numerical
  prediction, ranking only, or rejection.
- **Figure 4:** neighbouring programmes can recover candidate order from sparse
  recipient labels, but the unchanged route may fail in a frozen second
  recipient and must then abstain.

Each figure has one dominant conclusion, a 183 mm submission width, Arial text
at 5 pt or larger, editable PDF/SVG text, a 600 dpi LZW-compressed TIFF, and a
300 dpi PNG preview.

## Files

| Figure | Script | Source-data export | Canonical PDF |
|---|---|---|---|
| 2 | `analysis/make_figure2_failure_benchmark_nmi_v3.py` | `analysis/figures/source_data/figure2_failure_benchmark_nmi_v3.csv` | `analysis/figures/figure2_failure_benchmark_nmi_v3.pdf` |
| 3 | `analysis/make_figure3_relation_transfer_nmi_v3.py` | `analysis/figures/source_data/figure3_relation_transfer_nmi_v3.csv` | `analysis/figures/figure3_relation_transfer_nmi_v3.pdf` |
| 4 | `analysis/make_figure4_ordinal_screening_nmi_v3.py` | `analysis/figures/source_data/figure4_ordinal_screening_nmi_v3.csv` | `analysis/figures/figure4_ordinal_screening_nmi_v3.pdf` |

## Automated checks

- Nature-figure strict validator: **14 PASS, 0 WARN, 0 FAIL** for each script.
- Semantic verifier: `analysis/verify_main_figures_nmi_v3.py` returned
  `verified-complete` and wrote
  `analysis/results/main_figures_nmi_v3_VERIFIED.json`.
- The verifier recomputed the Figure 2 coefficient transport metrics and the
  0/40 complete-gate verdict; checked the Figure 3 external raw/log (R^2),
  Spearman value, row count, comparator family and controlled effects; checked
  the Figure 4 model count, primary ordering advantage and frozen null/harmful
  interval; and hashed all PDF/SVG/PNG/TIFF exports.

## Visual checks

All three PDFs were rendered independently with Poppler at 180 and 90 dpi.
The 90 dpi audit confirmed that panel labels, axes, interval direction, route
labels and the primary verdict remain readable at reduced display size. No
panel, tick label, confidence interval or decision label is clipped. Figure 4c
shows the full negative lower tails of sparse-recipient uncertainty rather than
truncating them at zero.

## Claim guards retained in the design

- Figure 3 external unseen-salt prediction is retrospective method development,
  not prospective confirmation.
- Figure 3 catalyst composition effects are disclosed post-primary analyses.
- Figure 4 primary screening stress test is outcome-inspected; the frozen second
  recipient is the unchanged boundary test.
- Ordinal success is not described as calibrated conductivity prediction or as
  prospective discovery acceleration.
