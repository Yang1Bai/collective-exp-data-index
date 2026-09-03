# Manuscript reorganization after the controlled OER perturbation series

## One-sentence argument

Neighboring experimental data improve out-of-distribution decisions only when
the transferred object is matched to both provenance distance and the decision
endpoint: a supported composition–performance relation plus a few recipient
anchors can cross selected experimental perturbations, provenance-anchored
response relations can cross article-specific offsets, and preserved ordinal
scores can improve candidate screening, whereas generic feature injection and
unqualified transfer should be rejected.

## Evidence hierarchy

### Tier 1: main-text claim-bearing results

| Result | Quantitative evidence | Claim it supports | Claim it does not support |
|---|---:|---|---|
| SpecGen derivative B and D | Five-label pooled RMSE gains 16.3% and 26.1%; pooled Spearman gains 0.347 and 0.407; all four candidate-bootstrap intervals exclude zero | A declared composition–OER relation plus a few recipient anchors can rescue complete-system OOD prediction for selected ligand or metal perturbations | Cross-laboratory independence; the composition analysis was promoted after its control result was seen |
| SpecGen derivative A and C boundary | A retains ranking but RMSE gain is only 3.2% with an interval crossing zero; C makes RMSE 10.4% worse | The same donor can be prediction-positive, ranking-only, or harmful depending on the perturbation | A universal composition-transfer rule |
| CALiSol contrast-and-anchor transfer | Macro-RMSE −6.91% versus the same-anchor absolute donor; article-bootstrap 0.88–14.00%; exact \(p=0.035\); 8/11 articles improve | Across article-specific scale shifts, a within-article response relation plus a small target anchor is more portable than an absolute donor prediction | Independent confirmation; the method was developed after the absolute-transfer null was known |
| SolventSeg programme-balanced ordinal transfer | With five recipient labels, source \(\rho=0.910\) versus 0.537 for the strongest of 13 recipient-only configurations; \(\Delta\rho=0.374\), 95% anchor-coverage interval 0.213–0.562; source-minus-per-draw recipient oracle 0.300 [0.183,0.540]; precision 0.933; regret 0.00047 | Separately trained neighboring experimental programmes can materially improve retrospective OOD candidate ordering when combined with equal programme weight, even when absolute calibration fails | Independent confirmation, reliable top-1 discovery, prospective acceleration, or universal electrolyte transfer |
| Frozen FINALES second-recipient test | Donor concordance 0.694 versus 0.783 for the strongest three-anchor recipient-only baseline; \(\Delta=-0.089\); 95% CI −0.293–0.096; permutation \(p=0.131\); regret 0.563 versus 0.180 | The framework must abstain even when chemistry and endpoint appear matched; SolventSeg is a positive edge, not a universal electrolyte rule | A successful independent replication |
| Systematic generic-injection benchmark | 0 of 40 real donor-feature edges repaired the designated OOD tasks across eight targets | Physical adjacency and an extra donor feature are insufficient; routing is necessary | All knowledge borrowing is impossible |

### Tier 2: concise triangulation or boundary evidence

| Result | Main-text use |
|---|---|
| Physics-aware mixture relation to an external new-salt programme | Strong method-development example: zero-shot raw \(R^2=0.629\), \(\rho=0.871\), and 28.64% [24.03%,33.52%] lower log-RMSE than state-only; chemistry permutation and neighbour-exclusion falsifiers pass, and 7/9 leave-one-salt-out targets improve in both error and ranking. State explicitly that the public target outcome and published result were inspected before method design, so this is not independent confirmation |
| KIT adjacent-temperature electrolyte prediction | One concise short-provenance rung: RMSE −15.02%, all five formulation folds improve |
| SpecGen later 20-candidate sets | Temporal rank corroboration for B, C and D, with the explicit caveat that candidates were selected by the source workflow |
| Caltech ESTM hard-OOD fixed ranking | One concise corroborating sentence or small panel: the only multiplicity-surviving external static-ranking contrast; do not present both donors as significant |
| Outcome-unseen Starrydata and TRI | One paragraph establishing abstention and cross-target heterogeneity |
| Pooled compensation and coefficient-transport tests | Short motivation that high in-domain association is not portable knowledge; detailed fits move to SI |
| OBELiX fixed-screening versus sequential-acquisition divergence | One compact endpoint-separation result; detailed policy curves move to SI |

### Tier 3: supplementary robustness, not headline evidence

| Result | Reason for demotion |
|---|---|
| State-matched MPEA UTS→YS +9.21% | Strict provenance-specificity analysis removes confirmatory status; the result remains useful as within-program mechanism development |
| Full resource/edge inventory | Establishes scope and auditability but does not advance the scientific mechanism |
| All wrong-domain donors, learner sensitivities, and per-fold values | Necessary falsification detail, but too dense for the main narrative |
| Battery, OPV, band-gap, and generic deep-donor nulls | Retain in the complete map/SI; use at most one aggregate sentence in the main text |

## Revised scientific structure

### 1. Why neighboring data are not automatically knowledge

Define the problem as OOD scientific decision-making under incomplete
experimental knowledge. Establish that a pooled relation, a skilled donor
model, and a transportable object are three different things.

### 2. The endpoint-routed borrowing contract

Define four transfer objects:

1. **Anchored performance relation** for numerical estimation when the donor
   and recipient share endpoint, representation and a declared experimental
   perturbation.
2. **Provenance-anchored response relation** when the relation is portable but the
   absolute scale changes across articles or laboratories.
3. **Independent ordinal score** for candidate screening when ordering may
   survive but calibration does not.
4. **Physics-aware mixture relation** when a recipient contains a new
   component identity but shares a mixture state space and endpoint with the
   source. Use an invariant source relation for zero-shot prediction and allow
   recipient anchors to fit only a shrinkage calibration.

All three require identity/provenance exclusion, grouped source skill, matched
falsifiers, practical utility, and abstention.

### 3. Generic borrowing fails

Lead the results with 0/40 OOD repairs. This is the necessity result: the paper
is not claiming that a better learner automatically transfers knowledge.

### 4. A controlled perturbation series shows when relation transfer works

Lead the positive results with the four derivative OER systems. Present B and
D as prediction-and-ranking positives, A as ranking-only, and C as harmful.
The within-series controls make selectivity visible without comparing unrelated
domains.

### 5. Transfer succeeds when the object matches the distance

Present the positive evidence in increasing provenance distance:

1. SpecGen/KIT: anchored or state-conditioned prediction within a programme.
2. CALiSol: anchored response relation across articles.
3. SolventSeg: programme-balanced ordinal ranking across databases, with
   absolute-prediction abstention and a 13-model recipient-only stress test.

The order itself is the mechanistic result. Each step transfers less absolute
information as provenance distance increases.

### 6. A frozen second recipient defines the boundary

Present FINALES directly after SolventSeg. The unchanged ranking loses to a
three-anchor recipient-only baseline despite identical named chemistry and
endpoint. This prevents the SolventSeg result from being mistaken for a
universal LiPF6/EC/EMC conductivity law and motivates abstention based on
programme state, sampling policy, and measurement provenance.

### 7. The output is a borrowing map, not a universal model

The map routes an eligible edge to prediction, anchored correction, ranking,
or rejection. Positive, null, and harmful edges are all outputs of the method.

## Revised figure architecture

1. **Figure 1 — The endpoint-routed borrowing framework.** OOD knowledge gap,
   directed donor→recipient edge, provenance ladder, three transferable
   objects, and gate outcomes. Dataset breadth is a small evidence strip, not
   the visual thesis.
2. **Figure 2 — Why generic transfer fails.** Pooled-relation transport
   failure, 0/40 systematic OOD repairs, and the matched falsifier logic.
3. **Figure 3 — Controlled OER perturbations identify a portable relation.**
   Four complete derivative systems, shuffled-source controls, five-label
   prediction and ranking effects, and later-candidate corroboration.
4. **Figure 4 — The portable object contracts with distance.** KIT and CALiSol
   prediction/anchor results followed by the SolventSeg source-portfolio
   ranking result, its recipient-oracle stress test, and the frozen FINALES
   non-replication.
5. **Figure 5 — Actionable borrowing map.** Route edges to calibrated
   prediction, anchored relation, independent shortlist, or abstention;
   include one Caltech corroboration and outcome-unseen boundaries.

## Claims to remove from the abstract and title

- The resource count as a proxy for generality.
- MPEA UTS→YS as the hero result.
- “Cross-database rankings recovered complementary regions” without the
  corrected multiplicity result.
- Any implication that SolventSeg establishes reliable top-1 discovery or
  prospective acceleration.
- Any implication that the FINALES null weakens the method. It weakens a
  universal electrolyte edge and strengthens the need for the gate.

## Preferred title

**Endpoint-routed knowledge borrowing selectively improves
out-of-distribution decisions from neighboring experiments**

## Final reader takeaway

The paper succeeds if the reader leaves with one operational principle:
transfer the smallest relation that is supported by the recipient endpoint:
an anchored composition–performance relation in a controlled perturbation, a
provenance-anchored response relation across studies, then only a candidate
ordering across databases—and reject the edge when its matched falsification
gate fails.
