# Research brief for Edison Analysis and Hypothesis Generation

## Research objective

Develop a stronger, falsifiable research programme around the following thesis:

> When scientific understanding is incomplete, universal laws do not emerge automatically from aggregated experimental data. However, neighbouring experimental domains can provide selective, quantifiable knowledge that improves data-poor and out-of-distribution (OOD) decisions, provided that source credibility, experimental context, endpoint compatibility and negative-transfer risk are explicitly controlled.

The desired contribution is not another generic transfer-learning benchmark. It is an operational, abstaining knowledge-borrowing map: a directed map showing which experimental domain can make a useful proposal to which target, for which endpoint, under which conditions, and when the method must refuse to borrow.

## Existing evidence that must be respected

- The project catalogs 118 experimental materials/chemistry resources and integrates 96,184 measurements from 13 normalized sources plus one analysis-only source, retaining identity, conditions and provenance.
- Direct transport of an apparently strong materials law fails: Borg same-record UTS--YS gives R2=0.790, whereas BIRDSHOT gives R2=0.067 and the Borg line transferred to BIRDSHOT gives R2=-3.006.
- A within-campaign neighbouring-condition edge works: KIT conductivity at -20 C used for a -30 C, n=30 target reduces RMSE by 15.02% (95% CI 8.61--21.10%), raises R2 from 0.739 to 0.811, passes leakage, learner, ordering and shuffled-source controls, and corresponds to about 37% point label saving.
- The analogous paper-disjoint CALiSol -30 C to -40 C edge is unresolved/null: +1.61% (-2.14--4.21%), negative absolute R2 and failed ordering/fold/sample-saving gates.
- In OBELiX, a thermoelectric prior improves a fixed OOD-screening rank endpoint directionally, but does not improve a sequential acquisition-and-refit campaign. Random acquisition beats the tested UCB policies.
- On an independent Caltech ionic-conductor target, frozen adaptive residual-injection policies fail, yet prespecified OBELiX and ESTM static rankings recover different external high-value candidates. A post-outcome target-model-free portfolio recovers 5/8 top candidates versus 2/8 and 3/8 individually.
- An outcome-informed family-first allocation recovers all 4/4 distinct Caltech identity/provenance components and 2/2 hard-OOD components by acquisition 20, with conditional shuffled-rank p=0.0020 and 0.0030. This result is retrospective and must not be represented as prospective confirmation.
- Two outcome-unseen programmes test the boundary. Starrydata is weakly directional (+0.88%, 0.02--1.77%) but fails Holm multiplicity, absolute utility, source specificity and hypothesis-card gates. Four-plate TRI OER is null (-0.08%, -0.31--0.16%). The two-target random-effects mean is null (+0.30%, -0.62--1.22%) and heterogeneous (I2=76.7%).
- Compensation-law analyses show that pooled regularities require artifact and family gates; they do not support a universal law.

## Non-negotiable validity constraints

1. Separate prediction, fixed screening, sequential acquisition and scientific-region discovery as different endpoints.
2. Separate exploratory/post-outcome observations from frozen or outcome-unseen confirmation.
3. Do not use target outcomes to choose a source, representation, policy, hyperparameter, stopping rule or hypothesis and then call the result confirmatory.
4. Require exact identity/provenance exclusions, grouped splits, source cross-fitting, wrong-domain controls, shuffled-source controls, multiplicity correction and absolute-utility checks.
5. A feature-importance result is not a physical mechanism. A retrospective high-value hit is not prospective discovery acceleration.
6. Null and harmful edges are part of the knowledge-borrowing map and must trigger abstention rather than being hidden.

## Requested investigation

Independently challenge and improve the programme. Do not merely summarize it or rewrite the manuscript.

### A. Generate falsifiable scientific hypotheses

Generate 8--12 non-redundant hypotheses explaining when and why neighbouring-domain knowledge improves OOD decisions. At minimum investigate:

- source credibility versus superficial physical adjacency;
- condition continuity and latent-state alignment, including why KIT succeeds but CALiSol does not;
- complementary source rankings versus adaptive feature/residual injection;
- whether family/component diversity is the correct objective for OOD scientific exploration;
- whether transfer benefit is localized to target regions with epistemic knowledge deficit rather than visible in global R2;
- directionality and endpoint specificity;
- mechanisms of negative transfer and principled abstention;
- whether multiple weak but conditionally independent neighbours can be more useful than one high-skill source.

For each hypothesis provide: mechanistic rationale, directional prediction, observable signature, existing evidence for/against it, decisive analysis or experiment, negative control, falsification criterion, required data, compute burden, and whether the test can be confirmatory with current data.

### B. Propose stronger borrowing methods

Compare and prioritize methods that could outperform static rank fusion or random-forest feature injection without creating leakage:

- uncertainty- and support-aware mixture-of-experts with abstention;
- conformal or risk-controlled borrowing gates;
- conditional rank aggregation that preserves independent source proposals;
- family-first or diversity-aware acquisition objectives;
- target-region-specific transfer rather than global transfer;
- hierarchical/meta-analytic modelling of source-target edges;
- physics-conditioned representation alignment;
- causal or invariant prediction approaches for experimental-condition shifts;
- meta-learning across directed edges, provided the number of independent edges is sufficient.

For each candidate method specify the minimal benchmark, comparator, ablation, failure guard and independent validation design.

### C. Identify the strongest next experiment

Return a ranked list of the five highest-information next analyses or experiments. Optimize for changing scientific belief, not for producing another positive metric. Identify one experiment that could establish a prospective neighbouring-domain discovery claim and one experiment likely to falsify the overall thesis.

### D. Adversarial synthesis

Conclude with:

1. the strongest version of the central hypothesis that the current evidence supports;
2. the largest unresolved confound;
3. the minimum additional evidence needed for a high-impact methods paper;
4. a proposed causal/decision diagram linking source credibility, physical adjacency, target knowledge deficit, endpoint, borrowing policy and observed utility;
5. a preregistration-ready primary hypothesis and analysis plan for a new outcome-unseen target.

All recommendations must preserve the core idea: neighbouring scientific domains can stimulate discovery, but only through qualified, selective and falsifiable borrowing rather than indiscriminate aggregation.
