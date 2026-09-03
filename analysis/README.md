# Analysis workflow

This directory contains the protocols, deterministic analyses, claim-bearing
outputs and publication figures for the knowledge-borrowing study.

> **Current submission alignment:** use [`paper/README.md`](../paper/README.md)
> for the article-facing allowlist and the distinction between the formal
> SolventSeg rank contrast (0.885 versus 0.162) and the separate 13-model
> pressure test (0.910 versus 0.537). Older narrative documents below are
> retained for provenance and may predate the current Word submission.

The experimental-catalyst attention model, pinned data contract, transfer
benchmarks, ablations, audit results, and exact reproduction commands are in
[`CATALYST_ATTENTION_TRANSFORMER.md`](CATALYST_ATTENTION_TRANSFORMER.md).
The frozen CrabNet, Perceiver, TabPFN-v2, and expert-disagreement comparison is
in
[`ADVANCED_CATALYST_MODEL_COMPARISON.md`](ADVANCED_CATALYST_MODEL_COMPARISON.md).
The KL-Shampoo, Adam-grafting, per-sublayer Multi-Head Attention Residual, and
unlabelled-domain-alignment experiments are in
[`CATALYST_KL_SHAMPOO_MHAR_RESULTS.md`](CATALYST_KL_SHAMPOO_MHAR_RESULTS.md).
No candidate passed both frozen catalyst transfer gates; Delta-MHAR is retained
as a complementary research expert rather than the universal default.
The shadow-only On-Policy Distillation implementation for a target-label-free
language-model expert router is documented in
[`CATALYST_OPD_ROUTER.md`](CATALYST_OPD_ROUTER.md). It retains the numerical
experts, fails malformed decisions closed to abstention, and makes no
scientific-effect claim without a stronger held-out teacher and a new sealed
programme.
The two gated SFT cold-start attempts and the decision not to run OPD with the
failed 360M teacher are recorded in
[`OPD_SFT_COLD_START_RESULT.md`](OPD_SFT_COLD_START_RESULT.md).
The subsequent 34-edge Ridge-router screen, including strict leave-one-suite
and leave-one-donor evaluation, is recorded in
[`NUMERIC_EXPERT_ROUTER_RESULT.md`](NUMERIC_EXPERT_ROUTER_RESULT.md). It failed
both frozen benefit gates and remains shadow-only.

## Current manuscript entry points

- `MANUSCRIPT_DRAFT_STREAMLINED.md` — the current four-step main-text
  argument, restricted to the generic-transfer failure, controlled catalyst
  relation transfer, external unseen-salt prediction, cross-programme
  candidate ordering, and the frozen recipient boundary.
- `PAPER_PACKAGE.md` — canonical title, abstract, evidence hierarchy, safe
  claims, and four-figure architecture.
- `CORE_STORY_EVIDENCE_SELECTION_2026-07-30.md` — explicit record of what
  remains in the main text and what has been moved to the Supplementary
  Information.
- `CORE_STORY_TERMINOLOGY_LEDGER_2026-07-30.md` — canonical terms and
  abbreviations used throughout the manuscript.

The longer list below is a reproducibility index, not the recommended
main-text narrative. Completion of an analysis does not by itself justify a
main-text showcase.

## Evidence order

1. `audit_snapshot.py` — data lake, signed-value and identity audits.
2. `run_confirmatory.py` — corrected original compensation, OBELiX, molecular
   and search controls.
3. `knowledge_map_design.json` + `run_knowledge_map.py` — internally frozen
   nine-target candidate-edge map.
4. `refine_candidate_permutations.py` — uniform 999-permutation refinement of
   all five discovery-selected edges.
5. `external_confirmation_design.json` + `run_external_confirmation.py` —
   independent BIRDSHOT rolling-time confirmation.
6. `run_external_sensitivities.py` — explicitly post-confirmation budget and
   interpolation diagnostics.
7. `matbench_steels_confirmation_design.json` +
   `run_matbench_steels_confirmation.py` — independent steel-target negative
   boundary using the official Matbench folds.
8. `kit_temperature_borrowing_design.json` +
   `run_kit_temperature_borrowing.py` — frozen formulation-grouped local rescue,
   temperature-distance controls, shuffled-source placebo, and label
   equivalence.
9. `run_kit_sample_equivalence_uncertainty.py` — explicitly post-outcome
   formulation/subset uncertainty diagnostic for the target-label equivalence;
   it cannot redefine the frozen decision.
10. `calisol_external_borrowing_design.json` +
   `run_calisol_external_borrowing.py` — frozen article-disjoint external
   boundary for the KIT rescue logic, with exact-chemistry exclusions,
   article-hierarchical uncertainty, distance controls, and placebo.
11. `STRENGTH_LAW_SPEC.md` + `run_strength_law_external.py` — direct-law
   transport test.
12. `ISODB_ISOSTERIC_SPEC.md` + `run_isodb_isosteric.py` — streamed matched-
   loading compensation and Krug null.
13. `run_isodb_universality.py` — post-primary family-conditioning diagnostic.
14. `OOD_DECISION_BORROWING_SPEC.md` + `ood_decision_borrowing_design.json` +
    `run_ood_decision_borrowing.py` — frozen fixed-ranking OOD screening test.
15. `hard_ood_composition_design.json` + `run_hard_ood_composition.py` —
    explicitly exploratory composition-distance stress test.
16. `obelix_ood_discovery_design.json` +
    `write_obelix_ood_discovery_input.py` +
    `run_obelix_ood_discovery.py` — frozen sequential RF-UCB experiment on the
    official OBELiX test pool, with paired target-only, thermoelectric-prior,
    shuffled-prior and uniform-random strategies. The completed Balam run is
    verified by `verify_obelix_ood_discovery_results.py`; the post-result policy
    diagnostic is isolated in `analyze_obelix_ood_discovery_diagnostics.py`.
17. `neighbor_transfer_methods_design.json` +
    `analyze_neighbor_transfer_signals.py` — explicitly post-result signal
    anatomy separating target mean, ensemble spread, source rank and composition
    novelty. `neighbor_transfer_policy_design.json` and
    `run_neighbor_transfer_policy_benchmark.py` freeze the next exploratory
    policy benchmark for independent-method selection;
    `audit_neighbor_transfer_policy_results.py` verifies attribution against the
    valid novelty baseline. These files cannot redefine the completed OBELiX
    null.
18. `caltech_ionic_external_policy_design.json` +
    `caltech_ionic_external_policy_implementation.json` +
    `run_caltech_ionic_external_policy.py` — outcome-frozen independent
    Li-ion-conductivity target with article/composition leakage removal,
    composition-novelty baseline, cross-validated residual-rank gates, three
    wrong-source controls, cumulative-recall endpoint, and one explicitly
    exploratory novelty-band strategy. `audit_caltech_ionic_external_target.py`
    records the passed quality gates. Formal Balam Job 70740 and same-environment
    verification Job 70767 are complete; `verify_caltech_ionic_external_policy_results.py`
    and `audit_caltech_ionic_external_policy_results.py` establish a frozen
    adaptive-policy null, passed wrong-source suppression guards, and
    prespecified retrospective static-neighbor OOD signal.
19. `ood_knowledge_deficit_design.json` +
    `run_ood_knowledge_deficit_audit.py` +
    `verify_ood_knowledge_deficit_results.py` — post-outcome localization of
    the target-only OOD error surface and the selective neighbor increment by
    label budget, OOD quartile, learner, wrong source, and shuffled source. It
    cannot change the earlier frozen OBELiX screening or acquisition decisions.
20. `CORE_STORY_EXPERIMENT_MATRIX.md` +
    `core_story_experiment_registry.json` +
    `check_core_story_experiments.py` — the submission gate for the complete
    causal chain. Two outcome-unseen programmes completed as Balam Job 70888 and
    passed portable verification: (i) Starrydata reverse transport, with 7,403 entities, 745
    components, five source channels, ten complete policy orders, and three
    hypothesis cards; and (ii) the clean four-set TRI OER benchmark, with 8,447
    entities, 240 composition clusters, five source channels, ten complete
    per-set policy orders, and three hypothesis cards. The originally nominated
    acid-OER target failed its outcome-free per-plate size gate after immutable
    accidental-access exclusions and is sensitivity-only. The two pre-outcome
    verifiers are mandatory sentinels; smoke runs are explicitly non-claim
    checks. `analysis/balam/run_core_story_outcome_unseen_balam.sh` executed all
    prediction, specificity, robustness, policy, card, and multi-target tests.
21. `synthesize_knowledge_map.py` — layered map evidence, endpoint-specific
    outcomes and claim boundaries.
22. `make_data_foundation_figure.py` — complete 21-resource role inventory,
    integrated measurement scale, explicit directed-evidence denominator, and
    all-program evidence portfolio.
23. `make_main_knowledge_map_figure.py` — editable SVG/PDF and high-resolution
    raster exports with panel-level source CSVs.
24. `make_ood_decision_figure.py` — fixed-screening and sequential-discovery
    decision figure, including the uniform-random policy reference.
25. `make_caltech_external_policy_figure.py` — external decomposition of
    selective neighbor admission, null adaptive source increments, and
    prespecified retrospective static-ranking evidence.
26. `make_outcome_unseen_validation_figure.py` — target-level effects,
    conjunctive gates, learner/representation heterogeneity, and all six
    prewritten hypothesis-card outcomes for Starrydata and TRI.
27. `write_release_manifest.py` — final hashes for the database, frozen
    designs, compact claim outputs, panel source data and figure bundle.
28. `specgen_derivative_oer_borrowing_design.json` +
    `run_specgen_derivative_oer_borrowing.py` +
    `run_specgen_composition_secondary.py` — complete-system OER perturbation
    series, source-shuffle falsifiers, and five-label relation-plus-residual
    borrowing. `run_specgen_top20_temporal_check.py` retains the later selected
    candidates as ranking corroboration only, and
    `verify_specgen_derivative_results.py` independently checks the compact
    release.
29. `bamboomixer_cross_database_interaction_design.json` +
    `run_bamboomixer_cross_database_interaction.py` — post-outcome,
    overlap-aware interaction among separately fitted BambooMixer, CALiSol and
    KIT conductivity programmes on SolventSeg and FINALES. The route separates
    numerical calibration from ordinal screening.
    `verify_bamboomixer_cross_database_interaction.py` independently
    recalculates the formal release.
    `run_bamboomixer_recipient_baseline_stress_test.py` challenges the
    five-label rank result with 13 recipient-only configurations and a
    non-deployable per-draw oracle; its summary and alignment are independently
    verified.

Final composite figure generators:

- `make_neighbor_map_exploration_figure.py` — combined qualification,
  adaptive-null, static-ranking, and family-first distinct-region figure.
- `make_battery_continuous_borrowing_figure.py` — protected temporal design,
  controlled continuous-borrowing contrasts, condition selectivity, gate
  coverage, and source-inspired condition cards.
- `make_bamboomixer_cross_database_interaction_figure.py` — source overlap,
  equal-programme construction, recipient-only stress test, paired rank
  contrasts, calibration abstention, and FINALES programme boundary.

## Primary claim-bearing files

- `results/strength_law_summary.json`
- `results/knowledge_map_edges_refined.csv`
- `results/external_confirmation_edges.csv`
- `results/matbench_steels_external_summary.json`
- `results/kit_temperature_summary.json`
- `results/kit_temperature_edges.csv`
- `results/kit_sample_equivalence_uncertainty.json`
- `results/calisol_external_summary.json`
- `results/calisol_external_edges.csv`
- `results/knowledge_map_synthesis_summary.json`
- `results/isodb_compensation_summary.json`
- `results/isodb_universality_summary.json`
- `results/ood_decision_summary.json`
- `results/hard_ood_decision_summary.json`
- `results/obelix_ood_discovery_summary.json`
- `results/obelix_ood_discovery_diagnostics.json`
- `results/neighbor_transfer_signal_summary.json` (post-result method diagnostic;
  not a new claim-bearing OBELiX result)
- `results/neighbor_transfer_policy_summary.json` and
  `results/neighbor_transfer_policy_validation.json` (post-result exploratory
  method selection; not a new claim-bearing OBELiX result)
- `results/caltech_ionic_external_policy_summary.json`,
  `results/caltech_ionic_external_policy_contrasts.csv`, and
  `results/caltech_ionic_external_policy_validation.json` (verified external
  adaptive-policy null and negative-transfer safety result)
- `results/caltech_ionic_external_policy_VERIFIED.json` (formal and
  same-environment verification jobs and release hashes)
- `results/caltech_neighbor_portfolio_diagnostic.csv` (post-result method
  selection only; not a confirmed source-to-policy edge)
- `results/ood_knowledge_deficit_summary.json` and
  `results/ood_knowledge_deficit_VERIFIED.json` (post-outcome conditional OOD
  localization; not an independent target replication)
- `CORE_STORY_EXPERIMENT_MATRIX.md` and
  `core_story_experiment_registry.json` (authoritative list of completed and
  submission-blocking core-story experiments)
- `results/starrydata_reverse_PREOUTCOME.json`,
  `results/starrydata_reverse_policy_orders.csv`, and
  `results/starrydata_reverse_hypothesis_cards.csv` (outcome-free freeze, not a
  target-result claim)
- `results/tri_oer_PREOUTCOME.json`, `results/tri_oer_policy_orders.csv`, and
  `results/tri_oer_hypothesis_cards.csv` (clean four-set OER pre-outcome freeze,
  not a target-result claim)
- `results/starrydata_reverse_VALIDATED.json`,
  `results/tri_oer_VALIDATED.json`, and
  `results/outcome_unseen_multi_target_summary.json` (portable verification of
  the complete reverse-target, second-family, and cross-target boundary)
- `results/local_gated_neighbor_portfolio_summary.json` (failed multiplicative
  local-gate method development; retained as a negative design result)
- `results/family_first_neighbor_portfolio_summary.json`,
  `results/family_first_neighbor_portfolio_metrics.csv`, and
  `results/family_first_neighbor_hypothesis_cards.csv` (outcome-informed CCA
  family-first breadth analysis; not independent confirmation)
- `results/multistage_battery_stage2/STAGE2_RELEASE_AUDIT.json` and the
  `multistage_battery_stage2_coverage_sensitivity` summaries (non-evaluable
  frozen primary plus disclosed continuous-borrowing method development)
- `results/specgen_composition_secondary_summary.json`,
  `results/specgen_top20_temporal_summary.json`, and
  `results/specgen_derivative_verification.json` (verified controlled
  derivative-system transfer and temporal ranking boundary)
- `results/bamboomixer_cross_database_interaction_summary.json` and
  `results/bamboomixer_cross_database_interaction_verification.json`
  (verified post-outcome cross-database ranking route with numerical
  abstention)
- `results/bamboomixer_recipient_baseline_stress_test_summary.json` and
  `results/bamboomixer_recipient_baseline_stress_test_verification.json`
  (13-model recipient-only sensitivity and oracle-envelope comparison)
- `figures/specgen_derivative_oer_transfer.pdf`
- `figures/data_foundation_scope.pdf`
- `figures/main_knowledge_borrowing.pdf`
- `figures/ood_decision_borrowing.pdf`
- `figures/neighbor_map_exploration.pdf`
- `figures/outcome_unseen_validation.pdf`
- `figures/battery_continuous_borrowing.pdf`
- `figures/cross_database_electrolyte_ranking.pdf`
- `results/manifest.json`

The paper-facing author draft and reporting companion are
`MANUSCRIPT_DRAFT_STREAMLINED.md` and `SUPPLEMENTARY_INFORMATION.md`. Manuscript
positioning, terminology constraints, and verified citations are in
`PAPER_PACKAGE.md`, `TERMINOLOGY_LEDGER.md`, `RELATED_WORK.md`,
`REFERENCES.bib`, and `CITATION_VERIFICATION.md`. Figure layout and statistical
QA are recorded in `DATA_FOUNDATION_FIGURE_CONTRACT.md`,
`DATA_FOUNDATION_FIGURE_QA.md`, `FIGURE_CONTRACT.md`, and `FIGURE_QA.md`.
The controlled OER figure has a dedicated contract and export/statistical audit
in `SPECGEN_DERIVATIVE_FIGURE_CONTRACT.md` and
`SPECGEN_DERIVATIVE_FIGURE_QA.md`.
The remaining adversarial reviewer risks are consolidated in
`PRESUBMISSION_REVIEW.md`.

Large per-prediction files are ignored by git and reproducible from the scripts.
Compact summaries, protocols and figure source data should be versioned.

## Interpretation rules

- `internally-selected-candidate` means the edge passed its internal screen but
  was selected from that screen and lacks external replication with positive
  absolute utility.
- `directionally-replicated-below-practical-gate` means the independent effect
  is statistically positive and learner/temporal directions agree, but at
  least one frozen practical gate failed.
- `exploratory-positive` is not confirmatory evidence.
- `practically-equivalent`, `harmful` and `unresolved` remain visible in the
  audited inventory; they are not discarded.
- Post-outcome diagnostics and sensitivities cannot redefine primary success.
- `within-campaign-local-neighbor-rescue-gate-passed` means every originally
  specified frozen KIT point-rule
  practical-effect, uncertainty, absolute-utility, fold, learner, source,
  leakage, permutation, learning-curve, distance, and placebo gate passed. It
  does not mean an uncertainty-qualified 30% saving lower bound,
  independent-dataset rescue, or field-level rescue. The post-outcome
  formulation/subset diagnostic spans 21.84–49.91% saved.
- `cross-article-borrowing-unresolved` means the frozen CALiSol edge did not
  satisfy the repeated-effect, practical, absolute-utility, article-fold,
  sample-saving, and adjacency gates. A small p value for one fixed
  permutation subset is insufficient to override those failures.
- `directional OOD screening signal` means a frozen fixed-ranking test has a
  positive paired effect, but consistency, practical-effect or absolute-utility
  gates prevent an OOD-improvement or rescue claim.
- Fixed-ranking OOD screening and sequential discovery are separate endpoints.
  On the official OBELiX pool, thermoelectric-prior RF-UCB saves only 0.25
  acquisitions [−1.30,1.82] and fails every frozen improvement/rescue gate.
- The exploratory hard-OOD subset is directionally positive but fails the
  5-experiment, 25%, 60%-seed and Random-Forest sensitivity gates. It cannot
  redefine the frozen official-test conclusion.
- Uniform random acquisition is a prespecified policy reference, not a borrowing
  success criterion. Its substantially earlier hits diagnose failure of the
  tested RF-UCB policy on this finite pool; they do not identify whether mean
  ranking, uncertainty calibration or iterative refitting is responsible, and
  do not establish random search as generally optimal.
- The post-result signal anatomy shows that positive ensemble spread bonuses
  steer the tested maximization policy toward lower-valued candidates, whereas
  direct source rank and composition novelty contain early-hit information.
  Because those methods were selected after seeing OBELiX outcomes, they are
  candidate methods for independent validation, not evidence that changes the
  frozen sequential decision.
- The completed post-diagnostic policy benchmark validates composition novelty
  against random, but does not isolate a neighbor-source increment beyond that
  baseline. Source-aware fusion improves official-pool cumulative recall only
  in a post-hoc secondary comparison and does not reproduce that advantage in
  hard OOD. It is a candidate for external method validation, not a discovery
  claim.
- The verified Caltech external benchmark is null for every frozen adaptive
  source increment. Its admission rule admits and weights OBELiX and ESTM more
  often than mechanical, catalysis, and shuffled controls, while all wrong-
  source harm guards pass. This is not an ordering of source skill: source OOF
  R² is 0.065 for OBELiX, 0.257 for ESTM, and 0.543 for the OCx control. The
  adaptive null cannot isolate source weakness from policy conversion.
- Prespecified OBELiX and ESTM static rankings exceed random and all wrong-source
  static references in both Caltech scopes after composition and DOI overlap
  removal. This is prespecified retrospective external signal. Static-source
  attribution gates and dataset-level replication intervals were not in the
  frozen primary family, so it is not an independently confirmed policy edge.
- The Caltech neighbor round-robin and consensus portfolios cover 5/8 external
  top entities versus 2/8 and 3/8 individually, demonstrating source
  complementarity on the observed target. They were constructed after
  inspecting outcomes, so they select the next target-model-free policy for a
  new frozen target rather than establish prospective acceleration on Caltech.
- CCA family-first consensus changes the objective from repeated entity hits to
  first recovery of distinct formula/DOI/ICSD components. It recovers 4/4 top
  external and 2/2 hard-OOD components by acquisition 20, with shuffled-rank
  conditional p=0.0020/0.0030, but reduces entity recall. This is an outcome-
  informed breadth strategy for an unseen target, not a generic ML improvement
  or a prospective Caltech discovery.
- The failed multiplicative local gate is part of the evidence: target OOD,
  source support, and local concordance reduced external AUC20 to 0.96 versus
  69 for static entity consensus. OOD should constrain a portfolio budget, not
  automatically multiply source evidence.

## Verified multi-target OOD borrowing benchmark

`MULTI_TARGET_OOD_BORROWING_PROTOCOL.md` defines the systematic test of the
paper's OOD-repair hypothesis. It reuses eight eligible recipient tasks and all
40 inherited real donor edges, adds eight shuffled-donor controls, and compares
Q4 OOD gain with Q1 ID gain under three fixed recipient learners. A designated
edge must improve OOD error, improve more in OOD than ID, retain positive
absolute OOD utility, beat fixed wrong and shuffled donors, survive learner
sensitivity and Holm correction, and remain identity-disjoint.

The formal run is complete and independently reconstructed. It contains eight
targets, seven programme clusters, 40 real edges, eight shuffled controls,
43,200 metric rows, 14,400 paired-contrast rows, and 63,600 group-error rows.
The strongest designated edge, alloy UTS→YS, reduces Q4 OOD RMSE by 6.65%
[3.53,14.02%] but reduces Q1 error by 7.74% and retains augmented Q4
R²=−0.666. No designated edge passes the complete OOD-repair gate; the
seven-programme mean is +0.92% [−0.35,2.92%], and 0/3 designated
cross-database edges pass.

The protocol was frozen before the unified run but after earlier component
outcomes had been inspected. It is therefore a systematic post-outcome
method-development benchmark, not prospective confirmation. Smoke outputs use
the `multi_target_ood_smoke_*` prefix and are never claim-bearing. The formal
`multi_target_ood_VERIFIED.json` package is the manuscript-authoritative result.

## Reproduce

Run from the repository root using the environment in
`analysis/requirements.txt`. The complete command sequence is listed in the
top-level README. The ISODB archive is downloaded to the user cache, verified
against the pinned SHA-256, streamed in memory and never extracted.

## Current claim boundary

The analysis instantiates an artifact-gated knowledge-borrowing map and a
selective strategy for qualifying, preserving, and combining neighboring
signals. A frozen adjacent-temperature electrolyte edge materially improves few-shot
error and passes the operational local-task-rescue table status for a simulated
label-poor within-campaign target, with uncertain label-saving magnitude. The paper-
disjoint CALiSol replication does
not reproduce rescue or temperature-distance ordering; BIRDSHOT provides
directional external replication without absolute utility, and Matbench
provides an independent null. This sparse mixture of positive, null, harmful,
and unresolved edges is the empirical content of the map; it is not a universal
distance law. The ordinal cross-domain neighborhood score and independent
cross-campaign or multi-domain rescue remain unconfirmed. Frozen fixed-ranking OBELiX screening is directional but below its
practical and consistency gates, while the completed sequential experiment is
null on the official pool. Thus average prediction, fixed OOD screening and
sequential discovery remain distinct decision endpoints. The independent
Caltech benchmark shows that OBELiX and ESTM neighbor rankings recover 2/8 and
3/8 external top entities after formula and DOI exclusions, whereas mechanical
and catalysis controls recover 0/8. A post-outcome portfolio recovers 5/8 and
demonstrates complementarity. CCA family-first allocation additionally recovers
4/4 distinct top external components and both 2/2 hard-OOD components while
deferring repeated members of one component; adaptive residual injection
remains null. The integrated policy was then tested on two outcome-unseen
targets. Starrydata gives a small +0.88% [0.02,1.77%] direction but fails
multiplicity and absolute utility; the four-plate TRI OER effect is -0.079%
[-0.313,0.155%]. Their random-effects mean is +0.304%
[-0.617,1.225%], I²=76.7%, and neither target passes its complete gate. These
results provide component-level proof that neighboring domains can improve
prediction and produce useful OOD proposals when the signal is preserved, plus
outcome-unseen evidence that the map must abstain or reject other proposed
edges. Prospective discovery remains unestablished. See
`PAPER_PACKAGE.md` for the manuscript-safe and unsafe claims.
