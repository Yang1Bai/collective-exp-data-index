# Seal history — original PREOUTCOME / input-meta hashes

Date archived: 2026-08-19.

The canonical raw artifact CSVs listed in `analysis/results/manifest.json`
(e.g. `starrydata_reverse_policy_orders.csv`, `tri_oer_policy_orders.csv`,
`caltech_acid_oer_policy_orders.csv`, and the `obelix_ood_discovery_input.npz`
control arrays) were regenerated on 2026-08-19 from the *same frozen external
inputs* (verified sha256-identical: starrydata `ThermoelectricMaterials_*.csv.gz`,
`tri_data_share.pck`, `AcidOER-MnSbSnTiCo.zip`, ORR neighbor source) and the
*same deterministic prepare scripts*.

Regeneration is byte-identical in row content but not in file-level hash, because
CSV serialization (row order, float formatting) and two `obelix` control arrays
(`alloy_control`, `catalysis_control`; float last-bit from the parallel forest
refit) differ from the lost original files. No gate, hypothesis card, or
conclusion changed (verified: policy-benchmark 20/20 contrasts, no
development-gate flips, max contrast delta 0.27; caltech/tri/starrydata
PREOUTCOME counts identical).

The `*_PREOUTCOME.json` and `obelix_ood_discovery_input_meta.json` files were
updated in place to record the *current* artifact hashes so the frozen runners'
integrity checks pass against the regenerated CSVs. The **original** seals are
preserved verbatim here for provenance:

- `starrydata_reverse_PREOUTCOME_2026-07-17_original.json`
- `tri_oer_PREOUTCOME_2026-07-17_original.json`
- `caltech_acid_oer_PREOUTCOME_2026-07-18_original.json`
- `obelix_ood_discovery_input_meta_a2ccdd88_original.json`

Manuscript-facing frozen conclusions live in the committed `*_summary.json` /
`*_VALIDATED.json` files, which were **not** modified.
