# Assessment of the Edison Legacy Kosmos flagship-search report

## Executive decision

The run did **not** identify a defensible flagship case in which neighboring
experimental knowledge robustly improves absolute OOD prediction. Its most
important positive result is narrower and potentially more useful for
discovery: a donor conductivity model may improve the **ranking** of unseen
electrolyte formulations even when it does not improve their absolute
conductivity predictions.

That ranking result is now independently verified as a real, practically
meaningful shortlist improvement, but it is still retrospective
method-development evidence rather than a confirmatory result. The
Oxford/Glasgow recipient has been traced to SolventSeg data DOI
`10.5281/zenodo.6299956` and publication DOI
`10.1016/j.xcrp.2022.101047`. The original \(\Delta\rho=0.2436206\) was
reproduced exactly, and the transfer remained positive when ranking
formulations at a fixed temperature. The remaining blockers are post-selection,
one independent recipient, only five OOD clusters, the absence of a
support-matched wrong-electrolyte donor, and an ambiguous data-specific licence.

The complete independent validation is archived at
`analysis/review_packages/edison/SOLVENTSEG_INDEPENDENT_VALIDATION_2026-07-30.md`.

## Archived source

- Edison project:
  `https://playground.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3`
- Raw Markdown report:
  `analysis/review_packages/edison/legacy_kosmos_2026-07-30/Flagship_experimental_OOD_knowledge-transfer_case_report.md`
- Raw-report SHA-256:
  `ad303386066f24d685ed98b9bdc902856991b848d6540f370c68e26f0acb6b3d`

## Audit of the user-provided “results” archive

- Supplied archive:
  `Flagship_experimental_OOD_knowledge-transfer_case_results.zip`
- Archive SHA-256:
  `f3763274c85dec2f88f3f80b497114633367646167f389403b631755388b4557`
- Archive members: exactly one.
- Sole member:
  `Flagship_experimental_OOD_knowledge-transfer_case_report.md`
- Sole-member SHA-256:
  `ad303386066f24d685ed98b9bdc902856991b848d6540f370c68e26f0acb6b3d`

The sole member is byte-for-byte identical to the report already archived
above. Despite the archive name, this is **not a computational result package**.
It contains no input manifest, source URLs, code, environment, split
assignments, anchor selections, fold predictions, metrics table, resampling
draws, model parameters, or checksum manifest. Consequently, none of the
reported effect sizes or significance tests can be independently recalculated
from this archive.

For an independently auditable release, Edison would need to export at least:

1. a source manifest with DOI, repository URL, licence, retrieved timestamp,
   and raw-file hashes;
2. the exact CALiSol, KIT/Jülich, and alleged Oxford/Glasgow analysis tables;
3. formulation identifiers, provenance groups, OOD folds, and anchor sets;
4. row-level measured values and predictions for every model/control;
5. fold-level and seed-level metrics plus all bootstrap/permutation draws;
6. executable code, fixed dependencies, random seeds, and a checksum manifest.

## What survived the adversarial audit

| Programme | Reported result | Audit decision |
|---|---:|---|
| CALiSol-23 → KIT/Jülich absolute conductivity | OLS residual transfer increased RMSE by 12.69%; nearest-donor restriction increased it by 25.41% | Clear negative transfer |
| Fixed unscaled Ridge reconstruction | RMSE decreased by 14.85% in one reconstruction | Reject as flagship: the result reversed under standardized, nested tuning, which increased RMSE by 19.02%; anchor sensitivity was severe |
| Arrhenius activation-energy transfer | Donor leave-publication-out \(R^2=0.669\); recipient correlation \(r=0.815\) | Mechanistic shape is portable, but a global intercept made absolute prediction catastrophically worse; scale is formulation-specific |
| CALiSol-23 → KIT/Jülich ranking | Mean \(\Delta\rho=0.02406\), all seven folds positive, nominal Holm-adjusted \(p=0.007\) | Promising but practically small and statistically not confirmatory |
| Oxford/Glasgow SolventSeg ranking replication | Mean \(\Delta\rho=0.2436206\), reproduced exactly; fixed-25 °C donor \(\rho=0.701\) versus original baseline \(0.316\) | Strongest current independent cross-database positive edge; valid as retrospective OOD-shortlist evidence, not yet confirmatory discovery |
| Purported independent conductivity contingency | Initially 18.85% lower RMSE | Invalid: it reused the same recipient CSV; the canonical rerun instead increased RMSE by 10.26% |
| KIT → Munich battery-ageing transfer | RMSE increased by 229.3% | Decisive negative transfer |

## External source checks

Two central public resources are traceable:

- CALiSol-23 is a real CC BY 4.0 dataset with 13,825 measurements from 27
  publications:
  `https://data.dtu.dk/articles/dataset/CALiSol-23/24559960`
  and DOI `10.1038/s41597-024-03575-8`.
- The KIT/Jülich recipient is traceable as the open dataset “Dataset of 5035
  Conductivity Experiments for Lithium-Ion Battery Electrolyte Formulations at
  Various Temperatures”, DOI `10.5281/zenodo.7244939`.

SolventSeg is independently traceable. Zenodo DOI
`10.5281/zenodo.6299956` archives the repository for the paper *Current-driven
solvent segregation in lithium-ion electrolytes*, DOI
`10.1016/j.xcrp.2022.101047`; the public GitHub repository contains the
experimental `Ternary_Physicochemical_Training.csv`. The harmonized recipient
contains 36 LiPF6/EC/EMC formulations at five temperatures, for 180
salt-containing measurements. Oxford/Glasgow/Faraday affiliations are distinct
from the three CALiSol donor source publications. The repository is MIT
licensed and Zenodo labels the deposit “Other (Open)”, but the data-specific
redistribution licence remains ambiguous.

## Why the ranking result is not yet a paper-level proof

1. **Post-selection:** the ranking endpoint was promoted after absolute-value
   transfer failed and after many models, partitions, anchors, and corrections
   had been inspected. Nominal \(p\)-values do not include this search.
2. **Dependence:** paired \(t\)-tests on seven or five cross-validation folds
   treat heavily overlapping training sets as if they were independent
   experiments.
3. **Small primary effect:** \(\Delta\rho=0.024\) is directional evidence, not
   by itself a material discovery advantage.
4. **Pathological secondary splits:** KMeans and agglomerative variants produced
   very large gains partly because recipient-only baselines were sometimes
   constant. Those values should not be used as headline evidence.
5. **Weak falsifier construction:** quantile-mapped battery-ageing donors are
   not a close, architecture- and support-matched electrolyte falsifier. After
   calibration, the true donor's mean \(\rho=0.960446\) exceeded the best wrong
   donor's \(0.957468\) by only about 0.003.
6. **Decision endpoint partly resolved:** at 25 °C, top-quartile precision was
   0.90 and normalized regret was 0.015, both substantially better than
   shuffled-donor controls. Top-one hit rate was only 0.40 and was not
   significant, so the allowed claim is shortlist enrichment rather than
   reliable selection of the single best formulation.
7. **One external recipient:** provenance, files, and publication are now
   resolved, but a second untouched recipient or a temporal/prospective split
   is still required for confirmation.

## Scientific interpretation

The run strengthens a transfer-object hierarchy:

1. laboratory-specific absolute values are least portable;
2. mechanistic curve shape can be partly portable but needs recipient-specific
   scale calibration;
3. ordinal candidate order may survive a provenance shift better than absolute
   calibration;
4. more distant curve transfer can be strongly harmful.

This is consistent with the project's central thesis, but it changes the
positive claim from “neighbor knowledge improves the target regressor” to
“neighbor knowledge can provide an independently useful OOD search prior”.
That is scientifically stronger than forcing a fragile RMSE gain, provided the
search utility is demonstrated directly.

## Frozen next experiment recommended

Treat the Edison analysis as method development and freeze a local
**rank-to-discovery validation** before any additional target outcomes are
inspected:

1. reproduce CALiSol-23 → KIT/Jülich with the donor model and ranking rule fixed;
2. freeze the now-verified SolventSeg method and repeat it on a second untouched
   experimental conductivity programme;
3. designate a third, genuinely untouched experimental conductivity programme
   as the confirmatory recipient;
4. hold out complete composition families or experimental campaigns, not random
   rows;
5. evaluate top-\(k\) recall, enrichment factor, normalized discounted
   cumulative gain, simple regret, and area under the discovery curve in
   addition to Spearman correlation;
6. compare against target-only, target-only uncertainty, shuffled CALiSol labels
   blocked by source DOI/formulation, a size- and support-matched wrong
   electrolyte donor, and a donor-free composition-similarity prior;
7. use formulation/cluster-level randomization inference and hierarchical
   bootstrap, with a multiplicity plan that includes every declared endpoint;
8. predeclare an abstention region for high-molality/curvature-mismatched
   formulations.

The ranking programme should enter the manuscript only if it improves an
actual discovery metric on the independently verified target and separates
from the matched falsifiers. Otherwise the Edison run remains valuable negative
evidence about the boundary between portable order and non-portable scale.
