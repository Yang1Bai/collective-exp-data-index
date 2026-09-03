# Prospective CCA-v2 protocol: local applicability before borrowing

## Claim to be tested

For a target programme whose outcomes were not used to choose the method,
candidate-local applicability and endpoint-specific source use can improve OOD
decision utility over both target-only and adjacency-only policies while
limiting negative transfer.

This protocol was written after the leave-one-program CCA-v1 result.  It may
guide implementation and prospective data collection, but any threshold tuned
on the current 13-program panel is developmental.  The confirmatory version,
source set, thresholds, target, candidate pool, and hypothesis cards must be
hashed before outcomes from the new programme are accessed.

## Why v2 is different

CCA-v1 could reject obvious wrong neighborhoods but could not rank alternative
sources within a credible neighborhood.  CCA-v2 therefore does not use global
source OOF R2 as a hard proxy for transferable benefit and does not reduce a
source-target relation to one scalar score.

## Frozen architecture for the next independent programme

### Stage A — contraindication gate

Reject a source when any of the following holds:

- exact material, article, campaign, or time leakage remains after grouping;
- the nominated relation lacks a written property/condition/mechanism rationale;
- a matched wrong-source or shuffled-source feature performs equivalently under
  the same capacity and split; or
- source uncertainty cannot be estimated without target-test outcomes.

Source OOF skill is retained as a continuous reliability covariate with an
interval, not a universal binary admission threshold.

### Stage B — candidate-local applicability

For every source-candidate pair, calculate without target outcomes:

- distance to the source training support in the frozen representation;
- source ensemble or conformal uncertainty calibrated by source groups;
- distance to the labelled target support;
- composition, condition, and provenance compatibility;
- agreement and disagreement with other admitted source ranks; and
- whether the proposed use is prediction, fixed screening, breadth exploration,
  or adaptive acquisition.

Applicability must be estimated inside source folds.  Target-test candidates
may be transformed but never used to select feature definitions or thresholds.

### Stage C — endpoint-specific borrowing

- **Few-shot prediction:** use cross-fitted source predictions through a
  shrinkage coefficient with a point mass at zero.  Compare with the identical
  target-only learner.
- **Fixed OOD screening:** preserve each source's rank; combine calibrated local
  support with rank consensus and a diversity constraint.
- **Breadth exploration:** allocate the first pass across outcome-free material
  families or provenance components and report the loss in entity recall.
- **Adaptive acquisition:** only proceed when the target-only acquisition
  backbone beats random.  Keep random and novelty arms available and update
  source allocation from observed rewards without changing the frozen source
  direction.

### Stage D — abstention

Borrow only when the lower calibrated bound on incremental utility exceeds a
predeclared practical dead zone.  Otherwise use the target-only policy.  A new
source-derived region is recorded as a hypothesis, not a discovery, until its
target measurement is revealed and a matched falsifier is tested.

## Minimum independent validation

Use at least one genuinely temporal or prospective target programme for the
first confirmatory test; accumulate at least five independent programmes across
two scientific families before estimating a general policy effect.  The target
programme, source set, candidate pool, grouping unit, representation, endpoint,
and all controls are frozen before target outcome access.

The independent unit is the programme or experimental campaign, never the ML
seed.  Repeated splits quantify algorithmic instability within a programme.

## Primary decision family

1. **Primary efficacy:** programme-level relative decision-utility improvement
   of CCA-v2 over adjacency-only, with a 95% interval above zero.
2. **Required target-only check:** the same CCA-v2 utility relative to the
   prespecified target-only policy must be positive with a 95% interval above
   zero.
3. **Safety guard:** no clearly harmful programme and no more than 10% clearly
   harmful admitted task decisions after accumulating five programmes.
4. **Coverage guard:** borrowing must occur in at least 20% of programmes and
   20% of eligible OOD candidates or tasks.

The two efficacy comparisons form one Holm-corrected family.  Safety and
coverage are conjunctive guards, not additional opportunities for significance.
All null, harmful, and abstaining programmes remain in the denominator.

## Required controls

- target only;
- adjacency only;
- global source credibility only;
- strongest single qualified source;
- shuffled source labels or ranks;
- size/skill/coverage-matched wrong source;
- novelty and uniform random for exploration endpoints; and
- oracle selection reported descriptively only.

## Scientific-inspiration endpoint

Before measuring each nominated target region, record a source-specific card:
the proposed material family or condition, why the source suggests it, the
expected direction, a mechanistic or compositional falsifier, and a matched
target-only or wrong-source control.  Success requires enrichment over the
matched control and survival of the frozen multiplicity family.  A predictive
gain alone is not counted as new science.

## Stop rules

- If adjacency-only equals or exceeds CCA-v2 on the first two independent
  programmes, freeze feature development and do not retune on those outcomes.
- If the target-only adaptive backbone fails to beat random, stop the adaptive
  claim and retain only fixed-screening evidence.
- If a wrong or shuffled source passes the same gate, classify the programme as
  non-specific and do not replace it with another target.

## First target-specific freeze

The first execution appendix is the multi-stage lithium-ion aging programme:
`analysis/MULTISTAGE_BATTERY_CCA_V2_PROTOCOL.md`. Stage 1 is the temporal source
and Stage 2 is the outcome-unseen OOD target. The exact endpoint,
condition-group unit, 2% dead zone, local applicability rule, two-comparison
Holm family, controls, outcome-sealing sequence, and non-replacement rules are
machine-readable in `analysis/multistage_battery_cca_v2_design.json`.

The target is frozen but not yet outcome-released. A two-archive metadata pilot
resolved the repository's duplicate-filename method: the archive serial must be
joined with the archive-internal serial. The complete 279-archive map was
hashed before any numeric aging CSV data row was parsed. CS13 is
`preoutcome-frozen`, not complete, and contributes no favorable result to the
paper.

The complete 279-archive map subsequently passed independent verification with
141 Stage 1 and 138 Stage 2 cells; the mapping operation opened no CSV member.
A protected endpoint audit later read only 32 first-line CSV headers across
three archives and no numeric data row. The official paper-defined 23-degree
RPT capacity extractor -- the mean of integrated step-21 charge and step-22
discharge capacity -- is now frozen in a version-5 pre-outcome amendment. CS13
remains `preoutcome-frozen` because Stage 1 source-model freezing, hypothesis
cards, and the sealed Stage 2 analysis have not yet occurred.
