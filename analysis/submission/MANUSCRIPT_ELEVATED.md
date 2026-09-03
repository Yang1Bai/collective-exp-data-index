# The Transferable Unit in Experimental Science Is a Falsified Relation, Not a Database

**Working title (elevated framing for Digital Discovery)**

A methods paper on *when* experimental knowledge may be borrowed across laboratories, and *what object* is safe to borrow. All numbers below are reproduced from the frozen verification records listed in each section. Retrospective, post-outcome evidence; no universal transfer, no prospective acceleration claim.

---

## Abstract (elevated)

The promise of machine learning in experimental science is that one laboratory's measurements can shorten another's search. We tested that promise as a falsifiable hypothesis across eight experimental programmes, forty declared transfer edges, and four independent databases, and found the popular target to be the wrong one: **generality does not transfer — relations do.** A strong within-programme alloy relation with log–log R² = 0.790 was destroyed by a change in experimental provenance (unchanged coefficient R² = −3.006); none of forty generic donor-feature edges repaired recipient out-of-distribution error under a complete gate; a pretrained molecular encoder made a scaffold-out-of-distribution photocatalysis recipient **28.1% worse**. What survived every boundary was not a database, not a model, and not a feature — it was a *falsified relation with its provenance preserved*: a LiAsF₆ cross-salt relation reduced unseen-formulation log-RMSE by **27.41%** (95% CI 21.79–32.92) under a temperature- and chemistry-scrambled falsifier, and a zero-label ordinal score ordered unmeasured SolventSeg formulations at **ρ = 0.910** where the strongest five-label recipient-only model reached 0.537 (Δρ = 0.374, 95% CI 0.213–0.562; Holm p = 0.00070). The same contract that produced these gains also produced its own negative cases: a frozen second-recipient test did not qualify (Δ = −0.089, 95% CI −0.293 to 0.096; p = 0.131), and two outcome-unseen recipients produced all-null transfers. We conclude that the transferable unit in experimental science is a falsified relation with its boundary conditions attached, not a database or a model. We specify a pre-registration protocol that freezes donor selection, transferred object, anchor budget, falsifiers, and decision endpoint before recipient outcomes are accessed, and we archive a machine-readable borrowing map so that every claim can be audited.

---

## 1. Introduction — why generality is the wrong target

**The puzzle.** Experimental data are the most expensive data in science, and the most siloed. The natural aspiration is that a model trained on one laboratory's electrolyte, alloy, or photocatalyst measurements should accelerate another laboratory's search. This aspiration underlies the modern "database economy" of experimental science: bigger and better-curated data are assumed to be intrinsically more reusable.

**The failure pattern we document.** We assembled 16 normalized donor datasets, 17 recipient datasets, and a benchmark of 40 declared transfer edges across eight targets. Under a complete, pre-registered OOD-repair gate — falsifiers, shuffled controls, and grouped error intervals — **0 of 40 edges qualified**. The largest apparent edge was a directional artefact of near-region error; three cross-database edges all failed; the mean programme-level gain was 0.92% (95% CI −0.35 to 2.92%). A separate model-capacity test showed that a strong pretrained molecular encoder, after passing every source-skill gate, made a scaffold-OOD photocatalysis recipient **28.1% worse** and failed against its own shuffled control.

**The interpretation error.** These are not merely null results. They identify a category mistake: the scientific object being transferred in most attempts is the wrong object. What is usually shared is (i) a database (rows), (ii) a model (parameters), or (iii) a feature representation (latent variables). None of these is a *relation* — a falsified statement of the form "under provenance P, outcome Y varies with mechanism X as f". A database contains rows, not truths; a model contains fitted parameters, not laws; a feature representation contains numbers, not mechanisms. When provenance changes, rows, parameters, and features all silently change meaning.

**Our thesis.** The transferable unit in experimental science is a falsified relation with its provenance attached. We demonstrate this by showing (i) that generic objects fail systematically, (ii) that relation-sized objects with explicit provenance survive across database boundaries, (iii) that the same contract abstains correctly at its boundary, and (iv) that the resulting evidence can be archived as an auditable borrowing map with a pre-registration protocol for prospective use.

**What this paper is not.** We do not claim universal transfer, a new electrolyte formulation, improved absolute conductivity prediction, or prospective acceleration. We report retrospective, post-outcome evidence, with all null and harmful edges retained in the record.

---

## 2. Materials and evidence architecture

**Data.** 16 donor and 17 recipient experimental datasets spanning alloys (Borg, BIRDSHOT), electrolytes (BambooMixer, SolventSeg, FINALES, KIT, CALiSol), catalysis (SpecGen, OCx, iron-substitution), and photocatalysis (Starrydata, TRI), normalized to a shared schema with per-row provenance (source DOI or archive identifier where available; BambooMixer lacks row-level DOI provenance, declared explicitly).

**Evidence registry.** Every experiment is registered in `analysis/core_story_experiment_registry.json` with a pre-declared claim, gate, and classification (`complete`, `complete-boundary`, or `method-development-complete`). Fifteen experiments require the paper-submission gate; CS01–02 are complete, CS03–13 and CS15 are complete-boundary, CS14 is method-development-complete. Attempts, including null and harmful ones, are logged in `research/evidence/ATTEMPT_LEDGER.csv` (27 attempts).

**Statistical contract.** All transfer claims are evaluated with (i) a recipient-only baseline, (ii) a matched false-donor control (chemistry-permuted or wrong-salt), (iii) grouped bootstrap 95% intervals over the clustering unit (article, programme, or composition cluster), and (iv) a pre-declared admission gate. We report both gains and abstentions.

---

## 3. Results

### 3.1 Generality fails — 0/40 edges, negative transfer, and a destroyed relation

**A strong relation is destroyed by provenance change.** The Borg alloy programme contains 495 paired ultimate- and yield-strength records with log–log R² = 0.790 in-domain. The independent BIRDSHOT campaign shares no exact composition and has in-domain R² = 0.067. Applying the Borg coefficient unchanged to BIRDSHOT gives **R² = −3.006** (95% composition-cluster interval −4.154 to −2.185); the median strength ratio changes from 1.36 to 2.72. The source relation was real but not portable as an unchanged coefficient.

**Generic feature injection fails at portfolio scale.** 0 of 40 declared edges passed the complete OOD-repair gate (Fig. 2b,c of the parent manuscript). Five of the eight designated edges paired two properties within the same database; three crossed a database boundary; none of the three cross-database edges passed. Mean designated-edge far-OOD gain across the seven programmes: **0.92%** (95% CI −0.35 to 2.92%).

**Model capacity does not rescue generality.** A pretrained molecular encoder that passed every source-skill gate made a scaffold-OOD photocatalysis recipient **28.1% worse** on average and failed against its own shuffled controls.

**Lesson.** These negatives bound the generic mechanism. They do not show that the edges are unrepairable — they show that the object being transferred was the wrong size. The remaining experiments therefore transfer a *declared relation*, not a model or a database.

### 3.2 A relation with provenance survives: LiAsF₆ cross-salt transfer

**Design.** From the BambooMixer extension archive (which contains LiAsF₆ and four reference salts), we restricted the analysis to the declared LiAsF₆ target: 1,660 rows / 156 unseen formulations, donor is a within-archive cross-salt relation. Controls: recipient-only (temperature+concentration), chemistry-permuted donor, wrong-salt (LiBOB), fluorine-control (LiBF₄), and drop-LiPF₆ sensitivity.

**Result.** External raw R² = 0.607, log R² = 0.718, Spearman ρ = 0.864, log-RMSE 0.342. Versus the temperature-and-concentration-only baseline: **relative log-RMSE gain −27.41%** (95% CI 21.79–32.92; Δρ +0.158). Versus the chemistry-permuted falsifier: **−25.88%** (95% CI 20.73–31.09; Δρ +0.129). Removing LiPF₆ from the donor degrades the gain to 16.08% (95% CI 12.10–19.80); a LiPF₆-only donor cannot reproduce the full-source gain (−28.50% is only attainable with the complete source). The wrong-salt control (LiBOB) and the fluorinated control (LiBF₄) are suppressed, showing the effect is salt-specific, not generic-fluorine.

**Interpretation.** What crossed the boundary was not "BambooMixer data" or "the BambooMixer model" — it was the relation *"under this provenance, log-conductivity varies with this component-order-invariant mixture descriptor"*, with the absolute scale and state dependence discarded. The falsifier tests show the relation is not an artefact of temperature, concentration, or arbitrary chemistry.

### 3.3 Zero-label ordinal transfer: ρ = 0.910 vs 0.537

**Design.** SolventSeg recipient (36 formulations, zero recipient labels used at decision time). Donors: BambooMixer (all rows), target-family-only, without-target-family, CALiSol, KIT, and a programme-balanced portfolio/rank-consensus. Decision endpoint: ordinal ranking of unmeasured formulations for experimental prioritization.

**Result.** With five anchors excluded, the programme-balanced frozen portfolio ranks unmeasured SolventSeg formulations at **ρ = 0.910** (top-quartile precision 0.933, normalized regret 0.00047). The strongest recipient-only model (RBF kernel ridge, five labels) reaches **ρ = 0.537**. Δρ = 0.374 (95% CI 0.213–0.562), Holm-corrected p = 0.00070 across the six donor variants. Even against a per-draw oracle that uses the five labels optimally, the programme-balanced portfolio retains Δρ = 0.300 (95% CI 0.183–0.540).

**Ablations.** The programme-balanced portfolio improves on the best single donor by Δρ = +0.0236 (95% CI 0.0069–0.0397) and raises top-quartile precision from 0.826 to 0.933. Absolute prediction still fails (programme-balanced portfolio vs state-only: −18.0% on relative log-RMSE), which is why the admitted decision is *ranking*, not absolute prediction.

**Interpretation.** Ordinal, decision-level reuse — "which unmeasured formulation should we try first" — is where cross-programme knowledge survives. The relation transferred is the *ordering*, not the absolute value. This is a distinct scientific object from a predictive model, and it is the object that our routing gate admits.

### 3.4 The contract abstains: frozen FINALES second recipient and outcome-unseen nulls

**Frozen second-recipient non-qualification.** Under the unchanged donor ranking and the pre-registered contract (3 anchors, ≥50 temperature-matched pairs, concordance advantage ≥ 0.10, permutation p ≤ 0.05), the FINALES second recipient (16 evaluation formulations, 98 eligible pairs) did **not** qualify: donor concordance 0.694 vs strongest recipient-only baseline 0.783, Δ = −0.089 (95% CI −0.293 to 0.096), permutation p = 0.131, normalized regret 0.563 vs 0.180. This is a deliberately *frozen* negative: the donor was not refit, thresholds were not tuned after outcome access. The SolventSeg result therefore does not generalize unconditionally; it is programme-specific, and the map records it as such.

**Outcome-unseen nulls.** Starrydata and TRI (photocatalysis), both outcome-unseen at the time of transfer, produced all-null transfers under the same contract (no edge passed). These are not failed experiments; they are correct abstentions — the mechanism abstains when the relation does not survive the boundary.

**Boundary synthesis.** The same contract that produced the two positives also produced its own negatives. This is the property that makes the framework scientific: it can be wrong in the direction of abstention, and it was.

### 3.5 The auditable borrowing map and routing discipline

**What is archived.** A machine-readable map of every declared edge (donor, recipient, transferred object, provenance, falsifiers, gate outcome, classification) in the manifest; attempt ledger; and verification records. Each positive edge carries its claim guard, its null/harmful boundary, and the exact archive/DOI hash.

**Routing discipline (the operational rule).** To borrow experimental knowledge:
1. Define a directed edge (donor → recipient) with a declared decision endpoint (predict, rank, or abstain).
2. Preserve experimental state: temperature, concentration, composition scope, and measurement protocol must be matched or explicitly violated.
3. Transfer the narrowest object the decision requires (relation, ordering, or nothing).
4. Challenge with recipient-only and matched false-donor controls.
5. Abstain when the contract fails; record the abstention.
6. Freeze the contract before recipient outcome access if the claim is prospective.

---

## 4. Discussion — what transfers, and what does not

**Why relations transfer when databases do not.** A database is a population snapshot; its rows are tied to a provenance distribution. A model is a fitted function over that population. A relation is a falsified statement of dependence that can be *stated independently of the population* and re-falsified on a new population. The LiAsF₆ result and the SolventSeg ordinal result are both relations: they specify *what varies with what* under a declared provenance, not *what the absolute values are*. The 0/40 benchmark and the Borg coefficient failure are what happens when the object transferred is a population-level artifact instead.

**The abstention is a feature, not a bug.** The frozen FINALES negative and the two outcome-unseen nulls are the strongest evidence that the framework measures something real: it refuses to claim transfer when the relation does not survive. A framework that always transferred would be indistinguishable from a hallucination. The presence of a systematic abstention rule is what converts "these two databases happened to correlate" into a falsifiable scientific claim.

**Boundary conditions and limitations.** (i) All positive results are retrospective/post-outcome; they do not convert into prospective claims. (ii) BambooMixer lacks row-level DOI provenance; the interaction analysis is explicitly post-outcome cross-database method development. (iii) The leave-one-programme admission gate (CS14) is method-development-complete, not a validated universal selector. (iv) CS13 (prospective/temporal candidate test) is complete-boundary, not independent confirmation. (v) The 0.910 ordinal result is conditional on the SolventSeg recipient; FINALES shows it does not generalize unconditionally. (vi) The model envelope is limited to composition descriptors and tree/kernel learners; graph representations, mechanistic latent variables, calibrated GPs, and cost-aware policies may expose additional portable relations but require the same grouped, falsifier-controlled evaluation.

**The decisive next test is not another retrospective edge.** It is a preregistered recipient programme in which donor selection, transferred object, anchor budget, falsifiers, and decision endpoint are frozen before any recipient outcome is accessed, followed by prospective measurement of the proposed shortlist. We specify this protocol in Section 5 and archive it.

---

## 5. The pre-registration protocol (prospective route)

1. **Freeze** the recipient programme, the donor archive (by hash), the transferred object (relation or ordering), the anchor budget, the falsifier set, and the decision endpoint *before* any recipient outcome is accessed.
2. **Declare** the admission gate: concordance advantage over the strongest recipient-only baseline, permutation p, regret improvement, top-quartile precision, and the minimum eligible-pair count — all with their thresholds.
3. **Pre-commit** to the abstention rule: if the gate fails, the edge is recorded as abstained and no post-hoc refit is permitted to rescue it.
4. **Measure** the proposed shortlist prospectively (new measurements, not previously accessed outcomes).
5. **Report** all edges, including abstentions, in the manifest; the verification records make each claim independently auditable.

---

## 6. Conclusions

Neighbouring experimental data can materially improve data-poor OOD decisions, but adjacency is not itself transferable knowledge. Generic donor-feature injection repaired 0 of 40 declared edges; a strong alloy relation was destroyed by a change in provenance (R² = −3.006); a pretrained encoder caused 28.1% harm. On separate recipients where the shared relation and decision endpoint were explicit, a mixture relation reduced external LiAsF₆ log-RMSE by 27.41%, and a zero-label ordinal score ordered unmeasured formulations at ρ = 0.910 versus the strongest five-label recipient-only model's 0.537. Controlled predictive, ranking-only, harmful, and frozen-abstention cases showed where those gains stopped. **The transferable unit in experimental science is a falsified relation with its provenance attached — not a database, and not a model.** The operational rule is to define a directed edge, preserve its experimental state, transfer the narrowest object the decision requires, challenge it with recipient-only and matched false donors, and abstain when the contract fails.

---

## Data availability (elevated)

The public catalog, source metadata, normalized-schema definition, source revisions, and task-specific provenance records are provided in the repository. Raw or derived data are redistributed only where source terms permit; external resources that cannot be redistributed are identified by stable URLs, file identifiers, commits, and hashes. The independent electrolyte recipients are available from the SolventSeg archive (doi:10.5281/zenodo.6299956; associated article doi:10.1016/j.xcrp.2022.101047) and the FINALES Materials Cloud record doi:10.24435/materialscloud:qt-1s. All figures and verification JSONs referenced here are listed in `analysis/submission/SUBMISSION_CHECKLIST.md`.

---

## Verification appendix (all numbers traced to frozen records)

| Claim | Value | Frozen record |
|---|---|---|
| Borg in-domain R² / BIRDSHOT / unchanged-coefficient transfer | 0.790 / 0.067 / −3.006 (−4.154 to −2.185) | parent manuscript §3.1 (attempt ledger, Borg/BIRDSHOT) |
| Generic donor-feature OOD-repair passes | 0 of 40 real edges; 3 cross-database edges all failed | `analysis/results/multi_target_ood_summary.json` |
| Mean programme-level far-OOD gain | 0.92% (95% CI −0.35 to 2.92%) | same |
| Pretrained encoder harm | 28.1% worse (scaffold-OOD photocatalysis), failed shuffled control | Supplementary §S10.2 |
| LiAsF₆ external metrics | log R² 0.718, raw R² 0.607, ρ 0.864, log-RMSE 0.342 (n=1,660; 156 formulations) | `analysis/results/bamboomixer_LiAsF6_only_summary.json` |
| LiAsF₆ vs state-only | −27.41% (21.79–32.92); Δρ +0.158 | same |
| LiAsF₆ vs chemistry-permuted | −25.88% (20.73–31.09); Δρ +0.129 | same |
| LiAsF₆ drop-LiPF₆ / LiPF₆-only | 16.08% (12.10–19.80) / full-source only | same |
| SolventSeg programme-balanced frozen | ρ 0.910, precision 0.933, regret 0.00047 | `analysis/results/bamboomixer_cross_database_interaction_summary.json` |
| Strongest recipient-only (five labels) | ρ 0.537 (RBF kernel ridge) | same + parent §3.3 |
| Δρ vs recipient-only / vs per-draw oracle | 0.374 (0.213–0.562) Holm p=0.00070 / 0.300 (0.183–0.540) | same |
| Programme-balanced vs best single donor | Δρ +0.0236 (0.0069–0.0397); precision 0.826→0.933 | same |
| Absolute prediction failure | −18.0% vs state-only → ranking-only decision | same |
| FINALES frozen second recipient | 0.694 vs 0.783, Δ −0.089 (−0.293 to 0.096), p=0.131, regret 0.563 vs 0.180 | `analysis/results/finales_rank_replication_summary.json` |
| Outcome-unseen nulls | Starrydata & TRI: all-null transfers | `analysis/results/starrydata_reverse_VALIDATED.json`, `analysis/results/tri_oer_VALIDATED.json` |
| KIT supplementary (S4) | −15.02% (8.61–21.10) at −20→−30 °C; temperature controls 15.02/5.01/0.95/−0.76%; shuffled −2.96% | KIT compact outputs (manifest) |
| Experiment registry | 15 paper_submission_required; CS01–02 complete; CS03–13/15 complete-boundary; CS14 method-development-complete | `analysis/core_story_experiment_registry.json` |

---

## Figure plan (elevated)

- **Figure 1 — The wrong objects.** Panel a: Borg coefficient destroyed by provenance (R² 0.790 → −3.006). Panel b: 0/40 gate outcomes; 3 cross-database edges highlighted. Panel c: 28.1% encoder harm.
- **Figure 2 — The right object.** LiAsF₆ cross-salt relation: external R² 0.607, ρ 0.864, falsifier contrasts (−27.41% vs state-only, −25.88% vs permuted; drop-LiPF₆ 16.08%).
- **Figure 3 — Ordinal survival.** SolventSeg zero-label ranking ρ 0.910 vs 0.537 recipient-only; per-draw oracle contrast; programme-balanced precision 0.933.
- **Figure 4 — The abstention boundary.** FINALES frozen negative (Δ −0.089) and outcome-unseen nulls; the routing map with abstain class.
- **Figure 5 — The borrowing map.** All 40 edges, classification (predict/rank/abstain), and provenance hash; the pre-registration protocol as an inset.

---

*This is the elevated story-line manuscript. The submission-ready full paper (all methods, supplementary, figures, references) remains `analysis/submission/SUBMISSION_MANUSCRIPT.md`; this document is the narrative core for the Digital Discovery submission and the basis for the response-to-Nature-comment discussion.*
