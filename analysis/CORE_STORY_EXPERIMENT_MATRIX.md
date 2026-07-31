# Core-story experiment matrix

## Purpose

The paper's primary claim is that qualified neighboring experimental knowledge
can reduce target-domain scarcity on selected few-shot or out-of-distribution
(OOD) edges, while an artifact-gated map identifies null, harmful, or endpoint-
specific edges and abstains elsewhere. This file is the submission gate for that
selective claim. An experiment is not dispensable merely because a related
diagnostic or null is already available.

The evidence chain is complete only when it tests all of the following without
dropping null or harmful outcomes:

1. the target-only knowledge deficit exists and increases with OOD distance or
   label scarcity;
2. whether neighboring information adds value beyond a strong target-only model;
3. whether any increment is specific to the nominated neighbor rather than leakage,
   source size, model skill, or extra model capacity;
4. whether the result is tied to one learner, representation, target, or OOD
   definition;
5. whether any remote-region gain is specifically larger in OOD than ID and
   produces positive absolute OOD utility;
6. whether complementary sources improve breadth beyond the best single source and
   standard transfer baselines;
7. whether the complete policy works on outcomes that did not inform its design; and
8. whether a source-derived candidate-region hypothesis written before
   the target outcome is revealed; and
9. whether an outcome-free gate trained without a target programme can select
   useful edges at non-trivial coverage rather than merely exclude obvious
   wrong sources.

`core_story_experiment_registry.json` is the machine-readable authority.
`check_core_story_experiments.py --require-complete` must fail while any
submission-blocking item remains incomplete.

## Submission-blocking matrix

| ID | Experiment | Why the main claim needs it | Current evidence | Status | Exact completion criterion |
|---|---|---|---|---|---|
| CS01 | OOD knowledge-deficit surface | The manuscript must show the problem it claims to solve: target-only error should be quantified jointly over label budget and outcome-free OOD distance. | Formal OBELiX diagnostic: five budgets, four dynamic OOD quartiles, one fixed hard-OOD scope, 100 repeats, ExtraTrees and Random Forest, real/wrong/shuffled sources. | **complete** | At n=30 the far-minus-near target-only RMSE gap is 0.373 [0.047,0.669], error–distance Spearman is 0.097 [0.049,0.144], and the thermoelectric source reduces far-OOD RMSE by 3.95% [2.65%,5.26%], 1.29 percentage points [0.21,2.40] beyond the best control. These are conditional post-outcome intervals. |
| CS02 | Leakage-safe few-shot neighbor increment | Establishes that a qualified neighbor can reduce target error under scarce labels. | KIT −20→−30 °C: 15.02% RMSE reduction, positive absolute R², grouped formulation split, distance controls, shuffled placebo. | **complete** | Existing frozen KIT gates remain reproducible. |
| CS03 | Independent positive predictive replication | One within-campaign positive cannot support a general OOD-knowledge claim. Null replications define a boundary but do not supply a second positive target. | The formal test is complete. Starrydata has a +0.88% hierarchical effect [0.02%,1.77%] but Holm p=0.071 and R²=−0.485; TRI OER is −0.079% [−0.313%,0.155%], with 0/4 plates at positive absolute R². | **complete-boundary** | The prespecified positive criterion was not met. The experiment is complete, but independent positive predictive replication remains unsupported and may not be claimed. |
| CS04 | Matched source-specificity controls | Wrong and shuffled sources are necessary but may differ in size, coverage, or source-model skill. | Formal source-size, source-skill, target-coverage, frozen-shuffle, and equal-capacity controls were retained. Starrydata's hierarchical neighbor-minus-best-control contrast is +0.75% [−0.14%,1.66%], Holm p=0.096; TRI all-neighbor minus best control is −1.25% [−1.75%,−0.75%]. | **complete-boundary** | Completed without dropping unfavorable controls; no target passes the complete specificity decision family. |
| CS05 | Learner and representation robustness | RF plus element composition can mistake one representation's geometry for transferable science. | All 12 target-by-learner-by-representation summaries are reported. Starrydata is positive in five of six cells and passes the frozen envelope; TRI changes sign by representation and has strongly negative Ridge effects. | **complete-boundary** | Complete heterogeneity report; robustness cannot rescue failed multiplicity or absolute utility. |
| CS06 | Standard transfer baselines | The proposed policy must beat credible alternatives, not merely a weak target surrogate. | Target-only, naive standardized pooling, source-only calibration, frozen stacking, residual shrinkage, mixture-of-experts, wrong, shuffled, random-feature, best-single, novelty, and CCA baselines were all evaluated in the formal runs. | **complete-boundary** | All named baselines retained; neither target passes the full comparative gate. |
| CS07 | Endpoint-separation falsification | Prediction, fixed screening, breadth, and adaptive acquisition are different claims. | OBELiX fixed-ranking direction, failed UCB campaign, random/novelty controls, and Caltech adaptive residual null. | **complete-boundary** | Preserve all nulls and prevent fixed-screening results from being relabelled as adaptive acceleration. |
| CS08 | Multi-source complementarity and family-first ablation | The map's actionable contribution is broader OOD-region coverage, not one lucky source hit. | Starrydata CCA AUC20=41, below same-domain ESTM=71; its source-rank permutation p=0.546. Across TRI plates, every CCA exploration contrast has Holm p=1.0. Entity, component, first-hit, wrong, shuffled, novelty, and single-source endpoints are retained. | **complete-boundary** | The complete policy test is reported and does not independently validate the outcome-informed Caltech portfolio. |
| CS09 | Outcome-unseen full-policy validation | This is the decisive protection against post-outcome method selection. | Balam Job 70888 completed the 7,403-entity Starrydata and 8,447-entity/four-plate TRI programmes; portable verifiers reproduce every row family, frozen artifact hash, endpoint, and boundary. | **complete-boundary** | Completed without replacing a target, plate, policy, source, learner, representation, or card after outcome access. |
| CS10 | Reverse-direction and second-domain replication | “Mutual inspiration” cannot be inferred from one direction or one ionic-transport target family. | The reverse direction has a small directional Starrydata interval but fails its full gate; the independent four-plate OER family is null. The acid-OER target remains sensitivity/source-only after its outcome-free quality failure. | **complete-boundary** | Both directed tests are complete; reciprocal or second-family positive transfer is not established. |
| CS11 | Prewritten scientific hypothesis and matched falsifier | A ranking becomes scientific inspiration only when it yields a testable, source-derived proposition before target reveal. | All three Starrydata and three TRI cards were tested against frozen matched controls. Starrydata Holm p values are 0.445, 1.0, 1.0; all TRI Holm p values are 1.0. | **complete-boundary** | All six cards and failures retained; no source-derived hypothesis is confirmed. |
| CS12 | Independent-unit and multi-target inference | Seed intervals from one fixed database do not quantify transport across science domains. | Two-target random-effects mean relative RMSE gain=+0.304% [−0.617%,1.225%], τ²=3.53×10⁻⁵, I²=76.7%; only one target is directionally concordant. | **complete-boundary** | Target-level effects and heterogeneity are complete; the pooled effect is null and cannot be called general transfer. |
| CS15 | Systematic multi-target OOD repair stress test | A donor can lower average error without repairing the recipient's remote knowledge deficit; OOD gain must exceed ID gain and yield positive absolute utility. | Formal Job 71429 retained eight targets, seven programme clusters, 40 real edges, eight shuffled controls, three learners, and 100 grouped draws. Alloy UTS→YS gives +6.65% [3.53%,14.02%] Q4 gain but +7.74% Q1 gain and Q4 R²=−0.666. | **complete-boundary** | No designated edge passes the complete OOD-repair gate; the seven-programme mean is +0.92% [−0.35%,2.92%], and 0/3 designated cross-database edges pass. Generic donor-feature injection is rejected within the tested envelope without erasing KIT or Caltech endpoint-specific evidence. |

## Cross-program method development

| ID | Experiment | Why it matters | Current evidence | Status | Exact completion criterion |
|---|---|---|---|---|---|
| CS14 | Leave-one-target-program borrowing gate | Tests whether credibility, compatibility, and abstention metadata learned on other programmes can select useful borrowing without target-program outcome leakage. | Independently reconstructed panel of 97 edges, 20 tasks, and 13 programme clusters. CCA mean utility is +1.58% [-0.23%,4.27%], with 11/13 programme coverage and 1/17 clearly harmful admissions. It retains 4/10 clear benefits and does not beat always-best credibility or never borrowing after Holm correction; adjacency-only is numerically stronger. | **method-development-complete** | The frozen v1 benchmark and verifier are complete. It establishes a safety/selection boundary, not an independently validated transfer policy. CCA-v2 must add candidate-local applicability and be tested on a new temporal or prospective programme. |

## Claim-upgrade experiment

| ID | Experiment | Required when | Status | Completion criterion |
|---|---|---|---|---|
| CS13 | Prospective or genuinely temporal candidate test | Required for “discovery acceleration”, “finds new science”, or laboratory-saving claims; not required for a retrospective methods/OOD-screening claim. | **missing** | Freeze source ranks and hypothesis cards before a new experimental/time block, test the nominated candidates and matched controls, and report cost, failures, and first-pass success without retrospective replacement. |

## Completed outcome-unseen target programme

Two targets are selected from metadata only in
`outcome_unseen_neighbor_validation_program.json`:

1. **Reverse transport target:** Starrydata2 thermoelectric measurements, with
   ESTM as a same-domain source and OBELiX/Caltech ionic-conductor data as the
   adjacent transport source. This tests whether the thermoelectric→ionic edge
   has a useful reverse direction and whether the adjacent source adds regions
   beyond the best same-domain source.
2. **Second scientific family:** the clean four-set Caltech/Toyota OER
   active-learning benchmark (DOI 10.22002/D1.1345), with same-reaction acid
   OER, adjacent ORR/OCx electrocatalysis, and mechanical/ionic controls. The
   initially nominated acid-OER target failed its outcome-free per-plate minimum
   after immutable accidental-access exclusions and is sensitivity-only. This tests whether the
   method extends beyond ionic/thermoelectric transport.

Selection of these targets did not predict that they would be positive. Both
formal programmes are complete. Neither passes the full prediction gate, so the
independent-positive-replication claim remains unsupported; the nulls and
abstentions stay in the map rather than being replaced by new targets.

## Non-negotiable reporting rules

- Report every target, source, learner, representation, OOD definition, and
  hypothesis card specified before outcome access.
- Use one primary endpoint per claim family and Holm correction over its named
  contrasts; exploratory endpoints cannot rescue a failed primary decision.
- Keep average prediction, high-OOD prediction, fixed screening, component
  breadth, and adaptive acquisition in separate columns and figures.
- Never use seed-to-seed variability as the only uncertainty for an external
  transport claim.
- A null or harmful source remains in the knowledge-borrowing map and triggers
  abstention; it is not removed from the denominator.
