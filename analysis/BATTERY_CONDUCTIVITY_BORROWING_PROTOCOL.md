# Conductivity-to-Battery OOD Borrowing Protocol

## Scientific question

Can experimentally reported conductivity knowledge repair prediction in
chemically and bibliographically out-of-distribution battery capacity records,
when the recipient evidence is deliberately sparse?

The mechanistic hypothesis is deliberately narrow. Conductivity may constrain
rate-limited charge transport, so the primary recipient endpoint is
rate-conditioned gravimetric capacity. The protocol does not treat
conductivity as a generic predictor of cycle life, stability, or overall
battery quality.

## Data source and frozen boundary

The source and recipient records are taken from Battery Materials Property
Database v2.0 (Figshare article 18154715, file `battery-v2.zip`, file id
34496339). The archive contains literature-mined experimental records for
capacity, conductivity, voltage, Coulombic efficiency, and energy.

The design in `battery_conductivity_borrowing_design.json` was frozen before
the archive payload was opened. The first executable stage is outcome-blind:
it may inspect file names, schemas, material identities, property labels,
units, conditions, publication identifiers, and missingness, but it must not
read or summarize numeric property values.

The outcome-blind audit is a binding go/no-go gate. If rate, cycle, material,
or publication provenance is too incomplete to define the frozen endpoint and
OOD groups, no model will be fit and the edge will be recorded as abstaining.

## Directional donor and recipient roles

- **Donor:** experimental conductivity records.
- **Recipient:** gravimetric capacity records with an explicit current-rate
  condition and an explicit or bounded early-cycle condition.
- **Secondary recipient:** Coulombic efficiency under similarly explicit
  operating conditions, evaluated only after the capacity analysis is locked.
- **Wrong-property controls:** voltage and energy records transformed through
  the same source-training pipeline.

The donor is allowed to improve a recipient sample only through a conductivity
card predicted from material identity and declared experimental state. Raw
conductivity values are never joined directly to recipient outcomes.

## Leakage boundary

Publication identifiers are the primary provenance groups.

1. No recipient evaluation publication may enter recipient training.
2. No recipient evaluation publication may enter the donor model used to make
   its conductivity card.
3. Every source prediction used on a labelled recipient record must be
   generated out of fold with respect to publication.
4. Exact material overlap across independent publications is retained in the
   practical borrowing analysis and disclosed.
5. A stricter material-excluded donor card is evaluated as a mechanism
   diagnostic; it is not substituted for the frozen primary result.
6. Titles, authors, journals, citation counts, and target property values are
   forbidden model features.

## OOD construction

Two independent shifts are required:

1. **Publication OOD:** a deterministic external set of publication groups is
   never labelled during recipient training.
2. **Chemical OOD:** within the publication-external set, the primary scope is
   the lowest-supported 40% of recipient materials relative to the labelled
   recipient materials, subject to nonzero donor support.

The primary benchmark uses sparse recipient label budgets of 60, 120, and 240
publication-material groups. Results are paired across methods using identical
draws and seeds.

## Borrowing methods

The recipient baseline uses material identity plus available current-rate,
cycle, temperature, and unit/state indicators. The real borrowed card contains
the conductivity donor ensemble mean, ensemble dispersion, donor-support
score, and missingness indicators.

The following matched methods are mandatory:

1. recipient-only;
2. recipient plus real conductivity card;
3. recipient plus publication-wise shuffled conductivity card;
4. recipient plus wrong-property voltage card;
5. recipient plus wrong-property energy card;
6. recipient plus equal-dimensional Gaussian card.

Prediction and exploration are separated. Feature injection is the primary
prediction test. An independent conductivity ranking is a secondary
candidate-prior test and cannot rescue a failed prediction gate.

## Primary estimand and success gate

The primary estimand is paired relative reduction in RMSE on the
conductivity-supported, chemically hard publication-OOD scope at the
120-group label budget.

A positive edge requires all of the following:

- mean RMSE reduction of at least 5%;
- publication-cluster bootstrap 95% interval entirely above zero;
- Holm-adjusted `p < 0.05` over the frozen primary contrast family;
- absolute recipient `R² > 0`;
- at least 3 percentage points better than shuffled conductivity;
- better than both wrong-property controls;
- at least 65% of paired repeats positive;
- no more than 1% mean harm on the full publication-OOD scope.

Failure of any item is a null, harmful, or abstaining edge, not a cue to change
the endpoint, OOD definition, or preferred method.

## Claim guard

A positive result would establish one retrospective, rate-conditioned
conductivity-to-capacity borrowing edge inside a literature-mined experimental
battery corpus. It would not establish universal battery transfer,
prospective laboratory discovery, improvement in cycle life, or automatic
validity of text-mined relations. Independent database confirmation would
still be required for the strongest manuscript claim.

