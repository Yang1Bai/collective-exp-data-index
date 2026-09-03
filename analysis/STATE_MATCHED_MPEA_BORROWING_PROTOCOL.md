# State-matched neighboring-endpoint borrowing

## Purpose

The aggregate composition-only benchmark showed that merely injecting a donor
prediction does not reliably repair out-of-distribution (OOD) error.  The raw
MPEA table, however, retains the experimental state that the unified table
discarded: processing route, phase family, test mode, test temperature,
microstructure and density.  This experiment asks whether UTS knowledge becomes
transferable to yield strength (YS) after the deployment state and the physical
relationship between the two endpoints are respected.

## Frozen robustness candidate

The post-selection candidate is fixed to:

1. composition plus planned-state covariates;
2. an ExtraTrees UTS donor trained without any evaluation elemental system;
3. system-cross-fitted donor predictions on target-training rows;
4. concatenation of the predicted UTS with the state-aware target features;
5. RandomForest and ExtraTrees target learners at a budget of 60 YS labels.

The residual-anchor alternative is retained as a disclosed failed development
candidate.  It cannot replace the frozen concatenation method after outcomes are
seen.

## Leakage boundary

The split unit is the unordered elemental system, not a row or exact formula.
No elemental system crosses target development and evaluation.  When producing
the UTS feature for a held target-training fold, the donor model excludes every
system in that fold and every evaluation system.  The final donor model excludes
all evaluation systems.  A shuffled-UTS donor is rebuilt inside every fold.
Under the V2 control correction, its prediction enters the identical feature-
concatenation target architecture, learner seed, label draw and evaluation rows
as the real donor. The earlier residual-anchor shuffled comparison is retained
for audit but is not used for source-specific inference.

## Evidence hierarchy

- **Primary robustness contrast:** state-aware target-only versus state-aware
  target plus cross-fitted predicted UTS in Q4.
- **Specificity:** Q4 gain must exceed Q1 gain.
- **Negative control:** the real donor must beat shuffled UTS.
- **Absolute utility:** augmented Q4 R² must be positive.
- **Auxiliary ceiling:** paired measured UTS is evaluated separately and is not
  called model transfer.

The run contains 30 target-label draws and two frozen tree learners.  The
primary interval is a frozen two-way cluster bootstrap with 100,000 replicates:
it resamples elemental systems and model-by-draw runs independently, preserving
all row-level errors within a system.

## Claim boundary

The method was selected after inspecting MPEA outcomes.  Therefore this run can
demonstrate stability on this experimental program and quantify how much of the
measured-UTS ceiling is recovered.  It cannot be described as independent,
prospective or universally general.  Independent confirmation requires a new
mechanical-property program with processing and test-state metadata.
