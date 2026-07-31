# MPEA provenance and donor-specificity strengthening protocol

## Purpose

This review-triggered analysis asks why neighboring experimental knowledge
helped the yield-strength task and whether the result survives stronger
provenance controls. It is a frozen sensitivity and mechanism analysis, not a
new prospective confirmation.

The target endpoint is experimental yield strength. The primary donor endpoint
is ultimate tensile strength. Both are modeled in log10(MPa). The evaluation
set is the same chemically held-out set used in the existing MPEA robustness
run so that the original result is not replaced by a more favorable split.

## Fixed evaluation and OOD definition

- Unordered elemental systems are assigned intact to development and
  evaluation with the existing seed and 60:20:20 partition.
- Discovery and confirmation partitions are combined only for retrospective
  evaluation.
- For each labeled target-training draw, evaluation systems are divided into
  quartiles by median nearest-neighbor composition distance. Q4 is the most
  compositionally distant quarter.
- The independent inferential unit is the unordered elemental system. Model
  seeds and learners are fixed algorithmic repetitions, not biological or
  experimental replicates.

## Analysis A: nested provenance ladder

The same ultimate-tensile-strength donor and state-aware model are evaluated
under three nested information boundaries:

1. **System-disjoint:** evaluation elemental systems are excluded from donor
   training, reproducing the original boundary.
2. **Donor DOI-disjoint:** the above restriction plus exclusion of every donor
   record from a publication DOI represented in evaluation.
3. **Full DOI-disjoint:** donor DOI exclusion plus removal of target-development
   records from evaluation DOIs. During cross-fitting, the donor also excludes
   the elemental systems and publication DOIs represented in the held target
   fold.

The evaluation systems and outcomes remain fixed. Any attenuation therefore
quantifies sensitivity to shared publication provenance rather than a change
in the test target.

## Analysis B: donor specificity

Under the strict full DOI-disjoint boundary, three experimentally measured
mechanical donors are compared:

- ultimate tensile strength;
- Vickers hardness;
- elongation at failure.

Each donor is deterministically limited to the same number of eligible source
records as the ultimate-tensile-strength donor. Every real donor has an
architecture-matched outcome-shuffled control. The primary question is not
whether the chosen donor beats an artificially weakened baseline, but whether
its gain is source-specific and whether it exceeds other plausible,
information-matched mechanical donors.

Additional yield-strength observations are not treated as a donor. They enter
only a target-only learning curve because same-endpoint labels are directly
usable target evidence, not transferred knowledge.

## Analysis C: state dependence

Under the strict boundary and with the ultimate-tensile-strength donor, the
following contracts are compared:

- composition only;
- full planned experimental state;
- no processing or phase descriptors;
- no test type or test temperature;
- no calculated density.

The same feature contract is applied to the donor and target models. This
tests whether the transferred signal requires experimental-state alignment or
is merely a composition proxy.

## Analysis D: target-label equivalence

Target-only models are trained at 30, 60, 120 and 240 labeled records under the
strict split. Their OOD error is compared with the 60-label transferred model.
If the learning curve crosses that error, log-budget interpolation reports the
approximate number of additional target labels needed to match borrowing.

## Frozen computation and reporting

- Thirty grouped label draws.
- Random-forest and extra-trees target learners.
- Extra-trees donor model.
- 320 trees per ensemble.
- 100,000 elemental-system cluster-bootstrap replicates.
- 100,000 elemental-system sign-flip draws for primary loss contrasts.
- Four primary one-sided contrasts are Holm-adjusted: ultimate-tensile-strength
  transfer versus target-only, versus its shuffled donor, versus hardness, and
  versus elongation.
- Report effect sizes and confidence intervals even when a threshold is not
  crossed. No failed donor, provenance level or state ablation may be removed.

## Claim guard

A robust positive result can show that a particular neighboring mechanical
endpoint contributes transferable information after chemical-system and
publication separation. It cannot prove universal transfer, prospective
laboratory discovery, or a mechanism of strengthening. Attenuation under
stricter provenance is itself a result and must be disclosed.
