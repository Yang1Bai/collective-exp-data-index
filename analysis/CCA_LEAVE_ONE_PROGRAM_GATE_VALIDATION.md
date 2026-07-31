# Leave-one-program borrowing-gate validation

## Decision

The outcome-informed credibility–compatibility–abstention (CCA) gate is a
useful safety screen but is not yet a validated benefit selector.  With each
complete target programme held out from gate fitting, it borrowed on 17 of 20
tasks spanning 11 of 13 programmes and obtained a mean programme-level relative
RMSE gain of 1.58% (programme bootstrap 95% CI, -0.23% to 4.27%).  Only one of
17 admitted decisions selected an edge whose complete reported interval was
harmful, but the gate retained only four of ten tasks for which at least one
clearly beneficial edge existed.  It did not pass either frozen superiority
contrast after Holm correction.

This is method-development evidence.  The edge outcomes, candidate features,
and CCA concept were already known when this benchmark was designed.  Leaving a
programme out prevents direct outcome leakage from that programme into its
prediction, but it does not convert the exercise into independent replication
or prospective validation.

## Frozen design and independent unit

The design is recorded in `cca_leave_one_program_gate_design.json`.  The panel
contains 97 directed source-target edges, 20 target tasks, and 13 independent
programme clusters.  Tasks sharing a dataset or campaign remain in one cluster;
the four TRI OER plates are not treated as four independent scientific
replications.  Each training programme has total weight one.  The held-out
programme contributes no edge outcome to its gate fit.

The gate used only outcome-free edge descriptors: physical-neighborhood score,
grouped source out-of-fold R2, positive source credibility, same-domain and
condition adjacency, cross-dataset status, and wrong/distant/shuffled flags.
An eligible source required positive source OOF R2, strong adjacency, and no
wrong, distant, or shuffled designation.  Weighted ridge regression estimated
the expected relative RMSE gain from the other programmes.  The policy admitted
only eligible edges with positive held-out predictions and selected the
highest predicted edge per task; otherwise it abstained.

Programme-level uncertainty used 10,000 cluster bootstrap resamples.  Exactly
two one-sided, paired programme-level sign-flip tests were prespecified and
Holm-corrected: CCA versus always selecting the most credible source, and CCA
versus never borrowing.  A 20% programme-coverage guard prevented trivial
abstention from being labelled safe.

## Results

| Policy | Mean programme utility | 95% cluster-bootstrap CI | Programme coverage | Clearly harmful selections | Clear benefits retained |
|---|---:|---:|---:|---:|---:|
| CCA meta-gate | +1.58% | -0.23% to +4.27% | 11/13 | 1/17 admitted | 4/10 available |
| Fixed CCA rule | +1.60% | -0.21% to +4.34% | 11/13 | 1/17 admitted | 4/10 available |
| Adjacency only | +1.80% | -0.19% to +4.52% | 13/13 | 1/20 admitted | 5/10 available |
| Best source credibility | +0.16% | -0.49% to +0.93% | 13/13 | 2/20 admitted | 3/10 available |
| Never borrow | 0 | 0 to 0 | 0/13 | 0 | 0/10 |
| Oracle, descriptive only | +2.93% | +1.11% to +5.41% | 12/13 | 0/19 admitted | 9/10 available |

CCA exceeded the best-credibility policy by 1.42 percentage points, but the
95% interval crossed zero (-0.23 to +4.08 percentage points; one-sided sign-
flip p=0.135, Holm p=0.270).  Its +1.58-point contrast with never borrowing
also crossed zero (-0.23 to +4.29; p=0.162, Holm p=0.270).  The nontrivial
coverage guard passed; the frozen superiority family did not.

The close agreement between the fitted meta-gate and the fixed CCA rule is
diagnostic.  The ridge layer contributed almost no useful discrimination beyond
the eligibility rule.  Adjacency alone was numerically stronger and retained
one more clearly beneficial task.  Global source OOF skill was especially weak
as a benefit-ranking variable: the best-credibility policy selected two clearly
harmful edges, while several beneficial sources were excluded because their
global source fit was non-positive.

## Failure anatomy

The errors divide into three actionable classes.

1. **Within-neighborhood ranking failure.**  For BIRDSHOT hardness, both alloy
   sources passed eligibility; CCA selected alloy YS (-5.14%, clearly harmful)
   instead of alloy UTS (+6.84%, clearly beneficial).  For polymer melting
   temperature it selected polymer Tg (-0.71%) instead of the admitted
   crystallization source (+0.34%, clearly beneficial).  Coarse edge metadata
   cannot distinguish two sources that share the same nominal neighborhood.
2. **Global-credibility false exclusion.**  The clearly beneficial
   polymer-Young's-modulus to tensile-strength edge (+1.38%) and the
   photoswitch Z-n-pi-star to Z-pi-pi-star edge (+0.66%) were excluded by the
   positive global source-skill requirement.  Global predictability is not the
   same estimand as local transferable information.
3. **Small nulls accepted as positives.**  Several physically adjacent TRI,
   aqueous, thermoelectric, and polymer edges were admitted but had small
   negative point estimates.  Most were not clearly harmful, explaining the
   gap between the 59% point-harm rate and the 6% clear-harm rate.  An admission
   rule therefore needs calibrated uncertainty and a practical dead zone, not
   only a sign prediction.

## Scientific interpretation

The cross-program result strengthens the selective-map thesis in a precise
way.  Physical adjacency contains useful first-order information: it materially
outperforms indiscriminate global source credibility in point estimates and
preserves several real benefits.  However, adjacency and global source skill
do not identify *where within a neighboring relation* borrowing is useful.
The present CCA features support contraindication screening, not benefit
ranking.  This is why the knowledge-borrowing map must be local, directional,
and endpoint-specific.

The result does not invalidate neighborhood knowledge transfer.  It rejects a
specific shortcut: learning one scalar edge score from global domain metadata.
The remaining oracle gap (+2.93% versus +1.58%) and the two explicit
within-neighborhood reversals show where improvement is available.  The missing
information is candidate-local source support, target novelty, endpoint
compatibility, and disagreement among qualified sources.

## Next method, frozen after this result

The next policy separates safety from benefit selection rather than asking one
regression to do both:

1. a **contraindication gate** removes identity/provenance leakage and sources
   defeated by matched wrong or shuffled controls;
2. a **local applicability model** estimates source support and uncertainty at
   each candidate from outcome-free composition/condition geometry;
3. an **endpoint-specific proposal layer** uses a shrinkable soft prior for
   few-shot prediction but preserves independent source ranks for screening;
4. a **portfolio allocator** rewards cross-source agreement and complementary
   regions while retaining novelty/random fallbacks; and
5. an **abstention margin** requires predicted utility to exceed calibrated
   uncertainty and a practical dead zone.

This version must be evaluated on a genuinely new temporal or prospective
programme.  The current 13 programmes can develop features and falsify design
choices, but cannot provide the confirming result after this failure anatomy
has been observed.

## Reproducibility

- Runner: `run_cca_leave_one_program_gate.py`
- Independent verifier: `verify_cca_leave_one_program_gate.py`
- Verification record: `results/cca_leave_one_program_VERIFIED.json`
- Policy summary: `results/cca_leave_one_program_policy_summary.csv`
- Primary contrasts: `results/cca_leave_one_program_contrasts.csv`
- Complete edge predictions: `results/cca_leave_one_program_predictions.csv`

