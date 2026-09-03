# Claude Science current-manuscript handoff

## Authority and scope

This package is for scientific restructuring and revision of the current
manuscript. `analysis/MANUSCRIPT_DRAFT_STREAMLINED.md` is the only authoritative
main-text draft. Older drafts and older Claude bundles are provenance records
and must not be used as alternative manuscripts.

Target venue: *Digital Discovery*. The desired standard is a concise,
mechanistically disciplined materials-informatics paper with high-impact
clarity, not inflated universality.

## Fixed scientific thesis

Heterogeneous experimental data do not automatically yield a universal law or
a universally useful transfer model. Neighbouring experimental programmes can,
however, reduce a data-poor recipient's out-of-distribution knowledge deficit
when the donor-recipient relation, experimental state, transferred scientific
object, provenance boundary, and decision endpoint are matched. An audited
edge is routed to numerical prediction, candidate ranking, or abstention.

The paper's contribution is an actionable and falsifiable knowledge-borrowing
map, not a claim that physical adjacency guarantees benefit.

## Claim-bearing evidence

- A relation trained on 10,407 experimental electrolyte measurements crossed
  an unseen-salt database boundary. A semantic audit restricted the public
  archive to 1,660 strict LiAsF6 rows (156 formulations), yielding raw-scale
  R2 = 0.607, Spearman rho = 0.864, and 27.41% lower log-RMSE than state-only.
- In an OOD screening task, a zero-label programme-balanced donor score ranked
  candidates at rho = 0.910, versus rho = 0.537 for the strongest of 13
  recipient-only configurations trained on five measured formulations. The
  contrast is delta rho = 0.374, with a 95% anchor-selection interval of 0.213
  to 0.562 conditional on this recipient.
- A controlled catalyst series shows that the same kind of transferred relation
  may support numerical prediction, ranking only, or harm, depending on state
  and endpoint alignment.
- A systematic benchmark across eight recipients and forty real donor edges
  found that generic donor-feature injection repaired none of the prespecified
  OOD tasks. This is a central falsification result.
- Null, harmful, and abstaining edges define the boundary of the map and must
  not be removed to make the story appear uniformly positive.

All quantitative statements must be checked against the supplied verified
summary, experiment matrix, attempt ledger, or supplementary information.

## Non-negotiable interpretation boundaries

- Do not present shared specimens or shared measurement events as independent
  cross-database transfer.
- Do not present a ranking gain as calibrated numerical-prediction gain.
- Do not present retrospective screening as prospective laboratory discovery.
- Do not revive effects around 1-2% as substantive without uncertainty,
  matched controls, absolute utility, and a scientific consequence.
- Do not replace failed generic transfer with a vague claim that all adjacent
  fields are useful.
- Do not change verified values or invent missing sample sizes, citations, or
  data-access facts.

## Reading order

1. `01_manuscript/MANUSCRIPT_DRAFT_STREAMLINED.md`
2. `01_manuscript/SUPPLEMENTARY_INFORMATION.md`
3. `02_evidence/CORE_STORY_EVIDENCE_SELECTION_2026-07-30.md`
4. `02_evidence/CORE_STORY_EXPERIMENT_MATRIX.md`
5. `02_evidence/ATTEMPT_LEDGER.csv`
6. `analysis/results/main_figures_v4_verification.json`
7. `03_reviews/PRESUBMISSION_REVIEW.md`
8. `03_reviews/MANUSCRIPT_STORY_AND_FLOW_AUDIT_2026-07-31.md`
9. `04_data/DATABASE_GUIDE.md`
10. the five canonical figures listed in `analysis/PAPER_PACKAGE.md`

## Requested work

First audit the claim-evidence chain and identify scientific weaknesses that
could still cause rejection. Then recommend a single streamlined story and
revise the title, abstract, four-paragraph Introduction, Results transitions,
Discussion, and figure legends. Preserve the distinction among numerical
prediction, ordinal screening, and abstention. Move nonessential evidence to
the supplement instead of accumulating cases.

For each proposed change, name the source file that supports it. Separate
manuscript-ready English from concise Chinese explanations of major scientific
decisions. Recommend at most three additional analyses, ranked by their likely
effect on acceptance probability; do not recommend more databases merely for
breadth.
