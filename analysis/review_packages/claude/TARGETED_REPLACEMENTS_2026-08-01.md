# Targeted manuscript replacements — second pass (2026-08-01)

Drop-in patches for `MANUSCRIPT_DRAFT_STREAMLINED.md`, its figure captions, `SUPPLEMENTARY_INFORMATION.md`, and `TERMINOLOGY_LEDGER.md`. Text not listed here is correct and should be left unchanged. No verified numerical value is altered.

Rationale for each patch is in `SECOND_PASS_REVIEW_2026-08-01.md` §3 (risks R1–R5) and §6 (figure logic).

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
