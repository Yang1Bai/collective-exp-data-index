# Phase 2 findings: cross-domain knowledge transfer (data-poor target)

**Question.** Can a data-poor domain borrow knowledge from adjacent domains?
Target: OBELiX solid-electrolyte ionic conductivity (518 compositions, log10 S/cm).
Method: stacked feature injection — a source-domain RF's prediction on the target
composition becomes one extra feature; few-shot learning curves, 8 random splits,
baseline = element-fraction features only. Script: `transfer_matrix.py`.

## Results (ΔR² vs baseline, mean ± SE)

| n target samples | + thermoelectric ZT (ESTM) | + electrocatalysis fe_H2 (OCx24) | baseline R² |
|---|---|---|---|
| 30  | **+0.155 ± 0.033** | −0.001 ± 0.002 | 0.003 |
| 60  | **+0.099 ± 0.013** | 0.000 ± 0.002 | 0.206 |
| 120 | **+0.081 ± 0.015** | +0.002 ± 0.001 | 0.423 |
| 240 | **+0.099 ± 0.022** | 0.000 ± 0.001 | 0.516 |

## Conclusion

**Yes — and selectively.** In the severely data-poor regime (n=30, where a
target-only model has zero skill, R²≈0.00), injecting thermoelectric-domain
knowledge yields a working model (R²≈0.16), and the benefit persists (+0.08
to +0.10 R²) even at n=240. Electrocatalysis knowledge transfers nothing —
a built-in negative control showing the effect is not an artifact of adding
features. The transfer is physically sensible: thermoelectrics and solid
electrolytes share activated-transport physics and chalcogenide/Li chemistry,
while catalytic faradaic efficiency does not probe bulk ion transport.

**Corollary for the program:** domain adjacency is measurable, asymmetric-in-
principle, and exploitable — the full pairwise transfer matrix over the data
lake is a "knowledge-borrowing map" telling any under-reported field which
neighbor to learn from. This is also the direct justification for cross-domain
priors in self-driving-lab campaign design (Phase 3).

## Limitations

One target domain so far; RF + composition features only (no structure);
MPEA source skipped (property column name mismatch — fix and rerun); transfer
mechanism (shared chemistry vs shared physics) not yet disentangled — family-
ablation is the natural next experiment.
