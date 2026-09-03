# Crosslab fade transfer — pre-outcome endpoint amendment 2

**Time:** 2026-07-29, after the outcome-blind audit (`eligible-preoutcome`),
**before any recipient (HUST) row beyond cycle 101 was read** and before any
transfer model was fitted.

## Trigger (donor-side data availability, not any outcome)

The PINN4SOH mirror truncates MIT/Severson capacity trajectories before the
frozen 80%-of-Q_ref end-of-life: across all 123 donor cell files the minimum
reached SOH has quantiles [0.837, 0.850, 0.855, 0.861, 0.909]; zero donor cells
reach 80%. The frozen life label is therefore uncomputable on the donor with
this mirror. (Discovered during the donor self-check stage; the recipient
remains sealed at 101 rows.)

## Amendment

- **End-of-life milestone redefined by a fixed rule, not a chosen number:**
  EOL SOH = the deepest 0.01-grid threshold reachable by at least 90% of
  Q_ref-valid donor cells. Computed: **0.89** (114/123 = 92.7%; 0.90 reaches
  only 94.4%→fails the deeper-first scan at 95%? — the applied rule is ≥90%,
  scan from deep to shallow: 0.85→27.2%, 0.86→59.2%, 0.87→73.6%, 0.88→87.2%,
  0.89→91.2% ✓).
- Life label := first cycle where median-filtered Qd/Q_ref ≤ **0.89**; the
  power-law life solve uses Qloss = 0.11. Applied **identically** to donor,
  wrong-chemistry donor, and recipient.
- **Interpretation consequence (binding for the manuscript):** the endpoint is
  "cycles to 89% SOH", an early-to-mid degradation milestone, not the standard
  80% EOL. Any claim must say so explicitly.
- **New abort check added to the formal stage:** if fewer than 20 recipient
  cells are uncensored at the amended milestone, the run records itself as
  abstaining (`insufficient-uncensored-recipient`), reports counts, and the
  success gate is not evaluated.
- **Donor milestone-consistency diagnostic added:** Spearman between
  cycles-to-89% and cycles-to-85% on the donor cells that reach both, to verify
  the milestone is a faithful proxy of deeper degradation ordering.

## Unchanged

Everything else: candidate-time window (≤100 cycles), degradation model and
WLS fit, features, mapping learners, prior/posterior combination, abstention,
budgets, contrast family, success-gate thresholds, seeds, bootstrap and
permutation counts, laboratory OOD unit, SNL→HUST backup decision, and the
recipient outcome seal (recipient rows beyond 101 remain unread until the
formal stage).
