# Discovery Report: Flagship experimental OOD knowledge-transfer case

**Date:** 2026-07-30

**Project ID:** 92532a0a-130d-4f42-a1ee-7866dc2d3fd3

---

## Research Objective

# Legacy Kosmos task: find and de-risk a flagship experimental OOD-transfer case

You are the lead scientist and adversarial methodologist for a materials-
informatics study. Your task is not to survey transfer learning broadly. Find,
verify, and de-risk one **genuinely compelling, executable flagship example**
in which knowledge learned from one open experimental database materially
improves prediction in a data-poor, out-of-distribution region of an
independent neighboring experimental domain.

Public project:
https://github.com/Yang1Bai/collective-exp-data-index

## Scientific thesis

When scientific understanding is incomplete, heterogeneous data aggregation
does not automatically reveal a universal law. However, neighboring
experimental domains may contain selectively transferable knowledge. The
portable object may be a mechanism-linked response relation, correction law,
low-dimensional physical parameter, or independent candidate ranking—not raw
pooled rows, generic pretrained weights, or an arbitrary donor prediction.

## Current evidence and the unresolved gap

The project contains 20 analyzed experimental resources. Generic donor-feature
injection repaired none of 40 designated OOD edges across eight targets.
Positive results exist but are not yet a decisive cross-database flagship:

- neighboring electrolyte temperatures within one campaign reduce few-shot
  RMSE by 15.02%;
- a state-matched alloy-property donor reduces a selected Q4 OOD RMSE by
  9.21%, but the properties largely share specimens/provenance;
- in literature-curated CALiSol, absolute cross-article transfer is unresolved
  (+1.61%). A post-outcome method that transfers within-article formulation
  response contrasts and uses one target-article anchor improves macro-RMSE by
  6.91% across 11 held-out articles;
- cross-database electrolyte donors improve retrospective candidate ranking in
  selected pools, but not global OOD numerical prediction;
- several genuinely external database pairs are null or harmful, including a
  deep molecular donor.

We therefore still lack one case that convincingly shows an independent
experimental database improving another database's true OOD prediction.

## Non-negotiable eligibility criteria

Both donor and recipient must:

1. contain downloadable numerical **experimental** measurements with stable
   paper/repository identifiers and legal reuse access;
2. come from independent databases, laboratories, publications, or experimental
   programmes—not two labels extracted from the same measurement event or the
   same batch of specimens;
3. expose a compatible input representation for recipient candidates
   (composition, molecule, formulation, structure, processing variables, or a
   justified crosswalk);
4. contain enough experimental-state metadata to avoid mixing incompatible
   temperature, pressure, electrolyte, synthesis, processing, or testing
   regimes;
5. support a defensible provenance-, time-, laboratory-, chemical-family-, or
   process-held-out OOD split. A random split or a nominal leave-one-element-out
   split that remains representational interpolation is insufficient;
6. have a mechanistic reason why a **relation, correction, parameter, or
   ranking** learned from the donor should transport to the recipient;
7. allow matched falsifiers: shuffled donor labels, an equally sized wrong
   donor, a wrong experimental condition, and target-only/state-aware
   baselines.

Reject DFT-to-DFT examples, proprietary/ICSD-dependent data, targets derived
algebraically from the donor label, unavailable supplementary files, same-row
proxy-label leakage, and cases whose only evidence is improved random-split
accuracy.

## What counts as a flagship success

Design for a result that could satisfy all of the following:

- independent donor and recipient sources;
- positive absolute OOD \(R^2\), not merely a less-negative score;
- at least approximately 15% macro-RMSE reduction relative to a strong,
  state-aware target-only model at a predeclared low-label budget or 1–3 target
  anchors;
- article/lab/family-cluster uncertainty interval with a lower bound above
  zero and multiplicity-aware \(p<0.05\);
- at least a 5 percentage-point advantage over an architecture- and
  size-matched shuffled/wrong donor;
- benefit in most independent OOD groups;
- replication in a second recipient database, second experimental programme,
  or locked secondary OOD region.

These are design targets, not permission to cherry-pick. A credible negative
assessment is preferable to an ineligible positive result.

## Search space

Search broadly across open experimental materials and chemistry repositories,
including but not limited to:

- ionic/electronic conductivity, diffusivity, viscosity, dielectric response,
  and battery rate or low-temperature performance;
- optical absorption, experimental band gaps, frontier energy levels,
  photoluminescence, photovoltaic, photocatalytic, and OLED/device performance;
- adsorption, surface/electronic descriptors, and experimentally measured
  catalytic or electrocatalytic activity;
- mechanical properties, processing, microstructure, fatigue, fracture, and
  strength;
- polymer, electrolyte, solubility, permeability, and transport datasets.

Prioritize pairs where the neighboring relation is known to be locally stable
but the absolute scale is shifted by laboratory or protocol, because these are
natural candidates for relation transfer plus few-shot provenance calibration.

## Required work

### Phase 1 — verified candidate discovery

Find at least ten plausible donor→recipient pairs. For every pair, verify:

- exact paper DOI and direct data/repository URL;
- experimental rather than computational status;
- download accessibility without subscription or private credentials;
- approximate row counts, independent publication/lab groups, target and donor
  columns, experimental conditions, identifiers, and license;
- common input representation and estimated recipient coverage;
- whether target outcomes are independent of donor labels;
- a concrete transfer object: response difference, derivative, transformation,
  physical parameter, residual correction, calibrated latent coordinate, or
  fixed ranking;
- a concrete true-OOD split and leakage unit;
- the strongest likely confound or fatal blocker.

Do not rank a pair highly until the data files and essential schema have been
inspected. Label unverified claims explicitly.

### Phase 2 — adversarial triage

Eliminate ineligible candidates. Produce a ranked shortlist of the best three
and score each from 0–5 for:

1. mechanistic adjacency;
2. independent provenance;
3. input/schema compatibility;
4. state metadata completeness;
5. target data scarcity and OOD relevance;
6. falsifiability and matched-control quality;
7. expected effect size;
8. computational feasibility;
9. publication value.

Give an explicit estimated probability that each candidate will pass the
flagship gate. Explain why the winner is more likely to succeed than the
project's previous generic donor injections.

### Phase 3 — winner audit and frozen test design

For the top candidate, perform an outcome-blind data audit where possible:

- retrieve and inspect the actual data files;
- compute entity, condition, publication/lab, and feature coverage;
- identify duplicate or shared-provenance leakage;
- define donor, recipient, OOD groups, common inputs, eligible sample counts,
  target-label budgets, and anchor-selection policy without examining the
  transfer outcome;
- state exactly which information is available at prediction time.

Then write a preregistration-ready experiment:

- primary estimand and independent unit;
- target-only and state-aware baselines;
- transfer model, including why the transferred object should survive
  provenance shift;
- nested/grouped cross-fitting;
- exact OOD split and prohibited leakage;
- matched wrong-donor, shuffled-donor, wrong-condition, and source-skill
  controls;
- primary and secondary metrics;
- clustered bootstrap/permutation tests and multiplicity correction;
- success, null, harm, and abstention gates;
- compute requirements and an executable implementation outline.

If accessible data permit, run only outcome-free schema/coverage checks and
small code smoke tests. Do not inspect the primary transfer outcome before the
design is frozen.

## Required output

Return:

1. a concise scientific conclusion;
2. a machine-readable candidate table;
3. the elimination log for rejected candidates;
4. the top-three scorecard;
5. exact verified data and paper links;
6. the complete frozen protocol for the winner;
7. a contingency plan for the second-ranked pair;
8. a section titled **What would make this result unpublishable?**

Do not substitute a generic methods review for verified, downloadable database
pairs. Do not claim success before a frozen test is executed.

---

## Dataset Description



---

## Summary of Discoveries

1. **[Residual-Correction OOD Transfer for Electrolyte Conductivity Is Fragile and Mechanism-Constrained](#discovery-1-residual-correction-ood-transfer-for-electrolyte-conductivity-is-fragile-and-mechanism-constrained)**

2. **[Cross-Database Transfer of Ordinal Formulation Rankings in Electrolyte Conductivity](#discovery-2-cross-database-transfer-of-ordinal-formulation-rankings-in-electrolyte-conductivity)**

3. **[Structured Triage, Contingency Execution, and Replication Hazards in Conductivity Transfer](#discovery-3-structured-triage-contingency-execution-and-replication-hazards-in-conductivity-transfer)**

4. **[Battery Aging: Strong Negative Transfer Across Independent Programs and Limits of Curve-Shape Portability](#discovery-4-battery-aging-strong-negative-transfer-across-independent-programs-and-limits-of-curve-shape-portability)**

---

## Discovery 1: Residual-Correction OOD Transfer for Electrolyte Conductivity Is Fragile and Mechanism-Constrained

### Summary

Using an independent donor–recipient pair of LiPF6 carbonate electrolytes, residual-correction transfer was found to be highly fragile: unconstrained linear calibration often worsened true out-of-distribution prediction, “regularized” variants helped only under particular random anchors, and several robustness and mechanism-guided interventions amplified errors. The few cases of apparent benefit did not arise from true shrinkage and degraded rapidly as a handful of recipient anchors were added, showing that any utility is narrowly confined to the lowest-label regime.

### Background

Cross-database transfer learning is attractive for experimental materials science because high-quality measurements are scarce, heterogeneous, and expensive, yet related domains may share local response structure. Electrolyte conductivity is a canonical test bed: it depends on temperature, salt concentration, and solvent composition, is measured with comparable impedance protocols, and exhibits known mechanistic regularities such as Arrhenius- or VFT-like temperature sensitivity. However, laboratory-, protocol-, and formulation-specific scale shifts complicate naive pooling, so the central scientific question is whether a portable relation, correction, or parameter learned from one experimental program can materially improve prediction in a neighboring domain without leaking provenance or overfitting.

### Results & Discussion

The study established a stringent, executable donor→recipient pair and a leakage-controlled out-of-distribution (OOD) protocol. The donor was CALiSol-23, a literature-curated ionic-conductivity collection (13,825 rows), which after strict unit and chemistry filtering yielded 1,012 LiPF6 measurements in EC/PC/EMC between 243.15–333.15 K from six independent source DOIs; the recipient was a KIT/Jülich EIS dataset of 5,035 conductivity measurements covering 109 unique mass-defined formulations across −30 to 60 °C in 10 °C steps [[r0](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/9988b9ff-d546-4227-87c1-d7269960e2ef)]. The shared inputs were temperature, LiPF6 molality, and EC/PC/EMC mass fractions; targets were converted to mS cm⁻¹ and K. Recipient formulations were partitioned into seven solvent-composition clusters, and leave-one-cluster-out evaluation held each cluster entirely for testing. The few-shot baseline trained a nonlinear regressor (HistGradientBoostingRegressor) on a small budget of k anchor formulations per fold; the transfer model pretrained the same regressor on all donor rows and fitted a low-dimensional linear residual corrector on the anchor rows using the five shared predictors. Performance was summarized as formulation-macro RMSE, defined as the equal-weight average of per-formulation RMSEs across their temperature series, with uncertainty from clustered or formulation-stratified bootstraps; pooled metrics were reported secondarily where relevant [[r1](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/cd3ed4f5-f26c-41ee-949f-e826bca1ab4e), [r4](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/dad2f38c-0229-4585-87c5-f3dc96873765), [r5](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/fa3627a7-5a5f-4d1f-8f10-4b491ee8d974)].

The canonical implementation with an unconstrained linear residual corrector did not improve OOD prediction: relative to the anchor-only baseline, formulation-macro RMSE increased by 12.69% (95% clustered-bootstrap CI −55.14% to 8.51%; one-sided p=0.8392), despite the donor retaining nontrivial signal versus a shuffled-label control and achieving positive OOD R² overall [[r1](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/cd3ed4f5-f26c-41ee-949f-e826bca1ab4e)]. Tightening donor locality around the anchors by selecting nearest-neighbor donor rows compounded harm, raising macro RMSE by 25.41% (95% CI −36.84% to −14.13%), with severe fold heterogeneity and pronounced sensitivity to which three anchors were used across 30 seeds, indicating that distance-based donor restriction alone cannot stabilize residual transfer [[r4](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/dad2f38c-0229-4585-87c5-f3dc96873765)]. These failures were not confined to one split or definition of macro aggregation, and in multiple folds the donor-corrected model underperformed the strong few-shot baseline, demonstrating genuine negative transfer rather than benign shrinkage toward the baseline [[r1](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/cd3ed4f5-f26c-41ee-949f-e826bca1ab4e), [r4](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/dad2f38c-0229-4585-87c5-f3dc96873765)].

A “regularized” variant—Ridge residual correction with alpha=1.0 and no scaling—reduced macro RMSE by 14.85% (95% bootstrap CI 4.30%–24.58%) in one frozen reconstruction and eliminated a catastrophic outlier incurred by ordinary least squares, yet it still lagged the baseline in some clusters, and the confidence interval did not guarantee ≥10% improvement with 95% confidence [[r5](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/fa3627a7-5a5f-4d1f-8f10-4b491ee8d974)]. Crucially, reproducibility checks showed this benefit was not robust to reasonable preprocessing: introducing standardization and tuning alpha by nested grouped cross-validation selected alpha=100 in nearly all folds and increased macro RMSE by 19.02% (95% CI −24.89% to −13.61%), with 0/20,000 bootstrap draws achieving the required 19.9% reduction; across 30 alternative anchor selections, tuned Ridge never outperformed fixed unscaled Ridge and frequently failed catastrophically [[r8](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/812e8a42-b874-40b8-95c9-2794c901a3c8)]. Making anchor choice deterministic via k-medoids improved solvent-composition coverage but did not improve accuracy or reduce variance compared to a matched random-anchor comparator (6.33% worse on macro RMSE; exact paired tests nonsignificant), implying that covering composition alone is insufficient when temperature and molality support remain mismatched [[r9](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/2a1163e9-fac0-46bf-b18d-13dde981feca)]. A forensic analysis traced one failure mode to standardization on nearly invariant anchor features: in a fixed fold, the EMC fraction’s anchor variance was so small (scale 0.000358) that a modest held-out shift to EMC=0.6991 was mapped to −16.97 standard deviations; combined with a standardized EMC coefficient of 518, this induced a −8,792 mS cm⁻¹ correction and drove a 432% RMSE increase versus the unscaled corrector, revealing a concrete mechanism by which scaling amplifies anchor-selection fragility [[r21](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/e6c1a088-e401-471c-9128-457ddc93cc21)].

Two additional analyses clarified why apparent “regularization” benefits are fragile and mechanism-constrained. First, direct coefficient reconstruction showed that Ridge(alpha=1.0) imposed negligible shrinkage relative to ordinary least squares at k=3 anchors: both learned near-identity affine recalibrations from donor prediction to measured conductivity, with virtually identical slopes (1.028–1.029) and intercepts (−0.20 mS cm⁻¹), reflecting that each corrector was in fact fitted to 50–220 temperature-resolved rows per fold, not three independent points [[r15](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/04e49cad-0894-476d-a3ad-57eb4bc8b848)]. Second, increasing the anchor budget from 3 to 9 made both models stronger, but the transfer advantage shrank monotonically from a mean 0.2300 mS cm⁻¹ at k=3 to 0.0475 mS cm⁻¹ at k=9 (79.3% relative decrease; within-seed slope −0.0305 mS cm⁻¹ per anchor, t(29)=−5.686, p=3.78×10<sup>-6</sup>), and the fraction of seed replicates favoring transfer fell from 28/30 to 22/30; variance decreased descriptively but not significantly, indicating that any benefit is concentrated at the very lowest data budgets and evaporates as a competent anchor-only model matures [[r12](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/5491f087-0ae3-435b-8a3b-76a5b76011d8)]. Together, these results refute the notion that generic residual regularization robustly stabilizes cross-database transfer and instead point to calibration geometry and anchor support as the dominant factors [[r5](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/fa3627a7-5a5f-4d1f-8f10-4b491ee8d974), [r8](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/812e8a42-b874-40b8-95c9-2794c901a3c8), [r12](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/5491f087-0ae3-435b-8a3b-76a5b76011d8), [r15](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/04e49cad-0894-476d-a3ad-57eb4bc8b848), [r21](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/e6c1a088-e401-471c-9128-457ddc93cc21)].

Finally, a mechanism-informed attempt to transfer Arrhenius temperature sensitivity underscored that even physically motivated objects must be calibrated appropriately. Activation energies (Ea) fitted per formulation were predictable across domains (leave-one-publication-out donor R²=0.669; on recipient, r=0.815), but replacing direct residual correction with a global-intercept Arrhenius strategy—predict Ea from composition, then calibrate a single ln(A) from three anchors—was uniformly harmful: macro RMSE ballooned from 1.980 to 36.133 mS cm⁻¹ (+1,725%), with failures in all seven folds and across 30 anchor reconstructions; even supplying “true” Ea while retaining a single global intercept remained disastrous (22.409 mS cm⁻¹), whereas an oracle with formulation-specific intercepts combined with predicted Ea achieved 1.263 mS cm⁻¹, revealing that temperature-sensitivity shape can transfer but scale must be modeled at the formulation level [[r19](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/f2443fb5-7e20-4a03-8df5-3182bf4066bf)]. Overall, across independent experimental programs with compatible representations and rigorous OOD evaluation, residual-correction transfer is fragile, strongly conditioned on anchor geometry and preprocessing, and mechanism-limited; stabilization will require calibration layers that respect feature support (e.g., variance floors and non-negativity constraints), hierarchical or composition-dependent intercepts, and anchor selection that jointly covers solvent composition, molality, and temperature rather than composition alone [[r0](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/9988b9ff-d546-4227-87c1-d7269960e2ef), [r1](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/cd3ed4f5-f26c-41ee-949f-e826bca1ab4e), [r4](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/dad2f38c-0229-4585-87c5-f3dc96873765), [r5](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/fa3627a7-5a5f-4d1f-8f10-4b491ee8d974), [r8](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/812e8a42-b874-40b8-95c9-2794c901a3c8), [r9](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/2a1163e9-fac0-46bf-b18d-13dde981feca), [r12](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/5491f087-0ae3-435b-8a3b-76a5b76011d8), [r15](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/04e49cad-0894-476d-a3ad-57eb4bc8b848), [r19](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/f2443fb5-7e20-4a03-8df5-3182bf4066bf), [r21](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/e6c1a088-e401-471c-9128-457ddc93cc21)].

---

## Discovery 2: Cross-Database Transfer of Ordinal Formulation Rankings in Electrolyte Conductivity

### Summary

This work identifies and de-risks a flagship experimental out-of-distribution (OOD) transfer case in which a donor model trained on an open electrolyte-conductivity database carries portable ordinal knowledge that improves ranking of unseen formulations in an independent experimental program. The ranking gain is significant, robust to alternative OOD partitions, specific against a large ensemble of mechanistically unrelated wrong donors, replicates on a second dataset, and is strongest in the few-shot regime while weakening in a high-molality region where response curvature diverges.

### Background

Transferring predictive knowledge across experimental programs is difficult because laboratory- and protocol-dependent shifts break absolute scales and can invalidate naïve pooling. Electrolyte conductivity is a stringent test bed: the same LiPF₆-in-carbonate formulations are measured under different temperatures, compositions, and protocols across laboratories, leaving substantial covariate overlap but nontrivial conditional shifts. In such settings, portable structure may reside in relative orderings (rankings) or low-dimensional response parameters rather than in absolute values. Demonstrating that ordinal information learned from one open database materially improves true OOD prediction in a second, independent experimental program provides a concrete pathway for scientifically grounded cross-database transfer.

### Results & Discussion

The donor–recipient pair was constructed from two independent open experimental resources with overlapping chemistry and temperature. The donor, CALiSol‑23 (CC BY 4.0), contains 13,825 literature-curated conductivity records; a rigorously unit- and chemistry-matched LiPF₆/EC/PC/EMC subset of 1,012 rows from six source DOIs was used for pretraining, treating the reported conductivity scale as mS cm⁻¹ under the audited harmonization assumption. The recipient, a KIT/Jülich electrochemical impedance spectroscopy dataset (5,035 measurements; 109 unique formulations; CC BY 4.0), provides repeated temperature series from −30 to 60 °C at fixed compositions. The shared feature space comprised solvent mass fractions (PC, EC, EMC), LiPF₆ molality, and temperature; OOD evaluation used leave-one-composition-cluster-out folds, with few-shot “anchor” formulations sampled only from non-held-out clusters to fit recipient-only baselines and optional residual correctors. Predictive performance was assessed by Spearman’s rank correlation ρ between predicted and measured conductivity on held-out formulations, averaging across anchor replicates within each fold and, in one protocol, across temperatures within fold-by-temperature evaluations [[r0](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/9988b9ff-d546-4227-87c1-d7269960e2ef), [r29](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/ecccb253-a69b-456f-b038-fa8329171099), [r38](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/f0e06237-8df4-43c9-b94b-857ab01b6c30)].

Donor pretraining conveyed real ordinal signal. Under a leakage-safe protocol using the KIT/Jülich dataset’s embedded clusters and 30 replicated three-formulation anchor sets, raw donor predictions outperformed an otherwise identical few-shot baseline in all seven folds (mean fold-level Δρ = 0.02406; 95% CI 0.01140–0.03671; paired t(6) = 4.651; two-sided p = 0.00350; Holm-adjusted p = 0.00700). After fitting a simple ridge residual corrector to anchors, the advantage remained significant but slightly compressed (mean Δρ = 0.02115; 95% CI 0.00479–0.03751; t(6) = 3.164; two-sided p = 0.01948), demonstrating that the transferable ranking structure resides in the pretrained model rather than being created by calibration [[r38](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/f0e06237-8df4-43c9-b94b-857ab01b6c30)]. The effect generalized across alternative OOD definitions: replacing the embedded split with KMeans‑10 or Agglomerative‑7 clusters preserved large positive fold-level advantages (mean Δρ = 0.656 and 0.677; one-sided paired t-tests p = 1.057×10<sup>-7</sup> and 4.950×10<sup>-7</sup>), despite a weaker baseline that sometimes produced constant predictions; even a worst-case bound that assigned +1 to undefined baseline ranks remained significant (p = 0.0434 and 0.00314), underscoring robustness of the qualitative ranking-transfer claim to split construction and baseline instability [[r29](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/ecccb253-a69b-456f-b038-fa8329171099)]. As expected for knowledge distillation under scarcity, the advantage attenuated monotonically with increasing anchor budget: at k = 3, 5, 7, and 9 formulations, mean Δρ values were 0.0261, 0.0150, 0.00929, and 0.00851, respectively (all one-sided p ≤ 0.0312 with Holm correction), and the fold-level trend in Δρ versus k was strongly negative (−0.00292 ρ units per additional anchor; t(6) = −8.49; one-sided p = 7.29×10<sup>-5</sup>) [[r42](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/cfa0d988-f6c2-4f2f-9073-8e1519c20666)].

The signal was chemically specific, not a generic model prior. Against an ensemble of 100 “wrong donors” constructed from 577,679 independent battery aging check-ups by quantile-mapping five battery covariates onto the electrolyte feature marginals, the true CALiSol-pretrained model achieved an overall mean fold-level ρ of 0.960446, exceeding the 90th, 95th, and 99th empirical percentiles of the wrong-donor distribution (maximum 0.957468), with a finite-simulation Monte Carlo p = (0+1)/(100+1) = 0.0099. Although residual correction narrowed pretrained-model separations (e.g., wrong donor 100 rose from ρ = 0.269388 uncorrected to 0.956265 corrected), the true donor continued to rank held-out formulations better than every falsifier on average across folds, supporting donor specificity at the aggregate level [[r32](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/31bb9dac-e29f-460c-a882-d8bde9e38d67)]. In concert with the raw-vs-corrected analysis, this shows that chemical regularities learned from electrolyte data—rather than calibration alone—drive the observed ranking advantage [[r38](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/f0e06237-8df4-43c9-b94b-857ab01b6c30), [r32](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/31bb9dac-e29f-460c-a882-d8bde9e38d67)].

Fold-level heterogeneity traced to a high-molality regime where donor and recipient responses diverged conditionally. Two weak folds (by predefined criterion: true-transfer mean ρ not exceeding the wrong-donor ensemble mean) were concentrated at high LiPF₆ molality (mean 1.825 and 1.922 mol kg⁻¹ versus 0.260 mol kg⁻¹ in a strong-control fold; both Holm-adjusted permutation p = 0.00006), yet one weak fold was significantly closer to the donor in feature space than the strong-control fold by Mahalanobis metrics, ruling out simple geometric extrapolation as a universal explanation. This pattern implicates conditional response differences rather than a lack of donor coverage per se [[r37](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/aa33e2b4-6441-4d1b-b2d8-e3550e1226a2)]. Independent temperature-response analyses support this view: above 1.8 mol kg⁻¹, both datasets exhibited substantially steeper Arrhenius slopes, but the donor surface showed much stronger inverse-temperature curvature than the recipient (curvature difference-in-differences = 3.016; 95% CI 1.869–4.162; z = 5.16; p = 2.53×10<sup>-7</sup>). Such curvature mismatch, especially at low temperatures, provides a mechanistic pathway for ranking breakdown in high-molality OOD clusters even when compositions lie within donor support [[r41](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/67629bb7-4097-431e-8d52-42f341d29d62), [r37](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/aa33e2b4-6441-4d1b-b2d8-e3550e1226a2)].

The phenomenon replicated in an independent experimental program. Using the Oxford/Glasgow SolventSeg dataset (36 LiPF₆/EC/EMC formulations × 5 temperatures; provenance independent of KIT/Jülich), raw CALiSol-pretrained predictions exceeded a three-formulation few-shot baseline under a five-fold KMeans formulation-level holdout by a mean fold-level Δρ of 0.244 (95% CI 0.099–0.389; one-sided t(4) = 4.67; p = 0.00477), with all five fold means positive. Data quality and split integrity were confirmed outcome-blind, although licensing metadata for the archived CSV require clarification before broad redistribution. Together with the KIT/Jülich results, this establishes that ordinal formulation knowledge learned in one open database can materially improve ranking in a second, genuinely independent experimental program under prospectively defined OOD partitions [[r39](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/54be41b6-52d2-4da7-89b1-60c6448493e5), [r35](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/65ba1474-c2c6-4817-97f5-fbee936ba734), [r0](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/9988b9ff-d546-4227-87c1-d7269960e2ef)].

---

## Discovery 3: Structured Triage, Contingency Execution, and Replication Hazards in Conductivity Transfer

### Summary

This work operationalizes a structured triage for experimental out‑of‑distribution transfer in electrolyte conductivity, executes a preregistered contingency when the primary plan fails, and then diagnoses a replication hazard that invalidates an independence claim. A contingency run achieved an 18.85% formulation‑macro RMSE reduction with positive OOD R², but a later audit showed the “replicate” was not an independent recipient dataset; a targeted refinement (composition‑distance donor weighting) also failed, and a third candidate was audited as viable but chemically mismatched and data‑limited.

### Background

Transferring predictive structure across neighboring experimental domains is attractive when absolute calibration varies by laboratory or protocol. Yet heterogeneous aggregation rarely yields a universal model; instead, portable objects are often relations, corrections, or low‑dimensional parameters that survive provenance shifts. Demonstrating a flagship success therefore requires independent donor/recipient sources, strict OOD splits aligned with scientific states, leakage control at the formulation or publication level, matched falsifiers, and uncertainty that respects clustered dependence. This study focuses on electrolyte conductivity, a mechanistically adjacent space with shared variables (temperature, salt concentration, solvent composition) but pronounced inter‑campaign and composition‑family shifts.

### Results & Discussion

A nine‑criterion scorecard prioritized three conductivity donor→recipient pairs: CALiSol‑23 → KIT/Jülich 5,035 EIS (43/45), CALiSol‑23 → FZJ/KIT one‑shot active‑learning conductivity (40/45, official contingency), and CALiSol‑23 → FEC/LiTFSI transport properties (34/45) [[r3](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/4d6f6212-08c6-4ef7-a502-ec5dcfecc9a1)]. The rubric weighted mechanistic adjacency, provenance independence, input/schema compatibility, state metadata, OOD relevance, falsifiability, expected effect size, computational feasibility, and publication value equally, and ranks were stable under leave‑one‑criterion‑out checks [[r3](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/4d6f6212-08c6-4ef7-a502-ec5dcfecc9a1)]. This triage created a predeclared execution pathway: attempt the primary conductivity transfer first, activate the one‑shot contingency if needed, and reserve the FEC/LiTFSI candidate as a higher‑risk stress test [[r3](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/4d6f6212-08c6-4ef7-a502-ec5dcfecc9a1)].

The primary CALiSol‑23 → KIT/Jülich test failed under a leave‑one‑composition‑cluster‑out design that grouped 109 exact mass‑tuple formulations into seven solvent‑fraction clusters and used three non‑test anchor formulations per fold. Models shared five predictors (temperature, LiPF6 molality, and EC/PC/EMC solvent mass fractions). Performance was summarized by formulation‑macro RMSE and macro R², computed by first evaluating RMSE and R² within each formulation and then averaging equally across formulations, with uncertainty from a cluster‑level bootstrap. Donor pretraining plus an ordinary‑least‑squares residual corrector increased macro RMSE by 12.69% versus the anchor‑only baseline (2.3570 vs 2.0915 mS/cm; one‑sided bootstrap p=0.8392; 95% CI −55.14% to 8.51%) and yielded macro R² 0.1169 versus 0.1468, with strong heterogeneity across clusters; a shuffled‑donor falsifier performed catastrophically, confirming that donor labels carry signal but not transferable benefit under this protocol [[r1](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/cd3ed4f5-f26c-41ee-949f-e826bca1ab4e)]. By the preregistered gate, this primary pair did not meet the ≥15% improvement criterion and was rejected [[r1](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/cd3ed4f5-f26c-41ee-949f-e826bca1ab4e)].

The contingency on the FZJ/KIT one‑shot conductivity dataset reproduced the audited split and froze unambiguous operational choices before outcome fitting (five features; three anchors per fold; scikit‑learn HistGradientBoostingRegressor with Ridge residual correction; formulation‑macro metrics; formulation‑cluster bootstrap). Source integrity checks reproduced the audited 1,012 donor and 5,035 recipient rows. Transfer reduced macro RMSE from 1.9475 to 1.5804 mS/cm (18.85% reduction; 95% CI 13.84%–23.34%), improved macro R² from −0.0811 to 0.3742, and helped 78/109 formulations and 6/7 clusters; however, one cluster remained negative and the confidence interval crossed the 15% threshold, so the result was interpreted as “criterion met by point estimate with residual uncertainty,” not a definitive ≥15% gain [[r7](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/7911adbc-eecf-4364-aae4-2efa4e582d2b)]. These estimates used leakage‑safe, leave‑cluster‑out evaluation at the formulation level, with uncertainty clustered on formulations within folds [[r7](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/7911adbc-eecf-4364-aae4-2efa4e582d2b)].

A subsequent canonical re‑run and provenance audit exposed a replication hazard: only one recipient CSV was supplied, so the purported contingency replicate was not an independent second dataset, and repeating the frozen, seed‑2025 protocol reversed the effect direction. Under the canonical seeds, donor pretraining plus Ridge residual correction increased macro RMSE by 10.26% (2.1706 vs 1.9686 mS/cm; paired difference −0.2020 mS/cm, 95% CI −0.3562 to −0.0420; Holm‑adjusted one‑sided p=0.8372), and macro R² fell from 0.6786 to 0.3767. Controls behaved as expected—shuffled‑donor and chemically “wrong‑donor” (LiBOB/LiBF4) models were far worse than the candidate transfer—but candidate transfer was practically indistinguishable from an unconstrained linear residual corrector (0.0055 mS/cm advantage). Fold‑level outcomes were highly heterogeneous, with severe error inflation in a three‑formulation fold, underscoring sensitivity to anchor selection and cluster composition; critically, treating the same table as two recipients would constitute pseudoreplication [[r14](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/3ff15ecb-6253-4a50-afd0-3c8fd91ef0a5)]. These findings highlight that preregistered independence checks must be enforced alongside fixed seeds and leakage units to avoid invalid replication claims [[r14](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/3ff15ecb-6253-4a50-afd0-3c8fd91ef0a5)].

Targeted method refinement did not rescue weak subspaces: adding an inverse‑exponential donor weight based on solvent‑fraction distance raised cluster‑1 RMSE by 3.25% versus unweighted transfer (1.5830 vs 1.5332 mS/cm; paired 95% CI 0.0222–0.0757; Wilcoxon p=3.6×10⁻4) and degraded overall macro RMSE by 7.88% (0.1374 mS/cm increase; paired 95% CI 0.0600–0.2258; Holm‑adjusted p=8×10⁻5). The likely explanation is that solvent‑only proximity ignores molality, temperature, and publication effects, producing only moderate and misaligned reweighting [[r13](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/f45fdfa3-d6c7-47c7-bcfa-8a51c2941700)]. The third‑ranked FEC/LiTFSI candidate was outcome‑blind audited as accessible (CC BY 4.0), harmonized, and split OOD by co‑solvent family, but donor chemistry overlap was minimal (zero FEC+LiTFSI in CALiSol‑23; only 56 LiTFSI donor rows across EC/DMC and PC), the recipient was tiny (30 rows across six formulations), and institutional independence was partial (both under the KIT umbrella); the pair is “viable with major limitations” suitable for a stress test rather than a flagship [[r30](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/ba856a22-72f8-42ed-8ddf-08565f10279d)]. Collectively, the triage‑to‑contingency pipeline worked operationally, but the ensuing independence failure and fragile gains emphasize that executable success requires preregistered provenance audits, leakage‑safe OOD grouping, strong matched falsifiers, and stability across anchor draws—not just on‑paper mechanistic adjacency [[r3](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/4d6f6212-08c6-4ef7-a502-ec5dcfecc9a1), [r1](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/cd3ed4f5-f26c-41ee-949f-e826bca1ab4e), [r7](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/7911adbc-eecf-4364-aae4-2efa4e582d2b), [r14](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/3ff15ecb-6253-4a50-afd0-3c8fd91ef0a5), [r13](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/f45fdfa3-d6c7-47c7-bcfa-8a51c2941700), [r30](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/ba856a22-72f8-42ed-8ddf-08565f10279d)].

---

## Discovery 4: Battery Aging: Strong Negative Transfer Across Independent Programs and Limits of Curve-Shape Portability

### Summary

This study executed an audited, preregistration-style test of knowledge transfer for battery aging across two fully independent experimental programs and found decisive negative transfer: donor pretraining and few-shot calibration more than doubled error relative to a strong recipient-only baseline. The result establishes a hard limit on curve-shape portability for capacity fade across laboratories, cell models, and protocols, and reframes where mechanistic constraints are needed to achieve reliable out-of-distribution transfer.

### Background

Transfer learning in materials informatics is often justified by the expectation that neighboring experiments share low-dimensional, mechanism-linked structure even when absolute scales differ. Battery aging is a natural testbed: relative capacity trajectories from reference performance tests are thought to follow stable shapes as functions of temperature, state-of-charge window, depth of discharge, and cycling severity, with laboratory-dependent offsets. The central question is whether such degradation “geometry” can be ported between independent programs and quickly calibrated with a few recipient anchors to improve prediction in a held-out protocol family that represents a true out-of-distribution regime.

### Results & Discussion

Two open, independent battery-aging programs were identified that permit a rigorous donor→recipient test with defensible out-of-distribution splits and matched falsifiers. The donor is a Karlsruhe Institute of Technology (KIT) study of 228 commercial NMC/graphite–silicon cells aged under 76 calendar and cycling conditions with standardized check-ups and raw time series (CC BY 4.0). The recipient is a Munich University of Applied Sciences/ISES study of 279 Samsung INR21700-50E cells tested in a two-stage design comprising factorial/Latin-hypercube sampling (Stage 1) and a parameter-individual optimal design (Stage 2) (CC BY 4.0). A second, smaller Stanford dataset (10 INR21700-M50T cells aged under dynamic UDDS discharge) remained a plausible but unaudited donor to KIT. The transferable object was defined a priori as the normalized capacity-fade curve (or surface) as a function of protocol variables, with a recipient-learned intercept/scale to absorb absolute offsets; true OOD was enforced by holding out Munich’s Stage‑2 “pi” family or an entire protocol block. The primary anticipated confounders were differences in cell construction, diagnostic protocols, and laboratory procedures that could reflect mechanism shift rather than a simple level offset [[r2](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/039bbacf-d5cd-4380-b36f-5788552a57c3)].

An outcome-blind data audit verified access, provenance independence, schema compatibility at the reference-test level, and a leakage-safe Munich holdout. Relative capacity was harmonized as Q_RPT(t)/Q_RPT(initial) using KIT EOCV2 standardized check-ups and Munich integrated charge/discharge capacities at designated step types, with quality control that excluded RPTs showing >5% charge/discharge disagreement. The prespecified OOD split held out all 60 Munich “pi” experiments; eight non‑pi records sharing internal identifiers with these cells were removed to prevent physical-cell leakage, yielding 211 training experiments. Canonical predictors were aging mode (calendar vs cycling), temperature, maximum state of charge, depth of discharge, charge/discharge C-rates, and elapsed days. Cell-macro root-mean-squared error (RMSE) was defined as the mean of per‑cell RMSEs to weight each independent experiment equally, and cell-macro R² was defined as the within‑cell coefficient of determination averaged across cells with nonzero target variance. Ten anchor cells were selected deterministically by greedy maximin coverage in protocol space. Models compared were: (i) a recipient-only gradient-boosting regressor trained on the 10 anchors; (ii) a transfer model with the same architecture pretrained on KIT and ridge-calibrated on anchor residuals; and (iii) a shuffled-donor control in which KIT targets were globally permuted before pretraining. Uncertainty was estimated by 5,000 bootstrap resamples of complete held-out cell trajectories [[r10](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/5c2e264a-b57b-4b9d-8b6f-98024e59f607), [r11](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/fad18a64-191d-4bc1-a941-0fd411639903)].

The primary test decisively falsified the transfer hypothesis. On the 60 held-out Munich “pi” cells (532 RPT records), the recipient-only baseline achieved a cell-macro RMSE of 0.02568 (95% CI 0.02035–0.03109), while KIT pretraining plus 10‑cell calibration degraded performance to 0.08457 (95% CI 0.07079–0.09866), a 229.3% increase in error (95% CI −260.18% to −205.11% when expressed as “reduction”), i.e., 3.29× the baseline error. The shuffled-donor control was also harmful (0.05110; 95% CI 0.04499–0.05724; −98.95% “reduction”), but remained substantially better than the real KIT transfer, indicating that apparently meaningful donor structure was misaligned with the recipient domain. Cell-macro R² likewise deteriorated from −1.096 (baseline) to −17.431 (transfer) and −5.862 (shuffled), with R² defined for 48 of 60 cells. Performance was heterogeneous by aging mode: for 24 calendar-aging cells, the baseline was already highly accurate (RMSE 0.00231; R² 0.884), whereas transfer worsened error (RMSE 0.02371; R² −1.618); for 36 cycling cells, transfer also degraded performance (baseline RMSE 0.04126 vs 0.12515 for transfer; R² −1.756 vs −22.702). These outcomes remained under the audited split, harmonization, and leakage guards, and they do not depend on any improvement from tuning hyperparameters post hoc [[r11](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/fad18a64-191d-4bc1-a941-0fd411639903)].

Mechanistically, these results indicate that degradation-curve “shape” is not portable across these programs via a simple residual correction, even with defensible normalization, careful OOD enforcement, and a few-shot recipient calibration. Differences in cell model (LG INR18650HG2 vs Samsung INR21700-50E), construction and electrode formulation, diagnostic definitions, and protocol supports plausibly alter the active aging modes, producing domain shift beyond an intercept/scale offset. The especially large harm for cycling protocols suggests that donor relationships captured under KIT’s cycling conditions do not map to Munich’s Stage‑2 pi‑optimized regime, whereas calendar-aging under a fixed environment left little room for any donor to help given the strong recipient-only fit. Together with the shuffled-donor control, the evidence supports a stringent conclusion: portable relations for battery aging likely require mode‑specific constraints, tighter protocol alignment, or mechanistic state variables that survive laboratory and cell‑design changes. A second dynamic‑to‑static pair (Stanford UDDS → KIT) remains a scientifically interesting but untested path; its very small donor size and deeper harmonization challenges counsel caution rather than optimism about achieving reliable out‑of‑distribution gains without stronger physical priors [[r2](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/039bbacf-d5cd-4380-b36f-5788552a57c3), [r11](https://platform.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3/trajectories/fad18a64-191d-4bc1-a941-0fd411639903)].

---