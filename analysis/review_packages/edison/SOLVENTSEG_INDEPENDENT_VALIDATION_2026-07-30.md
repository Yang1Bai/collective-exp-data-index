# Independent validation of the SolventSeg rank-transfer result

## Decision

The reported mean fold-level improvement,
\(\Delta\rho=0.2436205943\), is numerically real. Independent retraining
reproduced every one of the 150 donor and baseline Spearman values to floating
point precision: the maximum absolute error was \(9.7\times10^{-17}\), and the
reproduced mean was identical to the reported mean.

The result also survives the most important scientific correction. The
original Spearman calculation pooled measurements from five temperatures, so
it mixed temperature ranking with formulation ranking. At a fixed 25 °C, the
cross-database donor achieved mean fold-level \(\rho=0.701\), compared with
\(\rho=0.316\) for the original three-formulation recipient-only baseline,
giving \(\Delta\rho=0.385\). Against a stronger Extra Trees recipient-only
baseline, the fixed-temperature advantage remained \(0.312\), with a
five-fold interval of \(0.113\) to \(0.511\).

This is therefore the strongest genuine independent cross-database positive
edge currently available in the project, but it is still retrospective
method-development evidence rather than a confirmatory discovery claim.

## Source and provenance

- Recipient data: SolventSeg, DOI `10.5281/zenodo.6299956`.
- Associated publication: *Current-driven solvent segregation in lithium-ion
  electrolytes*, DOI `10.1016/j.xcrp.2022.101047`.
- Public repository: `https://github.com/ndrewwang/SolventSeg/tree/beta`.
- Recipient: 36 LiPF6/EC/EMC formulations measured at 10, 20, 25, 30, and
  40 °C, giving 180 salt-containing measurements.
- Donor: 410 harmonized LiPF6/EC/EMC conductivity measurements selected from
  CALiSol-23 and three source publications.
- The recipient publication and donor source DOIs are distinct. No exact
  recipient formulation was used as a recipient training/test split unit
  across folds.

The Zenodo record describes the deposit as open software with an
“Other (Open)” licence, while the co-archived repository uses MIT. The
experimental CSV is publicly accessible, but the licence applying specifically
to redistribution of the measurements should be clarified before publishing a
derived data package.

## Exact reproduction of the Edison estimand

The Edison procedure was reproduced as follows:

1. fit one histogram gradient-boosting donor model to all 410 donor rows;
2. partition the 36 recipient formulations into five composition clusters;
3. hold out one complete composition cluster at a time;
4. draw three recipient training formulations from the other clusters,
   retaining all five temperature measurements for each formulation;
5. train the stated recipient-only baseline on those 15 rows;
6. repeat 30 anchor draws per fold and compare Spearman correlations.

| Quantity | Reported | Independently reproduced |
|---|---:|---:|
| Mean fold-level \(\Delta\rho\) | 0.2436205943 | 0.2436205943 |
| 95% \(t\)-interval | 0.0987 to 0.3886 | 0.0987 to 0.3886 |
| One-sided \(t\)-test | 0.00477 | 0.00477 |
| Exact fold sign-flip \(p\) | 0.03125 | 0.03125 |
| Maximum replicate-level discrepancy | — | \(9.7\times10^{-17}\) |

The exact sign-flip result is more appropriate to emphasize than the
parametric \(t\)-test, although five overlapping cross-validation folds still
do not constitute five independent experimental replications.

## Decision-relevant reanalysis

The following values average the five held-out composition clusters.

| Estimand | Donor | Original recipient baseline | Advantage |
|---|---:|---:|---:|
| Original row-pooled Spearman | 0.688 | 0.445 | +0.244 |
| Mean within-temperature Spearman | 0.694 | 0.308 | +0.386 |
| Spearman at 25 °C | 0.701 | 0.316 | +0.385 |
| Formulation rank after averaging temperatures | 0.607 | 0.316 | +0.292 |
| Top-quartile precision at 25 °C | 0.900 | 0.398 | +0.502 |
| Normalized regret at 25 °C | 0.015 | 0.830 | 0.814 lower |

The top-quartile result is the most useful practical signal: across the five
held-out clusters, 90% of the formulations selected into the predicted top
quartile were truly in the top quartile at 25 °C. The top-one hit rate was only
40%, however, and was not distinguishable from the shuffled-donor distribution
(\(p=0.294\)). The result supports shortlist enrichment, not reliable selection
of the single best formulation.

## Stronger-baseline sensitivity

The direct donor remained better than each tested recipient-only model trained
on the same three formulations. At 25 °C:

- versus Extra Trees: \(\Delta\rho=0.312\), fold interval 0.113 to 0.511,
  exact sign-flip \(p=0.03125\);
- versus Random Forest: \(\Delta\rho=0.353\), fold interval 0.119 to 0.587;
- versus quadratic Ridge: \(\Delta\rho=0.631\);
- versus linear regression: \(\Delta\rho=0.649\).

This argues against the result being solely an artefact of the original
histogram-boosting baseline. The model panel was defined during this audit,
after the Edison outcome was known, so it is a robustness analysis rather than
a new confirmatory test.

## Shuffled-donor falsifier

Two hundred donor-label permutations were fitted while leaving the recipient,
composition folds, and evaluation metrics unchanged.

| Metric | Real donor | Shuffled mean | Shuffled 95th percentile | Empirical \(p\) |
|---|---:|---:|---:|---:|
| Row-pooled Spearman | 0.688 | 0.024 | 0.321 | 0.00498 |
| Within-temperature Spearman | 0.694 | 0.023 | 0.431 | 0.00498 |
| Spearman at 25 °C | 0.701 | 0.017 | 0.466 | 0.00498 |
| Formulation-mean Spearman | 0.607 | 0.031 | 0.500 | 0.0149 |
| Top-quartile precision at 25 °C | 0.900 | 0.363 | 0.667 | 0.00498 |
| Normalized regret at 25 °C | 0.015 | 0.340 | — | 0.0149 |

The learned donor labels therefore carry real transportable ordinal
information. A support-matched wrong-electrolyte donor is still needed to show
that the gain is chemically specific rather than a generic consequence of
training on a smooth conductivity surface.

## Limitations that prevent a confirmatory claim

1. The ranking method and recipient were selected after earlier absolute-value
   transfer attempts had failed. The nominal \(p\)-values do not include this
   search history.
2. Only one independent recipient programme and five composition clusters are
   available.
3. The KMeans OOD partition is a heuristic composition partition, not a
   temporal or prospective campaign holdout.
4. The three-formulation baseline is intentionally data-poor, but it is an
   extreme regime; the advantage should be mapped over anchor budgets.
5. The 410-row donor conductivity unit is recorded inconsistently in its
   source metadata. A positive constant conversion would not change ranks, but
   the ambiguity must be resolved for absolute-value analyses.
6. The result improves retrospective shortlist quality. It does not yet show
   prospective laboratory discovery acceleration.

## Project-wide ranking of positive results

1. **SolventSeg fixed-temperature ranking:** strongest independent
   cross-database positive result. Use as the flagship feasibility example,
   explicitly as an OOD shortlist prior.
2. **Caltech hard-OOD ranking from an external transport donor:** AUC20 of 51
   versus a shuffled mean of 11.59, the sole member of its four-test family to
   survive Holm correction (\(p=0.0396\)). Valuable corroboration for ranking,
   but retrospective and based on one target.
3. **Within-campaign neighboring-temperature rescue:** adding the -20 °C
   conductivity relation reduced -30 °C RMSE by 15.02%, with a positive
   interval and positive absolute \(R^2\). This is a strong local-neighbor
   mechanism check, not independent cross-database transfer.
4. **Anchored delta transfer across CALiSol articles:** transporting
   neighboring-temperature changes rather than absolute values reduced macro
   RMSE by 6.91% versus absolute transfer, with 8 of 11 articles positive and
   exact sign-flip \(p=0.0352\). This is the clearest evidence that changing the
   transfer object improves portability.

The MPEA 9.21% result should no longer be described as a clean donor-specific
cross-domain success: under stricter DOI-disjoint and same-information donor
controls, the effect shrank and no primary donor-specificity contrast survived
Holm correction. Battery conductivity, optical-to-photovoltaic, and
bandgap-to-photovoltaic programmes are null at their complete gates.

## Reproducibility package

All inputs, fold assignments, anchor replicates, code, and independent outputs
are stored under:

`analysis/review_packages/edison/legacy_kosmos_2026-07-30/solventseg_validation`

Key SHA-256 values:

- outcome-blind source/split audit:
  `8d84ae4d2951290f424f86ce73e92dc2110557b6d163a0fb57e0720e9a75e169`;
- audit script:
  `4a193f61e26ef56869da4dfed575d2f40f4fde661154548de2dc1144fbb3ddf7`;
- audit summary:
  `b4e8b275c5e1d91808096b45d9378db9ea5220d402920e7f8bc244cc505395d2`;
- replicate-level recalculation:
  `5eff3118516ee69cfeed7ea2ce08301d4111bc71643dcb464fb0d48b6b9634b2`;
- baseline sensitivity:
  `fe81526b5d7d33b56051f93dbaf8e70d027d77b0edbc0a134392c0fff0dc53fe`;
- shuffled-donor controls:
  `67ef012ab52c63969cb18b2568a0da9892b9836fef6f85f8620ddd746cb27d88`.
