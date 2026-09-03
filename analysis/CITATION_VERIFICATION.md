# Citation verification report

Verification date: 17 July 2026.

The personal LitReview search endpoint was attempted first, as required by the
citation workflow, but returned HTTP 401 without an authenticated session.
References were therefore checked against Crossref metadata and primary
publisher or institutional records. Exact-title web searches for retraction,
correction, or withdrawal notices found one material update: the published
author correction to Jha *et al.* (2019). No retraction notice surfaced for the
other records in the verified set. Absence of a surfaced notice is not a
guarantee against a later editorial action, so this check should be refreshed
immediately before submission.

## Status

| Reference group | Status | Check and manuscript implication |
|---|---|---|
| Yamada 2019; Gupta 2021; Kong 2021 | verified | Crossref/publisher title, authors, journal, year, volume/article and DOI agree; establish prior cross-property and tangential-domain transfer |
| Jha 2019 + Jha 2020 correction | verified with correction | Crossref explicitly links the correction; the manuscript must cite both and use the corrected 1,643-observation target and revised errors |
| Cubuk 2019 | verified and title corrected locally | The formal title is “Screening billions of candidates for solid lithium-ion conductors: A transfer learning approach for small data,” not the earlier paraphrase |
| Taskonomy 2018 | verified | CVF/IEEE record and DOI 10.1109/CVPR.2018.00391; removes any claim to the first computational task-transfer map |
| OBELiX 2026 | verified | RSC/Crossref metadata: *Digital Discovery* 5, 910--918; establishes dataset and leakage-aware benchmark precedent |
| Attari and Arroyave 2025 | verified | RSC/Crossref metadata: *Digital Discovery* 4, 2765--2780; the published March 2025 BIRDSHOT table has 147 rows, distinct from the pinned v5 file used here |
| Dunn 2020 Matbench + correction | verified with correction | Official npj metadata identifies 13 tasks and the five listed authors; DOI 10.1038/s41524-020-00433-0 corrects a figure label from yield strength in GPa to MPa. The local normalization and manuscript use MPa |
| Hacking Materials 2018 steel data | verified dataset | Official Figshare record 10.6084/m9.figshare.7250453 reports 312 deduplicated experimental steels, recommends matminer access, and carries an MIT license; the exact CSV is hash-pinned locally |
| Rahmanian et al. 2023 | verified | Official *Scientific Data* record and Crossref metadata agree on eight authors, volume 10 article 43 and DOI 10.1038/s41597-023-01936-3. The article confirms 504 JSON experiments, −30 to 60 °C in 10 °C steps, repeated measurements, and the CC-BY Zenodo dataset |
| de Blasio et al. 2024 + CALiSol-23 data | verified | Official *Scientific Data*, Crossref, and DTU Data records agree on the five authors, volume 11 article 750, article DOI 10.1038/s41597-024-03575-8, 13,825 points from 27 articles, and CC-BY 4.0. Crossref reports no `update-to` record and links the article to collection DOI 10.11583/DTU.c.6929599.v1. DTU repository metadata identifies the exact item DOI 10.11583/DTU.24559960.v1 and file 43151344; the CSV is SHA-256 pinned locally |
| Ottomano 2024 | verified | RSC/Crossref metadata; establishes the prior result that heterogeneous aggregation need not improve materials ML |
| MDF; OPTIMADE; Medina-Smith vocabulary | verified | Crossref plus official project/NIST records; remove priority claims for data infrastructure, federation and metadata schemas |
| FAIR materials data; data-only illusion; shared experimental memory | verified | Official Nature Portfolio pages and Crossref metadata agree on titles, authors, years, and DOIs; these sources motivate experimental-first framing but do not by themselves establish the manuscript's method |
| Tshitoyan 2019; Marwitz 2026 | verified | Official Nature and Nature Machine Intelligence pages plus Crossref metadata; remove any priority claim for latent-literature recommendations or AI-suggested materials research directions |
| Chang 2022 mixture of experts | verified | Official npj and Crossref metadata; establishes multi-source model combination and learned source-task relevance as direct prior art |
| Li 2023 redundancy; Li 2025 OOD | verified | Official Nature Portfolio pages and Crossref metadata; establish that dataset scale and heuristic OOD labels do not guarantee information-rich or representationally OOD evaluation |
| NIST ISODB | verified institutional dataset | NIST PDR record, DOI 10.18434/T43882, version 1.0; cite as a dataset and do not claim creation or full normalization |
| Krug 1976; Cornish-Bowden 2002 | verified | DOI/publisher or PubMed metadata; establish the statistical-artifact critique |
| Bond 2000; Mianowski and Urbańczyk 2017 | verified | Publisher/institutional metadata; establish heterogeneous-catalysis and isosteric-adsorption compensation precedent |
| LEEP; OTDD | verified | Official PMLR and NeurIPS proceedings records; establish transferability scoring and model-agnostic dataset-distance precedents |
| Multi-fidelity BO; multi-information-source optimization | verified | Official PMLR and NeurIPS proceedings records; establish cost-aware use of biased or lower-fidelity information sources in sequential optimization |

The exportable BibTeX file is `REFERENCES.bib`. Its purpose is to prevent
novelty drift: these references are not decorative background, but explicit
constraints on what this manuscript can claim.

## 17 July 2026 adjacent-framework additions

- Nguyen *et al.*, LEEP, PMLR 119, 7294--7305 (2020):
  `https://proceedings.mlr.press/v119/nguyen20b.html`.
- Alvarez-Melis and Fusi, geometric dataset distances via optimal transport,
  NeurIPS 33 (2020): official NeurIPS abstract and BibTeX record.
- Kandasamy *et al.*, multi-fidelity Bayesian optimisation, PMLR 70,
  1799--1808 (2017): `https://proceedings.mlr.press/v70/kandasamy17a.html`.
- Poloczek, Wang and Frazier, multi-information source optimization, NeurIPS 30
  (2017): official NeurIPS abstract and BibTeX record.

These references bound the novelty claim: the manuscript does not introduce
task-distance estimation, transferability scoring, or multi-fidelity Bayesian
optimization. Its distinction is the falsification-first audit of realized
experimental source→target utility across separate prediction, screening, and
acquisition endpoints.

## 17 July 2026 experimental-first framing additions

- Scheffler *et al.*, *Nature* 604, 635--642 (2022), DOI
  `10.1038/s41586-022-04501-x`.
- Smit and Garcia, *Nature Materials* (2026), DOI
  `10.1038/s41563-026-02578-7`.
- Akhound, Sauer and Thygesen, *Nature Reviews Materials* (2026), DOI
  `10.1038/s41578-026-00938-y`.
- Tshitoyan *et al.*, *Nature* 571, 95--98 (2019), DOI
  `10.1038/s41586-019-1335-8`.
- Marwitz *et al.*, *Nature Machine Intelligence* 8, 535--544 (2026), DOI
  `10.1038/s42256-026-01206-y`.
- Chang, Wang and Ertekin, *npj Computational Materials* 8, 242 (2022), DOI
  `10.1038/s41524-022-00929-x`.
- Li *et al.*, *Nature Communications* 14, 7283 (2023), DOI
  `10.1038/s41467-023-42992-y`; and *Communications Materials* 6, 9 (2025), DOI
  `10.1038/s43246-024-00731-w`.

Crossref returned no `update-to` record for these eight additions on the stated
verification date. Their role is explicit: the first three establish the need
for contextual experimental memory, the next two establish AI-assisted
scientific inspiration as prior art, Chang *et al.* establish learned
multi-source relevance, and the two Li *et al.* studies bound claims about data
volume and OOD generalization. The manuscript's remaining distinction is the
experimental falsification and endpoint-conversion layer.
