# Flagship cross-database OOD case: execution status

## Edison Legacy Kosmos

- Task name: `Flagship experimental OOD knowledge-transfer case`
- Task ID: `FCD3EA`
- Run URL:
  `https://playground.edisonscientific.com/kosmos/92532a0a-130d-4f42-a1ee-7866dc2d3fd3`
- State at submission: `IN PROGRESS`, 0%
- Cost: 200 Edison credits
- Prompt:
  `analysis/review_packages/edison/LEGACY_KOSMOS_FLAGSHIP_OOD_PROMPT_2026-07-29.md`
- Prompt SHA-256:
  `a58fa90f50ae42b417e716ca07d2dd3025f6af6fb3a9665fb568d46ec1fad107`

The task is constrained to verified open experimental database pairs,
independent provenance, true OOD splits, mechanism-linked transfer objects,
matched falsifiers, and a preregistration-ready winner. DFT-only, proprietary,
same-specimen, derived-label, and random-split-only examples are excluded.

## Local leading frozen test

The strongest already frozen and outcome-unseen local candidate is
**experimental static alloy strength → experimental fatigue life**:

- donor: Borg experimental multi-principal-element-alloy UTS;
- recipient: FatigueData-CMA2022 experimental S-N curves;
- recipient repository DOI: `10.6084/m9.figshare.23007362.v2`;
- recipient article DOI: `10.1038/s41597-023-02354-1`;
- 62 eligible curves, 36 recipient DOIs, 17 compositions;
- all recipient DOIs excluded from Borg donor fits;
- donor source skill: group-OOF \(R^2=0.501\);
- transfer object: predicted UTS used to normalize applied stress, not a
  generic injected feature;
- outer unit: connected provenance-chemistry component;
- target budgets: 20 and 40 whole curves;
- controls: size-matched hardness, size-matched elongation, shuffled UTS,
  target-only, two target learners, and an independent BIRDSHOT disagreement
  gate;
- frozen Balam job: `71905`.

The frozen formal gate uses a 5% minimum RMSE gain. For use as the manuscript's
flagship case, the result will also be judged against the stricter, newly stated
editorial target of approximately 15% gain, positive absolute OOD \(R^2\),
cluster interval above zero, multiplicity-adjusted significance, control
separation, and benefit in most independent components. The original frozen
gate will not be altered.

## Closed or deprioritized candidates

- Battery conductivity → rate-conditioned capacity:
  0.049% primary RMSE gain, interval crosses zero, negative absolute \(R^2\).
- Experimental/theory band gap → perovskite device efficiency:
  all policies fail; effects are approximately zero or harmful.
- Cross-laboratory battery fade:
  formal router abstains on all recipient cells; no transfer effect is
  identified.

These programmes should not receive additional flagship compute unless a new,
mechanistically distinct transfer object is proposed and frozen.

## Edison completion and decision (2026-07-30)

- State: `COMPLETE`
- Edison project display ID: `#7620A8`
- Project UUID:
  `92532a0a-130d-4f42-a1ee-7866dc2d3fd3`
- Cost: 200 Edison credits
- Raw report:
  `analysis/review_packages/edison/legacy_kosmos_2026-07-30/Flagship_experimental_OOD_knowledge-transfer_case_report.md`
- Independent assessment:
  `analysis/review_packages/edison/LEGACY_KOSMOS_FLAGSHIP_ASSESSMENT_2026-07-30.md`

Kosmos did not find a robust flagship absolute-prediction edge. The strongest
apparent numerical result (18.85% RMSE reduction) was invalidated by a
provenance audit and reversed to a 10.26% RMSE increase under the canonical
rerun. A fixed Ridge result that reduced RMSE by 14.85% was not stable to
reasonable preprocessing and nested tuning.

The only promising positive direction is cross-database **ordinal ranking** of
unseen electrolyte formulations. CALiSol-23 predictions improved KIT/Jülich
fold-level Spearman correlation by 0.02406, and Kosmos reports a larger
0.244 improvement on an Oxford/Glasgow target. The latter is not yet admissible:
the report supplies no public DOI or data URL and explicitly leaves its licence
unresolved.

## Updated next decision

1. Recover and independently verify Balam job `71905`; do not infer its result.
2. Do not add the invalid 18.85% conductivity result to the manuscript.
3. Treat the Edison ranking analysis as post-outcome method development.
4. Resolve the alleged Oxford/Glasgow dataset's DOI, file, licence, and
   provenance before accepting the replication.
5. Freeze a rank-to-discovery validation with top-k enrichment/regret endpoints,
   clustered randomization inference, matched electrolyte falsifiers, and a
   third untouched recipient.
