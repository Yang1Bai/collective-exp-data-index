# Crosslab fade transfer — findings (formal run, 2026-07-29)

**Frozen decision:** `null-harmful-or-incomplete-edge` — more precisely, an
**abstain-everywhere** outcome. Verification: `crosslab_fade_VERIFIED.json`
(`verified-complete`, 26/26 checks).

## Execution chain (all artifacts committed)

| Stage | Result | File |
|---|---|---|
| Design freeze (before any data download) | frozen | `crosslab_fade_transfer_design.json`, `CROSSLAB_FADE_TRANSFER_PROTOCOL.md` |
| Amendment 1 (network allowlist → GitHub mirror, XJTU wrong-chem, feature set without ΔQ(V)) | pre-outcome | `CROSSLAB_FADE_INFRASTRUCTURE_AMENDMENT.md` |
| Outcome-blind audit (recipient hard-capped at `nrows=101`) | `eligible-preoutcome`: 77/77 cells, features computable, 77 rate families known | `results/crosslab_fade_preoutcome_audit.json` |
| Amendment 2 (mirror truncates donor trajectories before 80% SOH → rule-derived 89% milestone; recipient still sealed) | pre-outcome | `CROSSLAB_FADE_ENDPOINT_AMENDMENT_2.md` |
| Donor self-check | **passed**: 113 valid cells; batch-out OOF life Spearman **0.575** (gate ≥0.5); milestone consistency ρ(89 vs 85)=**0.990** | `results/crosslab_fade_donor_selfcheck.json` |
| Formal run (single, no rerun) | gate fail | `results/crosslab_fade_formal_summary.json` |

## What actually happened

**The frozen applicability gate abstained on 100% of recipient cells.** Every
HUST cell's early-window feature vector lies beyond the 90th-percentile
Mahalanobis support of the MATR donor feature distribution, so all four
transfer arms (real, shuffled, wrong-chemistry, Gaussian) fell back to the
own-curve prediction on every cell, and all primary contrasts are exactly zero.
The gate did precisely what it was designed to do: **it detected that the two
laboratories do not overlap in candidate-time feature space and refused to
borrow anywhere.** The dominant cause is protocol-driven: MATR cells are
fast-charged (policy-specific charge statistics), HUST cells share one 5C
two-stage charge protocol — the 48 charge-segment features separate the labs
almost completely.

## Numbers a reader needs

- Recipient (HUST, cycles-to-89%-SOH milestone): 77/77 uncensored; lives
  682–1696 cycles; **std of log10 life only 0.079** — the milestone forced by
  the mirror truncation compresses outcome variance severely.
- `recipient_only` (own-curve extrapolation from 100 cycles): RMSE 0.451 log10,
  MAPE 268%, Spearman 0.09, R² −32.2 — as expected, LFP fade in the first 100
  cycles is nearly flat and own-curve extrapolation is pathological.
- **Labeled post-outcome diagnostic** (not part of the frozen family):
  `prior_only` — the unconditional donor coefficient prior, which by
  construction bypasses the mapping and the abstention gate — improves the
  own-curve baseline by **22.7% relative RMSE [7.3, 30.5], 74% of cells
  improved**, MAPE 268%→81%. Even the weakest form of cross-laboratory
  parameter information regularizes the pathological baseline; but absolute
  utility remains far below zero (R² −18.8), so it passes no gate.
- Within-lab oracle (LOO mapping on recipient): RMSE 0.120 — but even the
  oracle's R² is **−1.34** on this narrow-variance milestone. No method,
  including a fully recipient-trained one, beats the recipient mean here.
- Donor-side transfer skill existed: batch-out OOF Spearman 0.575 on MATR
  itself with the reduced (no-ΔQ(V)) features.

## Interpretation (bounded)

1. This run is a **provenance-ladder L3 data point of a new kind**: failure was
   declared *before* borrowing, by candidate-time support mismatch, rather than
   *after* borrowing by a null contrast. "Abstain-everywhere" is the correct
   behavior of the contract when two laboratories' operating envelopes are
   disjoint.
2. The run is **infrastructure-limited, and that limit is quantified**: the
   sandbox network allowlist forced a GitHub mirror without raw V/I/t curves
   (no ΔQ(V) features, no true 80% EOL). The compressed 89% milestone makes
   even within-lab prediction absolute-utility-negative (oracle R² −1.34), so
   no transfer method could have passed the absolute-utility gate on this
   execution regardless of merit. The scientific question is *not settled
   negative*; it is settled that **this data channel cannot answer it**.
3. The `prior_only` diagnostic is the one genuine cross-laboratory signal:
   population-level fade-coefficient information moves the needle on a
   pathological baseline. It is consistent with the within-specimen-bridge
   hypothesis but is far from the success gate.

## What would upgrade this to a real test (no design change needed)

Re-run the identical frozen pipeline on the **raw** sources — MATR .mat files
(data.matr.io, CC BY 4.0) and `hust_data.zip` (Mendeley) — from a network
position that can reach them (e.g., the user's own machine, which already
holds other raw archives in `data/external/`). That restores: true 80% EOL
(life std ≈0.3 log10 across MATR), ΔQ(V) features (the known strong signal),
IR and temperature channels, and a recipient life range wide enough for
absolute utility to be achievable. The design, gates, seeds, and contrast
family in `crosslab_fade_transfer_design.json` apply unchanged; only the
`DATA` path and the two amendments' mirror-specific clauses are superseded.
The abstention gate should be *kept* — whether it still fires at 100% with
ΔQ(V)-based features is itself the first scientific question of the re-run.

## Status of the fact table

Fact table row H1 moves from "plan" to: **executed once under mirror
constraints → abstain-everywhere (verified); substantive cross-laboratory
question remains open pending raw-data re-run.**
