# Digital Discovery paper package — status: analysis complete

**Working title:** "A unified experimental data lake for materials and chemistry:
cross-domain regularity, artifacts, and selective knowledge transfer"

## Claims and evidence (all reproducible from analysis/ scripts)

1. **Infrastructure.** Open catalog of 118 verified experimental databases
   (experimental-only policy, automated discovery pipeline with human review
   gate) + unified data lake (10 datasets, 105,955 measurements, 319 properties,
   single SQLite schema). Scripts: repo-wide.
2. **No domain-wide compensation law.** Pooled thermoelectric Meyer-Neldel
   R²=0.053 (113 activated materials). Regularity is family-scoped
   (Ag-Se R²=0.56, Co-Li-O R²=0.47; T_iso >> experimental range → passes Krug).
3. **Artifact gatekeeping is essential.** Strongest apparent cross-system law
   (adsorption H-S compensation, R²=0.892, 42 systems) is a Krug artifact
   (T_iso=303K vs T_hm=305K).
4. **Knowledge transfers selectively between adjacent domains.** Data-poor
   solid electrolytes (OBELiX) + thermoelectric knowledge (ESTM): ΔR²=+0.16 at
   n=30 (baseline zero skill), +0.09 persisting to n=240. Controls all pass:
   - Leakage: **0** shared compositions between source and target.
   - Placebo (shuffled source feature): **negative** (−0.04/−0.02).
   - Graded adjacency: MPEA yield strength ≈ +0.01; OCx24 catalysis ≈ 0.00.
   - Chemistry ablation: transfer **survives** in the non-chalcogenide subset
     (+0.033±0.013) → not merely shared chalcogenide chemistry; chalcogenide
     subset null is size-limited (n_total=135), flagged as inconclusive.
5. **Thesis.** Under incomplete scientific understanding, grand-unified laws do
   not fall out of aggregated data — but adjacent-domain inspiration is real,
   measurable, selective, and exploitable for data-poor fields.

6. **The knowledge-borrowing map is sparse and physically ordered.** Full
   pairwise ΔR² matrix over 9 domains (inorganic + organic, shared element-
   composition space, n=60): transfer is NOT universal — it concentrates on
   the data-poor solid-electrolyte target borrowing from transport-physics
   neighbors (TE:ZT +0.089, Alloy:YS +0.041), while organic molecular
   properties (logS, pKa, λ_max, Tg) borrow ~0 from inorganic sources
   (the organic↔inorganic null) and little from each other — element
   composition is too coarse for molecular targets, which need structural
   fingerprints. Regularity is a sparse, physically-adjacent graph, not a
   dense field.

## Main-text figures (all in analysis/, 200 dpi)

- **Fig 1** `fig1_resource.png` — resource: 118-database catalog composition +
  105,955-measurement data lake.
- **Fig 2+3** `fig_main.png` — (a) family-scoped MN compensation; (b) the Krug
  adsorption artifact; (c) transfer learning curves with placebo/graded controls.
- **Fig 4** `fig4_transfer_matrix.png` — cross-domain knowledge-borrowing map
  (ΔR² heatmap), hot cell SE←TE highlighted, organic↔inorganic null visible.

## Remaining before submission (mechanical, no new science)

- Molecular-domain transfer with structural fingerprints (Morgan/RDKit) to test
  whether the organic-side null is physical or a featurization limit — one added
  panel, sharpens the discussion.
- Raise replicate splits to 20; add CIs to all matrix cells (currently 4 reps).
- Full ISODB build (raise ISODB_CAP on a real machine) + per-isotherm fits.
- Pre-registration note in repo for the expanded family-MN test.
- Methods text: catalog policy, TDM compliance stance, pipeline description.
- Repo goes public at submission; archive snapshot to Zenodo for a DOI.
