# Article-ready repository links

These links target the current reviewer-response branch. They will resolve
after this package is committed and pushed to that branch.

- Submission evidence landing page: <https://github.com/Yang1Bai/collective-exp-data-index/tree/submission/reviewer-response-package/paper>
- Claim-to-artifact manifest: <https://github.com/Yang1Bai/collective-exp-data-index/blob/submission/reviewer-response-package/paper/claims/claim_manifest.csv>
- Article source data: <https://github.com/Yang1Bai/collective-exp-data-index/blob/submission/reviewer-response-package/paper/data/article_source_data.csv>
- Data access, DOI and licence manifest: <https://github.com/Yang1Bai/collective-exp-data-index/blob/submission/reviewer-response-package/paper/data/datasets.csv>
- Model and protocol allowlist: <https://github.com/Yang1Bai/collective-exp-data-index/blob/submission/reviewer-response-package/paper/models/README.md>
- Editable final figures: <https://github.com/Yang1Bai/collective-exp-data-index/tree/submission/reviewer-response-package/analysis/figures/final_manuscript_svgs>
- Reproduction instructions: <https://github.com/Yang1Bai/collective-exp-data-index/blob/submission/reviewer-response-package/paper/reproduction/README.md>

## Data and code availability text for the manuscript

Code, frozen model specifications, derived result tables, validation records
and editable figure files are available in the submission evidence package at
<https://github.com/Yang1Bai/collective-exp-data-index/tree/submission/reviewer-response-package/paper>.
The claim-to-artifact mapping and full-precision values underlying the reported
headline results are provided in the claim manifest and article source-data
table within that package. Third-party raw datasets are not redistributed by
default; their access URLs, DOIs, licence terms and repository representations
are listed in the data manifest. Upstream datasets remain subject to their
original terms.

## Publication step

The branch URLs above are appropriate for review, not long-term citation.
Before acceptance, tag the exact frozen commit, archive that release through
Zenodo or an equivalent service, add the resulting DOI to `CITATION.cff`, and
replace the landing-page URL in the paragraph above with the DOI. Keep the
claim, data and model links as repository-relative paths inside the archived
release.
