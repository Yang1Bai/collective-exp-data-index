# Digital Discovery paper package

## Canonical title

**Falsification-gated knowledge borrowing improves out-of-distribution
prediction and screening**

## One-sentence contribution

Neighbouring experimental programmes can materially improve selected
out-of-distribution (OOD) predictions and candidate rankings when the shared
relation, experimental state, transferred object, leakage boundary, and
decision endpoint are matched; otherwise the method abstains.

## Core story

1. **The need:** Data-poor experimental models are weakest in the OOD regions
   where new scientific exploration is most valuable.
2. **The failure of the obvious approach:** Pooled relations are not
   automatically portable, and generic donor-feature injection repairs none of
   40 declared OOD edges.
3. **The method:** Endpoint-routed knowledge borrowing transfers a qualified
   relation or ordinal score rather than an entire database. Every edge must
   pass validity, utility, robustness, and specificity gates.
4. **Strong prediction evidence:** A permutation-invariant electrolyte relation
   learned from 10,407 measurements across 22 salts predicts an external
   unseen-salt programme with raw \(R^2=0.629\), \(\rho=0.871\), and 28.64%
   lower log-RMSE than temperature and concentration alone.
5. **Strong screening evidence:** With five recipient measurements, a
   three-programme conductivity score ranks unseen formulations at
   \(\rho=0.910\), versus 0.537 for the strongest of 13 recipient-only
   configurations. The gain is \(\Delta\rho=0.374\), with a 95% interval of
   0.213--0.562, and high-performance-quartile precision rises from 0.490 to
   0.933.
6. **Selectivity and boundary:** The same score fails absolute calibration and
   loses to the same-anchor recipient model in a frozen second programme. A
   controlled catalyst series likewise contains two predictive successes, one
   ranking-only edge, and one harmful edge.
7. **Meaning:** The output is an actionable borrowing map that routes an edge
   to numerical prediction, candidate ranking, or rejection. It is not a
   universal transfer model or a unified physical law.

## Evidence hierarchy

### Main-text evidence

| Evidence | Quantitative result | Narrative role |
|---|---|---|
| Generic donor-feature benchmark | 0/40 real edges pass the complete OOD-repair gate | Establishes that naive transfer is insufficient |
| Controlled catalyst derivatives | Five anchors reduce RMSE by 16.3% and 26.1% in two complete held-out systems; one edge is ranking-only and one is harmful | Shows selective relation transfer under controlled perturbations |
| External unseen-salt electrolyte programme | Raw \(R^2=0.629\), \(\rho=0.871\), and 28.64% lower log-RMSE than state-only | Strong cross-database absolute-prediction example |
| SolventSeg unseen-formulation screening | Five-anchor \(\rho=0.910\) versus 0.537; \(\Delta\rho=0.374\) [0.213, 0.562]; precision 0.933 versus 0.490 | Flagship data-poor OOD-ranking example |
| Frozen FINALES boundary | Donor concordance 0.694 versus 0.783 for the same-anchor recipient model; \(\Delta=-0.089\) [\(-0.293\), 0.096] | Establishes programme-specific abstention |

### Supplementary evidence

The following analyses remain available for robustness, mechanism development,
and negative-result transparency, but do not lead the main narrative:

- neighbouring-temperature conductivity transfer within one campaign;
- cross-article anchored response transfer;
- state-aware alloy-strength transfer;
- solid-electrolyte screening and active-learning tests;
- Caltech static-ranking analyses;
- outcome-unseen reverse-transport and second-family catalysis nulls;
- detailed compensation-law and artifact analyses;
- complete resource, edge, model, and threshold audits.

## Draft abstract

Models are most valuable to experimental science when they extrapolate beyond
what has already been measured, but this is also where data-poor models are
least reliable. Neighbouring experimental programmes could supply missing
knowledge, yet physical similarity between databases does not specify what is
portable or how it should be used. Here we treat knowledge borrowing as a
directed, falsifiable contract: donor and recipient must share candidate-level
inputs, the relevant experimental state, a declared transferable relation, and
a decision endpoint; otherwise the method abstains. Generic injection of a
donor prediction repaired 0 of 40 declared out-of-distribution (OOD) edges
across eight recipients. In contrast, a permutation-invariant electrolyte
relation learned from 10,407 measurements across 22 salts predicted an
external unseen-salt programme with raw \(R^2=0.629\), Spearman
\(\rho=0.871\), and 28.64% lower log-scale root-mean-square error than a
temperature--concentration baseline. When absolute calibration was not
portable, an equal-programme ordinal score still ranked unseen formulations
from five recipient measurements at \(\rho=0.910\), compared with 0.537 for
the strongest of 13 recipient-only configurations
(\(\Delta\rho=0.374\), 95% interval 0.213--0.562). Controlled chemical
perturbations separated predictive, ranking-only, and harmful edges, and the
unchanged ordinal route was rejected in a frozen second recipient. These
results show that neighbouring experiments can materially improve selected OOD
predictions and screening decisions, provided that the transferred object is
qualified against matched falsifiers and routed to the endpoint it can support.

## Main-text architecture

### Introduction

1. Scientific exploration is an OOD problem.
2. Experimental aggregation can create an illusion of portable knowledge.
3. Existing transfer methods do not qualify the donor, transferred object, or
   endpoint.
4. This work introduces falsification-gated borrowing and previews the strongest
   prediction and screening results.

### Methods

1. Experimental evidence layer and directed donor--recipient roles.
2. Transfer objects: relation-based prediction, permutation-invariant mixture
   prediction, and ordinal scoring.
3. Grouped OOD construction, matched recipient-only baselines, false donors,
   and four gate families.
4. Four claim-bearing experiments: generic failure benchmark, controlled
   catalyst perturbations, external unseen-salt prediction, and
   cross-programme ordinal screening with a frozen recipient boundary.

### Results

1. A systematic failure benchmark establishes the need for routing.
2. Controlled perturbations reveal relation-specific transfer.
3. A routed relation crosses database and salt identity.
4. Ordinal borrowing rescues screening when calibration fails.
5. A frozen second recipient sets the abstention boundary.

### Discussion and conclusion

Interpret what transfers, why utility depends on the decision endpoint, and
where the retrospective evidence stops. Conclude with the operational rule,
not a list of every experiment.

## Main figures

1. **From neighbouring experiments to an OOD decision:** the data-poor
   recipient, qualified donor--recipient edge, endpoint routing, four gate
   families, and the quantitative prediction, screening, and rejection
   outcomes that anchor the paper.
2. **Why naive reuse fails:** one compact portability/artifact example and the
   40-edge generic-feature benchmark.
3. **Matched relations improve OOD prediction:** controlled catalyst
   derivatives and external unseen-salt prediction.
4. **Borrowed order rescues screening but is programme-specific:** the
   13-model recipient stress test, source ranking, failed calibration, and
   frozen second-recipient rejection.

Existing supplementary figures remain in the repository but should not be
added to the main text merely because they are available.

## Defensible claims

- Neighbouring experimental knowledge can materially improve selected OOD
  numerical predictions and candidate rankings.
- Generic donor-feature injection is insufficient within the tested benchmark.
- The transferable object can be a relation or ordinal score rather than a
  calibrated property value.
- Strong recipient-only baselines and matched false donors are necessary to
  distinguish borrowed knowledge from regularization or weak-target effects.
- Programme-specific abstention is part of the method.

## Claims excluded from the paper

- Neighbouring domains generally or automatically transfer.
- The method has discovered a universal physical law.
- The SolventSeg result establishes calibrated conductivity prediction.
- The retrospective examples establish prospective laboratory discovery
  acceleration.
- The catalog size proves generalization.
- Every completed exploratory analysis deserves a main-text showcase.

## Canonical files

- Main manuscript: `analysis/MANUSCRIPT_DRAFT_STREAMLINED.md`
- Main workflow figure: `analysis/figures/knowledge_borrowing_overview_ai_v4.pdf`
- Failure benchmark: `analysis/figures/figure2_failure_benchmark_nmi_v3.pdf`
- Qualified-relation prediction: `analysis/figures/figure3_relation_transfer_nmi_v3.pdf`
- Ordinal screening and boundary: `analysis/figures/figure4_ordinal_screening_nmi_v3.pdf`
- Main-figure QA: `analysis/figures/FIGURE_QA_NMI_V3.md`
- Evidence selection: `analysis/CORE_STORY_EVIDENCE_SELECTION_2026-07-30.md`
- Terminology ledger: `analysis/CORE_STORY_TERMINOLOGY_LEDGER_2026-07-30.md`
- Supplementary Information: `analysis/SUPPLEMENTARY_INFORMATION.md`
- Superseded ranking figure: `analysis/figures/cross_database_electrolyte_ranking.pdf`
- Formal interaction summary:
  `analysis/results/bamboomixer_cross_database_interaction_summary.json`
- Independent interaction verification:
  `analysis/results/bamboomixer_cross_database_interaction_verification.json`
- Recipient-baseline stress test:
  `analysis/results/bamboomixer_recipient_baseline_stress_test_summary.json`

## Remaining high-value work

1. Convert the manuscript citations and equations to the journal template.
2. Add a concise related-work comparison table to the Supplementary
   Information.
3. Freeze one outcome-sealed third recipient or prospective experimental
   shortlist as the independent confirmation test.
