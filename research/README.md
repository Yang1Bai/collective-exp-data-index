# Organized research package

This directory is the stable public entry point for the data-driven methods
paper developed in this repository. It deliberately separates four layers
that should not be confused:

1. the **127-resource discovery catalog**, which maps experimental data that
   may be useful to the community;
2. the **analysed resource portfolio**, whose data entered at least one audit,
   model, control, or validation in this project;
3. the **paper-facing evidence**, which contains only the experiments required
   to support the current argument; and
4. the **complete attempt record**, which also retains null, harmful,
   non-evaluable, and method-development results.

## Scientific argument

When scientific knowledge is incomplete, heterogeneous experimental data do
not automatically yield a universal law or a universally useful transfer
model. However, neighbouring experimental programmes can reduce a recipient's
OOD knowledge deficit when the donor-recipient relation, experimental state,
transferred object, provenance boundary, and decision endpoint are matched.
The method therefore routes an audited edge to numerical prediction, candidate
ranking, or abstention instead of assuming that every adjacent database should
be pooled.

The main positive evidence is intentionally compact: a relation trained on
10,407 experimental electrolyte measurements crossed an unseen-salt database
boundary with raw-scale R2 = 0.629 and Spearman rho = 0.871; a programme-balanced
source score then improved five-label OOD candidate ranking from rho = 0.537 to
0.910 (delta rho = 0.374, 95% interval 0.213-0.562). A controlled catalyst
series shows that the same transferred relation can yield numerical benefit,
ranking-only benefit, or harm. The 40-edge generic-injection benchmark and the
frozen second-recipient electrolyte test provide the principal falsification
and boundary evidence.

## Where to start

| Need | Canonical entry |
|---|---|
| Latest manuscript | [`analysis/MANUSCRIPT_DRAFT_STREAMLINED.md`](../analysis/MANUSCRIPT_DRAFT_STREAMLINED.md) |
| Supplementary information | [`analysis/SUPPLEMENTARY_INFORMATION.md`](../analysis/SUPPLEMENTARY_INFORMATION.md) |
| Submission and figure package | [`analysis/PAPER_PACKAGE.md`](../analysis/PAPER_PACKAGE.md) |
| Current four-figure architecture | [`analysis/CORE_STORY_EVIDENCE_SELECTION_2026-07-30.md`](../analysis/CORE_STORY_EVIDENCE_SELECTION_2026-07-30.md) |
| Human-readable experiment matrix | [`analysis/CORE_STORY_EXPERIMENT_MATRIX.md`](../analysis/CORE_STORY_EXPERIMENT_MATRIX.md) |
| Machine-readable experiment registry | [`analysis/core_story_experiment_registry.json`](../analysis/core_story_experiment_registry.json) |
| Complete positive/null/harm attempt ledger | [`evidence/ATTEMPT_LEDGER.csv`](evidence/ATTEMPT_LEDGER.csv) |
| Analysed database access and licence ledger | [`data/ANALYSED_RESOURCE_LEDGER.csv`](data/ANALYSED_RESOURCE_LEDGER.csv) |
| Edison/Kosmos reports and validation | [`../analysis/review_packages/edison/README.md`](../analysis/review_packages/edison/README.md) |
| Full experimental-resource catalog | [`../CATALOG.md`](../CATALOG.md) and [`../catalog/catalog.csv`](../catalog/catalog.csv) |
| Reproducibility index | [`../analysis/README.md`](../analysis/README.md) |

## Paper-facing figures

The canonical files are the editable SVG, review PDF, screen-resolution PNG,
and submission TIFF for each figure:

- Figure 1: `analysis/figures/knowledge_borrowing_overview_ai_v4.*`
- Figure 2: `analysis/figures/figure2_failure_benchmark_nmi_v3.*`
- Figure 3: `analysis/figures/figure3_relation_transfer_nmi_v3.*`
- Figure 4: `analysis/figures/figure4_ordinal_screening_nmi_v3.*`

Figure-generation scripts and semantic verification are versioned beside the
manuscript. Large obsolete TIFF exports are excluded because they are
deterministically regenerated and do not add scientific information.

## What is and is not redistributed

This repository versions original code, protocols, freezes, compact result
summaries, verification records, derived source data for figures, and the AI
research reports required to reconstruct the decision trail. It does **not**
re-host local working copies of publisher supplements, licensed archives, or
multi-gigabyte row-level intermediates. Those files retain upstream ownership
and licence terms. Their authoritative DOI/URL, access status, role in the
project, and redistribution decision are recorded in the analysed-resource
ledger.

The code licence is defined by [`LICENSE`](../LICENSE). Catalog metadata follow
[`LICENSE-DATA.md`](../LICENSE-DATA.md). Neither licence overrides the terms of
an upstream experimental dataset.

## Release rule

An analysis may influence the manuscript only if its design and leakage unit
are explicit, its source and target files are hashable, its result is retained
whether positive or negative, and its claim does not exceed the endpoint it
actually tested. Post-outcome analyses are labelled as method development and
cannot be converted retroactively into independent confirmation.
