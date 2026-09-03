# Claude prompt: scientific strategy review of neighbouring-domain knowledge borrowing

You are serving as an adversarial scientific co-investigator and pre-submission referee for a data-driven materials-science methods paper targeted at *Digital Discovery*. Do not focus on prose, formatting or politeness. Your job is to decide whether the scientific case is real, what the most defensible central claim is, and which one or two additional analyses would most increase the probability of acceptance.

## Repository

Read the local repository:

`D:\OneDrive - University of Toronto\AC\Project\Collective exp dataset`

Start with these files:

### Manuscript and story

- `analysis\MANUSCRIPT_DRAFT_STREAMLINED.md`
- `analysis\MANUSCRIPT_STREAMLINING_MAP.md`
- `analysis\CORE_STORY_EXPERIMENT_MATRIX.md`
- `analysis\core_story_experiment_registry.json`
- `analysis\STREAMLINED_MANUSCRIPT_QA.md`
- `analysis\PAPER_PACKAGE.md`
- `analysis\PHASE1_FINDINGS.md`
- `analysis\PHASE2_FINDINGS.md`
- `analysis\PHASE3_FINDINGS.md`
- `analysis\ADVERSARIAL_REVIEW_RESPONSE.md`

### Central verified evidence

- `analysis\results\state_matched_mpea_balam_v2_summary.json`
- `analysis\results\state_matched_mpea_balam_v2_bootstrap_summary.json`
- `analysis\results\state_matched_mpea_balam_v2_VERIFIED.json`
- `analysis\results\multi_target_ood_summary.json`
- `analysis\results\multi_target_ood_target_summary.csv`
- `analysis\results\multi_target_ood_edge_summary.csv`
- `analysis\results\multi_target_ood_contrasts.csv`
- `analysis\results\multi_target_ood_VERIFIED.json`
- `analysis\results\caltech_ionic_external_policy_summary.json`
- `analysis\results\caltech_ionic_external_policy_gate_summary.csv`
- `analysis\results\caltech_ionic_external_policy_utility.csv`
- `analysis\results\caltech_ionic_external_policy_VERIFIED.json`
- `analysis\results\opv_optical_external_formal_summary.json`
- `analysis\results\opv_optical_external_formal_VERIFIED.json`
- `analysis\OPTICAL_SUPERVISED_BORROWING_FINDINGS.md`

### Pending or proposed experiments

- `analysis\STRENGTH_TO_FATIGUE_OOD_PROTOCOL.md`
- `analysis\strength_to_fatigue_ood_design.json`
- `analysis\strength_fatigue_implementation.json`
- `analysis\results\strength_fatigue_preoutcome_audit.json`
- `analysis\results\strength_fatigue_preoutcome_VERIFIED.json`
- `analysis\results\strength_fatigue_ood_submit.log`
- `analysis\BATTERY_CONDUCTIVITY_BORROWING_PROTOCOL.md`
- `analysis\battery_conductivity_borrowing_design.json`
- `analysis\results\battery_conductivity_preoutcome_audit.json`
- `analysis\XRD_TO_SYNTHESIS_PREOUTCOME_READINESS.md`
- `analysis\xrd_to_synthesis_readiness.json`

### Data-resource foundation

- `catalog\catalog.csv`
- `analysis\CATALOG_TO_PAPER_OPPORTUNITY_AUDIT.md`

Do not recursively read model checkpoints, bootstrap-row archives or large raw data unless needed to verify a specific disputed result. Prefer verified summaries, frozen protocols, source tables and code relevant to the disputed claim.

## Non-negotiable scientific objective

The intended claim is:

> When scientific understanding is incomplete, naive aggregation of heterogeneous experimental data does not automatically reveal a grand unified law. However, neighbouring experimental domains can provide selective, quantifiable and operationally useful knowledge for data-poor/OOD regions when donor-recipient direction, physical state, endpoint, provenance, leakage boundaries, applicability and decision use are correctly matched.

The contribution should be stronger than an audit-only paper. We want to establish that an explicit borrowing strategy can improve OOD prediction or exploration in at least one scientifically meaningful setting, while rejecting inappropriate edges.

Do not weaken the paper into “transfer is usually impossible.” Conversely, do not call 1-2% changes evidence of meaningful improvement unless uncertainty, controls and practical scale make that defensible.

## Radical redesign permission

Most completed cross-database experiments in the current repository are null, harmful, or too small to carry the paper. Treat that as the starting condition, not as a result that must be defended.

You are explicitly authorized to redesign the scientific programme from first principles:

- do not assume the current donor-feature injection is the right transfer mechanism;
- do not assume the current donor-recipient pairs are the right examples;
- do not assume Random Forest, composition vectors, scalar source predictions or mean-RMSE improvement are the right model, representation or endpoint;
- do not optimize only around the existing manuscript;
- do not preserve an experiment merely because substantial compute has already been spent on it.

The only fixed elements are the research objective, candidate-time information boundary, strict provenance/leakage control and requirement for independently testable OOD benefit.

Generate genuinely new hypotheses about **what kind of knowledge is portable between neighbouring experimental domains**. Possibilities may include, but are not limited to:

- transferable physical latent variables rather than donor predictions;
- dimensionless or mechanism-normalized representations;
- residual/correction learning around a physical baseline;
- hierarchical Bayesian or multi-task models with partial pooling;
- mixture-of-experts or retrieval systems that select local donors per candidate;
- causal/invariant feature discovery across experimental environments;
- contrastive or self-supervised pretraining on experimental measurements;
- calibrated donor disagreement used to select OOD experiments;
- knowledge transfer to ranking, uncertainty reduction or experimental design rather than average in-domain fit;
- transfer of failure modes, process windows, phase boundaries or mechanistic constraints instead of scalar properties.

These examples are prompts, not restrictions. Propose a different framework if the evidence suggests one.

At least two recommendations must be **new executable research programmes**, not variations of an already completed analysis. Each must include a falsifiable hypothesis, suitable public experimental data, candidate-time inputs, an OOD unit, negative controls, a preregistration boundary and a result large enough to matter scientifically.

## Evidence-state guard

Keep these categories separate:

1. **Verified completed results:** only results carrying independent `VERIFIED`/`COMPLETE` records and reproducible source tables.
2. **Pending formal results:** the strength-to-fatigue job is Balam job `71905`; at the time of this prompt it was submitted but still pending resources. Do not infer its result. Battery-conductivity formal outputs are not present locally; treat the result as unknown unless you find a subsequently verified package.
3. **Proposed/blocked work:** XRD-to-synthesis is deliberately on HOLD until a complete attempt-level recipient table, including failures and partial reactions, is verified.

If manuscript text conflicts with verified result files, trust the verified files and identify the inconsistency.

## Scientific questions to answer

### 1. Is the central phenomenon actually demonstrated?

- Separate same-specimen, same-curve, same-batch, same-platform, cross-programme and cross-database transfer.
- Decide whether the positive results demonstrate transferable knowledge, a proxy label, shared provenance, or some mixture.
- Determine whether there is a defensible “provenance/state ladder” and whether effect size decreases with semantic and provenance distance.
- Explain what evidence would distinguish a mechanistic bridge from a statistical shortcut.

### 2. Is the OOD test scientifically valid?

- Audit the unit of splitting, connected-component construction, DOI/campaign grouping and donor cross-fitting.
- Ask whether the held-out regions represent realistic scientific novelty or only convenient statistical tails.
- Check whether target samples, compositions, curves, papers, batches or derived labels can leak through donor fitting, feature engineering, hyperparameter choice or target selection.
- Check whether uncertainty and multiplicity are calculated at the scientific replication unit rather than at seed or row level.

### 3. Should the current borrowing method be retained, replaced or decomposed?

Evaluate the strategy as a system:

- donor-recipient role assignment;
- state and endpoint matching;
- cross-fitted donor predictions;
- support distance and applicability;
- shrinkage or abstention;
- matched shuffled/wrong-property/wrong-domain controls;
- prediction versus independent ranking;
- minimum practical-effect and absolute-skill gates.

Identify which components are necessary, which are redundant, and which are post-hoc. Propose an ablation that can isolate their contributions without an unmanageable experiment matrix.

Then propose at least three alternative transfer mechanisms that are materially different from scalar donor-feature injection. For each alternative, state:

- what scientific information is transferred;
- why that information should be more invariant than the donor endpoint itself;
- what data are required;
- how the method abstains when the donor is inapplicable;
- the simplest experiment that could falsify it;
- whether it is feasible with current public data.

### 4. Stress-test the pending strength-to-fatigue experiment before seeing outcomes

The proposed bridge is independent experimental ultimate-tensile-strength knowledge used to normalize and augment fatigue S-N prediction in held-out chemical/provenance components.

Assess:

- whether strength is a physically defensible bridge to fatigue life;
- whether predicted strength provides information beyond stress amplitude, composition and processing;
- whether the outer connected-component split is strict enough;
- whether 17 components and 62 curves support the proposed inference;
- whether the wrong-property, shuffled, independent-donor and oracle controls answer the important alternatives;
- whether the acceptance gate is strong enough to prevent a noisy 1-2% result from becoming a headline;
- what interpretation is justified if it passes, partially passes or fails.

Do not modify its frozen scientific design after inspecting outcomes. You may recommend prospective follow-up work.

### 5. Invent the best next scientific programme, not merely the next database pair

Search the repository catalog and, if useful, current primary literature and official data repositories. Rank at most five candidates using:

- explicit shared physical latent variable;
- compatible candidate-time inputs;
- compatible state and measurement conditions;
- independent provenance;
- target data scarcity and meaningful OOD axis;
- accessible negative/null outcomes;
- sufficient grouping information;
- low leakage risk;
- expected effect large enough to matter.

For each candidate, specify:

- donor and recipient;
- physical bridge;
- exact borrowed quantity;
- recipient endpoint;
- OOD split;
- negative controls;
- estimated chance of a >5% practically meaningful improvement;
- data/compute required;
- go/no-go metadata check before outcomes are opened.

The search is not limited to the current catalog or to pairs already attempted. You may introduce a newly published public experimental dataset, combine several donors, redefine the recipient endpoint, or replace property prediction with OOD ranking/exploration if that gives a stronger and more honest scientific test.

Pay particular attention to, but do not restrict yourself to:

- experimental strength to fatigue;
- ionic/electrical transport to battery behaviour;
- phase/reaction knowledge to solid-state synthesis;
- bandgap/optical knowledge to photocatalysis or photovoltaic performance.

Explicitly explain why already failed optical/OPV or broad multi-target experiments should or should not be revisited with a different method.

### 6. Compare novelty with prior work

Browse recent primary literature and authoritative reviews, especially *Digital Discovery*, Nature-family materials/AI journals, and work on:

- multi-task and transfer learning in materials;
- knowledge-integrated materials ML;
- OOD and domain generalization;
- experimental database integration;
- negative transfer and abstention;
- provenance-aware evaluation;
- synthesis-success and failed-experiment datasets.

Use real DOI or publisher/repository links. Do not invent citations. Tell us which claim is genuinely new, which is already known, and what must be distinguished more sharply.

### 7. Decide the manuscript

Recommend:

- the strongest one-sentence thesis;
- which results belong in the main text;
- which results belong only in the Supplementary Information;
- which results should be removed because they distract or overcount evidence;
- the minimum additional experiment needed for acceptance;
- whether the appropriate posture is reject, major revision or near-submission-ready.

## Required output

Write in Chinese, retaining essential English technical terms. Use evidence pointers to exact repository files and, where possible, rows/fields/sections.

Return:

1. **Executive scientific verdict** - no more than 300 Chinese characters.
2. **Shared fact table** - claim, evidence, status (`supported`, `weak`, `unsupported`, `pending`).
3. **Reviewer 1: materials/physical interpretation emphasis.**
4. **Reviewer 2: ML/statistics/OOD validity emphasis.**
5. **Reviewer 3: novelty and *Digital Discovery* significance emphasis.**
6. **Cross-review synthesis** - consensus versus disagreements.
7. **Three highest-leverage next actions**, in priority order, each with:
   - exact analysis;
   - expected decision value;
   - new data/compute required;
   - stop rule;
   - how the manuscript changes under positive, null and harmful outcomes.
8. **A keep/cut/reframe/run decision table** for every major evidence programme.
9. **A revised central claim and figure logic** that stays ambitious without exceeding the evidence.
10. **A clean-sheet research programme**, containing:
    - at least three new transfer hypotheses;
    - the best one selected by explicit scientific and feasibility criteria;
    - a complete experiment specification;
    - the public datasets and access links;
    - the expected physical mechanism;
    - the anticipated effect scale;
    - failure and abstention criteria;
    - a staged compute plan;
    - what result would justify a strong manuscript claim.

For every major criticism, state the concrete resolution test. Do not spend space on grammar, stylistic polishing or generic recommendations.
