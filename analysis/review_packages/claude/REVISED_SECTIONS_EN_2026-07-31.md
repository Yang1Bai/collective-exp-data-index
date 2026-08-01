# Manuscript-ready revised sections (English)

Drop-in replacements for `MANUSCRIPT_DRAFT_STREAMLINED.md`. Text not reproduced here is unchanged. Every number is taken verbatim from the current draft, SI §S10.3, or `ATTEMPT_LEDGER.csv`; no value has been altered.

---

## Title

**Recommended:**

> Falsification-gated borrowing routes neighbouring experimental knowledge to out-of-distribution prediction, screening or abstention

**Alternatives:**

1. Falsification-gated knowledge borrowing selectively improves out-of-distribution prediction and screening
2. Qualified relations, not pooled databases, carry experimental knowledge across out-of-distribution boundaries

*(Rationale: the current title's unconditional "improves" claims the effect; the recommendation claims the contribution — the routing map — and encodes abstention, which is half the evidence.)*

---

## Abstract

> Models are most valuable to experimental science when they extrapolate beyond what has already been measured, but this is where data-poor models are least reliable. Neighbouring experimental programmes could supply the missing knowledge, yet physical similarity between databases does not specify what is portable or how it should be used. Here we treat knowledge borrowing as a directed, falsifiable contract: donor and recipient must share candidate-level inputs, the relevant experimental state, a declared transferable relation, and a decision endpoint; otherwise the method abstains. Generic injection of a donor prediction repaired 0 of 40 declared out-of-distribution (OOD) edges across eight recipients. In contrast, a component-order-invariant electrolyte relation learned from 10,407 measurements across 22 salts predicted an external programme for a salt absent from the source with raw \(R^2=0.629\), Spearman \(\rho=0.871\), and 28.6% lower log-scale error than a temperature–concentration baseline. Where absolute calibration was not portable, a programme-balanced ordinal score computed without recipient labels ranked unmeasured formulations at \(\rho=0.910\), whereas the strongest of 13 recipient-only models trained on five measured formulations reached \(\rho=0.537\) (\(\Delta\rho=0.374\), 95% interval 0.213–0.562). Controlled chemical perturbations separated predictive, ranking-only and harmful edges, and the unchanged ordinal route failed to qualify in a frozen second recipient and was withheld. These retrospective benchmarks show that neighbouring experiments can materially improve selected OOD predictions and screening decisions — provided the transferred object is qualified against matched falsifiers, routed to the endpoint it can support, and withheld when the contract fails.

*(Changes: W2 fix — the score is zero-label and the five labels belong to the baselines; "retrospective benchmarks" disclosed once; FINALES stated as failure-to-qualify, not non-transfer; 28.64% → 28.6% in the abstract only, full precision retained in Results; final sentence makes abstention part of the claim.)*

---

## Introduction (four paragraphs)

**¶1 (problem — light edits only).**

> Scientific exploration is intrinsically an out-of-distribution (OOD) problem. The candidates most likely to extend knowledge lie outside the compositions, formulations, or operating states already measured, and they are also the candidates for which a data-poor model has the weakest empirical support, mechanistic guidance, and uncertainty calibration. The tension is acute in experimental materials science and chemistry, where measurements are expensive and distributed across small, heterogeneous programmes. A neighbouring programme may nevertheless contain partial knowledge of a shared composition space, transport process, structural motif, or measurement state. The unresolved question is whether that knowledge can reduce an OOD evidence deficit without importing a spurious relation or negative transfer.

**¶2 (why more data is not the answer — unchanged except final sentence).**

> Larger data collections do not resolve this problem by themselves. An experimental value is inseparable from material identity, formulation or processing, test conditions, provenance, and reporting practice. Distributed databases therefore constitute a partial scientific memory rather than a pool of interchangeable labels [@Draxl2022FAIR; @Akhound2026ExperimentalMemory]. Harmonized infrastructures make that memory findable and exchangeable [@Blaiszik2016MDF; @Andersen2021OPTIMADE; @MedinaSmith2021Vocabulary], but pooled correlations can still be driven by chemical families, restricted ranges, or coupled parameter estimation [@Krug1976Compensation; @CornishBowden2002Phantom]. Transfer learning, cross-property models, task maps, and multi-information-source optimization offer more active forms of reuse [@Yamada2019Shotgun; @Jha2019DeepTransfer; @Gupta2021CrossProperty; @Chang2022MixtureExperts; @Zamir2018Taskonomy; @Kandasamy2017Multifidelity]. Yet a related database is not automatically a calibrated fidelity, and a strong in-domain fit is not evidence that its knowledge survives a new experimental programme.

**¶3 (the missing unit — unchanged except sharpened burden-of-proof close).**

> The missing unit is not another database but a qualified relation. We call two programmes neighbours for a particular task only if they share a candidate-level representation and a falsifiable physical or experimental relation to the recipient endpoint. What crosses that directed edge may be a composition–performance relation, a state-aware mixture response, or an ordinal score; it need not be a raw feature vector or a calibrated property value. This definition matters because heuristic OOD splits can remain interpolative [@Li2025OOD], whereas transformations can be more portable than raw features or pretrained weights [@Yahagi2025DomainTransformation]. It also inverts the burden of proof: a borrowing edge must preserve the state that makes the relation meaningful, beat a matched false donor, improve the endpoint that will actually guide the experiment, and be rejected when any required condition fails.

**¶4 (what we do — W2 fix, tightened roadmap, map as the closing claim).**

> Here we introduce falsification-gated knowledge borrowing. The method keeps the source database behind, permits only a qualified relation or candidate order to cross into the sparse OOD recipient, and routes that object to prediction, screening, or abstention (Fig. 1). We test the idea along increasing transfer distance. The obvious alternatives fail first: unchanged coefficient transport collapses across alloy programmes, and generic donor-feature injection repairs 0 of 40 declared OOD edges. A component-order-invariant relation learned from 10,407 conductivity measurements then reduces log-scale error by 28.64% for a salt absent from the source, and a controlled catalyst series shows why the same kind of relation must be routed separately to prediction, ranking, or rejection. Finally, where numerical calibration fails, an ordinal score from three independently trained programmes orders unmeasured formulations at \(\rho=0.910\) — against \(\rho=0.537\) for the strongest recipient-only model trained on five measured formulations — yet the unchanged score fails to qualify in a frozen second recipient. The result is not a universal transfer model. It is an operational map from a qualified neighbouring relation to numerical prediction, candidate screening, or abstention, together with the falsifiers that define where each route ends.

---

## Results transitions (exact replacement sentences)

**§3.1, compression of the compensation paragraph (C6).** Replace the "pooled regularity" paragraph ("The pooled regularity tests showed why…") with:

> Pooled regularity tests reached the same verdict from the opposite direction: a strong pooled adsorption heat–intercept association (\(R^2=0.637\) across 1,103 systems) survived a parameter-coupling artifact null yet retained adsorbate-family structure under article-cluster tests (\(p=0.0002\)), so association, artifact resistance, family conditioning, and transport remained distinct claims (Supplementary Section S7).

**§3.1, new closing sentence (C7), after "…not a reliable way to repair recipient OOD prediction."**

> Nor is model capacity the explanation: strong pretrained molecular encoders that passed every source-skill gate made a scaffold-OOD photocatalysis recipient 28.1% worse on average, failing against their own shuffled controls (Supplementary Section S10.2).

Keep the existing bridge paragraph ("These negative controls do more than motivate a different model…") unchanged.

**§3.2, closing (C8).** Replace the final sentence of §3.2 with:

> This retrospective external benchmark establishes the feasibility of numerical relation transfer, not prospective confirmation in a previously unseen programme — and it leaves open whether one qualified relation should be used the same way in every nearby recipient.

**§3.3, closing — keep unchanged** ("…This selectivity experiment explains why the map routes each edge to prediction, screening or abstention instead of reporting a pooled transfer effect."). It already hands off correctly.

**§3.4, opening (C3/C9).** Replace the first two sentences with:

> Numerical prediction is not the only decision an experiment requires. We therefore asked a narrower question: can neighbouring knowledge identify which unseen candidates should be measured first, even when their property values cannot be calibrated — and can it do so better than any model built from the few labels the recipient actually has?

**§3.4, headline comparison (C3/C9).** Replace "Across 100 outcome-independent selections… (95% anchor-coverage interval 0.213–0.562; Fig. 4b)." with:

> Across 100 outcome-independent selections of five measured recipient formulations, the zero-label source score retained mean \(\rho=0.910\), precision 0.933, and regret 0.00047 on the remaining candidates. The strongest of 13 recipient-only configurations trained on those same five formulations was radial-basis kernel ridge regression, with \(\rho=0.537\), precision 0.490, and regret 0.0393. The source advantage was \(\Delta\rho=0.374\) (95% interval 0.213–0.562 over anchor selections, conditional on this recipient programme; Fig. 4b).

**§3.5, heading and first sentences (C10).** Replace the heading and opening with:

> ### 3.5 A frozen second recipient fails to qualify, and the map abstains
>
> The accepted ordinal route was carried unchanged into a second experimental programme, with donor, chemistry conversion, anchor budget, metrics, thresholds, and inference frozen before any outcome was accessed. It did not qualify. In the frozen Fast INtention-Agnostic LEarning Server electrolyte recipient, the donor ranking achieved pairwise concordance of 0.694, whereas the strongest recipient-only model fitted to the same three chronological anchors achieved 0.783. The donor advantage was \(-0.089\) (95% bootstrap interval \(-0.293\) to 0.096; permutation \(p=0.131\); Fig. 4d) — an interval compatible with harm, with no effect, and with a modest benefit smaller than the recipient baseline's. Under the frozen contract this is precisely the situation in which the method must withhold the edge rather than defend it.

Keep the remainder of §3.5 (precision tie, regret, matched-versus-unmatched provenance discussion) unchanged.

---

## Discussion (revised §4.3; §§4.1–4.2 unchanged except one word)

**§4.2, one-word change:** "The SolventSeg score produced a large and robust ranking gain while failing numerical calibration" → retain; no other change.

**§4.3, full replacement:**

> ### 4.3 Retrospective evidence defines the next prospective test
>
> The strongest positive results remain retrospective, and the asymmetry deserves to be stated plainly: every design that was frozen before outcome access — the FINALES second recipient, and the outcome-unseen Starrydata and TRI programmes reported in the Supplementary Information — ended in rejection, null, or abstention, whereas every positive result was developed after some recipient outcome had been inspected. The controlled catalyst composition analysis was promoted after its planned control was inspected; the unseen-salt representation was designed after the public recipient outcomes and the published transfer observation were known; the SolventSeg portfolio and recipient stress test were developed after earlier outcomes had been inspected. Design freezes, intact-group inference, matched falsifiers, and independent recalculation protect the reported estimands, but they cannot convert them into prospective confirmation.
>
> This asymmetry is not evidence that the framework fails; it is the framework operating as designed. A falsification-gated map earns trust precisely by rejecting attractive edges under frozen contracts, and the frozen negatives demonstrate that the gates bind. What the retrospective positives establish is existence and magnitude: large OOD improvements are possible, and the contracts under which they occurred are now explicit. What they cannot establish is the probability that a newly nominated neighbouring programme will transfer — positive evidence is concentrated in selected catalyst and electrolyte programmes, SolventSeg contains 36 formulations, and the frozen second recipient was withheld.
>
> The current model envelope is limited to composition descriptors and tree or kernel learners. Graph representations, mechanistic latent variables, calibrated Gaussian processes, and cost-aware experimental policies may expose additional portable relations, but they require the same grouped and falsifier-controlled evaluation. The decisive next test is therefore not another retrospective edge. It is a preregistered recipient programme in which donor selection, transferred object, anchor budget, falsifiers, and decision endpoint are frozen before any recipient outcome is accessed, followed by prospective measurement of the proposed shortlist. The present framework supplies the contract, the falsifiers, and the failure criteria for that experiment.

---

## Conclusions (one-sentence fix)

Replace "an ordinal score increased five-label candidate ordering from \(\rho=0.537\) to 0.910" with:

> a zero-label ordinal score ordered unmeasured formulations at \(\rho=0.910\) where the strongest five-label recipient-only model reached 0.537

---

## Figure legends (full replacements)

**Figure 1 | Falsification-gated knowledge borrowing into a sparse OOD recipient.**
**a,** Conceptual illustration of three neighbouring experimental programmes, their measurement records, and a sparse recipient landscape. The source databases remain in place: only a candidate-level relation or ordering signal can cross, and only after shared inputs, the relevant experimental state, a declared physical relation, and a matched falsifier have been satisfied. Most candidate streams terminate at these checks. The surviving teal path enters the recipient landscape, in which filled blue cubes denote measured anchors and open orange cubes denote unmeasured OOD candidates; the coral branch denotes abstention. Panel a is explanatory rather than quantitative. **b,** Decision-level evidence from the committed result tables. Numerical prediction is accepted for the external unseen-salt programme: 28.64% lower log-RMSE than a temperature–concentration baseline, raw \(R^2=0.629\), \(\rho=0.871\). Ordinal screening is accepted when a programme-balanced score computed without recipient labels orders unmeasured formulations at \(\rho=0.910\) (high-performance-quartile precision 0.933), whereas the strongest recipient-only model trained on five measured formulations reaches \(\rho=0.537\) (precision 0.490). Otherwise the method abstains: generic donor-feature injection passed 0 of 40 complete OOD-repair gates, and the frozen second-recipient donor concordance of 0.694 was below the recipient-only value of 0.783.

**Figure 2 | Strong fits and generic donor features do not establish portable knowledge.**
**a,** The relation between ultimate and yield strength is strong inside one alloy programme (\(R^2=0.790\)) but fails unchanged coefficient transport to an independent programme (\(R^2=-3.006\)); the dashed orange line is fitted only to show the recipient shift. **b,** Mean relative far-OOD RMSE effects for 40 real donor-feature edges across eight recipients. The outlined column contains the declared donors; positive values denote lower error. **c,** Collapsed audit of the declared edges. A complete pass requires useful absolute performance, repeat and learner robustness, OOD- and donor-specificity, multiplicity-adjusted inference, and exclusion of record overlap. No real edge passes the complete gate; the seven-programme mean far-OOD gain is 0.92% (95% interval \(-0.35\) to 2.92%).

**Figure 3 | Qualified relations improve selected complete OOD prediction tasks.**
**a,** A component-order-invariant mixture relation trained on 10,407 measurements from 22 salts is applied, without recipient labels, to 1,827 measurements of lithium hexafluoroarsenate, a salt absent from the source. **b,** Zero-label external prediction. Colour density denotes overlapping observations and the dashed line denotes equality; raw- and log-scale \(R^2\) are reported separately. **c,** Relative log-RMSE gain of the full relation over matched state-only, chemistry-permuted, salt-exclusion, nearest-salt and wrong-salt comparators. Points are formulation-grouped bootstrap means; bars are 95% intervals. This benchmark was designed after the recipient outcomes were public and is retrospective (Methods 2.6). **d,** Five-anchor effects in four controlled catalyst perturbations from the disclosed post-primary composition relation. Positive values denote lower RMSE or higher Spearman correlation; right-hand labels give the route assigned to each complete non-anchor candidate set (predict + rank, ranking only, or reject).

**Figure 4 | Cross-programme knowledge recovers candidate ordering but remains programme-specific.**
**a,** Three independently trained conductivity sources produce a programme-balanced score. The endpoint gate routes the score to candidate screening and rejects its interpretation as calibrated conductivity. **b,** The zero-label source ranking compared with 13 recipient-only configurations trained on five measured formulations and with a non-deployable per-draw recipient oracle. Points are means and bars are 2.5th–97.5th percentiles over 100 outcome-independent anchor selections, conditional on this recipient programme. **c,** Source and fixed recipient-only ordering across three, five and ten measured formulations; shaded regions are the corresponding percentile intervals, including their negative lower tails. **d,** Donor advantage with 95% intervals in the primary recipient and under an unchanged, frozen contract in a second programme. The ordinal route is accepted only in the first; in the second it fails to qualify and is withheld.

---

## Supplementary Information corrections

1. Retitle the SI to match the manuscript title and change "This document is the reporting companion to `MANUSCRIPT_DRAFT.md`" to "…to `MANUSCRIPT_DRAFT_STREAMLINED.md`".
2. §S2 first paragraph: "Six enter as frozen external or temporal programmes" → "Seven enter as frozen external or temporal programmes" (Table S1 lists seven; main text §2.1 says seven).
