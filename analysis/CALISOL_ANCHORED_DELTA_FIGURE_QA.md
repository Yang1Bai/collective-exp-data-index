# Figure 2 panel-c QA: CALiSol provenance-anchored contrast transfer

## Scientific mapping

- **Claim:** changing the transferred object from an absolute neighboring
  function to a within-article response relation improves the same
  held-article-out task after one target-article anchor.
- **Independent unit:** source article DOI, \(n=11\).
- **Point definition:** article-level RMSE over non-anchor −40 °C
  formulations.
- **Matched baseline:** absolute −30 °C ridge donor calibrated by the same
  target-article anchor.
- **Primary model:** within-source-article −30 °C contrast ridge with the same
  anchor.
- **No exclusions for display:** all 11 common-scope articles appear. The three
  harmful articles remain visible as crosses.

## Statistical annotation

- Macro-RMSE: 0.4901 absolute versus 0.4562 contrast.
- Relative macro-RMSE gain: 6.91%.
- Interval: 10,000-replicate article-cluster bootstrap, [0.88,14.00%].
- Primary test: exact one-sided sign-flip test over 11 paired article RMSE
  differences, \(p=0.0352\).
- Falsifier: 199 within-source-article donor-label permutations,
  \(p=0.005\).
- The caption states that this is a post-outcome mechanistic reanalysis.

## Visual QA

- Python/matplotlib exclusively produced the SVG, PDF, PNG and TIFF.
- Automated source preflight: 13 passes, zero failures, one reviewed width
  warning.
- Exported SVG size: 513.45 pt = 181.1 mm wide, within a 183 mm double-column
  contract after tight-bounding-box expansion.
- SVG and PDF retain editable text (`svg.fonttype=none`, `pdf.fonttype=42`).
- TIFF: 4,280 × 4,059 pixels at 600 dpi with LZW compression.
- Minimum explicit text size in the source is 5.4 pt.
- Improved and harmful articles differ by both color and marker shape; color is
  not the only encoding.
- Final-size visual inspection found no clipping. Close harmful points A08 and
  A09 use separate label offsets.

## Remaining reviewer boundary

The panel visualizes method-development evidence on one programme. It must not
be captioned as preregistered, independent, zero-shot, universal, or
prospective validation.

