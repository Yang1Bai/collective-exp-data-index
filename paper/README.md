# Submission evidence package

This directory is the clean entry point for the code, frozen model
specifications, derived results and source data used by the submitted English
manuscript. It is an
allowlist, not a second copy of the repository: authoritative artifacts remain
at their original tracked paths and are linked here so reviewers can audit each
claim without navigating legacy experiments.

## Claim-to-evidence map

| Article result | Route | What the evidence supports | Authoritative files |
|---|---|---|---|
| Broad far-OOD screen | **WITHHOLD** | Forty declared donor–recipient edges across eight targets produced no complete gate pass. The programme-mean OOD gain was 0.92% (95% interval −0.35% to 2.92%). This rejects the tested protocol—injecting one cross-fitted donor-prediction scalar as immediately usable quantitative knowledge—not multitask learning, pretraining or representation transfer in general. | [design](../analysis/multi_target_ood_borrowing_design.json), [runner](../analysis/run_multi_target_ood_borrowing.py), [summary](../analysis/results/multi_target_ood_summary.json), [verification](../analysis/results/multi_target_ood_VERIFIED.json) |
| External LiAsF6 conductivity | **PREDICT** | Within source-covered temperature–concentration state and a chemistry/state representation aligned with the transport mechanism, the frozen source model learned from 10,407 measurements across 22 salts and reached raw R² = 0.607 and Spearman ρ = 0.864 on the LiAsF6 recipient; log-RMSE was 27.41% lower than the state-only model. | [design](../analysis/bamboomixer_response_transfer_design.json), [runner](../analysis/run_bamboomixer_response_transfer_development.py), [source audit](../analysis/results/bamboomixer_response_transfer_summary.json), [corrected summary](../analysis/results/bamboomixer_LiAsF6_only_summary.json), [predictions](../analysis/results/bamboomixer_LiAsF6_only_external_predictions.csv) |
| SolventSeg sparse-label screening | **RANK** | When independent programme effects make absolute calibration unreliable, only ordering is transferred. With five measured formulations, the formal equal-programme percentile-rank consensus achieved mean held-out ρ = 0.885 versus 0.162 for the prespecified target-only Ridge model (Δρ = 0.723; 95% interval 0.329–1.349). The absolute portfolio was on average 18.0% worse in log-RMSE than the state-only comparator, so it is not routed to numerical prediction. | [design](../analysis/bamboomixer_cross_database_interaction_design.json), [runner](../analysis/run_bamboomixer_cross_database_interaction.py), [summary](../analysis/results/bamboomixer_cross_database_interaction_summary.json), [verification](../analysis/results/bamboomixer_cross_database_interaction_verification.json) |
| SolventSeg target-only stress test | **Sensitivity** | The main conclusion is not dependent on Ridge alone: across 13 recipient-only configurations, the strongest tested target model reached mean ρ = 0.537, while the source numerical portfolio reached 0.910. This is an outcome-inspected robustness analysis, not an independent confirmation and not the formal route-defining contrast above. | [runner](../analysis/run_bamboomixer_recipient_baseline_stress_test.py), [summary](../analysis/results/bamboomixer_recipient_baseline_stress_test_summary.json), [verification](../analysis/results/bamboomixer_recipient_baseline_stress_test_verification.json) |
| FINALES second recipient | **WITHHOLD** | With 19 eligible formulations and the first three as anchors, donor concordance was 0.694 versus 0.783 for the strongest recipient model (difference −0.089; 95% interval −0.293 to 0.096; permutation P = 0.131). Top-quartile precision was 0.50 for both and donor regret was worse. This is insufficient evidence for transfer under the frozen gate; the interval crossing zero does not prove harmful transfer. | [frozen design](../analysis/finales_rank_replication_design.json), [runner](../analysis/run_finales_rank_replication.py), [summary](../analysis/results/finales_rank_replication_summary.json), [verification](../analysis/verify_finales_rank_replication.py) |

The same mapping is available as a machine-readable
[claim manifest](claims/claim_manifest.csv), and every headline number is
listed with its JSON path in [article source data](data/article_source_data.csv).

## Transfer boundaries used in the manuscript

- **Numerical prediction** is considered only when recipient state variables
  remain within source support and the chemical representation encodes the
  variables relevant to the property mechanism.
- **Ranking only** is used when source and recipient are independent programmes
  and preparation, thermal management or instrument effects are missing or not
  harmonized, so monotone candidate order may travel while numerical scale
  does not.
- **Withhold** means the prespecified evidence gate did not pass. In the broad
  polymer and alloy cases, the present benchmark cannot distinguish a genuinely
  non-portable relation from an inadequate fixed representation; it therefore
  makes no claim that all transfer methods must fail.

## What belongs to the submitted article

- Exact model and protocol allowlist: [models/README.md](models/README.md)
- Data access, DOI, licence and repository representation:
  [data/README.md](data/README.md)
- Copy-ready repository links for the manuscript:
  [ARTICLE_LINKS.md](ARTICLE_LINKS.md)
- Fast audit and full rerun commands:
  [reproduction/README.md](reproduction/README.md)

## Data-availability boundary

The 15 third-party resources used in the submitted study remain available from
their original repositories. Their access links, DOIs and licence information
are recorded in [the data manifest](data/datasets.csv). Raw third-party data
are not redistributed in this submission package. Repository paths in the
manifest point only to normalized snapshots, harmonized subsets or derived
results retained for audit under the applicable upstream terms.

Large computational intermediates are intentionally omitted. The frozen
designs and runners reconstruct those intermediates from the upstream inputs;
their absence does not remove any submitted headline result or source-data
value from this package.

## Scope and release status

Historical, exploratory, null and superseded analyses and figure drafts remain
in the repository for provenance, but they are not automatically article
evidence. Only paths in the claim manifest and model allowlist should be cited
as support for the current manuscript.

The URLs in `ARTICLE_LINKS.md` point to the reviewer-response branch. They are
usable during peer review but are not yet archival. Before publication, create
an immutable release, archive it, and replace the review-branch landing URL
with the release DOI; no DOI is fabricated in this package.
