# Streamlined manuscript QA and remaining evidence gap

## Editorial status

- Main-text draft: `MANUSCRIPT_DRAFT_STREAMLINED.md`
- Scope: methods-led full paper for *Digital Discovery*
- Main-text length: approximately 6,362 words including captions and
  end-matter
- Abstract: 229 words
- Main figures: five
- Referenced bibliography keys: 27; all are present in `REFERENCES.bib`
- Main-text result policy: retain only results that establish data breadth,
  falsify unsafe aggregation, demonstrate a qualified positive edge, separate
  prediction from exploration, or define abstention

The draft no longer narrates the full project history. Job identifiers,
verifier chronology, outcome-guided method searches, complete gate lists,
programme-level diagnostics, and unused hypothesis cards are assigned to the
Supplementary Information or excluded from the submission narrative.

## Main evidence chain

| Question | Main-text evidence | Decision |
|---|---|---|
| Is the study broad enough to test transfer beyond one narrow domain? | 20 analysed resources; 13-resource normalized core with 96,184 measurements, 230 property labels, and 29,516 canonical entities | Retain in Fig. 1 and state once in the text |
| Does a strong pooled relation automatically transport? | Borg UTS–YS \(R^2=0.790\), but unchanged Borg→BIRDSHOT \(R^2=-3.006\); thermoelectric and ISODB compensation tests | No; pooled association, artifact resistance, and transport are separate claims |
| Can a qualified neighbor help a data-poor task? | KIT −20→−30 °C: 15.02% RMSE reduction, 95% CI 8.61–21.10%, \(p=0.001\) | Yes, within one controlled campaign |
| Does the same absolute-transfer method automatically cross articles or programmes? | CALiSol 1.61% with interval crossing zero; Matbench −1.23% | No; nominal adjacency is insufficient |
| Can the CALiSol provenance boundary be repaired by changing the transferred object? | Post-outcome contrast transfer plus one target-article anchor: 6.91% macro-RMSE gain over the same-anchor absolute donor, [0.88,14.00%], exact \(p=0.035\), shuffled \(p=0.005\), pooled \(R^2=0.234\) | Yes for this method-development programme; unchanged external replication required |
| Does generic donor-feature injection repair OOD prediction? | Forty real edges across eight targets; no designated edge passes the complete OOD-repair gate | No |
| Can alignment make a failed OOD edge useful? | State-aware target features improve Q4 RMSE by 8.25%; predicted UTS then adds a further 9.21% over the state-aware target-only model; real-minus-shuffle 9.47 percentage points; pooled augmented Q4 \(R^2=0.103\) | Yes, on the selected MPEA programme |
| Does predictive gain imply search acceleration? | OBELiX fixed screening is directional, while target-refitted sequential UCB is null | No |
| Can cross-database information still guide OOD exploration? | On Caltech, preserved OBELiX and ESTM rankings recover complementary top candidates and outperform random AUC20 | Yes, retrospectively as an independent ranking object |
| Are positive cases defining the map after the fact? | Outcome-unseen Starrydata and TRI targets fail their complete gates | The strategy must retain abstention |

## Numerical traceability

| Claim block | Primary checked source |
|---|---|
| Data-cohort counts | `DATA_FOUNDATION_FIGURE_QA.md`; `make_data_foundation_figure.py` |
| KIT and original CALiSol absolute transfer | `results/kit_temperature_summary.json`; `results/calisol_external_summary.json` |
| CALiSol anchored contrast transfer | `results/calisol_anchored_delta_summary.json`; `results/calisol_anchored_delta_verified.json`; `CALISOL_ANCHORED_DELTA_TRANSFER_FINDINGS.md` |
| Matbench boundary | `results/matbench_steels_external_summary.json` |
| Systematic OOD benchmark | `results/multi_target_ood_summary.json`; `results/multi_target_ood_edge_summary.csv` |
| State-matched MPEA | `results/state_matched_mpea_balam_v2_VERIFIED.json`; `results/state_matched_mpea_balam_v2_bootstrap_summary.json`; `results/state_matched_mpea_figure_source_data.csv` |
| OBELiX screening and acquisition | `results/ood_decision_summary.json`; `results/obelix_ood_discovery_summary.json` |
| Caltech rankings | `results/caltech_ionic_external_policy_summary.json`; `results/figure_caltech_policy_panel_c.csv` |
| Outcome-unseen boundary | `results/figure_outcome_unseen_panel_a.csv`; `results/outcome_unseen_multi_target_summary.json` |

## What is still missing

### 1. External cross-database OOD-prediction replication

**Priority:** claim-critical only if the title, abstract, or conclusion states
that one experimental database improves the OOD predictive accuracy of another.

The strongest positive OOD-prediction results currently use neighboring
endpoints or conditions within one resource. CALiSol now crosses complete
article boundaries with one target-article anchor, but it is a post-outcome
few-shot reanalysis rather than an independent database replication. The
Caltech result is cross-database but
supports OOD ranking, not improved global or Q4 predictive calibration.
Therefore the current evidence supports “neighboring experimental information
can improve OOD prediction” and “cross-database rankings can guide OOD
exploration.” It does not yet support the stronger combined claim that
cross-database borrowing has passed the complete OOD-prediction gate.

**Minimal test:** freeze the current state-matched contract on one genuinely
uninspected, state-resolved recipient. Require group-disjoint Q4 evaluation,
positive absolute Q4 \(R^2\), an architecture-matched shuffled donor, a
physically wrong donor, and a practical effect threshold. BIRDSHOT is useful
for method development because its local snapshot retains campaign year,
grain size, holding time, and cold-work metadata, but its outcomes have already
been inspected. Independent confirmation needs a new mechanical, perovskite,
or battery programme.

**Cost:** new accessible data plus moderate compute.

### 2. State-block ablation

**Priority:** recommended for the Supplementary Information.

The current staged comparison already separates composition, reported state,
predicted UTS, shuffled UTS, and measured-UTS ceiling. Add a leave-one-block-out
analysis for processing/phase, test mode, temperature, and density under the
same elemental-system split. This will make the method more transferable to
other researchers by showing which metadata alignment is essential.

**Cost:** reanalysis only; no new data.

### 3. Prospective candidate testing

**Priority:** unnecessary for the present bounded methods paper; required for a
future discovery-acceleration or “new science” claim.

Freeze a donor-ranked shortlist before outcomes exist, test the candidates
experimentally, and compare hit rate or regret with target-only and random
selection. Retrospective acquisition simulations cannot replace this test.

**Cost:** new experiments and substantially more time.

## Submission decision

The streamlined manuscript is coherent enough for a bounded *Digital
Discovery* methods paper after the state-block ablation is added to the
Supplementary Information. Do not restore the battery, CCA, full policy-search,
or hypothesis-card results to the main text. If the intended headline remains
the stronger cross-database OOD-prediction claim, complete one frozen external
state-resolved replication before submission; otherwise retain the current
precise distinction between predictive borrowing and cross-database OOD
exploration.
