# Edison 7BDBBC46 scientific audit and project integration

## Source

- File reviewed: `Edison Playground.pdf`
- Edison task: `7bdbbc46-cf15-4c6a-9ad3-7cecf58db99b`
- Audit date: 2026-07-29
- Intended use: scientific strategy, not manuscript editing

## Bottom-line decision

The report contains one important methodological insight but does not satisfy the
experimental brief well enough to determine the paper's next flagship by itself.

> The transferable object should often be a **relative response law, physical
> correction, or mechanism parameter**, rather than a donor's absolute property
> prediction.

This principle should be adopted. Edison's proposed flagship experiments should
not be adopted as the empirical centre of the paper:

1. OC20 to OC22 is a computational DFT-to-DFT transfer problem, not borrowing
   between experimental databases.
2. DFT-to-experimental band-gap calibration is a multi-fidelity Sim2Real problem,
   not neighbouring experimental-domain borrowing; its proposed experimental
   recipient was not verified.

The most useful synthesis of the Edison and Claude reviews is therefore:

> **Mechanism-anchored differential borrowing:** use an independent experimental
> donor to learn how a system responds, or how a small set of physical parameters
> changes, then update that transferable relationship with a small amount of
> recipient evidence. Do not transplant absolute donor labels.

The best immediate implementation is the proposed cross-laboratory battery
degradation experiment. HTEM cross-library response fields and pairwise
solid-state reaction boundaries are secondary programmes.

## Compliance with the clean-sheet brief

| Required item | Edison output | Audit |
|---|---|---|
| Experimental neighbouring-domain flagship | OC20 to OC22 DFT transfer | **Failed requirement** |
| At least 10 new hypotheses | Six hypotheses | **Incomplete** |
| Verified experimental dataset landscape | Mostly computational resources; experimental band-gap recipient unverified | **Incomplete** |
| Candidate-time semantics | Generally discussed | **Partly adequate** |
| Independent experimental OOD unit | Not supplied for the flagship | **Failed requirement** |
| Negative/wrong-domain controls | Proposed in broad terms | **Partly adequate** |
| Preregistered practical gate | Proposed | **Useful, but thresholds are not justified by power** |
| New scientific-discovery endpoint | DFT-ranked oxide catalysts and band gaps | **Computational validation, not experimental discovery** |

The bibliography also overstates breadth: the PDF contains 38 DOI mentions but
only 15 unique DOIs. The statement that 76 papers were surveyed cannot be inferred
from the report's traceable reference list.

## What should be adopted

### 1. Transfer differences rather than absolute values

For candidate \(i\) relative to an anchor \(j\), learn

\[
\Delta y_{ij}=y_i-y_j=f(\Delta x_{ij},s_i,s_j),
\]

where \(s\) contains matched experimental state. This can cancel laboratory
offsets and other nuisance terms that dominate absolute cross-database values.
The relationship is usable only where the donor contains comparable perturbations
and state.

### 2. Transfer physical parameters and update them locally

When a response curve has an interpretable low-dimensional form, transfer a
population prior over its parameters and the mapping from early observations to
those parameters. Recipient evidence then updates the prior. This is more robust
than freezing donor predictions because the recipient retains an experimental
anchor.

### 3. Use a small bridge only when it is a real experimental bridge

SevenNet-Omni shows that small bridging sets can align computational potential
energy surfaces. In this paper, the analogous bridge must consist of measurements
from the recipient programme, not additional calculations silently treated as
experimental evidence. Bridge size must be varied prospectively.

### 4. Retain the null expert

Every model must be allowed to revert to the recipient-only baseline when donor
support, state compatibility, or donor-recipient agreement is inadequate. A
forced-transfer model is not a knowledge-borrowing policy.

## What should not be adopted

1. **Do not replace the paper's experimental centre with OC20 to OC22.** It would
   change the question from experimental knowledge borrowing to transfer among
   calculated potential-energy surfaces.
2. **Do not call UMAP separation proof of OOD.** UMAP is representation- and
   hyperparameter-dependent. The formal split must be defined by provenance and
   scientifically interpretable excluded groups, then supplemented with
   predeclared support distances.
3. **Do not equate near-optimal calculated O-star binding with experimental OER
   activity.** It is a surrogate and is especially fragile where scaling
   relations break.
4. **Do not call SHAP-guided feature selection causal discovery.** SHAP attributes
   a fitted predictor; it does not identify causal mechanisms.
5. **Do not use unpowered success thresholds.** Values such as twofold TPR,
   20% MAE reduction, and 0.3 eV MAE were extrapolated from unrelated studies.
6. **Do not use candidate validation by HSE or GW as experimental confirmation.**
   It is higher-fidelity computation.
7. **Do not return to band-gap-to-device-performance scalar injection.** The
   project's formal perovskite-power-conversion-efficiency experiment already
   found no passing policy and effect sizes close to zero.

## Flagship upgrade: mechanism-anchored differential battery borrowing

### Scientific hypothesis

Across independent laboratories using the same cell chemistry, absolute capacity
and lifetime values are strongly shifted by protocol and instrumentation, but the
mapping from a cell's **early relative degradation response** to a small set of
degradation parameters is more stable. A donor-learned parameter prior and mapping,
updated with at most ten labelled recipient cells, will improve lifetime prediction
for the remaining recipient cells.

### Donor and recipient

- **Donor:** MATR/Severson and Attia LFP/graphite cell programmes, with complete
  early-cycle trajectories and late-life outcomes.
- **Recipient:** SNL LFP cells from Battery Archive, conditional on an
  outcome-blind metadata audit; HUST LFP is the frozen backup.
- **Wrong-chemistry donor:** NCA/NMC cells, expected to trigger abstention or null.

The primary OOD boundary is the entire recipient laboratory/dataset, not a random
cell split.

### Transferable knowledge object

For every cell, only measurements available by cycle 100 are used to construct:

- capacity loss relative to cycles 1, 10, 50 and 100;
- slopes and curvature of relative capacity loss;
- relative changes in coulombic efficiency and internal resistance where shared;
- differential-voltage or \(Q(V)\) changes on a common voltage grid;
- protocol-normalized charge throughput and temperature exposure.

Fit an interpretable degradation curve such as

\[
Q_{\mathrm{loss}}(n)=a n^\beta + h(n;n_{\mathrm{knee}},\gamma),
\]

and transfer:

1. the donor population prior over
   \((\log a,\beta,\log n_{\mathrm{knee}},\gamma)\); and
2. the donor mapping from early **relative** response features to those parameters.

Recipient early-cycle data update the cell-level parameter posterior. No absolute
donor lifetime prediction is inserted as a feature.

### Models

1. Recipient-only hierarchical degradation model with weak priors.
2. Donor-informed hierarchical model with the differential response mapping.
3. Simple target-only elastic net/tree model on the same early-cycle features.
4. Optional Gaussian-process response model as a sensitivity analysis.

The complex model is acceptable only if it outperforms both simple recipient-only
baselines.

### Controls

The comparison family is frozen before recipient lifetime labels are read:

1. recipient-only model;
2. absolute-value donor transfer, testing whether differencing is essential;
3. shuffled donor cell-to-parameter mapping;
4. wrong-chemistry NCA/NMC prior;
5. donor prior without the response mapping;
6. response mapping with an information-matched unstructured Gaussian prior;
7. oracle recipient-full-data ceiling, excluded from inference.

### Label budgets and estimand

- Recipient labelled-cell budgets: 0, 5 and 10.
- Primary estimand: paired relative reduction in RMSE of
  \(\log_{10}(\text{cycles to 80% SOH})\) on held-out recipient cells.
- Secondary: MAPE, calibration/coverage, error at short- and long-life tails,
  and top-risk-cell recall at a frozen review budget.
- Replication unit: cell; protocol blocks are retained in cluster resampling.
- Random seeds are not replicates.

### Success gate

All conditions must be satisfied at a budget of at most ten labelled recipient
cells:

1. at least 10% relative RMSE improvement over recipient-only;
2. cell/condition-clustered 95% interval lower bound above zero;
3. Holm-adjusted \(p<0.05\) across the frozen control family;
4. at least five percentage points better than both shuffled and wrong-chemistry
   controls;
5. absolute held-out \(R^2>0\);
6. empirical interval coverage no worse than recipient-only;
7. at least 65% of paired label-budget draws are positive.

### Abstention

Use recipient-only prediction for a cell when either:

- its early response falls outside the predeclared donor support; or
- recipient evidence creates a large prior-posterior conflict.

The support metric and conflict threshold must be frozen using donor-only
resampling. Coverage and abstention rate are reported as primary operating
characteristics, not hidden.

### Interpretation

- **Positive:** an experimentally independent cross-laboratory edge shows that a
  response law and parameter prior can cross provenance where absolute values do
  not.
- **Null:** the provenance barrier also disrupts degradation-response parameters;
  the donor must abstain, supporting the borrowing-map boundary.
- **Harmful:** the proposed invariant is not invariant; retire the method rather
  than tune on the revealed recipient outcomes.

## Secondary programme 1: HTEM cross-library response-field transfer

The High-Throughput Experimental Materials Database currently exposes 1,891
thin-film libraries and 82,776 samples, including composition, processing,
structure, optical properties and electrical properties. Its spatially resolved
combinatorial libraries create natural controlled perturbations.

Proposed test:

1. learn local composition/process perturbation to relative band-gap,
   conductivity, or phase-boundary response inside donor libraries;
2. transfer this response field to an entirely held-out experimental library or
   campaign in a related chemical system;
3. predict sparse recipient measurements using composition and synthesis state
   available before the withheld measurement;
4. group inference by library and project, never by individual wafer position;
5. compare against absolute-value transfer, target-only learning, shuffled spatial
   gradients and chemically distant libraries.

This is the closest fully experimental analogue of Edison's analogical
transduction idea. It should begin with a metadata-only audit of cross-library
property overlap and independent campaign counts. It is not confirmatory until
the target libraries and endpoints are frozen before outcomes are inspected.

## Secondary programme 2: pairwise reaction boundary transfer

The Precursor Genome provides 1,035 pairwise solid-state reactions, genuine
negative and partial outcomes, complete thermal metadata and XRD-derived phase
labels. Its relational structure is ideal for learning

\[
\Delta(\text{precursor pair, thermal state})\rightarrow
\Delta(\text{reaction outcome}).
\]

The intended recipient remains the complete A-Lab attempt table. This programme
stays on hold until all 355 attempted recipes, including failures and partial
products, can be linked to candidate-time precursor and process fields. An
internal element-family holdout may develop the method but cannot be presented as
independent cross-database validation.

## Literature audit

1. **Segal et al., Known Unknowns.** The published claim is property-tail
   extrapolation using transductive analogical relations. Its reported threefold
   materials TPR gain does not prove cross-database experimental transfer.
2. **Yahagi et al.** The chemistry-informed transformation is a real
   computation-to-experiment proof of concept for reverse water-gas-shift
   catalysis, using fewer than ten target points. It motivates physical
   transformations but does not validate the proposed band-gap correction.
3. **SevenNet-Omni.** Selective task regularization plus approximately 0.1%
   domain-bridging structures improves multi-domain interatomic potentials.
   This supports the bridge concept only in computational PES space.
4. **BOOM.** Generic language-model pretraining improves in-distribution metrics
   but not OOD molecular property prediction; the paper defines OOD mainly by
   property tails. This supports stopping generic pretraining, not a universal
   prohibition on all physically aligned pretraining.
5. **OC20 to OC22.** Prior work already demonstrated transfer between computed
   metal and oxide catalyst datasets. The new bilinear proposal is untested, and
   success would primarily be a model contribution in computational catalysis.

## Final project decision

Edison should change the method layer, not the dataset centre:

> Replace “inject a neighbouring domain's predicted property” with
> **“transfer a mechanism-normalized response law or parameter prior, anchor it
> with sparse recipient evidence, and abstain when the invariant breaks.”**

The cross-laboratory battery degradation programme is the highest-priority
experimental test of this idea. The HTEM response-field programme is the best
fully experimental analogue of Edison's relative-representation proposal. The
OC20/OC22 and DFT/band-gap experiments are useful external benchmarks or future
computational studies, but they should not consume the current paper's main
experimental claim budget.

