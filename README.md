# Collective Experimental Data Index

> **Research release (31 July 2026).** Start with the
> [organized project package](research/README.md). It separates the latest
> manuscript, main-text evidence, supplementary and negative results, analysed
> database access records, Edison/Kosmos reports, and reproducibility assets.
> The current 127-resource discovery catalog is an index, not a claim that all
> 127 resources entered the paper. Third-party raw data are linked rather than
> relicensed or re-hosted.

**Current manuscript:**
[`analysis/MANUSCRIPT_DRAFT_STREAMLINED.md`](analysis/MANUSCRIPT_DRAFT_STREAMLINED.md)
| **Supplement:**
[`analysis/SUPPLEMENTARY_INFORMATION.md`](analysis/SUPPLEMENTARY_INFORMATION.md)
| **Paper package:**
[`analysis/PAPER_PACKAGE.md`](analysis/PAPER_PACKAGE.md)
| **Edison reports:**
[`analysis/review_packages/edison/README.md`](analysis/review_packages/edison/README.md)
| **All tested edges:**
[`research/evidence/ATTEMPT_LEDGER.csv`](research/evidence/ATTEMPT_LEDGER.csv)

An artifact-gated neighborhood-borrowing strategy for strengthening few-shot
prediction and OOD exploration, supported by an experimental-first metadata
index and pinned integration workflow. Reported measurements are retained with
identity, conditions, provenance, and reuse constraints rather than treated as
context-free labels. The repository does not assume that every indexed resource
is openly licensed, experimentally complete, or immediately interoperable.

## Scientific question

When target-domain evidence is sparse in few-shot and OOD regions, can
neighboring experimental domains supply missing knowledge without reproducing a
data-only illusion? The evidence here says yes—but only selectively and only
when experimental context is preserved and the borrowing mechanism survives
attempts to falsify it. The
strategy qualifies sources under leakage and wrong-source controls, matches
soft-prior injection to prediction, keeps source rankings separate for OOD
exploration, and combines complementary neighbors as a safe shortlist
portfolio.

The evidence contains one material within-campaign few-shot improvement. A
−20 °C liquid-electrolyte conductivity model reduces error at −30 °C, with a point
estimate of 37% equivalent target labels saved, decays with temperature distance,
and fails under source scrambling. The effect is not automatically portable:
a separately frozen CALiSol test that holds out entire source articles gives
only +1.61% [−2.14%,+4.21%], negative absolute R², and no distance ordering.
BIRDSHOT gives directional cross-dataset error reduction without absolute
utility, Matbench is an independent null, many candidate edges are harmful, and the
pre-existing 0–3 cross-domain distance score is not established.

A systematic benchmark across eight targets then tests the stronger OOD-repair
claim. Among 40 real donor–recipient edges, alloy UTS→YS gives the strongest
designated OOD error reduction (+6.65% [3.53,14.02%]), but improves
in-distribution error slightly more and retains negative OOD R². No designated
edge passes the complete OOD-repair gate; the seven-programme mean is +0.92%
[−0.35,2.92%]. Generic donor-feature injection is therefore insufficient for
OOD repair, even when it transfers useful correlation.

An independently frozen Caltech ionic-conductor benchmark shows why policy
design matters. Prespecified OBELiX and ESTM rankings recover 2/8 and 3/8
external top-5% entities after exact composition and DOI exclusions, while
mechanical and catalysis controls recover 0/8. A post-outcome neighbor portfolio
recovers 5/8 externally and 3/3 in hard OOD, demonstrating complementary source
proposals. A CCA family-first allocation then recovers all 4/4 distinct top
external formula/DOI/ICSD components and both 2/2 hard-OOD components by
acquisition 20, while deliberately reducing repeated within-component entity
hits. In contrast, every target-refitted adaptive source increment fails.

The Caltech-derived strategy was then frozen on two outcome-unseen programmes.
Ionic-to-thermoelectric borrowing on Starrydata gives a small +0.88%
[0.02,1.77%] far-OOD effect but fails Holm multiplicity (p=0.071), source
specificity, and absolute utility (R²=-0.485). Multi-neighbor borrowing across
four TRI OER plates gives -0.079% [-0.313,0.155%] and negative absolute R² on
every plate. Their random-effects mean is +0.304% [-0.617,1.225%], I²=76.7%.
Neither target passes its complete gate. The formal result is therefore a
selective map with abstention, not a general transfer law.

Together, these results instantiate a selective knowledge-borrowing map over
the tested relations. The KIT edge shows that neighboring evidence can deliver
a material few-shot gain; Caltech shows that neighboring domains can generate
complementary OOD proposals; and the null, harmful, and endpoint-changing edges
show where the same idea should be rejected or redesigned. “Map” here means an
auditable decision object, not a universal distance law or a guarantee for
untested datasets.

The current paper-facing files are
[`analysis/MANUSCRIPT_DRAFT_STREAMLINED.md`](analysis/MANUSCRIPT_DRAFT_STREAMLINED.md),
[`analysis/SUPPLEMENTARY_INFORMATION.md`](analysis/SUPPLEMENTARY_INFORMATION.md),
the executable strategy specification
[`analysis/SELECTIVE_NEIGHBOR_BORROWING_STRATEGY.md`](analysis/SELECTIVE_NEIGHBOR_BORROWING_STRATEGY.md),
the outcome-unseen validation protocol
[`analysis/CCA_FAMILY_FIRST_PROTOCOL.md`](analysis/CCA_FAMILY_FIRST_PROTOCOL.md),
the data-foundation and evidence-scope figure
[`analysis/figures/data_foundation_scope.svg`](analysis/figures/data_foundation_scope.svg),
the editable knowledge-map figure
[`analysis/figures/main_knowledge_borrowing.svg`](analysis/figures/main_knowledge_borrowing.svg),
the systematic multi-target OOD figure
[`analysis/figures/multi_target_ood_borrowing.svg`](analysis/figures/multi_target_ood_borrowing.svg),
and the OOD decision-endpoint figure
[`analysis/figures/ood_decision_borrowing.svg`](analysis/figures/ood_decision_borrowing.svg),
plus the combined knowledge-borrowing map and exploration figure
[`analysis/figures/neighbor_map_exploration.svg`](analysis/figures/neighbor_map_exploration.svg),
plus the outcome-unseen validation figure
[`analysis/figures/outcome_unseen_validation.svg`](analysis/figures/outcome_unseen_validation.svg),
and the temporal battery strategy figure
[`analysis/figures/battery_continuous_borrowing.svg`](analysis/figures/battery_continuous_borrowing.svg).

## Repository snapshot

As of 31 July 2026, the catalog contains **127 resources with experimental
content**:

- 98 experimental and 29 mixed experimental/computational resources;
- 118 open-access, 5 registration-gated, and 4 restricted resources;
- 22 records with an unresolved (`Unknown`) data license;
- a source/evidence URL for every record, without implying current
  availability, reuse rights, or independent scientific validation.

The catalog links to authoritative sources and does not re-host their files.
See [CATALOG.md](CATALOG.md), [catalog/catalog.csv](catalog/catalog.csv), and
[catalog/catalog.json](catalog/catalog.json).

## Local integrated snapshot

[`scripts/localdb/build_localdb.py`](scripts/localdb/build_localdb.py) builds a
local SQLite snapshot from commits pinned in
[`scripts/localdb/sources.lock.json`](scripts/localdb/sources.lock.json). The
current build registers 14 sources (13 normalized and NIST ISODB analysis-only)
and contains **96,184 measurements, 230 property labels, and 29,516 canonical
formula, molecule, or mixture entities**. Each measurement records:

`dataset · source row · raw material · canonical entity · property · value · unit · conditions JSON · reference · source commit · quality flags`

NIST ISODB is analyzed directly from a hash-verified commit archive because its
adsorbent identifiers do not fit the formula/SMILES entity schema and one
historical path is invalid on Windows. The isosteric workflow streams 54,253
JSON files without extracting them and produces one matched-loading fit per
eligible adsorbent–adsorbate system.

## Main results

1. **A strong source calibration fails to travel.** Same-record Borg UTS–yield-strength
   pairs give log–log R²=0.790. BIRDSHOT gives R²=0.067, and the Borg line
   evaluated unchanged on BIRDSHOT gives R²=−3.006. Composition-cluster
   bootstrap places the Borg-minus-BIRDSHOT slope difference at 0.510–0.854
   (95% interval); exact composition overlap is zero.
2. **One neighboring-task borrowing edge is an internally selected candidate.** With 30
   target observations, the Borg UTS prediction feature reduces held-out Borg
   yield-strength RMSE by 6.46% [3.69%,13.03%]. A uniform 999-permutation
   refinement over all five discovery-selected edges gives Holm p=0.005. Mean
   R² moves from −0.149 to +0.025, and the monotone target-only learning curve
   corresponds to 73.4% target-equivalent samples saved.
3. **The direction replicates independently but misses the frozen practical
   gate.** In BIRDSHOT rolling-time tests (Year 1→2 and Years 1–2→3), the same
   Borg UTS feature reduces RMSE by 4.30% [3.36%,5.51%], with both folds
   positive, within-year feature permutation p=0.003, and all three learners
   positive. It remains below the predeclared 5% external threshold and is
   labelled `directionally-replicated-below-practical-gate`, not externally
   confirmed. The temporal learning curve is nonmonotone, so no external
   sample-saving number is claimed. A post hoc process-aware model including
   cold work, holding time and grain size retains a 5.23% [3.74%,7.03%]
   reduction, so the signal is not explained by those omitted variables.
   However, rolling-time pooled R² remains negative (−1.216 to −0.992): this is
   robust error reduction, not demonstrated practical rescue.
4. **Independent mechanical adjacency is not sufficient.** On the official
   five Matbench steel folds, Borg UTS→steel yield strength gives −1.23%
   [−15.88%,2.48%], mapping-permutation p=0.794, and five negative fold means.
   Tree sensitivities are below 1%, far short of the 5% practical gate.
5. **A local neighbor materially improves KIT few-shot performance.** In the KIT electrolyte
   campaign, formulations rather than EIS runs are the independent units. A
   −20 °C prior reduces n=30 target RMSE at −30 °C by 15.02%
   [8.61%,21.10%], p=0.001, and improves pooled R² from 0.739 to 0.811. All five
   formulation folds and three learners are positive. The augmented error is
   equivalent to 47.884 target-only labels, or 37.35% saved. A post-outcome
   formulation/subset bootstrap spans 21.84–49.91%, so the direction of the
   sample-efficiency gain is supported but its magnitude relative to the frozen
   30% point threshold is uncertain.
6. **The KIT improvement fails to transport across experimental articles.** CALiSol-23
   aggregates 13,825 measurements from 27 publications. A separately frozen
   −30→−40 °C test holds out all formulations from each target article, removes
   exact held-out chemistry identities from source fits, and hierarchically
   resamples articles. At n=30, RMSE changes by only +1.61%
   [−2.14%,+4.21%]; pooled R² remains negative (−0.049→−0.014), two of five
   article folds are harmful, estimated label savings are 16.9%, and the
   distance controls are not ordered. A p=0.004 result on the single fixed
   permutation subset does not override the failed repeated-effect,
   practical, absolute-utility, fold, saving, and adjacency gates.
7. **Borrowing is physically selective.** Frozen KIT temperature-distance effects
   are 15.02%, 5.01%, 0.95%, and −0.76% at ΔT=10, 30, 60, and 90 °C; a shuffled
   adjacent source is harmful (−2.96% [−4.32%,−1.44%]). The internal
   non-calibration map contains 42 directed edges and BIRDSHOT adds 15. Internal edge
   heterogeneity is strong (Cochran Q p=0.00036); eight external edges are
   harmful and two practically equivalent. A post-map direct-neighbor versus
   distant-control contrast favors neighbors in 9/12 targets (one-sided
   Wilcoxon p=0.046), but is leave-one-target-out fragile. The original ordinal
   0–3 score is not established (Spearman p=0.113).
8. **Generic donor-feature injection does not constitute OOD repair.** The
   systematic benchmark retains 40 real edges across eight targets, three
   learners, wrong and shuffled controls, and outcome-free Q1/Q4 groups. The
   strongest designated edge, alloy UTS→YS, lowers OOD RMSE by 6.65%
   [3.53,14.02%] but lowers ID RMSE by 7.74% and retains augmented OOD
   R²=−0.666. No designated edge passes the complete gate; the seven-programme
   mean is +0.92% [−0.35,2.92%], and 0/3 cross-database edges pass.
9. **Artifact gates change the meaning of pooled regularities.** Reference-
   separated thermoelectric Arrhenius series show only a weak Meyer–Neldel
   association (n=112, R²=0.107). ISODB instead shows a strong pooled isosteric
   heat–intercept relation (n=1,103, R²=0.637) that is not reproduced by the
   independent-parameter Krug null and whose T_iso=513 K is far from the median
   harmonic temperature of 301 K. It must not be discarded as a simple Krug
   artifact; however, DOI-clustered family intercept shifts are required
   (wild-cluster p=0.0002), so one unconditional line is still inadequate.
10. **OOD screening does not become sequential discovery for the tested policy.** A frozen
   fixed-ranking OBELiX test gives a directional 2.09 percentage-point reduction
   [0.94,3.46] in the pool fraction inspected before the first top-5% hit, but
   fails the practical and repeat-consistency gates. The sequential design was
   prespecified after this fixed-ranking direction was known and is not an
   independent confirmation. In the completed 100-seed sequential test,
   target-only and thermoelectric-prior RF-UCB require 24.34
   and 24.09 acquisitions: only 0.25 saved [−1.30,1.82], p=0.3889. Uniform
   random acquisition is substantially faster than either UCB policy, locating
   the failure at the tested policy level without identifying its cause.
11. **Family-first borrowing broadens OOD exploration.** The eight external
   top entities collapse to four connected formula/DOI/ICSD components. CCA
   family-first consensus raises distinct-component AUC20 from 47 to 60 and
   recovers 4/4 external top components; in hard OOD it ranks both 2/2 top
   components first and second. Wrong-source AUC20 is 6/18 and 5,000 shuffled-
   rank pairs give conditional p=0.0020/0.0030. Entity recall falls because
   repeated members of one component are deferred: this is a distinct-region
   discovery gain, not a claim that every ML metric improves.
12. **Outcome-unseen tests reject general transfer while preserving edge
    selectivity.** Starrydata ionic→thermoelectric borrowing gives +0.88%
    [0.02,1.77%], but Holm p=0.071 and R²=-0.485; its CCA policy trails the
    same-domain ESTM reference and all three hypothesis cards fail. Across four
    TRI OER plates, all-neighbor borrowing gives -0.079% [-0.313,0.155%], every
    absolute R² is negative, and no policy or card is confirmed. The pooled
    effect is +0.304% [-0.617,1.225%] with I²=76.7%. This is the evidence that
    borrowing is sparse, directed, representation-sensitive, and endpoint-
    specific.
13. **Previously attractive claims remain withdrawn.** The designated
   thermoelectric→OBELiX ridge result is negative/model-dependent, the organic
   FreeSolv→AqSolDB effect is practically small, and no OBELiX
   OOD-discovery-improvement or rescue claim passes its frozen gates.

The defensible conclusion is not that all global regularities are false. It is
that pooled correlation, coefficient transport, predictive borrowing, and OOD
proposal generation are different claims and require different validation
gates. The present data show a material KIT few-shot improvement, selective
transferable correlations that do not meet OOD-repair criteria, selective
external Caltech OOD rankings, and complementary neighbor proposals whose
diagnostic portfolio covers 5/8 top entities versus 2/8 and 3/8 individually.
CCA family-first allocation additionally covers 4/4 distinct top external
components and 2/2 hard-OOD components, making broader OOD region discovery the
operational objective rather than average fit improvement. Outcome-unseen
Starrydata and TRI tests then show that the integrated strategy does not
automatically generalize: it abstains on one edge and rejects another.
Together these results provide component-level proof of a selective,
falsification-first neighborhood-borrowing strategy. The operational local-task-
rescue status remains restricted to its table definition, and prospective
acceleration or field-level rescue is not established.

## Reproduce

```bash
python -m venv .venv
# Windows: .venv\Scripts\python -m pip install -r analysis\requirements.txt
# POSIX:   .venv/bin/python -m pip install -r analysis/requirements.txt

python scripts/localdb/build_localdb.py
python analysis/audit_snapshot.py
python analysis/run_confirmatory.py
python analysis/run_knowledge_map.py
python analysis/refine_candidate_permutations.py
python analysis/run_external_confirmation.py
python analysis/run_external_sensitivities.py
python analysis/run_matbench_steels_confirmation.py
python analysis/run_kit_temperature_borrowing.py --jobs 8
python analysis/run_kit_sample_equivalence_uncertainty.py --jobs 8
python analysis/run_calisol_external_borrowing.py --jobs 8
python analysis/run_strength_law_external.py
python analysis/run_isodb_isosteric.py
python analysis/run_isodb_universality.py
python analysis/run_ood_decision_borrowing.py
python analysis/run_hard_ood_composition.py
python analysis/write_obelix_ood_discovery_input.py
python analysis/run_obelix_ood_discovery.py
python analysis/verify_obelix_ood_discovery_results.py
python analysis/analyze_obelix_ood_discovery_diagnostics.py
python analysis/synthesize_knowledge_map.py
python analysis/make_data_foundation_figure.py
python analysis/make_main_knowledge_map_figure.py
python analysis/make_ood_decision_figure.py
python analysis/make_caltech_external_policy_figure.py
python analysis/run_local_gated_neighbor_portfolio.py
python analysis/audit_family_first_neighbor_portfolio.py
python analysis/make_family_first_neighbor_portfolio_figure.py
python analysis/make_neighbor_map_exploration_figure.py
python analysis/make_outcome_unseen_validation_figure.py
python analysis/make_battery_continuous_borrowing_figure.py
python analysis/write_release_manifest.py
```

The six main figures are
[analysis/figures/data_foundation_scope.pdf](analysis/figures/data_foundation_scope.pdf),
[analysis/figures/main_knowledge_borrowing.pdf](analysis/figures/main_knowledge_borrowing.pdf),
[analysis/figures/ood_decision_borrowing.pdf](analysis/figures/ood_decision_borrowing.pdf),
[analysis/figures/neighbor_map_exploration.pdf](analysis/figures/neighbor_map_exploration.pdf),
[analysis/figures/outcome_unseen_validation.pdf](analysis/figures/outcome_unseen_validation.pdf),
and [analysis/figures/battery_continuous_borrowing.pdf](analysis/figures/battery_continuous_borrowing.pdf),
with editable SVG, 600 dpi TIFF, PNG, and panel-level source CSVs. Full methods,
evidence status, and machine-readable outputs are in
[analysis/README.md](analysis/README.md),
[analysis/PAPER_PACKAGE.md](analysis/PAPER_PACKAGE.md),
[analysis/SUPPLEMENTARY_INFORMATION.md](analysis/SUPPLEMENTARY_INFORMATION.md),
and [analysis/results](analysis/results).

## Catalog policy

Purely computational resources are excluded at build time and retained in
[`catalog/excluded_computational.json`](catalog/excluded_computational.json).
Mixed resources remain when they contain a meaningful experimental component.
Automated discoveries remain candidates until human review; unknown licenses
stay visible rather than being silently treated as open.

## Repository layout

```text
catalog/                    machine-readable catalog and schema
scripts/                    discovery, export, validation, and pinned integration
analysis/                   protocols, analyses, figures, and result tables
analysis/results/           machine-readable evidence and source data
docs/methodology.md         sourcing, verification, and licensing policy
tests/                      identity, leakage, schema, and analysis smoke tests
```

## Validation and licensing

```bash
python scripts/validate_catalog.py
python analysis/audit_snapshot.py
python -m unittest discover -s tests -v
```

- Code: MIT; see [LICENSE](LICENSE).
- Catalog metadata authored here: CC-BY-4.0; see
  [LICENSE-DATA.md](LICENSE-DATA.md).
- Source datasets retain their own licenses and access terms.
