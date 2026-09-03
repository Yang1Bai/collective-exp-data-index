# Figure 3e–h QA: state-matched MPEA borrowing

## Release decision

**Pass.** The figure is suitable for double-column manuscript layout and is
generated directly from the independently verified V2 result files. No plotted
number is manually transcribed.

## Scientific checks

- The plotted primary Q4 effect is +9.21% relative RMSE gain with a 95% two-way
  cluster-bootstrap interval of [4.43, 14.37]%.
- The architecture-matched shuffled control is −0.26%
  [−1.81, 1.01]%.
- The real-minus-matched-shuffled contrast is +9.47 percentage points
  [4.80, 14.34]%.
- The Q1 effect is +7.21% [3.05, 11.52]%; Q4-minus-Q1 is +2.00 percentage
  points [−4.66, 8.62]%, so the figure does not imply Q4-exclusive benefit.
- Pooled augmented Q4 R² is 0.103. The caption separately discloses that the
  Q4 R² bootstrap interval crosses zero.
- The measured-UTS bar is labelled as an auxiliary ceiling, not learned
  transfer.
- V2 uses the identical concatenation architecture for real and shuffled UTS
  features and supersedes the V1 residual-anchor shuffled comparison.

## Statistical checks

- Primary intervals use 100,000 two-way cluster-bootstrap replicates over 59
  elemental systems and 60 frozen model-by-draw runs.
- State-only and measured-UTS ceiling intervals are descriptive t intervals
  across the 60 frozen runs and are identified as such in the caption and
  source-data table.
- The source-data table is generated from
  `state_matched_mpea_balam_v2_bootstrap_summary.json`,
  `state_matched_mpea_balam_v2_summary.json`, and
  `state_matched_mpea_balam_v2_screen.csv`.
- Re-running the formal verifier returned `verified-complete` with design hash
  `a250f52f2653f90d000bd70cf6913adaf0b38106c21d1ef5e03969140baae6b4`.

## Visual and export checks

- PNG: 2307 × 1287 pixels at 300 dpi.
- TIFF: 4624 × 2574 pixels at 600 dpi.
- SVG: editable text retained (`svg.fonttype = none`; 65 text elements).
- PDF: valid PDF header with embedded TrueType text (`pdf.fonttype = 42`).
- Panel labels are e–h to extend the existing Figure 3a–d benchmark.
- Text remains legible at double-column width; no label, interval, or annotation
  overlaps in the final rendered preview.
- Color does not carry meaning alone: every effect and control has a direct text
  label and numerical annotation.

## Files

- `figures/state_matched_mpea_borrowing.svg`
- `figures/state_matched_mpea_borrowing.pdf`
- `figures/state_matched_mpea_borrowing.tiff`
- `figures/state_matched_mpea_borrowing.png`
- `results/state_matched_mpea_figure_source_data.csv`
- `make_state_matched_mpea_figure.py`

## Claim boundary

The admissible claim is that state-matched, leakage-controlled neighboring
endpoint borrowing produces a source-specific and practically useful reduction
of error within the chemically distant Q4 region of this alloy programme. The
analysis is post-selection and same-programme; it is neither independent
prospective confirmation nor evidence that the gain is statistically stronger
in Q4 than in Q1.
