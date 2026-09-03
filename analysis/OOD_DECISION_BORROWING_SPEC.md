# OOD decision borrowing: frozen extension

**Internally frozen:** 2026-07-14 18:11:15 UTC, before any ranking,
enrichment, first-hit, or regret calculation. This is an author-controlled,
self-attested timestamp, not a public preregistration.

## Why this extension is necessary

Average held-out RMSE asks whether a prior improves property prediction over
the whole target distribution. It is not the same question as whether the
prior helps a scientist choose experiments in the part of a database that is
chronologically, compositionally, or provenance-wise outside the target
training set. A source prior may be poorly calibrated yet still rank rare
high-performing candidates usefully. The reverse is also possible: a small
RMSE improvement can leave the discovery ranking unchanged.

The candidate-edge audit therefore has two axes:

1. **predictive utility** — relative RMSE, absolute R², uncertainty, and model
   robustness;
2. **OOD decision utility** — how much of a fixed held-out candidate pool must
   be screened before finding a genuinely high-performing candidate.

Neither axis substitutes for the other.

## Locked primary endpoint

For each frozen held-out candidate pool, the true positive set is the highest
5% of observed target values. Baseline and borrowing models rank the same
pool. The primary endpoint is

\[
\Delta f_{\mathrm{hit}} = f_{\mathrm{hit,baseline}}
- f_{\mathrm{hit,borrowed}},
\]

where `f_hit` is the one-indexed rank of the first true positive divided by
the pool size. Positive values mean that borrowing saves candidate
evaluations. The first 10% of the ranked pool is the practical shortlist.

The independent primary family contains exactly three previously frozen
prediction settings:

- Borg UTS → BIRDSHOT yield strength under chronological campaign holdout;
- −30 °C → −40 °C CALiSol conductivity under complete-article holdout;
- ESTM ZT → OBELiX ionic conductivity under the official DOI/composition-
  disjoint evaluation split.

Holm correction is applied across those three edges. KIT is a within-campaign
positive reference; Matbench is an independent composition-holdout boundary.

## Rescue is a decision crossing, not an R² adjective

An edge is an **OOD exploration rescue** only if it passes the adjusted
inference, stability, practical-effect, and control gates in
`ood_decision_borrowing_design.json`, and changes the median result from
requiring more than 10% of the pool to requiring at most 10%. A merely positive
point estimate is directional evidence. This operational definition prevents
the word *rescue* from being attached post hoc to any favorable ranking change.

## Scope

The experiment is retrospective: all candidate outcomes are already present
in the databases and are revealed only for evaluation. It tests whether a
source prior would have improved screening decisions on a fixed OOD pool. It
does not by itself demonstrate a prospective laboratory acceleration or a
universal notion of chemical distance.
