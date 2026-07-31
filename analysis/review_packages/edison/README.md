# Edison and Kosmos research package

This directory preserves the Edison-platform contribution as an auditable
research input rather than as an authority. Raw AI reports, prompts, task/run
metadata, local scientific assessments, independent recalculations, and the
final manuscript disposition are kept separately.

## Report inventory

| Run or package | Purpose | Raw output | Local audit or integration | Final disposition |
|---|---|---|---|---|
| Edison Literature (High) | Broad literature review and proposed experimental OOD transfer cases | [`raw_exports/Edison_Literature_High_report.pdf`](raw_exports/Edison_Literature_High_report.pdf) | The 23-page report was reviewed as a literature/hypothesis source | Ideas only; no numerical claim enters the paper without repository validation |
| Edison task `7BDBBC46` | Scientific audit of the early project framing | Preserved in the dated integration package | [`../EDISON_7BDBBC46_AUDITED_INTEGRATION_2026-07-29.md`](../EDISON_7BDBBC46_AUDITED_INTEGRATION_2026-07-29.md) | Helped shift the transfer object from generic features toward relations, corrections, parameters, and endpoint routing |
| Edison task `F0A9CE` | Clean-sheet research/hypothesis development | [`../EDISON_F0A9CE_FULL_REPORT.md`](../EDISON_F0A9CE_FULL_REPORT.md) | [`../EDISON_F0A9CE_INTEGRATION_NOTES.md`](../EDISON_F0A9CE_INTEGRATION_NOTES.md) and [`../EDISON_HYPOTHESIS_COMBINED_SYNTHESIS.md`](../EDISON_HYPOTHESIS_COMBINED_SYNTHESIS.md) | Generated testable candidates; repository evidence remains controlling |
| Hypothesis Generation `76B68839-DCBF-403D-B2E5-E03B58A0764E` | Independent hypothesis expansion | [`../HYPOTHESIS_GENERATION_76B68839_FULL_EXPORT.zip`](../HYPOTHESIS_GENERATION_76B68839_FULL_EXPORT.zip) | [`../HYPOTHESIS_GENERATION_76B68839_SUMMARY.md`](../HYPOTHESIS_GENERATION_76B68839_SUMMARY.md) | Combined with Edison proposals, then filtered by data access, provenance, leakage, and falsifiability |
| Legacy Kosmos task `FCD3EA` | Execute a flagship experimental OOD knowledge-transfer case | [`legacy_kosmos_2026-07-30/edison_report_download.zip`](legacy_kosmos_2026-07-30/edison_report_download.zip) and extracted [`legacy_kosmos_2026-07-30/Flagship_experimental_OOD_knowledge-transfer_case_report.md`](legacy_kosmos_2026-07-30/Flagship_experimental_OOD_knowledge-transfer_case_report.md) | [`LEGACY_KOSMOS_FLAGSHIP_ASSESSMENT_2026-07-30.md`](LEGACY_KOSMOS_FLAGSHIP_ASSESSMENT_2026-07-30.md), [`SOLVENTSEG_INDEPENDENT_VALIDATION_2026-07-30.md`](SOLVENTSEG_INDEPENDENT_VALIDATION_2026-07-30.md) | Absolute CALiSol-to-KIT transfer was rejected; SolventSeg ranking signal was independently reproduced and then strengthened with harder local baselines |

## Legacy Kosmos task metadata

- Task name: `Flagship experimental OOD knowledge-transfer case`
- Task ID: `FCD3EA`
- Edison run: <https://playground.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3>
- Execution status record:
  [`FLAGSHIP_CASE_EXECUTION_STATUS_2026-07-29.md`](FLAGSHIP_CASE_EXECUTION_STATUS_2026-07-29.md)
- Original prompt:
  [`LEGACY_KOSMOS_FLAGSHIP_OOD_PROMPT_2026-07-29.md`](LEGACY_KOSMOS_FLAGSHIP_OOD_PROMPT_2026-07-29.md)
- Raw extracted report SHA256:
  `ad303386066f24d685ed98b9bdc902856991b848d6540f370c68e26f0acb6b3d`

The raw Markdown retains the trajectory-level Edison links used by the report.
Those links are archived as provenance but should not be treated as independent
primary sources. Dataset DOIs and repository URLs are recorded below and in
[`research/data/ANALYSED_RESOURCE_LEDGER.csv`](../../../research/data/ANALYSED_RESOURCE_LEDGER.csv).

## Resources used or proposed by Edison

| Resource | Role in Edison work | Authoritative access |
|---|---|---|
| CALiSol-23 | Principal electrolyte-conductivity donor | Article DOI [`10.1038/s41597-024-03575-8`](https://doi.org/10.1038/s41597-024-03575-8) |
| KIT/Juelich 5,035 conductivity experiments | Initial recipient and split-development programme | Zenodo DOI [`10.5281/zenodo.7244939`](https://doi.org/10.5281/zenodo.7244939) |
| SolventSeg | Independent formulation-ranking recipient proposed by Kosmos | GitHub [`ndrewwang/SolventSeg`](https://github.com/ndrewwang/SolventSeg/tree/beta); Zenodo DOI [`10.5281/zenodo.6299956`](https://doi.org/10.5281/zenodo.6299956) |
| FINALES conductivity/cycle-life campaign | Frozen second-recipient boundary used after SolventSeg | Materials Cloud DOI [`10.24435/materialscloud:qt-1s`](https://doi.org/10.24435/materialscloud:qt-1s); article DOI [`10.1002/aenm.202403263`](https://doi.org/10.1002/aenm.202403263) |
| Multi-stage lithium-ion battery aging | Temporal/provenance test candidate | Figshare [`25975315`](https://figshare.com/articles/dataset/Multi-Stage_Lithium_Ion_Battery_Aging_Study/25975315); DOI [`10.6084/m9.figshare.25975315.v1`](https://doi.org/10.6084/m9.figshare.25975315.v1) |
| MATR fast-charge data | Cross-laboratory battery donor candidate | <https://data.matr.io> |
| HUST battery lifecycle data | Cross-laboratory battery recipient candidate | Mendeley Data <https://data.mendeley.com/datasets/nsc7hnsg4s/2> |
| FINALES FEC/LiTFSI and one-shot variants | Contingency candidates discussed by Kosmos | Retained as proposals; exact executable use is governed by the local audits, not by the AI ranking |

## What survived validation

The initial absolute CALiSol-to-KIT residual-transfer flagship did **not**
survive a canonical rerun and preprocessing sensitivity checks. The strongest
useful Edison contribution was instead an ordinal hypothesis: a donor trained
on neighbouring electrolyte measurements may preserve candidate order when it
does not preserve absolute scale.

The repository independently reproduced Edison's SolventSeg claim exactly
(`delta rho = 0.2436205943`). It then replaced the weak original comparator
with 13 recipient-only configurations evaluated over 100 outcome-blind
five-label selections. The final programme-balanced source score reached mean
`rho = 0.910`, versus `0.537` for the strongest recipient-only configuration
(`delta rho = 0.374`, 95% interval `0.213-0.562`). This strengthened local
analysis, not the Edison report alone, is the paper-facing result.

The same frozen ordinal route failed on FINALES (`delta rho = -0.089`, 95%
interval `-0.293 to 0.096`). The manuscript therefore reports a selective
ranking edge with an explicit abstention boundary, not a universal electrolyte
transfer rule.

## Independent validation artefacts

The directory
[`legacy_kosmos_2026-07-30/solventseg_validation/`](legacy_kosmos_2026-07-30/solventseg_validation/)
contains the outcome-blind audit, harmonized small tables, original Edison fold
results, an independent verifier, recomputed metrics, shuffled-donor controls,
and baseline sensitivities. Duplicate desktop downloads are intentionally not
versioned; hashes confirmed that the canonical files here are identical.

## Citation and claim rule

Edison/Kosmos is credited as a research ideation and analysis tool where
appropriate, but scientific claims cite the underlying experimental resources
and repository verification. A favorable AI-generated result cannot change a
frozen null, replace a prespecified endpoint, or become independent validation
after its outcomes have been inspected.
