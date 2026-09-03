# Digital Discovery submission checklist

> **Historical checkpoint:** this checklist was frozen on 2026-08-14 and is
> retained for provenance. The current claim, model, data and figure allowlist
> is [`paper/README.md`](../../paper/README.md). In particular, 0.885 versus
> 0.162 is the formal SolventSeg route-defining comparison; 0.910 versus 0.537
> is the separate 13-model baseline-sensitivity analysis.

**Canonical manuscript:** `analysis/submission/SUBMISSION_MANUSCRIPT.md`
**Frozen on:** 2026-08-14, from `analysis/MANUSCRIPT_DRAFT_STREAMLINED.md` + verified result JSONs.

## Scientific readiness verdict

**Yes — scientifically defensible for *Digital Discovery* as a methods-led full paper**, with the following character:

- Every `paper_submission_required` experiment in `analysis/core_story_experiment_registry.json` (15 experiments) is `complete` or `complete-boundary`.
- Claim boundary is explicit and honest: retrospective; no universal transfer; no prospective acceleration.
- Main positive evidence: LiAsF₆ relation transfer (log-RMSE −27.41%, CI 21.79–32.92; ρ=0.864; raw R²=0.607) and SolventSeg ordinal screening (ρ=0.910 vs 0.537 recipient-only; Δρ=0.374, CI 0.213–0.562; Holm p=0.00070).
- Boundary evidence: 0/40 generic OOD-repair gates; frozen FINALES second-recipient non-qualification (Δ=−0.089, CI −0.293 to 0.096); outcome-unseen Starrydata/TRI nulls; negative-transfer and abstention cases retained.
- Independent audits: Edison (hypothesis generation + validation), Claude science review (two passes), adversarial presubmission review (`analysis/PRESUBMISSION_REVIEW.md`).

**Bottom line:** with a DOI, a clean Linux reproduction, author metadata, and RSC formatting completed, this is a submittable *Digital Discovery* paper. It is not a Nature Comment.

## What is already submission-ready

- [x] Main manuscript text (English; full Introduction/Methods/Results/Discussion/Conclusion)
- [x] Supplementary Information (12 sections, evidence hierarchy, tables S1–S10, null/harmful boundaries)
- [x] Five main figures with canonical exports (SVG/PDF/PNG/TIFF) and semantic verification
  - `analysis/figures/knowledge_borrowing_overview_ai_v4.*`
  - `analysis/figures/figure2_failure_benchmark_nmi_v3.*`
  - `analysis/figures/figure3_relation_transfer_nmi_v3.*`
  - `analysis/figures/figure4_routing_nmi_v4.*`
  - `analysis/figures/figure5_ordinal_screening_nmi_v4.*`
- [x] Experiment registry (`analysis/core_story_experiment_registry.json`, 15 experiments)
- [x] Attempt ledger incl. null/harmful/abstaining (`research/evidence/ATTEMPT_LEDGER.csv`, 27 attempts)
- [x] Resource and licence ledger (`research/data/ANALYSED_RESOURCE_LEDGER.csv`, 31 resources)
- [x] Verification records for headline metrics (e.g. `analysis/results/main_figures_nmi_v3_VERIFIED.json`, `finales_rank_replication_summary.json`, `bamboomixer_*_summary.json`, `specgen_composition_secondary_summary.json`)
- [x] References (`analysis/REFERENCES.bib`, 48 entries) with citation verification (`analysis/CITATION_VERIFICATION.md`)
- [x] Paper package (`analysis/PAPER_PACKAGE.md`) and presubmission review (`analysis/PRESUBMISSION_REVIEW.md`)

## What must be completed before submission (in priority order)

1. **Persistent release DOI.** Archive the exact frozen commit at Zenodo/figshare; record the DOI in the manuscript Data availability section and CITATION.cff.
2. **Clean Linux reproduction.** Run the full test suite (118 tests) plus the five verification scripts on a clean environment; add a `REPRODUCTION.md` log with environment hashes.
3. **Author metadata.** Fill CRediT author contributions, affiliations, ORCIDs, funding, acknowledgements, and conflicts in the manuscript.
4. **RSC formatting.** Convert the markdown into the RSC template (Digital Discovery Word/LaTeX), including journal-style citations from `REFERENCES.bib`.
5. **Optional but valuable.** Add a related-work comparison table to the Supplementary Information (transfer-learning, negative-transfer, applicability-domain, rank-fusion references) and freeze one outcome-sealed third recipient or prospective shortlist as the independent confirmation test.

## Notable caveats to keep visible in the paper

- The main positive results are retrospective/post-outcome; do not convert them into prospective claims.
- BambooMixer lacks row-level DOI provenance; the interaction analysis is explicitly "post-outcome cross-database method development".
- The leave-one-programme admission gate (CS14) is method-development-complete, not a validated universal selector.
- CS13 (prospective/temporal candidate test) is complete-boundary, not an independent confirmation.
- The 0.910 ordinal result is conditional on the SolventSeg recipient; FINALES shows it does not generalize unconditionally.
