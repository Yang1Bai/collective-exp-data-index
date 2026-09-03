# Claim–evidence audit and revision plan — MANUSCRIPT_DRAFT_STREAMLINED.md
**Date:** 2026-07-31 · **Target venue:** *Digital Discovery* (methods-led Full paper)
**Authority:** `01_manuscript/MANUSCRIPT_DRAFT_STREAMLINED.md` is the only manuscript audited. All other files are used as evidence or provenance, per `START_HERE.md`.

---

## 1. Files accessed (reading order per START_HERE.md)

| # | File | Status |
|---|---|---|
| 1 | `01_manuscript/MANUSCRIPT_DRAFT_STREAMLINED.md` | read in full |
| 2 | `01_manuscript/SUPPLEMENTARY_INFORMATION.md` | read in full |
| 3 | `02_evidence/CORE_STORY_EVIDENCE_SELECTION_2026-07-30.md` | read in full |
| 4 | `02_evidence/CORE_STORY_EXPERIMENT_MATRIX.md` | read in full |
| 5 | `02_evidence/ATTEMPT_LEDGER.csv` | read in full (27 attempts A01–A27) |
| 6 | `02_evidence/main_figures_nmi_v3_VERIFIED.json` | read in full |
| 7 | `03_reviews/PRESUBMISSION_REVIEW.md` | read in full |
| 8 | `03_reviews/MANUSCRIPT_STORY_AND_FLOW_AUDIT_2026-07-31.md` | read in full |
| 9 | `04_data/DATABASE_GUIDE.md` | read in full |
| 10 | `05_figures/` all four figures (PNG, visual inspection) + `FIGURE_QA_NMI_V3.md` | inspected |
| — | `01_manuscript/PAPER_PACKAGE.md`, `03_reviews/MANUSCRIPT_STREAMLINING_MAP.md`, `04_data/README.md`, `FILE_MANIFEST.tsv` | scanned for consistency (provenance only) |
| — | `01_manuscript/REFERENCES.bib`, `RELATED_WORK.md`, `EDISON_REPORT_ASSESSMENT_2026-07-29.md`, `core_story_experiment_registry.json`, `ANALYSED_RESOURCE_LEDGER.csv` | present, not required by the reading order; not used for the audit below |

All headline numbers in the draft were cross-checked against `ATTEMPT_LEDGER.csv`, `main_figures_nmi_v3_VERIFIED.json`, and SI §S10.3 and match: 0/40 (A02, S10), raw R²=0.629 / ρ=0.871 / 28.64% (A23, figure3 block), Δρ=0.374 [0.213, 0.562] (A24, `primary_delta`=0.3737), FINALES −0.089 [−0.293, 0.096] (A25, `frozen_delta`=−0.0887), SpecGen 16.3%/26.1%/ranking-only/harmful (A22, §3.3).

---

## 2. Claim–evidence audit: weaknesses that could still cause rejection

Ranked by rejection risk. Each item names the supporting source file(s).

### W1 — No outcome-frozen positive edge exists anywhere in the evidence base (highest risk)
Every main-text positive is disclosed post-outcome method development: the unseen-salt benchmark was designed after the public recipient outcomes and the published transfer observation were known (manuscript §2.6); the SpecGen composition donor was promoted post-primary after target-correlation inspection (§2.5); the SolventSeg stress test was specified after SolventSeg and FINALES outcomes were inspected (SI §S10.3). The only fully frozen confirmatory tests — FINALES (§3.5), Starrydata and TRI (SI §S9), and CS13 — are a rejection, two nulls, and a missing item respectively (`CORE_STORY_EXPERIMENT_MATRIX.md` CS03/CS09/CS13). A referee can compress this into one sentence: *"whenever the authors froze the design before outcomes, the method did not win."*
**Mitigation (presentation, not new experiments):** state the retrospective status once in the Abstract; in Discussion §4.3, own the asymmetry explicitly and reframe it — the frozen tests are the demonstration that the falsification machinery actually rejects edges, and the prospective recipient is the designed next test, with its contract already specified. Do not let the qualifier be discoverable only in Methods §2.6.

### W2 — The ordinal headline is worded so that it misstates what used the five labels
The programme-balanced score uses **zero** recipient labels; the five measured formulations parameterize only the 13 recipient-only baselines and the anchor-exclusion split (SI §S10.3: "mean ρ=0.9103 … the strongest average recipient-only model … 0.5366"). But the Abstract says the score "ranked unseen formulations **from five recipient measurements** at ρ=0.910", and the Figure 1 legend says "five recipient measurements **raise** candidate ordering from ρ=0.537 to 0.910". Both read as if the labels feed the score, and "raise from 0.537 to 0.910" implies a within-model improvement rather than a between-model comparison. This is exactly the kind of wording the project's non-negotiable boundaries forbid.
**Fix:** rewrite as a comparison: zero-label donor score ρ=0.910 versus the strongest of 13 recipient-only models trained on the same five measured formulations, ρ=0.537 (Δρ=0.374). Apply in Abstract, §1 ¶4, §3.4, Conclusions, Figure 1b and Figure 4 legends. Source: SI §S10.3; `ATTEMPT_LEDGER.csv` A24.

### W3 — Single-recipient inference behind the headline interval
The Δρ 95% interval (0.213–0.562) is the 2.5th–97.5th percentile over 100 anchor selections within one 36-formulation recipient (SI §S10.3). It quantifies anchor-selection variability conditional on SolventSeg, not transfer uncertainty across programmes. Stating this in one clause costs nothing and makes the FINALES rejection (§3.5) coherent rather than contradictory.
**Fix:** add "conditional on this recipient programme" where the interval is first reported (§3.4) and in the Figure 4b legend. Source: SI §S10.3.

### W4 — The 0/40 falsification is mechanism-bounded and the main text hides its strongest defence
§3.1 tests one generic mechanism (cross-fitted donor prediction as one feature; Ridge primary, RF/ExtraTrees sensitivities — SI §S10). A referee will call this a weak strawman ("nobody transfers like that; fine-tuning is the standard"). The evidence base already contains the rebuttal: SI §S10.2 shows that strong Chemprop source encoders with passing source-skill gates made scaffold-OOD hydrogen evolution **worse** by 28.1% on average — model strength and representation transfer do not rescue the generic route. This is invisible in the main text.
**Fix:** one sentence at the end of §3.1 citing SI §S10.2, so the falsification covers both feature injection and pretrained-representation transfer within the tested envelope. Sources: SI §S10, §S10.2; `ATTEMPT_LEDGER.csv` A17.

### W5 — The FINALES boundary is an underpowered null presented with slightly too much confidence
n=16 evaluated formulations; Δ=−0.089 [−0.293, 0.096], permutation p=0.131 (§3.5; A25). The data are compatible both with no donor benefit and with a modest benefit. The current §3.5 heading ("converts non-transfer into abstention") and "It did not replicate" assert non-transfer; the defensible claim is "failed to qualify under the frozen contract → abstain". The distinction matters because abstention is the paper's own third route.
**Fix:** retitle §3.5 and adjust two sentences; optionally add the minimum-detectable-effect diagnostic (Analysis 1 below). Sources: manuscript §3.5; `main_figures_nmi_v3_VERIFIED.json` `frozen_delta`.

### W6 — Internal count inconsistency: 21 resources
Manuscript §2.1: "Thirteen … normalized locally, **seven** entered through frozen task-specific representations, and … NIST … streamed" (13+7+1=21). SI §S2 prose: "**Six** enter as frozen external or temporal programmes" (13+6+1=20), while SI Table S1 itself lists seven frozen entries (Caltech ionic, multi-stage battery, Acid-OER, ORR, Starrydata2, TRI, SpecGen). Fix SI §S2 to "seven". Sources: manuscript §2.1; SI §S2 + Table S1.

### W7 — SI companion header is stale
The SI title ("From pooled regularities to selective priors: artifact-gated knowledge borrowing…") does not match the manuscript title, and the SI declares itself the companion to `MANUSCRIPT_DRAFT.md`, not `MANUSCRIPT_DRAFT_STREAMLINED.md`. Under START_HERE's authority rule this is a provenance error a careful referee or editor will notice. Source: SI header; `START_HERE.md`.

### W8 — Terminology drift
"Component-order-invariant" (Abstract, §3.2, Fig 3a art) vs "permutation-invariant" (§2.2 item 2, `PAPER_PACKAGE.md`); "equal-programme" vs "programme-balanced" for the same score (§3.4 vs Fig 4a). Standardize on **component-order-invariant** (already printed in Figure 3a — cheapest to align) and **programme-balanced**, with one parenthetical alias at first use. Sources: manuscript §2.2/§3.2/§3.4; figures.

### W9 — Residual "rescue" rhetoric in a figure title
Figure 4 legend title: "Cross-programme knowledge **rescues** candidate ordering…". Reviewer 3 in `PRESUBMISSION_REVIEW.md` flagged exactly this word class. Replace with "recovers". The §3.4 body text already uses "rescue" once ("can neighbouring knowledge … rescue"? — it uses "identify which unseen candidates should be measured first": fine).

### W10 — Non-scientific submission blockers still open
Persistent release DOI, clean-environment reproduction, author metadata/CRediT, ESTM redistribution ambiguity (SI §S12 unchecked items; `PRESUBMISSION_REVIEW.md` "Missing materials"). These are outside the manuscript text but will block acceptance regardless of prose quality.

**What is NOT weak.** The leakage architecture (intact-unit splits, cross-fitting, provenance audits, matched false donors, Holm families), the retention of null/harmful edges, the endpoint separation, and the verified figure pipeline are the paper's strongest assets and need no structural change. The evidence-selection file and the story audit have already produced a defensible single narrative; the remaining problems are claim hygiene and disclosure placement, not evidence gaps — consistent with the presubmission verdict ("major revision to presentation, not another retrospective experiment cycle").

---

## 3. Recommended single streamlined story

Keep the existing five-rung ladder — it is correct and already matches `CORE_STORY_EVIDENCE_SELECTION_2026-07-30.md` and the story audit. State it everywhere in this exact logical order:

1. **Generic reuse fails** — 0/40 declared OOD edges repaired by donor-feature injection; coefficient transport R²=−3.006 (A02, A09).
2. **A qualified relation crosses** — component-order-invariant mixture relation: unseen salt, raw R²=0.629, ρ=0.871, 28.64% lower log-RMSE (A23).
3. **The same relation must be routed** — SpecGen controlled series: predict+rank ×2, ranking-only ×1, reject ×1 (A22).
4. **Order transfers when scale does not** — SolventSeg: zero-label score ρ=0.910 vs best five-label recipient model 0.537 (A24).
5. **The map must abstain** — frozen FINALES contract fails to qualify (A25).

One structural change only: compress the Meyer–Neldel/ISODB compensation paragraph in §3.1 to a single sentence pointing to SI §S7 (it is a third failure mode inside a section that needs only two, and `CORE_STORY_EVIDENCE_SELECTION` already lists compensation audits as supplement-only).

---

## 4. Change log (every proposed change → supporting source)

| # | Location | Change | Supporting source |
|---|---|---|---|
| C1 | Title | Replace unconditional "improves" with routing formulation (options in revision file) | `PRESUBMISSION_REVIEW.md` (Reviewer 2: title must sell the map, not a general effect); `START_HERE.md` thesis |
| C2 | Abstract | Add "retrospective" qualifier once; fix W2 wording; state abstention as an outcome, not a failure | §2.6 of the manuscript itself; SI §S10.3; `CORE_STORY_EVIDENCE_SELECTION` claim boundary |
| C3 | Abstract + §3.4 + Fig 1b/4 legends | Zero-label score vs five-label recipient-only comparison wording | SI §S10.3; A24 |
| C4 | §1 ¶4 | Tighten roadmap; same W2 fix; end on map contribution | `MANUSCRIPT_STORY_AND_FLOW_AUDIT` question sequence |
| C5 | §2.2 item 2 | Rename "Permutation-invariant" → "Component-order-invariant (permutation-invariant) mixture prediction" | W8; Figure 3a printed text |
| C6 | §3.1 ¶2 | Compress compensation results to one sentence → SI §S7 | `CORE_STORY_EVIDENCE_SELECTION` supplement-only list |
| C7 | §3.1 end | Add one sentence citing SI §S10.2 (pretrained-encoder failure) | SI §S10.2; A17 |
| C8 | §3.2 end → §3.3 open | Explicit bridge: external feasibility ≠ uniform usage; hand off to routing | Story audit transition rules |
| C9 | §3.4 | Add "conditional on this recipient programme" to the Δρ interval; fix comparison wording | SI §S10.3 |
| C10 | §3.5 heading + 2 sentences | "Fails to qualify → abstain" instead of "non-transfer"; report p=0.131 and interval as compatible-with-zero | A25; W5 |
| C11 | §4.3 | Own the frozen-negative asymmetry; specify the prospective contract as the designed next test | CS13 (`CORE_STORY_EXPERIMENT_MATRIX`); presubmission verdict |
| C12 | Fig 1b legend | Rewrite screening line (W2); label evidence values as committed-result-table values | SI §S10.3; `FIGURE_QA_NMI_V3.md` claim guards |
| C13 | Fig 4 legend | "rescues" → "recovers"; interval definition; frozen-recipient wording | W9; W3; Reviewer 3 |
| C14 | SI §S2 | "Six" → "seven" frozen programmes | W6; SI Table S1 |
| C15 | SI header | Retitle to match manuscript; point to `MANUSCRIPT_DRAFT_STREAMLINED.md` | W7; `START_HERE.md` |
| C16 | Throughout | Standardize "programme-balanced score" (alias "equal-programme weighting" once, in Methods §2.2) | W8 |

---

## 5. Recommended additional analyses (max 3, ranked by effect on acceptance probability)

**A1 — Minimum-detectable-effect diagnostic for the frozen FINALES boundary.** *(highest impact / lowest cost; no new data)* With 16 evaluation formulations and the frozen bootstrap, compute the smallest donor concordance advantage detectable at 80% power. Report it in §3.5 in one sentence beside Δ=−0.089 [−0.293, 0.096]. It converts the weakest headline element (an underpowered null driving a headline "rejection") into a precise abstention statement: the contract failed to qualify, and effects smaller than the MDE were not resolvable. Declared as a disclosed post-outcome diagnostic; the frozen decision is unchanged. Primary estimand: MDE for pairwise concordance advantage; leakage unit: formulation; falsification outcome: none (diagnostic).

**A2 — One alternative generic-transfer arm on the eight designated edges.** *(closes the W4 strawman attack)* Re-run only the eight designated donor–recipient edges from the S10 benchmark with a second generic mechanism — donor-model anchored-delta / residual-correction transfer (the object the project itself identified as more portable, A05) — under the identical splits, draws, controls, and complete OOD-repair gate. Prespecified expectation: it also fails the complete gate generically, extending the falsification from "donor-feature injection" to "generic donor correction", or it passes somewhere and the map gains an edge; either outcome strengthens the paper. Declared post-outcome method development; OOD split, leakage units, controls, and Holm family inherited from `multi_target_ood_borrowing_design.json`.

**A3 — Anchor-set sensitivity for the SpecGen five-anchor effects.** *(preempts "one lucky anchor set")* The catalyst analysis uses one outcome-independent five-anchor selection per system (§2.5); the reported intervals bootstrap candidates, not anchors. Repeat the frozen borrowed-vs-target-only contrast over ~100 outcome-independent anchor selections per derivative system and report the distribution of RMSE and ρ gains (the SolventSeg design already does exactly this — reuse its machinery). Routing decisions stand if the sign structure (predict+rank / ranking-only / reject) is stable across anchor draws.

**Explicitly not recommended:** any new database or recipient added for breadth (per `START_HERE.md`), and any attempt to upgrade the retrospective claims by re-running frozen designs. CS13 (prospective test) remains the acceptance requirement only for discovery-acceleration claims, which this manuscript correctly does not make.
