# Post-primary amendment: composition-relation transfer

## Timing

The frozen spectral-transfer benchmark included a composition-only donor as a
specificity control. Its A, B and D recipient correlations were inspected before
the inference below was specified. This amendment is therefore explicitly
post-primary and exploratory. It cannot retroactively convert the composition
result into a confirmatory finding.

## Rationale

The control suggests that, when the endpoint, composition grid, experimental
programme and metal-slot substitution are aligned, the transferable relation
may be the low-dimensional composition-to-OER ranking rather than the full
spectrum-to-OER mapping. This is scientifically distinct from generic
composition-feature injection: the recipient is an entire derivative
experimental system and the changed metal occupies a declared homologous slot.

## Frozen secondary analysis

- Donor model: ExtraTrees regression with 500 trees, minimum leaf size 2 and
  all six composition slots available at each split.
- Donor source-skill check: shuffled five-fold cross-validated prediction on
  the 462 donor compositions.
- Zero-label falsifier: 500 source-outcome permutations, each refitting the same
  donor architecture, with Holm correction across A-D.
- Five-label transfer: predict with the donor composition relation and add a
  three-nearest-neighbour interpolation of donor residuals from five target
  anchors.
- Matched target-only baseline: use the same five anchors and the same
  composition distance, but interpolate the target outcomes directly.
- Metrics and acceptance thresholds are unchanged from the original derivative
  protocol.

The result may identify a method and an internal perturbation series suitable
for later external confirmation. Until such confirmation, it must be described
as a retrospective secondary finding within one published experimental
programme.
