# Focused supervised optical borrowing protocol

## Question

Can experimental optical measurements from a neighboring molecular domain
repair prediction for chemically distant, data-poor molecular
photocatalysis, after the original scalar feature-injection strategy failed?

## Frozen strategy

The fixed source architecture is a Chemprop v2.1.2 directed bond
message-passing neural network. It is trained only on experimental optical
outcomes after removing every recipient molecule. Separate encoders learn from
water/small-alcohol records and molecular-solid records. Their latent
representations are never trained on recipient outcomes.

For each target-label draw, a recipient-only hurdle model first predicts
whether hydrogen evolution is nonzero and then its positive magnitude. The
source representation may only correct out-of-fold residuals from this
target-only model. The correction is scaled by source chemical support and its
weight is chosen by inner scaffold-group validation from a grid that includes
zero. Thus, unsupported or harmful borrowing can reduce exactly to the
recipient-only model.

## Necessary comparisons

The primary state-aligned encoder is compared with:

- the optimized recipient-only hurdle model;
- an otherwise identical encoder trained without experimental-state
  separation;
- the same state-aligned architecture trained after shuffling source optical
  labels;
- the previously tested scalar optical predictions.

The shuffled-label control is decisive: it retains molecular inputs,
architecture, optimization and dimensionality while removing the external
experimental knowledge claimed to be borrowed.

## OOD evaluation

The experiment reuses the previously frozen 300 outcome-independent,
scaffold-separated draws at each target-label budget of 30, 60 and 120. Within
every draw, the primary evaluation scope is the 40% of eligible molecules
farthest from the labeled target set by Morgan-fingerprint Tanimoto
similarity. The full scaffold-separated evaluation pool is secondary.

Development draws and neural-network seeds are computational sensitivity
replicates, not independent experimental samples. Development p values will
not be reported as confirmatory inference.

## Release rule

At 60 labels, the primary method must reduce mean hard-OOD RMSE by at least 3%,
be positive in at least 65% of draws, exceed the shuffled-source control by at
least two percentage points, and not underperform the state-blind encoder. It
must remain non-harmful in hard OOD at 30 and 120 labels and cause less than 1%
mean harm in the full evaluation scope at every budget. At least half of
primary-budget draws must select a nonzero donor correction; otherwise an
apparent gain is classified as target-model improvement rather than borrowing.

Only if every condition passes may one fully specified model be hashed and
released to the still-unopened 96-molecule blind set. Otherwise the programme
abstains and the optical-to-photocatalysis edge remains null.

## Evidential limit

This stage is explicitly post-gate method development. A later blind pass would
support one retrospective optical-to-photocatalysis borrowing edge. It would
not erase the failed scalar-injection result, establish universal transfer, or
demonstrate prospective laboratory discovery.
