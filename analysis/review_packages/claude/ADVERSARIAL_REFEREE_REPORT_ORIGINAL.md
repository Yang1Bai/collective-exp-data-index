# Adversarial referee report — *Digital Discovery*

**Manuscript:** "From pooled regularities to selective priors: artifact-gated knowledge borrowing in experimental materials data"
**Article type:** Full paper (methods-led)
**Reviewer stance:** Hostile, technically precise. Rejection is the default; the evidence must earn a lower bar.
**Review date:** 17 July 2026

---

## 0. What I actually inspected and independently verified

I did not take the self-review at face value. I extracted and re-derived numbers from the compact result files, re-hashed a verification sentinel, re-rendered the figures from both PNG and vector PDF, and cross-summed the data tables. Findings that ground the report:

- **Numbers reproduce.** KIT (`kit_temperature_summary.json`), CALiSol (`calisol_external_summary.json`), ISODB (`isodb_compensation_summary.json`, `isodb_universality_summary.json`), and the OBELiX sequential summary match the manuscript to the reported precision (e.g., KIT 15.02% [8.61,21.10], R² 0.739→0.811, ρ=−1, shuffled −2.96%; CALiSol 1.61% [−2.14,4.21], R² −0.049→−0.014, all rescue gates fail; ISODB pooled R²=0.637, T_iso=513 K, Krug median R²=0.0028, wild-cluster p=0.0002/0.625).
- **Integrity chain is real, not decorative.** The `VERIFIED` sentinel's `summary_sha256` (`3c86d19d…`) matches the actual SHA-256 of `caltech_ionic_external_policy_summary.json`. `manifest.json` confirms 14 datasets, 96,184 measurements, 230 properties, 29,516 entities, 197 hashed artifacts; Table S1 per-source counts sum **exactly** to 96,184.
- **Two findings that the self-review does not surface** (detailed below): a **figure-integrity defect** in Fig. 1b that contradicts the figure's own contract and QA record, and a **source-model-quality confound** in the Caltech benchmark visible in `caltech_ionic_external_policy_source_quality.csv`.

The package is unusually disciplined and honest. That earns it a fair hearing, not a discount on scrutiny. The remainder is adversarial by design.

---

## 1. Headline judgment (full verdict in §12)

**Major revision.** The paper is scientifically defensible **only** as a methods-led falsification/decision-mapping paper, and only if the central noun "map" is demoted to what the evidence supports: a small set of directed edges, exactly one of which is a within-campaign positive. The contribution is real and unusually rigorous, but three things must change before it is publishable: (i) the figure defect and its false QA attestation must be fixed; (ii) the Caltech "credibility ≠ utility" claim must be reconciled with the source-model-weakness confound; and (iii) the self-attested internal "freezing" must be recharacterized honestly and, ideally, externally anchored. No new experiments are strictly required for acceptance of the scoped claims, but the framing must retreat further than the authors have so far conceded.

---

## 2. Issues by severity

Each issue lists: **severity · unsupported inference or failure mode · minimum defensible fix · fix class (new data / compute / reanalysis / reframing) · acceptable without the fix?**

### FATAL

**F1 — There are no fatal issues *at the paper's stated scope*, but exactly one framing that would be fatal if retained.**
If the abstract/title/§3.3/§3.9 continue to present a directed knowledge-borrowing **"map"** or **"cartography"** as an established object, that is fatal, because the empirical content is 42 internal edges with **one** gate-passing positive (Borg UTS→YS, itself internally selected and never externally replicated) plus a **single** independent within-campaign positive (KIT). A "map" implies a populated, navigable structure of transportable relations; the data show an overwhelmingly null/harmful edge set with one bright pixel.
- **Fix:** Reframe from "map/cartography" to "a falsification protocol and a mostly-null audit of candidate edges." Retain the word "map" only as "an audited, mostly-negative edge inventory." (See wording table, §13.)
- **Fix class:** Reframing.
- **Acceptable without fix?** No. This is the single change that separates acceptance from rejection.

### MAJOR

**M1 — Figure 1b omits the two primary markers, contradicting the figure contract and a false statement in the QA record.**
- *Failure mode:* In the delivered `main_knowledge_borrowing.png` **and** the vector `main_knowledge_borrowing.pdf`, the rows "KIT −20 °C (ΔT 10; primary)" and "CALiSol −30 °C (ΔT 10; primary)" contain **only annotation text** — no plotted point, no confidence interval. The single most important positive result in the paper (KIT +15.02% [8.61,21.10]) is not drawn in the forest plot built to display it, and the primary external boundary (CALiSol) is likewise undrawn. Visual prominence instead goes to a **control** (KIT 0 °C, ΔT 30, +5.01%, bright blue) whose CI straddles the 5% gate — a casual reader will misread the control as the result. `FIGURE_CONTRACT.md` (lines 18–22) explicitly requires the KIT primary edge and CALiSol primary "with … intervals"; `FIGURE_QA.md` (lines 34–36) asserts "no clipped … confidence intervals" and that "Panel b's KIT primary interval clears the red 5% gate." Both statements are false against the artifact. This is a QA-process failure, not only a plotting bug.
- *Minimum fix:* Regenerate Fig. 1b so both primary edges are plotted with markers and 95% intervals, visually dominant over controls; correct the QA record; and re-run the "no clipped elements" inspection as an actual check rather than an assertion.
- *Fix class:* Reanalysis/compute (figure regeneration) + reframing (QA text).
- *Acceptable without fix?* No — a figure that hides its headline effect and a QA record that misdescribes it cannot go to production.

**M2 — Figure source data are not in the bundle; figure provenance is internally inconsistent.**
- *Failure mode:* `FIGURE_QA.md` says the panels are sourced from `results/figure_main_panel_a.csv … _d.csv`; `FIGURE_CONTRACT.md` says panel b comes from `kit_temperature_edges.csv`/`calisol_external_edges.csv` and panel c from `kit_temperature_learning_curve.csv`. The `figure_*_panel_*.csv` files and `kit_temperature_learning_curve.csv` are **absent** from `results/`. Two different provenance stories for the same figure, and the nominal source files are missing, means the figures cannot be independently regenerated from the handoff.
- *Minimum fix:* Ship a single, consistent set of figure source CSVs (or point unambiguously to the edge/learning-curve tables), and reconcile QA vs contract provenance language.
- *Fix class:* New data (include the CSVs) + reframing.
- *Acceptable without fix?* No for a reproducibility-forward venue; the editors will ask.

**M3 — Caltech does *not* cleanly separate "source credibility" from "policy utility"; the adaptive null is confounded with weak source models and a weak target backbone.**
- *Failure mode:* `caltech_ionic_external_policy_source_quality.csv` shows the **same-property** OBELiX source model has out-of-fold R²=0.065 (barely above the mean) on its own data, while a designated **wrong-domain** control, OCx catalysis, has the **highest** source skill (R²=0.543, Spearman 0.738). The "gate recognizes real neighbors" ordering (admission 0.355 vs 0.168) is therefore driven by composition-space agreement, **not** by source-model predictive quality — the most skillful source model in the panel is a control. Meanwhile the target backbone is so weak that composition-novelty gets AUC20=0 in the full external pool. So "credibility is necessary but not sufficient" is not established: the adaptive null is equally consistent with "the same-property source model is nearly useless and the target surrogate cannot exploit any residual." The manuscript concedes composition-only representation as a limitation but does not confront that its central Caltech interpretation rests on a source whose own R² is 0.065.
- *Minimum fix:* (a) Report source OOF quality in the main text/Fig. 3 and state plainly that the same-property source model is weak; (b) weaken "credibility is observable but not utility" to "in this benchmark, neither the weak same-property source model nor the residual-injection policy improved acquisition, and admission ordering reflects composition proximity rather than demonstrated source skill"; (c) do **not** attempt to fix this by re-tuning on Caltech outcomes. A genuine test needs a stronger source/target model **frozen on a new outcome-unseen target**.
- *Fix class:* Reanalysis (surface existing numbers) + reframing; a *stronger* claim would need new compute on a new target.
- *Acceptable without fix?* Conditionally — acceptable only if the interpretive claim is weakened as above; not acceptable if "credibility ≠ utility" is presented as a demonstrated principle.

**M4 — "Frozen" is entirely self-attested and time-clustered; it is not preregistration and should not be allowed to carry preregistration's epistemic weight.**
- *Failure mode:* Every freeze claim is a field the authors wrote in files they control (`analysis_status`, `frozen_utc`), and the timestamps cluster on 14 July 2026 (`ood_decision_borrowing_design.json` 18:11:15Z; `obelix_ood_discovery_design.json` 18:20:56Z; KIT/CALiSol "designated-before-first-outcome"), with the Caltech design at 16 July. There is no external, tamper-evident anchor (OSF/AsPredicted registration, signed public git history, timestamping authority). The OBELiX **sequential** design is candidly labeled `frozen-post-existing-results`, i.e., frozen after the fixed-ranking direction was known — good honesty, but it means the sequential "confirmation" is conditioned on prior inspection of the same data family. The circularity guard the paper leans on (frozen designs) reduces to "trust our timestamps."
- *Minimum fix:* (a) State explicitly that all freezes are internal and self-attested, not preregistered; (b) for the release, publish the design JSONs in a public repository with immutable commit history **before** the archival DOI, and cite the commit hashes/dates; ideally deposit the outcome-unseen designs to a registration service; (c) stop using "confirmatory" for anything frozen after related-endpoint inspection (e.g., OBELiX sequential) — call it "prespecified given prior screening."
- *Fix class:* Reframing (now) + process (public timestamping before submission); no new science.
- *Acceptable without fix?* Acceptable only with the honesty fix; the word "confirmatory" for post-inspection freezes should be removed regardless.

**M5 — The entire positive case rests on one within-campaign edge with an already-usable baseline; "rescue" and "data-poor" oversell it.**
- *Failure mode:* The only positive that survives every gate is KIT −20→−30 °C, a **same-property, same-campaign, adjacent-temperature** edge where the n=30 target-only model already has R²=0.739. Fold effects range 2.13%–25.75% across five folds of ~21 formulations each — a large spread on small folds. The label-saving point estimate (37.35%) has a post-outcome interval (21.84–49.91%) straddling the 30% gate, and only 80.5% of replicates clear it. Calling this "local task rescue" of a "data-poor task" imports connotations (a broken task made viable) that the R²=0.739 baseline contradicts. The BIRDSHOT "directional replication" has **negative absolute R²**; Matbench is null; CALiSol is null. So there is **zero** independently replicated positive source-to-policy edge in the paper.
- *Minimum fix:* Replace "rescue"/"data-poor rescue" in headings and abstract with "materially improves few-shot error and sample efficiency in a simulated label-poor slice of one campaign." Retain "local task rescue" only as an explicitly defined operational status tied to Table S2, and say once, prominently, that no independently replicated positive edge exists.
- *Fix class:* Reframing (no new data required for the scoped claim). A genuinely stronger paper needs a second, independent positive edge — new data/compute.
- *Acceptable without fix?* Acceptable for the scoped methods claim only with the wording retreat; not acceptable if "rescue"/"data-poor field" language remains in title/abstract.

**M6 — Data/code availability and licensing are not yet at *Digital Discovery* bar; several are hard blockers.**
- *Failure mode:* No persistent release DOI; 21 catalog licenses "Unknown"; ESTM redistribution "unresolved" and one source non-commercial, so the generated SQLite cannot be shipped; live-URL revalidation incomplete; no clean-environment CI record on the final commit; figure source CSVs missing (M2). RSC requires persistent, reviewer-accessible data/code deposition and a specific Data Availability statement.
- *Minimum fix:* Archive the exact release (Zenodo/figshare) with a DOI; resolve or explicitly exclude ESTM/NC sources; complete a clean-Linux reproduction and cite the CI record; supply the RSC-formatted Data/Code Availability statements naming version + DOI.
- *Fix class:* Process/new data (deposition), no new science.
- *Acceptable without fix?* No — these are standard submission blockers for the venue.

### MINOR

**m1 — Multiple-comparisons discipline is good but under-described for the *whole* study.** Holm is applied *within* families (five internal candidates; three named OOD edges; eight Caltech contrasts per scope) but there is no accounting for the number of families/endpoints explored across the paper. *Fix:* add a short "family-wise scope" paragraph enumerating every frozen family and stating that no cross-family correction is claimed. *Class:* reframing. *Acceptable without:* yes. (Reassuringly, the Caltech source-increment nulls are null even at raw signflip p — 0.084/0.556/0.110 hard-OOD — so the null is not a multiplicity artifact; say so.)

**m2 — Bootstrap/uncertainty units are heterogeneous and the reader must work to see it.** KIT uses formulation-hierarchical bootstrap (108 units), CALiSol article-hierarchical (15 articles), Borg composition-cluster (208), ISODB DOI-cluster (512) + wild-cluster. The KIT interval is *within one campaign*, so it is seed/formulation uncertainty, **not** dataset-level uncertainty — a point the paper makes but should make once, crisply, next to the headline number. The Caltech static rankings have **zero dataset-level uncertainty** (deterministic ranking; "100 seeds" is not 100 datasets); the manuscript says this but the AUC20 "33/45 vs 11.25" contrast still reads as if it had inferential weight. *Fix:* one uncertainty-taxonomy sentence per result; drop implied inference from zero-width static intervals. *Class:* reframing. *Acceptable without:* yes.

**m3 — Small-n claims.** KIT n=30 with five folds; BIRDSHOT 171 rows/151 comps; Matbench 312 (927 measurements); thermoelectric Meyer–Neldel n=112 series (pooled R²=0.107); OBELiX 500 comps, sequential 100 seeds; Caltech 144 external / 58 hard-OOD candidates with 8 true top-5% external entities. The hard-OOD "recall20=1.000" rests on **3** true entities in 58 candidates — near-anecdotal. *Fix:* report absolute counts beside every recall/AUC figure (e.g., "recall20=1.000 = 3/3"), and label hard-OOD conclusions as n-limited. *Class:* reframing. *Acceptable without:* yes but strongly advised.

**m4 — Krug null tests one artifact, not the space of artifacts.** The ISODB conclusion (survives Krug) is correctly hedged, but the independent-parameter Krug permutation is the *simplest* coupling null; it does not address correlated measurement error, limited-temperature-range coupling within DOI, or selection by fit quality. T_iso=513 K sits far above the harmonic median (301 K), which is the real strength of the argument — lead with that geometric fact rather than the permutation p. *Fix:* state which artifacts Krug does and does not exclude; foreground T_iso vs temperature range. *Class:* reframing. *Acceptable without:* yes.

**m5 — Model/representation family is narrow, and this bounds every conclusion.** All learners are tree ensembles (RF/ExtraTrees) + degree-2 Ridge; all features are composition fractions/one-hots (+8 descriptors for OBELiX). No chemistry-aware representation (graph, SOAP/MBTR, learned embeddings), no GP/BO-native acquisition despite active-learning claims. The sequential "random beats UCB" result is specifically a mean+1·SD ExtraTrees UCB failure, which may reflect uncalibrated ensemble spread rather than a general prior-utility result. *Fix:* state the representation/learner envelope as a first-class limitation on generality and soften "endpoints are distinct" to "distinct **for these learners/representations**." *Class:* reframing (a broader claim needs new compute). *Acceptable without:* yes.

**m6 — Novelty is well-defended; residual risk is priority drift, not missing prior art.** `RELATED_WORK.md`/`CITATION_VERIFICATION.md` are exemplary and pre-empt the obvious challenges (Yamada, Jha±correction, Gupta, Kong, Cubuk, Taskonomy, Ottomano, OBELiX, Attari, Matbench±correction, Krug/Cornish-Bowden/Bond/Mianowski, MDF/OPTIMADE). One gap for an RSC audience: **multi-fidelity / cost-aware BO** and **task-similarity/meta-learning transferability metrics** (e.g., LEEP/OTDD-style task distances, fidelity-aware GP-BO) are adjacent framings that a referee will raise; the paper's "endpoint separation" overlaps conceptually with multi-fidelity's "cheap signal ≠ expensive optimum." *Fix:* add one paragraph distinguishing the borrowing endpoints from multi-fidelity acquisition and from learned task-distance metrics. *Class:* reframing/light literature. *Acceptable without:* yes.

**m7 — Terminology load.** The gate vocabulary (directional / descriptive / rescue / unresolved / practically equivalent) is precise but heavy; a nonspecialist can mistake "local task rescue" for a breakthrough. *Fix:* one glossary box or tight Table 1 ↔ Table S3 alignment; use "materially improves" in prose and reserve defined terms for the tables. *Class:* reframing. *Acceptable without:* yes.

---

## 3. Leakage, provenance, circularity, outcome-selected methods, preregistration (prompt topic 1)

Leakage controls are genuinely strong and I could not find a hole: exact canonical-composition exclusions, provenance/DOI/article-disjoint splits, cross-fitted target-training source features, forbidden same-series quantities (Arrhenius/EIS/VTF), audited zero source–target overlap, and two OBELiX train/test duplicates caught and removed by canonicalization. The Caltech design excludes exact formulas and target DOIs and was frozen before target download. **The residual risks are circular-analysis and outcome-selection, not row leakage:** (a) the internal Borg UTS→YS "internally confirmed" edge is discovery-selected from 42 edges and never externally replicated (BIRDSHOT lacks absolute utility, Matbench null) — it should be labeled candidate-only, not "confirmed"; (b) the hard-OOD 40% subset and the OBELiX sequential design were specified after the whole-pool direction was known (the paper says so, but "confirmatory" should be dropped for the sequential campaign — M4); (c) the Caltech portfolio (recall20 0.625/1.000) is explicitly outcome-selected and correctly quarantined — **do not** let it drift into the results narrative, and per your instruction I do **not** recommend any additional tuning on observed Caltech outcomes; any portfolio claim must be frozen on a new outcome-unseen target. **Frozen ≠ preregistered** (M4): the credibility of every "frozen before outcome" statement rests on self-generated timestamps and must be described as such.

## 4. Statistics: bootstrap units, small-n, multiplicity, dataset- vs seed-level uncertainty, Krug (prompt topic 2)

Covered in M5, m1–m4. Net: the inferential machinery is careful and, where I checked, correctly implemented (Holm within families; hierarchical/cluster bootstraps matched to the grouping; wild-cluster for ISODB families). The two things an adversary presses: (1) **the KIT interval is within-campaign seed/formulation uncertainty, not dataset-level** — it cannot support any cross-dataset generalization, and the 30% saving gate is not robust (interval 21.84–49.91%); (2) **static-ranking "signal" has zero dataset-level uncertainty** and its impressive AUC20 numbers should not be read inferentially; the honest external-pool statistic is recall20 = 0.25 (OBELiX) / 0.375 (ESTM), below the 0.50 gate. The Krug test is a single-artifact null; the geometric T_iso argument is the stronger evidence.

## 5. Is the model/representation family too narrow? (prompt topic 3)

Yes, and it bounds the headline conclusions (m5). "Average prediction, OOD screening, and sequential discovery are distinct endpoints" is well supported **for tree-ensemble learners on composition features with a mean+SD UCB**. It is not established that the *endpoints* are distinct in general versus that *this acquisition function/representation* is weak — indeed uniform random beating UCB (official median 13 vs 28 acquisitions) is more naturally read as "this UCB is miscalibrated on this pool" than as a deep statement about endpoints. The paper should make the learner/representation envelope a first-class caveat and soften the endpoint-separation claim accordingly.

## 6. Does one KIT positive + external nulls support the proposed map? (prompt topic 4)

No — this is F1/M5. One within-campaign positive, one internally selected internal positive, and otherwise null/harmful edges do not constitute a "map." They constitute a **falsification protocol with a mostly-negative worked example set**. That is still a legitimate and useful contribution for *Digital Discovery*, but only if named accurately.

## 7. Does Caltech separate source credibility from policy utility, or reflect a weak backbone? (prompt topic 5)

Largely the latter (M3). The verified null is real and valuable as a negative result, and the wrong-source safety guards passing is a genuine, useful safety property. But the "credibility observable, utility absent" reading is confounded: the same-property source model is near-useless on its own data (R²=0.065) while a wrong-domain control is the most skillful source (OCx R²=0.543), and the target surrogate is weak enough that even composition-novelty gets AUC20=0 externally. The defensible claim is narrow: *on this target, with these weak source/target models, residual-injection and target-mean steering did not convert admission-ordering into acquisition gains.* Not: *credibility is necessary but not sufficient* as a principle.

## 8. Do the three figures visually and statistically support the hierarchy? (prompt topic 6)

- **Fig. 1 (main):** panels a, c, d are strong and honest (a: transport failure with R²=−3.01 shown; c: sample-efficiency with the 22–50% diagnostic drawn; d: compensation with Krug median and family p on-plot). **Panel b fails (M1):** it does not plot its two primary edges. As delivered, Fig. 1 does not visually support the headline KIT positive — the reader must trust text.
- **Fig. 2 (OOD):** excellent and adversarially honest — panel c literally shows random (median 13) beating both UCB policies (28/26) and states censoring; panels a/b separate fixed screening from sequential nulls. Supports its claim.
- **Fig. 3 (Caltech):** clean and correctly labels the static panel "descriptive only" and excludes the portfolio. But it should add source-model OOF quality (M3) so panel a's "gate recognizes real neighbors" is not misread as "real neighbors are the skillful sources," and panel c should annotate absolute recall (0.25/0.375 external) beside AUC20 to avoid overselling.

## 9. Novelty vs transfer learning, task-similarity/meta-learning, multi-fidelity, compensation critiques, DB integration (prompt topic 7)

Adequately to well handled (m6). The composition — a provenance-aware, artifact-gated, falsification-first borrowing audit — is defensible novelty; none of the components is new and the manuscript says so. Add one paragraph on multi-fidelity/cost-aware BO and learned task-distance metrics, which an RSC reviewer will treat as the nearest neighbors to "endpoint separation."

## 10. Data/code availability, licensing, reproducibility, editor expectations (prompt topic 8)

Covered in M2/M6. Editors will require: persistent DOI for the exact release; a Data Availability statement that resolves the ESTM/NC redistribution question (rebuild-from-lock is acceptable if stated); figure source data included and consistent; a clean-environment reproduction record; author list/affiliations/CRediT/conflicts/funding; RSC formatting + graphical abstract; and a final numeric/terminology consistency pass across abstract, text, SI, figures, README. None of these is scientific, but several are hard blockers.

---

## 11. What does *not* need fixing (credit where due)

The leakage discipline, retention of null/harmful edges, refusal to promote an alternative CALiSol temperature after the 0 °C control looked better, refusal to let the CALiSol mapping p=0.004 override failed practical gates, the prespecified random-acquisition control that embarrasses the authors' own UCB and is kept anyway, the honest quarantine of the Caltech portfolio, and the citation/novelty audit are all model behavior. The verification chain (matching sentinel hashes, exact data-count reconciliation) is better than most published materials-ML work. These should be preserved verbatim through revision.

---

## 12. Verdict (one paragraph)

**Major revision — potentially acceptable at *Digital Discovery* as a methods-led falsification and decision-mapping paper, not as a "knowledge-borrowing map."** The technical execution is unusually rigorous and honest, the leakage/artifact/multiplicity controls are strong, and the numbers I checked reproduce exactly against the compact results and verification sentinels. But the positive case is a single within-campaign, same-property, adjacent-temperature edge over an already-usable baseline, with no independently replicated positive source-to-policy edge anywhere in the paper; the central Caltech "credibility ≠ utility" interpretation is confounded with a near-useless same-property source model and a weak target backbone; the headline figure omits its own primary markers and its QA record falsely certifies them; and every "frozen before outcome" guarantee is self-attested on same-day timestamps rather than preregistered. None of this is fabrication or leakage — it is over-claiming relative to genuinely careful evidence. Fix the figure and its QA, surface and re-interpret the Caltech source-quality confound, recharacterize "frozen" and "rescue," and close the deposition/licensing/reproduction gaps, and the scoped claims are publishable. Retain the current field-rescue or "map" framing, or present the outcome-selected portfolio as an edge, and it should be rejected.

## 13. Three highest-leverage actions before (re)submission

1. **Rebuild Fig. 1b to plot both primary edges with intervals, and correct the false QA attestation** (M1) — the paper currently cannot show its own headline result, and a QA record that certifies a missing interval is a credibility landmine an editor will not forgive.
2. **Resolve the Caltech interpretation against `source_quality.csv`** (M3): report source OOF R² on-figure, weaken "credibility is necessary but not sufficient" to the benchmark-scoped statement, and explicitly note that the most skillful source model in the panel is a wrong-domain control — do not re-tune on Caltech; any stronger claim must be frozen on a new outcome-unseen target.
3. **Retreat the framing globally** (F1/M5/M4): title/abstract/section headings drop "map/cartography," "rescue," "data-poor field," and "confirmatory" (for post-inspection freezes); state once, prominently, that no independently replicated positive edge exists and that all freezes are internal/self-attested; then complete the DOI/licensing/CI deposition (M6).

## 14. Claim-by-claim wording actions

| # | Current wording / claim | Action | Why |
|---|---|---|---|
| 1 | Title: "artifact-gated knowledge borrowing … in experimental materials data" | **Weaken/replace** — remove implied populated map; see §15 | One positive edge ≠ a borrowing map |
| 2 | Abstract & §3: directed knowledge-borrowing **"map" / "cartography"** | **Weaken** to "audited, mostly-null inventory of candidate edges / falsification protocol" | F1 |
| 3 | "local task **rescue**" of a "**data-poor**" task (abstract, §3.4, §5) | **Weaken** in prose to "materially improves few-shot error and sample efficiency"; **retain** "local task rescue" only as a defined operational status tied to Table S2 | M5; baseline R²=0.739 |
| 4 | KIT "37.35% of target labels saved" | **Retain the point estimate but never as a ≥30% lower bound**; always print the [21.84,49.91]% diagnostic beside it | M5; gate not robust |
| 5 | Borg UTS→YS "internally **confirmed**, awaiting external replication" | **Weaken** to "internally selected candidate; not externally replicated" | Discovery-selected; BIRDSHOT/Matbench do not confirm |
| 6 | BIRDSHOT "directional replication" | **Retain** but always adjacent to "negative absolute R²; below practical gate" | Avoids implying a positive edge |
| 7 | OBELiX sequential campaign "**confirmatory** under its frozen definition" | **Weaken** to "prespecified given prior fixed-ranking inspection" | Frozen after related-endpoint direction known (M4) |
| 8 | "uniform random acquisition outperformed both UCB policies" | **Retain** (strength); add "consistent with an uncalibrated UCB rather than a general prior-utility result" | m5; honest and disarms over-reading |
| 9 | Caltech "a physically ordered credibility score is observable, but credibility is not utility" | **Weaken** to benchmark-scoped statement; add source OOF R² caveat | M3 |
| 10 | Caltech static "real neighbors far stronger than random" (AUC20 33/45 vs 11.25) | **Retain but recontextualize** with recall20 = 0.25/0.375 (external) and "descriptive, zero dataset-level uncertainty" | m2/m3; avoids inferential over-read |
| 11 | Post-result OBELiX/ESTM portfolio (recall20 0.625/1.000) | **Retain in SI as method-selection only**; must be frozen on a new target before any edge claim; keep out of Results/abstract/figures | Per prompt; outcome-selected |
| 12 | ISODB "survives the Krug null" | **Retain**; add which artifacts Krug does/doesn't exclude; foreground T_iso=513 K vs 301 K | m4 |
| 13 | "aggregation does not automatically reveal a universal law" | **Retain** — core, well-supported | — |
| 14 | Any implication of prospective/lab acceleration or new science | **Delete/keep deleted** — none tested | Consistent with limitations |
| 15 | Data Availability "available in the public repository … [DOI]" | **Retain but complete** with archived DOI + license resolution + figure CSVs | M2/M6 |

## 15. Strongest alternative title and abstract framing

**Recommended title:**
*"When does one dataset help another? A falsification protocol for knowledge borrowing in heterogeneous experimental materials data."*
(Alternatives: *"Aggregation is not transport: gated tests that mostly reject borrowed priors in experimental materials data"*; *"A falsification-first audit of knowledge borrowing across experimental materials datasets."*)

**Recommended abstract framing (structure, ~200 words):**
Lead with the negative, methods-first thesis; make the single positive a bounded example, not the headline; foreground endpoint separation and the mostly-null result. For example: *"Combining experimental materials datasets can expose strong correlations without establishing that knowledge transports. We present a falsification protocol that forces a candidate source→target 'borrowing' edge through leakage, absolute-utility, practical-effect, multiplicity, distance, and placebo gates, and that keeps null and harmful edges as first-class results. Applied across alloy strength, electrolyte conductivity, adsorption compensation, and solid-electrolyte screening, the protocol rejects most edges: a strong in-domain UTS–YS calibration fails unchanged out of domain (R²=−3.0); an internally selected alloy edge does not replicate with positive absolute utility; and a mechanically adjacent target is null. Exactly one edge — an adjacent-temperature prior within a single electrolyte campaign — materially reduces few-shot error (15.0% [8.6,21.1]; R² 0.739→0.811) and improves sample efficiency, but does not transport to a paper-disjoint test. A directional out-of-distribution ranking signal does not survive sequential acquisition, where uniform random search outperforms the tested policy; and on an independent, verified ionic-conductor benchmark no adaptive source-aware policy improves acquisition. Useful borrowing is sparse, endpoint-specific, and provenance-dependent; the contribution is a reproducible procedure for deciding which neighboring measurements to trust — and for rejecting the rest."*

---

*Prepared as an adversarial referee assessment. All quantitative claims above were checked against the compact result files, verification sentinels, and re-rendered figures in the review bundle; the outcome-selected Caltech portfolio was treated as non-confirmatory and no re-tuning on observed Caltech outcomes was proposed.*

