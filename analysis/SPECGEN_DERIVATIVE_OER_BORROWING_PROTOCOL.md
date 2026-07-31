# SpecGen derivative-system OER borrowing protocol

## Status and claim boundary

This protocol was frozen after the public article's aggregate transfer-learning
results and spot checks of the files were known, but before fitting the
donor-to-recipient performance models defined below. It is therefore a
retrospective, hypothesis-driven reanalysis, not a prospective or strictly
outcome-blind validation.

The experiment can establish that a relation learned in one experimental OER
system retains useful predictive or ranking information in a wholly held-out
derivative system. It cannot establish cross-laboratory transfer, prospective
laboratory discovery, or a general law of electrocatalysis.

## Scientific hypothesis

The transferable object is not the metal formula alone. It is the relation
between an experimentally measured spectrum, which reports the catalyst's
chemical microenvironment, and its OER overpotential. Transfer should be
selective: derivative systems that preserve this state-to-performance relation
should pass, whereas perturbations that change the relation should abstain or
fail.

## Data and OOD unit

- Donor: 462 Co-Ni-Cu-Mg-Cd-Zn catalysts with a terephthalic ligand.
- Recipients: four complete derivative systems, 126 catalysts each.
  - A: 2-aminoterephthalic ligand; same six metals.
  - B: 1,3,5-benzenetricarboxylic ligand; same six metals.
  - C: Fe replaces Mg; original ligand.
  - D: Mn replaces Cd; original ligand.
- Input state: 719-point UV-vis-NIR spectrum measured before the electrochemical
  outcome.
- Outcome: OER potential at 10 mA cm-2, converted to overpotential in mV.
- OOD split: the complete derivative system is excluded from donor training.
  Random row splits are not accepted as OOD evidence.

## Frozen models

### Donor model selection

Candidate source models are selected using donor-only five-fold cross-validation
by lowest mean absolute error:

1. partial least-squares regression with 2, 4, 8, 12 or 16 components;
2. ridge regression on source-standardized principal components retaining
   99.5% variance, with alpha 0.1, 1, 10 or 100.

No recipient outcome is used for source-model or hyperparameter selection.

### Transfer modes

1. **Static spectral relation:** apply the frozen donor spectral model directly
   to all recipient spectra.
2. **Anchored spectral relation:** with 3, 5, 10 or 20 recipient labels, correct
   the static donor prediction by a distance-weighted local model of donor
   residuals.
3. **Target-only matched baseline:** use the same target spectral distance
   representation and the same anchors, but interpolate target outcomes without
   the donor prediction.
4. **Composition-only donor:** fit a donor model to the six compositional slots;
   for C and D, the substituted metal occupies the corresponding fourth or
   fifth slot.
5. **Shuffled-source falsifier:** refit the selected donor model after permuting
   donor outcomes; use 500 fixed permutations.

All outcome-free spectral transformations may use the complete unlabeled
recipient spectrum matrix. No unlabelled recipient outcome may enter fitting.

## Estimands

Lower overpotential is better.

### Primary zero-label estimand

For every complete held-out recipient system:

- Spearman rank correlation between static donor predictions and outcomes;
- precision among the predicted best 10% of candidates;
- normalized simple regret after selecting the predicted best 10%.

The primary null distribution is the 500 shuffled-source models. Four recipient
systems are corrected by Holm's procedure.

### Primary five-label estimand

Across 200 fixed anchor draws per recipient:

- relative RMSE gain of anchored transfer over the target-only matched baseline;
- Spearman gain;
- best-10% precision gain;
- normalized regret reduction.

### Acceptance gate

A recipient edge is positive only if:

1. the donor has positive cross-validated absolute source skill;
2. zero-label Spearman exceeds 0.30 and the Holm-adjusted shuffled-source
   p-value is below 0.05;
3. at five labels, median relative RMSE gain is at least 5% and median Spearman
   gain is at least 0.10;
4. the 95% candidate-bootstrap interval for both gains excludes zero;
5. the absolute five-label borrowed Spearman exceeds 0.40.

If the zero-label ranking passes but the five-label prediction gate does not,
the edge is classified as **ranking-only**. If support is poor or the source
skill gate fails, the method must abstain.

## Interpretation

The four recipients are a built-in perturbation series, not four independent
laboratories. Concordance between transfer success and outcome-free spectral
support can support the proposed routing mechanism. It must not be counted as
four independent replications of cross-database transfer.
