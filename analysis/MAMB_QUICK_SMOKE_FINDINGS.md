# MAMB quick-smoke findings

## Status

This is an outcome-informed screening diagnostic, not confirmatory evidence.
It uses three target-training draws and three fixed learners on the same frozen
Q1/Q4 evaluation strata as the completed eight-target benchmark. There are no
confidence intervals, multiplicity adjustments, nested bundle selection, or
independent targets.

## Result

Simply replacing one donor prediction with a physically related multi-donor
bundle produced one clear escalation candidate:

- **Polymer tensile strength:** the predeclared bundle of Young's modulus,
  hardness, elongation and glass-transition temperature gave a mean Q4 RMSE
  reduction of **15.13%**, compared with **2.23%** for the single designated
  Young's-modulus donor. The bundle's mean Q4 gain exceeded its Q1 gain by
  **5.60 percentage points**, and mean Q4 R² became **+0.057** rather than
  remaining negative.

Several other bundles improved Q4 error without yet repairing absolute OOD
utility:

- thermoelectric factor bundle to zT: +3.81% Q4 gain, but larger Q1 gain and
  negative Q4 R²;
- mechanical bundle to alloy yield strength: +6.26% Q4 gain, but larger Q1
  gain and negative Q4 R²;
- thermoelectric transport bundle to electrolyte conductivity: +4.77% Q4
  gain with +0.91 percentage-point specificity, but strongly negative Q4 R².

Unfiltered five-donor stacking sometimes generated larger apparent gains,
including catalysis, but admitted distant controls and retained negative
absolute Q4 R². Those results are a warning against unconstrained feature
accumulation, not evidence of successful borrowing.

## Decision

The full MAMB run is justified, led by polymer tensile strength as the first
mechanism-bundle test. The next implementation must learn sparse nonnegative
weights inside grouped pseudo-OOD development folds, retain a target-only
fallback, and include wrong, shuffled and random experts. The formal run must
retain all eight targets and all null/harmful outcomes.

The corresponding protocol is
`analysis/MECHANISM_ALIGNED_MODULAR_BORROWING_PROTOCOL.md`.

