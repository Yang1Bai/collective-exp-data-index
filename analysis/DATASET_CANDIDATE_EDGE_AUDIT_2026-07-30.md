# Audit of newly supplied experimental datasets

## Decision

The added folder contains one scientifically useful transfer structure, not a
large collection of interchangeable electrocatalysis donors. The useful
structure is the SpecGen OER perturbation series: one 462-catalyst donor,
four complete 126-catalyst derivative systems, target-available spectra and
compositions, a common electrochemical endpoint, and later synthesized
candidate sets. It is retained as a controlled system-held-out mechanism test.

The other nominally adjacent electrocatalysis pairs are rejected before
recipient-outcome fitting because their common representation or chemical
support is insufficient.

## Candidate-edge decisions

| Donor → recipient | Structural evidence | Decision |
|---|---|---|
| SpecGen original OER → four derivative OER systems | Same endpoint and robotic protocol; complete ligand or one-metal perturbations; 462 donor and 4 × 126 recipients | Retain. Composition-relation transfer is positive for B and D, ranking-only for A, and harmful for C. |
| Alkaline HER literature → Runze OER | The broad HER set has grouped OOF Spearman 0.462, but the strict Co–Cu–Fe–Mn–Ni subset has only 20 rows from 9 references and Spearman −0.386 | Reject. The apparent donor skill disappears in the recipient-supported chemistry. |
| Alkaline HER literature → senary high-entropy OER | Cd is absent and Mg/Zn are rare in the HER source; none of the 462 recipient compositions is fully supported | Reject. Cross-reaction adjacency does not repair element-support failure. |
| Senary high-entropy OER → Runze OER | 68 Runze rows use only Co/Ni/Cu/Zn, but only 9 unique compositions remain; donor compositions contain all six metals and donor-space nearest-neighbour distances are far outside the source's own 95% range | Reject as a confirmatory edge. It would be extrapolation from an interior senary simplex to pure and binary corners. |
| Ru-host sol–gel OER → Runze OER | Nearly every activity-labelled source sample contains Ru, which is absent from Runze | Reject. The nominally shared dopants are confounded with a missing host. |
| Formate oxidation → OER | Only Cu is shared between the octonary formate system and the senary OER system | Reject. Reaction label similarity is not a common material representation. |
| Ru-host alkaline HER → Ru-host sol–gel OER | Only 12 strictly supported HER rows from 5 references remain | Reject. Too small for a grouped source-skill gate. |
| Polymer optical properties → photocatalytic HER | Optical and HER measurements are attached to the same polymer campaign and were already represented in the optical-transfer development programme | Do not count as an independent cross-database edge. |
| OER activity → OER stability within the sol–gel file | Same samples and campaign, with substantial missingness across endpoints | Potential supplementary multi-endpoint test only; it does not strengthen the central cross-resource claim. |

## Retained SpecGen result

The donor composition model has five-fold OOF \(R^2=0.774\) and Spearman
\(\rho=0.887\). With no recipient labels, A, B and D have rank correlations of
0.552, 0.610 and 0.748; all exceed 500 refitted shuffled-source controls after
Holm correction. With five anchors:

- B: pooled RMSE gain 16.3% (95% candidate-bootstrap interval 9.2–22.9%);
  pooled Spearman gain 0.347 (0.260–0.426).
- D: pooled RMSE gain 26.1% (20.0–31.7%); pooled Spearman gain 0.407
  (0.352–0.459).
- A: pooled RMSE gain 3.2% with an interval crossing zero; retain as
  ranking-only.
- C: pooled RMSE gain −10.4% (−17.2 to −3.4%); reject.

On the subsequently synthesized 20-candidate sets, unchanged ranks remain
significant for B, C and D after Holm correction. These candidates were
selected by the source study's workflow, so this is temporal corroboration of
ordering, not prospective or unbiased discovery acceleration.

## Manuscript consequence

Use the perturbation series as the controlled method demonstration:

1. complete-system OOD rather than random row holdout;
2. a declared homologous relation rather than generic feature injection;
3. a few recipient anchors for local residual correction;
4. matched target-only and shuffled-source controls;
5. separate prediction and ranking gates;
6. mandatory abstention on C.

Retain SolventSeg as the more distant cross-database rank-transfer case and
FINALES as its frozen programme boundary. Do not add the rejected local pairs
to the main narrative merely to increase dataset count.
