# Catalog-to-paper opportunity audit

**Snapshot date:** 2026-07-20  
**Remote catalog snapshot:** 233 records, `catalog/catalog.csv` SHA `75583d412075f542f1903ca766033f4012ad4ef9`  
**Current analysis snapshot:** 118 catalog records  
**Decision:** keep the 118-record curated snapshot as the manuscript denominator. Use the expanded catalog to select and preregister the next target, not as an already validated 233-database scientific result.

## Executive decision

The catalog contains one high-value confirmatory candidate and two high-value developmental stress tests.

1. **Multi-stage lithium-ion battery ageing is the best next CCA-v2 target.** It supplies a genuinely temporal, staged programme with explicit temperature, SOC, DOD, charge/discharge-rate, cell, and laboratory metadata. Stage 1 and the external battery programmes can provide neighbouring evidence; Stage 2 can be frozen as the OOD target before raw outcomes are downloaded. This is the cleanest way to test whether candidate-local applicability improves an unseen programme rather than another random split.
2. **Perovskite stability is the best mechanistic stress test.** The MIT programme reports weak high/low-temperature stability correlations and a reversal in cation effects across temperature. That is a natural falsifier for naive adjacency and a direct demonstration of why condition-aware local gating is necessary. Because the published outcome behaviour has now been inspected, it cannot serve as independent confirmation.
3. **Reaction HTE to AstraZeneca ELN is the best organic-chemistry challenge.** It is structured, open, modest in size, and already known to defeat ordinary same-reaction HTE pretraining. A CCA-v2 analysis would therefore test whether local support, shrinkage, and abstention can recover useful subregions where global transfer failed. It is method development, not an outcome-unseen confirmation.

The full shortlist is recorded in `results/catalog_transfer_readiness_shortlist.csv`.

## Why the multi-stage battery target has the highest confirmatory value

The Scientific Data record describes a two-stage experimental design conducted over approximately one year per stage. It exposes condition variables and cell-level metadata, provides CSV measurements and per-file metadata, and separates calendar and cycle ageing. These are exactly the variables missing from the current global CCA gate: candidate-local support, condition compatibility, temporal provenance, and a defensible programme-level evaluation unit.

A target-specific freeze should define:

- target: Stage 2 cells and prespecified degradation endpoint(s);
- source set: Stage 1 plus selected BatteryArchive/NASA/CALCE/Oxford/TRI programmes, with no cell or time leakage;
- OOD groups: held-out temperature/SOC/DOD/rate combinations and cell groups;
- target-only comparator: the identical learner without source features or source ranks;
- adjacency-only comparator: fixed physical-neighbour rule without local applicability;
- CCA-v2: source support distance, grouped uncertainty, target-support distance, condition compatibility, and source agreement/disagreement;
- wrong controls: size/coverage-matched non-ageing or mismatched-chemistry sources and shuffled source outcomes;
- primary unit: experimental programme or condition block, never seed;
- endpoints: prediction, fixed screening, and scientific-inspiration cards analysed separately;
- stop rule: no adaptive acquisition claim unless the target-only policy first beats uniform random.

This experiment would not by itself prove a universal transfer policy. It would provide the first temporal, raw-outcome-unseen test of the frozen CCA-v2 architecture and can become the independent positive example the current paper lacks if both efficacy contrasts, safety, and coverage pass.

## Perovskite: use the reversal, not a generic positive-transfer claim

The perovskite family is unusually well suited to the paper's conceptual argument. The Perovskite Database contains more than 42,400 devices with device-stack, processing, performance, stability, and DOI provenance fields. The MIT robotic programme contains more than 1,400 samples across composition, deposition method, illumination, humidity, and ageing temperature. Its reported high/low-temperature correlations are weak, and the sign of the cation-stability relation reverses below approximately 100 degrees C.

The correct paper use is therefore a **known-mechanism falsification benchmark**:

- naive high-temperature-to-low-temperature transfer should be allowed to fail;
- adjacency-only should be compared with a condition-aware gate;
- the gate succeeds if it abstains from unsupported extrapolation or restricts borrowing to locally compatible regimes;
- any source-derived composition hypothesis must specify the temperature range and a crossover falsifier.

The HZB ageing archive is open and contains 2,245 MPPT efficiency traces. Direct inspection of its pickle structure found time and MPPT-efficiency traces but no obvious companion device-covariate table. It is therefore not yet a model-ready target for candidate-local transfer unless those traces can be linked to device stack, composition, and test-condition metadata.

## Reaction HTE/ELN: a sharp test of whether the new strategy is actually better

The catalog connects three unusually informative reaction datasets: a 3,960-combination Buchwald-Hartwig HTE design, a Suzuki-Miyaura HTE design, and a sparse 781-reaction AstraZeneca ELN set covering a much wider chemical space. The Chemical Science source paper reports that ordinary pretraining on the same-reaction HTE data followed by ELN fine-tuning produced negative or near-zero R2. That prior null prevents a novelty claim for generic transfer but creates a strong challenge for CCA-v2.

The useful question is not whether a larger neural network can transfer. It is whether outcome-free local support and abstention can identify the small subset of ELN reactions for which focused HTE evidence is applicable. A defensible analysis would use reaction fingerprints and condition features; scaffold/reagent/provenance groups; cross-fitted source uncertainty; same-reaction and adjacent-reaction sources; and shuffled plus matched wrong-reaction controls. Report coverage and negative-transfer avoidance even if the mean effect is null.

## Catalog quality gate: the 233-record headline is not manuscript-ready

The remote catalog contains 115 records from the July 2026 `api-discovery-tdm` harvest. A deterministic metadata audit found:

| Audit flag in TDM cohort | Count | Fraction of 115 |
|---|---:|---:|
| Missing tags | 115 | 100.0% |
| Exact-title duplicate members | 55 | 47.8% |
| Raw/support/metadata-like record wording | 40 | 34.8% |
| Marked experimental but computational/simulation wording present | 16 | 13.9% |
| Obvious out-of-scope biomedical/ecological/astronomical wording | 12 | 10.4% |

Flags overlap and are triage indicators, not final exclusion decisions. Nevertheless, they show that the TDM cohort is a discovery queue rather than a curated database count. Examples include simulated adsorption isotherms marked experimental, FEFF-computed spectra marked experimental, diabetic-foot imaging classified as catalysis, and exact-title Zenodo concept/version duplicates.

There is also a validation inconsistency. The remote CSV uses `api-discovery-tdm` for all 115 new records, while `catalog/schema.json` does not allow that value. The stdlib validator checks enums for domain, data type, and access but not for `source`, so the catalog can pass the advertised lightweight validation despite violating its schema.

Required fixes before claiming 233 curated databases:

1. quarantine the 115 TDM records as candidates until human review;
2. deduplicate concept/version records using DOI concept identifiers plus normalized title;
3. correct data type and subdomain with a human-reviewed exclusion reason;
4. add `api-discovery-tdm` to the schema only if it remains a supported provenance class;
5. make the lightweight validator enforce every schema enum, especially `source`;
6. distinguish a database, a dataset, a raw source-data package, and a metadata-only record;
7. add transfer-readiness enrichment without contaminating the base metadata schema.

## Transfer-readiness enrichment needed for this paper

The current schema is sufficient for discovery but cannot support outcome-blind target selection. Add a separately generated enrichment table with:

- entity grain and canonical identifier type;
- number of entities, measurements, programmes, and outcome-bearing records;
- measured endpoints, units, and condition variables;
- file format, direct-download route, checksum, and approximate size;
- experimental batch, article, campaign, time, and replicate grouping fields;
- negative/failed outcome availability;
- candidate-pool and sequential-trajectory availability;
- source/target representation compatibility;
- outcome-access status and timestamp;
- eligible OOD axes;
- proposed physical relation, contraindication, and wrong-source family.

This layer turns the catalog from a list into a preregistration instrument: targets can be chosen from metadata before outcome access, and every rejected candidate remains auditable. It directly supports the paper's claim that artifact gatekeeping begins before modelling.

## Manuscript implications

- Retain **118** as the frozen, reviewed catalog snapshot used by the current analyses. State the snapshot hash/date.
- Describe the 115-record TDM expansion as an automated discovery queue, not 115 additional curated experimental databases.
- Add a supplement table showing target selection and rejection based only on transfer-readiness metadata.
- Use the catalog graph to nominate sources, adjacency-only baselines, and matched wrong-source controls; never use catalog proximity as evidence that transfer worked.
- Keep prediction, fixed OOD screening, breadth exploration, adaptive acquisition, and scientific inspiration as separate endpoints.
- Do not claim prospective discovery until a source-derived hypothesis card is written before the target measurement and survives its matched falsifier.

## Submission blockers exposed by the repository audit

1. **Repository availability:** the GitHub repository is currently private and its README explicitly labels it private-first. A manuscript calling it public is factually wrong until the repository is opened or an immutable archival release is deposited.
2. **Version drift:** the online main branch says 233 curated databases, while the analysis snapshot contains 118. The manuscript, supplement, release manifest, and repository landing page must identify which snapshot supports each number.
3. **Validation drift:** schema and lightweight validation disagree about the new provenance class.
4. **Over-counting risk:** raw source-data packages and version duplicates must not be counted as independent databases.

## Recommended next move

Do not add five more retrospective demonstrations. Perform two bounded actions:

1. **Data/infrastructure:** repair the catalog gate, freeze the 118-record manuscript release, and publish/archive it.
2. **Science:** write and hash one target-specific CCA-v2 appendix for the multi-stage battery ageing dataset before downloading its raw outcome files. Treat perovskite reversal and reaction HTE-to-ELN as developmental falsification benchmarks, not as independent confirmation.

That combination strengthens both halves of the paper: a trustworthy experimental-data foundation and one genuinely temporal test of whether qualified neighbouring knowledge improves OOD decisions.

## Sources

- Repository README, catalog, schema, and validator: `Yang1Bai/collective-exp-data-index`, remote main snapshot inspected 2026-07-20.
- Jacobsson et al., *Nature Energy* 7, 107-115 (2022), DOI 10.1038/s41560-021-00941-3.
- Zhao et al., *Nature Communications* 12, 2191 (2021), DOI 10.1038/s41467-021-22472-x.
- Hartono et al., Perovskite Solar Cells Ageing Dataset, Zenodo 10.5281/zenodo.8185883.
- Saebi et al., *Chemical Science* 14, 4997-5005 (2023), DOI 10.1039/D2SC06041H.
- Stroebl et al., *Scientific Data* 11, 1020 (2024), DOI 10.1038/s41597-024-03859-z; Figshare 10.6084/m9.figshare.25975315.v1.
