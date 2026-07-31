# Edison F0A9CE: audited integration notes

## Provenance

- Edison task: `#F0A9CE`
- Agent: Literature (High)
- Raw report: `EDISON_F0A9CE_FULL_REPORT.md`
- Raw-report SHA256: `BB0B78814E73D5E5341B8069B6C6327E35FA288A13F7764C5D77D5D5721693CC`
- Audit date: 2026-07-19

## Bottom-line decision

Edison strengthens the paper's positive main line, but it does not supply new empirical confirmation. Its most useful contribution is a sharper decision framework:

> A neighboring source is useful when it provides credible, locally compatible information for a specific target region and decision endpoint. The scientific object is therefore not a universal transfer model but a directed policy that decides **borrow, combine, or abstain**, while preserving complementary source proposals for OOD exploration.

This is more ambitious and more defensible than either “transfer generally improves prediction” or “aggregation fails.” It keeps the paper centered on qualified neighboring-domain knowledge borrowing.

## Adopt directly

1. **Positive-first narrative.** Open with the KIT result as the empirical anchor; use Borg→BIRDSHOT as the sharp counterexample that motivates qualification and abstention.
2. **Endpoint taxonomy.** Prediction, fixed screening, sequential acquisition, and scientific-region discovery are different causal/decision questions and must never be pooled into one transfer claim.
3. **Local and directional utility.** The most plausible generalization is target-region-specific benefit under epistemic deficit, not a global increase in R².
4. **Complementarity mechanism.** Static, source-independent proposals can be scientifically valuable even when adaptive residual injection fails. This supports conditional rank portfolios and family-aware exploration.
5. **Abstention as output.** Null and harmful edges are not embarrassing failures; they are necessary observations for learning the boundary of the borrowing map.
6. **Conceptual contribution.** Present the map as a directed, weighted, endpoint-indexed graph with a reject option, not as a symmetric similarity network.

## Modify before adoption

### 1. Do not pluralize the clean positive evidence

The KIT edge is currently the clean predictive anchor. Edison sometimes writes as though a class of “within-campaign neighboring-condition edges” has already been established. Until independent replication, manuscript language must say **one rigorously controlled edge demonstrates feasibility** and the broader class is a testable hypothesis.

### 2. Re-rank the largest confound

Edison calls “implicit representation sharing” the largest unresolved confound. That is too strong. A deterministic composition descriptor shared across datasets is not leakage by itself. Leakage exists if feature selection, scaling, embeddings, thresholds, or hyperparameters use held-out target outcomes—or if use of target covariates is transductive but described as inductive.

The larger inferential weakness is **selection plus scarcity of independent positive edges**: source, target, policy, and endpoint choices can become data-dependent while only one clean positive edge remains. Run a representation audit, but treat independent outcome-unseen replication and frozen edge selection as the primary validity problem.

### 3. A failed poor-quality edge does not validate the gate

Edison Experiment 2 is informative only if the policy predicts `abstain` before target outcomes are revealed. Merely showing that a deliberately poor edge fails is trivial. The severe test must score the gate's decisions over a preregistered panel containing beneficial, null, and harmful edges.

### 4. Conformal guarantees need explicit shift assumptions

Ordinary split conformal validity does not survive arbitrary source→target shift. A borrowing gate may use weighted conformal prediction under covariate shift, but must state that the target/source density ratio is known or estimable from unlabeled target covariates. Under more general shift, report empirical risk and abstention behavior without claiming distribution-free target coverage.

### 5. Sample size must be simulation-based

The proposed “60–80 labels” and “20–30 acquisitions” are planning heuristics, not power calculations. Freeze a generative/resampling model from source-side or historical target data and simulate the paired policy contrast, grouped dependence, hit prevalence, and intended multiplicity correction before choosing `n` or acquisition budget.

### 6. Edge count is effective, not nominal

Fifteen to twenty source→target evaluations are not 15–20 independent units if they share campaigns, targets, or candidate pools. The gate benchmark needs campaign/target clustering and either hierarchical inference or cluster-level resampling. Inventory the effective number of independent target programmes before promising a meta-analytic gate.

## Mandatory next evidence package

### Work package 1 — frozen edge-panel and borrowing gate

Use all currently defensible edges, but cluster them by target programme and provenance. Before inspecting edge outcomes, freeze:

- source credibility features;
- physical/condition adjacency features;
- target-support and epistemic-deficit features computed without target outcomes;
- endpoint label;
- borrow/abstain rule;
- always-borrow, never-borrow, support-only, wrong-source, and shuffled controls.

Primary endpoint: harmful-transfer rate at the target-programme level. Secondary endpoints: accepted-edge utility, coverage/abstention rate, and calibration by target region. A hierarchical edge model may summarize heterogeneity but cannot manufacture independent replication.

### Work package 2 — independent neighboring-condition replication

Select one genuinely new, outcome-unseen experimental campaign with an adjacent condition pair. Freeze source, target, direction, representation, learner, split grouping, `n`, and primary metric before outcomes. The primary claim is a paired relative-RMSE reduction versus target-only learning; absolute R², sample saving, and local-region utility are secondary and multiplicity-controlled.

### Work package 3 — prospective complementary-source discovery test

On a new external candidate pool, compare:

1. best prespecified single source;
2. naive mean/Borda rank;
3. conditional portfolio using only source-side proposal dependence;
4. target-only or no-borrow baseline;
5. shuffled/overlap-matched portfolios.

Primary endpoint: preregistered top-`k` hit count at a fixed budget. Secondary endpoint: distinct high-value family/component recovery. Family-first acquisition is an ablation or secondary policy unless a separate budget supports a confirmatory comparison.

These three work packages are the minimum route from “compelling framework with one positive edge” to “operational borrowing policy with independent evidence.”

## Method priority

1. **Target-region-specific support/credibility gate** — highest priority; simplest direct test of the thesis.
2. **Conditional multi-source rank portfolio** — highest discovery relevance and best match to the Caltech complementarity observation.
3. **Hierarchical edge model** — needed for map-level inference and honest heterogeneity estimates.
4. **Weighted conformal/risk-control layer** — useful only with explicit covariate-shift assumptions and adequate calibration support.
5. **Family-first diversity objective** — retain for scientific-region discovery, not global prediction.
6. **Physics-conditioned alignment** — promising but should be a focused mechanistic case study, not required for the first map paper.
7. **rMFBO-style robust sequential borrowing** — relevant future direction; current evidence shows that target-side sequential policies can lose to random, so do not make this the paper's empirical center.

## Reference audit

The raw report contains 36 DOI occurrences but only 18 unique DOIs; half are duplicate aliases created by the report's citation scheme. Do not copy the bibliography verbatim.

Verified high-value references:

- Li et al., *Communications Materials* 6, 9 (2025), “Probing out-of-distribution generalization in machine learning for materials,” DOI 10.1038/s43246-024-00731-w. The paper supports the distinction between statistically OOD and representationally OOD tests.
- Buterez et al., *Nature Communications* (2024), DOI 10.1038/s41467-024-45566-8. It supports multi-fidelity transfer in sparse high-fidelity tasks, but within an explicit fidelity hierarchy; it also documents method-dependent negative transfer.
- Hu et al., *Digital Discovery* 3, 300–312 (2024), DOI 10.1039/D3DD00162H. Correct title: “Realistic material property prediction using domain adaptation based machine learning.” Edison used an inconsistent “Improving realistic…” form in parts of the report.
- Mikkola et al., AISTATS/PMLR 206, 7425–7454 (2023), “Multi-Fidelity Bayesian Optimization with Unreliable Information Sources.” Cite the proceedings version, not only the arXiv DOI.
- Sabanza-Gil et al., *Nature Computational Science* 5, 572–581 (2025), DOI 10.1038/s43588-025-00822-9. Edison lists only the arXiv DOI in its numbered bibliography despite calling it a Nature Computational Science article.
- Zhao et al., *Matter* 8 (2025), article 102377, DOI 10.1016/j.matt.2025.102377. This is a real physics-transfer discovery paper but is a single curated multiscale relation, not a population-level experimental borrowing map.
- Zhang et al., “A Survey on Negative Transfer,” DOI 10.1109/JAS.2022.106004. Appropriate background for harmful transfer, not evidence that the proposed material-specific gate works.
- Tibshirani et al., NeurIPS 2019, “Conformal Prediction Under Covariate Shift.” Use this foundational weighted-conformal reference instead of relying on the Edison report's LLM-specific 2025 conformal citation.

Still requiring manuscript-grade verification: all compensation-law references, BOOM metadata/year, the 2026 Digital Discovery initialization paper's final pagination, and any claim that “no prior work” constructs a comparable map. Absence claims require a reproducible literature search, not Edison alone.

## Recommended central claim for the manuscript

> Experimental neighbors can rescue data-poor OOD decisions, but only as qualified lenders: their value is local, directional, and endpoint-specific. We operationalize this principle as a provenance-aware knowledge-borrowing map that predicts when to borrow, when to combine complementary proposals, and when to abstain; controlled positive, null, and harmful edges jointly define the map.

This language preserves the ambitious story while matching the present evidence hierarchy.
