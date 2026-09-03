# Main-text streamlining map

> Superseded on 2026-07-30 by
> `analysis/MANUSCRIPT_REORGANIZATION_2026-07-30.md` after independent
> validation of SolventSeg and the frozen FINALES second-recipient
> non-replication. The MPEA result is no longer the hero result, and this file
> is retained only as an audit trail of the earlier narrative.

## Locked paper argument

Across heterogeneous experimental materials data, neighboring knowledge does
not transfer automatically. When experimental state, endpoint, leakage
boundaries, and decision contracts are aligned, however, qualified donor
information can improve few-shot and chemically held-out OOD prediction.
Target-model-independent donor rankings can also support cross-database OOD
exploration, while matched falsifiers and abstention prevent unsupported
transfer claims.

## Evidence retained in the main text

| Evidence block | Role in the argument | Main-text treatment |
|---|---|---|
| 20 analysed resources and 96,184 normalized measurements | Establishes empirical breadth and source-pinned provenance | Retain once in Abstract, Introduction, and Fig. 1; avoid repeating the inventory |
| Borg-to-BIRDSHOT coefficient transport | Shows that strong source correlation is not a portable law | Retain as the first falsification example |
| Thermoelectric and ISODB compensation tests | Shows that pooled regularities may be weak, artefactual, or conditional | Compress into one paragraph paired with coefficient transport |
| KIT −20→−30 °C | Strong within-campaign few-shot success | Retain as the first positive borrowing example |
| CALiSol and Matbench | Demonstrate that nominal adjacency is insufficient | Retain as concise external boundaries beside KIT |
| Eight-target, 40-edge OOD benchmark | Rejects generic donor-feature injection | Retain as the baseline failure that motivates state matching |
| State-matched MPEA UTS→YS | Main positive OOD-prediction result | Promote as the hero result with matched shuffle, Q1/Q4 boundary, and measured-UTS ceiling |
| OBELiX fixed ranking versus UCB | Separates prediction, screening, and sequential acquisition | Retain only the decisive fixed-ranking direction and sequential null |
| Caltech OBELiX/ESTM rankings | Cross-database OOD-exploration feasibility and complementarity | Retain as the main external exploration result |
| Starrydata and TRI outcome-unseen tests | Prevents post-hoc selectivity and supports abstention | Retain as one compact boundary subsection; detailed cells stay in SI |

## Evidence moved out of the main narrative

| Material | Destination | Reason |
|---|---|---|
| Complete gate lists, exact amendments, hashes, job identifiers, and verifier lifecycle | Methods summary table and SI | Essential for reproducibility but interrupts the scientific argument |
| Per-fold and per-learner values for KIT, CALiSol, BIRDSHOT, and Matbench | SI Tables S2–S3 and S6 | Secondary robustness details |
| OBELiX post-result novelty/fusion benchmark and full knowledge-deficit surface | SI S8 | Outcome-informed method development does not change the primary result |
| Caltech local multiplicative-gate failure and full CCA family-first sensitivities | SI S8 | Useful design diagnostics but not independent evidence |
| Leave-one-program CCA meta-gate | SI S9 | Does not outperform adjacency or abstention and distracts from the validated contracts |
| Multi-stage battery programme | New SI subsection / separate development report | Frozen primary is non-evaluable and favorable continuous borrowing was outcome-guided |
| Focused optical Chemprop-to-photocatalysis test | SI S10.2 / separate findings report | Strong source skill and state-aware representations still produced harmful scaffold-OOD corrections; useful as a rigorous rejection, not another main-text showcase |
| All six source-derived hypothesis cards | SI S8–S9 | They define future tests but do not establish a discovery |
| Full programme-by-programme limitation ledger | SI and evidence table | Repetition makes the main text defensive |

## Material removed from the submission narrative

- Balam job numbers in prose.
- Chronological accounts of failed implementation and verifier amendments.
- Repeated statements that the same result is retrospective, post-selection, or
  non-prospective after that status has been defined once.
- The phrase `local task rescue` outside tables.
- Broad claims about large language models that are not tested by this study.
- Repeated recitations of every null effect after its decision status is clear.

## Main-text architecture

1. **Introduction**: OOD knowledge scarcity; why aggregation is unsafe; why
   existing transfer methods do not qualify experimental neighbors; present
   strategy and decisive results.
2. **Methods**: resource layer; borrowing objects and gates; prediction
   protocols; OOD exploration protocols; pooled-law falsification; outcome-unseen
   boundary tests; statistics and reproducibility.
3. **Results and discussion**:
   1. experimental integration enables directed tests;
   2. pooled regularities do not imply portable laws;
   3. neighboring-condition borrowing is selective;
   4. state matching converts the best OOD edge into useful prediction;
   5. preserved donor rankings support OOD exploration but not automatic
      acquisition;
   6. outcome-unseen tests define abstention and the operational design rules.
4. **Limitations**: evidence level; model/representation envelope;
   retrospective-versus-prospective boundary; data and preregistration scope.
5. **Conclusions**: contribution, decisive evidence, practical rule, boundary.

## Locked terminology for the streamlined draft

| Canonical term | Use |
|---|---|
| knowledge borrowing | Umbrella method |
| donor and recipient | Directed task roles |
| donor-derived feature | Cross-fitted scalar used for prediction |
| target-model-independent donor ranking | Transfer object used for OOD exploration |
| borrowing edge | One directed donor→recipient test |
| improvement | Positive performance change under the stated comparison |
| OOD repair | Positive relative gain with positive absolute OOD utility |
| abstention | No borrowing when endpoint-specific gates fail |
| outcome-unseen | Target outcomes were not inspected during design, but already existed |
| prospective | Outcomes did not yet exist or were generated after the frozen design |

## Remaining claim upgrade

The streamlined paper already supports a bounded claim about **neighboring
experimental information**: a state-matched cross-property donor improves
chemically held-out prediction within one alloy resource, an adjacent
experimental condition improves few-shot prediction, and cross-database donor
rankings improve retrospective OOD exploration. It does not yet contain a
fully gated, outcome-unseen example in which a donor from one database improves
the absolute OOD predictive accuracy of a recipient in another database.

That distinction determines the only high-priority new experiment. If the
paper claims that neighboring *databases* improve OOD prediction, freeze the
state-matched borrowing contract on a new state-resolved recipient before its
outcomes are inspected. Use group-disjoint OOD splits, an
architecture-matched shuffled donor, a physically wrong donor, and positive
absolute OOD utility. BIRDSHOT can be used for development because it retains
campaign, grain-size, holding-time, and cold-work metadata, but its outcomes
have already been inspected in this project and it cannot supply independent
confirmation. A genuinely uninspected mechanical, perovskite, or battery
programme is required for that upgrade.

A smaller, SI-level reanalysis should ablate the state blocks (processing/phase,
test mode, temperature, and density) under the same elemental-system split.
This would show which alignment step is responsible for the gain without
creating another headline result. A prospective laboratory campaign is needed
only if the paper is upgraded from predictive knowledge borrowing to discovery
acceleration or new-science validation.
