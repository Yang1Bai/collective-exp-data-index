# Phase 1 findings: compensation laws across the unified experimental data lake

**Question.** Does a domain-transcending "unified" empirical law (Meyer-Neldel /
enthalpy-entropy compensation) emerge from pooled multi-domain experimental data?

**Data.** `data/collective.sqlite` (105,955 measurements). Domains tested:
thermoelectric transport (ESTM, 880 materials with T-series) and gas adsorption
(NIST ISODB, van't Hoff systems). Scripts: `mn_compensation.py`, `mn_family.py`,
`hs_isodb.py`; parameter tables in the adjacent CSVs.

## Results

1. **No domain-wide compensation.** Pooling all 113 activated-transport
   thermoelectric materials (Arrhenius R²>0.9, 0<Ea<2 eV): lnA vs Ea gives
   **R² = 0.053** — no unified Meyer-Neldel law at the whole-domain level.

2. **Compensation is family-scoped, and plausibly genuine there.** Grouping by
   chemical family (major elements ≥15 at.%), families with n≥8:

   | family | n | R² | T_iso (K) |
   |---|---|---|---|
   | Ag-Se | 13 | 0.56 | 1689 |
   | Ag-Bi-Se | 9 | 0.52 | 706 |
   | Co-Li-O | 8 | 0.47 | 1851 |

   Family-median R² = 0.52 vs pooled 0.053 (10×). For Ag-Se and Co-Li-O,
   T_iso lies far above the experimental temperature range (~300–800 K),
   passing the Krug artifact criterion; Ag-Bi-Se (706 K) is borderline.

3. **The strongest apparent cross-system law is a statistical artifact.**
   Adsorption (42 clean van't Hoff systems) shows seemingly strong
   enthalpy–entropy compensation, **R² = 0.892** — but T_iso = 303 K vs
   Krug harmonic-mean temperature 305 K (within 1%). This is the textbook
   signature of error-induced compensation, not thermodynamics.

## Conclusion

**In the first controlled cross-domain test on unified experimental data,
there is no evidence for a domain-transcending compensation law. Empirical
regularity lives at the chemical-family level (moderate, artifact-robust
Meyer-Neldel signals within thermoelectric families), while the strongest
apparent cross-system regularity (adsorption H–S compensation, R²≈0.9)
fails the Krug artifact control.** Practical corollary for the
grand-unification program: any candidate "universal law" mined from
aggregated experimental databases must clear artifact screens (Krug test,
family stratification) before being interpreted — the screens, not the
correlations, are the gatekeepers.

## Limitations & next steps

Small family sizes (n=8–13, p≈0.03–0.05); single summary-point extraction for
ISODB (full-isotherm fits would sharpen ΔH); only 2 domains tested. Next:
grow families via full ISODB build + more T-resolved datasets (Starrydata2),
apply the same pipeline to OBELiX ionic conductivity, and pre-register the
family-level MN hypothesis before the expanded test.
