# Focused optical-to-photocatalysis borrowing: verified findings

## Decision

The focused supervised strategy is **rejected for prediction transfer**. It
does not qualify for the unopened 96-molecule blind set and is not a positive
case for the main manuscript. Its proper role is a supplementary boundary
test showing that source-domain skill, a stronger molecular representation,
state-aware source subsets, nested cross-fitting, and a zero-correction option
are still insufficient when the donor representation is not predictive of the
recipient endpoint under scaffold shift.

## Test completed

Experimental optical measurements were used to train Chemprop directed
message-passing encoders for aqueous/small-alcohol, self-host solid, and
state-blind source scopes. The state-aligned source tasks were demonstrably
learnable under scaffold cross-validation: all five aqueous/small-alcohol
tasks and all three self-host solid tasks passed the frozen source-skill gate.
For example, source out-of-fold Spearman correlations were 0.867 and 0.842 for
aqueous absorption and emission maxima and 0.810 and 0.844 for their solid-state
counterparts.

The target analysis used 900 frozen, scaffold-separated development draws:
300 each at 30, 60, and 120 recipient labels. The primary method used
state-aligned source representations to fit a nested cross-fitted ridge
correction to a recipient-only hurdle model. State-blind, shuffled-label, and
scalar optical representations were matched controls. Sixteen draws contained
fewer than three unique labelled scaffolds; their donor corrections were forced
exactly to zero and the draws remained in all aggregate metrics.

## Primary result

At the frozen primary budget of 60 labels and in the dynamic hard-OOD 40%
scope:

| Method | Mean relative RMSE gain | Positive draws | Mean RMSE |
|---|---:|---:|---:|
| State-aligned pretrained residual | **-28.12%** | 74/300 (24.67%) | 0.8090 |
| State-blind pretrained residual | -15.40% | 65/300 (21.67%) | 0.7288 |
| Shuffled-source pretrained residual | -2.89% | 53/300 (17.67%) | 0.6415 |
| Scalar optical residual | -0.84% | 107/300 (35.67%) | 0.6272 |
| Recipient-only hurdle reference | 0% | -- | 0.6225 |

The state-aligned method was 25.23 percentage points worse than the shuffled
source and 12.72 percentage points worse than the state-blind source. It
selected a nonzero correction in 190/300 draws. Conditional on using a nonzero
correction, the mean relative RMSE gain was -44.40%, and only 74/190 draws
improved. Harm persisted at the other target-label budgets: -42.11% at 30
labels and -4.51% at 120 labels in the hard-OOD scope.

Only the mechanical requirement that a correction was sometimes selected
passed. The practical-gain, repeat-consistency, shuffled-source superiority,
state-alignment superiority, other-budget, and full-scope harm gates all
failed. The release decision was therefore `blind-release-denied`; no blind
outcome was opened.

## Interpretation

This result separates three propositions that should not be conflated:

1. The optical source endpoints are predictable.
2. The source and recipient share molecular structures and plausible
   photophysical relevance.
3. The learned source representation improves scaffold-OOD prediction of
   photocatalytic hydrogen evolution.

The first two propositions hold, but the third does not. Source cross-validation
therefore cannot qualify a donor by itself. The nested selector frequently
mistook within-labelled-scaffold residual structure for a portable correction,
and the resulting adjustment failed on unseen scaffolds. The likely scientific
gap is endpoint contract: hydrogen evolution depends on excited-state redox
driving force, charge separation, catalytic kinetics, formulation, and reaction
conditions that are not identified by generic absorption, emission, lifetime,
quantum-yield, and extinction-coefficient supervision alone.

The result does not show that photophysical knowledge can never help
photocatalysis. It shows that a database-level representation trained on these
optical endpoints is not a qualified predictive donor for this recipient
contract. A future positive test would require recipient-matched spectroscopy
or mechanistically signed excited-state descriptors measured under comparable
reaction conditions; that is a new-data experiment, not a defensible
reanalysis of the present edge.

## Verification

The Balam run independently verified 21 checkpoint hashes, 668 target
structures, 10,800 metric rows, 9,000 paired-contrast rows, all 16
insufficient-scaffold abstentions, and the final release decision. A complete
local run gave -28.07% primary gain and the same failed gate; the Balam value
was -28.12%, a 0.05-percentage-point platform difference with no decision
change. The authoritative artifacts are:

- `results/optical_supervised_source_VERIFIED.json`;
- `results/optical_supervised_borrowing_VERIFIED.json`;
- `results/optical_supervised_borrowing_summary.json`;
- `results/optical_supervised_borrowing_release.json`.

