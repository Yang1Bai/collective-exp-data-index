# Edison + Hypothesis Generation: combined research synthesis

## Provenance and scope

- Edison task: `F0A9CE`; full report and audited notes are preserved in this directory.
- Google Labs Hypothesis Generation run: `76B68839-DCBF-403D-B2E5-E03B58A0764E`, completed 20 July 2026.
- Hypothesis Generation export: 50 evaluated ideas, including 23 labelled `HIGH POTENTIAL` and 27 labelled `NON VIABLE`.
- Raw export SHA256: `821226F2D57BEFA360A3110C7ACC46DD11178C9B74AEC45313119CE08351C058`.
- This synthesis is an adversarial audit of the two external-agent outputs. It does not treat their generated mechanisms, citations, thresholds, or proposed experiments as evidence.

## Decision

The two reports converge on one useful upgrade:

> Neighboring experimental domains should be treated as qualified, directional lenders. Their information is borrowed only for a specified target region and decision endpoint; complementary lenders may be combined, and the policy must explicitly abstain when credibility, support, or physical compatibility is insufficient.

This strengthens rather than replaces the paper's thesis. The positive existence result remains KIT, while the failed coefficient transports, CALiSol, Starrydata, TRI, and adaptive OBELiX/Caltech policies define the borrowing boundary. Caltech supplies retrospective evidence that qualified neighbors can retain complementary OOD-ranking information even when adaptive prediction transfer fails. The scientific object is therefore a directed, endpoint-indexed map with three actions: **borrow, combine, or abstain**.

The reports do not add a new empirical positive edge. They add a better policy hypothesis and a sharper validation programme.

## What the 23 “high-potential” ideas reduce to

The 23 ideas are not 23 independent scientific directions. Most are near-duplicate combinations of DAKB, conformal gating, mixture-of-experts, physical-oracle checks, and abstention. After removing duplication and proposals disconnected from the repository, five non-redundant ideas remain.

1. **Directed abstention map.** Transferability is asymmetric and endpoint-specific; null and harmful edges remain in the graph and train the refusal rule.
2. **Separate statistical support from physical compatibility.** A source can be statistically close yet physically irrelevant, or physically adjacent yet unsupported at a particular candidate. These are distinct gates.
3. **Explicit null expert.** The combination rule must allow all sources to receive zero weight, falling back to target-only prediction or novelty. Ordinary softmax routing cannot express complete abstention.
4. **Local utility rather than global fit.** The primary question is whether borrowing improves decisions in target regions with high epistemic deficit, not whether pooled test-set R² rises.
5. **Boundary experiments.** Negative transfer is scientifically useful when it coincides with a prewritten mechanism or condition boundary; the experiment should test that boundary rather than merely optimize a metric.

The four-tier evidence hierarchy, provenance exclusion, wrong-source and shuffled controls, outcome-unseen testing, hypothesis cards, and endpoint separation proposed by the reports are already implemented in this project.

## What must not be imported from the generated report

- Do not add palladium cross-coupling, perovskite-interface, BaIrO3, Fe-porphyrin, or transition-metal-GNN stories. They were generated without evidence that the required data, measurements, or experimental access exist in this project.
- Do not use the generated labels `PZOG`, `SPO-ACSI`, `GQL`, `GQPO`, `MSRA-CDG`, or similar branding in the manuscript. They add vocabulary without validation.
- Do not claim that a “physics-based zero-shot oracle” is an oracle. A rule chosen or tuned after viewing target outcomes is another outcome-informed model.
- Do not import numerical success thresholds such as 25% error reduction, 35% OOD improvement, or 50% experiment saving. The reports supplied no power analysis or physical basis for them.
- Do not claim conformal target-domain coverage under unrestricted source-to-target shift. Weighted conformal arguments require explicit covariate-shift and density-ratio assumptions; otherwise report empirical calibration and abstention performance only.
- Do not use target residuals, target labels, or an under-trained target model's unstable gradients to decide whether the same sample should borrow. Several generated gates are circular or logically inverted in precisely this way.
- Do not interpret 23 high-potential labels as independent expert support. They are correlated generations from the same run and frequently repeat the same architecture.

## The strategy to carry forward: credibility, compatibility, and abstention

The project already uses `CCA` for credibility-gated, complementary, abstaining borrowing. Retain that name and make the policy operational at the candidate-region level.

### Inputs fixed without target outcomes

For every source, target, endpoint, and candidate region, record:

1. **Source credibility:** source-only grouped cross-validation, measurement provenance, sample size, coverage, and uncertainty.
2. **Local source support:** whether the candidate lies within a defensible source-support region using outcome-free descriptors.
3. **Physical/condition compatibility:** a prewritten relationship such as shared transport carrier, temperature continuity, reaction family, phase regime, or known boundary.
4. **Target epistemic deficit:** target-label scarcity and outcome-free OOD distance. This identifies where help is needed; it must not automatically multiply a weak source into a high acquisition score.
5. **Endpoint:** prediction, fixed screening, family/component breadth, sequential acquisition, or hypothesis confirmation.
6. **Historical edge prior:** if a gate is learned from past edges, estimate it with leave-one-target-program-out training so the held-out programme contributes no outcomes to its own decision.

### Decision rule

- **Borrow** when one source passes the frozen credibility, local-support, physical-compatibility, and endpoint gates.
- **Combine** when multiple admitted sources make complementary, source-side-independent proposals. Use a frozen rank portfolio or family-first allocation; do not force agreement.
- **Abstain** when no source passes. The fallback is target-only prediction, composition novelty, or uniform exploration, chosen for the named endpoint.

OOD distance should define reporting strata, quotas, or tie-breaking. It should not be used as a multiplicative reward capable of overwhelming weak source evidence; the project's local multiplicative-gating experiment already failed that design.

### Minimum comparators

Every evaluation must include target-only/no-borrow, always-borrow, support-only, physical-adjacency-only, best single source, naive rank fusion, novelty/diversity, wrong source, and shuffled source. A complex gate is useful only if it improves the benefit–coverage trade-off and reduces harmful transfer relative to these simple policies.

## New falsifiable hypotheses worth testing

### H1 — Local epistemic-deficit hypothesis

Qualified source information produces its largest gain in target regions that are simultaneously label-scarce and outcome-free OOD, even when the global average effect is small.

- Signature: a positive source-specific gain in the prespecified far-OOD stratum and a positive interaction between borrowing and target epistemic deficit.
- Control: matched wrong and shuffled sources with the same feature capacity.
- Falsifier: the adjacent source is no better than the strongest control in the far-OOD stratum, or absolute target utility remains unusable.

### H2 — Credibility-over-adjacency hypothesis

Physical adjacency is necessary but not sufficient; an adjacent source with poor measurement/model credibility should be rejected even when a superficially more distant but credible source retains useful ranking information.

- Signature: gate decisions and realized utility follow credibility plus local compatibility more closely than domain labels alone.
- Control: skill-, size-, and coverage-matched wrong sources.
- Falsifier: adjacency-only admission performs as well as the full gate on held-out target programmes.

### H3 — Complementary-proposal hypothesis

Two admitted neighbors with conditionally independent ranking errors recover more distinct high-value families or provenance components than the best single source, even if their mean prediction ensemble does not improve RMSE.

- Signature: higher distinct-component hit count or AUC at a fixed budget, with non-inferior harmful-hit rate.
- Control: matched shuffled ranks and naive mean/Borda fusion.
- Falsifier: the portfolio does not beat the best single source after target-program-level inference.

### H4 — Endpoint-transition hypothesis

A source can be useful for static OOD screening yet useless or harmful after adaptive refitting because target-model error and acquisition dynamics overwrite the source signal.

- Signature: positive fixed-ranking utility accompanied by null sequential utility under the same frozen source ranking.
- Control: uniform random, novelty, target-only UCB, and a static source-only policy.
- Falsifier: source value is stable across endpoints and policy conversion under independent replication.

### H5 — Boundary-as-science hypothesis

A prewritten physical or condition boundary predicts where an otherwise useful edge changes from positive to null or harmful.

- Signature: transfer utility changes sign or the policy abstains across the nominated boundary while matched within-regime controls remain positive.
- Control: a boundary irrelevant to the endpoint.
- Falsifier: the proposed boundary does not modify transfer utility or abstention behavior.

## Ranked experiments

### 1. Independent neighboring-condition replication — highest priority

Select a genuinely new experimental campaign with a condition-adjacent source and target, then freeze the source, direction, representation, learner, grouped split, label budget, OOD rule, primary metric, and hypothesis card before target outcomes are accessed.

- Primary endpoint: paired relative RMSE reduction in the prespecified high-deficit target region.
- Required gates: positive interval, multiplicity-adjusted source-specific contrast, positive absolute utility, learner sensitivity, and no identity/provenance overlap.
- Cost: new data access plus moderate compute.
- Value: supplies the missing independent positive edge if successful; gives a legitimate abstention boundary if null.

### 2. Leave-one-target-program-out borrowing-gate benchmark

Assemble the current positive, null, harmful, and unresolved edges into target-programme clusters. Train any admission rule without the held-out target programme and predict `borrow` or `abstain` for that programme.

- Primary endpoint: harmful-transfer rate among admitted target programmes.
- Secondary endpoints: accepted-edge utility, abstention coverage, calibration, and regret relative to always- and never-borrow.
- Inference: target-programme bootstrap or hierarchical model, not seed-level pseudoreplication.
- Cost: reanalysis and moderate compute; no new measurements.
- Limitation: the number of independent programmes and clean positive edges is currently small, so this is method development rather than definitive gate validation.

### 3. Prospective complementary-neighbor discovery test

Freeze a new external candidate pool, at least two source rankings, source admission, rank-dependence estimate, family/component definition, and top-k budget before measuring target outcomes.

- Primary endpoint: top-k high-value hits at fixed experimental cost.
- Secondary endpoint: distinct high-value family/component recovery.
- Comparators: best single source, naive fusion, target-only/novelty, wrong-source portfolio, and shuffled-source portfolio.
- Cost: new experiments or a genuinely future temporal block.
- Value: this is the clean route from retrospective OOD screening to “neighboring fields stimulate new science.”

### 4. Adversarial boundary panel

Predeclare a small panel containing plausible positive, null, and harmful edges and test whether CCA abstains before target outcomes are revealed.

- Primary endpoint: false-positive borrowing rate at target-programme level.
- Required guard: the policy must also retain useful edges; trivial always-abstain behavior fails.
- Cost: reanalysis if suitable untouched targets exist; otherwise new data.
- Value: establishes that the map is a decision instrument, not a catalogue of post hoc explanations.

### 5. Focused physical-compatibility ablation

On one domain with a defensible physical boundary and available descriptors, compare support-only gating with support plus the prewritten physical check.

- Primary endpoint: incremental reduction in harmful transfer at matched coverage.
- Cost: depends on descriptor availability; avoid expensive calculations unless they are already available.
- Value: tests whether “scientific knowledge” adds anything beyond statistical distance.

## Manuscript consequence

No present numerical result changes. The manuscript should become more positive at the claim level while preserving the evidence boundary:

> Neighboring experimental domains can rescue selected data-poor and OOD decisions. The rescue is not a global property of domain labels: it is local, directional, and endpoint-specific. We make that selectivity operational through a provenance-aware map that qualifies lenders, preserves complementary proposals, and abstains at unsupported edges. Positive, null, and harmful transfers jointly reveal where experimental knowledge can be borrowed.

The current paper can support this as a bounded retrospective methods claim: KIT is the clean existence proof, Caltech is the external OOD-ranking and complementarity demonstration, and the null/harmful programmes validate the need for selection and abstention. A second independent positive predictive edge or a prospective candidate test is required to upgrade the claim to replicated general transfer or discovery acceleration.

## Instructions for a subsequent manuscript editor

1. Preserve the positive thesis above; do not rewrite the article as a catalogue of failures.
2. Do not imply that all adjacent domains transfer, that CCA has already been prospectively validated, or that global R² is the sole success criterion.
3. Present prediction, fixed screening, family/component discovery, sequential acquisition, and hypothesis confirmation as separate endpoints.
4. Use the generated reports only as hypothesis and design inputs. Verify every external citation, dataset claim, physical mechanism, and mathematical guarantee independently before manuscript use.
5. Treat the five experiments above as the complete upgrade path. Do not replace them with additional retrospective model variants that reuse observed target outcomes.
