# Analysis result policy

This directory versions compact scientific results: JSON summaries, decision
records, checksums, independent-verification reports, small contrast tables,
and figure source data. Large row-level predictions, repeated bootstrap draws,
model checkpoints, embeddings, and scheduler archives are excluded from Git
because they are deterministic intermediates and can exceed GitHub's file-size
limits.

The code, frozen designs, environment specifications, input hashes, and compact
verification outputs required to reconstruct those intermediates remain in the
repository. The public attempt index is
[`research/evidence/ATTEMPT_LEDGER.csv`](../../research/evidence/ATTEMPT_LEDGER.csv),
and the experiment-by-experiment command map is
[`analysis/README.md`](../README.md).

The catalyst-attention summaries are
`catalyst_attention_specgen_summary.json`,
`catalyst_attention_specgen_ablation.json`,
`catalyst_attention_ocx24_summary.json`,
`catalyst_attention_seccm_summary.json`, and
`catalyst_attention_audit.json`. The frozen advanced comparison adds
`catalyst_attention_advanced_specgen.json`,
`catalyst_attention_advanced_ocx24.json`, and
`catalyst_attention_advanced_seccm.json`. Each dataset-scoped file is marked
partial; `catalyst_attention_advanced_summary.json` binds their hashes into
the complete comparison. No advanced candidate passed its promotion gate.
`aggregate_advanced_catalyst_results.py` deterministically rebuilds that
compact summary; a full one-command rerun writes the distinct
`catalyst_attention_advanced_monolithic.json` schema.
The accompanying checkpoints remain ignored and are
reproducible from
[`analysis/CATALYST_ATTENTION_TRANSFORMER.md`](../CATALYST_ATTENTION_TRANSFORMER.md).

The optimizer/residual-routing extension adds:

- `catalyst_optimizer_mhar_screening.json` — initial standard/MHAR ×
  AdamW/KL-Shampoo screen;
- `catalyst_optimizer_mhar_refinement_screening.json` — corrected
  per-sublayer routing and Adam-grafted KL-Shampoo screen;
- `catalyst_optimizer_mhar_confirmation.json` — three-seed Delta-MHAR
  confirmation;
- `catalyst_optimizer_mhar_standard_ocx24_confirmation.json` — matched
  standard-attention OCx24 complementarity diagnostic;
- `catalyst_mhar_domain_alignment_screening.json` — unlabelled-target CORAL
  screen; and
- `catalyst_optimizer_mhar_summary.json` — deterministic validation and
  decision aggregate.

`aggregate_catalyst_optimizer_mhar_results.py` validates all linked design
hashes and records all result hashes. These experiments are retrospective
method development: no candidate passed both frozen dataset gates, and the
post-outcome standard/MHAR expert complementarity is not promotion evidence.

The target-free router experiments add
`catalyst_opd_router_smoke_summary.json`,
`catalyst_opd_sft_cold_start_summary.json`, and
`catalyst_numeric_expert_router_summary.json`. The detailed 34-edge numeric
router audit is `catalyst_numeric_expert_router.json`. Both the LLM/OPD path
and the numeric-router path failed their frozen held-out gates; neither is a
promotion result.
