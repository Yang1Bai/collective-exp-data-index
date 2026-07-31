# Mechanism-aligned modular borrowing (MAMB)

## Purpose

The first multi-target benchmark rejected a generic implementation, not the
scientific premise of neighboring-domain borrowing. A single donor prediction
was appended to a recipient feature matrix for every edge, even when the
transferable object was a constitutive factor, a condition response, a
scale-free ranking, or a component of a hybrid material. The formal result is
therefore a useful design diagnosis: transfer must be matched to the mechanism
and endpoint before its OOD value is tested.

MAMB replaces universal feature injection with a small set of prespecified
borrowing contracts. Every target retains a target-only expert and can abstain
from all donors. Donor modules are frozen before recipient evaluation, and
recipient outcomes can only calibrate or gate them inside grouped development
folds.

This protocol was written after inspection of the formal multi-target outcome
and is method development. It cannot convert those eight targets into an
independent confirmation. A successful method must subsequently be frozen on
an outcome-unseen temporal, external, or prospective target.

## Evidence that motivated the redesign

1. The generic eight-target benchmark contained real signal but little
   OOD-specific repair. Examples include power factor to thermoelectric figure
   of merit and hardness or ultimate tensile strength to yield strength. These
   donors reduced Q4 error, but target-only Q4 R² often remained negative and
   the gain was not consistently larger than in Q1.
2. The KIT experiment showed that an endpoint-matched neighboring condition
   can improve absolute prediction: conductivity at −20 °C usefully informed
   conductivity at −30 °C.
3. The Caltech experiment showed that scale-robust donor rankings can remain
   useful even when target-refitted residual injection and OOD-weighted gates
   erase their signal.
4. Moon *et al.* combined two catalyst families only because the new target was
   a structural crossbreed of the source families. Separate surface and bulk
   encoders were trained with shared chemical co-descriptors, then activated
   together for the hybrid target. Their use of relative activity trends also
   shows that the prediction head must respect cross-dataset calibration
   limits.

## Borrowing contracts

Each directed edge receives exactly one primary contract before evaluation.
Edges without a defensible contract abstain.

| Contract | Scientific relation | Transfer object | Primary estimator | Examples in this project |
|---|---|---|---|---|
| Condition transport | Same endpoint under a neighboring temperature, time, concentration, or protocol | Calibrated response curve or residual | Hierarchical response surface with target-specific offset/slope | KIT −20→−30 °C; multistage battery stage 1→stage 2 |
| Constitutive bundle | Target is generated from or tightly constrained by several measured factors | Joint vector of frozen donor experts plus an explicit constitutive layer | Modular multi-donor model | power factor, conductivity and thermal transport→zT; strength and ductility properties→yield strength |
| Hybrid component | Target material combines components represented separately in source domains | Shared co-descriptor bottleneck plus separate component encoders | Crossbred modular encoder | surface/support or active-site/bulk combinations when the catalog supplies both components |
| Shared latent mechanism | Different endpoints share a plausible latent physical quantity but not an algebraic identity | Aligned shared representation plus domain-private residuals | Shared–private multi-task model | selected mechanical, ionic-transport, thermodynamic, or polymer-property families |
| Rank-only | Absolute scales are incompatible but relative order is reproducible | Cross-fitted rank or pairwise preference | Rank stack/portfolio with calibration abstention | Caltech external screening; cross-laboratory catalytic activity |

The contracts are not interchangeable. In particular, raw OOD distance is
never multiplied into a source score. The earlier local-gated Caltech
experiment showed that this heuristic can destroy a valid ranking.

## Model

For recipient input \(x\), source \(s\), and target \(t\):

\[
\hat y_t(x)=\hat y_{t,0}(x)+
\sum_{s \in {\cal A}_t} w_{t,s}(x)\,\Delta_{t,s}(x),
\]

where \(\hat y_{t,0}\) is the target-only expert, \(\Delta_{t,s}\) is a
cross-fitted and target-scale-calibrated donor correction, and
\(w_{t,s}(x)\ge 0\). The total donor allocation is at most one, leaving an
explicit target-only fallback weight. A donor may therefore help locally,
contribute globally, or abstain exactly.

### 1. Frozen donor modules

Each donor is trained under material-, article-, time-, or campaign-grouped
cross-validation. Exact recipient evaluation identities and shared provenance
groups are excluded. The exported module contains:

- a prediction or pairwise rank;
- a compact supervised latent representation rather than only one scalar;
- predictive uncertainty from grouped ensembles;
- its observed support in the shared co-descriptor space;
- a task and condition embedding.

### 2. Shared and private representations

Available descriptors are divided into:

- **shared co-descriptors**, physically interpretable variables available or
  computable in both domains;
- **domain-private descriptors**, retained in source- or target-specific
  branches;
- **context descriptors**, including temperature, synthesis, formulation,
  measurement protocol, and provenance when reported.

Co-descriptors are selected inside the outer development fold using stability
selection. A descriptor must be repeatedly associated with the endpoint in
both participating domains or be part of a declared constitutive relation.
Literature evidence may nominate a descriptor but cannot use evaluation
outcomes to retain it.

For formula-only tasks, the first implementation uses donor-supervised
projections of element and compact composition descriptors. A second
implementation can replace these projections with graph or composition
encoders. Molecule tasks use a separate molecular representation and are never
forced into the formula encoder.

### 3. Conditional sparse mixer

The gate receives source uncertainty, calibrated donor predictions, shared
latent coordinates, target-only uncertainty, and task/condition context. It is
a low-capacity softmax or sparse convex model, not a high-capacity neural
network. Its weights are learned only from grouped inner folds of recipient
development data.

The target-only expert is always included. Wrong-domain, shuffled-label, and
random-feature experts are present during development so that the gate must
learn zero allocation to invalid information. A donor is rejected if its
development-fold lower confidence bound is harmful.

### 4. OOD-specific development objective

Inner recipient groups are partitioned into pseudo-ID and pseudo-OOD folds
without using outcomes. Model selection minimizes:

\[
L =
L_{\mathrm{Q4}}+
\lambda_{\mathrm{tail}}\operatorname{CVaR}_{0.25}(e^2)+
\lambda_{\mathrm{rank}}L_{\mathrm{pairwise}}+
\lambda_{\mathrm{ID}}\max(0,L_{\mathrm{Q1}}-L_{\mathrm{Q1},0}-\epsilon)+
\lambda_{\mathrm{harm}}P_{\mathrm{wrong/shuffled}}.
\]

Thus the model is trained to reduce remote and worst-group error, preserve
rank when absolute scales are not transportable, avoid degrading ID behavior,
and suppress false donors. OOD distance defines folds and reporting strata;
it is not itself treated as evidence that a donor deserves more weight.

### 5. Representation-aware applicability

The original raw-feature distance quartiles remain the primary frozen test for
comparability with the completed benchmark. A sensitivity analysis estimates
target support from cross-fitted latent representations using k-nearest
neighbors or kernel density. Agreement and disagreement between raw and latent
OOD labels are both reported. No OOD definition is selected using evaluation
performance.

### 6. Uncertainty and abstention

Predictions are accompanied by grouped-ensemble or conformal intervals. The
method abstains to the target-only expert when:

- no donor clears its grouped development harm guard;
- the calibrated donor interval is wider than the target-only interval by a
  frozen margin;
- the candidate is unsupported in every admitted donor's co-descriptor space;
- rank-only transfer is requested for an absolute-value endpoint.

## First executable ablation

The existing eight targets and forty real edges are retained as a
method-development panel. No edge may be deleted because its previous result
was null or harmful.

1. Target-only baseline.
2. Best single scalar donor feature, reproducing the completed benchmark.
3. All-donor scalar stack.
4. Mechanism-bundled frozen donor modules with a global sparse convex mixer.
5. MAMB conditional sparse mixer.
6. MAMB without shared co-descriptors.
7. MAMB without the target-only fallback.
8. MAMB with average-error rather than pseudo-OOD/CVaR selection.
9. Shuffled, wrong-domain, and random-feature expert banks.
10. Rank-only head for targets with a prespecified calibration mismatch.

Primary endpoints remain Q4 relative RMSE gain, positive Q4 R²,
Q4-minus-Q1 specificity, wrong/shuffled separation, learner robustness, and
Holm-adjusted inference. Rank endpoints are secondary unless the borrowing
contract was frozen as rank-only.

The minimum portfolio-level success rule is:

- at least two independent programme clusters pass the complete OOD-repair
  gate;
- the programme-bootstrap mean Q4 gain has a positive lower interval;
- the method beats the best single-donor injection, not only target-only;
- harmful and shuffled experts receive negligible weight;
- at least one cross-database edge passes if a cross-database prediction claim
  is made.

## Compute plan

### Local smoke test

Run three grouped draws for the global sparse mixer, multi-donor stack, and
contract-specific rank head. This checks schemas, leakage exclusions, and
whether the donor bundles carry more information than the best scalar edge.

### Balam method-development run

Run 100 grouped draws for all eight targets, three learners, nested
pseudo-OOD tuning, 5,000 hierarchical bootstrap samples, and 9,999 sign flips.
GPU use is justified only for shared–private neural encoders; the initial
convex and tree-based ablation is CPU-bound.

### Independent confirmation

Freeze the winning contract, expert set, co-descriptors, gate capacity,
abstention rules, and analysis code before obtaining outcomes for a new
temporal, external, or prospective target. This is the experiment that can
upgrade the manuscript from method development to independently replicated
OOD knowledge borrowing.

## Expected scientific contribution

The optimized contribution is not that every neighboring database improves
every recipient. It is a transport rule for deciding **what** knowledge can
move, **how** it should be represented, **where** it should be allowed to act,
and **when** the system must abstain. That makes the knowledge-borrowing map an
operational collection of mechanism-labelled edges rather than a matrix of
undifferentiated correlations.

