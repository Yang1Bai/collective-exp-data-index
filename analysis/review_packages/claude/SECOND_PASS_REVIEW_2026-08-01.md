# Second-pass adversarial review — *Falsification-gated borrowing routes neighbouring experimental knowledge to out-of-distribution prediction, screening or abstention*

**Role:** adversarial co-author / referee · **Date:** 2026-08-01 · **Venue:** *Digital Discovery*, methods-led Full paper
**Scope:** second pass after selective integration of the 2026-07-31 audit. First-pass findings W1–W10 are not re-litigated; only their implementation is checked (§2), and all new findings in §3 are issues the first pass did not raise.

---

## 1. Files accessed

Complete prescribed reading order, all opened successfully:

| # | File | Status |
|---|---|---|
| 1 | `01_current/MANUSCRIPT_DRAFT_STREAMLINED.md` | read in full (41,487 B) |
| 2 | `01_current/SUPPLEMENTARY_INFORMATION.md` | read in full, plus targeted re-reads of §S2, §S9, §S10, §S10.2, §S10.3, §S12 |
| 3 | `01_current/PAPER_PACKAGE.md` | read |
| 4 | `02_integration/CLAUDE_MANUSCRIPT_REVIEW_INTEGRATION_2026-07-31.md` | read in full |
| 5 | `02_integration/MANUSCRIPT_AUDIT_2026-07-31.md` | read (own first-pass output; used only for QA cross-check) |
| 6 | `02_integration/REVISED_SECTIONS_EN_2026-07-31.md` | read (own first-pass output) |
| 7 | `03_evidence/CORE_STORY_EVIDENCE_SELECTION_2026-07-30.md` | read |
| 8 | `03_evidence/CORE_STORY_EXPERIMENT_MATRIX.md` | read; byte-identical to the first-pass copy |
| 9 | `03_evidence/ATTEMPT_LEDGER.csv` | read; byte-identical to the first-pass copy |
| 10 | `03_evidence/main_figures_nmi_v3_VERIFIED.json` | read; byte-identical to the first-pass copy |
| 11 | `04_figures/` — all four PNGs | inspected visually; SHA-256 identical to the first-pass exports (figures were **not** regenerated) |
| — | `PROMPT_FOR_CLAUDE_SCIENCE_SECOND_PASS.md`, `FILE_MANIFEST.tsv` | read |
| — | `01_current/TERMINOLOGY_LEDGER.md` (new in this bundle) | read in full |
| — | `01_current/RELATED_WORK.md`, `01_current/REFERENCES.bib` | read for the novelty stress test (§4); 44 bibliography keys enumerated |
| — | `02_integration/DECISIONS_ZH_2026-07-31.md` | present, not re-reviewed (own prior output) |

**Verified unchanged since the first pass:** attempt ledger, experiment matrix, verified-figure JSON, and all four figure files. Every quantitative claim below is therefore checked against the same committed evidence.

---

## 2. Integration QA table

| First-pass item | Required change | Implemented? | Evidence |
|---|---|---|---|
| **W1** frozen-negative asymmetry | Own it in Discussion, correctly scoped | **Yes, and correctly narrowed.** §4.3 now says "Every independent external validation whose complete route was frozen before recipient-outcome access ended in null, rejection, or abstention", naming FINALES/Starrydata/TRI. It does not overclaim "all frozen analyses are negative", preserving the internally frozen positive KIT result | MS §4.3; integration record "Disposition" |
| **W1b** do not let a frozen negative masquerade as validation | Add the symmetric caveat | **Yes** — "nor does a frozen negative validate the framework by itself" (§4.3 ¶2). This is a stronger and more honest formulation than the first pass proposed | MS §4.3 ¶2 |
| **W2** zero-label vs five-label | Rewrite as a between-model comparison everywhere | **Yes, completely.** Zero occurrences of "raise … from 0.537 to 0.910" remain in MS, SI or paper package. Abstract, §1 ¶4, §3.4, §5, Fig 1b and Fig 4b all now read "zero-label … whereas the strongest of 13 recipient-only models trained on five measured formulations". Locked in `TERMINOLOGY_LEDGER.md` | grep across `01_current/`; MS lines 25, 94, 444, 585, 643, 682 |
| **W3** interval interpretation | Label as anchor-selection variability within one recipient | **Yes**, in all four places: Abstract ("95% anchor-selection interval within this recipient"), §3.4, Fig 4b caption, `PAPER_PACKAGE.md` | MS + package |
| **W4** 0/40 is mechanism-bounded | Surface the pretrained-encoder null | **Yes** — new §3.1 ¶4: "Nor was model capacity the explanation… 28.1% worse… failed against their own shuffled controls (Supplementary Section S10.2)" | MS §3.1 |
| **W5** FINALES wording | "Fails to qualify → abstain", not "non-transfer" | **Yes.** Heading changed; "compatible with harm, no effect, or a modest donor advantage" added; p=0.131 retained in text | MS §3.5 |
| **W6** resource arithmetic | SI "six" → "seven" | **Yes.** SI §S2 now reads "Seven enter as frozen external or temporal programmes", reconciling 13+7+1=21 with MS §2.1 and Table S1 | SI §S2 |
| **W7** SI header | Retitle, repoint companion file | **Yes.** SI H2 matches the new manuscript title; companion pointer is now `MANUSCRIPT_DRAFT_STREAMLINED.md` | SI header |
| **W8** terminology | Canonicalize two term pairs | **Yes**, and better than requested: a `TERMINOLOGY_LEDGER.md` now locks the forms. One residual: SI line 824 still says "equal programme weight" in prose. Immaterial — it is a methods description, not a term of art, and the ledger permits "equal-programme" as the parenthetical alias | MS §2.2; SI 824 |
| **W9** "rescues" in Fig 4 title | Replace with "recovers" | **Yes.** Zero occurrences of "rescue" remain anywhere in the manuscript | grep, 0 hits |
| **W10** release blockers | Author/release task | **Not addressed and correctly deferred**; SI §S12 still shows four unchecked items (persistent DOI, clean-environment run, author metadata, ESTM redistribution). These remain acceptance-blocking regardless of prose | SI §S12 |
| Compensation compression | One sentence → SI §S7 | **Yes** | MS §3.1 ¶2 |
| Title | Routing formulation | **Yes**, recommended option adopted verbatim; propagated to SI and paper package | all three files |
| Figures | Legends only, no re-rendering | **Legends updated; figure files unchanged (hash-identical).** This is a defect only where a legend now describes something the panel does not show — see R2 and §5 | SHA-256 comparison |

**Contradictions found: one, and it is consequential.** Figure 4b's caption now reads "The zero-label source ranking compared with 13 recipient-only configurations trained on five measured formulations", but the panel itself lists **15 rows** (the source score, the per-draw oracle, and 13 recipient-only models) — consistent — while `main_figures_nmi_v3_VERIFIED.json` records `figure4.models = 15`. No error, but the caption should say "13 recipient-only configurations and a non-deployable per-draw oracle (15 rows)" so the verifier field and the caption are trivially reconcilable by a referee. Minor.

**One wording residue that survives the W2 fix.** §3.4 ¶1 still reports the *whole-recipient* figures ("the unchanged three-programme source score achieved ρ=0.918, precision 1.000, zero regret") immediately before the anchor-averaged figures. Both are correct, but a reader meets 0.918 and 0.910 in consecutive sentences with no statement of which one is the claim. See §6, replacement T4.

---

## 3. Remaining scientific rejection risks (five, none from the first pass)

### R1 — The falsification set and the demonstration set are disjoint, so "generic fails / qualified works" is confounded with a change of data
**Severity: major.** This is now the strongest available attack and the paper walks into it in the Abstract ("…repaired 0 of 40 declared OOD edges… **In contrast**, a component-order-invariant electrolyte relation…").

The 40-edge benchmark covers eight recipients — alloy yield strength, catalytic H₂ selectivity, electrolyte conductivity, hydration free energy, polymer tensile strength, polymer melting temperature, aqueous solubility, thermoelectric ZT (SI Table S10). The three main-text positives use BambooMixer→LiAsF₆, three conductivity programmes→SolventSeg, and SpecGen→four derivative systems. **Not one positive edge is in the 40, and not one of the 40 failed edges was retried with a declared relation, an anchored correction, or an ordinal route.** The manuscript therefore demonstrates that mechanism A fails on edge set X and mechanism B succeeds on edge set Y. That does not license "in contrast".

- *Unsupported inference:* that the qualified route repairs what generic injection could not.
- *Missing comparison:* the qualified/anchored route applied to at least one designated edge from the S10 benchmark.
- *Fix level:* **wording** for the minimum; **new computation** (existing machinery, existing frozen splits) for the strong fix — this is proposed analysis (3), and it is the only one of the three that touches this risk.
- *Minimum defensible fix:* replace "In contrast" with a construction that names the set change, and add one sentence to §3.1 or §4.1 stating that the benchmark bounds the generic mechanism within its tested envelope and does not establish that the declared-relation route would repair those same edges.
- *Publishable without the computation?* **Yes**, provided the wording fix is made. Without the wording fix, this is the sentence a referee quotes when recommending rejection.

### R2 — "Carried unchanged into a second programme" overstates comparability: the anchor policy differs, and the FINALES estimate rests on a single anchor draw
**Severity: major.** SolventSeg anchors are chosen by outcome-independent maximin coverage, averaged over **100 draws** at budgets 3/5/10, with the selected formulations excluded wholesale (MS §2.7; SI §S10.3). FINALES anchors are "the first three chronologically distinct formulations" — **one draw**, chronologically determined, in an autonomous campaign whose early formulations are plausibly a designed coverage grid and therefore an unusually favourable training set for the recipient-only comparator (MS §2.7). Evaluation is 16 formulations against 36.

So four things differ between the two recipients: anchor-selection rule, number of draws, evaluation size, and campaign sampling policy. Three of the four are analysis choices, not properties of the recipient. The manuscript nonetheless attributes the failure to programme specificity ("physical adjacency can nominate an edge but cannot validate it", §3.5 ¶2).

Note this does **not** invalidate the head-to-head: donor and recipient-only models see the same three anchors, and the donor score is zero-label so anchors affect only the comparator and the evaluation pool. The problem is the inference drawn from it, and the claim of an identical contract.

- *Unsupported inference:* that the two recipients differ in transferability rather than in evaluation design.
- *Missing comparison:* the FINALES contrast under the SolventSeg anchor policy (maximin, multiple draws), as a disclosed sensitivity.
- *Fix level:* **wording** minimum; **reanalysis** with existing code for the strong fix. This is the correct, expanded form of proposed analysis (2).
- *Minimum defensible fix:* state in §2.7 or §3.5 exactly which elements were frozen-identical (donor model, chemistry conversion, transferred object, metrics, thresholds, inference) and which necessarily differed (chronological rather than maximin anchors, one draw rather than 100, 16 rather than 36 candidates), and note that the chronological rule was chosen because it mimics deployment in a temporally ordered campaign.
- *Publishable without the reanalysis?* **Yes**, with the disclosure. But the reanalysis is cheap and materially strengthens the abstention route, which is one third of the paper's contribution.

### R3 — The flagship "unseen salt" may be interpolative in the representation the model actually uses, and no applicability-domain evidence is given
**Severity: major.** LiAsF₆ is a new salt *identity*, but AsF₆⁻ is octahedral, singly charged, weakly coordinating, and closely analogous to PF₆⁻ and BF₄⁻, which the 22-salt source contains in quantity. The manuscript's own ablation shows that excluding the nearest abundant fluorinated lithium salt costs 16.38% [12.66–20.24%] of a 28.64% total gain — i.e. a large share of the gain is carried by a chemically adjacent salt. Solvent families, temperature range, and concentration range are, as far as the manuscript states, shared between source and recipient; only the anion changes.

The manuscript cites Li *et al.* for the point that heuristic OOD splits can remain interpolative, and then defines its own flagship OOD split by a categorical identity rather than by any distance in the mixture representation the Random Forest sees. There is no reported coverage statistic for the recipient — no fraction of recipient rows inside the source descriptor support, no distance quantile, nothing. SI Table S1's eligibility checklist lists "source coverage and candidate-local representation distance" as a recorded dimension; it is not reported for this edge.

- *Unsupported inference:* that a new salt identity constitutes representation-level extrapolation.
- *Missing comparison:* recipient-vs-source position in the component-order-invariant descriptor space.
- *Fix level:* **new computation, but trivial** — the descriptors and both datasets already exist; one distance/coverage statistic and one sentence. Alternatively **wording** alone.
- *Minimum defensible fix:* one clause in §3.2 and Fig 3 caption acknowledging that the recipient anion is chemically analogous to abundant source salts, that the split is by component identity rather than by descriptor distance, and that the ablation quantifies how much of the gain depends on that local analogue. Best fix: add the coverage statistic to SI and cite it in one clause.
- *Publishable without it?* **Yes** — but this is the criticism most likely to come from an electrochemist referee rather than a methods referee, and it costs one sentence to defuse.

### R4 — The paper reports effect sizes but never the two decision quantities its own framing promises: the gate's operating characteristic, and the label budget borrowing replaces
**Severity: major.** The contribution is stated as a routing framework. A routing framework is evaluated by how often it routes correctly. That evaluation exists — SI §S9, leave-one-target-programme CCA gate, 97 edges / 20 tasks / 13 programme clusters — and it is unflattering: the gate admitted 17/20 tasks with 1/17 clearly harmful admissions, but **retained only 4 of the 10 tasks that had a clearly beneficial edge available**, did not beat never-borrowing after Holm correction (+1.58 pp, p=0.1621, Holm 0.2700), and was numerically worse than adjacency-only selection (+1.80%). None of this reaches the main text.

Separately, the screening claim never states the decision-relevant number: **how many recipient measurements would be needed for a recipient-only model to match the borrowed order.** Figure 4c shows the answer is more than ten of thirty-six, which is a strong and quotable result — the manuscript does not quote it.

A referee will notice that the paper is transparent about individual edges and silent about the aggregate behaviour of the thing it is proposing.

- *Unsupported inference:* that a validated evidence-generating protocol is a validated edge-selection rule. These are different objects and the manuscript's own leave-one-programme test separates them.
- *Missing comparison:* false-abstention rate; recipient-only label budget at which the advantage closes.
- *Fix level:* **wording only** — both numbers already exist in the SI and in Figure 4c.
- *Minimum defensible fix:* one short paragraph in §4.2 reporting the gate's operating characteristic and stating plainly that the selection rule is conservative and has not been shown to outperform adjacency-only selection; one clause in §3.4 giving the budget statement.
- *Publishable without it?* **Marginal.** A methods paper whose method's own error rates are only in the SI invites a "the aggregate result is hidden" review. Include it; it converts an ambush into a limitation the authors own.

### R5 — The composition of the designated-edge family makes the 0/40 headline read as broader than it is
**Severity: minor (but free to fix, and the fix strengthens the claim).** Of the eight designated edges in SI Table S10, five pair two properties measured **within the same database** (alloy YS←alloy UTS, catalysis H₂←voltage, polymer tensile←Young's modulus, polymer melting T←crystallization T, ZT←Seebeck). Only three are cross-database (electrolyte←thermoelectric, hydration←solubility, solubility←hydration). The SI already states that "zero of three designated cross-database edges passed the upgrade gate"; the main text and Abstract do not, so "0 of 40 declared OOD edges across eight recipients" invites the response that the falsification is partly directed at within-database property transfer, which is not the paper's subject.

- *Unsupported inference:* none; the numbers are correct. The risk is a reader's misreading, and it is asymmetric — disclosing the composition makes the cross-database statement *sharper*.
- *Fix level:* **wording.**
- *Minimum defensible fix:* one clause in §3.1 and in the Fig 2 caption.
- *Publishable without it?* Yes.

### Explicit decision on the absent positive, outcome-frozen, independent external validation

**Not fatal for the present bounded retrospective claim. It is fatal for three specific sentences the manuscript does not currently write.**

The reasoning, against this manuscript rather than an idealized one:

1. **The claim structure does not require it.** The paper asserts an *existence* result (large OOD gains are attainable under explicit contracts), a *selectivity* result (the same relation routes to predict / rank-only / reject under matched conditions), and a *procedure*. None of the three is a rate, and none requires that an arbitrary nominated edge transfer. §4.3 and the Conclusions are already written at this scope.
2. **The frozen negatives are load-bearing evidence, not absent evidence.** FINALES, Starrydata and TRI are what makes abstention an empirically instantiated route rather than a design aspiration. A framework whose third action had never fired would be *weaker*.
3. **The controlled catalyst series partially substitutes for external replication on the point that matters most.** It is the only experiment in the paper where the assay, grid and endpoint are held fixed and one chemical factor varies, producing predict / rank-only / reject outcomes under matched conditions. That is direct evidence for the routing claim, independent of any single external recipient.
4. **What the absence does forbid,** and what must therefore stay out of the paper: (i) any probability or rate that a nominated neighbouring programme will transfer; (ii) any claim that the *gate* selects useful edges — the only test of that (SI §S9) failed against adjacency-only and never-borrowing; (iii) any prospective, discovery-acceleration or labour-saving language.
5. **The line that must be drawn explicitly:** what is validated here is the *evidence-generating protocol* (declared object, declared endpoint, matched falsifier, grouped inference, retained nulls). What is *not* validated is the *edge-selection rule*. The manuscript currently blurs these in §4.2 ("The practical output is consequently a map with three actions"). R4's fix draws the line.

For *Digital Discovery* — which publishes methods and negative results and does not require prospective laboratory validation — a bounded retrospective methods paper with this leakage architecture clears the bar. It would not clear a Nature-family bar, and the manuscript should not be pushed there.

---

## 4. Novelty verdict and essential literature

### Stress test against each adjacent field

| Field | What already exists | What this paper cannot claim | What survives |
|---|---|---|---|
| Transfer learning in materials | Shotgun TL, computational→experimental deep TL, cross-property TL, solid-electrolyte small-data TL | Novel architecture, first cross-property or cross-domain materials transfer | Nothing architectural |
| Automatic source selection | Mixture-of-experts over pretrained materials models learning source relevance | Novel source-weighting mechanism | Nothing mechanistic |
| Task maps | Taskonomy's directed transfer dependency map | First map of directed task transfer | Nothing structural |
| Transferability estimation | LEEP, optimal-transport dataset distance | A better predictor of which source will transfer | The paper *measures* a realized effect instead of predicting one |
| Multi-fidelity / multi-information-source BO | Fidelity-aware acquisition with source bias and cost models | A fidelity-aware acquisition policy | Explicit refusal to assume calibrated fidelity |
| Rank fusion | Reciprocal rank fusion, Condorcet fusion, Borda | Novelty for equal-weight rank/score averaging — the programme-balanced score is textbook unweighted fusion | Only the *provenance-balanced* weighting rationale (programme, not record count) |
| Applicability domain | Descriptor-space AD definitions in QSAR, four decades old | Novelty for eligibility/coverage gating | Only its use as a *transfer* precondition rather than a per-prediction confidence |
| Learning with a reject option | Chow's error–reject tradeoff, 1970; selective prediction | Novelty for abstention as such | Abstention applied at the level of a *donor–recipient edge* rather than a test instance |
| Negative transfer | A systematic survey of ~50 approaches organized as domain-similarity estimation, safe transfer, and mitigation | Novelty for observing or controlling negative transfer | Retention of harmful edges in the reported denominator |

**Verdict: the novelty is real but narrow, and it is a protocol/benchmark contribution, not a methodological one.** Every component is prior art. Two things are not: (i) the *conjunction* — transferred object and decision endpoint declared jointly before recipient-outcome access, with ranking-only and abstention as admissible outcomes on equal footing with prediction; and (ii) the *denominator discipline* — null, harmful and abstaining edges retained and reported, across heterogeneous experimental programmes with provenance-level leakage units. That is publishable at *Digital Discovery* as a methods/benchmark paper. It is not publishable as a machine-learning advance, and the manuscript wisely does not try.

**Shortest defensible novelty statement (drop into §1 ¶3 or §4.1):**

> We do not introduce a transfer model. The contribution is an endpoint-resolved falsification protocol in which the transferred object, the decision endpoint and the matched falsifier are declared before recipient outcomes are accessed, so that each donor–recipient edge is assigned to numerical prediction, ranking-only use, or abstention — and in which null and harmful edges remain in the reported denominator.

### Essential missing literature (four; DOIs verified this session)

The related-work file currently contains **zero** occurrences of "applicability domain", "conformal", "rank fusion", "Borda", or "reject option", and one passing mention of negative transfer. Each omission is in a field whose referee would recognize the paper's own machinery under a different name.

1. **Chow, C. K.** On optimum recognition error and reject tradeoff. *IEEE Trans. Inf. Theory* **16**, 41–46 (1970). doi:[10.1109/TIT.1970.1054406](https://doi.org/10.1109/TIT.1970.1054406) — the abstention route is a fifty-five-year-old formalism (error–reject tradeoff). Cite it where abstention is introduced (§2.2 or §4.2) and state the difference: abstention here is per-edge and pre-declared, not per-instance and confidence-thresholded.
2. **Sahigara, F. *et al.*** Comparison of different approaches to define the applicability domain of QSAR models. *Molecules* **17**, 4791–4810 (2012). doi:[10.3390/molecules17054791](https://doi.org/10.3390/molecules17054791) — the eligibility and coverage gates are applicability-domain estimation. Cite in §2.2 and use it to frame the R3 coverage statistic.
3. **Zhang, W., Deng, L., Zhang, L. & Wu, D.** A survey on negative transfer. *IEEE/CAA J. Autom. Sinica* **10**, 305–329 (2023). doi:[10.1109/JAS.2022.106004](https://doi.org/10.1109/JAS.2022.106004) — the canonical taxonomy of negative transfer and of "safe transfer" / domain-similarity estimation. The 0/40 result and the specificity gates sit inside this literature; not citing it is the clearest available novelty objection. Cite in §1 ¶2 and §4.1.
4. **Cormack, G. V., Clarke, C. L. A. & Büttcher, S.** Reciprocal rank fusion outperforms Condorcet and individual rank learning methods. *SIGIR '09*, 758–759 (2009). doi:[10.1145/1571941.1572114](https://doi.org/10.1145/1571941.1572114) — the programme-balanced score is unweighted score fusion. Cite in §2.2 item 3, and state that the balancing unit is the experimental programme rather than the record, which is the only defensible novelty in that component.

No other citation is essential. Do not add a conformal-prediction reference unless calibrated uncertainty is added to the paper.

---

## 5. Additional-analysis ranking

Ranked by realistic ability to change acceptance probability. **This ranking differs from the integration record's**, which placed catalyst anchor sensitivity first.

### 1. Anchored-delta / residual transfer on the designated generic OOD edges — **run it; main text**
- *Resolves:* **R1**, the strongest structural criticism. It is the only proposed analysis that converts "generic mechanism fails on set X, declared relation works on set Y" into a within-edge comparison. Whatever the outcome, the paper wins: if the anchored route also fails the complete gate, the falsification extends from donor-feature injection to donor-correction transfer and the 0/40 headline becomes much harder to call a strawman; if it passes anywhere, the map gains its first repaired edge from the benchmark itself.
- *Cannot resolve:* prospective confirmation. It remains post-outcome method development and must be labelled as such, inheriting the frozen splits, draws, controls and Holm family from `multi_target_ood_borrowing_design.json`.
- *Placement:* one added column in Figure 2c or one paragraph in §3.1; full design in SI §S10.
- *Cost:* moderate — eight edges, existing splits, existing gate.

### 2. FINALES precision analysis, expanded to anchor-policy sensitivity — **run the expanded version; SI with one main-text sentence**
- *Resolves:* **R2** and the residual power question. As originally proposed (minimum detectable effect only) it answers "was the null informative?" — useful but narrow. Expanded to recompute the contrast under maximin anchors over multiple outcome-independent draws, it also answers "did the edge fail because of the programme or because of the anchor rule?", which is the question that determines whether the abstention result means what §3.5 says it means.
- *Cannot resolve:* whether the ordinal route would qualify in a third programme; nor can it overturn the frozen decision, which must remain the chronological primary.
- *Placement:* SI, with one sentence in §3.5. The frozen chronological result stays primary and unchanged.
- *Cost:* low — existing verifier machinery already aligns 300 source rows against the anchor table.

### 3. Outcome-independent anchor-selection sensitivity for the catalyst five-anchor results — **defer to SI or future work**
- *Resolves:* a robustness question on a result that is already disclosed as post-primary and is not the flagship. It would preempt "one lucky anchor set", a real but second-order objection.
- *Cannot resolve:* R1–R4. It touches no structural criticism.
- *Placement:* SI if run; otherwise a stated limitation. Do not delay submission for it.

### The direct answer the prompt asks for

**Yes — only a new outcome-frozen recipient can resolve the remaining central limitation.** None of the three analyses, in any combination, can produce a positive independent external validation, because all three re-use outcomes that have already been inspected. What they can do is remove three specific referee objections (dataset-swap confound, anchor-policy confound, anchor-set luck) at low cost. The central limitation — that the framework has never been shown to *win* under a complete pre-outcome freeze — is resolvable only by freezing donor selection, transferred object, anchor budget, falsifiers, endpoint and inference before accessing a recipient nobody has looked at, or by prospective measurement. The manuscript already says this in §4.3 and should not pretend otherwise.

---

## 6. Story and figure logic

### The five-rung sequence

**Retain it unchanged.** It is the clearest available ordering, it survives adversarial reading, and §§3.1–3.5 map onto it one-to-one. Two structural observations, one of which requires action:

- **Rung ordering is right, not merely acceptable.** An alternative would lead with the controlled catalyst series (rung 3) because it is the only controlled experiment and the direct evidence for routing. Reject that: rung 1 must come first because the paper's entire justification for a complicated method is that the simple one fails, and the reader will not accept the complication before seeing the failure. The current order also puts the strongest single number (28.64% / R²=0.629) early, which is correct for a methods paper that must earn attention.
- **The figure mapping does not honour the sequence.** Five rungs are currently carried by four figures, and the compression falls in the wrong place.

### Figure-by-figure verdict

| Figure | Logical job | Verdict |
|---|---|---|
| **1a** | The contract: what may cross, and the three actions | Keep. Does one job. |
| **1b** | The three routes instantiated with committed numbers | Keep. It is the graphical abstract and is cheap. |
| **2a** | Rung 1, part one: a strong in-programme relation fails unchanged transport | Keep. |
| **2b,c** | Rung 1, part two: 0/40 | Keep both — 2b shows the effect distribution, 2c the gate verdict, and 2c carries the claim. Same job, no split needed. |
| **3a,b,c** | Rung 2: a qualified relation crosses an unseen-component boundary | Keep. |
| **3d** | **Rung 3: routing.** | **Move.** This panel is the paper's central claim — the same declared relation producing prediction, ranking-only and rejection under matched conditions — and it is currently a two-panel appendage inside the figure whose job is "prediction works". Figure 3 therefore does two jobs and the routing evidence is visually demoted. Promote it to a standalone **Figure 4**, renumbering the ordinal figure to **Figure 5**. |
| **4a** (current) | Schematic: three sources → programme-balanced score → ORDER/VALUE | **Delete.** It restates Figure 1a's contract with different graphics and adds only three dataset sizes, which belong in the text. Its removal makes room for the promoted routing panel without increasing the figure count beyond one. |
| **4b,c,d** (current) | Rungs 4 and 5: order transfers; the frozen recipient abstains | Keep as the new Figure 5b,c,d (or a,b,c after 4a is deleted). Note that 5c is the panel that answers the label-budget question in R4 — give it a caption clause saying so. |

**Net recommendation:** four data figures become five, or four if the conceptual Figure 1 is merged into a graphical abstract. Either way, the routing experiment gets its own figure and no figure carries two rungs. **Do not add any new case** — the SI contains at least a dozen additional edges and none of them belongs in the main text.

---

## 7. Targeted replacement text

Only necessary replacements, by exact section. Verified values are unaltered throughout. Text not listed here is correct and should be left alone.

### T1 — Abstract, sentences 5–6 (fixes R1)

Replace:
> Generic injection of a donor prediction repaired 0 of 40 declared out-of-distribution (OOD) edges across eight recipients. In contrast, a component-order-invariant electrolyte relation learned from 10,407 measurements across 22 salts predicted…

with:
> Generic injection of a donor prediction repaired 0 of 40 declared out-of-distribution (OOD) edges across eight recipients, including all three declared cross-database edges. On separate recipients, where the transferred object could instead be declared explicitly, a component-order-invariant electrolyte relation learned from 10,407 measurements across 22 salts predicted…

### T2 — §3.1, after "…mean designated-edge far-OOD gain was 0.92% (95% interval −0.35 to 2.92%)." (fixes R5, part of R1)

Insert:
> Five of the eight designated edges paired two properties measured within the same database, and three crossed a database boundary; none of the three cross-database edges passed. Adding a physically adjacent model output was therefore not a reliable way to repair recipient OOD prediction, either within or across programmes.

Then delete the existing sentence "Adding a physically adjacent model output was therefore not a reliable way to repair recipient OOD prediction." (now absorbed above).

### T3 — §3.1, replace the closing bridge paragraph (fixes R1)

Replace:
> These negative controls do more than motivate a different model. They identify the scientific object that the remaining experiments must preserve: the relation that survives the boundary, while discarding the absolute scale or state dependence that does not.

with:
> These negative controls bound the generic mechanism within its tested envelope; they do not show that the edges themselves are unrepairable, because no declared-relation route was applied to them. What they do identify is the scientific object that the remaining experiments must preserve: the relation that survives the boundary, while discarding the absolute scale or state dependence that does not. The experiments that follow therefore test that object on recipients where it can be declared and falsified, not on the benchmark edges themselves.

### T4 — §3.4, first paragraph (removes the 0.918 / 0.910 ambiguity noted in §2)

Replace:
> The data-poor SolventSeg recipient contained 36 formulations. At 25 °C, the unchanged three-programme source score achieved \(\rho=0.918\), high-performance-quartile precision of 1.000, and zero normalized regret. No source record matched a recipient record under the frozen composition, temperature, and outcome fingerprint.

with:
> The data-poor SolventSeg recipient contained 36 formulations, and no source record matched a recipient record under the frozen composition, temperature, and outcome fingerprint. Scoring all 36 formulations at 25 °C, the unchanged three-programme source order achieved \(\rho=0.918\), high-performance-quartile precision of 1.000, and zero normalized regret; the claim below is based instead on the anchor-excluded evaluation, in which the measured formulations are withheld from scoring.

### T5 — §3.4, after the Δρ sentence (fixes R4, budget half)

Insert:
> The advantage did not close within the tested budget: across three, five, and ten measured formulations, no fixed recipient-only configuration reached the zero-label source score, and the source score itself was essentially unchanged by the added labels (Fig. 5c). Ten formulations is more than a quarter of this recipient's entire candidate pool, so the borrowed order was not a substitute for a small number of missing measurements but for a measurement campaign the recipient did not have.

*(Renumber the figure reference if the §6 figure recommendation is not adopted.)*

### T6 — §2.7, after "…No donor, split, metric, or threshold was changed after outcome access." (fixes R2)

Insert:
> The elements frozen identically across the two recipients were the donor models, the chemistry conversion, the transferred object, the metrics, the practical thresholds, and the inferential procedure. Two elements necessarily differed: anchors were the first three chronologically distinct formulations rather than a maximin coverage selection, and the contrast was evaluated on that single chronological anchor set rather than averaged over repeated outcome-independent selections. The chronological rule was chosen before outcome access because it reproduces how the donor would be deployed inside a temporally ordered autonomous campaign.

### T7 — §3.5, replace the final sentence of paragraph 2 (fixes R2)

Replace:
> The contrast between the strong SolventSeg result and the frozen rejection shows why physical adjacency can nominate an edge but cannot validate it.

with:
> The contrast between the strong SolventSeg result and the frozen non-qualification shows why physical adjacency can nominate an edge but cannot validate it. Because the two recipients also differed in anchor policy and in the number of evaluated candidates, the comparison should be read as a failure of the unchanged contract to qualify in the second programme, rather than as an estimate of how much of the SolventSeg advantage is programme-specific.

### T8 — §3.2, after "…Local chemical similarity and broad state coverage were thus complementary rather than interchangeable." (fixes R3)

Insert:
> The split was defined by component identity rather than by distance in the mixture representation. The recipient anion is chemically analogous to abundant fluorinated source salts, and the ablation above quantifies how much of the gain depends on that local analogue: the relation is extrapolative in salt identity and in experimental provenance, but the recipient formulations remain inside the source's solvent, temperature, and concentration support (Supplementary Section S10.3). The result therefore demonstrates portability across a component and a database boundary, not extrapolation beyond the donor's state coverage.

*(If the coverage statistic from §5 analysis is computed, replace "remain inside the source's solvent, temperature, and concentration support" with the quantified statement.)*

### T9 — §4.2, new final paragraph (fixes R4, operating-characteristic half; draws the protocol/selector line)

Append to §4.2:
> Two claims must be separated here. The evidence-generating protocol — declared object, declared endpoint, matched falsifier, grouped inference, retained null and harmful edges — is what the present experiments exercise. The edge-*selection* rule is a different object, and it is weaker. In the leave-one-programme benchmark reported in Supplementary Section S9, an outcome-free gate trained on 97 edges across 13 programme clusters admitted 17 of 20 held-out tasks with only one clearly harmful admission, but retained a clearly beneficial edge in just four of the ten tasks where one existed, and did not outperform never borrowing after multiplicity correction; simple physical adjacency was numerically stronger. The gate is therefore calibrated conservatively — it avoids harm rather than capturing benefit — and no claim is made that it identifies useful edges better than a domain expert would. What the map contributes is a procedure for deciding what an already-tested edge is allowed to support, not a validated predictor of which untested edge will help.

### T10 — §1 ¶2, extend the transfer-learning citation sentence (adds the four essential references)

Replace:
> Yet a related database is not automatically a calibrated fidelity, and a strong in-domain fit is not evidence that its knowledge survives a new experimental programme.

with:
> Yet a related database is not automatically a calibrated fidelity, and a strong in-domain fit is not evidence that its knowledge survives a new experimental programme. That failure mode is itself an established field: negative transfer has a systematic taxonomy of causes and mitigations [@Zhang2023NegativeTransfer], reliable prediction has long been bounded by an explicit applicability domain [@Sahigara2012ApplicabilityDomain], the option to withhold a decision rather than issue an unreliable one dates to the classical error–reject tradeoff [@Chow1970Reject], and combining independent candidate orderings without calibrated scores is standard rank fusion [@Cormack2009RRF]. What is missing is not any one of these components but their conjunction at the level of an experimental donor–recipient edge, where the transferred object and the decision endpoint must be declared together before the recipient outcome is seen.

### T11 — §4.1, insert the novelty statement as the closing sentence of paragraph 1

Append:
> We therefore do not introduce a transfer model. The contribution is an endpoint-resolved falsification protocol in which the transferred object, the decision endpoint, and the matched falsifier are declared before recipient outcomes are accessed, and in which null and harmful edges remain in the reported denominator.

### T12 — Figure captions (if the §6 recommendation is adopted)

**Figure 2, add to panel c:** "…No real edge passes the complete gate; five of the eight designated edges pair two properties measured within one database and three cross a database boundary, and none of the three cross-database edges passes. The seven-programme mean far-OOD gain is 0.92% (95% interval −0.35 to 2.92%)."

**Figure 3, revised title and closing:** "**Figure 3 | A component-order-invariant relation crosses a database and component boundary.** **a–c,** [unchanged text through the bootstrap-interval sentence] This benchmark was designed after the recipient outcomes were public and is retrospective (Methods 2.6); the split is defined by salt identity and experimental provenance rather than by distance in the mixture representation." *(Panel d moves out.)*

**New Figure 4 (promoted from 3d):** "**Figure 4 | The same declared relation routes to prediction, ranking, or rejection.** Five-anchor effects in four controlled catalyst perturbations from the disclosed post-primary composition relation, evaluated on every non-anchor catalyst in each complete held-out derivative system. Left, relative RMSE gain; right, Spearman gain; points are bootstrap means over candidate identities and bars are 95% intervals. Right-hand labels give the route assigned by the frozen endpoint gate. Assay, composition grid, and endpoint are held fixed while one ligand or metal centre changes, so the differing routes are attributable to the perturbation rather than to the experimental setting."

**Figure 5 (former Figure 4, panel a deleted):** "**Figure 5 | Cross-programme knowledge recovers candidate ordering but remains programme-specific.** **a,** The zero-label programme-balanced source ranking compared with 13 recipient-only configurations trained on five measured formulations and with a non-deployable per-draw recipient oracle (15 rows in total). Points are means and bars are 2.5th–97.5th percentiles over 100 outcome-independent anchor selections, conditional on this recipient programme. **b,** Source and fixed recipient-only ordering across three, five, and ten measured formulations; shaded regions are the corresponding percentile intervals, including their negative lower tails. No recipient-only configuration reaches the source score at any tested budget. **c,** Donor advantage with 95% intervals in the primary recipient and under a frozen contract in a second programme, in which anchors were the first three chronologically distinct formulations. The ordinal route is accepted only in the first; in the second it fails to qualify and is withheld."

### T13 — Supplementary Information

1. §S2, one sentence after the resource arithmetic: record the source-coverage statistic for the LiAsF₆ recipient if computed (R3), or state that coverage was audited qualitatively.
2. §S10.3, add the anchor-policy sensitivity subsection when analysis 2 is run, explicitly marked as a disclosed post-outcome sensitivity that does not alter the frozen decision.
3. §S10, add the anchored-delta arm when analysis 1 is run, inheriting the frozen design hash and Holm family.
4. `TERMINOLOGY_LEDGER.md`: add entries for **abstention** ("per-edge, pre-declared withholding of a transferred object; distinct from per-instance reject-option classification") and **programme-balanced fusion** ("equal weight per experimental programme, not per record; distinct from reciprocal-rank fusion, which weights by rank position").

---

## Appendix A — 主要科学决策说明（中文）

**1. 为什么"0/40 失败集"与"成功集"不重叠是本轮最重要的新问题（R1）。**
40 条边覆盖八个接收方（合金屈服强度、催化 H₂ 选择性、电解液电导、水合自由能、聚合物拉伸/熔点、溶解度、热电 ZT），而三个正面结果用的是 BambooMixer→LiAsF₆、三程序→SolventSeg、SpecGen 四个衍生体系——**没有一条正面边属于那 40 条，也没有任何一条失败边被用"合格关系"路线重试过**。因此摘要里的 "In contrast" 在逻辑上把"机制变化"和"数据集变化"混在了一起。审稿人只需要引用这一句就能建议拒稿。最低成本修法是措辞（T1、T2、T3）；根本修法是在那八条指定边上跑锚定残差迁移，这也是我把该分析排到第一位的原因。

**2. 为什么把 FINALES 的"未加改动地冻结迁移"降级为"合同的部分要素相同"（R2）。**
SolventSeg 用 maximin 覆盖选锚、100 次抽样、36 个配方；FINALES 用"时间上最早的三个配方"、**单次抽样**、16 个配方。四个差异中有三个是分析选择而非接收方性质。头对头比较本身是公平的（施主分数零标签，锚点只影响基线和评估池），但由此推断"程序特异性"就超出了证据。时间顺序选锚在自主实验活动里是正确的部署模拟，所以不必改主结果——但必须把"哪些要素完全冻结、哪些必然不同"写清楚（T6、T7），并把 maximin 多抽样版本作为披露的事后敏感性分析（分析 2 的扩展版）。这比原先提议的"最小可检测效应"更有价值。

**3. 为什么质疑旗舰未见盐结果的"OOD 程度"（R3）。**
LiAsF₆ 是新的盐**身份**，但 AsF₆⁻ 与源中大量存在的 PF₆⁻/BF₄⁻ 在几何、电荷与配位能力上高度类似；剔除最近的含氟锂盐邻居只损失 28.64% 中的 16.38%。论文自己引用了"启发式 OOD 划分可能仍是内插"的文献，却用类别身份而非表示空间距离来定义自己的旗舰划分，且全文没有报告任何覆盖度/适用域统计量。一句话承认"按组分身份而非描述符距离划分、溶剂与状态覆盖仍在源支撑内"即可化解（T8），若能补一个覆盖统计量更好。这条同时与缺失的适用域文献互相印证。

**4. 为什么必须把"路由框架的自身错误率"写进正文（R4）。**
论文卖的是路由框架，而框架的评估在补充材料 §S9：门控接纳 17/20，仅 1 例明显有害，但**在 10 个存在明显有益边的任务中只保住了 4 个**，Holm 校正后不优于"从不借用"，且数值上不如"仅按邻接性选择"。把这些藏在补充材料里，等于把最容易被审稿人抓到的东西留给审稿人去抓。同时，筛选主张缺少真正可执行的数字：接收方需要多少标签才能追平借来的排序（图 4c 显示 >10/36）。T5 和 T9 把这两点写进正文，代价是承认门控偏保守，收益是把伏击变成作者自陈的局限。

**5. 关于"缺少正面的、完全结果前冻结的独立外部验证"是否致命——判断为否。**
理由：本文主张的是**存在性 + 路由**，不是**转移率**；冻结阴性（FINALES/Starrydata/TRI）是让"弃权"成为经验实例化路由的必要证据，而不是证据缺口；受控催化剂系列在同一测定、同一网格、同一端点下产生 predict/rank-only/reject 三种结局，直接支持路由主张而不依赖任何单一外部接收方。它禁止的是三类具体表述：任何转移概率或成功率、任何"门控能选出有用边"的主张（唯一的检验已失败）、任何前瞻/加速/省实验的语言。必须明确划线：**被验证的是证据生成协议，未被验证的是边选择规则**（T9）。对 *Digital Discovery* 这一定位而言，这条线以内的稿件是可发表的；对 Nature 系列则不是，不应向那个方向推。

**6. 图件建议为什么要动 3d 和 4a。**
五级叙事由四张图承载，压缩点压错了地方：图 3d 承载的是全文**核心主张（路由）**，却被塞进"预测有效"那张图里当附属面板，导致图 3 同时做两件事；而图 4a 只是用另一套图形复述图 1a 的合同，唯一新增信息是三个数据集规模（应放正文）。删 4a、把 3d 提升为独立图，图数不增而每张图恢复单一职责。不要因为补充材料里还有十几条边就往正文加案例。

**7. 新论性判断与必补文献。**
所有组件都是先例：迁移学习、专家混合源选择、任务图、可迁移性打分、多保真优化、适用域、拒识选项、排序融合、负迁移综述。真正新的只有两点：转移对象与决策端点在接触接收方结果前**联合声明**，且 ranking-only 与 abstention 与 prediction 平级作为可接受结局；以及阴性/有害边保留在报告分母内。这是协议/基准贡献，不是算法贡献——这一点写清楚反而更安全。四篇必补文献（DOI 已本轮核验）分别封堵四个领域审稿人"这不就是我们领域早有的东西"的质疑。

---

## 8. Verdict

**Major revision — presentation and framing, plus two low-cost analyses; not another retrospective experiment cycle.** The first-pass corrections were implemented faithfully and in places improved on what was asked: the frozen-negative statement was correctly narrowed to independent external validations so that the internally frozen positive KIT result is not misrepresented, the zero-label wording is now consistent across manuscript, supplement, package and figure legends, and a terminology ledger locks the canonical forms. The evidence architecture — intact-unit splits, cross-fitting, provenance audits, matched false donors, Holm families, retained null and harmful edges, an independently verified figure pipeline, 118 passing tests — remains unusually strong and is the paper's real asset. What now stands between this manuscript and acceptance is not missing data but four inferential overreaches that are each cheap to fix: a headline contrast drawn between two disjoint edge sets (R1), an "unchanged frozen contract" that differed in anchor policy and resampling (R2), a flagship OOD split defined by chemical identity without any representation-level coverage evidence (R3), and a routing framework whose own operating characteristic is reported only in the supplement, where it is unflattering (R4). The absence of a positive, fully outcome-frozen independent external validation is **not fatal** to the bounded retrospective claim — the claim is existence plus routing, not a transfer rate, and the frozen negatives are what make the abstention route real — but it does forbid any statement that the *gate* selects useful edges, any generalization rate, and any prospective language. Fix the four overreaches in wording, run the anchored-delta arm and the FINALES anchor-policy sensitivity, add the four missing citations, and give the routing experiment its own figure; the paper is then a defensible and genuinely useful *Digital Discovery* methods contribution.

## Three highest-leverage next actions

1. **Apply T1, T2, T3, T9 and T11 today.** They cost an afternoon of editing, they remove the two objections most likely to produce a rejection (disjoint comparison sets; unevaluated routing rule), and T9 converts the supplement's least flattering result into an owned limitation before a referee finds it.
2. **Run the anchored-delta / residual arm on the eight designated edges** under the inherited frozen splits, draws, controls and Holm family. This is the only available analysis that repairs the paper's central logical seam, and both possible outcomes strengthen the manuscript. Run the FINALES maximin anchor sensitivity alongside it — same week, far lower cost — and report it as a disclosed post-outcome sensitivity that leaves the frozen decision untouched.
3. **Close the release package** (persistent DOI, clean-environment reproduction, author metadata and CRediT, ESTM redistribution resolution — SI §S12's four unchecked boxes). These have been open across two review passes and will block acceptance no matter how good the prose becomes.
