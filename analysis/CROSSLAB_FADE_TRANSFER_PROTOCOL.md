# Cross-laboratory degradation-parameter transfer — frozen protocol

**Frozen:** 2026-07-29, before any recipient data download and before any recipient
outcome access. Machine-readable twin: `crosslab_fade_transfer_design.json`.
Parent: `analysis/review_packages/claude/CLAUDE_SCIENCE_REVIEW_2026-07-29.md` §10.

## Scientific question

Can the *mapping* from a cell's own early-life measurements to its degradation-model
coefficients — together with the population prior over those coefficients — transfer
across laboratories, when raw endpoint values demonstrably do not transfer across
provenance boundaries anywhere in this project?

This operationalizes the within-specimen bridge: every prior positive edge in the
repository (MPEA UTS→YS, KIT −20→−30 °C) kept the recipient specimen's own cheap
measurement as the anchor. Here the anchor is each recipient cell's own first 100
cycles; only the coefficient prior and the early-feature→coefficient mapping cross
the laboratory boundary.

## Roles

- **Donor:** MATR LFP/graphite cells, 4 batches (Severson 2019 + Attia 2020),
  CC BY 4.0, URLs pinned from BatteryML (MIT). Full trajectories read — the donor
  is not the test.
- **Recipient:** HUST 77-cell LFP dataset (Mendeley nsc7hnsg4s/2). This is the
  **declared backup**: the primary SNL recipient is application-gated and the
  batteryarchive.org host is unreachable from the execution environment; the
  backup rule was declared in the parent review §10.8 before any recipient data
  or outcome access. OOD axis = laboratory, cycler platform, protocol family.
- **Wrong-chemistry donor control:** CALCE LCO prismatic cells.
- Dropped pre-outcome: SNL NCA/NMC chemistry-OOD secondary edge (same access
  reason).

## Candidate-time boundary

Recipient information available to any model: cycles ≤ 100 only, plus protocol
descriptors. Forbidden until the single formal run: any recipient measurement
after cycle 100, any life label, and **total observed cycle counts** (these are
correlated with life; the audit records only the boolean "has ≥100 usable
cycles").

## Transfer object

1. Per-cell power-law fade fit `Qloss = a·n^β` (WLS in log–log, cycles 10 onward),
   life = cycles to 80% SOH, `n̂ = (0.2/a)^{1/β}`.
2. Donor mapping `g`: early-window features → (log₁₀a, β), Random Forest primary,
   Ridge sensitivity; prior covariance from donor protocol-block out-of-fold
   residuals.
3. Recipient cell posterior = precision-weighted combination of the donor prior
   `g(x_i)` and the cell's **own** cycles-10–100 WLS fit.
4. Budgets k ∈ {0, 5, 10} labelled recipient cells; k>0 adds a shrunken intercept
   recalibration (τ=5). Primary budget k=0.
5. Abstention: recipient cells outside the donor 90th-percentile feature
   Mahalanobis support fall back to own-curve prediction and stay in the
   denominator.

## Controls (Holm family of five, primary budget)

recipient_only · shuffled_donor · wrong_chemistry_prior · prior_only ·
gaussian_prior; oracle_all_recipient reported outside the family as ceiling.

## Success gate (all required; failure = null/harmful/abstain, unrepairable)

≥10% relative RMSE reduction (log₁₀ life, uncensored cells) vs recipient_only;
cell-bootstrap 95% CI lower bound > 0; Holm p < 0.05; ≥5 pp margin over shuffled
and wrong-chemistry; absolute log-life R² > 0; 90% interval coverage degraded by
≤5 pp; ≥65% of cells improved.

## Outcome-blind audit gates

≥20 recipient cells; ≥90% with ≥100 usable early cycles; feature intersection
must include capacity series, ΔQ(V), and protocol descriptors; ≥150 donor cells
with valid fits; donor protocol-block OOF Spearman ≥ 0.5. Any failure → recorded
abstention, stop.

## Interpretation preassignment

- **Pass:** first outcome-blind, cross-laboratory, parameter-level borrowing edge;
  ladder L2/L3 remains closed for endpoint values while the parameter/mapping
  channel is open. If MATR and HUST share the same nominal cell model, the claim
  is "same cell model, different laboratory" — stated explicitly.
- **Null:** the provenance floor extends to parameter space; combined with the
  variance-decomposition programme (H2) this is a quantitative boundary result,
  not a failure of the paper.
- **Harmful:** shrinkage miscalibration; report posterior-shrinkage diagnostics
  and archive as a negative case for hierarchical transfer.
