# Figure QA — cross-database electrolyte ranking

Status: **passed static preflight and visual QA**.

## Scientific integrity

- Panel a uses all three source programmes in the frozen portfolio and reports
  both the 71-record source-source overlap and zero source-target overlap.
- Panel b uses every one of the 100 five-anchor draws and all 13 declared
  recipient-only configurations; no model or draw was removed.
- The recipient oracle is the maximum recipient-only Spearman value within
  each draw and is explicitly labelled as an oracle, not a deployable policy.
- Panel c uses paired draw-wise contrasts. Intervals are the 2.5th–97.5th
  percentiles over the 100 anchor selections.
- Panel d uses the two frozen absolute-prediction contrasts and their 5,000
  formulation-bootstrap intervals. The FINALES annotation uses the complete
  16-candidate multitask evaluation, not a favourable seven-candidate subset.
- SolventSeg and FINALES are labelled in the manuscript as post-outcome method
  development or boundary evidence; the figure does not imply independent
  confirmation.

## Visual QA

- Core conclusion is visible from the title and panel order.
- Hero evidence occupies the full right column.
- Signal, adversarial oracle, source-interaction increment, and failed
  numerical route use distinct teal, orange, navy and red encodings.
- All panel labels and axis labels are readable at 183-mm width.
- No text, title, confidence interval, or panel overlaps remain in the final
  PNG inspection.
- The figure remains interpretable in grayscale through position and labels,
  not colour alone.
- SVG text remains editable.

## Export QA

- SVG: editable vector text.
- PDF: editable TrueType text.
- PNG: 2,282 × 1,547 pixels at 300 dpi.
- TIFF: 4,615 × 3,095 pixels at 600 dpi with LZW compression.
- Static validator: 14 pass, 0 warning, 0 failure.

## Ready-to-paste legend

**Figure 4c | Cross-database electrolyte knowledge improves candidate order
but not calibration.** **a,** Three conductivity programmes were fitted
separately and combined with equal programme weight. The complete
LiPF6/ethylene-carbonate/ethyl-methyl-carbonate target family was removed from
the BambooMixer arm; 71 near-identical BambooMixer–CALiSol records were
disclosed, and no source record matched the 180-row SolventSeg recipient.
**b,** Spearman candidate-order correlation after five labelled recipient
formulations. Points are means and bars are 2.5th–97.5th percentiles across
100 outcome-independent maximin anchor selections. The recipient oracle
selects the best of 13 recipient-only configurations separately in each draw
and is not deployable. **c,** Paired source-score advantages over the strongest
average recipient model, the per-draw recipient oracle, and the broad single
BambooMixer donor. **d,** Relative log-RMSE contrasts and the complete FINALES
multitask boundary route the source portfolio to retrospective ranking rather
than absolute prediction. Source data are provided in the repository result
tables.

