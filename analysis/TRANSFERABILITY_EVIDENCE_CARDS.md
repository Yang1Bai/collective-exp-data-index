# Quantitative transferability evidence cards

These cards are a reporting layer over the frozen analyses. They do not alter
the original code, models, training, hyperparameters, or default routing. They
also do not claim that transferability can be reduced to a universal 0--100
score. Each card reports the observed support and effect for a particular
donor--recipient relation and decision endpoint.

| Recipient | Quantitative data support | Observed endpoint evidence | Route |
|---|---|---|---|
| LiAsF6 | Salt overlap 0%; solvent overlap 30.4%; temperature and concentration coverage 100%; 60.8% within donor q95 relation boundary | log-RMSE gain vs state-only 27.4% (95% CI 21.8% to 32.9%); raw R2 0.607; rho 0.864; gain vs chemistry-shuffled 25.9% | **predict** |
| SolventSeg | 3 separate source programmes; 36 recipient formulations at 5 temperatures; strict source--recipient record overlap 0; source ranking uses 0 recipient labels | absolute log-RMSE gain vs state-only -18.0%; five-anchor rank rho 0.910 vs 0.537; delta 0.374 (95% CI 0.213 to 0.562); top-quartile precision 0.932 vs 0.490 | **rank** |
| FINALES | 16 evaluation formulations; 98 temperature-matched pairs; 3 recipient anchors; donor and recipient DOI do not overlap | donor concordance 0.694 vs recipient 0.783; delta -0.089 (95% CI -0.293 to 0.096); p=0.131; regret 0.563 vs 0.180 | **withhold** |

## Interpretation

- **LiAsF6:** Transfer is not justified by exact identity overlap. It is
  justified by complete experimental-state coverage, partial relation-space
  support, and positive lower confidence bounds against both a state-only
  baseline and a chemistry-destroyed control. The supported object is an
  absolute chemistry--state relation.
- **SolventSeg:** Cross-programme scale shift defeats absolute prediction, but
  the zero-label candidate order remains stronger than the best fixed
  five-label recipient baseline. The supported object is ordinal ranking only.
- **FINALES:** Having enough evaluable pairs does not imply transferability.
  The frozen donor order loses to the recipient baseline and fails uncertainty,
  significance, precision, and regret checks. The supported action is to
  withhold.

## Frozen decision gates

- **LiAsF6 absolute prediction:** temperature and concentration coverage must
  both equal 100%, some recipient rows must lie inside the donor relation
  boundary, and the 95% interval lower bounds against both the state-only and
  chemistry-shuffled controls must exceed zero.
- **SolventSeg absolute prediction:** the gains against state-only and the
  five-anchor target-only baseline must each be at least
  10% with positive 95% lower bounds; log-R2 must
  be positive; and the gain against chemistry permutation must be positive
  with a positive 95% lower bound.
- **SolventSeg ranking:** absolute prediction must fail; the source-minus-
  recipient rank advantage must be at least 0.10 with a
  positive 95% lower bound; Holm-adjusted permutation P must be at most
  0.05; top-quartile precision must improve; and normalized
  regret must decrease.
- **FINALES ranking:** every frozen replication gate in
  `analysis/results/finales_rank_replication_summary.json` must pass. Failure
  of any gate yields `withhold`.

## Reproduce the package

```bash
python -m pip install --only-binary=:all: -r analysis/requirements-transfer-policy.txt
python analysis/build_transferability_evidence_cards.py
python -m analysis.run_transfer_action_policy
python analysis/submission/make_transfer_action_policy_figures.py
python -m unittest discover -s tests -v
```

The committed JSON, CSV, SVG, PDF, PNG, and TIFF files are generated artifacts.
The dedicated GitHub Actions workflow reruns these commands and rejects drift.

## Recommended manuscript use

Use the support columns to explain *why the source data are relevant*, and the
endpoint columns to establish *what level of reuse is empirically allowed*.
Keep the route recipient-specific. These values describe evaluated relations;
they are not a prospective selector for an unseen programme until the same
fields and thresholds are frozen and validated prospectively.
