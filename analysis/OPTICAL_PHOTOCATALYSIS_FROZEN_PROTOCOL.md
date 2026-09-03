# Frozen retrospective protocol: experimental optical knowledge borrowing for molecular photocatalysis

## Question

Can an experimental optical-property database supply information that repairs
prediction and ranking in chemically distant, data-poor regions of an
independently measured molecular photocatalysis programme?

The directed edge is:

> experimental molecular spectroscopy (donor) -> photocatalytic hydrogen
> evolution by aromatic organic molecules (recipient)

This is a mechanistically adjacent edge. Light absorption and excited-state
relaxation occur upstream of charge transfer and sacrificial hydrogen evolution,
but the optical endpoints are not themselves the photocatalytic outcome.

## Evidence status and claim boundary

This is a **frozen retrospective external benchmark**, not a prospective
experiment. Before this freeze, the two published papers, their scientific
conclusions, the names of the data columns, and a few schema-validation rows were
inspected. No cross-database model was fitted and no aggregate target-outcome
profile or transfer contrast was calculated.

A positive primary result may establish one experimental-database borrowing
edge from molecular spectroscopy to molecular photocatalysis. It cannot
establish prospective discovery, transfer to inorganic photocatalysis, or a
universal advantage of optical descriptors. Null, harmful, and abstaining
outcomes remain part of the borrowing map.

The machine-readable contract is
`analysis/optical_photocatalysis_borrowing_design.json`.

## Data roles

### Donor: experimental optical properties

The fixed donor is Figshare version 2 of the database accompanying
Joung *et al.*, *Scientific Data* (2020), DOI
`10.1038/s41597-020-00634-8`.

Its grain is one chromophore-environment measurement. Candidate donor endpoints
are absorption maximum, emission maximum, fluorescence lifetime,
photoluminescence quantum yield, and log extinction coefficient. The primary
donor learner predicts the per-chromophore median across reported environments.
Water, methanol/alcohol, and solid-state subsets are sensitivities because the
recipient experiment used a triethylamine-methanol-water mixture with in-situ
platinum.

Every recipient molecule is removed from donor training. Removing donor
molecules with fingerprint similarity at least 0.95 to any recipient is a
strict sensitivity, not a replacement primary analysis.

### Recipient: molecular photocatalytic hydrogen evolution

The recipient is the high-throughput molecular library reported by Li *et al.*,
*Chemical Science* (2021), DOI `10.1039/D1SC02150H`.

The published 572-molecule library is the development set. The separately
published 96-molecule blind set is locked for final evaluation. Hydrogen
evolution rate is transformed with `log1p`; the paper's activity thresholds of
1.07 and 12.5 micromol per hour are retained for secondary classification and
retrieval endpoints.

The blind outcomes cannot be joined to the feature table until donor-property
admission, model settings, label-budget draws, OOD scopes, and controls have
been hashed in a blind-release manifest.

## What counts as OOD

Molecules are represented by radius-2, 2,048-bit Morgan fingerprints.
Out-of-distribution distance is one minus the maximum Tanimoto similarity to
the eligible 572-molecule development library.

The primary OOD scope is the 40% of blind molecules with lowest maximum
similarity to development. The most distant 25% is a sensitivity. Ties are
broken with a canonical-SMILES hash and are therefore outcome-independent.

Bemis-Murcko scaffolds define resampling and grouping units. Acyclic molecules
receive a deterministic acyclic label.

## How knowledge is borrowed

For each optical property, a donor model learns the relation

`molecular structure -> experimental optical property`.

Only donor properties with positive scaffold-held-out skill are admitted. For
each recipient molecule, the admitted donor models produce an optical
prediction vector and an uncertainty vector. The target model then learns

`molecular structure + borrowed optical vector -> photocatalytic activity`.

The donor vector is therefore not the target answer. It is an externally learned
summary of how the molecule is expected to interact with light and dissipate an
excited state.

Admission has two stages:

1. donor-only gate: the optical property must be predictable for held-out donor
   scaffolds;
2. development-only recipient gate: at label budget 60, the whole admitted
   optical vector must improve scaffold-group cross-validation by at least 2%
   and exceed a matched shuffled-vector median.

The 96 blind outcomes cannot influence either gate.

## Primary comparison and success

The primary endpoint is paired relative reduction in `log1p(HER)` RMSE versus a
target-structure-only model in the frozen hard-OOD 40% of the blind set at
recipient label budget 60.

Success requires all of the following:

- at least 5% relative RMSE improvement;
- a scaffold-cluster bootstrap 95% interval with lower bound above zero;
- Holm-adjusted *p* below 0.05;
- positive absolute augmented-model R2;
- improvement over a shuffled donor vector;
- no more than 2% relative RMSE harm across the full blind set.

Secondary endpoints include rank correlation, active/high-activity average
precision, top-5/10/20 enrichment, experiments needed to recover high-activity
molecules, and performance as a function of donor support.

## Required controls

- target molecular structure only;
- target structure plus the published calculated electronic descriptors;
- target structure plus admitted donor optical predictions;
- target structure plus both donor optical predictions and calculated
  descriptors;
- column-wise shuffled donor vector;
- equal-dimensional Gaussian random features;
- molecular melting-point prediction as an optional wrong-domain donor if that
  source independently passes its source-only skill and coverage gates.

Direct optical measurements for recipient molecules may be shown only as a
clearly labeled real-world lookup upper bound. They cannot enter the strict
transfer primary result.

## Interpretation

The result supports the paper's central story only if the optical donor improves
the locked molecular OOD region beyond target-only, calculated-descriptor, and
matched false-borrowing controls. If the feature fails donor skill, target
increment, or final utility gates, the correct decision is abstention. This is
the intended behavior of a selective knowledge-borrowing map.
