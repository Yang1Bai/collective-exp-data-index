# Claude manuscript-review integration record

**Date:** 2026-07-31
**Authoritative manuscript:** `analysis/MANUSCRIPT_DRAFT_STREAMLINED.md`

## Disposition

The external audit was checked against the manuscript, Supplementary
Information, attempt ledger, experiment matrix, verified figure JSON, and the
current test suite. W2--W9 were accepted in substance and merged selectively.
W10 remains an author/release task rather than a prose problem.

W1 was narrowed before integration. The repository does not support the broad
sentence that every outcome-frozen analysis was negative: the within-campaign
KIT task used an internal freeze and was positive. The supported statement is
that every **independent external validation whose complete route was frozen
before recipient-outcome access** currently ended in null, rejection, or
abstention (FINALES, Starrydata, and TRI). The manuscript now states that
asymmetry directly without treating a frozen negative as validation by itself.

## Changes merged

- The title now makes routing and abstention part of the contribution.
- The SolventSeg source score is correctly described as zero-label; five
  recipient measurements train the recipient-only comparators.
- The 0.213--0.562 interval is identified as anchor-selection variability
  conditional on one recipient programme.
- The main text now exposes the pretrained-encoder failure that complements
  the 0/40 generic-feature benchmark.
- The FINALES result is reported as failure to qualify under a frozen contract,
  not proof of non-transfer.
- `component-order-invariant` and `programme-balanced` are the canonical terms.
- The compensation-law discussion is compressed and routed to Supplementary
  Section S7.
- The Supplementary Information title, companion-file pointer, and 21-resource
  arithmetic are aligned with the manuscript.
- Figure legends distinguish zero-label source ordering, five-label recipient
  baselines, retrospective numerical transfer, and frozen abstention.

## Statistical reporting judgement

- The SolventSeg interval is an empirical 2.5th--97.5th percentile range over
  100 outcome-independent anchor selections within one 36-formulation
  recipient. It is not a cross-programme confidence interval.
- The FINALES primary evaluation contains 16 formulations. Its donor advantage
  of -0.089 (95% bootstrap interval -0.293 to 0.096; permutation p=0.131) does
  not establish equivalence or absence of transfer. The frozen decision is
  abstention because the edge did not qualify.
- Formulation, article, programme, and complete catalyst-system groups remain
  the independent resampling units specified by each analysis. No row-level
  pseudoreplication was introduced by the wording changes.

## Additional-analysis priority

1. **Controlled-catalyst anchor sensitivity.** Repeat the five-anchor analysis
   over outcome-independent anchor selections. This most directly tests the
   robustness of a main-text positive routing result.
2. **FINALES precision or minimum-detectable-effect diagnostic.** Report only
   as disclosed post-outcome precision analysis; it cannot change the frozen
   abstention decision.
3. **Anchored-delta or residual transfer on the designated generic edges.** This
   can expand the tested generic-method envelope, but it remains post-outcome
   method development. The existing pretrained-encoder null already prevents
   the 0/40 result from being presented as the only tested generic mechanism.

None of these retrospective analyses can supply independent positive external
confirmation. That requires an outcome-sealed or prospectively measured
recipient with the donor, transferred object, anchor budget, falsifiers,
decision endpoint, and inference frozen before outcome access.

## Validation

- All 23 manuscript citation keys occur in the 44-entry bibliography.
- The manuscript and Supplementary Information titles match.
- No remaining canonical-paper text says that five recipient measurements
  entered or raised the zero-label source score.
- `python -m pytest tests -q`: 118 passed, with three pre-existing warnings.
