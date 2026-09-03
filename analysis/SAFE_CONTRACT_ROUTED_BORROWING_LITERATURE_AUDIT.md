# Literature audit for safe, contract-routed knowledge borrowing

## Decision

The next method should not be a larger generic transfer model. The literature
and the completed eight-target benchmark point to a **contract-routed,
target-anchored ensemble** in which:

1. the deployment contract determines what may be transferred;
2. source predictions are cross-fitted by material identity before their
   transferability is estimated;
3. donors explain only target-model residuals;
4. the target-only prediction is always an available fallback;
5. OOD-tail extrapolation is handled by a separate analogy/ranking head rather
   than being conflated with ordinary covariate-shift prediction.

This version is called **SAFE-MAMB**: source-aware, fallback-equipped,
mechanism-aligned modular borrowing.

## What the strongest related methods actually establish

| Method family | Strong result | Boundary relevant to this project | Adopted element |
|---|---|---|---|
| Cross-material component learning | Moon *et al.* trained separate surface and bulk branches, joined them through five common descriptors, ranked 14 unseen monometallic systems and experimentally validated a screened multimetallic catalyst. | The target was an explicit hybrid of the two source material classes under the same OER contract; this is component alignment, not evidence that arbitrary neighboring databases transfer. | Define the transferable object before fitting and route by physical contract. |
| Mixture of experts for materials | Chang *et al.* reported that a model-agnostic MoE outperformed pairwise transfer on 14 of 19 materials-property tasks. | Static task-level expert combination was evaluated mostly on calculated crystal-property tasks, not our experimental OOD portfolio. | Combine multiple source experts instead of selecting one donor. |
| Cross-modality embedding | CroMEL transferred calculated structure knowledge to composition-only predictors and improved all 14 experimental targets. Its regression-based transferability estimator selected sources 6.5–12.4 times faster than exhaustive retraining. | It assumes a large calculated structure source and evaluates ordinary cross-validation; it does not by itself solve input-defined experimental OOD or negative transfer. | Estimate source usefulness from target-development predictions before full fitting; use the score as shrinkage evidence, not as a universal physical truth. |
| Task-routed MoE | OmniMol routes the same molecule differently for different property tasks and handles sparse, partially annotated multi-property data. | It used roughly 250,000 labels and random 8:1:1 splits. A neural task router is too flexible for target budgets of 15–30. | Use the task-routing principle, but implement a low-capacity contract router and sparse linear residual gate. |
| Polymer multi-task learning | A property-selector network trained on 36 polymer properties handled about 95% missingness better than a conventional multi-head network; category-restricted correlated task groups performed best. | The dataset contained more than 23,000 labels, far larger than our OpenPoly subset, and its evaluation was not a scaffold-defined OOD test. | Represent each observed material-property pair with a property token; share only within a mechanism-defined property bundle. |
| Thermoelectric multi-gate MoE | A thermoelectric MMoE reported a 71% Seebeck improvement while the other tasks remained within cross-validation variance. | The gain was endpoint-selective and ordinary cross-validation does not establish OOD repair. | Treat endpoint heterogeneity as expected and require target-specific gates. |
| Multioutput Gaussian processes | Negative transfer can persist when too few latent functions force unrelated outputs to share structure. | A single dense shared latent process is unsafe for our heterogeneous tasks and non-nested databases. | Retain task-specific residuals and sparse source allocation; do not force every endpoint into one common latent function. |
| Regression transferability estimation | STE estimates regression transferability from regularized linear fit error and outperformed earlier estimators on its benchmarks. | Its validation was not materials-specific and does not certify causality or OOD benefit. | Score each donor using only cross-fitted target-development predictions. |
| Bilinear Transduction / MatEx | Reported 1.8-fold higher extrapolative precision for materials, 1.5-fold for molecules and up to threefold higher recall of high-value candidates. | Its principal OOD split is defined by the response value, while our primary Q4 is defined without outcomes. The authors state that the original theoretical guarantees may not fully apply to their output-OOD adaptation. | Add a prespecified secondary tail/rank head; do not replace the outcome-free Q4 benchmark. |
| Structure-based OOD benchmarks | Random splits overstate performance, and no tested model dominates across all OOD constructions. | Model complexity alone is not a solution. | Preserve grouped, outcome-free Q1/Q4 evaluation and learner sensitivity. |
| Representation-space OOD diagnosis | Chemical labels such as “contains Mg” can mix representationally ID and OOD samples, and embedding density only imperfectly tracks error. | Raw composition distance is an incomplete gate. | Use distance for evaluation strata, but never multiply distance directly into a transfer weight; add uncertainty/disagreement for abstention. |
| Weighted conformal prediction | Coverage can be recovered under covariate shift when density ratios are known or accurately estimated from unlabeled target covariates. | It assumes stable conditional response and reliable density-ratio estimation; it cannot create a better point predictor. | Use only for interval/abstention reporting after the point-prediction method is fixed. |

## Local data-contract audit

The repository contains two qualitatively different transfer settings.

### Paired or partially paired multi-property programmes

- thermoelectrics: target and principal donors share 100% of material keys;
- OCX catalysis: target and principal donors share 100%;
- polymer tensile strength: Young's modulus 100%, elongation 90%, glass
  transition 99%, and hardness 62% target-key coverage;
- alloy yield strength: principal donor coverage ranges from 47% to 63%;
- hydration free energy: 82% of target molecules occur in AqSolDB.

These programmes support masked multi-property learning, but a zero-shot
deployment must still hide auxiliary labels of held-out target identities.

### Non-paired cross-database programme

- OBELiX ionic conductivity and the thermoelectric sources have zero shared
  material keys and zero shared material groups.

This programme cannot use paired multi-output learning. It requires a frozen
source expert, a common composition representation, target-development
calibration, and an explicit right to abstain.

## Failure mode found in the previous quick smoke

The previous donor models excluded all target evaluation identities, which is
correct. However, their predictions on sampled target-development identities
could be produced by a source model that had seen the same material's donor
label. The meta-model therefore saw easier donor features during fitting than
during evaluation. This is not target-outcome leakage, but it is a
train–deployment feature-contract mismatch.

SAFE-MAMB fixes it by cross-fitting each donor prediction by material identity:
for every target meta-fold, the source model excludes the target identities in
that fold before producing their donor features.

## SAFE-MAMB local-screen algorithm

For each target-training draw:

1. fit the target-only learner and obtain grouped out-of-fold target
   predictions;
2. obtain material-identity-cross-fitted predictions from every eligible donor;
3. estimate each donor's signed residual-transfer score using only the sampled
   target-development outcomes;
4. retain only mechanism-eligible donors with positive cross-fitted evidence;
5. fit a ridge-shrunk residual stack;
6. choose a blend with the target-only prediction from
   `{0, 0.25, 0.5, 0.75, 1}` using grouped meta-cross-validation and a
   pseudo-OOD-weighted objective;
7. if no blend beats the target-only objective, assign zero donor weight;
8. evaluate without refitting on the frozen outcome-free Q1 and Q4 strata.

The first local screen uses three representative contracts:

- OpenPoly tensile strength: paired, sparse multi-property;
- MPEA yield strength: partially paired, same-domain multi-property;
- OBELiX ionic conductivity: non-paired, cross-database transport.

## References

1. Chang, R., Wang, Y.-X. & Ertekin, E. *npj Comput. Mater.* **8**, 242
   (2022). https://doi.org/10.1038/s41524-022-00929-x
2. Moon *et al.* *Nat. Mater.* (2026).
   https://doi.org/10.1038/s41563-026-02622-6
3. Jeong *et al.* *npj Comput. Mater.* **11**, 235 (2025).
   https://doi.org/10.1038/s41524-025-01723-1
4. Wang *et al.* *Nat. Commun.* **16** (2025).
   https://doi.org/10.1038/s41467-025-63730-6
5. Künneth *et al.* *Patterns* **2**, 100238 (2021).
   https://doi.org/10.1016/j.patter.2021.100238
6. Leveraging language representation for materials exploration and
   discovery. *npj Comput. Mater.* **10** (2024).
   https://doi.org/10.1038/s41524-024-01231-8
7. Li, M. & Kontar, R. *SIAM/ASA J. Uncertainty Quantification* (2022).
   https://doi.org/10.1137/21M1436816
8. Nguyen *et al.* UAI 2023.
   https://proceedings.mlr.press/v216/nguyen23a.html
9. Segal *et al.* *npj Comput. Mater.* **11**, 345 (2025).
   https://doi.org/10.1038/s41524-025-01808-x
10. Omee *et al.* *npj Comput. Mater.* **10**, 144 (2024).
   https://doi.org/10.1038/s41524-024-01316-4
11. Probing out-of-distribution generalization in machine learning for
   materials. *Commun. Mater.* (2025).
   https://doi.org/10.1038/s43246-024-00731-w
12. Tibshirani *et al.* Conformal prediction under covariate shift. NeurIPS
   (2019). https://papers.nips.cc/paper/2019/hash/8fb21ee7a2207526da55a679f0332de2-Abstract.html
