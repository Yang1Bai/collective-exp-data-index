# Cross-database interaction plan for the BambooMixer relation

## Scientific objective

Use the BambooMixer experimental conductivity corpus as one broad donor inside
the project's artifact-gated borrowing map, rather than treating its published
LiAsF6 result as a new discovery. The decisive question is whether the frozen
mixture relation improves an independent programme relative to recipient-only,
state-only and chemistry-destroyed alternatives, and whether the routing gate
correctly distinguishes absolute prediction, candidate ranking and abstention.

## Provenance finding that changes the design

The public BambooMixer training JSON contains formulation, state and outcome
fields but no article DOI or row-level provenance. Direct database-name
separation is therefore insufficient.

A preliminary record-fingerprint audit compared the 359 conductivity records
in the BambooMixer LiPF6/EC/EMC subset with the harmonized CALiSol and
SolventSeg resources:

- 71 of the 410 CALiSol subset rows have a near-exact match in
  solvent composition, salt concentration, temperature and conductivity
  (composition distance at most \(10^{-4}\) and conductivity difference at
  most 0.01 mS cm\(^{-1}\));
- no SolventSeg row has a match under that strict criterion; one row has a
  near match only after relaxing the composition tolerance to \(10^{-3}\);
- absence of a strict row match does not prove article independence because
  the BambooMixer source omitted DOI metadata.

Consequences:

1. BambooMixer and CALiSol must not be pooled or labeled independent without
   decontamination.
2. CALiSol cannot serve as a confirmatory recipient for the unfiltered
   BambooMixer source.
3. SolventSeg is the best available development recipient because it is an
   independently measured programme and lacks strict record matches.
4. A future confirmatory recipient must have explicit programme provenance and
   outcomes unavailable when the method is frozen.

## Experiment 1: external programme reuse on SolventSeg

### Recipient

The 36 LiPF6/EC/EMC formulations measured at 10, 20, 25, 30 and 40 degrees C
in SolventSeg. All five temperature rows from one formulation remain an
indivisible group. The target is already outcome-known in this project, so the
experiment is method development, not confirmation.

### Frozen donor arms

1. complete BambooMixer conductivity relation;
2. BambooMixer excluding every LiPF6/EC/EMC record;
3. BambooMixer LiPF6/EC/EMC-only relation;
4. the existing provenance-rich CALiSol donor;
5. the existing KIT controlled-campaign donor;
6. a decontaminated multi-source portfolio in which duplicate
   composition--state--outcome fingerprints receive one source identity and
   one total weight;
7. temperature-and-concentration-only, chemistry-permuted and wrong-salt
   controls.

### Endpoints

- zero-shot absolute log-RMSE and \(R^2\) over the full external programme;
- fixed-25-degrees-C Spearman correlation, top-quartile precision and
  normalized regret;
- one-, three- and five-formulation anchor calibration versus same-budget
  recipient-only models;
- edge-versus-centre and five-cluster formulation OOD scopes already frozen
  for SolventSeg.

### What the contrasts identify

- complete versus state-only: value of transferable mixture chemistry;
- complete versus chemistry-permuted: source specificity;
- complete versus LiPF6/EC/EMC-only: value of chemically diverse source
  coverage;
- complete versus LiPF6/EC/EMC-excluded: marginal value of the closest
  formulation family;
- decontaminated portfolio versus best single donor: whether multiple
  experimental programmes provide complementary relations;
- frozen source versus same-budget recipient-only: data-scarcity rescue.

## Experiment 2: unchanged test on FINALES

Apply the exact relation and routing thresholds selected in Experiment 1 to the
chronological FINALES LiPF6/EC/EMC campaign. Preserve its three chronological
anchors and later evaluation formulations. Because FINALES outcomes have
already been inspected in this project, this remains a locked secondary
development test. It can establish whether the new representation repairs the
previous ranking failure or whether programme-level scale and sampling policy
still force abstention; it cannot provide independent confirmation.

Absolute metrics are secondary until the FINALES conductivity unit and
instrument conversion are reconciled with BambooMixer. Temperature-matched
pairwise concordance and within-temperature ranking remain the safe endpoints.

## Experiment 3: outcome-sealed confirmation

After Experiments 1 and 2, freeze:

- the molecular and mixture representation;
- source datasets and decontamination rule;
- source weights or portfolio rule;
- state-only, chemistry-permuted and nearest-family-exclusion controls;
- target-anchor selection and shrinkage strength;
- grouping unit, primary metric and practical gate;
- prediction/ranking/abstention routing thresholds.

Test one newly measured or outcome-sealed electrolyte programme containing a
salt, solvent family or concentration regime absent from at least one donor.
The preferred target has 24--60 exact formulations, at least three measurement
states per formulation, one fixed protocol and explicit provenance.

The primary success condition is:

1. at least 10% lower formulation-grouped log-RMSE than state-only and the
   strongest same-budget recipient-only model;
2. 95% formulation-bootstrap intervals above zero for both contrasts;
3. positive absolute \(R^2\);
4. real-source benefit greater than chemistry permutation and
   nearest-family-exclusion controls;
5. no exact formulation, article or measurement-event overlap;
6. no post-outcome change of donor, representation, endpoint or threshold.

If absolute prediction fails but the frozen ranking improves Spearman
correlation by at least 0.10, improves top-quartile precision and reduces
regret, route the edge to screening. Otherwise abstain.

## Manuscript role

The published LiAsF6 reanalysis demonstrates that a chemistry-aware mixture
relation can be portable and supplies the mechanism and controls. SolventSeg
tests interaction with an independently collected database. FINALES tests an
unchanged adverse programme boundary. The outcome-sealed third programme is
the only step that can convert the sequence into independent evidence that the
project's routing rule, rather than post-outcome model selection, predicts
when neighboring experimental knowledge repairs an OOD decision.

The resulting main-text claim should be:

> A broad experimental donor relation can transfer to an independent
> formulation programme, but the useful object and admissible claim depend on
> source decontamination, shared state support and recipient endpoint; the
> frozen gate decides between prediction, ranking and abstention.
