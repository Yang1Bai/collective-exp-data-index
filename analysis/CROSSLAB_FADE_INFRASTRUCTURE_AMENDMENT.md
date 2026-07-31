# Crosslab fade transfer — pre-outcome infrastructure amendment 1

**Time:** 2026-07-29, after design freeze, **before any recipient (HUST) file content
was read** and before any formal model fit. Recipient access at amendment time:
directory listing of `data/HUST data/` filenames only. Donor access at amendment
time: column schema + one cell's trajectory (`MIT data/2017-05-12_battery-1.csv`)
and a 3-row header check of one XJTU file. No recipient outcome, no recipient
early-window value, and no aggregate statistic of any dataset has been computed.

## Trigger

The execution environment's network allowlist blocks every primary and declared
data source: `data.matr.io`, `data.mendeley.com`, `web.calce.umd.edu`,
`batteryarchive.org`, plus `zenodo.org`, `figshare.com`, `huggingface.co`,
`osf.io`. Reachable: `github.com` and `*.githubusercontent.com` only. This is an
infrastructure constraint independent of any outcome.

## Amendments (all pre-outcome, none outcome-responsive)

1. **Raw source → GitHub mirror.** Donor and recipient data are taken from the
   companion repository of Wang et al., *Nat. Commun.* **15** (2024),
   10.1038/s41467-024-48779-z: `github.com/wang-fujin/PINN4SOH`, commit
   `bf7a93148de6a7e249c1b053bd60fe3c9a3dc1f0` (2024-10-16). It contains per-cycle
   feature + capacity CSVs with identical 17-column schema for MIT (Severson,
   125 cells, 3 batches), HUST (77 cells), TJU (130), XJTU (55). The repository
   carries no LICENSE file; data are used for analysis only and not
   redistributed; provenance is cited.
2. **Donor batch set.** The mirror contains the three Severson batches only
   (2017-05-12, 2017-06-30, 2018-04-12); the 2019-01-24 Attia batch is absent.
   Donor = 3 batches. Consequently the donor-count audit gate is lowered from
   ≥150 to **≥100 cells with valid fits** — forced by availability, not by any
   outcome.
3. **Batch-continuation errata handling.** The original five batch-1 cells that
   continue into batch-2 cannot be re-linked from mirror filenames. Conservative
   pre-declared rule: donor cells that are right-censored (never reach 80% SOH
   in their file) or whose Q_ref falls outside [0.9, 1.2]×1.1 Ah are excluded
   from donor fitting and counted in the audit. This removes truncated
   batch-1 fragments and mid-life batch-2 continuations without identity
   guesswork.
4. **Feature list.** Raw V/I/t series are unavailable on every reachable
   mirror, so ΔQ(V) features are not computable. Amended symmetric feature set
   (computable from cycles ≤100 in all four datasets): the 16 per-cycle
   charge-segment statistics × {early level = median(cycles 10–30), drift =
   OLS slope(cycles 10–100), delta = median(91–100) − median(5–14)} plus
   capacity-series features {Q(100)/Q_ref, capacity slope(2–100), log10
   variance of detrended capacity residuals(10–100)}. The audit gate
   `required_feature_intersection` becomes {capacity series, charge-segment
   statistics}. The binding safeguard against feature-set weakness is unchanged:
   the donor protocol-block self-check gate (OOF Spearman ≥ 0.5) must pass
   before the formal run; if the reduced features cannot support donor skill,
   the experiment aborts pre-formal.
5. **Protocol descriptors** are not symmetrically available as model features
   (MIT charge policies are not recoverable from mirror filenames). They are
   excluded from the feature set and retained only for block definitions:
   donor CV blocks = batch folder; recipient sensitivity blocks = first-stage
   discharge rate family from the published HUST protocol table (BatteryML
   `preprocess_HUST.py` DISCHARGE_RATES, source: RSC SI d2ee01676a).
6. **Wrong-chemistry donor.** CALCE (unreachable) → **XJTU 55 NCM cells** from
   the same mirror, identical schema and processing — a strictly better-matched
   wrong-chemistry control.

## Unchanged (still frozen)

Endpoint and life definition; degradation model and coefficient fit; recipient
candidate-time boundary (cycles ≤100; the audit reads recipient files with a
hard `nrows=101` cap so outcomes are physically unread); laboratory OOD unit;
budgets {0,5,10}; the five-contrast Holm family; the full success gate; seeds;
abstention rule; bootstrap and permutation specification; the SNL→HUST backup
decision.
