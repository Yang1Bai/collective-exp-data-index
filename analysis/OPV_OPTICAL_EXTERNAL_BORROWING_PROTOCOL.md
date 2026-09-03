# Outcome-frozen optical-to-organic-photovoltaic borrowing protocol

## Question

Can experimental optical knowledge learned from a separate spectroscopy
database improve prediction of organic photovoltaic devices in regions that
are simultaneously data-poor, publication-disjoint and molecularly OOD?

The proposed edge is not “optics is related to photovoltaics.” It is a
directional and falsifiable contract:

> an independently learned optical property card for both the electron donor
> and electron acceptor supplies information about light harvesting and
> excited-state energetics that is missing from a small OPV-labelled set.

## Why this is a stronger target

The recipient is the CC-BY OPV-DB strict molecular benchmark, not another
random split of the 350-molecule HOPV15 collection. Its release metadata
declares 21,720 internally consistent single-junction device records, 5,459
source DOIs and 5,094 reported donor-acceptor pairs. The outcome-free local
audit retained 21,720 parseable donor/acceptor structure pairs and placed
4,012 records from 1,044 entire DOIs into an immutable external partition.

Only package documentation, data definitions, aggregate release summaries,
identity, molecular structure, provenance and device-state columns were
inspected before this protocol was frozen. Row-level PCE, Voc, Jsc and FF
values remained unread.

## Donor qualification and leakage boundary

Deep4Chem is the external spectroscopy source. The audit found four exact
target molecules in the global source and no target DOI overlap. The strict
source model nevertheless removes **every** target donor and acceptor
molecule, including those not present in the source, and every target DOI
before training. The resulting model is therefore a source-domain
generalization model, not a cross-database lookup.

The primary source scope consists of records in which the chromophore is its
own solid-state host. The global source is a state-alignment ablation.
Absorption maximum, emission maximum, lifetime, quantum yield and extinction
coefficient must each pass source-only grouped OOF skill before entering the
borrowed card. Matched source-label-permuted models retain the same structures,
architecture, task masks and training effort.

## Recipient unit, state and OOD definition

One recipient observation is one reported OPV device. A target-only model
receives donor and acceptor molecular fingerprints plus available device
state: blend ratio, additive, device architecture, transport layers, active
layer thickness, solvent and annealing temperature. Missing state is explicit.
The target database’s HOMO, LUMO and gap annotations are forbidden in the
primary analysis because they are target-side reference properties rather than
independent borrowed knowledge.

Development and external records are separated by normalized DOI hash, with
all records from one publication kept together. At each of 200 deterministic
repeats, 60, 120 or 240 unique development DOI-pair units are labelled. The
primary external scope contains source-qualified devices for which both
molecules have at least 0.20 solid-source support, restricted to the 40% least
similar to labelled donor and acceptor molecules. This scope is outcome-free
and cannot move after the result is read.

## Borrowing methods and controls

For donor and acceptor separately, the source ensemble produces the mean and
standard deviation of every admitted optical endpoint. Role-matched
differences, absolute differences and products form a compact device-level
optical card. The primary comparison appends this card to the complete
state-aware target model.

Required controls are:

1. molecular structure only;
2. state-aware target only;
3. target-excluded solid optical card;
4. source-label-shuffled solid optical card;
5. state-blind global optical card;
6. row-permuted real optical card;
7. equal-dimensional Gaussian features.

The same target draws, learner seeds and evaluation records are used for every
method. PCE is fitted directly for the primary analysis. Voc, Jsc and FF are
mechanistic diagnostics; a physically recombined PCE is secondary.

## Acceptance rule

At 120 target labels and in the frozen qualified hard-OOD scope, the real
solid-state optical card must:

- reduce PCE RMSE by at least 3% relative to the state-aware target model;
- have a DOI-cluster bootstrap 95% interval entirely above zero;
- retain Holm-adjusted \(P<0.05\);
- achieve positive absolute PCE \(R^2\);
- exceed the shuffled-source card by at least two percentage points;
- exceed the row-permuted real card;
- produce non-negative mean Jsc improvement;
- improve at least 65% of the 200 target-label repeats; and
- cause no more than 1% PCE RMSE harm in the full external DOI partition.

Failure of any condition keeps the edge null or harmful. A favorable secondary
endpoint cannot replace the primary result.

## Claim boundary

A passing result would show that carefully qualified experimental
spectroscopy can repair a data-poor OPV model outside its labelled molecular
and publication neighbourhood. It would not establish prospective device
discovery or universal optical transfer. A failure would be retained beside
the optical-to-photocatalysis failure and would sharpen the boundary between
mechanistic adjacency and thematic similarity.
