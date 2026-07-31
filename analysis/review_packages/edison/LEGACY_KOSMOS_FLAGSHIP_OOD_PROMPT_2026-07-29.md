# Legacy Kosmos task: find and de-risk a flagship experimental OOD-transfer case

You are the lead scientist and adversarial methodologist for a materials-
informatics study. Your task is not to survey transfer learning broadly. Find,
verify, and de-risk one **genuinely compelling, executable flagship example**
in which knowledge learned from one open experimental database materially
improves prediction in a data-poor, out-of-distribution region of an
independent neighboring experimental domain.

Public project:
https://github.com/Yang1Bai/collective-exp-data-index

## Scientific thesis

When scientific understanding is incomplete, heterogeneous data aggregation
does not automatically reveal a universal law. However, neighboring
experimental domains may contain selectively transferable knowledge. The
portable object may be a mechanism-linked response relation, correction law,
low-dimensional physical parameter, or independent candidate ranking—not raw
pooled rows, generic pretrained weights, or an arbitrary donor prediction.

## Current evidence and the unresolved gap

The project contains 20 analyzed experimental resources. Generic donor-feature
injection repaired none of 40 designated OOD edges across eight targets.
Positive results exist but are not yet a decisive cross-database flagship:

- neighboring electrolyte temperatures within one campaign reduce few-shot
  RMSE by 15.02%;
- a state-matched alloy-property donor reduces a selected Q4 OOD RMSE by
  9.21%, but the properties largely share specimens/provenance;
- in literature-curated CALiSol, absolute cross-article transfer is unresolved
  (+1.61%). A post-outcome method that transfers within-article formulation
  response contrasts and uses one target-article anchor improves macro-RMSE by
  6.91% across 11 held-out articles;
- cross-database electrolyte donors improve retrospective candidate ranking in
  selected pools, but not global OOD numerical prediction;
- several genuinely external database pairs are null or harmful, including a
  deep molecular donor.

We therefore still lack one case that convincingly shows an independent
experimental database improving another database's true OOD prediction.

## Non-negotiable eligibility criteria

Both donor and recipient must:

1. contain downloadable numerical **experimental** measurements with stable
   paper/repository identifiers and legal reuse access;
2. come from independent databases, laboratories, publications, or experimental
   programmes—not two labels extracted from the same measurement event or the
   same batch of specimens;
3. expose a compatible input representation for recipient candidates
   (composition, molecule, formulation, structure, processing variables, or a
   justified crosswalk);
4. contain enough experimental-state metadata to avoid mixing incompatible
   temperature, pressure, electrolyte, synthesis, processing, or testing
   regimes;
5. support a defensible provenance-, time-, laboratory-, chemical-family-, or
   process-held-out OOD split. A random split or a nominal leave-one-element-out
   split that remains representational interpolation is insufficient;
6. have a mechanistic reason why a **relation, correction, parameter, or
   ranking** learned from the donor should transport to the recipient;
7. allow matched falsifiers: shuffled donor labels, an equally sized wrong
   donor, a wrong experimental condition, and target-only/state-aware
   baselines.

Reject DFT-to-DFT examples, proprietary/ICSD-dependent data, targets derived
algebraically from the donor label, unavailable supplementary files, same-row
proxy-label leakage, and cases whose only evidence is improved random-split
accuracy.

## What counts as a flagship success

Design for a result that could satisfy all of the following:

- independent donor and recipient sources;
- positive absolute OOD \(R^2\), not merely a less-negative score;
- at least approximately 15% macro-RMSE reduction relative to a strong,
  state-aware target-only model at a predeclared low-label budget or 1–3 target
  anchors;
- article/lab/family-cluster uncertainty interval with a lower bound above
  zero and multiplicity-aware \(p<0.05\);
- at least a 5 percentage-point advantage over an architecture- and
  size-matched shuffled/wrong donor;
- benefit in most independent OOD groups;
- replication in a second recipient database, second experimental programme,
  or locked secondary OOD region.

These are design targets, not permission to cherry-pick. A credible negative
assessment is preferable to an ineligible positive result.

## Search space

Search broadly across open experimental materials and chemistry repositories,
including but not limited to:

- ionic/electronic conductivity, diffusivity, viscosity, dielectric response,
  and battery rate or low-temperature performance;
- optical absorption, experimental band gaps, frontier energy levels,
  photoluminescence, photovoltaic, photocatalytic, and OLED/device performance;
- adsorption, surface/electronic descriptors, and experimentally measured
  catalytic or electrocatalytic activity;
- mechanical properties, processing, microstructure, fatigue, fracture, and
  strength;
- polymer, electrolyte, solubility, permeability, and transport datasets.

Prioritize pairs where the neighboring relation is known to be locally stable
but the absolute scale is shifted by laboratory or protocol, because these are
natural candidates for relation transfer plus few-shot provenance calibration.

## Required work

### Phase 1 — verified candidate discovery

Find at least ten plausible donor→recipient pairs. For every pair, verify:

- exact paper DOI and direct data/repository URL;
- experimental rather than computational status;
- download accessibility without subscription or private credentials;
- approximate row counts, independent publication/lab groups, target and donor
  columns, experimental conditions, identifiers, and license;
- common input representation and estimated recipient coverage;
- whether target outcomes are independent of donor labels;
- a concrete transfer object: response difference, derivative, transformation,
  physical parameter, residual correction, calibrated latent coordinate, or
  fixed ranking;
- a concrete true-OOD split and leakage unit;
- the strongest likely confound or fatal blocker.

Do not rank a pair highly until the data files and essential schema have been
inspected. Label unverified claims explicitly.

### Phase 2 — adversarial triage

Eliminate ineligible candidates. Produce a ranked shortlist of the best three
and score each from 0–5 for:

1. mechanistic adjacency;
2. independent provenance;
3. input/schema compatibility;
4. state metadata completeness;
5. target data scarcity and OOD relevance;
6. falsifiability and matched-control quality;
7. expected effect size;
8. computational feasibility;
9. publication value.

Give an explicit estimated probability that each candidate will pass the
flagship gate. Explain why the winner is more likely to succeed than the
project's previous generic donor injections.

### Phase 3 — winner audit and frozen test design

For the top candidate, perform an outcome-blind data audit where possible:

- retrieve and inspect the actual data files;
- compute entity, condition, publication/lab, and feature coverage;
- identify duplicate or shared-provenance leakage;
- define donor, recipient, OOD groups, common inputs, eligible sample counts,
  target-label budgets, and anchor-selection policy without examining the
  transfer outcome;
- state exactly which information is available at prediction time.

Then write a preregistration-ready experiment:

- primary estimand and independent unit;
- target-only and state-aware baselines;
- transfer model, including why the transferred object should survive
  provenance shift;
- nested/grouped cross-fitting;
- exact OOD split and prohibited leakage;
- matched wrong-donor, shuffled-donor, wrong-condition, and source-skill
  controls;
- primary and secondary metrics;
- clustered bootstrap/permutation tests and multiplicity correction;
- success, null, harm, and abstention gates;
- compute requirements and an executable implementation outline.

If accessible data permit, run only outcome-free schema/coverage checks and
small code smoke tests. Do not inspect the primary transfer outcome before the
design is frozen.

## Required output

Return:

1. a concise scientific conclusion;
2. a machine-readable candidate table;
3. the elimination log for rejected candidates;
4. the top-three scorecard;
5. exact verified data and paper links;
6. the complete frozen protocol for the winner;
7. a contingency plan for the second-ranked pair;
8. a section titled **What would make this result unpublishable?**

Do not substitute a generic methods review for verified, downloadable database
pairs. Do not claim success before a frozen test is executed.
