# Internally frozen specification for auditing candidate borrowing edges

> **Protocol provenance.** This author-controlled document was internally
> frozen before the multi-target
> map and BIRDSHOT confirmation were run. Statements below that use “present”
> or “current” describe the pre-map state and are retained to avoid rewriting
> the protocol after seeing outcomes. It was not publicly preregistered. The
> dated outcome annotation at the end is reporting, not a change to the
> admission rules.

## Fixed scientific thesis

When scientific understanding is incomplete, a single domain-wide law should
not be expected to emerge automatically from heterogeneous aggregated data.
Nevertheless, knowledge transfer may be directional, local, and selective: a
source task can materially reduce the amount of target-domain data needed in a
bounded setting. The intended contribution is therefore a **candidate-edge
audit** plus an **artifact-rejection protocol**, not a grand-unified theory.

At the time of this freeze, the corrected benchmark established the artifact-
rejection protocol but did **not yet establish a positive predictive map**: the
original ESTM-to-OBELiX edge was model-dependent and failed the designated
primary test. The experiments below were defined as the minimum evidence needed
to complete the thesis without restoring that false positive.

## Terminology ledger

| Canonical term | Operational meaning | Terms not to substitute |
|---|---|---|
| task | one dataset--property prediction problem with a defined population and evaluation split | field, discipline |
| neighborhood | a source--target relation declared from chemistry, mechanism, conditions, or representation before transfer outcomes are inspected | intuitive adjacency |
| knowledge borrowing | improvement obtained from information learned only from the source task and added to a fixed target learner | universal transfer |
| directed edge | a source-to-target effect estimated at a specified target-data budget | correlation |
| confirmed edge | a directed edge that passes effect-size, uncertainty, multiplicity, leakage, robustness, and independent-replication gates | significant edge |
| rescue | a prespecified practically meaningful reduction in target data needed to reach a fixed predictive utility | any positive ΔR² |
| knowledge-borrowing map | the set of confirmed, null/equivalent, harmful, and unresolved directed edges, each with uncertainty and scope | 9×9 heatmap |

## One-sentence paper argument

Across heterogeneous experimental materials tasks, we test whether global
regularities survive family-aware validation and whether predeclared local
source--target neighborhoods reduce target sample requirements; the final claim
requires **[evidence needed: independently replicated positive edges plus
confirmed null or harmful edges]**, while entity resolution, provenance-aware
splitting, artifact diagnostics, and multiplicity control define where the map
is trustworthy.

## What makes a map operational

The map is a directed graph, not a matrix of point estimates.

- **Node:** a task defined by dataset, target property, population, conditions,
  representation, and train/test regime.
- **Candidate edge:** source task → target task, evaluated at target budgets such
  as n=20, 30, and 50 intact provenance groups.
- **Primary edge weight:** target-equivalent samples saved. From the target-only
  learning curve, estimate how many target observations are required to match
  the source-augmented model's held-out error at the fixed budget.
- **Secondary weights:** held-out relative RMSE change and ΔR², with
  cluster-aware confidence intervals.
- **Edge metadata:** canonical-overlap count, neighborhood features, source
  model quality, model sensitivity, target population, and confirmation status.

An edge is useful only if it answers an experimental planning question: *which
source should be borrowed from, for which target, at what data budget, and how
many target measurements might it replace?*

## Neighborhood must be declared without seeing transfer outcomes

Each candidate pair receives a pre-outcome neighborhood vector. At minimum it
should include:

1. composition-distribution proximity, using a fixed divergence on elemental
   fractions rather than exact formula overlap;
2. property/mechanism proximity from a frozen ontology or expert rubric;
3. state and measurement-condition compatibility;
4. representation support, including elements or molecular motifs outside the
   source domain;
5. source model reliability under source-group cross-validation.

The physical-neighborhood rubric and thresholds must be frozen before the
confirmatory transfer run. A neighborhood inferred from the observed transfer
matrix would be circular.

## Discovery and confirmation design

### Stage 0: lock the protocol

- Freeze target endpoints, grouping keys, target budgets, primary learner,
  hyperparameters, neighborhood rubric, practical-effect threshold, and
  multiplicity family in a time-stamped release.
- Preserve canonical identity and provenance groups before any split.
- Audit exact and scale-equivalent source--target overlap.

### Stage 1: map discovery

- Use at least four data-poor target tasks spanning at least three material or
  chemistry domains; OBELiX may be one target but cannot be the only target.
- Evaluate all declared source--target pairs with at least 100 grouped target
  resamples per budget.
- Use one designated target learner for inference and at least two structurally
  different learners for sensitivity.
- Include shuffled-source, random-feature, target-only, and same-domain positive
  controls.
- Keep target test groups fixed and untouched by source selection or tuning.

Discovery results classify edges as candidates, not confirmed findings.

### Stage 2: independent edge confirmation

- Confirm the most important positive edge on a second dataset, later temporal
  tranche, or prospectively held-out target population that was not used to
  choose the source, representation, learner, or budget.
- Re-run the full canonical-overlap and provenance-group audit.
- Test the predeclared directional hypothesis with family-wise error control.
- Report all attempted confirmations, including failed edges.

### Stage 3: test selectivity rather than count significant cells

Selective transfer requires more than a mixture of small and large p-values.
Test whether edge effects vary beyond sampling error and whether the frozen
neighborhood score predicts out-of-sample transfer benefit. A hierarchical
edge model or meta-regression should estimate:

- between-edge heterogeneity;
- the neighborhood-score slope and uncertainty;
- residual source and target effects;
- prediction intervals for a new edge.

The knowledge-borrowing map is supported only if neighborhood information
predicts transfer on held-out edges or targets. Otherwise the map remains a
descriptive benchmark.

## Confirmed-edge gate

A directed edge is **confirmed positive** only when all conditions hold:

1. its prespecified primary held-out error improves after multiplicity
   correction;
2. the cluster-aware confidence interval excludes zero in the beneficial
   direction;
3. the effect exceeds the frozen practical threshold, proposed as at least 5%
   relative RMSE reduction or at least 30% target-equivalent samples saved;
4. the direction survives at least two of three target learners, with no large
   contradictory degradation;
5. exact and canonical source--target overlap is absent or removed before
   fitting;
6. shuffled-source and random-feature placebos do not reproduce the gain;
7. the edge replicates on an independent target population.

Other statuses are equally important:

- **equivalent/null:** the entire interval lies within the practical
  equivalence region;
- **harmful:** the corrected interval lies in the adverse direction;
- **suggestive:** positive discovery result without independent replication;
- **unresolved:** interval spans both meaningful benefit and harm.

The current ESTM-to-OBELiX predictive result is **unresolved/model-dependent**.
Its later fixed-ranking OOD screen is **directional only**, and its sequential
design, prespecified after that ranking direction was known, fails every
improvement gate. These are
retained as endpoint-specific map annotations, not as a confirmed positive
edge.

## Decision-endpoint extension

Every candidate edge may now carry three non-interchangeable utility fields:

1. **predictive utility:** held-out error and absolute target performance;
2. **OOD screening utility:** fraction of a fixed held-out pool screened before
   the first true top-5% hit;
3. **sequential discovery utility:** acquisitions required under a frozen
   reveal-and-refit policy.

A positive field cannot be copied into another. Sequential improvement requires
its own budget, stopping rule, censoring treatment, sensitivity learner,
wrong-source and shuffled controls, and random acquisition reference. The
OBELiX result demonstrates why this separation is necessary: a directional
fixed-ranking signal becomes a sequential null, and the tested UCB acquisition
policy underperforms uniform random acquisition.

## Global-law arm

The contrast with local borrowing must also be tested rather than asserted.
For each candidate global regularity:

1. define a valid observational unit and exclude parameter-estimation
   artifacts;
2. compare a single pooled law with family-varying or hierarchical
   alternatives;
3. measure coefficient heterogeneity and leave-family-out predictive value;
4. apply family-size rules, robust uncertainty, and multiplicity correction;
5. repeat across more than one scientifically defensible regularity before
   generalizing beyond the tested case.

The present Meyer--Neldel analysis supports only this bounded statement: a
single high-explanatory compensation law does not describe the tested ESTM
snapshot. It does not prove that grand laws never exist.

## Minimum accept-level evidence package

1. Four or more data-poor targets across at least three domains.
2. A frozen, outcome-independent neighborhood rubric.
3. Target learning curves that convert prediction gains into samples saved.
4. At least one independently replicated beneficial edge.
5. Confirmed null/equivalent or harmful edges demonstrating selectivity.
6. A held-out-edge test that neighborhood score predicts borrowing benefit.
7. At least two valid global-regularity tests, or a deliberately narrower claim
   restricted to Meyer--Neldel compensation.
8. The existing identity, provenance, artifact, resampling, multiplicity, and
   model-sensitivity gates.

Under this original strong criterion, items 1--6 were required for a portable
predictive topology. The outcome annotation below distinguishes that stronger
object from the endpoint-resolved operational decision map now reported.

## Outcome annotation (14 July 2026; not part of the frozen design)

| Frozen requirement | Outcome |
|---|---|
| four targets across three domains | met: nine targets spanning thermoelectric, alloy, catalysis/electrolyte, molecular and polymer tasks |
| outcome-independent neighborhood rubric | met for the declared 0--3 rubric in `knowledge_map_design.json` |
| target learning curves | met internally; the independent temporal curve is nonmonotone, so no external sample-saving estimate is admitted |
| independently replicated beneficial edge | directional statistical replication met for Borg UTS→BIRDSHOT YS, but the 4.30% effect misses the frozen 5% practical gate; therefore no edge is fully confirmed under the seven-part definition above |
| null/equivalent and harmful edges | met and retained in the audited inventory |
| held-out predictive neighborhood law | not met: ordinal Spearman p=0.113; the binary near-versus-distant contrast is post-map, exploratory and leave-one-target-out fragile |
| multiple global-regularity tests | met for thermoelectric Meyer--Neldel and ISODB isosteric compensation, with different gate outcomes |
| fixed OOD screening utility | directional only for ESTM ZT→OBELiX: 17.3% relative reduction, Holm p=0.0003, but practical and consistency gates fail |
| sequential discovery utility | not met for ESTM ZT→OBELiX: 0.25 acquisitions saved [−1.30,1.82], p=0.389; random acquisition outperforms both tested UCB policies |

The outcome supports an **operational decision map** over the tested edges: each
relation is located by endpoint, evidence state, and scope, including positive,
null, harmful, and unresolved regions. It does not satisfy the stronger frozen
criterion for a **portable predictive topology** that anticipates utility on
held-out edges or targets. The manuscript uses “artifact-gated knowledge-
borrowing map” in the first, operational sense and explicitly excludes the
second, as well as any fully calibrated cross-materials transfer law.
