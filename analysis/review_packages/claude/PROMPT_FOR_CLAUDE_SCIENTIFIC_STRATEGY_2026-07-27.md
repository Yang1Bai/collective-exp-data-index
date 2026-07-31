# Scientific strategy review request for Claude

You have access to the local repository:

`D:\OneDrive - University of Toronto\AC\Project\Collective exp dataset`

Act as an adversarial but constructive senior scientist in materials
informatics, experimental materials databases, transfer learning, OOD
generalization, active learning, and statistical inference. The target journal
is *Digital Discovery* (RSC).

This is not a copy-editing task. Do not spend the response on prose style,
formatting, figure cosmetics, or generic requests for “more data”. Evaluate
the science, decide what the evidence actually establishes, and design the
smallest set of high-information analyses or experiments that would make the
paper substantially stronger.

## Fixed scientific objective

The intended positive thesis is:

> When scientific knowledge is incomplete, heterogeneous experimental data do
> not automatically yield a universal law. Nevertheless, neighboring
> experimental domains can provide transferable information for data-sparse
> OOD regions when donor-recipient direction, experimental state, physical
> endpoint, provenance, support, leakage boundaries, and decision objective are
> aligned. An artifact-gated borrowing map should identify positive, null,
> harmful, and abstaining edges and determine whether donor information should
> enter a predictive model, remain an independent candidate ranking, or be
> rejected.

Do not weaken this into a paper whose only contribution is “transfer often
fails” or “we performed careful auditing”. The authors need a strong positive
methods contribution. At the same time, do not protect the thesis from
falsification. Decide what positive claim is already supported and what
additional evidence is needed for the stronger cross-database OOD-prediction
claim.

## Read these files first

Read the repository files themselves and cite exact file paths, sections,
figures, JSON fields, and result rows in your review. Do not rely only on the
summary in this prompt.

1. `analysis/MANUSCRIPT_DRAFT_STREAMLINED.md`
2. `analysis/MANUSCRIPT_STREAMLINING_MAP.md`
3. `analysis/SELECTIVE_NEIGHBOR_BORROWING_STRATEGY.md`
4. `analysis/CORE_STORY_EXPERIMENT_MATRIX.md`
5. `analysis/STREAMLINED_MANUSCRIPT_QA.md`
6. `analysis/SUPPLEMENTARY_INFORMATION.md`
7. `analysis/LITERATURE_GUIDED_TRANSFER_METHOD_DEVELOPMENT_FINDINGS.md`
8. `analysis/OPTICAL_SUPERVISED_BORROWING_FINDINGS.md`
9. `analysis/PAPER_PACKAGE.md`

Then inspect the compact evidence and its verification records:

- `analysis/results/kit_temperature_summary.json`
- `analysis/results/multi_target_ood_summary.json`
- `analysis/results/state_matched_mpea_balam_v2_summary.json`
- `analysis/results/state_matched_mpea_balam_v2_bootstrap_summary.json`
- `analysis/results/state_matched_mpea_balam_v2_VERIFIED.json`
- `analysis/results/ood_decision_summary.json`
- `analysis/results/obelix_ood_discovery_summary.json`
- `analysis/results/caltech_ionic_external_policy_summary.json`
- `analysis/results/caltech_ionic_external_policy_VERIFIED.json`
- `analysis/results/outcome_unseen_multi_target_summary.json`
- `analysis/results/optical_supervised_borrowing_summary.json`
- `analysis/results/optical_supervised_borrowing_VERIFIED.json`
- `analysis/results/opv_optical_external_formal_summary.json`
- `analysis/results/opv_optical_external_formal_VERIFIED.json`

Inspect the main figures under `analysis/figures/`, especially:

- `data_foundation_scope.png`
- `main_knowledge_borrowing.png`
- `multi_target_ood_borrowing.png`
- `state_matched_mpea_borrowing.png`
- `neighbor_map_exploration.png`
- `outcome_unseen_validation.png`

For the currently running conductivity-to-battery experiment, first inspect:

- `analysis/BATTERY_CONDUCTIVITY_BORROWING_PROTOCOL.md`
- `analysis/battery_conductivity_borrowing_design.json`
- `analysis/battery_conductivity_implementation.json`
- `analysis/battery_conductivity_release_freeze.json`
- `analysis/battery_conductivity_source_freeze.json`
- `analysis/battery_conductivity_benchmark_freeze.json`
- `analysis/run_battery_conductivity_borrowing.py`
- `analysis/verify_battery_conductivity_borrowing.py`

If the following files exist, the Balam run has completed and they must be
included in the assessment:

- `analysis/results/battery_conductivity_formal_summary.json`
- `analysis/results/battery_conductivity_complete.json`
- `analysis/results/battery_conductivity_checksums.sha256`

If they do not exist, explicitly mark the battery result as pending. Do not
infer its outcome and do not recommend changing its frozen endpoint, OOD split,
control family, or success gate after outcome access.

## Current evidence that must be reconciled

The review must explain, rather than hide, the following pattern:

- A neighboring-temperature, within-campaign experiment gives a 15.02% RMSE
  reduction with positive absolute prediction.
- Generic donor-feature injection across eight targets and forty real edges
  does not pass the complete OOD-repair gate.
- State and endpoint alignment recover a strong alloy cross-property result:
  reported processing/testing state improves the hard-OOD target model, and a
  cross-fitted predicted tensile-strength feature adds a further approximately
  9.21% Q4 RMSE reduction over the state-aware target-only model, while the
  matched shuffled donor does not reproduce the gain.
- Cross-database ionic-conductor rankings identify complementary high-value OOD
  regions in the Caltech recipient, but adaptive refitting does not preserve
  that benefit.
- Outcome-unseen Starrydata and oxygen-evolution targets do not pass their
  complete gates; they define heterogeneity and abstention rather than positive
  replication.
- A strong optical source model does not rescue scaffold-OOD photocatalysis;
  the focused development programme correctly abstains.
- In the external optical-to-organic-photovoltaic test, the real optical card
  gives only about 0.4% relative RMSE improvement over the state-aware
  target-only model, fails the practical-effect gate, and does not beat the
  matched shuffled optical card. It is therefore not a successful
  cross-database predictive edge.

Check every numerical statement against the repository before using it.

## Scientific questions you must answer

### 1. What is the strongest defensible scientific claim?

Separate and evaluate:

1. transfer of a pooled coefficient or “law”;
2. donor-derived feature improvement of OOD prediction;
3. cross-database transfer versus within-resource cross-property borrowing;
4. fixed donor ranking for OOD exploration;
5. adaptive acquisition or discovery acceleration;
6. prospective scientific discovery.

State exactly which levels are already established, which are only
component-level feasibility, and which remain unsupported. Recommend the
strongest title-level claim that does not collapse into an overly conservative
negative paper.

### 2. Is “neighboring domain” defined scientifically enough?

Audit whether adjacency is currently defined independently of target outcomes.
Propose an operational, outcome-blind donor-recipient compatibility contract
that could be reused by other researchers. Consider at least:

- shared material identity or representational support;
- shared experimental state variables;
- endpoint/mechanism relationship;
- source-model skill and uncertainty;
- local support at each candidate, not only global source credibility;
- publication and sample provenance;
- directionality;
- whether the transfer object is a model feature, residual prior, ranking, or
  hypothesis generator.

Do not merely propose a learned “distance” that is trained on the same target
outcomes it is supposed to predict.

### 3. Is the positive gain truly borrowed knowledge?

For each headline positive edge, test alternative explanations:

- extra feature capacity;
- composition or publication leakage;
- donor and recipient labels derived from the same record;
- processing-state confounding;
- repeated chemical families or connected provenance components;
- target-model weakness;
- regression-to-the-mean or support selection;
- post-outcome method selection;
- seed-level rather than dataset-level inference.

Specify the exact ablation or falsifier that distinguishes transferred
scientific information from these alternatives.

### 4. How should the transfer method be improved?

Do not answer “try a GNN/Transformer” without a causal reason and a matched
test. Compare scientifically motivated alternatives to scalar donor-feature
injection, such as:

- cross-fitted residual or adapter transfer;
- state-conditioned donor cards;
- candidate-local applicability or mixture-of-experts gating;
- uncertainty-aware shrinkage or conformal abstention;
- multi-task representation learning with missing labels;
- physically structured latent variables;
- source-rank preservation when calibration is unreliable;
- multi-source portfolios that reward distinct chemical regions rather than
  duplicate entities.

For every recommended method, state what failure in the existing evidence it
addresses, the risk of negative transfer, the required control, and the
criterion by which it would replace the current method.

### 5. What are the three highest-value next experiments?

Rank proposals by expected scientific information gain, not by how likely they
are to produce a positive result. Include:

- one reanalysis using existing data only;
- one genuinely independent or temporal cross-database predictive test;
- one prospective or laboratory-facing test only if it is necessary for the
  desired claim.

For each proposal give:

- donor and recipient;
- physical hypothesis;
- exact endpoint;
- outcome-blind eligibility rule;
- OOD construction and independent sampling unit;
- target-only and standard transfer baselines;
- shuffled, wrong-domain, equal-capacity, and state-ablation controls as
  applicable;
- primary estimand and practical-effect threshold;
- multiplicity family;
- minimum data and approximate compute requirement;
- what positive, null, and harmful outcomes would each mean for the paper.

Also identify analyses that should *not* be run because they would be
post-outcome target shopping, redundant, or incapable of changing the claim.

### 6. Does the statistical evidence support the manuscript hierarchy?

Audit:

- cluster/bootstrap units and dependence;
- small numbers of independent datasets or programmes;
- multiple comparisons across edges, endpoints, budgets, models, and OOD
  definitions;
- practical effect sizes versus small but statistically detectable gains;
- positive absolute OOD utility, not only relative improvement over a bad
  baseline;
- uncertainty from target programmes rather than repeated seeds alone;
- whether negative and abstaining edges remain in the denominator;
- whether compensation-law and Krug-artifact conclusions are appropriately
  bounded.

Recommend a target-level or programme-level synthesis that does not pretend
that 118 catalogued resources are 118 independent transfer trials.

### 7. What would make this publishable and influential?

Distinguish:

- minimum changes needed for a defensible *Digital Discovery* paper now;
- the one claim-upgrade experiment with the highest payoff;
- longer-term work needed for a stronger general or prospective claim.

Evaluate novelty relative to materials transfer learning, multi-task learning,
multi-fidelity optimization, task-similarity/meta-learning, experimental
database integration, and negative-transfer/abstention work. Verify citations;
do not invent references.

## Required response format

Respond in Chinese, retaining English technical terms where useful.

1. **One-paragraph scientific verdict**: reject / major revision / minor
   revision / accept, with the strongest currently supportable claim.
2. **Claim-evidence matrix**: each central claim, evidence for it, strongest
   alternative explanation, status, and exact resolution test.
3. **Fatal and major scientific weaknesses**: severity, file/evidence pointer,
   specific fix, and whether it requires new data, compute, reanalysis, or
   reframing.
4. **Method-improvement table**: proposed transfer mechanism, why it should
   help, negative-transfer risk, required control, and decision gate.
5. **Ranked next-experiment plan**: no more than five items, with the top three
   clearly marked.
6. **What not to do**: analyses that would add volume but not evidence.
7. **What would change your mind**: a concrete acceptance threshold.
8. **Recommended final scientific storyline**: one title, one central
   hypothesis, and a six-step evidence chain.

Do not give a review dominated by grammar, formatting, or figure aesthetics.
Do not demand every conceivable experiment. Identify the smallest decisive
set. Do not erase positive evidence merely because transfer is selective, but
do not relabel retrospective ranking as predictive accuracy, adaptive
acceleration, or prospective discovery.
